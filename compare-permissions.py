import yaml
import os.path as path
import logging
import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

config = yaml.load(open("backup.yaml"))
logging.basicConfig(
	level=logging.getLevelName(config["logging"]),
	format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

yaml_path = path.join(config["folder"], config["repos"])
if not path.exists(yaml_path):
	raise Exception, "Can't find %s. Did you run list-repos.py first?" % yaml_path
current_repos = yaml.load(open(yaml_path))

changes = []

if path.exists(yaml_path + ".old"): # Otherwise, changes is empty
	previous_repos = yaml.load(open(yaml_path + ".old"))

	def makePermsDict(repo):
		return {x["who"]: (x["what"],x["why"]) for x in repo["access"]}

	def note_change(msg):
		changes.append(msg)
		logging.warning(msg)

	for r in current_repos:
		if r == "_when": # Magic entry that has info on when this was recorded
			continue
		logging.debug("Checking %s", r)
		repo = makePermsDict(current_repos[r])
		old_repo = makePermsDict(previous_repos[r])
		for k in repo:
			user = repo[k]
			if k not in old_repo:
				note_change("%s has been added to %s with permissions %s because of %s"% (k, r, user[0], user[1]))
			else:
				old_user = old_repo[k]
				if old_user[0] != user[0]:
					note_change("%s has changed permissions from %s to %s because of %s on %s (was %s)"% (k, old_user[0], user[0], user[1], r, old_user[1]))

		for k in old_repo:
			user = old_repo[k]
			if k not in repo:
				note_change("%s has been removed %s from permissions %s. Old reason was %s"% (k, r, user[0], user[1]))

msg = MIMEMultipart()
when = datetime.datetime.now().strftime("%Y-%m-%d")
if changes != []:
	when = previous_repos["_when"]
	new_path = yaml_path + when.strftime("-%Y-%m-%dT%H:%M:%S%z")
	logging.warning("Writing to %s because of changes", new_path)
	with open(new_path, "w") as new_file:
		yaml.dump(previous_repos, new_file)
	msg['Subject'] = 'CHANGES: Github permission changes for %s' % when
	text = "Changes!\n--------\n\n" + "\n".join(changes)
else:
	msg['Subject'] = 'Github permission list for %s' % when
	text = "No changes"

msg['From'] = config["email_from"]
msg['To'] = config["email_to"]
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
