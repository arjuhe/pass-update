# YML documentation

This file is explains the structure of a website/instance `yml` file.

`pass update` uses independant *YAML* file to store website dependent data to
update a password. Because this data may change throught the time, the use of
*YAML* file make the maintenance simple.

Here is an example of this file for [gitlab.com](https://gitlab.com):

```YAML
instance: gitlab

url: https://gitlab.com

visit: /profile/password/edit

password:
  lenght: '25'
  character_set: '[:graph:]'
  no_symbols: 'false'

pages:
  - auth
  - update

auth:
  title: Sign in
  find:
    - user[login]
    - user[password]
  input:
    - login
    - password

update:
  title: User Settings
  find:
    - user[current_password]
    - user[password]
    - user[password_confirmation]
  input:
    - password
    - new-password
    - new-password
```

## `instance`
For service that can have multiple instance, the instance var set the name of
the instance. Eg: The process of updating password for gitlab.com is the same
than the process of updating password for a specific instance of Gitlab. Thus,
the same ym can be used.

## `url`
Base URL of the website. This url can be overwritten by the url present in the
path or/and present in the password file.

## `visit`
This is the location of the page where an user can change its password.

## `password`
A set of password settings when generating a new password:
* `lenght`: Set a password lenght. The maximun password lenght accepted by the
website. If `None`, use default in pass.
* `character_set`: Set character set for password generation. If `None`, use
default in pass.
* `no_symbols`: If `true` exclude symbols from password generation

If you do not want to set special password configuration, just do not write any
password variables.

## `pages`
The list of the page the updater needs to go throught in order to enter a new
password for a given website.

## Page structure
A `page` contains the name of the form input the updater needs to fill in. The structure of a `page` is the following:
* `title`: string included in the name of the page. This string is needed by selenium in order to detect if the page has been loaded. It doesn't have to be the full name of the page.
* `find`: The name of the form input to fill in.
* `input`: The type of input corresponding to the name of the input.


## Inputs supported
Here is the list of supported inputs:
* `password`: The updater will retrieve the password from the repository.
* `login`: The updater will retrieve the login from the repository.
* `new-password`: The updater will return a newly generated password.
* `otp`: One Time Password. Tell the updater to retrieve a OTP for two factor
authentication secret.
