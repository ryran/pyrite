#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/06
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
    """OpenSSL interface for encryption/decryption.
    
    First thing: use subprocess module to call an openssl process, ensuring it
    is available on the system; if not, of course we have to quit (raise
    exception). Either way, that's all for __init__.
    
    See the docstring for the main method -- openssl() -- for next steps.
    
    Security: Xface.openssl() can take a passphrase for symmetric enc/dec as
    an argument, but it never stores that passphrase on disk; the passphrase is
    passed to openssl via an os file descriptor.
    
    """
    
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
        
        # I/O dictionary obj
        self.io = dict(
            stdin='',   # Input text for subprocess
            stdout='',  # Stdout stream from subprocess
            stderr='',  # Stderr stream from subprocess
            infile=0,   # Input filename for subprocess
            outfile=0)  # Output filename for subprocess
        
        self.childprocess = None
    
    
    # Main openssl interface method
    def openssl(
        self,
        action,         # One of: enc, dec
        passwd,         # Passphrase for symmetric
        base64=True,    # Add '-a' when encrypting/decrypting?
        cipher=None,    # Cipher in gpg-format; None = use aes256
        ):
        """Build an openssl cmdline and then launch it, saving output appropriately.

        This method inspects the contents of class attr 'io' -- a dict object that should
        contain all of the following keys, at least initialized to 0 or '':
            stdin       # Input text for subprocess
            infile      # Input filename for subprocess, in place of stdin
            outfile     # Output filename -- required if infile was given
        io['infile'] should contain a filename OR be set to 0, in which case io'[stdin']
        must contain the input data.
        
        Whether reading input from infile or stdin, each openssl command's stdout &
        stderr streams are saved to io['stdout'] and io['stderr'].
        
        Nothing is returned -- it is expected that this method is being run as a separate
        thread and therefore the responsibility to determine success or failure falls on
        the caller (i.e., by examining the Popen instance's returncode attribute).
        
        """
        
        if self.io['infile'] and self.io['infile'] == self.io['outfile']:
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
        #else:                           cipher = 'aes-256-cbc'
        
        fd_in       = None
        fd_out      = None
        cmd         = ['openssl', cipher, '-pass']
        
        fd_in, fd_out = pipe() ; write(fd_out, passwd) ; close(fd_out)
        cmd.append('fd:{}'.format(fd_in))
        
        if base64:
            cmd.append('-a')
        if action in 'enc':
            cmd.append('-salt')
        elif action in 'dec':
            cmd.append('-d')
        if self.io['infile']:
            cmd.append('-in')
            cmd.append(self.io['infile'])
            cmd.append('-out')
            cmd.append(self.io['outfile'])
        
        stderr.write("{}\n".format(cmd))
        
        # If working direct with files, setup our Popen instance with no stdin
        if self.io['infile']:
            self.childprocess = Popen(cmd, stdout=PIPE, stderr=PIPE)
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            self.childprocess = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        # Time to communicate! Save output for later
        self.io['stdout'], self.io['stderr'] = self.childprocess.communicate(input=self.io['stdin'])
        
        # Print stderr
        stderr.write(self.io['stderr'])
        stderr.write("-----------\n")
        
        # Close os file descriptor
        close(fd_in)
        

