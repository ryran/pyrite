#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/01/27
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

from sys import stderr
from os import pipe, write, close
from shlex import split
from subprocess import Popen, PIPE, check_output


class Xface():
    """Woo."""
    
    def __init__(self, show_version=True):
        """Confirm we can run openssl."""
        
        try:
            vers = Popen(['openssl', 'version'], stdout=PIPE).communicate()[0]
        except:
            stderr.write("OpenSSL not found on your system.\n\n")
            raise
        
        # To show or not to show version info
        if show_version:
            stderr.write("{}\n".format(vers))
        
        # Class attributes
        self.stdin  = None      # Stores input text for openssl()
        self.stdout = None      # Stores stdout stream from subprocess
        self.stderr = None      # Stores stderr stream from subprocess
    
    
    # Main openssl interface method
    def openssl(
        self,
        action,         # One of: enc, dec
        passwd,         # Passphrase for symmetric
        cipher=None,    # Cipher in gpg-format; None = use default of aes256
        infile=None,    # Input file
        outfile=None,   # Output file
        ):
        """Build an openssl cmdline and then launch it, saving output appropriately.

        openssl() returns either True or False, depending on openssl's exit code.
        """
        
        if infile and infile == outfile:
            stderr.write("Same file for both input and output, eh? Is it going "
                         "to work? ... NOPE. Chuck Testa.\n")
            raise Exception("infile, outfile must be different")
        
        if cipher:  cipher = cipher.lower()
        if   cipher == None:            cipher = 'aes-256-cbc'
        elif cipher == '3des':          cipher = 'des-ede3-cbc'
        elif cipher == 'cast5':         cipher = 'cast5-cbc'
        elif cipher == 'blowfish':      cipher = 'bf-cbc'
        elif cipher == 'aes':           cipher = 'aes-128-cbc'
        elif cipher == 'aes192':        cipher = 'aes-192-cbc'
        elif cipher == 'aes256':        cipher = 'aes-256-cbc'
        elif cipher == 'camellia128':   cipher = 'camellia-128-cbc'
        elif cipher == 'camellia192':   cipher = 'camellia-192-cbc'
        elif cipher == 'camellia256':   cipher = 'camellia-256-cbc'
        else:                           cipher = 'aes-256-cbc'
        
        fd_in       = None
        fd_out      = None
        cmd         = ['openssl', cipher, '-a', '-pass']
        
        fd_in, fd_out = pipe() ; write(fd_out, passwd) ; close(fd_out)
        cmd.append('fd:{}'.format(fd_in))
        
        if action in 'enc':
            cmd.append('-salt')
        elif action in 'dec':
            cmd.append('-d')
        
        stderr.write("{}\n".format(cmd))
        
        # If working direct with files, setup our Popen instance with no stdin
        if infile:
            P = Popen(cmd, stdout=PIPE, stderr=PIPE)
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            P = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        # Time to communicate! Save output for later
        self.stdout, self.stderr = P.communicate(input=self.stdin)
        
        # Print stderr
        stderr.write(self.stderr)
        stderr.write("-----------\n")
        
        # Close os file descriptor
        close(fd_in)
        
        # Return based on openssl exit code
        if P.returncode == 0:
            return True
        else:
            return False

