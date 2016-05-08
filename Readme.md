Scrutiny
========

Scrutiny is a tool for permissions audit and backup of Github repositories for an organisation. It uses [github-backup](https://github.com/josegonzalez/python-github-backup) for the underlying backup, but enhances it to check that all the repositories that should be backed up are, and adds it's own auditing process.

It's based upon [LShift's](http://www.lshift.net/) requirements for a backup and audit tool, but should be usable for other organisations.

Assumptions
-----------
1. All repositories of the organisation should be backed up
2. There's a team that should have (at least) read-only access to all repositories of the organisation (e.g. one containing all your developers)

Operation
---------
Scrutiny enables you to do the following:

1. List the set of permissions on every repository
2. Audit changes to that set of permissions (current assumption: on a daily basis)
3. Backup every repository that's changed since the last backup

The first step requires a [Github personal access token](https://github.com/settings/tokens/new) from a user with "Owner" privileges, however this token only needs ["repo" and "read:org"](https://developer.github.com/v3/oauth/#scopes) scope in order to list all of the repositories.

After that, we can use a token from a more restricted user (with "repo" scope) to do the backup.

Configuration
------------
1. Copy `backup.yaml.example` to `backup.yaml` and edit appropriately. The paths are partially required because we assume the script is likely to be run from Cron, and they reduce the likelihood of things going wrong...
2. Make a file called whatever you set `account` to in `backup.yaml` containing an SSH private key of the `account` account and put it in `backup_folder`
3. Run `generate.py`
4. You now have a `backup.sh` which does all the steps mentioned in "Operation". If for example you only want the audit steps, you may want to comment out the `run-backup` step.
