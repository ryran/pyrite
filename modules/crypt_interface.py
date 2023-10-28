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

from os import pipe, write, close
from shlex import split
from subprocess import Popen, PIPE, check_output
from sys import stderr
from time import sleep


def flatten_list_to_stderr(lines):
    stderr.write("-" * 79 + "\n")
    for item in lines:
        stderr.write(item + " ")
    stderr.write("\n\n")


class Gpg:
    """GPG interface for encryption/decryption/signing/verifying.
    
    First thing: use subprocess module to call a gpg process, ensuring
    that it is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    See the docstring for the main method -- gpg() -- for next steps.
    
    Security: Xface.gpg() can take a passphrase for symmetric enc/dec as
    an argument, but it never stores that passphrase on disk; the passphrase is
    passed to gpg via an os file descriptor. If any access to your secret key is
    required, gpg() invokes gpg with gpg-agent enabled.
    
    """

    def __init__(self, show_version=True):
        """Confirm we can run gpg."""

        try:
            self.vers = Popen(['gpg', '--version'], stdout=PIPE).communicate()[0]
            self.GPG_BINARY = 'gpg'
        except:
            stderr.write("gpg not found on your system.\n\n")
            raise

        # To show or not to show version info
        if show_version:
            stderr.write("{}\n".format(self.vers))

        # I/O dictionary obj
        self.io = dict(
            stdin='',  # Stores input text for subprocess
            stdout='',  # Stores stdout stream from subprocess
            stderr=0,  # Stores tuple of r/w file descriptors for stderr stream
            gstatus=0,  # Stores tuple of r/w file descriptors for gpg-status stream
            infile=0,  # Input filename for subprocess
            outfile=0)  # Output filename for subprocess

        self.childprocess = None

    # Main gpg interface method
    def gpg(
            self,
            action=None,  # One of: enc, dec, embedsign, clearsign, detachsign, verify
            encsign=False,  # Add '--sign' when encrypting?
            digest=None,  # One of: sha256, sha1, etc; None == use gpg defaults
            localuser=None,  # Value passed to --local-user to set default key for signing, etc
            base64=True,  # Add '--armor' when encrypting/signing?
            symmetric=False,  # Add '--symmetric'?
            passwd=None,  # Passphrase for symmetric
            asymmetric=False,  # Add '--encrypt'?
            recip=None,  # Recipients for asymmetric (semicolon-delimited)
            enctoself=False,  # Add first id from secret keyring as recipient?
            cipher=None,  # One of: aes256, 3des, etc; None == use gpg defaults
            verbose=False,  # Add '--verbose'?
            alwaystrust=False,  # Add '--trust-model always'?
            yes=True  # Add '--yes'? (will overwrite files)
    ):
        """Build a gpg cmdline and then launch gpg, saving output appropriately.
        
        This method inspects the contents of class attr 'io' -- a dict object that should
        contain all the following keys, at least initialized to 0 or '':
            stdin       # Input text for subprocess
            infile      # Input filename for subprocess, in place of stdin
            outfile     # Output filename if infile was given
        io['infile'] should contain a filename OR be set to 0, in which case io['stdin']
        must contain the input data. If using infile, outfile is not necessarily required,
        but it's probably a good idea unless you're doing sign-only.
        
        Additional highlights:
        recip: Use a single semicolon to separate recipients. Superfluous leading/
            trailing semicolons or spaces are stripped.
        enctoself: Self is assumed to be first key returned by gpg --list-secret-keys;
            however, if localuser is provided, that is used as self instead.
        
        Re gpg-agent:
        If symmetric & passwd are specified when encrypting or decrypting (and
        asymmetric is not), gpg-agent isn't called. In all other scenarios requiring a
        passphrase--whether encrypting, decrypting, or signing--gpg-agent will be
        invoked.
        
        Whether reading input from infile or stdin, each gpg command's stdout &
        stderr streams are saved to io['stdout'] and io['stderr'].
        
        Nothing is returned -- it is expected that this method is being run as a separate
        thread and therefore the responsibility to determine success or failure falls on
        the caller (i.e., by examining the Popen instance's returncode attribute).
        
        """

        if self.io['infile'] and self.io['infile'] == self.io['outfile']:
            stderr.write("Same file for both input and output, eh? Is it going "
                         "to work? ... NOPE. Chuck Testa.\n")
            raise Exception("infile, outfile must be different")

        fd_pwd_R = None
        fd_pwd_W = None
        useagent = True
        cmd = [self.GPG_BINARY]

        if self.io['gstatus']:
            # Status to file descriptor option
            cmd.append('--status-fd')
            cmd.append(str(self.io['gstatus'][1]))

        # Setup passphrase file descriptor for symmetric enc/dec
        if (action in 'enc' and symmetric and passwd and not encsign) or (
                action in 'dec' and symmetric and passwd):
            useagent = False
            fd_pwd_R, fd_pwd_W = pipe()
            write(fd_pwd_W, passwd)
            close(fd_pwd_W)
            cmd.append('--passphrase-fd')
            cmd.append(str(fd_pwd_R))

        # Encrypt opts
        if action in 'enc':
            if encsign:
                cmd.append('--sign')
            if digest:
                cmd.append('--digest-algo')
                cmd.append(digest)
            if symmetric:
                cmd.append('--symmetric')
                cmd.append('--force-mdc')
            if asymmetric:
                cmd.append('--encrypt')
            if cipher:
                cmd.append('--cipher-algo')
                cmd.append(cipher)
            if enctoself:
                cmd.append('--recipient')
                if localuser:
                    cmd.append(localuser)
                else:
                    cmd.append(self.get_gpg_default_key())
            if recip:
                while recip[-1] == ' ' or recip[-1] == ';':
                    recip = recip.strip()
                    recip = recip.strip(';')
                for r in recip.split(';'):
                    cmd.append('--recipient')
                    cmd.append(r)

        # Decrypt opts
        elif action in 'dec':
            cmd.append('--decrypt')

        # Sign opts
        elif action in {'embedsign', 'clearsign', 'detachsign'}:
            if action in 'embedsign':
                cmd.append('--sign')
            elif action in 'clearsign':
                cmd.append('--clearsign')
            elif action in 'detachsign':
                cmd.append('--detach-sign')
            if digest:
                cmd.append('--digest-algo')
                cmd.append(digest)

        # Verify opts
        elif action in 'verify':
            cmd.append('--verify')

        # Wouldn't hurt to use armor for all, but it only works with these 3
        if action in {'enc', 'embedsign', 'detachsign'}:
            if base64:
                cmd.append('--armor')

        # Action-independent opts
        if useagent:
            if self.GPG_BINARY in 'gpg':
                cmd.append('--use-agent')
        else:
            if self.GPG_BINARY in 'gpg':
                cmd.append('--no-use-agent')
            else:
                cmd.append('--batch')
        if localuser:
            cmd.append('--local-user')
            cmd.append(localuser)
        cmd.append('--no-tty')
        if yes:
            cmd.append('--yes')
        if alwaystrust:
            cmd.append('--trust-model')
            cmd.append('always')
        if verbose:
            cmd.append('--verbose')
        if self.io['outfile']:
            cmd.append('--output')
            cmd.append(self.io['outfile'])
        if self.io['infile']:
            cmd.append(self.io['infile'])

        # Print a separator + the command-arguments to stderr
        flatten_list_to_stderr(cmd)

        # If working direct with files, set up our Popen instance with no stdin
        if self.io['infile']:
            self.childprocess = Popen(cmd, stdout=PIPE, stderr=self.io['stderr'][1])
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            b = self.io['stderr']
            self.childprocess = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=b[1])

        # Time to communicate! Save output for later
        b = self.io['stdin'].encode('utf-8')
        self.io['stdout'] = self.childprocess.communicate(input=b)[0]

        # Clear stdin from our dictionary asap, in case it's huge
        self.io['stdin'] = ''

        # Close os file descriptors
        if fd_pwd_R:
            close(fd_pwd_R)
        sleep(0.1)  # Sleep a bit to ensure everything gets read
        close(self.io['stderr'][1])
        if self.io['gstatus']:
            close(self.io['gstatus'][1])

    def get_gpg_default_key(self):
        """Return key id of first secret key in gpg keyring."""
        cmd = split("{} --list-secret-keys --with-colons --fast-list-mode".format(self.GPG_BINARY))
        return check_output(cmd).split(':', 5)[4]


