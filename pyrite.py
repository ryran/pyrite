#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/08
# Latest version at <http://github.com/ryran/pyrite>
# Copyright 2012 Ryan Sawhill <ryan@b19.org>
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
#
# TODO:
#   * Icons for for encrypt, decrypt, sign, verify buttons, application
#   * Undo stack. Blech. Kill me.
#   * Update notifications
#   * BUG: First drag/drop onto FileChooserButton fails; 2nd, 3rd, etc succeed.
#
#------------------------------------------------------------------------------


import modules.core


if __name__ == "__main__":
    
    FeS2 = modules.core.Pyrite()
    try:
        FeS2.main()
    except KeyboardInterrupt:
        print
        exit()
    except:
        raise
    
