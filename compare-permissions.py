import yaml
import os.path as path
import logging

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

yaml_path = path.join(config["folder"], config["repos"])
current_repos = yaml.load(open(yaml_path))
previous_repos = yaml.load(open(yaml_path + ".old"))

def makePermsDict(repo):
	return {x["who"]: (x["what"],x["why"]) for x in repo["access"]}

allsame = True
for r in current_repos:
	if r == "_when": # Magic entry that has info on when this was recorded
		continue
	logging.debug("Checking %s", r)
	repo = makePermsDict(current_repos[r])
	old_repo = makePermsDict(previous_repos[r])
	for k in repo:
		user = repo[k]
		if k not in old_repo:
			allsame = False
			logging.warning("%s has been added to %s with permissions %s because of %s", k, r, user[0], user[1])
		else:
			old_user = old_repo[k]
			if old_user[0] != user[0]:
				allsame = False
				logging.warning("%s has changed permissions from %s to %s because of %s on %s (was %s)", k, old_user[0], user[0], user[1], r, old_user[1])

	for k in old_repo:
		user = old_repo[k]
		if k not in repo:
			allsame = False
			logging.warning("%s has been removed %s from permissions %s. Old reason was %s", k, r, user[0], user[1])

if not allsame:
	when = previous_repos["_when"]
	new_path = yaml_path + when.strftime("-%Y-%m-%dT%H:%M:%S%z")
	logging.warning("Writing to %s because of changes", new_path)
	with open(new_path, "w") as new_file:
		yaml.dump(previous_repos, new_file)