class Openssl:
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
            stdin='',  # Stores input text for subprocess
            stdout='',  # Stores stdout stream from subprocess
            stderr=0,  # Stores tuple of r/w file descriptors for stderr stream
            infile=0,  # Input filename for subprocess
            outfile=0)  # Output filename for subprocess

        self.childprocess = None

    # Main openssl interface method
    def openssl(
            self,
            action,  # One of: enc, dec
            passwd,  # Passphrase for symmetric
            base64=True,  # Add '-a' when encrypting/decrypting?
            cipher=None,  # Cipher in gpg-format; None = use aes256
    ):
        """Build an openssl cmdline and then launch it, saving output appropriately.

        This method inspects the contents of class attr 'io' -- a dict object that should
        contain all the following keys, at least initialized to 0 or '':
            stdin       # Input text for subprocess
            infile      # Input filename for subprocess, in place of stdin
            outfile     # Output filename -- required if infile was given
        io['infile'] should contain a filename OR be set to 0, in which case io['stdin']
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

        if cipher:
            cipher = cipher.lower()
        if cipher is None:
            cipher = 'aes-256-cbc'
        elif cipher == '3des':
            cipher = 'des-ede3-cbc'
        elif cipher == 'cast5':
            cipher = 'cast5-cbc'
        elif cipher == 'blowfish':
            cipher = 'bf-cbc'
        elif cipher == 'aes':
            cipher = 'aes-128-cbc'
        elif cipher == 'aes192':
            cipher = 'aes-192-cbc'
        elif cipher == 'aes256':
            cipher = 'aes-256-cbc'
        elif cipher == 'camellia128':
            cipher = 'camellia-128-cbc'
        elif cipher == 'camellia192':
            cipher = 'camellia-192-cbc'
        elif cipher == 'camellia256':
            cipher = 'camellia-256-cbc'
        # else:                           cipher = 'aes-256-cbc'

        fd_pwd_R = None
        fd_pwd_W = None
        cmd = ['openssl', cipher, '-md', 'sha256', '-pass']

        # Setup passphrase file descriptors
        fd_pwd_R, fd_pwd_W = pipe()
        write(fd_pwd_W, passwd)
        close(fd_pwd_W)
        cmd.append('fd:{}'.format(fd_pwd_R))

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

        # Print a separator + the command-arguments to stderr
        flatten_list_to_stderr(cmd)

        # If working direct with files, set up our Popen instance with no stdin
        if self.io['infile']:
            self.childprocess = Popen(cmd, stdout=PIPE, stderr=self.io['stderr'][1])
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            self.childprocess = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=self.io['stderr'][1])

        # Time to communicate! Save output for later
        b = self.io['stdin'].encode('utf-8')
        self.io['stdout'] = self.childprocess.communicate(input=b)[0]

        # Clear stdin from our dictionary asap, in case it's huge
        self.io['stdin'] = ''

        # Close os file descriptors
        close(fd_pwd_R)
        sleep(0.1)  # Sleep a bit to ensure everything gets read
        close(self.io['stderr'][1])
