import yaml
import subprocess
import os.path as path
import os
import re
import sys
import logging

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
if len(sys.argv) > 1:
	repos = sys.argv[1:]
else:
	repos = [x.strip() for x in open(path.join(config["folder"], config["repos"])).readlines()]
logging.info("Repos to backup: %s", ", ".join(repos))
cmd = "github-backup {org} --issues --issue-comments --issue-events --pulls --pull-comments --pull-commits --labels --hooks --milestones --repositories --wikis -O --fork --prefer-ssh -o {folder} -t {token} --private -R {repo}"

if not path.exists(path.join(path.dirname(path.realpath(__file__)), "ssh-git.sh")):
	raise Exception, "Can't find %s" % path.join(config["folder"],"ssh-git.sh")

if not path.exists(path.join(config["folder"], config["account"])):
	raise Exception, "Can't find %s" % path.join(config["folder"], config["account"])

env = os.environ.copy()
env["GIT_SSH"] = path.abspath("{folder}/ssh-git.sh".format(**config))
env["PKEY"] = path.abspath("{folder}/{account}".format(**config))
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
	"^$"
	]
goodlines = [re.compile(x) for x in goodlines]

allok = True
for repo in repos:
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
	errlines = [x for x in stderrdata.split("\n") if x != ""]
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
