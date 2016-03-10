import github
import yaml
import os.path as path
from datetime import datetime, timedelta

config = yaml.load(open("backup.yaml"))

g = github.Github(login_or_token=config["admin-token"])

repos = {}
oldest_when = datetime.now() - timedelta(days=90) # Github doesn't return events more than 90 days ago, so assume repos with that timestamp had something just before then https://developer.github.com/v3/activity/events/
for repo in g.get_organization(config["org"]).get_repos():
	events = list(repo.get_events().get_page(0))
	if len(events) > 0:
		when = events[0].created_at
	else:
		when = oldest_when.replace() # Can't do copy, but replace works!
	repos[repo.name] = {"last_event": when}

with open(path.join(config["folder"], config["repos"]), "w") as reposfile:
	reposfile.write(yaml.safe_dump(repos))
