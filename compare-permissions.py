import yaml
import os.path as path
import logging

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

current_repos = yaml.load(open(path.join(config["folder"], config["repos"])))
previous_repos = yaml.load(open(path.join(config["folder"], config["repos"] + ".old")))

def makePermsDict(repo):
	return {x["who"]: (x["what"],x["why"]) for x in repo["access"]}

for r in current_repos:
	logging.debug("Checking %s", r)
	repo = makePermsDict(current_repos[r])
	old_repo = makePermsDict(previous_repos[r])
	for k in repo:
		user = repo[k]
		if k not in old_repo:
			logging.warning("%s has been added to %s with permissions %s because of %s", k, r, user[0], user[1])
		else:
			old_user = old_repo[k]
			if old_user[0] != user[0]:
				logging.warning("%s has changed permissions from %s to %s because of %s on %s (was %s)", k, old_user[0], user[0], user[1], r, old_user[1])

	for k in old_repo:
		user = old_repo[k]
		if k not in repo:
			logging.warning("%s has been removed %s from permissions %s. Old reason was %s", k, r, user[0], user[1])

	#break
