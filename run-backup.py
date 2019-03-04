import yaml
import subprocess
import os.path as path
import os
import re
import sys
import logging
from datetime import datetime
import stat
from smtpHandler import BufferingSMTPHandler

config = yaml.load(open("backup.yaml"))

logger = logging.getLogger()
logger.setLevel(logging.getLevelName(config["logging"]))

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
smtpHandler = BufferingSMTPHandler(config["smtp_server"], config["email_from"], config["email_to"], "ERROR in Github backup", 10000)
logger.addHandler(smtpHandler)

with open(path.join(config["backup_folder"], config["repos"])) as reposFile:
	repos = yaml.load(reposFile.read())["repos"]

if len(sys.argv) > 1:
	repos = {k: v for k, v in repos.iteritems() if k in sys.argv[1:]}

logging.info("Repos to backup: %s", ", ".join(sorted(repos, key=str.lower)))
cmd = "github-backup {org} --issues --issue-comments --issue-events --pulls \
	--pull-comments --pull-commits --labels --hooks --milestones --repositories --wikis -O --fork --prefer-ssh -o {backup_folder} -t {token} --private -R {repo}"

if not path.exists(path.join(path.dirname(path.realpath(__file__)), "ssh-git.sh")):
	raise Exception, "Can't find %s" % path.join(config["backup_folder"],"ssh-git.sh")

pkey = path.abspath("{backup_folder}/{account}".format(**config))
if not path.exists(pkey):
	raise Exception, "Can't find %s" % pkey
mode = stat.S_IMODE(os.stat(pkey).st_mode)
if mode != 0o600:
	raise Exception, "%s must be in file mode 600, or SSH doesn't accept it. It's in %s"%(pkey, oct(mode)[1:])

env = os.environ.copy()
env["GIT_SSH"] = path.abspath("{code_folder}/ssh-git.sh".format(**config))
env["PKEY"] = pkey
if "SSH_AUTH_SOCK" in env:
	del env["SSH_AUTH_SOCK"]

goodlines = [
	r"Backing up user ",
	r"(?:Retrieving|Filtering|Backing up) repositories",
	r"Retrieving [^ ]+ (?:issues|pull requests|milestones|labels|hooks)",
	r"(?:Saving|Writing) \d+ (?:issues|pull requests|milestones|labels|hooks) to disk",
	r"Cloning [^ ]+ repository from git@github.com:[^ ]+.git to /", # more path after the /
	r"Updating [^ ]+ in /", # more path after the /
	r"Skipping [^ ]+ \(git@github\.com:.+?\.wiki\.git\) since it's not initalized", # allowed to not have wikis
	r"Exceeded rate limit of \d+ requests; waiting \d+ seconds to reset",
	r"No more requests remaining",
	r"^$"
	]
goodlines = [re.compile(x) for x in goodlines]

allok = True
for repo in sorted(repos, key=str.lower):
	repo_folder = path.join(config["backup_folder"], "repositories", repo, "repository", ".git") # .git folder always gets updated
	if path.exists(repo_folder):
		last_time = datetime.fromtimestamp(os.path.getmtime(repo_folder))
		if last_time > repos[repo]["last_event"]:
			logger.info("Skipping %s due to it being already up to date (%s < %s)", repo, repos[repo]["last_event"], last_time)
			continue

	logger.info("Backing up %s",repo)
	torun = cmd.format(repo=repo, **config)
	logger.debug("Backup command %s", torun)
	popen = subprocess.Popen(
		torun,
		shell=True, # to use PATH
		env=env,
		stderr=subprocess.PIPE,
		stdout=subprocess.PIPE)
	(stdoutdata, stderrdata) = popen.communicate()
	badlines = []
	uncheckedErrlines = [x for x in stderrdata.split("\n") if x != ""]
	errlines = []
	for line in uncheckedErrlines:
		for g in goodlines:
			if g.search(line) is not None:
				break
		else:
			errlines.append(line)
	fourOhFoursAllowed = 0 # We allow some due to hooks fun
	fourOhFour = "API request returned HTTP 404: Not Found"
	for line in stdoutdata.split("\n"):
		for g in goodlines:
			if g.search(line) is not None:
				break
		else:
			if line == "Unable to read hooks, skipping" and errlines == [fourOhFour]:
				# Anything else we don't know, but this is acceptable
				fourOhFoursAllowed = 1
			else:
				badlines.append(line)
	if badlines != [] or stdoutdata.strip() == "" or errlines != ([fourOhFour] * fourOhFoursAllowed):
		logger.error("Backup failure for %s", repo)
		for line in badlines:
			logger.warning("Bad line '%s'", line)
		logger.warning("Stdout: %s", stdoutdata)
		logger.warning("Stderr: %s", stderrdata)
		allok = False
	else:
		logger.info("Backed up %s ok", repo)

if not allok:
	smtpHandler.flush()
	sys.exit(-1)
else:
	smtpHandler.clear()
