#!/usr/bin/env bash
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

PYTHON="python3"
UPDATER_DIR="${PASSWORD_STORE_UPDATER_DIR:-/usr/lib/password-store/updaters/instances/}"
UPDATER_BIN="${PASSWORD_STORE_UPDATER_BIN:-/usr/lib/password-store/updaters/updater.py}"

#
# Commons color and functions
#
bold='\e[1m'
Bred='\e[1;31m'
Bgreen='\e[1;32m'
reset='\e[0m'
_message() { echo -e " ${bold} . ${reset} ${*}"; }
_success() { echo -e " ${Bgreen}(*)${reset} ${green}${*}${reset}"; }
_error() { echo -e " ${Bred}[*]${reset}${bold} Error :${reset} ${*}"; }
_die() { _error "${@}" && exit 1; }

# Check importers dependencies
# pass update requires python3 and the python auto-update program.
_ensure_dependencies() {
	command -v "${PYTHON}" &>/dev/null || _die "$PROGRAM $COMMAND requires ${PYTHON}"
	command -v "${UPDATER_BIN}" &>/dev/null || _die "$PROGRAM $COMMAND requires ${UPDATER_BIN}"
}

cmd_update_verion() {
	cat <<-_EOF
	$PROGRAM $COMMAND - A pass extension that provides an automatic
	              solution to update your passwords.

	Vesion: 0.2
	_EOF
}

cmd_update_usage() {
	cmd_update_verion
	echo
	cat <<-_EOF
	Usage:
	    $PROGRAM $COMMAND pass-names...
			Multiple pass-names can be given in order to update multiple password.

			If the password is from a supported website (or instance), it will
			try to automaticaly update your password.

			In manual mode, it prints the old password and wait for the user
			before generating a new one. Both old and newly generated password
	        can optionally be written on the clipboard using the --clip
	        option. The --force option allows you to update the password
	        immediately.

	Options:
	    -c, --clip     Put the password in the clipboard
	    -a, --auto     Only update password that can be updated automaticaly
	    -f, --force    Update the password immediately
	        --all      Update all the password in the repository
		-l, --list     Print the list of the supported websites/instances.
	    -v, --version  Show version information.
	    -h, --help	   Print this help message and exit.

	More information may be found in the pass-update(1) man page.
	_EOF
	exit 0
}

# Print the list of the supported instance for automatic password update
cmd_update_list() {
	_success "$PROGRAM $COMMAND supports:"
	for instance in $(updater_list); do
		_message "$instance"
	done
}

# Call the python auto update program in order to auto-update a set of password.
# $@: The paths to be updated.
_updater() {
	export PREFIX PASSWORD_STORE_KEY GIT_DIR PASSWORD_STORE_GPG_OPTS
	export X_SELECTION CLIP_TIME PASSWORD_STORE_UMASK GENERATED_LENGTH
	export CHARACTER_SET CHARACTER_SET_NO_SYMBOLS UPDATER_DIR
	export PASSWORD_STORE_ENABLE_EXTENSIONS EXTENSIONS PASSWORD_STORE_SIGNING_KEY
	"$PYTHON" "$UPDATER_BIN" ${*}
	[ $? = 0 ] || _die "Auto Updating ${@}"
}

# Generate and return a newly generated password.
#
# The aim of this function is to generate the same kind of password than pass
# itself in 'pass generate'. It uses the same command line to generate password
# but does not overwrite a pass entry.
#
# This function should only be used by UPDATER_BIN.
cmd_update_generate() {
	local length="${GENERATED_LENGTH}"
	local characters="${CHARACTER_SET}"
	local password

	[[ $length =~ ^[0-9]+$ ]] || _die "Error: pass-length \"$length\" must be a number."
	read -r -n $length password < <(LC_ALL=C tr -dc "$characters" < /dev/urandom)
	[[ ${#password} -eq $length ]] || _die "Could not generate password from /dev/urandom."
	echo -n "$password"
}

# Print the list of the available updater in UPDATER_DIR
updater_list() {
	for file in $(find "$UPDATER_DIR/"*.yml); do
		file="${file##*/}"
		echo "${file%.*}"
	done
}

# Global options
ALL=0
QUIET=0
AUTO=0
CLIP=""
FORCE=0
opts="$($GETOPT -o vahfclq -l version,auto,all,help,force,clip,generate,list,quiet -n "$PROGRAM $COMMAND" -- "$@")"
err=$?
eval set -- "$opts"
while true; do case $1 in
	--all) ALL=1; shift ;;
	-a|--auto) AUTO=1; shift ;;
	-q|--quiet) QUIET=1; shift ;;
	-c|--clip) CLIP="--clip"; shift ;;
	-f|--force) FORCE=1; shift ;;
	--generate) cmd_update_generate; exit 0 ;;
	-l|--list) cmd_update_list; exit 0 ;;
	-h|--help) shift; cmd_update_usage; exit 0 ;;
	-v|--version) shift; cmd_update_verion; exit 0 ;;
	--) shift; break ;;
esac done

[[ $err -ne 0 ]] && exit 1
_ensure_dependencies
_updater "$@"
