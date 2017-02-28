#!/usr/bin/env python3
# pass update - Password Store Extension (https://www.passwordstore.org/)
# Copyright (C) 2017 Alexandre PUJOL <alexandre@pujol.io>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__name__    = "pass update"
__version__ = "0.2"
__author__  = "Alexandre Pujol"
__date__    = "$29-Feb-2017$"

import os
import sysPasswordFileError
import yaml
import time
import logging
import argparse
import validators # TODO: use "from urlparse import urlparse" instead
import subprocess
from selenium import webdriver # https://selenium-python.readthedocs.io
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from password_store import PasswordStore, PasswordStoreError

if 'UPDATER_DIR' not in os.environ:
    print("This program should only be called by 'pass update'.")
    exit(1)

UPDATER_DIR = os.environ['UPDATER_DIR']

class c():
    purple = '\033[35m'
    blue = '\033[34m'
    green = '\033[32m'
    yellow = '\033[33m'
    red = '\033[31m'
    end = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

def message(content):
    print(c.bold + "  .  " + c.end + content)

def success(content):
    print(c.bold + c.green + " (*) " + c.end + c.green + content + c.end)

def warning(content):
    print(c.bold + c.yellow + " [W] " + c.end + c.yellow + content + c.end)

def error(content):
    print(c.bold + c.red + " [*] " + c.end + c.red + content + c.end)

def die(content):
    error(content)
    exit(1)

