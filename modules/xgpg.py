#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/01
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
#from multiprocessing import Process, Pipe
#from time import sleep


class Xface():
    """GPG/GPG2 interface for encryption/decryption/signing/verifying.
    
    First thing: use subprocess module to call a gpg or gpg2 process, ensuring
    that one of them is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    See the docstring for the main method -- gpg() -- for next steps.
    
    Security: Xface.gpg() can take a passphrase for symmetric enc/dec as
    an argument, but it never stores that passphrase on disk; the passphrase is
    passed to gpg via an os file descriptor. If any access to your secret key is
    required, gpg() invokes gpg/gpg2 with gpg-agent enabled.
    
    """
    
    
    def __init__(self, show_version=True, firstchoice='gpg2'):
        """Confirm we can run gpg or gpg2."""
        
        def gpg1():
            self.vers = Popen(['gpg', '--version'], stdout=PIPE).communicate()[0]
            self.GPG = 'gpg'
        
        def gpg2():
            self.vers = Popen(['gpg2', '--version'], stdout=PIPE).communicate()[0]
            self.GPG = 'gpg2'
        
        if firstchoice == 'gpg':
            try: gpg1()
            except:
                try: gpg2()
                except:
                    stderr.write("gpg, gpg2 not found on your system.\n\n")
                    raise
        else:
            try: gpg2()
            except:
                try: gpg1()
                except:
                    stderr.write("gpg, gpg2 not found on your system.\n\n")
                    raise
        
        # To show or not to show version info
        if show_version:
            stderr.write("{}\n".format(self.vers))
            
    
    # Main gpg interface method
    def gpg(
        self,
        io,                 # Dictionary containing stdin, infile, outfile
        action=     None,   # One of: enc, dec, embedsign, clearsign, detachsign, verify
        encsign=    False,  # Add '--sign' when encrypting?
        digest=     None,   # One of: sha256, sha1, etc; None == use gpg defaults
        localuser=  None,   # Value passed to --local-user to set default key for signing, etc
        base64=     True,   # Add '--armor' when encrypting/signing?
        symmetric=  False,  # Add '--symmetric'?
        passwd=     None,   # Passphrase for symmetric
        asymmetric= False,  # Add '--encrypt'?
        recip=      None,   # Recipients for asymmetric (semicolon-delimited)
        enctoself=  False,  # Add first id from secret keyring as recipient?
        cipher=     None,   # One of: aes256, 3des, etc; None == use gpg defaults
        verbose=    False,  # Add '--verbose'?
        alwaystrust=False,  # Add '--trust-model always'?
        yes=        True    # Add '--yes'? (will overwrite files)
        ):
        """Build a gpg cmdline and then launch gpg/gpg2, saving output appropriately.
        
        The io dict object should contain at least one of these keys:
            stdin       # Input text for subprocess
            infile      # Input filename for subprocess, in place of stdin
            outfile     # Output filename if infile was given (even then, it's optional)
        If using infile, outfile is not necessarily required, but it's probably a good
        idea unless you're doing sign-only.
        
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
        
        Finally, gpg() returns a tuple: the True/False return-value of the subprocess,
        and the newly modified io object.
        """
        
        if io['infile'] and io['infile'] == io['outfile']:
            stderr.write("Same file for both input and output, eh? Is it going "
                         "to work? ... NOPE. Chuck Testa.\n")
            raise Exception("infile, outfile must be different")
        
        fd_in       = None
        fd_out      = None
        useagent    = True
        cmd         = [self.GPG]
        
        # Setup passphrase file descriptor for symmetric enc/dec
        if (action in 'enc' and symmetric and passwd and not encsign) or (
            action in 'dec' and symmetric and passwd):
                useagent=False
                fd_in, fd_out = pipe() ; write(fd_out, passwd) ; close(fd_out)
                cmd.append('--passphrase-fd')
                cmd.append(str(fd_in))
        
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
                    cmd.append(self.get_gpgdefaultkey())
            if recip:
                while recip[-1] == ' ' or recip[-1] == ';':
                    recip = recip.strip()
                    recip = recip.strip(';')
                for r in recip.split(';'):
                    cmd.append('--recipient')
                    cmd.append(r)
        
        # Decrypt opts
        elif action in 'dec':   cmd.append('--decrypt')
        
        # Sign opts
        elif action in {'embedsign', 'clearsign', 'detachsign'}:
            if action in 'embedsign':       cmd.append('--sign')
            elif action in 'clearsign':     cmd.append('--clearsign')
            elif action in 'detachsign':    cmd.append('--detach-sign')
            if digest:
                cmd.append('--digest-algo')
                cmd.append(digest)
        
        # Verify opts
        elif action in 'verify':        cmd.append('--verify')
        
        # Wouldn't hurt to use armor for all, but it only works with these 3
        if action in {'enc', 'embedsign', 'detachsign'}:
            if base64:
                cmd.append('--armor')
        
        # Action-independent opts
        if useagent:
            if self.GPG in 'gpg':   cmd.append('--use-agent')
        else:
            if self.GPG in 'gpg':   cmd.append('--no-use-agent')
            else:                   cmd.append('--batch')
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
        if io['outfile']:
            cmd.append('--output')
            cmd.append(io['outfile'])
        if io['infile']:
            cmd.append(io['infile'])
        
        stderr.write("{}\n".format(cmd))
        
        # If working direct with files, setup our Popen instance with no stdin
        if io['infile']:
            P = Popen(cmd, stdout=PIPE, stderr=PIPE)
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            P = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        # Time to communicate! Save output for later
        io['stdout'], io['stderr'] = P.communicate(input=io['stdin'])
        
        # Clear stdin from our dictionary asap, in case it's huge
        io['stdin'] = 0
        
        # Print gpg stderr
        stderr.write(io['stderr'])
        stderr.write("-----------\n")
        
        # Close os file descriptor if necessary
        if fd_in:  close(fd_in)
        
        # Return based on gpg exit code
        if P.returncode == 0:   ret = True
        else:                   ret = False
        return (ret, io)
    
    
    def get_gpgdefaultkey(self):
        """Return key id of first secret key in gpg keyring.""" 
        return check_output(split(
            "{} --list-secret-keys --with-colons --fast-list-mode"
            .format(self.GPG))).split(':', 5)[4]
    
