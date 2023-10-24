#!/usr/bin/env python3
#
# This file is part of Pyrite.
# Last file mod: 2013/09/15
# Latest version at <http://github.com/ryran/pyrite>
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

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from os import getenv

# Important variables
VERSION = 'v1.0.2'
ASSETDIR = './'
USERPREF_FILE = getenv('HOME') + '/.pyrite'
USERPREF_FORMAT_INFO = {'version': 'Must6fa'}

# List of possible Infobar message types
MSGTYPES = [
    0,
    Gtk.MessageType.INFO,  # 1
    Gtk.MessageType.QUESTION,  # 2
    Gtk.MessageType.WARNING,  # 3
    Gtk.MessageType.ERROR  # 4
]

# List of possible images to show in Infobar
IMGTYPES = [
    Gtk.STOCK_APPLY,  # 0
    Gtk.STOCK_DIALOG_INFO,  # 1
    Gtk.STOCK_DIALOG_QUESTION,  # 2
    Gtk.STOCK_DIALOG_WARNING,  # 3
    Gtk.STOCK_DIALOG_ERROR  # 4
]
