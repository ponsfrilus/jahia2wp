# pylint: disable=W1306
import logging
import subprocess

from utils import Utils


class WPGenerator:

    USER_NAME_LENGTH = 32
    DB_NAME_LENGTH = 32
    PASSWORD_LENGTH = 32

    WP_VERSION = Utils.get_mandatory_env(key="WP_VERSION")

    MYSQL_DB_HOST = Utils.get_mandatory_env(key="MYSQL_DB_HOST")
    MYSQL_SUPER_USER = Utils.get_mandatory_env(key="MYSQL_SUPER_USER")
    MYSQL_SUPER_PASSWORD = Utils.get_mandatory_env(key="MYSQL_SUPER_PASSWORD")

    WP_ADMIN_USER = Utils.get_mandatory_env(key="WP_ADMIN_USER")
    WP_ADMIN_EMAIL = Utils.get_mandatory_env(key="WP_ADMIN_EMAIL")

    def __init__(self, environment=None, domain=None, folder=None, title=None, webmaster=None, responsible=None):
        self.environment = environment
        self.domain = domain
        self.folder = folder
        self.title = title
        self.webmaster = webmaster
        self.responsible_username = responsible

        self.set_unique_vars()

    def __repr__(self):
        return "{}/{}/{}".format(self.environment, self.domain, self.folder)

    def set_unique_vars(self):
        self.mysql_wp_user = Utils.generate_random_b64(
            self.USER_NAME_LENGTH).lower()
        self.mysql_wp_password = Utils.generate_password(self.PASSWORD_LENGTH)
        self.wp_db_name = Utils.generate_random_b64(
            self.DB_NAME_LENGTH).lower()
        self.wp_admin_password = Utils.generate_password(self.PASSWORD_LENGTH)
        self.wp_webmaster_password = Utils.generate_password(
            self.PASSWORD_LENGTH)
        self.wp_responsible_password = Utils.generate_password(
            self.PASSWORD_LENGTH)

    def run_command(self, command):
        try:
            subprocess.check_output(command, shell=True)
            logging.debug("Generator - %s - Run command %s",
                          repr(self), command)
        except subprocess.CalledProcessError as err:
            logging.error("Generator - %s - Command %s failed %s",
                          repr(self), command, err)
            return False

    def run_mysql(self, command):
        mysql_connection_string = "@mysql -h {0.MYSQL_DB_HOST} -u {0.MYSQL_SUPER_USER}" \
            " --password={0.MYSQL_SUPER_PASSWORD} ".format(self)
        self.run_command(mysql_connection_string + command)

    def wp_cli(self, command):
        try:
            cmd = "wp {} --path='{}'".format(command, self.domain)
            logging.debug("exec '%s'", cmd)
            return subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as err:
            logging.error("%s - WP export - wp_cli failed : %s",
                          repr(self), err)
            return None

    def generate(self):
        # create MySQL user
        self.run_mysql(
            "-e \"CREATE USER '{0.mysql_wp_user}' IDENTIFIED BY '{0.mysql_wp_password}';\"".format(self))

        # grant privileges
        self.run_mysql(
            r"-e \"GRANT ALL PRIVILEGES ON \`{0.wp_db_name}\`.* TO \`{0.mysql_wp_user}\`@'%';".format(self))

        # create htdocs path
        self.run_command(
            "mkdir -p /srv/{0.wp_env}/{0.site_domain}/htdocs".format(self))

        # install WordPress 4.8
        self.run_command(
            "wp core download --version=4.8 --path=/srv/{0.wp_env}/{0.site_domain}/htdocs".format(self))

        # config WordPress
        command = "wp config create --dbname={0.wp_db_name} --dbuser={0.mysql_wp_user}".format(
            self)
        command += " --dbpass={0.mysql_wp_password} --dbhost={0.mysql_db_host}".format(
            self)
        command += " --path=/srv/{0.wp_env}/{0.site_domain}/htdocs".format(
            self)
        self.run_command(command)

        # create database
        self.run_command(
            "wp db create --path=/srv/{0.wp_env}/{0.site_domain}/htdocs".format(self))

        # fill out first form in install process (setting admin user and permissions)
        command = "wp --allow-root core install --url=http://{0.site_domain} --title={0.wp_title}".format(
            self)
        command += " --admin_user={0.wp_admin_user} --admin_password={0.wp_admin_password}".format(
            self)
        command += " --admin_email={0.wp_admin_email} --path=/srv/{0.wp_env}/{0.site_domain}/htdocs".format(
            self)
        self.run_command(command)