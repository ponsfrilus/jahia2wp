import os
import logging
import subprocess

from .models import WPException, WPUser


class WPRawConfig:
    """ First object to implement some business logic
        - is the site installed? properly configured ?

        It provides also the methods to actually interact with WP-CLI
        - generic run_wp_cli
        - adding WP users, either from name+email or sciperID
    """

    def __init__(self, wp_site):
        self.wp_site = wp_site

    def __repr__(self):
        installed_string = '[ok]' if self.is_installed else '[ko]'
        return "config {0} for {1}".format(installed_string, repr(self.wp_site))

    def run_wp_cli(self, command):
        try:
            cmd = "wp --quiet {} --path='{}'".format(command, self.wp_site.path)
            logging.debug("exec '%s'", cmd)
            return subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as err:
            logging.error("%s - WP export - wp_cli failed : %s", repr(self.wp_site), err)
            return None

    @property
    def is_installed(self):
        return os.path.isdir(self.wp_site.path)

    @property
    def is_config_valid(self):
        if not self.is_installed:
            return False
        # TODO: check that the config is working (DB and user ok)
        # wp-cli command (status?)

    @property
    def is_install_valid(self):
        if not self.is_config_valid():
            return False
        # TODO: check that the site is available, that user can login and upload media
        # tests from test_wordpress

    @property
    def db_infos(self):
        # TODO: read from wp_config.php {db_name, mysql_username, mysql_password}
        pass

    @property
    def admin_infos(self):
        # TODO: read from DB {admin_username, admin_email}
        pass

    def add_wp_user(self, username, email):
        return self._add_user(WPUser(username, email))

    def add_ldap_user(self, sciper_id):
        try:
            return self._add_user(WPUser.from_sciper(sciper_id))
        except WPException as err:
            logging.error("Generator - %s - 'add_webmasters' failed %s", repr(self), err)
            return None

    def _add_user(self, user):
        if not user.password:
            user.set_password()
        # TODO: call wp-cli to add user in WP
        return user