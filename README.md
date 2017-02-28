# pass update [![Build Status][build-status]][build-url]

**WARNING: This program is under development.**

A [pass](https://www.passwordstore.org/) extension that provides an automatic
solution to update your passwords.

## Description
`pass-update` is the first open source solution than can update most of your
password without human interation. It is dedicated to work as a extension for
pass, *the standart unix password manager*.

It supports two modes:
* Automatic update: if your password is for a website/instance supported.
* Manual update: otherwise.

**How does it work?**

`pass-update` uses [selenium][selenium] to automate web
password update. We use selenium because password update is usualy not supported
by website API. However, every website has an unique way to update their password.
They require to sign in, go to the user setting page, update the password...

In order to provide a unique solution for all the websites, we store all website
specific data in a `YAML` file. In this way this is simple to support a lot of
different website and to maintain the system without changing the source code itself.

**How many sites does it support?**

We currently support **7 websites**, you are very welcome to provide new website
support. The only thing you need to do is to create yml file for each new
website following our [YML documentation](YML.md).


## Examples

**Manual upddate**

Update `Social/facebook.com`
```
$ pass update Social/facebook.com
 (*) Changing password for Social/facebook.com
[}p&62"#"x'aF/_ix}6X3a)zq
  ?  Are you ready to generate a new password? [y/N] y
The generated password for Social/facebook.com is:
~*>afZsB+G\,c#+g$-,{OqJ{w
```

**Automatic update**

Update `<website-url>` (if `<website-url>` is a supported website see `doc/autoupdate.md`)
```
$ pass update Social/facebook.com
 (*) Changing password for Social/facebook.com
  .  Trying to automaticaly update your password
 (*) Succesfuly updated password for Social/facebook.com
```

## Usage

```
pass update - A pass extension that provides an automatic
              solution to update your passwords.

Vesion: 0.2

Usage:
    pass update [--help,-h] [--clip,-c] [--force,-f] pass-names...
        Provide an interactive solution to update a set of passwords.
        It prints the old password and wait for the user before
        generating a new one. Both old and newly generated password
        can optionally be written on the clipboard using the --clip
        option. The --force option allows you to update the password
        immediately. Multiple pass-names can be given in order to
        update multiple password.

Options:
    -c, --clip     Put the password in the clipboard
    -a, --auto     Only update password that can be updated automaticaly
    -f, --force    Update the password immediately
        --all      Update all the password in the repository
    -v, --version  Show version information.
    -h, --help	   Print this help message and exit.

More information may be found in the pass-update(1) man page.
```

See `man pass-update` for more information.


## Installation

**ArchLinux**

		pacaur -S pass-update

**Other linux**

		git clone https://gitlab.com/roddhjav/pass-update/
		cd pass-update
		sudo make install

**Requirments**

* `pyhton3`
* `python selenium` (webdriver only)
* `pyhton yaml`
* `pass 1.7.0` or greater.
* You need to enable the extensions in pass: `PASSWORD_STORE_ENABLE_EXTENSIONS=true pass`.
You can create an alias in `.bashrc`: `alias pass='PASSWORD_STORE_ENABLE_EXTENSIONS=true pass'`


## Contribution
Feedback, contributors, pull requests are all very welcome.


## License

    Copyright (C) 2017  Alexandre PUJOL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

[build-status]: https://gitlab.com/roddhjav/pass-update/badges/master/build.svg
[build-url]: https://gitlab.com/roddhjav/pass-update/commits/master
[selenium]: http://www.seleniumhq.org/
