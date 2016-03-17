import jinja2
import yaml
import os
import stat

loader = jinja2.FileSystemLoader('.')
env = jinja2.Environment(loader=loader)
config = yaml.load(open("backup.yaml"))

template = env.get_template('backup.sh.template')
template.stream(config).dump("backup.sh")
os.chmod("backup.sh", os.stat("backup.sh").st_mode | stat.S_IXUSR)
