import jinja2
import yaml
import os
import stat
import os.path as path

loader = jinja2.FileSystemLoader('.')
env = jinja2.Environment(loader=loader)
config = yaml.load(open("backup.yaml"))
config["repos_fullpath"] = path.abspath(path.join(config["backup_folder"], config["repos"]))
template = env.get_template('backup.sh.template')
template.stream(config).dump("backup.sh")
os.chmod("backup.sh", os.stat("backup.sh").st_mode | stat.S_IXUSR)
