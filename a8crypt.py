#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# a8crypt v0.9.5 last mod 2012/01/11
# Latest version at <http://github.com/ryran/a8crypt>
# Copyright 2012 Ryan Sawhill <ryan@b19.org>
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
# TODO: Learn enough about GTK to replace Glade xml with GTK calls

# Modules from the Standard Library
import gtk
from pango import FontDescription
from sys import stderr
from os import access, R_OK
from os import pipe, write, close
from shlex import split
from subprocess import Popen, PIPE, check_output


class GpgInterface():
    """GPG/GPG2 interface for encryption/decryption.
    
    First thing: use subprocess module to call a gpg or gpg2 process, ensuring
    that one of them is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    For symmetric (passphrase-based) encryption & decryption, use
    GpgInterface.scrypt(). This requires specifying a passphrase.
    
    To perform asymmetric (key-based) encryption or decryption, call
    GpgInterface.acrypt(). If encrypting, you must specify at least one recipient
    with recipients=''. Separate multiple recipients with semicolons.
    
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
        
    Both acrypt() and scrypt() have three more optional arguments:

    base64 (bool) -- Defaults to True, configuring gpg to produce base64-encoded
    (ASCII-armored) output.
        
    cipher -- If not specified, gpg decides which cipher to use (which will
    depend on your gpg settings and the preferences of the pubkeys you're using
    for encryption). Good or common choices: AES256, Twofish, Camellia256,
    AES192, Camellia192, CAST5, Blowfish. This argument corresponds to the gpg
    --cipher-algo option, which is case-insensitive, by the way.
    
    sign (bool) -- Defaults to False; setting to True will tell gpg to sign the
    encrypted output using your secret key.
    
    Security: GpgInterface.scrypt() takes a passphrase as an argument, but it
    never stores that passphrase on disk; the passphrase is passed to gpg via an
    os file descriptor.
    
    List of StdLib modules/methods used and how they're expected to be named:
        from sys import stderr
        from os import pipe, write, close
        from shlex import split
        from subprocess import Popen, PIPE, check_output
    """
    
    
    def __init__(self, show_version=True):
        """Confirm we can run gpg or gpg2."""
        
        try:
            vgpg = Popen(['gpg2', '--version'], stdout=PIPE).communicate()[0]
            self.GPG = 'gpg2'
        except:
            try:
                vgpg = Popen(['gpg', '--version'], stdout=PIPE).communicate()[0]
                self.GPG = 'gpg'
            except:
                stderr.write("This program requires either gpg or gpg2, neither "
                             "of which were found on your system.\n\n")
                raise
        
        # To show or not to show (gpg --version output)
        if show_version:
            stderr.write("{}\n".format(vgpg))
        
        # Class attributes
        self.stdin = None       # Stores input text for acrypt() or scrypt()
        self.stdout = None      # Stores stdout stream from gpg subprocess
        self.stderr = None      # Stores stderr stream from gpg subprocess
    
    
    # Generic filetype test to see if a file contains binary data or simply text
    def test_file_isbinary(self, filename):
        """Utilize nix file cmd to determine if filename is binary or text."""
        output = check_output(split("file -b -e soft {}".format(filename)))
        if output[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    
    # Sanity check arguments of scrypt or acrypt
    def __sanitycheck_crypt_args(self, caller, mode, infile=None, outfile=None,
                                 base64=True, sign=False, recipients=None):
        
        if mode not in {'en', 'de'}:
            stderr.write("Improper mode specified. Must be one of 'en' or 'de'.\n")
            raise Exception("Bad mode chosen")
        
        if infile and not outfile:
            stderr.write("You specified {!r} as an input file but you didn't "
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
        
        if sign not in {True, False}:
            stderr.write("Improper sign setting specified. Must be either "
                         "True or False (default: False).\n")
            raise Exception("Bad sign setting chosen")
        
        if caller in 'acrypt' and mode in 'en' and not recipients:
            stderr.write("You must specify at least one recipient with "
                         "recipients='XXX' (use semicolons to separate).\n")
            raise Exception("Missing recipient")
    
    
    # Convert scrypt or acrypt encryption-mode arguments into gpg options
    def __prep_encrypt_opts(self, base64, cipher, sign):
        # ASCII-armor
        if base64:  a = '--armor'
        else:       a = ''
        # cipher-algo
        if cipher:  cipher = "--cipher-algo {}".format(cipher)
        else:       cipher = ''
        # encrypt+sign
        if sign:    sign = '--sign'
        else:       sign = ''
        return a, cipher, sign
    
    
    # SYMMETRIC
    def scrypt(self, mode, passphrase, infile=None, outfile=None, base64=True,
               cipher=None, sign=False):
        """Launch gpg in SYMMETRIC mode (passphrase used for shared key).
        
        The same passphrase is required for both encryption and decryption.
        """
        
        # Sanity checking of arguments and input
        self.__sanitycheck_crypt_args('scrypt', mode, infile, outfile, base64,
                                      sign)
        
        # Set gpg1-specific options for symmetric
        GPG = self.GPG
        if GPG in 'gpg':    GPG = 'gpg --no-use-agent'
        
        # Write our passphrase to an os file descriptor
        fd_in, fd_out = pipe()
        write(fd_out, passphrase) ; close(fd_out)
        
        # Encryption mode
        if mode in 'en':
            
            # Convert args to gpg options
            a, cipher, sign = self.__prep_encrypt_opts(base64, cipher, sign)
            
            # General encryption command -- reads stdin, writes stdout
            cmd = ("{gpg} -v --symmetric {a} --force-mdc {cipher} {sign} "
                   "--passphrase-fd {fd} --batch --no-tty --yes"
                   .format(gpg=GPG, a=a, cipher=cipher, sign=sign, fd=fd_in))
        
        # Decryption mode
        elif mode in 'de':
            
            # General decryption command -- reads stdin, writes stdout
            cmd = ("{gpg} -v --decrypt --passphrase-fd {fd} --batch --no-tty --yes"
                   .format(gpg=GPG, fd=fd_in))
        
        # If given filenames, add them to our cmd before finishing up
        if infile:
            cmd = "{cmd} -o {fout} {fin}".format(cmd=cmd, fout=outfile, fin=infile)
            return self.__crypt_launch(cmd, filemode=True, fd=fd_in)
        else:
            return self.__crypt_launch(cmd, filemode=False, fd=fd_in)
    
    
    # ASYMMETRIC
    def acrypt(self, mode, recipients=None, infile=None, outfile=None,
               base64=True, cipher=None, sign=False):
        """Launch gpg in ASYMMETRIC mode (public/private keypairs).
        
        If encrypting, at least one recipient must be specified with
        recipients=''. Use a semicolon to separate multiple recipients.
        """
        
        # Sanity checking of arguments and input
        self.__sanitycheck_crypt_args('acrypt', mode, infile, outfile, base64,
                                      sign, recipients)
        
        # Set gpg1-specific options for asymmetric
        GPG = self.GPG
        if GPG in 'gpg':    GPG = 'gpg --use-agent'
        
        # Encryption mode
        if mode in 'en':
            
            # Convert args to gpg options
            a, cipher, sign = self.__prep_encrypt_opts(base64, cipher, sign)
            
            # Prepare recipients by stripping extraneous semicolons and then
            #   replacing each remaining semicolon with '-r'
            while recipients[-1] == ' ' or recipients[-1] == ';':
                recipients = recipients.strip()
                recipients = recipients.strip(';')
            recipients = recipients.replace(';', ' -r ')
        
            # General encryption command -- reads stdin, writes stdout
            cmd = ("{gpg} -v --encrypt {a} {cipher} {sign} -r {recip} "
                   "--batch --no-tty --yes"
                   .format(gpg=GPG, a=a, cipher=cipher, sign=sign, recip=recipients))
        
        # Decryption mode
        elif mode in 'de':
            
            # General decryption command -- reads stdin, writes stdout
            cmd = "{gpg} -v --decrypt --batch --no-tty --yes".format(gpg=GPG)
        
        # If given filenames, add them to our cmd before finishing up
        if infile:
            cmd = "{cmd} -o {fout} {fin}".format(cmd=cmd, fout=outfile, fin=infile)
            return self.__crypt_launch(cmd, filemode=True)
        else:
            return self.__crypt_launch(cmd, filemode=False)
    
    
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
        stderr.write("-----------\n")
        
        # Close os file descriptor if necessary
        if fd: close(fd)
        
        # Return based on gpg exit code
        if P.returncode == 0:
            return True
        else:
            return False



class XmlForGtkBuilder:
    def __init__(self):
        """Store the Glade XML that GtkBuilder will use to build our GUI."""
        self.inline_gladexmlfile = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="2.24"/>
  <!-- interface-naming-policy project-wide -->
  <object class="GtkImage" id="image1">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-media-forward</property>
  </object>
  <object class="GtkImage" id="image2">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-media-rewind</property>
  </object>
  <object class="GtkImage" id="image3">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-save-as</property>
  </object>
  <object class="GtkImage" id="image4">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-open</property>
  </object>
  <object class="GtkImage" id="image5">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-clear</property>
  </object>
  <object class="GtkImage" id="image6">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-save</property>
  </object>
  <object class="GtkImage" id="image7">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-clear</property>
  </object>
  <object class="GtkListStore" id="liststore1">
    <columns>
      <!-- column-name Text -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">Default</col>
      </row>
      <row>
        <col id="0" translatable="yes">AES256</col>
      </row>
      <row>
        <col id="0" translatable="yes">Twofish</col>
      </row>
      <row>
        <col id="0" translatable="yes">Camellia256</col>
      </row>
      <row>
        <col id="0" translatable="yes">AES192</col>
      </row>
      <row>
        <col id="0" translatable="yes">Camellia192</col>
      </row>
      <row>
        <col id="0" translatable="yes">AES</col>
      </row>
      <row>
        <col id="0" translatable="yes">Camellia128</col>
      </row>
      <row>
        <col id="0" translatable="yes">CAST5</col>
      </row>
      <row>
        <col id="0" translatable="yes">Blowfish</col>
      </row>
      <row>
        <col id="0" translatable="yes">3DES</col>
      </row>
    </data>
  </object>
  <object class="GtkWindow" id="window1">
    <property name="can_focus">False</property>
    <property name="title" translatable="yes">a8crypt</property>
    <property name="window_position">center</property>
    <property name="default_height">340</property>
    <signal name="destroy" handler="on_window1_destroy" swapped="no"/>
    <child>
      <object class="GtkVBox" id="vbox1">
        <property name="visible">True</property>
        <property name="can_focus">False</property>
        <child>
          <object class="GtkMenuBar" id="menubar1">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <child>
              <object class="GtkMenuItem" id="menuitem1">
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_File</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="filemenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_encrypt">
                        <property name="label" translatable="yes">_Encrypt</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="image">image1</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_encrypt_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_decrypt">
                        <property name="label" translatable="yes">_Decrypt</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="image">image2</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_decrypt_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="separatormenuitem1">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_save">
                        <property name="label" translatable="yes">_Save text buffer</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="tooltip_text" translatable="yes">Save contents of window to a text file</property>
                        <property name="use_underline">True</property>
                        <property name="image">image3</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_save_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_open">
                        <property name="label" translatable="yes">_Open file</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Choose a filename to pass directly to gpg as input

File WILL NOT be loaded into the text buffer</property>
                        <property name="use_underline">True</property>
                        <property name="image">image4</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_open_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="separatormenuitem2">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_quit">
                        <property name="label">gtk-quit</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_quit_activate" swapped="no"/>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
            <child>
              <object class="GtkMenuItem" id="menuitem2">
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">Edi_t</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="editmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_cut">
                        <property name="label">gtk-cut</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_cut_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_copy">
                        <property name="label">gtk-copy</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_copy_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_paste">
                        <property name="label">gtk-paste</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_paste_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_clear">
                        <property name="label">Cle_ar</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Resets all buffers</property>
                        <property name="use_underline">True</property>
                        <property name="image">image7</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_clear_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="sep1">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_savecipherpref">
                        <property name="label" translatable="yes">_Make cipher selection default</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Attempts to modify the a8crypt script to permanently change the default cipher setting

This will fail if a8crypt is not writable</property>
                        <property name="use_underline">True</property>
                        <property name="image">image6</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_savecipherpref_activate" swapped="no"/>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
            <child>
              <object class="GtkMenuItem" id="menuitem4">
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_Help</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="helpmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_about">
                        <property name="label">gtk-about</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_about_activate" swapped="no"/>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">0</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox1">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <child>
              <object class="GtkCheckButton" id="checkbutton_binary">
                <property name="label" translatable="yes">_Binary</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Configures gpg output mode for encryption

When checked, gpg produces traditional binary output; otherwise, gpg produces ASCII-armored (text) output

On opening a file, this is set based on whether the file is detected as binary data or text, but it can be overridden

Setting not used when decrypting</property>
                <property name="use_underline">True</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="padding">2</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="checkbutton_sign">
                <property name="label" translatable="yes">Si_gn</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">In asymmetric encryption mode, this tells gpg to use your secret key to sign output

Setting not used when decrypting</property>
                <property name="use_underline">True</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="padding">2</property>
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkHButtonBox" id="hbuttonbox1">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="layout_style">edge</property>
                <child>
                  <object class="GtkButton" id="button_encrypt">
                    <property name="label" translatable="yes">_Encrypt</property>
                    <property name="use_action_appearance">False</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">False</property>
                    <property name="has_tooltip">True</property>
                    <property name="tooltip_text" translatable="yes">Encrypt input</property>
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="on_gtk_encrypt_activate" swapped="no"/>
                  </object>
                  <packing>
                    <property name="expand">False</property>
                    <property name="fill">False</property>
                    <property name="position">0</property>
                  </packing>
                </child>
                <child>
                  <object class="GtkButton" id="button_decrypt">
                    <property name="label" translatable="yes">_Decrypt</property>
                    <property name="use_action_appearance">False</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">False</property>
                    <property name="has_tooltip">True</property>
                    <property name="tooltip_text" translatable="yes">Decrypt input</property>
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="on_gtk_decrypt_activate" swapped="no"/>
                  </object>
                  <packing>
                    <property name="expand">False</property>
                    <property name="fill">False</property>
                    <property name="position">1</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkVSeparator" id="vseparator1">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="checkbutton_symmetric">
                <property name="label" translatable="yes">_Symmetric</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Toggle between symmetric and asymmetric encryption / decryption modes

Symmetric requires specifying a passphrase as a shared key (for both encryption &amp; decryption)

Asymmetric requires specifying recipients whose public keys will be used for encryption; or for decryption, it requires access to your gpg secret key</property>
                <property name="use_underline">True</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="on_gtk_symmetric_toggle_activate" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">4</property>
              </packing>
            </child>
            <child>
              <object class="GtkVSeparator" id="vseparator2">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_entry_passrecip">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_Passphrase: </property>
                <property name="use_underline">True</property>
                <property name="mnemonic_widget">entry_passrecip</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">6</property>
              </packing>
            </child>
            <child>
              <object class="GtkEntry" id="entry_passrecip">
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Symmetric encryption/decryption key

Max length limited only by available memory</property>
                <property name="visibility">False</property>
                <property name="invisible_char">●</property>
                <property name="width_chars">8</property>
                <property name="truncate_multiline">True</property>
                <property name="shadow_type">etched-in</property>
                <property name="primary_icon_activatable">False</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="position">7</property>
              </packing>
            </child>
            <child>
              <object class="GtkVSeparator" id="vseparator3">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">8</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_cipher">
                <property name="width_request">96</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Configures symmetric encryption cipher algorithm

In asymmetric mode, the chosen cipher is used in concert with recipients' pubkeys for encryption

With 'Default', gpg decides the cipher based on local system settings (weighing them against the preferences of recipient pubkeys if performing asymmetric encryption)

Setting not used when decrypting</property>
                <property name="model">liststore1</property>
                <property name="active">5</property>
                <accelerator key="c" signal="popup" modifiers="GDK_MOD1_MASK"/>
                <child>
                  <object class="GtkCellRendererText" id="cellrenderertext1"/>
                  <attributes>
                    <attribute name="text">0</attribute>
                  </attributes>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">9</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">1</property>
          </packing>
        </child>
        <child>
          <object class="GtkScrolledWindow" id="scrolledwindow1">
            <property name="visible">True</property>
            <property name="can_focus">True</property>
            <property name="hscrollbar_policy">automatic</property>
            <property name="vscrollbar_policy">automatic</property>
            <property name="shadow_type">etched-in</property>
            <child>
              <object class="GtkTextView" id="textview">
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="has_focus">True</property>
              </object>
            </child>
          </object>
          <packing>
            <property name="expand">True</property>
            <property name="fill">True</property>
            <property name="position">2</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox2">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <child>
              <object class="GtkStatusbar" id="statusbar_gpgvers">
                <property name="width_request">60</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="spacing">2</property>
                <property name="has_resize_grip">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkStatusbar" id="statusbar">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="spacing">2</property>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="position">1</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">3</property>
          </packing>
        </child>
      </object>
    </child>
  </object>
</interface>
        """



def show_errmsg(message):
    """Display message in GTK error dialog or print to terminal stderr."""
    dialog = gtk.MessageDialog(
        None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
    dialog.run() ; dialog.destroy()



class AEightCrypt:
    """Display GTK window to interact with gpg via GpgInterface object.
    
    Look at GpgInterface.__doc__ for all the juicy non-gui details.
    """
    
    
    def __init__(self):
        """Build GUI interface from XML, etc."""
        
        # Instantiate GpgInterface, which will check for gpg/gpg2
        try:
            self.g = GpgInterface()
        except:
            show_errmsg("This program requires either gpg or gpg2, neither "
                        "of which were found on your system.")
            raise
        
        # Other class attributes
        self.lastrecip = ''     # Saves/restores recipients when switching modes
        self.lastpass = ''      # Saves/restores passphrase when switching modes
        self.in_filename = None
        self.out_filename = None
        self.about_dialog = None
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file('a8crypt.glade') 
        except:
            try:
                gbuild = XmlForGtkBuilder()
                builder.add_from_string(gbuild.inline_gladexmlfile)
            except:
                show_errmsg("Missing a8crypt.glade XML file! Cannot continue.")
                raise
        
        # Set small Statusbar to gpg binary name (GPG or GPG2)
        gstatusbar = builder.get_object('statusbar_gpgvers') 
        cid = gstatusbar.get_context_id('ver')
        gstatusbar.push(cid, "[{}]".format(self.g.GPG.upper()))
        
        # Get widgets which will be referenced in callbacks
        self.window = builder.get_object('window1')
        self.binary_toggle = builder.get_object('checkbutton_binary')
        self.symmetric_toggle = builder.get_object('checkbutton_symmetric')
        self.sign_toggle = builder.get_object('checkbutton_sign')
        self.entrylabel = builder.get_object('label_entry_passrecip')
        self.entry = builder.get_object('entry_passrecip')
        self.textview = builder.get_object('textview')
        self.combobox = builder.get_object('combobox_cipher')
        self.statusbar = builder.get_object('statusbar')
        
        # Override a8crypt's default cipher by setting ComboBox active item index
        # 'Default'=0, AES256=1, Twofish=2, Camellia256=3, etc
        self.combobox.set_active(1)
        
        # Connect signals
        builder.connect_signals(self)
        
        # Set TextView font
        self.textview.modify_font(FontDescription('monospace 10'))
        
        # Set app icon to something halfway-decent
        gtk.window_set_default_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # Initialize main Statusbar
        self.status = self.statusbar.get_context_id('main')
        self.statusbar.push(self.status, "Enter message to encrypt/decrypt")
    
    
    # This is called when user tries to save or en/decrypt
    def sanitycheck_textviewbuff(self, choice):
        buff = self.textview.get_buffer()
        # Fail if TextBuffer is empty 
        if buff.get_char_count() < 1:
            show_errmsg("You haven't even entered any text yet.")
            return False
        # Fail if TextBuffer contains a message from direct-file-mode
        if not buff.get_modified():
            if choice in 'save':
                show_errmsg("Saving the buffer at this point would only save "
                            "a copy of the message you see in the main window.")
            else:
                show_errmsg(
                    "Your last file en/decryption operation succeeded. Selecting "
                    "'{}crypt' at this point would only save a copy of the message "
                    "you see in the main window. Either load a new file from the "
                    "'Open file' menu, or type/paste a new message"
                    .format(choice.title()))
            return False
        return True
    
    
    # Death!
    def on_window1_destroy(self, widget, data=None):        gtk.main_quit()
    def on_gtk_quit_activate(self, menuitem, data=None):    gtk.main_quit()
    
    
    # 'Encrypt' button & menu item
    def on_gtk_encrypt_activate(self, menuitem, data=None): self.crypt('en')
    
    
    # 'Decrypt' button & menu item
    def on_gtk_decrypt_activate(self, menuitem, data=None): self.crypt('de')
    
    
    # 'Open file' menu item
    def on_gtk_open_activate(self, menuitem, data=None):    self.open_file()
    
    
    # 'Save text buffer' menu item
    def on_gtk_save_activate(self, menuitem, data=None):
        if self.sanitycheck_textviewbuff('save'):
            filename = self.chooser_grab_filename('save')
            if filename: self.write_file(filename)
    
    
    # 'Cut' menu item
    def on_gtk_cut_activate(self, menuitem, data=None):
        buff = self.textview.get_buffer()
        buff.cut_clipboard(gtk.clipboard_get(), True)
    
    
    # 'Copy' menu item
    def on_gtk_copy_activate(self, menuitem, data=None):
        buff = self.textview.get_buffer()
        buff.copy_clipboard(gtk.clipboard_get())
    
    
    # 'Paste' menu item
    def on_gtk_paste_activate(self, menuitem, data=None):
        buff = self.textview.get_buffer()
        buff.paste_clipboard(gtk.clipboard_get(), None, True)
    
    
    # 'Clear' button & menu item 
    def on_gtk_clear_activate(self, menuitem, data=None):
        """Reset Statusbar, TextBuffer, Entry, gpg input & filename."""
        self.statusbar.pop(self.status)
        self.statusbar.push(self.status, "Enter message to encrypt/decrypt")
        buff = self.textview.get_buffer()
        buff.set_text('')
        buff.set_modified(False)
        self.textview.set_sensitive(True)
        self.textview.set_cursor_visible(True)
        self.entry.set_text('')
        self.binary_toggle.set_sensitive(False)
        self.binary_toggle.set_active(False)
        self.in_filename = None
        self.out_filename = None
        self.g.stdin = None
        self.lastrecip = ''
        self.lastpass = ''
    
    
    # 'Make cipher selection default' menu item
    def on_gtk_savecipherpref_activate(self, menuitem, data=None):
        """Get current cipher setting from ComboBox & save it as default in argv[0]."""
        from sys import argv
        cbindex = self.combobox.get_active()
        cmd = split('sed -i "s/^        self.combobox.set_active(.)/        '
                    'self.combobox.set_active({})/" {}'.format(cbindex, argv[0]))
        try:
            check_output(cmd)
        except:
            show_errmsg("Saving cipher setting failed. Try again while running {} "
                        "as root.".format(argv[0]))
    
    
    # 'Symmetric' checkbox toggle
    def on_gtk_symmetric_toggle_activate(self, widget, data=None):
        """Switch between symmetric & asymmetric mode, modifying necessary widgets."""
        
        # SWITCH TO SYMMETRIC
        if self.symmetric_toggle.get_active():
            
            self.entrylabel.set_label("_Passphrase: ")
            self.lastrecip = self.entry.get_text()
            self.entry.set_text(self.lastpass)
            self.entry.set_visibility(False)
            self.entry.set_tooltip_text(
                "Symmetric encryption/decryption key\n\n"
                "Max length limited only by available memory")
            self.sign_toggle.set_sensitive(False)
            self.sign_toggle.set_active(False)
        
        # SWITCH TO ASYMMETRIC
        else:  
            
            self.entrylabel.set_label("_Recipients: ")
            self.lastpass = self.entry.get_text()
            self.entry.set_text(self.lastrecip)
            self.entry.set_visibility(True)
            self.entry.set_tooltip_text(
                "Keys to use for asymmetric encryption\n\n"
                "Use a semicolon to separate recipients\n\n"
                "Tip: add yourself if you want to be able to read the encrypted message")
            self.sign_toggle.set_sensitive(True)
    
    
    # Generic file chooser for opening or saving
    def chooser_grab_filename(self, mode, save_suggestion=None):
        """Present file chooser dialog and return filename or None."""
        
        filename = None
        
        cmd = ("gtk.FileChooserDialog('{0} File...', self.window, "
               "gtk.FILE_CHOOSER_ACTION_{1}, (gtk.STOCK_CANCEL, "
               "gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))"
               .format(mode.title(), mode.upper()))
        chooser = eval(cmd)
        chooser.set_do_overwrite_confirmation(True)
        if save_suggestion: chooser.set_current_name(save_suggestion)
        
        response = chooser.run()
        if response == gtk.RESPONSE_OK: filename = chooser.get_filename()
        chooser.destroy()
        return filename
    
    
    # Save contents of buffer to file
    def write_file(self, filename):
        """Write TextView buffer to filename."""
        
        # Add message to status bar
        self.statusbar.push(self.status, "Saving {}".format(filename))
        
        while gtk.events_pending(): gtk.main_iteration()
        
        # Get contents of buffer
        buff = self.textview.get_buffer()
        buffertext = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
        
        try:
            # Try to open filename for writing
            fout = open(filename, 'w')
        except:
            # Error opening file, show message to user
            show_errmsg("Could not save file: {}".format(filename))
        else:
            # Write text from buffer to file
            fout.write(buffertext)
            fout.close()
        
        # Clear saving status
        self.statusbar.pop(self.status)
    
    
    def open_file(self):
        """Choose a filename to pass directly to gpg (without loading into textview).
        
        For very large files, it would be good to avoid pasting them into the
        GtkWindow and then having to pass that input (and resulting output) through
        Popen.communicate() ... right? Not to mention binary files.
        
        This method prompts for a filename to open (for gpg input) and then an output
        filename (to save gpg output to) and sets up everything to make it possible
        for AEightCrypt.crypt() to pass the file NAMES directly to the gpg subprocess,
        without ever opening the files in Python.
        """
        
        while True:
            # Prompt for a file to open
            infile = self.chooser_grab_filename('open')
            if not infile: return  # Cancel opening if user hit Cancel
            if access(infile, R_OK): break  # We're done if we can read infile
            show_errmsg("Could not open file {0!r} for reading. Choose a new file."
                        .format(infile))
        
        while True:
            # Prompt for name to save output to
            outfile = self.chooser_grab_filename('save', infile)
            if not outfile: return  # Return if user hit Cancel
            # TODO: Get Gtk.FileChooser's confirm-overwrite signal to handle this:
            if infile != outfile: break  # We're done if we got 2 different files
            show_errmsg("Simultaneously reading from & writing to a file is a "
                        "baaad idea. Choose a different output filename.")
        
        # Set binary CheckButton toggle
        self.binary_toggle.set_sensitive(True)
        if self.g.test_file_isbinary(infile):
            self.binary_toggle.set_active(True)
        
        # Ready message to status; disable text view & replace it with a message
        self.statusbar.push(self.status,
                            "Ready to encrypt or decrypt file: {}".format(infile))
        self.textview.set_cursor_visible(False)
        self.textview.set_sensitive(False)
        buff = self.textview.get_buffer()
        buff.set_text("Choose 'Encrypt' or 'Decrypt' to have {0} load file"
                      "\n   {1!r}\nas input, saving output to file\n   {2!r}"
                      .format(self.g.GPG.upper(), infile, outfile))
        buff.set_modified(False)
        
        # Promote our filenames
        self.in_filename = infile
        self.out_filename = outfile
    
    
    def crypt(self, mode):
        """Manage I/O between Gtk objects and our GpgInterface object.
        
        This method is called with an argument of 'en' or 'de' for encryption
        or decryption when the user selects one of the Encrypt or Decrypt Gtk
        menu items or toolbar buttons.
        
        It reads the passphrase from our GtkEntry box, ensuring it's not
        null; then it reads in the buffer from the TextBuffer of our TextView,
        if needed (this isn't necessary if the user already chose a file for
        direct-loading by gpg); then it passes everything over to GpgInterface
        and manages the task of getting any output back to the user.
        """
        
        if self.symmetric_toggle.get_active():
            # Get passphrase from Entry box in symmetric mode
            passrecip = self.entry.get_text()
            if not passrecip:
                show_errmsg("You must enter a passphrase.")
                return
        else:
            # Get recipients from Entry box in asymmetric mode
            passrecip = self.entry.get_text()
            if not passrecip and mode in 'en':
                show_errmsg("You must enter at least one recipient.")
                return
        
        # Get cipher algo from ComboBox for encryption
        cbmodel = self.combobox.get_model()
        cbindex = self.combobox.get_active()
        if cbindex == 0:    cipher = None
        else:               cipher = cbmodel[cbindex][0]
        
        # Use status of binary CheckButton to decide about ASCII-armoring output
        if self.binary_toggle.get_active():     base64 = False
        else:                                   base64 = True
        
        # Use status of sign CheckButton for message-signing
        if self.sign_toggle.get_active():   sign = True
        else:                               sign = False
        
        # FILE INPUT PREP
        if self.in_filename:
            
            # Set statusbar
            self.statusbar.push(self.status,
                                "{}crypting input ...".format(mode.title()))
        
        # TEXT INPUT PREP
        else:
            
            # Make sure textview has a proper message in it
            if not self.sanitycheck_textviewbuff(mode): return
            
            # Make TextView immutable to changes & set statusbar
            self.textview.set_cursor_visible(False)
            self.textview.set_sensitive(False)
            self.statusbar.push(self.status,
                                "{}crypting input ...".format(mode.title()))
            
            # Save textview buffer to GpgInterface.stdin
            buff = self.textview.get_buffer()
            self.g.stdin = buff.get_text(buff.get_start_iter(),
                                         buff.get_end_iter())
        
        # ATTEMPT EN-/DECRYPTION
        if self.symmetric_toggle.get_active():  cryptmethod = self.g.scrypt
        else:                                   cryptmethod = self.g.acrypt
        
        retval = cryptmethod(mode, passrecip, self.in_filename,
                             self.out_filename, base64, cipher, sign)
        
        # FILE INPUT MODE CLEANUP
        if self.in_filename:
            
            # Success!
            if retval:
                
                # Clear last two statusbar messages to get back to default
                # 'crypting input' and 'Ready to encrypt or decrypt file'
                self.statusbar.pop(self.status) ; self.statusbar.pop(self.status)
                
                # Replace textview buffer with success message
                buff = self.textview.get_buffer()
                buff.set_text("SUCCESS!\n\n{} saved new {}crypted file to:\n{}"
                              .format(self.g.GPG.upper(), mode, self.out_filename))
                buff.set_modified(False)
                
                # Unlock TextView
                self.textview.set_sensitive(True)
                self.textview.set_cursor_visible(True)
                
                # Reset filenames
                self.in_filename = None ; self.out_filename = None
                
                # Disable binary CheckButton
                self.binary_toggle.set_sensitive(False)
                self.binary_toggle.set_active(False)
            
            # Fail!
            else:
                
                self.statusbar.pop(self.status)  # Remove 'crypting input' status
                show_errmsg("{}Problem {}crypting {!r}\nTry again with another "
                            "passphrase or select Clear from the Edit menu."
                            .format(self.g.stderr, mode, self.in_filename))
        
        # TEXT INPUT MODE CLEANUP
        else:
            
            # Remove '...crypting input...' status
            self.statusbar.pop(self.status)
            
            # Unlock TextView
            self.textview.set_sensitive(True)
            self.textview.set_cursor_visible(True)
            
            # Reset inputdata
            self.g.stdin = None
            
            # Success!
            if retval:
                buff.set_text(self.g.stdout)  # Set TextBuffer to gpg stdout
            
            # Fail!
            else:
                show_errmsg(self.g.stderr)
    
    
    # About dialog
    def on_gtk_about_activate(self, menuitem, data=None):
        if self.about_dialog: 
            self.about_dialog.present()
            return
        authors = ["Ryan Sawhill <ryan@b19.org>"]
        about_dialog = gtk.AboutDialog()
        about_dialog.set_transient_for(self.window)
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name('a8crypt')
        about_dialog.set_version('0.9.5')
        about_dialog.set_copyright("Copyright \xc2\xa9 2012 Ryan Sawhill")
        about_dialog.set_website('http://github.com/ryran/a8crypt')
        about_dialog.set_comments("Encryption & decryption via GPG/GPG2")
        about_dialog.set_authors(authors)
        about_dialog.set_logo_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # callbacks for destroying the dialog
        def close(dialog, response, self):
            self.about_dialog = None
            dialog.destroy()
        def delete_event(dialog, event, self):
            self.about_dialog = None
            return True
        
        about_dialog.connect('response', close, self)
        about_dialog.connect('delete-event', delete_event, self)
        
        self.about_dialog = about_dialog
        about_dialog.show()
    
    
    # Run main application window
    def main(self):
        self.window.show()
        gtk.main()



if __name__ == "__main__":
    
    a8 = AEightCrypt()
    a8.main()
    
