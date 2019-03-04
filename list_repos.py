import github
import yaml
import os.path as path
from datetime import datetime, timedelta
import collections
import logging

Access = collections.namedtuple('Access', ['who', 'why', 'what'])

def max_permission(perms):
	if "admin" in perms:
		return "admin"
	elif "push" in perms:
		return "push"
	elif "pull" in perms:
		return "pull"
	elif "none" in perms:
		return "none"
	else:
		raise Exception, perms

def max_permission_from_response(resp):
	perms = resp._rawData['permissions']
	return max_permission({k: v for k,v in perms.items() if v}.keys())

def parseRepo(repo, admins, teams, members, org):
	result = {}
	access = []
	oldest_when = datetime.now() - timedelta(days=90) # Github doesn't return events more than 90 days ago, so assume repos with that timestamp had something just before then https://developer.github.com/v3/activity/events/

	def new_access(adding):
		existing = [x for x in access if x.who == adding.who]
		if len(existing) == 1:
			existing = existing[0]
			new_perm = max_permission([adding.what, existing.what])
			if new_perm != existing.what:
				logging.debug("Replaced %s for %s in favour of %s for %s - %s", existing.what, existing.who, adding.what, adding.who, adding.why)
				access.remove(existing)
				access.append(adding)
		elif len(existing) == 0:
			logging.debug("Adding %s because of %s with %s", adding.who, adding.why, adding.what)
			access.append(adding)
		else:
			raise Exception, existing

	for admin in admins:
		new_access(Access(admin, "[Owner]", "admin"))

	for team in repo.get_teams():
		if team.name not in teams:
			team_repos = team.get_repos()
			teams[team.name] = {}
			for tr in team_repos:
				teams[team.name][tr.name] = max_permission_from_response(tr)
		logging.debug("team %s has access to %s with %s", team.name, repo.name, teams[team.name][repo.name])
		for user in team.get_members():
			new_access(Access(user.login, team.name, teams[team.name][repo.name]))

	for collaborator in repo.get_collaborators():
		perms = max_permission_from_response(collaborator)
		new_access(Access(collaborator.login, "Collaborator", perms))

	for member in members:
		new_access(Access(member, "[Organisation member]", org.raw_data["default_repository_permission"]))

	if not repo.private:
		new_access(Access("Everyone", "[Public access]", "pull"))

	result["access"] = [dict(x._asdict()) for x in access]

	events = list(repo.get_events().get_page(0))
	if len(events) > 0:
		when = events[0].created_at
	else:
		when = oldest_when.replace() # Can't do copy, but replace works!
	result["last_event"] = when

def runLists(config):
	logging.basicConfig(
		level=logging.getLevelName(config["logging"]),
		format='%(asctime)s %(levelname)s: %(message)s')
	logging.getLogger("github").setLevel(logging.INFO) # Don't give extra debug!
	logger = logging.getLogger(__name__)

	g = github.Github(login_or_token=config["admin-token"])

	repos = {}

	org = g.get_organization(config["org"])

	admins = []
	for member in org.get_members(role="admin"):
		admins.append(member.login)

	members = []
	for member in org.get_members():
		members.append(member.login)

	teams = {}

	for repo in org.get_repos():
		logging.info("repo %s", repo.name)
		repos[repo.name] = parseRepo(repo, admins, teams, members, org)

	data = {
		"when": datetime.now(), # Record when we generated this
		"repos": repos,
		"members": members
	}
	return data

def load_config(fname):
	return yaml.safe_load(open(fname))

if __name__ == "__main__":
	config = load_config("backup.yaml")
	with open(path.join(config["backup_folder"], config["repos"]), "w") as reposfile:
		data = runLists(config)
		reposfile.write(yaml.safe_dump(data))
