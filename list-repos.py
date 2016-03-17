import github
import yaml
import os.path as path
from datetime import datetime, timedelta
import collections
import logging

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logging.getLogger("github").setLevel(logging.INFO) # Don't give extra debug!
logger = logging.getLogger(__name__)

g = github.Github(login_or_token=config["admin-token"])

repos = {}
oldest_when = datetime.now() - timedelta(days=90) # Github doesn't return events more than 90 days ago, so assume repos with that timestamp had something just before then https://developer.github.com/v3/activity/events/

org = g.get_organization(config["org"])

Access = collections.namedtuple('Access', ['who', 'why', 'what'])

admins = []
for member in org.get_members(role="admin"):
	admins.append(member.login)

def max_permission(perms):
	if "admin" in perms:
		return "admin"
	elif "push" in perms:
		return "push"
	elif "pull" in perms:
		return "pull"
	else:
		raise Exception, perms

for repo in org.get_repos():
	logging.info("repo %s", repo.name)
	repos[repo.name] = {}
	access = []
	def new_access(adding):
		existing = [x for x in access if x.who == adding.who]
		if len(existing) == 1:
			existing = existing[0]
			new_perm = max_permission([adding.what, existing.what])
			if new_perm != existing.what:
				access.remove(existing)
				access.append(adding)
		elif len(existing) == 0:
			access.append(adding)
		else:
			raise Exception, existing

	for admin in admins:
		new_access(Access(admin, "[Owner]", "admin"))

	for team in repo.get_teams():
		for user in team.get_members():
			new_access(Access(user.login, team.name, team.permission))

	for collaborator in repo.get_collaborators():
		perms = collaborator._rawData['permissions']
		perms = max_permission({k: v for k,v in perms.items() if v}.keys())
		new_access(Access(collaborator.login, "Collaborator", perms))

	if not repo.private:
		new_access(Access("Everyone", "[Public access]", "pull"))

	repos[repo.name]["access"] = [dict(x._asdict()) for x in access]

	events = list(repo.get_events().get_page(0))
	if len(events) > 0:
		when = events[0].created_at
	else:
		when = oldest_when.replace() # Can't do copy, but replace works!
	repos[repo.name]["last_event"] = when

repos["_when"] = datetime.now() # Record when we generated this

with open(path.join(config["backup_folder"], config["repos"]), "w") as reposfile:
	reposfile.write(yaml.safe_dump(repos))
