#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
#
#------------------------------------------------------------------------------

import gtk
from os import getenv

# Important variables
VERSION                 = 'v1.0.2'
ASSETDIR                = '/usr/share/pyrite/'
USERPREF_FILE           = getenv('HOME') + '/.pyrite'
USERPREF_FORMAT_INFO    = {'version':'Must6fa'}

# List of possible Infobar message types
MSGTYPES = [0,
            gtk.MESSAGE_INFO,      # 1
            gtk.MESSAGE_QUESTION,  # 2
            gtk.MESSAGE_WARNING,   # 3
            gtk.MESSAGE_ERROR]     # 4

# List of possible images to show in Infobar
IMGTYPES = [gtk.STOCK_APPLY,            # 0
            gtk.STOCK_DIALOG_INFO,      # 1
            gtk.STOCK_DIALOG_QUESTION,  # 2
            gtk.STOCK_DIALOG_WARNING,   # 3
            gtk.STOCK_DIALOG_ERROR]     # 4
