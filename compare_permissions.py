import yaml
import os.path as path
import logging
import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def gen_changes(current_repos, previous_repos):
	changes = {}

	def makePermsDict(repo):
		return {x["who"]: (x["what"],x["why"]) for x in repo["access"]}

	def note_change(key, msg):
		changes[key] = msg
		logging.warning(msg)

	for r in current_repos:
		logging.debug("Checking %s", r)
		repo = makePermsDict(current_repos[r])
		old_repo = makePermsDict(previous_repos[r]) if r in previous_repos else {}
		for k in repo:
			user = repo[k]
			if k not in old_repo:
				note_change((k, r), "%s has been added to %s with permissions %s because of %s"% (k, r, user[0], user[1]))
			else:
				old_user = old_repo[k]
				if old_user[0] != user[0]:
					note_change((k, r), "%s has changed permissions from %s to %s because of %s on %s (was %s)"% (k, old_user[0], user[0], user[1], r, old_user[1]))

		for k in old_repo:
			user = old_repo[k]
			if k not in repo:
				note_change((k, r), "%s has been removed %s from permissions %s. Old reason was %s"% (k, r, user[0], user[1]))

	return [changes[k] for k in sorted(changes.iterkeys())]


if __name__ == "__main__":
	config = yaml.load(open("backup.yaml"))
	logging.basicConfig(
		level=logging.getLevelName(config["logging"]),
		format='%(asctime)s %(levelname)s: %(message)s')
	logger = logging.getLogger(__name__)

	yaml_path = path.join(config["backup_folder"], config["repos"])
	if not path.exists(yaml_path):
		raise Exception, "Can't find %s. Did you run list-repos.py first?" % yaml_path
	current_repos = yaml.load(open(yaml_path))["repos"]

	old_yaml_path = yaml_path + ".old"
	old_permissions_exists = path.exists(old_yaml_path)
	data = yaml.load(open(old_yaml_path)) if old_permissions_exists else None
	if data is not None: # both an existing permissions and a usable file
		previous_repos = data["repos"]
		changes = gen_changes(current_repos, previous_repos)
	else:
		changes = []

	msg = MIMEMultipart()
	when = datetime.datetime.now().strftime("%Y-%m-%d")
	if changes != []:
		new_path = yaml_path + data["when"].strftime("-%Y-%m-%dT%H:%M:%S%z")
		logging.warning("Writing to %s because of changes", new_path)
		with open(new_path, "w") as new_file:
			yaml.dump(previous_repos, new_file)
		msg['Subject'] = 'CHANGES: Github permission changes for %s' % when
		text = "Changes!\n--------\n\n" + "\n".join(changes)
	else:
		msg['Subject'] = 'Github permission list for %s' % when
		text = "No changes"
		if not old_permissions_exists:
			text += "\n\nCannot find %s. This is an error if you're not running this for the first time." % (path.abspath(yaml_path + ".old"))

	msg['From'] = config["email_from"]
	msg['To'] = ", ".join(config["email_to"])
	changes = MIMEText(text, "plain")
	msg.attach(changes)

	with open(yaml_path) as fp:
		yaml_block = MIMEText(fp.read(), "x-mime")
		yaml_block.add_header('Content-Disposition', 'attachment', filename="permissions.yaml")
		msg.attach(yaml_block)

	composed = msg.as_string()
	file("dump", "w").write(composed)

	s = smtplib.SMTP(config["smtp_server"])
	s.sendmail(config["email_from"], config["email_to"], composed)
	s.quit()
