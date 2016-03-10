import yaml
import subprocess
import os.path as path
import os
import re
import sys

config = yaml.load(open("backup.yaml"))
repos = [x.strip() for x in open(config["repos"]).readlines()]
cmd = "github-backup {org} --issues --issue-comments --issue-events --pulls --pull-comments --pull-commits --labels --hooks --milestones --repositories --wikis -O --fork --prefer-ssh -o {folder} -t {token} --private -R {repo}"

if not path.exists(path.join(config["folder"], "ssh-git.sh")):
	raise Exception, "Can't find %s" % path.join(config["folder"],"ssh-git.sh")

if not path.exists(path.join(config["folder"], config["account"])):
	raise Exception, "Can't find %s" % path.join(config["folder"], config["account"])

env = os.environ.copy()
env["GIT_SSH"] = path.abspath("{folder}/ssh-git.sh".format(**config))
env["PKEY"] = path.abspath("{folder}/{account}".format(**config))
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

for repo in repos:
	torun = cmd.format(repo=repo, **config)
	print "Backing up %s" % repo
	popen = subprocess.Popen(
		torun,
		shell=True, # to use PATH
		env=env,
		stderr=subprocess.PIPE,
		stdout=subprocess.PIPE)
	(stdoutdata, stderrdata) = popen.communicate()
	badlines = []
	errlines = [x for x in stderrdata.split("\n") if x != ""]
	for line in stdoutdata.split("\n"):
		for g in goodlines:
			if g.search(line) != None:
				break
		else:
			if line == "Unable to read hooks, skipping" and errlines == ["API request returned HTTP 404: Not Found"]:
				# Anything else we don't know, but this is acceptable
				pass
			else:
				badlines.append(line)
	if badlines != [] or stdoutdata.strip() == "":
		for line in badlines:
			print "Bad line '%s'" % line
		print "\nOutput:\n"
		print stdoutdata
		print stderrdata
		sys.exit(-1)
	else:
		print "Backed up %s ok" % repo
	break
