import yaml
import subprocess
import os.path as path
import os
import re
import sys
import logging
from datetime import datetime

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

with open(path.join(config["backup_folder"], config["repos"])) as reposFile:
	repos = yaml.load(reposFile.read())["repos"]

if len(sys.argv) > 1:
	repos = {k: v for k, v in repos.iteritems() if k in sys.argv[1:]}

logging.info("Repos to backup: %s", ", ".join(sorted(repos, key=str.lower)))
cmd = "github-backup {org} --issues --issue-comments --issue-events --pulls --pull-comments --pull-commits --labels --hooks --milestones --repositories --wikis -O --fork --prefer-ssh -o {backup_folder} -t {token} --private -R {repo}"

if not path.exists(path.join(path.dirname(path.realpath(__file__)), "ssh-git.sh")):
	raise Exception, "Can't find %s" % path.join(config["backup_folder"],"ssh-git.sh")

if not path.exists(path.join(config["backup_folder"], config["account"])):
	raise Exception, "Can't find %s" % path.join(config["backup_folder"], config["account"])

env = os.environ.copy()
env["GIT_SSH"] = path.abspath("{code_folder}/ssh-git.sh".format(**config))
env["PKEY"] = path.abspath("{backup_folder}/{account}".format(**config))
if "SSH_AUTH_SOCK" in env:
	del env["SSH_AUTH_SOCK"]

goodlines = [
	"Backing up user ",
	"(?:Retrieving|Filtering|Backing up) repositories",
	"Retrieving [^ ]+ (?:issues|pull requests|milestones|labels|hooks)",
	"(?:Saving|Writing) \d+ (?:issues|pull requests|milestones|labels|hooks) to disk",
	"Cloning [^ ]+ repository from git@github.com:[^ ]+.git to /", # more path after the /
	"Updating [^ ]+ in /", # more path after the /
	"Skipping [^ ]+ \(git@github\.com:.+?\.wiki\.git\) since it's not initalized", # allowed to not have wikis
	"Exceeded rate limit of \d+ requests; waiting \d+ seconds to reset",
	"No more requests remaining",
	"^$"
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

	logger.info("Backing up %s" % repo)
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
			if g.search(line) != None:
				break
		else:
			errlines.append(line)
	fourOhFoursAllowed = 0 # We allow some due to hooks fun
	fourOhFour = "API request returned HTTP 404: Not Found"
	for line in stdoutdata.split("\n"):
		for g in goodlines:
			if g.search(line) != None:
				break
		else:
			if line == "Unable to read hooks, skipping" and errlines == [fourOhFour]:
				# Anything else we don't know, but this is acceptable
				fourOhFoursAllowed = 1
				pass
			else:
				badlines.append(line)
	if badlines != [] or stdoutdata.strip() == "" or errlines != ([fourOhFour] * fourOhFoursAllowed):
		logger.error("Backup failure for %s", repo)
		for line in badlines:
			logger.warning("Bad line '%s'" % line)
		logger.warning("Stdout: %s", stdoutdata)
		logger.warning("Stderr: %s", stderrdata)
		allok = False
	else:
		logger.info("Backed up %s ok", repo)
if not allok:
	sys.exit(-1)
