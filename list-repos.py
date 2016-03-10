import github
import yaml
import os.path as path

config = yaml.load(open("backup.yaml"))

g = github.Github(login_or_token=config["admin-token"])

repos = [repo.name for repo in g.get_organization(config["org"]).get_repos()]
with open(path.join(config["folder"], config["repos"]), "w") as reposfile:
	for repo in sorted(repos, key=unicode.lower):
		reposfile.write("%s\n" % repo)
