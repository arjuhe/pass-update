#!/usr/bin/env python3
# password store wrapper - https://www.passwordstore.org/
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

# Inspired by
# - https://github.com/jmcs/py-password-store
# - https://github.com/languitar/pass-git-helper/blob/master/pass-git-helper

# Wrapper system for sensitive input inspired by (WIP)
# - https://github.com/vsajip/python-gnupg

import os
import sys
import yaml
import logging
import logging.config
import logging
from subprocess import Popen
from subprocess import PIPE
from subprocess import list2cmdline

logging.config.fileConfig('conf.ini')
logger = logging.getLogger('pass')
logger.setLevel(logging.DEBUG)

class PasswordStoreError(Exception):
    pass

class PasswordStore():
    """ Password Store class in Python.
        For all sensitive operation, password_store works like a wrapper for the
        pass shell script. However, simple non sensitive command (list, found...)
        are in pure python. Moreover, this class fully support all the pass
        environnement variables.

    :Parameters:
        :prefix: (string)
            PASSWORD_STORE_DIR

        :env: (dict)
            Contains all the pass environnement variables.
    """

    VERSION = '1.7.0'
    passbinary = "/usr/bin/pass"

    def __init__(self,
                 PASSWORD_STORE_DIR = os.path.expanduser('~') + "/.password-store",
                 PASSWORD_STORE_KEY = '',
                 PASSWORD_STORE_GIT = '',
                 PASSWORD_STORE_GPG_OPTS = '',
                 PASSWORD_STORE_X_SELECTION = 'clipboard',
                 PASSWORD_STORE_CLIP_TIME = '45',
                 PASSWORD_STORE_UMASK = '077',
                 PASSWORD_STORE_GENERATED_LENGHT = '25',
                 PASSWORD_STORE_CHARACTER_SET = "[:graph:]",
                 PASSWORD_STORE_CHARACTER_SET_NO_SYMBOLS = "[:alnum:]",
                 PASSWORD_STORE_ENABLE_EXTENSIONS = '',
                 PASSWORD_STORE_EXTENSIONS_DIR = os.path.expanduser('~') + "/.extensions",
                 PASSWORD_STORE_SIGNING_KEY = '',
                 GNUPGHOME = os.path.expanduser('~') + "/.gnupg",
                 use_os_environ = False):
        """
            :PASSWORD_STORE_*:
                The environnement variables to be given to pass as a subprocess.
                They can be overwritten at any time.

            :use_os_environ: (boolean)
                If true, Overwrite default password store variables by OS
                environnement variables. Usefull when strated from an extension.
        """
        self.encoding = 'latin-1'
        self.prefix = PASSWORD_STORE_DIR
        self.env = dict(PASSWORD_STORE_DIR = PASSWORD_STORE_DIR,
                        PASSWORD_STORE_KEY = PASSWORD_STORE_KEY,
                        PASSWORD_STORE_GIT = PASSWORD_STORE_GIT,
                        PASSWORD_STORE_GPG_OPTS = PASSWORD_STORE_GPG_OPTS,
                        PASSWORD_STORE_X_SELECTION = PASSWORD_STORE_X_SELECTION,
                        PASSWORD_STORE_CLIP_TIME = PASSWORD_STORE_CLIP_TIME,
                        PASSWORD_STORE_UMASK = PASSWORD_STORE_UMASK,
                        PASSWORD_STORE_GENERATED_LENGHT = PASSWORD_STORE_GENERATED_LENGHT,
                        PASSWORD_STORE_CHARACTER_SET = PASSWORD_STORE_CHARACTER_SET,
                        PASSWORD_STORE_CHARACTER_SET_NO_SYMBOLS = PASSWORD_STORE_CHARACTER_SET_NO_SYMBOLS,
                        PASSWORD_STORE_ENABLE_EXTENSIONS = PASSWORD_STORE_ENABLE_EXTENSIONS,
                        PASSWORD_STORE_EXTENSIONS_DIR = PASSWORD_STORE_EXTENSIONS_DIR,
                        PASSWORD_STORE_SIGNING_KEY = PASSWORD_STORE_SIGNING_KEY,
                        GNUPGHOME = GNUPGHOME) #,
                        #**os.environ)

        if use_os_environ:
            if not 'PREFIX' in os.environ:
                raise PasswordStoreError("PASSWORD_STORE_DIR is not present")

            self._setenv('PASSWORD_STORE_DIR', 'PREFIX')
            self._setenv('PASSWORD_STORE_KEY')
            self._setenv('PASSWORD_STORE_GIT', 'GIT_DIR')
            self._setenv('PASSWORD_STORE_GPG_OPTS')
            self._setenv('PASSWORD_STORE_X_SELECTION', 'X_SELECTION')
            self._setenv('PASSWORD_STORE_CLIP_TIME', 'CLIP_TIME')
            self._setenv('PASSWORD_STORE_UMASK')
            self._setenv('PASSWORD_STORE_GENERATED_LENGHT', 'GENERATED_LENGTH')
            self._setenv('PASSWORD_STORE_CHARACTER_SET', 'CHARACTER_SET')
            self._setenv('PASSWORD_STORE_CHARACTER_SET_NO_SYMBOLS', 'CHARACTER_SET_NO_SYMBOLS')
            self._setenv('PASSWORD_STORE_ENABLE_EXTENSIONS')
            self._setenv('PASSWORD_STORE_EXTENSIONS_DIR', 'EXTENSIONS')
            self._setenv('PASSWORD_STORE_SIGNING_KEY')
            self._setenv('GNUPGHOME')
            self.prefix = self.env['PASSWORD_STORE_DIR']

    def _setenv(self, var, env = None):
        """ Add var in the environnement variables directory.
            env must be an existing os environnement variables.
        """
        if env is None:
            env = var
        if env in os.environ:
            self.env[var] = os.environ[env]

    #
    # Wrapper Management
    #


    def _pass(self, arg = None):
        """ Call to pass """
        command = [self.passbinary]
        if arg is not None:
           command.extend(arg)

        print(str(command))
        res = subprocess.run(command, universal_newlines = True,
                             stdout = subprocess.PIPE, env = self.env )
        if res.returncode != 0:
            raise PasswordStoreError(res.stdout)

        return res.stdout

    def add_to(self, arg, option, optname, boolean = False):
        if option:
            if boolean is True:
                optname += '=' + option
            arg.append(optname)
        return arg

    #
    # Password Store Commands
    #

    def init(self, gpgid, path = None):
        """ Initialize new password storage and use gpg-id for encryption.

        :path:
            if set, specific gpg-id or set of gpg-ids is assigned for that
            specific sub folder of the password store.
        """
        arg = ['init']
        arg = self.add_to(arg, path, '--path', True)
        arg.append(gpgid)
        return self._pass(arg)

    def list(self):
        """ Pyhton implementation of 'pass list'

        :Return:
            The list of the path present in the password store
        """
        paths = []
        for root, dirs, files in os.walk(self.prefix):
            files = [f for f in files if not f[0] == '.']  # Ignore hidden file
            dirs[:] = [d for d in dirs if not d[0] == '.'] # Ignore hidden dirs
            files = [os.path.splitext(f)[0] for f in files ] # Remove extension
            paths+=files

        return paths

    def grep(self, string):
        """ Searches inside each decrypted password file for string,
            and displays line containing matched string along with filename
        """
        arg = ['grep']
        arg.append(string)
        return self._pass(arg)

    def find(self, paths):
        """ Pyhton implementation of 'pass find'

        :Argument:
            :paths: List of the path to search in the password store

        :Return:
            :found: List of the found path
        """
        found = []
        for path in paths:
            for root, dirs, files in os.walk(self.prefix):
                files = [f for f in files if not f[0] == '.']  # Ignore hidden file
                dirs[:] = [d for d in dirs if not d[0] == '.'] # Ignore hidden dirs
                files = [os.path.splitext(f)[0] for f in files ] # Remove extension
                if path in files:
                    found.append(path)

        return found

    def show(self, path, clip = None, qrcode = None):
        """ Decrypt and print a password named path.

        """
        arg = ['show']
        arg = self.add_to(arg, clip, '--clip', True)
        arg = self.add_to(arg, qrcode, '--qrcode', True)
        arg.append(path)
        return self._pass(arg)

    def insert(self, path, data, echo = True, multiline = False, force = False):
        """ This is an early work in progress version """
        raise PasswordStoreError("This command has been implemented yet.")

    def edit(self, path = None):
        raise PasswordStoreError("This command does not exit in python password store")

    def generate(self, path, lenght = None, inplace = False,
                 no_symbols = False, clip = False, force = False):
        """ Generate  a new password using /dev/urandom of length :length: and
            and insert into path.

        Supported options:
            :inplace: only replace the first line of the password file with the
               new generated password, keeping the remainder of the file intact.
            :no_symbols: do not use any non-alphanumeric characters.
            :clip: do not print the password but instead copy it to the clipboard.
            :force: do not prompt before overwriting an existing password.
        """
        arg = ['generate']
        arg = self.add_to(arg, inline, '--in-place')
        arg = self.add_to(arg, no_symbols, '--no-symbols')
        arg = self.add_to(arg, clip, '--clip')
        arg = self.add_to(arg, force, '--force')
        arg.append(path)
        if lenght is not None:
            arg.append(length)

        return self._pass(arg)

    def remove(self, path, recursive = False, force = False):
        """ Remove  the password named path from the password store. """
        arg = ['rm']
        arg = self.add_to(arg, recursive, '--recursive')
        arg = self.add_to(arg, force, '--force')
        return self._pass(arg)

    def move(self, oldpath, newpath, force = False):
        """ Renames the password or directory named oldpath to newpath """
        arg = ['mv']
        arg = self.add_to(arg, force, '--force')
        arg.extend([oldpath, newpath])
        return self._pass(arg)

    def copy(self, oldpath, newpath, force = False):
        """ Renames the password or directory named oldpath to newpath """
        arg = ['cp']
        arg = self.add_to(arg, force, '--force')
        arg.extend([oldpath, newpath])
        return self._pass(arg)

    def git(self, gitcmd):
        """ If the password store is a git repository, pass git-command-args as
            arguments to git using the password store as the git repository.
        """
        raise PasswordStoreError("This command has been implemented yet.")

    def credential(self, path):
        """ Decrypt path and read the credential in the password file.

        :Return: (tuple)
            :password: The password

            :login: The login. By conventient the login is present in the second
            line. It can be a pseudo, a mail, an ID we do not care.

            :meta: the metadata present in the file (YML format)
        """
        password = None
        login = None
        meta = dict()

        credential = self.show(path).split('\n', 2)
        if len(credential) - 1 >= 1:
            password = credential[0]

        if len(credential) - 1 > 1:
            login = credential[1].split(' ')[1]

        if len(credential) - 1 > 2:
            meta = yaml.load(credential[2:])

        return (password, login, meta)

    def version(self):
        return self.VERSION