def yesno(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    # From https://code.activestate.com/recipes/577058/
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

class InstanceError(Exception):
    """ Error in a YML instance file """
    pass

class UpdateInputError(Exception):
    """ Error in the input code system """
    pass

class PasswordFileError(Exception):
    """ Error linked to the PasswordFile class """
    pass

class Driver():
    """ Context Manager and Selenium webdriver manager.

    It supports the following browsers:
        - Firefox
        - HTML
        - Chrome

    The headless mode can be activated to shortcut GUI outputs (default)
    Some security feature are activated in the Firefox browser profile:

    """

    def __init__(self, browser = 'Firefox', headless = True):
        self.browser = browser
        self.headless = headless

    def __enter__(self):
        # TODO:
        # - Test other driver (incl HTML one, the faster)
        # - Check if we can configure the profile for security params
        # - Option for full command line (no gui output)
        if self.browser == 'Firefox':
            self._driver = webdriver.Firefox()
        else:
            raise Exception("Browser not supported")

        return self._driver

    def __exit__(self, type, value, traceback):
        if type is not None:
            pass
        #self._driver.quit() # TODO: only if not debug mode
        del self.browser

class PassUpdate():
    """ Auto uptade a password in the password store repository

    :Parameters:
        :file: (PasswordFile)

        :driver: (webdriver)
            Selenium webdriver

        :web: (dict)
            YML Instance data
    """

    def __init__(self, file, driver):
        self.file = file
        self.driver = driver
        self._newpassword = None

    def run(self):
        """ Run the YML instance file.

            :Raise: UpdateInputError, Selenium Error
        """
        self.driver.get(self.file.url + self.web['visit'])
        # TODO: Get error if the page does not exits or not available.
        logger.debug("Website url: %s", self.driver.current_url)

        for page in self.web['pages']:
            if page == '2fa':
                continue # 2FA is not supported yet.

            WebDriverWait(self.driver, 10).until(EC.title_contains(self.web[page]['title']))
            time.sleep(4)
            logger.debug("Page Title: %s", self.driver.title)

            for ii in range(0, len(self.web[page]['find'])):
                field = self.driver.find_element_by_name( self.web[page]['find'][ii] )
                field.send_keys(self._get( self.web[page]['input'][ii] ))
            field.submit()

            # TODO Find a way to check if this is a success or a fail.
            # TODO Manage selenium expection

    def parse(self):
        """ Parse the YML instance file for data and errors.

        :Create:
            :web: (dict) The parsed data

        :Raise: InstanceError if the parser detect an error.
        """
        with open(os.path.join(UPDATER_DIR, self.file.instance, '.yml')) as file:
            web = yaml.safe_load(file)

        # instance:
        if 'instance' not in web:
            raise InstanceError("instance name must not be empty")

        # url:
        if 'url' in web:
            if self.file.url is None:
                self.file.url = web['url']
        else:
            raise InstanceError("url must not be empty")

        # visit:
        if 'visit' not in web:
            raise InstanceError("visit must not be empty")

        # password:
        if 'password' in web:
            if 'lenght' in web['password']:
                self.file.store.env['PASSWORD_STORE_GENERATED_LENGHT'] = str(web['password']['lenght'])

            if 'character_set' in web['password']:
                self.file.store.env['PASSWORD_STORE_CHARACTER_SET'] = web['password']['character_set']

            if 'no_symbols' in web['password']:
                if web['password']['no_symbols'] is True:
                    # FIXME, set self.no_symbols, give it to pass update --generate no_symbols
                    self.file.store.env['PASSWORD_STORE_CHARACTER_SET'] = self.file.store.env['PASSWORD_STORE_CHARACTER_SET_NO_SYMBOLS']

        # pages - Check find and input size
        for page in web['pages']:
            if 'title' not in web[page]:
                raise InstanceError(page + "['title'] must not be empty")

            if len(web[page]['find']) != len(web[page]['input']):
                raise InstanceError(page + "['find'] and " + page + "['input'] must have the same size")

        self.web = web
        logger.debug("parse: %s", web)

    def _get(self, input):
        """
            From a specific type of input requested return the corresponding
            real input present in path.

            The supported input are:
                - login: Return the user login.
                - password: Return the user password.
                - new-password: Create and return a new password.
                                Or return the newly generated password.
                - otp: Return a One Time Password code for 2FA.

            :Raise: UpdateInputError
        """
        logger.debug("_get: %s", input)
        if input == 'login':
            return self.file.login
        elif input == 'password':
            return self.file.password
        elif input == 'new-password':
            if self._newpassword is None:
                self._newpassword = self._genpass()
            return self._newpassword
        elif input == 'otp':
            raise UpdateInputError("OTP is not supported yet.")
        else:
            raise UpdateInputError(input + "is not a supported input.")

    def _genpass(self):
        """ Call pass update --generate in order to generate a new password

            The aim of this function is to generate the same kind of password
            than pass itself. It use the same command line to generate password.

            :Raise: PassError
        """
        command = ['/usr/bin/pass', 'update', '--generate']
        if self.no_symbols:
            command.append('no_symbols')

        res = subprocess.run(command, universal_newlines = True,
                             stdout = subprocess.PIPE, env = self.file.store.env )
        if res.returncode != 0:
            raise PasswordStoreError(res.stdout)

        logger.debug("_genpass: %s", res.stdout)
        return res.stdout

    def overwrite(self):
        """ Overwrite the old password by the new one.

        """
        path = self.file.path

        content = self.file.store.show(self.file.path)
        new_content = self._newpassword + content[2:]
        print(new_content)

        try:
            self.file.store.remove(path)
        except:
            path += '.new'
            warning("Unable to remove %s, writting new password in %s", self.file.path, path)

        try:
            self.file.store.insert(path, content, multiline = True)
        except:
            warning("Unable to insert %s in the password repository.", path)
            warning("The content is the following:")
            print(new_content)

        del content new_content

    def quit(self):
        del self.file
        del self._newpassword

class PasswordFile():
    """ PasswordFile represents a file in a password repository.

    :Parameter:
        :path: (string)
            Path to the encrypted password in the repository

        :store: (password_store)
            Password Store pyhton wrapper object

        :password: (string)

        :login: (string)
            Login id. This is the content of the second line in path.

        :meta: (dict)
            YML content structure representing the content of path. Password and
            login are not present.

        :instance: (string)
            instance_path is the path to the instance YML file
            The name of the instance file to load. All website linked to the
            same instance can be managed using the same YML file.
            (both extension and path are not needed)

        :url: (string)
            url is url to use in order to connect to the website. If url is
            None, the the url present in instance_path
    """

    def __init__(self, path, store):
        self.path = path
        self.store = store
        self.url = None

    def _in_directory(self, path, directory, instance = False):
        """ Is path present in the directory """
        for root, dirs, files in os.walk(directory):
            files = [f for f in files if not f[0] == '.']    # Ignore hidden file
            dirs[:] = [d for d in dirs if not d[0] == '.']   # Ignore hidden folder
            files = [os.path.splitext(f)[0] for f in files ] # Remove extension
            if instance:
                files = [os.path.splitext(f)[0] for f in files ] # Remove second extension
            if os.path.basename(self.path) not in files:
                return False

        return True

    def in_store(self):
        """ Is path in the password store """
        return self._in_directory(self.path, self.store.prefix)

    def supported_updater(self):
        """ If the path basename is the same than the instance name present in
            UPDATER_DIR then path is a supported website/instance.
        """
        return self._in_directory(self.path, UPDATER_DIR)

    def supported_instance(self):
        """ Is the instance name collected in the password file is a supported
            instance?
        """
        return self._in_directory(self.meta['instance'], UPDATER_DIR, True)

    def getdata(self):
        """ Retrieve data from the password file

        :Store:
            :password: Password
            :login: Login
            :meta: (dict) YML content structure
        """
        (self.password, self.login, self.meta) = self.store.credential(self.path)

    def has_login(self):
        """ Is a login present in path """
        if self.login is None:
            return False
        else:
            return True

    def path_is_url(self):
        """ Is the pathname a valid url that can be used by the updater? """
        return validators.url(self.path)

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path

def autoupdate_files(files):
    """ Run the auto updater system for all the files in 'files' """
    with Driver() as driver:
        for file in files:
            # try:
            updater = PassUpdate(file, driver)
            updater.parse()
            updater.run()
            # except Exception as e:
                # logger.warning("Warning: " + updater.file.path + ' ' + str(e))
            # else:
                # updater.overwrite()
            # finally:
                # updater.quit()

def sanity_check(prefix, paths):
    """ Check and previous dectection for the different path in 'paths'.

        Tests effectued:
            - Is path present in the password store repository?
            - Is a login present?
            - Is path supported by our YML instances (trivially detection)?
            - Is a instance name provided?
            - Is path supported by our YML instances (advanced detection)?
            - Is a url provided?

        Return: Three list of PasswordFile object.
    """
    auto_files = []
    manual_files = []
    invalid_files = []

    for path in paths:
        try:
            store = PasswordStore(prefix, use_os_environ = True)
            file = PasswordFile(path, store)

            if not file.in_store():
                raise PasswordStoreError("is not in the password store.")

            file.getdata()
            if not file.has_login():
                raise PasswordFileError("does not have a login.")

            if file.supported_updater():
                auto_files.append(file)
                file.instance = os.path.basename(file.path)
            elif 'instance' in file.meta:
                if file.supported_instance():
                    auto_files.append(file)
                    file.instance = file.meta['instance']
                else:
                    raise PasswordFileError("is not a supported instance")
            else:
                raise PasswordFileError("does not have an instance.")

            if file.path_is_url():
                file.url = file.path
            elif 'url' in file.meta:
                file.url = file.meta['url']
            else:
                file.url = None # Use instance default

            logger.debug("url: %s", file.url)
            logger.debug("instance: %s", file.instance)
        except PasswordStoreError as e:
            invalid_files.append(file)
            logger.warning(path + ' ' + str(e))

        except PasswordFileError as e:
            manual_files.append(file)
            logger.warning(path + ' ' + str(e))

    return (auto_files, manual_files, invalid_files)

if __name__ == '__main__':

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-q', '--quiet'  , action='store_true', default=False)
    # parser.add_argument('-v', '--verbose', action='store_true', default=False)
    # parser.add_argument('-d', '--debug'  , action='store_true', default=False)
    # arg = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.debug("Auto Updater")

    try:
        paths = sys.argv
        paths.pop(0)
        prefix = os.environ['PREFIX']
    except Exception:
        die("This program should only be called by 'pass update'.")

    logging.debug("paths: " + str(paths))

    (auto_files, manual_files, invalid_files) = sanity_check(prefix, paths)
    success("The following password are going to be automaticaly updated:")
    print(auto_files)
    warning("The following password are not going to be automaticaly updated:")
    print(manual_files)
    print(invalid_files)

    if len(invalid_files) > 0:
        die("ERROR")

    if len(auto_files) > 0:
        autoupdate_files(auto_files)

    if len(manual_files) > 0:
        message('manual passwords update')
        for file in manual_files:
            message("Updating password for " + file)
            print(file.password)
            yes = yesno("Are you ready to generate a new password?")
            if yes:
                file.store.generate(file.path, inplace = True)
    else:
        message('No manual passwords to update' )
