#!/usr/bin/env python
#
# a4crypt v0.9.3 last mod 2012/01/10
# Latest version at <http://github.com/ryran/a8crypt>
# Copyright 2011, 2012 Ryan Sawhill <ryan@b19.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License <gnu.org/licenses/gpl.html> for more details.
#------------------------------------------------------------------------------
#
# TODO: SCRIPT docstring

from sys import stderr
from os import pipe, write, close
from shlex import split
from subprocess import Popen, PIPE
from collections import namedtuple
from getpass import getpass



class GpgInterface():
    """GPG/GPG2 interface for encryption/decryption.
    
    First thing: use subprocess module to call a gpg or gpg2 process, ensuring
    that one of them is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    To perform asymmetric (key-based) encryption or decryption, call
    GpgInterface.acrypt(). If encrypting, you must specify at least one recipient
    with recipients=''. Separate multiple recipients with spaces.
    
    For symmetric (passphrase-based) crypting, use GpgInterface.scrypt(). This
    requires specifying a passphrase to encrypt or decrypt.    
    
    Aside from the above, there are no differences between the two methods.
    
    Both require specifying a mode ('en' for encrypt; 'de' for decrypt) and can
    optionally take arguments of filenames to pass directly to gpg (for input &
    output). If these optional arguments are not used, input is read from
    GpgInterface.stdin (which must contain normal non-list data).
    
    Whether reading from GpgInterface.stdin or using filenames, both crypt
    methods save gpg's stdout & stderr streams to GpgInterface.stdout &
    GpgInterface.stderr and return a success status boolean (set by the exit
    code of gpg). Additionally, gpg stderr is written to sys.stderr regardless
    of how gpg exits.
        
    Both acrypt() and scrypt() have two more optional arguments:

    base64 (bool) -- Defaults to True, configuring gpg to produce base64-encoded
    (ASCII-armored) output.
        
    cipher -- Defaults to AES256, but other good/common choices are CAST5,
    Camellia256, Twofish, Blowfish. This argument corresponds to the gpg
    --cipher-algo option, which defaults to CAST5 and is case-insensitive.
    
    Security: GpgInterface.scrypt() takes a passphrase as an argument, but it
    never stores that passphrase on disk; the passphrase is passed to gpg via an
    os file descriptor.
    
    List of StdLib modules/methods used and how they're expected to be named:
        from sys import stderr
        from os import pipe, write, close
        from shlex import split
        from subprocess import Popen, PIPE
    """
    
    
    def __init__(self, show_version=True):
        """Confirm we can run gpg or gpg2."""
        
        try:
            vgpg = Popen(['gpg', '--version'], stdout=PIPE).communicate()[0]
            self.gpg = 'gpg --no-use-agent'
        except:
            try:
                vgpg = Popen(['gpg2', '--version'], stdout=PIPE).communicate()[0]
                self.gpg = 'gpg2'
            except:
                stderr.write("This program requires either gpg or gpg2, neither "
                             "of which were found on your system.\n\n")
                raise
        
        # To show or not to show (gpg --version output)
        if show_version:
            stderr.write("{0}\n".format(vgpg))
        
        # Class attributes
        self.stdin = None       # Stores input text for acrypt() or scrypt()
        self.stdout = None      # Stores stdout stream from gpg subprocess
        self.stderr = None      # Stores stderr stream from gpg subprocess
        # Convert 'gpg --opts' or 'gpg2 --opts' to simply 'GPG' or 'GPG2'
        self.gpgupper = self.gpg[:4].upper().strip()
    
    
    def __sanitycheck_crypt_args(self, caller, mode, infile=None, outfile=None, base64=True, recipients=None):
        """Sanity check arguments of GpgInterface's acrypt & scrypt methods.
        
        Intended to be called from the beginning of scrypt() and acrypt().
        """
        
        if mode not in {'en', 'de'}:
            stderr.write("Improper mode specified. Must be one of 'en' or 'de'.\n")
            raise Exception("Bad mode chosen")
        
        if infile and not outfile:
            stderr.write("You specified {0!r} as an input file but you didn't "
                         "specify an output file.\n".format(infile))
            raise Exception("Missing outfile")
        
        if infile and infile == outfile:
            stderr.write("Same file for both input and output, eh? Is it going "
                         "to work? ... NOPE. Chuck Testa.\n")
            raise Exception("infile, outfile must be different")
        
        if not infile and not self.stdin:
            stderr.write("You must either save input to GpgInterface.stdin, or "
                         "specify input & output files.\n")
            raise Exception("Missing input")
        
        if base64 not in {True, False}:
            stderr.write("Improper base64 setting specified. Must be either "
                         "True or False (default: True).\n")
            raise Exception("Bad base64 setting chosen")
        
        if caller in 'acrypt' and mode in 'en' and not recipients:
            stderr.write("You must specify at least one recipient with "
                         "recipients='XXX' (use spaces to separate).\n")
            raise Exception("Missing recipient")
    
    
    # ASYMMETRIC
    def acrypt(self, mode, infile=None, outfile=None, recipients=None, base64=True, cipher='aes256'):
        """Launch gpg in ASYMMETRIC mode (public/private keypairs).
        
        If encrypting, at least one recipient must be specified with
        recipients=''. Separate multiple recipients with spaces.
        """
        
        # Sanity checking of arguments and input
        self.__sanitycheck_crypt_args('acrypt', mode, infile, outfile, base64, recipients)
        
        # Encryption mode
        if mode in 'en':
            
            # Set ASCII-armored output option
            if base64:  a = '--armor'
            else:       a = ''
            
            # Prepare recipients by prepending each with -r
            recipients = recipients.replace(' ', ' -r ')
            
            # General encryption command -- reads stdin, writes stdout
            cmd = ("{gpg} {a} --cipher-algo {cipher} --encrypt -r {recip}"
                   .format(gpg=self.gpg[:4], a=a, cipher=cipher, recip=recipients))
        
        # Decryption mode
        elif mode in 'de':
            
            # General decryption command -- reads stdin, writes stdout
            cmd = "{gpg} -d".format(gpg=self.gpg)
        
        # If given filenames, add them to our cmd before finishing up
        if infile:
            cmd = "{cmd} -o {fout} {fin}".format(cmd=cmd, fout=outfile, fin=infile)
            return self.__crypt_launch(cmd, filemode=True)
        else:
            return self.__crypt_launch(cmd, filemode=False)
    
    
    # SYMMETRIC
    def scrypt(self, mode, passphrase, infile=None, outfile=None, base64=True, cipher='aes256'):
        """Launch gpg in SYMMETRIC mode (passphrase used for shared key).
        
        The same passphrase is required for both encryption and decryption.
        """
        
        # Sanity checking of arguments and input
        self.__sanitycheck_crypt_args('scrypt', mode, infile, outfile, base64)
        
        # Write our passphrase to an os file descriptor
        fd_in, fd_out = pipe()
        write(fd_out, passphrase) ; close(fd_out)
        
        # Encryption mode
        if mode in 'en':
            
            # Set ASCII-armored output option
            if base64:  a = '-a'
            else:       a = ''
            
            # General encryption command -- reads stdin, writes stdout
            cmd = ("{gpg} --batch --no-tty --yes --passphrase-fd {fd} "
                   "--cipher-algo {cipher} --symmetric --force-mdc {a}"
                   .format(gpg=self.gpg, fd=fd_in, cipher=cipher, a=a))
        
        # Decryption mode
        elif mode in 'de':
            
            # General decryption command -- reads stdin, writes stdout
            cmd = ("{gpg} --batch --no-tty --yes --passphrase-fd {fd} -d"
                   .format(gpg=self.gpg, fd=fd_in))
        
        # If given filenames, add them to our cmd before finishing up
        if infile:
            cmd = "{cmd} -o {fout} {fin}".format(cmd=cmd, fout=outfile, fin=infile)
            return self.__crypt_launch(cmd, filemode=True, fd=fd_in)
        else:
            return self.__crypt_launch(cmd, filemode=False, fd=fd_in)
    
    
    def __crypt_launch(self, cmd, filemode, fd=None):
        """Helper function to close the deal at the end of ?crypt()."""
        
        # If working direct with files, setup our Popen instance with no stdin
        if filemode:
            P = Popen(split(cmd), stdout=PIPE, stderr=PIPE)
        
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            P = Popen(split(cmd), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        # Time to communicate! Save output for later
        self.stdout, self.stderr = P.communicate(input=self.stdin)
        
        # Print gpg stderr
        stderr.write(self.stderr)        
        
        # Close os file descriptor if necessary
        if fd: close(fd)
        
        # Return based on gpg exit code
        if P.returncode == 0:
            return True
        else:
            return False



class AFourCrypt:
    """Provide cmdline wrapper for symmetric {en,de}cryption functions of GPG.
    
    This simply aims to make GPG1/GPG2 symmetric ASCII encryption in terminals
    easier and more fun. (Actually, this was just an excuse for a project in my
    first week of learning python, but hey. ...)
    
    Instantiate this class with color=False if you like spam.
    
    The actual encryption and decryption is handled by the GpgInterface class.
    So all this really does is setup some pretty colors for terminal output,
    prompt for user input & passphrases, pass it all over to
    GpgInterface.scrypt(), and display the output.
    """
    
    
    def __init__(self, color=True):
        """Decide GPG or GPG2 and define class attrs."""
        
        # Instantiate GpgInterface, which will check for gpg/gpg2
        self.g = GpgInterface(show_version=False)
        
        # Set default symmetric encryption cipher algo
        self.cipher = 'AES256'
        
        # Color makes it a lot easier to distinguish input & output
        Colors = namedtuple('Colors', 'Z B p r b g c')
        if color:
            self.c = Colors(       # Zero, Bold, purple, red, blue, green, cyan
                Z='\033[0m', B='\033[0m\033[1m', p='\033[1;35m',
                r='\033[1;31m', b='\033[1;34m', g='\033[1;32m', c='\033[0;36m')
        else:
            self.c = Colors('', '', '', '', '', '', '')
    
    
    def test_rawinput(self, prompt, *args):
        """Test user input. Keep prompting until recieve one of 'args'."""
        prompt = self.c.B + prompt + self.c.Z
        userinput = raw_input(prompt)
        while userinput not in args:
            userinput = raw_input("{0.r}Expecting one of {args}\n{prompt}"
                                  .format(self.c, args=args, prompt=prompt))
        return userinput
    
    
    def get_multiline_input(self, EOFstr, keeplastline=False):
        """Prompt for (and return) multiple lines of raw input.
        
        Stop prompting once receive a line containing only EOFstr. Return input
        minus that last line, unless run with keeplastline=True.
        """
        userinput = []
        userinput.append(raw_input())
        while userinput[-1] != EOFstr:
            userinput.append(raw_input())
        if not keeplastline:
            userinput.pop()
        return "\n".join(userinput)
    
    
    def get_passphrase(self, confirm=True):
        """Prompt for a passphrase until user enters same one twice.
        
        Skip the second confirmation prompt if run with confirm=False.
        """
        while True:
            pwd1 = getpass(prompt="{b}Carefully enter passphrase:{Z} "
                                  .format(**self.c._asdict()))
            while len(pwd1) == 0:
                pwd1 = getpass(prompt="{r}You must enter a passphrase:{Z} "
                                      .format(**self.c._asdict()))
            if not confirm: return pwd1
            pwd2 = getpass(prompt="{b}Repeat passphrase to confirm:{Z} "
                                  .format(**self.c._asdict()))
            if pwd1 == pwd2: return pwd1
            print("{r}The passphrases you entered did not match!{Z}"
                  .format(**self.c._asdict()))
    
    
    def load_main(self):
        """Load initial prompt and kick off all the other functions."""
        
        GPG = self.g.gpgupper
        # Banner/question
        print("{0.p}<{gpg}>".format(self.c, gpg=GPG)),
        print("{B}Choose: [{r}e{B}]ncrypt, [{r}d{B}]ecrypt, [{r}c{B}]ipher, "
              "or [{r}q{B}]uit{Z}".format(**self.c._asdict()))
        
        # Set mode with response to prompt
        mode = self.test_rawinput(": ", 'e', 'd', 'c', 'q')
        
        # QUIT MODE
        if mode in {'q', 'Q'}:
            
            if __name__ == "__main__":
                exit()
            return
        
        # CIPHER-SETTING MODE
        elif mode in 'c':
            
            print("{0.p}Set cipher algorithm for encryption{0.Z}\n"
                  "Good choices: AES256, Camellia256, Twofish, CAST5\n"
                  "Current setting: {0.r}{1}{0.Z} (gpg default: CAST5)\n"
                  "{0.p}Input new choice (case-insensitive) or Enter to cancel{0.B}"
                  .format(self.c, self.cipher))
            
            userinput = raw_input(": {0.Z}".format(self.c))
            if userinput:
                self.cipher = userinput
                print("encryption will be done with '--cipher-algo {0}'"
                      .format(userinput))
        
        # ENCRYPT MODE
        elif mode in 'e':
            
            # Get our message-to-be-encrypted from the user; save to variable
            print("{b}Type or paste message to be encrypted.\nEnd with line "
                  "containing only a triple-semicolon, i.e. {B};;;\n:{Z}"
                  .format(**self.c._asdict())),
            self.g.stdin = self.get_multiline_input(';;;')
            print
            
            # Get passphrase from the user
            passphrase = self.get_passphrase(confirm=True)
            
            # Launch our subprocess and print the output
            retval = self.g.scrypt('en', passphrase, cipher=self.cipher)
            
            # If gpg succeeded, print output
            if retval:
                print("{0.g}\nEncrypted message follows:\n\n{0.c}{output}{0.Z}"
                      .format(self.c, output=self.g.stdout))
            
            # Otherwise, user must have picked a bad cipher-algo
            else:
                print("{0.r}Looks like {gpg} didn't like the cipher-algo you "
                      "entered.\nChoose a different one.{0.Z}"
                      .format(self.c, gpg=GPG.lower()))
        
        # DECRYPT MODE
        elif mode in 'd':
            
            # Get our encrypted message from the user; save to variable
            print("{b}Paste gpg-encrypted message to be decrypted.\n{B}:{Z}"
                  .format(**self.c._asdict())),
            self.g.stdin = self.get_multiline_input('-----END PGP MESSAGE-----',
                                                    keeplastline=True)
            print
            
            # Get passphrase from the user
            passphrase = self.get_passphrase(confirm=False)
            
            # Launch our subprocess
            retval = self.g.scrypt('de', passphrase)
            
            while True:
                
                # If gpg succeeded, print output
                if retval:
                    print("{0.g}\nDecrypted message follows:\n\n{0.c}{output}"
                          "{0.Z}\n".format(self.c, output=self.g.stdout))
                    break
                
                # Otherwise, print error and give option to try again
                else:
                    print("{0.r}Error in decryption process! Try again with a "
                          "different passphrase?{0.Z}".format(self.c))
                    tryagain = self.test_rawinput("[y/n]: ", 'y', 'n')
                    if tryagain in 'n': break
                    passphrase = self.get_passphrase(confirm=False)
                    retval = self.g.scrypt('de', passphrase)



# BEGIN
if __name__ == "__main__":

    from sys import argv
    if len(argv) == 2 and (argv[1] == '--nocolor' or argv[1] == '-n'):
        a4 = AFourCrypt(color=False)
    
    elif len(argv) == 1:
        a4 = AFourCrypt()
    
    else:
        print("Run with no arguments to get interactive prompt.\n"
              "Optional argument: --nocolor (alias: -n)")
        exit()
    
    while True:
        a4.load_main()
    
