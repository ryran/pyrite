#!/usr/bin/env python3
# Copyright 2012, 2013 Ryan Sawhill Aroha <rsaw@redhat.com>
#
# License:
#
#    Pyrite is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Pyrite is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Pyrite.  If not, see <http://gnu.org/licenses/gpl.html>.
#
# TODO:
#   * Icons for for encrypt, decrypt, sign, verify buttons, application
#   * Undo stack. Blech. Kill me.
#   * Update notifications
#   * BUG: First drag/drop onto FileChooserButton fails; 2nd, 3rd, etc succeed.
#       It's a GTK+ issue. Reported. bugzilla.gnome.org/show_bug.cgi?id=669718

import argparse
from sys import argv

import modules.core

# Parse command-line arguments
parser = argparse.ArgumentParser(
    prog='pyrite',
    description="GnuPG/OpenSSL GUI to encrypt, decrypt, sign, or verify files/"
                "ASCII text input.")

parser.add_argument('input', metavar='INPUT', nargs='?',
                    help="ascii input file to populate Message area with (NOTE"
                         ": treatment of INPUT is modified by '-t' & '-d')")

g2 = parser.add_mutually_exclusive_group()

g2.add_argument('-d', '--direct-file', action='store_true',
                help="flag INPUT as a file path to open in direct-mode")

g2.add_argument('-t', '--text-input', action='store_true',
                help="flag INPUT as text instead of a file path")

g1 = parser.add_mutually_exclusive_group()

g1.add_argument('-e', '--encdec', action='store_true',
                help="enable encrypt/decrypt mode")

g1.add_argument('-s', '--signverify', action='store_true',
                help="enable sign/verify mode")

parser.add_argument('-c', '--symmetric', action='store_true',
                    help="enable symmetric encryption mode")

parser.add_argument('-r', '--recipients', metavar='RECIP',
                    help="recipients for asymmetric mode (semicolon-separated)")

parser.add_argument('-k', '--defaultkey', metavar='KEYUID',
                    help="override default gpg private key")

parser.add_argument('-b', '--backend', choices=('gpg', 'openssl'),
                    help="backend program to use as encryption engine")

args = parser.parse_args()

# If no cmdline options specified, let's save some cycles later
if len(argv) == 1:
    args = None

if __name__ == "__main__":

    FeS2 = modules.core.Pyrite(args)
    try:
        FeS2.main()
    except KeyboardInterrupt:
        print()
        exit()
