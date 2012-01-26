#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# a8crypt v0.9.9.12 last mod 2012/01/26
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
# TODO: Dialog with progress bar & cancel button when working
# TODO: Get icons for for encrypt, decrypt, sign, verify buttons, application
# TODO: Preferences dialog that can save settings to a config file?
# TODO: Implement undo stack. Blech. Kill me.
# TODO: Implement update notifications.
# TODO: CHOOSE A PROPER PROJECT NAME. After that, time to stop packing everything
#       into one script -- will need to package things up proper-like


# Modules from the Standard Library
import gtk
from glib import timeout_add_seconds
from pango import FontDescription
from sys import stderr
from os import access, R_OK
from os import pipe, write, close
from shlex import split
from subprocess import Popen, PIPE, check_output


class GpgInterface():
    """GPG/GPG2 interface for encryption/decryption/signing/verifying.
    
    First thing: use subprocess module to call a gpg or gpg2 process, ensuring
    that one of them is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    See the docstring for the main method -- gpg() -- for next steps.
    
    Security: GpgInterface.gpg() can take a passphrase for symmetric enc/dec as
    an argument, but it never stores that passphrase on disk; the passphrase is
    passed to gpg via an os file descriptor. If any access to your secret key is
    required, gpg() invokes gpg/gpg2 with gpg-agent enabled.
    
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
        self.stdin  = None       # Stores input text for gpg()
        self.stdout = None      # Stores stdout stream from gpg subprocess
        self.stderr = None      # Stores stderr stream from gpg subprocess
    
    
    def test_file_isbinary(self, filename):
        """Utilize nix file cmd to determine if filename is binary or text."""
        cmd = split("file -b -e soft '{}'".format(filename))
        if check_output(cmd)[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    
    def get_gpgdefaultkey(self):
        """Return key id of first secret key in gpg keyring.""" 
        return check_output(split(
            "{} --list-secret-keys --with-colons --fast-list-mode"
            .format(self.GPG))).split(':', 5)[4]
    
    
    # Main gpg interface method
    def gpg(
        self,
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
        infile=     None,   # Input file
        outfile=    None,   # Output file
        verbose=    False,  # Add '--verbose'?
        alwaystrust=False,  # Add '--trust-model always'?
        yes=        True    # Add '--yes'? (will overwrite files)
        ):
        """Build a gpg cmdline and then launch gpg/gpg2, saving output appropriately.
        
        Arguments with their defaults + explanations, reproduced from the code:
        
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
        infile=     None,   # Input file
        outfile=    None,   # Output file
        verbose=    False,  # Add '--verbose'?
        alwaystrust=False,  # Add '--trust-model always'?
        yes=        True    # Add '--yes'? (will overwrite files)
        
        Things important enough to highlight:
        recip: Use a single semicolon to separate recipients. Superfluous leading/
            trailing semicolons or spaces are stripped.
        enctoself: Self is assumed to be first key returned by gpg --list-secret-keys;
            however, if localuser is provided, that is used as self instead.
        infile/outfile: If using infile, outfile is not necessarily required, but
            unless doing sign-only, it's probably a good idea.
        
        If no infile is specified, input is read from GpgInterface.stdin.
        Whether reading input from infile or stdin, each gpg command's stdout &
        stderr streams are saved to GpgInterface.stdout and GpgInterface.stderr,
        overwriting their contents.
        
        Re gpg-agent: If symmetric & passwd are specified when encrypting or
        decrypting, gpg-agent isn't called. In all other scenarios requiring a
        passphrase--whether encrypting, decrypting, or signing--gpg-agent will be
        invoked.
        
        Finally, gpg() returns either True or False, depending on gpg's exit code.
        """
        
        if infile and infile == outfile:
            stderr.write("Same file for both input and output, eh? Is it going "
                         "to work? ... NOPE. Chuck Testa.\n")
            raise Exception("infile, outfile must be different")
        
        fd_in =     None
        fd_out =    None
        useagent =  True
        cmd =       [self.GPG]
        
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
        if verbose:     cmd.append('--verbose')
        if outfile:     cmd.append('--output') ; cmd.append(outfile)
        if infile:      cmd.append(infile)
        
        stderr.write("{}\n".format(cmd))
        
        # If working direct with files, setup our Popen instance with no stdin
        if infile:
            P = Popen(cmd, stdout=PIPE, stderr=PIPE)
        # Otherwise, only difference for Popen is we need the stdin pipe
        else:
            P = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        
        # Time to communicate! Save output for later
        self.stdout, self.stderr = P.communicate(input=self.stdin)
        
        # Print gpg stderr
        stderr.write(self.stderr)
        stderr.write("-----------\n")
        
        # Close os file descriptor if necessary
        if fd_in:  close(fd_in)
        
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
  <object class="GtkImage" id="image6">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-clear</property>
  </object>
  <object class="GtkImage" id="image7">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-zoom-in</property>
  </object>
  <object class="GtkImage" id="image8">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-zoom-out</property>
  </object>
  <object class="GtkImage" id="img_clear">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-clear</property>
  </object>
  <object class="GtkImage" id="img_decrypt">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-revert-to-saved</property>
  </object>
  <object class="GtkImage" id="img_encrypt">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-apply</property>
  </object>
  <object class="GtkImage" id="img_open">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-open</property>
  </object>
  <object class="GtkImage" id="img_save">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-save</property>
  </object>
  <object class="GtkImage" id="img_saveas">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-save-as</property>
  </object>
  <object class="GtkListStore" id="liststore_ciphers">
    <columns>
      <!-- column-name Text -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">Default</col>
      </row>
      <row>
        <col id="0">AES256</col>
      </row>
      <row>
        <col id="0">Twofish</col>
      </row>
      <row>
        <col id="0">Camellia256</col>
      </row>
      <row>
        <col id="0">AES192</col>
      </row>
      <row>
        <col id="0">Camellia192</col>
      </row>
      <row>
        <col id="0">AES</col>
      </row>
      <row>
        <col id="0">Camellia128</col>
      </row>
      <row>
        <col id="0">CAST5</col>
      </row>
      <row>
        <col id="0">Blowfish</col>
      </row>
      <row>
        <col id="0">3DES</col>
      </row>
    </data>
  </object>
  <object class="GtkListStore" id="liststore_hashes">
    <columns>
      <!-- column-name Text -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">Default</col>
      </row>
      <row>
        <col id="0">SHA512</col>
      </row>
      <row>
        <col id="0">SHA384</col>
      </row>
      <row>
        <col id="0">SHA256</col>
      </row>
      <row>
        <col id="0">SHA224</col>
      </row>
      <row>
        <col id="0">RIPEMD160</col>
      </row>
      <row>
        <col id="0">SHA1</col>
      </row>
      <row>
        <col id="0">MD5</col>
      </row>
    </data>
  </object>
  <object class="GtkListStore" id="liststore_sigmodes">
    <columns>
      <!-- column-name Text -->
      <column type="gchararray"/>
    </columns>
    <data>
      <row>
        <col id="0" translatable="yes">Embedded</col>
      </row>
      <row>
        <col id="0" translatable="yes">Clearsign</col>
      </row>
      <row>
        <col id="0" translatable="yes">Detached</col>
      </row>
    </data>
  </object>
  <object class="GtkWindow" id="window1">
    <property name="can_focus">False</property>
    <property name="title" translatable="yes">a8crypt</property>
    <property name="window_position">center</property>
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
                      <object class="GtkImageMenuItem" id="mnu_clear">
                        <property name="label">C_lear</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Clear all text/file buffers</property>
                        <property name="use_underline">True</property>
                        <property name="image">image6</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="l" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_clear" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_open">
                        <property name="label" translatable="yes">_Open Text File as Message</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Open a text file as Message Input for encrypting, decrypting, signing, or verifying</property>
                        <property name="use_underline">True</property>
                        <property name="image">img_open</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="o" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_open" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_save">
                        <property name="label" translatable="yes">_Save Copy of Message</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="tooltip_text" translatable="yes">Save contents of Message Input/Output area to a text file</property>
                        <property name="use_underline">True</property>
                        <property name="image">img_saveas</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="s" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_save" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="mnu_sep1a">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_quit">
                        <property name="label">gtk-quit</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="q" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_quit" swapped="no"/>
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
                <property name="label" translatable="yes">Edit</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="editmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_undo">
                        <property name="label">gtk-undo</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_undo" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_redo">
                        <property name="label">gtk-redo</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_redo" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="mnu_sep2a">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_cut">
                        <property name="label">gtk-cut</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_cut" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_copy">
                        <property name="label">gtk-copy</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_copy" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_paste">
                        <property name="label">gtk-paste</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_paste" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="mnu_sep2b">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_preferences">
                        <property name="label">gtk-preferences</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">NOT IMPLEMENTED YET
WHOOPS</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_savecipherpref">
                        <property name="label" translatable="yes">_Make Cipher Selection Default</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Attempts to modify the a8crypt script to permanently change the default cipher setting

This will fail if a8crypt is not writable</property>
                        <property name="use_underline">True</property>
                        <property name="image">img_save</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_savecipherpref" swapped="no"/>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
            <child>
              <object class="GtkMenuItem" id="menuitem3">
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_View</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="viewmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkCheckMenuItem" id="toggle_wordwrap">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Toggles wrapping of lines the Message area. This will not actually add newline characters.</property>
                        <property name="label" translatable="yes">Text _Wrapping</property>
                        <property name="use_underline">True</property>
                        <property name="active">True</property>
                        <signal name="toggled" handler="action_toggle_wordwrap" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkCheckMenuItem" id="toggle_taskstatus">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Show/hide side pane containing gpg status messages</property>
                        <property name="label" translatable="yes">_Task Status side panel</property>
                        <property name="use_underline">True</property>
                        <property name="active">True</property>
                        <signal name="toggled" handler="action_toggle_taskstatus" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkCheckMenuItem" id="toggle_gpgverbose">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Enable/disable verbose status output from gpg (displayed in side panel or error messages)</property>
                        <property name="label" translatable="yes">_Verbose gpg output</property>
                        <property name="use_underline">True</property>
                        <property name="active">True</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkSeparatorMenuItem" id="mnu_sep3a">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_zoomin">
                        <property name="label" translatable="yes">Increase Font Size</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="image">image7</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="plus" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_zoom" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_zoomout">
                        <property name="label" translatable="yes">Decrease Font Size</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="image">image8</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <accelerator key="minus" signal="activate" modifiers="GDK_CONTROL_MASK"/>
                        <signal name="activate" handler="action_zoom" swapped="no"/>
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
                <property name="label" translatable="yes">Help</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="helpmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="mnu_about">
                        <property name="label">gtk-about</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="action_about" swapped="no"/>
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
            <property name="spacing">3</property>
            <child>
              <object class="GtkLabel" id="space1a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">0</property>
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
                    <property name="receives_default">True</property>
                    <property name="image">img_encrypt</property>
                    <property name="relief">none</property>
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="action_encrypt" swapped="no"/>
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
                    <property name="receives_default">True</property>
                    <property name="image">img_decrypt</property>
                    <property name="relief">none</property>
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="action_decrypt" swapped="no"/>
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
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space1b">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes"> </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkButton" id="btn_clear">
                <property name="label" translatable="yes">C_lear</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">True</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Clear all text/file buffers</property>
                <property name="image">img_clear</property>
                <property name="relief">none</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <signal name="clicked" handler="action_clear" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space1c">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes"> </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">8</property>
                <property name="position">4</property>
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
          <object class="GtkHBox" id="hbox2">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <property name="spacing">1</property>
            <child>
              <object class="GtkLabel" id="space2a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkRadioButton" id="toggle_mode_signverify">
                <property name="label" translatable="yes">Sign/Verif_y Mode</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="tooltip_text" translatable="yes">Sign-only / verify-only mode

For adding a signature to a message/file without encrypting it or for verifying a signed message/file that isn't encrypted</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
                <property name="group">toggle_mode_encdec</property>
                <signal name="toggled" handler="action_toggle_mode_signverify" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_sign_chooseoutput">
                <property name="label" translatable="yes">Choose Output Filenames</property>
                <property name="use_action_appearance">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">When signing external files, the output filenames are automatically chosen by gpg -- output is saved to the same directory as the input file and an extension is added based on the options used

Check this if you wish to choose the output filename yourself (e.g., because the input file is in a directory you can't write to)</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkVSeparator" id="vseparator2a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">12</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkRadioButton" id="toggle_mode_encdec">
                <property name="label" translatable="yes">Enc/Dec _Mode</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Encrypt / decrypt / encrypt + sign mode</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">4</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_mode_symmetric">
                <property name="label" translatable="yes">_Symmetric</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Symmetric encryption/decryption

Requires specifying a passphrase which is used as a shared key (for both encryption &amp; decryption)</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="action_toggle_symmetric" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_mode_asymmetric">
                <property name="label" translatable="yes">_Asymmetric</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Asymmetric encryption/decryption

Requires specifying recipients whose public keys will be used for encryption; or for decryption, it requires access to your gpg secret key</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="action_toggle_asymmetric" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">6</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_advanced">
                <property name="label" translatable="yes">Adva_nced</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Allow mixing symmetric encryption with asymmetric and signing

When creating a signed + symmetrically-encrypted message, anything in the passphrase entry box will be ignored -- gpg-agent will need to ask for both the symmetric encryption key (passphrase) and [potentially] the passphrase to your secret key</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="action_toggle_advanced" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">7</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">2</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox3">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <property name="spacing">1</property>
            <child>
              <object class="GtkLabel" id="space3a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_entry_pass">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_Passphrase:</property>
                <property name="use_markup">True</property>
                <property name="use_underline">True</property>
                <property name="mnemonic_widget">entry_pass</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkEntry" id="entry_pass">
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Symmetric encryption/decryption key

Max length limited only by available memory</property>
                <property name="visibility">False</property>
                <property name="invisible_char">●</property>
                <property name="width_chars">10</property>
                <property name="truncate_multiline">True</property>
                <property name="shadow_type">etched-in</property>
                <property name="invisible_char_set">True</property>
                <property name="primary_icon_stock">gtk-dialog-authentication</property>
                <property name="primary_icon_activatable">True</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
                <property name="primary_icon_tooltip_text" translatable="yes">Clear entry field</property>
                <signal name="icon-press" handler="action_clear_entry" swapped="no"/>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space3b">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes"> </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_entry_recip">
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_Recipients:</property>
                <property name="use_markup">True</property>
                <property name="use_underline">True</property>
                <property name="mnemonic_widget">entry_recip</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">4</property>
              </packing>
            </child>
            <child>
              <object class="GtkEntry" id="entry_recip">
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Keys to use for asymmetric encryption

Use a semicolon to separate recipients</property>
                <property name="invisible_char">●</property>
                <property name="width_chars">10</property>
                <property name="truncate_multiline">True</property>
                <property name="shadow_type">etched-in</property>
                <property name="invisible_char_set">True</property>
                <property name="caps_lock_warning">False</property>
                <property name="primary_icon_stock">gtk-orientation-portrait</property>
                <property name="primary_icon_activatable">True</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
                <property name="primary_icon_tooltip_text" translatable="yes">Clear entry field</property>
                <signal name="icon-press" handler="action_clear_entry" swapped="no"/>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_enctoself">
                <property name="label" translatable="yes">Enc. To Se_lf</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Tells gpg to encrypt the message with the public key that corresponds to the first secret key in your keyring

This is done in addition to any other recipients, or if in Advanced mode and performing symmetric encryption with a passphrase, then in addition to that

Note for power users: if 'Change Default Key' in the signature options toolbar is enabled, the contents of its entry box are used as self, instead of the first secret key in your keyring</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">6</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space3c">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">  </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">7</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_combobox_cipher">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">_Cipher:</property>
                <property name="use_underline">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">8</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_cipher">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[Not used when decrypting, verifying]

Configures symmetric encryption cipher algorithm

In asymmetric mode, the chosen cipher is used in concert with recipients' pubkeys for encryption

With 'Default', gpg decides the algorithm based on local system settings (weighing them against the preferences of recipient pubkeys if performing asymmetric encryption)</property>
                <property name="model">liststore_ciphers</property>
                <property name="active">0</property>
                <property name="focus_on_click">False</property>
                <child>
                  <object class="GtkCellRendererText" id="cellrenderertext4"/>
                  <attributes>
                    <attribute name="text">0</attribute>
                  </attributes>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">9</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">3</property>
          </packing>
        </child>
        <child>
          <object class="GtkHPaned" id="hpaned1">
            <property name="visible">True</property>
            <property name="can_focus">True</property>
            <property name="position">522</property>
            <property name="position_set">True</property>
            <child>
              <object class="GtkHBox" id="hbox6">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <child>
                  <object class="GtkVBox" id="vbox2">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkLabel" id="space6a">
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">True</property>
                        <property name="position">0</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkButton" id="btn_open">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">True</property>
                        <property name="receives_default">True</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Open a text file as Message Input for encrypting, decrypting, signing, or verifying</property>
                        <property name="relief">none</property>
                        <property name="focus_on_click">False</property>
                        <signal name="clicked" handler="action_open" swapped="no"/>
                        <child>
                          <object class="GtkImage" id="image1">
                            <property name="visible">True</property>
                            <property name="can_focus">False</property>
                            <property name="stock">gtk-open</property>
                          </object>
                        </child>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">True</property>
                        <property name="position">1</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkButton" id="btn_save">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">True</property>
                        <property name="receives_default">True</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Save contents of Message area to a text file</property>
                        <property name="relief">none</property>
                        <property name="focus_on_click">False</property>
                        <signal name="clicked" handler="action_save" swapped="no"/>
                        <child>
                          <object class="GtkImage" id="image2">
                            <property name="visible">True</property>
                            <property name="can_focus">False</property>
                            <property name="stock">gtk-save-as</property>
                          </object>
                        </child>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">True</property>
                        <property name="position">2</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkButton" id="btn_copyall">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">True</property>
                        <property name="receives_default">True</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Copy contents of Message area to the clipboard</property>
                        <property name="relief">none</property>
                        <property name="focus_on_click">False</property>
                        <signal name="clicked" handler="action_copyall" swapped="no"/>
                        <child>
                          <object class="GtkImage" id="image3">
                            <property name="visible">True</property>
                            <property name="can_focus">False</property>
                            <property name="stock">gtk-select-all</property>
                          </object>
                        </child>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">True</property>
                        <property name="position">3</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkHSeparator" id="hseparator6a">
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">True</property>
                        <property name="padding">8</property>
                        <property name="position">4</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkButton" id="btn_undo">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">True</property>
                        <property name="receives_default">True</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Undo the last action in Message area</property>
                        <property name="relief">none</property>
                        <property name="focus_on_click">False</property>
                        <property name="image_position">top</property>
                        <signal name="clicked" handler="action_undo" swapped="no"/>
                        <child>
                          <object class="GtkImage" id="image4">
                            <property name="visible">True</property>
                            <property name="can_focus">False</property>
                            <property name="stock">gtk-undo</property>
                          </object>
                        </child>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">False</property>
                        <property name="position">5</property>
                      </packing>
                    </child>
                    <child>
                      <object class="GtkButton" id="btn_redo">
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">True</property>
                        <property name="receives_default">True</property>
                        <property name="has_tooltip">True</property>
                        <property name="tooltip_text" translatable="yes">Redo the last undone action in Message area</property>
                        <property name="relief">none</property>
                        <property name="focus_on_click">False</property>
                        <property name="image_position">top</property>
                        <signal name="clicked" handler="action_redo" swapped="no"/>
                        <child>
                          <object class="GtkImage" id="image5">
                            <property name="visible">True</property>
                            <property name="can_focus">False</property>
                            <property name="stock">gtk-redo</property>
                          </object>
                        </child>
                      </object>
                      <packing>
                        <property name="expand">False</property>
                        <property name="fill">False</property>
                        <property name="position">6</property>
                      </packing>
                    </child>
                  </object>
                  <packing>
                    <property name="expand">False</property>
                    <property name="fill">True</property>
                    <property name="padding">1</property>
                    <property name="position">0</property>
                  </packing>
                </child>
                <child>
                  <object class="GtkFrame" id="frame1">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <property name="border_width">3</property>
                    <property name="label_xalign">0</property>
                    <child>
                      <object class="GtkVBox" id="vbox_ibar">
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <child>
                          <object class="GtkExpander" id="expander_filemode">
                            <property name="visible">True</property>
                            <property name="can_focus">True</property>
                            <child>
                              <object class="GtkHBox" id="hbox7">
                                <property name="visible">True</property>
                                <property name="can_focus">False</property>
                                <child>
                                  <object class="GtkFileChooserButton" id="btn_filechooser">
                                    <property name="visible">True</property>
                                    <property name="can_focus">False</property>
                                    <property name="has_tooltip">True</property>
                                    <property name="tooltip_text" translatable="yes">Choose a file to pass directly to gpg as input instead of loading into the Message area

File WILL NOT be loaded into the text buffer, so this is the way to go when dealing with binary or very large files</property>
                                    <property name="focus_on_click">False</property>
                                    <property name="title" translatable="yes">Choose gpg input file...</property>
                                    <signal name="file-set" handler="action_filemode_chooser_set" swapped="no"/>
                                  </object>
                                  <packing>
                                    <property name="expand">True</property>
                                    <property name="fill">True</property>
                                    <property name="padding">4</property>
                                    <property name="position">0</property>
                                  </packing>
                                </child>
                                <child>
                                  <object class="GtkLabel" id="space4b1">
                                    <property name="visible">True</property>
                                    <property name="can_focus">False</property>
                                    <property name="label" translatable="yes"> </property>
                                  </object>
                                  <packing>
                                    <property name="expand">False</property>
                                    <property name="fill">True</property>
                                    <property name="padding">3</property>
                                    <property name="position">1</property>
                                  </packing>
                                </child>
                                <child>
                                  <object class="GtkCheckButton" id="toggle_plaintext">
                                    <property name="label" translatable="yes">Generate _Text Output</property>
                                    <property name="use_action_appearance">False</property>
                                    <property name="visible">True</property>
                                    <property name="sensitive">False</property>
                                    <property name="can_focus">True</property>
                                    <property name="receives_default">False</property>
                                    <property name="has_tooltip">True</property>
                                    <property name="tooltip_text" translatable="yes">[Not used when decrypting, verifying]

Tells gpg to output plaintext instead of binary data when encrypting and signing

This kind of output is commonly called 'base64-encoded' or 'ASCII-armored'

On opening a file, this is set based on whether the file is detected as binary data or text, but it can be overridden</property>
                                    <property name="use_underline">True</property>
                                    <property name="focus_on_click">False</property>
                                    <property name="active">True</property>
                                    <property name="draw_indicator">True</property>
                                  </object>
                                  <packing>
                                    <property name="expand">False</property>
                                    <property name="fill">False</property>
                                    <property name="padding">6</property>
                                    <property name="position">2</property>
                                  </packing>
                                </child>
                              </object>
                            </child>
                            <child type="label">
                              <object class="GtkLabel" id="label_filemode">
                                <property name="visible">True</property>
                                <property name="can_focus">False</property>
                                <property name="label" translatable="yes">Inp_ut File For Direct Operation</property>
                                <property name="use_underline">True</property>
                                <property name="mnemonic_widget">expander_filemode</property>
                                <attributes>
                                  <attribute name="variant" value="small-caps"/>
                                </attributes>
                              </object>
                            </child>
                          </object>
                          <packing>
                            <property name="expand">False</property>
                            <property name="fill">True</property>
                            <property name="pack_type">end</property>
                            <property name="position">0</property>
                          </packing>
                        </child>
                        <child>
                          <object class="GtkScrolledWindow" id="scrolledwindow1">
                            <property name="visible">True</property>
                            <property name="can_focus">True</property>
                            <property name="hscrollbar_policy">automatic</property>
                            <property name="vscrollbar_policy">automatic</property>
                            <child>
                              <object class="GtkTextView" id="textview1">
                                <property name="visible">True</property>
                                <property name="can_focus">True</property>
                                <property name="has_focus">True</property>
                                <property name="wrap_mode">word</property>
                              </object>
                            </child>
                          </object>
                          <packing>
                            <property name="expand">True</property>
                            <property name="fill">True</property>
                            <property name="pack_type">end</property>
                            <property name="position">1</property>
                          </packing>
                        </child>
                      </object>
                    </child>
                    <child type="label">
                      <object class="GtkLabel" id="label1">
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="label" translatable="yes">&lt;i&gt;_Message Input/Output&lt;/i&gt;</property>
                        <property name="use_markup">True</property>
                        <property name="use_underline">True</property>
                        <property name="mnemonic_widget">textview1</property>
                      </object>
                    </child>
                  </object>
                  <packing>
                    <property name="expand">True</property>
                    <property name="fill">True</property>
                    <property name="position">1</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="resize">True</property>
                <property name="shrink">False</property>
              </packing>
            </child>
            <child>
              <object class="GtkFrame" id="frame2">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="border_width">3</property>
                <property name="label_xalign">0</property>
                <child>
                  <object class="GtkScrolledWindow" id="scrolledwindow2">
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="hscrollbar_policy">automatic</property>
                    <property name="vscrollbar_policy">automatic</property>
                    <child>
                      <object class="GtkTextView" id="textview2">
                        <property name="visible">True</property>
                        <property name="sensitive">False</property>
                        <property name="can_focus">True</property>
                        <property name="wrap_mode">word</property>
                        <property name="cursor_visible">False</property>
                      </object>
                    </child>
                  </object>
                </child>
                <child type="label">
                  <object class="GtkLabel" id="label2">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <property name="label" translatable="yes">&lt;i&gt;Task Status&lt;/i&gt;</property>
                    <property name="use_markup">True</property>
                    <property name="use_underline">True</property>
                  </object>
                </child>
              </object>
              <packing>
                <property name="resize">True</property>
                <property name="shrink">True</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">True</property>
            <property name="fill">True</property>
            <property name="position">4</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox4">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <property name="spacing">1</property>
            <child>
              <object class="GtkLabel" id="space4a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">2</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_signature">
                <property name="label" translatable="yes">Add Si_gnature:</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[Not used when decrypting, verifying]

Tells gpg to use your secret key to sign the input

This will likely require you to interact with gpg-agent</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="action_toggle_signature" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_sigmode">
                <property name="sensitive">False</property>
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[Not used when decrypting, verifying]

This allows you to choose the signature type for signing in Sign/Verify mode

Embedded: encodes the signature and message together (this is most often used along with encryption)

Clearsign: wraps the message with a plaintext signature

Detached: creates a separate signature that does not contain the message</property>
                <property name="model">liststore_sigmodes</property>
                <property name="active">0</property>
                <property name="focus_on_click">False</property>
                <child>
                  <object class="GtkCellRendererText" id="cellrenderertext3"/>
                  <attributes>
                    <attribute name="text">0</attribute>
                  </attributes>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space4b">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes"> </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_combobox_hash">
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">D_igest:</property>
                <property name="use_underline">True</property>
                <property name="mnemonic_widget">combobox_hash</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">4</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_hash">
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[Not used when decrypting, verifying]

Configures message digest algorithm (used for hashing message, i.e., creating your signature)

With 'Default', gpg decides the algorithm based on local system settings, weighing them against the preferences of your secret key</property>
                <property name="model">liststore_hashes</property>
                <property name="active">0</property>
                <property name="focus_on_click">False</property>
                <child>
                  <object class="GtkCellRendererText" id="cellrenderertext2"/>
                  <attributes>
                    <attribute name="text">0</attribute>
                  </attributes>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space4c">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes"> </property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">6</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_defaultkey">
                <property name="label" translatable="yes">Change Default _Key:</property>
                <property name="use_action_appearance">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Tell gpg which secret key to use for signing

This is only useful if you have multiple secret keys in your keyring</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="action_toggle_defaultkey" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">7</property>
              </packing>
            </child>
            <child>
              <object class="GtkEntry" id="entry_defaultkey">
                <property name="can_focus">True</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Key identifier of the non-default key to use for signing

Input is passed to gpg '--local-user' option</property>
                <property name="invisible_char">●</property>
                <property name="width_chars">11</property>
                <property name="truncate_multiline">True</property>
                <property name="shadow_type">etched-in</property>
                <property name="invisible_char_set">True</property>
                <property name="caps_lock_warning">False</property>
                <property name="primary_icon_stock">gtk-orientation-portrait</property>
                <property name="primary_icon_activatable">True</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
                <property name="primary_icon_tooltip_text" translatable="yes">Clear entry field</property>
                <signal name="icon-press" handler="action_clear_entry" swapped="no"/>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">8</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">5</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox5">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <child>
              <object class="GtkSpinner" id="spinner1">
                <property name="width_request">16</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">0</property>
              </packing>
            </child>
            <child>
              <object class="GtkStatusbar" id="statusbar">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
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
            <property name="position">6</property>
          </packing>
        </child>
      </object>
    </child>
  </object>
</interface>
        """



def show_errmsg(message, dialogtype=gtk.MESSAGE_ERROR):
    """Display message with GtkMessageDialog."""
    dialog = gtk.MessageDialog(
        None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        dialogtype, gtk.BUTTONS_OK, message)
    dialog.run()
    dialog.destroy()




class AEightCrypt:
    """Display GTK window to interact with gpg via GpgInterface object.
    
    For now, we build the gui from a Glade-generated gtk builder xml file.
    Once things are more finalized, we'll add the pygtk calls in here.
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
        self.in_filename  = None
        self.out_filename = None
        self.about_dialog = None
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file('a8crypt.glade') 
        except:
            gbuild = XmlForGtkBuilder()
            ret = builder.add_from_string(gbuild.inline_gladexmlfile)
            if ret == 0:
                show_errmsg("Problem loading GtkBuilder UI definition! "
                            "Cannot continue.")
                exit()
        
        #--------------------------------------------------------- GET WIDGETS!
        
        # Main window
        self.g_window       = builder.get_object('window1')
        # Menu items
        self.g_mopen        = builder.get_object('mnu_open')
        self.g_msave        = builder.get_object('mnu_save')
        self.g_mcut         = builder.get_object('mnu_cut')
        self.g_mcopy        = builder.get_object('mnu_copy')
        self.g_mpaste       = builder.get_object('mnu_paste')
        self.g_wrap         = builder.get_object('toggle_wordwrap')
        self.g_taskstatus   = builder.get_object('toggle_taskstatus')
        self.g_gpgverbose   = builder.get_object('toggle_gpgverbose')
        # Infobar funness
        self.g_vb_ibar      = builder.get_object('vbox_ibar')
        self.g_ibar         = None
        # Top action toolbar
        self.g_encrypt      = builder.get_object('button_encrypt')
        self.g_decrypt      = builder.get_object('button_decrypt')
        self.g_bopen        = builder.get_object('btn_open')
        self.g_bsave        = builder.get_object('btn_save')
        self.g_chooserbtn   = builder.get_object('btn_filechooser')
        self.g_bcopyall     = builder.get_object('btn_copyall')
        # Mode-setting toolbar
        self.g_signverify   = builder.get_object('toggle_mode_signverify')
        self.g_chk_outfile  = builder.get_object('toggle_sign_chooseoutput')
        self.g_symmetric    = builder.get_object('toggle_mode_symmetric')
        self.g_asymmetric   = builder.get_object('toggle_mode_asymmetric')
        self.g_advanced     = builder.get_object('toggle_advanced')
        # Encryption toolbar
        self.g_enctoolbar   = builder.get_object('hbox3')
        self.g_passlabel    = builder.get_object('label_entry_pass')
        self.g_pass         = builder.get_object('entry_pass')
        self.g_reciplabel   = builder.get_object('label_entry_recip')
        self.g_recip        = builder.get_object('entry_recip')
        self.g_enctoself    = builder.get_object('toggle_enctoself')
        self.g_cipherlabel  = builder.get_object('label_combobox_cipher')
        self.g_cipher       = builder.get_object('combobox_cipher')
        # Middle input area
        self.g_msgtxtview   = builder.get_object('textview1')
        self.buff           = self.g_msgtxtview.get_buffer()
        self.g_frame2       = builder.get_object('frame2')
        self.g_errtxtview   = builder.get_object('textview2')
        self.buff2          = self.g_errtxtview.get_buffer()
        # Bottom toolbar
        self.g_plaintext    = builder.get_object('toggle_plaintext')
        self.g_signature    = builder.get_object('toggle_signature')
        self.g_sigmode      = builder.get_object('combobox_sigmode')
        self.g_hashlabel    = builder.get_object('label_combobox_hash')
        self.g_hash         = builder.get_object('combobox_hash')
        self.g_chk_defkey   = builder.get_object('toggle_defaultkey')
        self.g_defaultkey   = builder.get_object('entry_defaultkey')
        # Statusbar
        self.g_statusbar    = builder.get_object('statusbar')
        self.g_activityspin = builder.get_object('spinner1')
        
        # Set window title dynamically
        self.g_window.set_title(
            "{current} [{GPG}]"
            .format(current=self.g_window.get_title(), GPG=self.g.GPG.upper()))
        
        # Set app icon to something halfway-decent
        gtk.window_set_default_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # Override a8crypt's default cipher by setting ComboBox active item index
        # 'Default'=0, AES256=1, Twofish=2, Camellia256=3, etc
        self.g_cipher.set_active(1)
        
        # Connect signals
        builder.connect_signals(self)
        
        # sensitivity not defaulted to False because that makes this Entry's icons
        #   stay insensitive-looking forever
        self.g_recip.set_sensitive(False)
        
        # Set TextView fonts
        self.msgfontsz = 9
        self.errfontsz = 7
        self.g_msgtxtview.modify_font(FontDescription('monospace {}'.format(self.msgfontsz)))
        self.g_errtxtview.modify_font(FontDescription('normal {}'.format(self.errfontsz)))
        """Might play with colors at some point...
        self.g_msgtxtview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
        self.g_msgtxtview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))
        """
        
        self.buff2.set_text("Output from each call to gpg will be displayed here.\n\n"
                            "In the View menu you can change gpg's verbosity level, "
                            "hide this pane, or simply change the font size.")
        
        # Initialize main Statusbar
        self.status = self.g_statusbar.get_context_id('main')
        self.g_statusbar.push(self.status, "Enter message to encrypt/decrypt")
    
    
    #--------------------------------------------------------- HELPER FUNCTIONS
    
    def set_stdstatus(self):
        """Set a standard status message that is mode-depenedent."""
        self.g_statusbar.pop(self.status)
        if self.g_signverify.get_active():
            s = "Enter message to sign/verify"
        else:
            s = "Enter message to encrypt/decrypt"
        self.g_statusbar.push(self.status, s)
    
    
    def infobar(self, message, msgtype=gtk.MESSAGE_INFO, timeout=5):
        """Instantiate a new auto-hiding InfoBar with a Label of message."""
        
        message = "<span foreground='#2E2E2E'>" + message + "</span>"
        if msgtype == gtk.MESSAGE_INFO:         icon = gtk.STOCK_APPLY
        elif msgtype == gtk.MESSAGE_ERROR:      icon = gtk.STOCK_DIALOG_ERROR
        elif msgtype == gtk.MESSAGE_WARNING:    icon = gtk.STOCK_DIALOG_WARNING
        elif msgtype == gtk.MESSAGE_QUESTION:   icon = gtk.STOCK_DIALOG_QUESTION
        
        ibar                    = gtk.InfoBar()
        self.g_vb_ibar.pack_end (ibar, False, False)
        ibar.set_message_type   (msgtype)
        ibar.add_button         (gtk.STOCK_OK, gtk.RESPONSE_OK)
        ibar.connect            ("response", lambda *args: ibar.destroy())
        img                     = gtk.Image()
        img.set_from_stock      (icon, gtk.ICON_SIZE_LARGE_TOOLBAR)
        label                   = gtk.Label()
        label.set_markup        (message)
        content                 = ibar.get_content_area()
        content.add             (img)
        content.add             (label)
        img.show()
        label.show()
        ibar.show()
        if timeout:
            timeout_add_seconds(timeout, ibar.destroy)
    
    
    # This is called when entering & exiting direct-file mode.
    def filemode_enablewidgets(self, x=True):
        """Enable/disable certain widgets due to working in direct-file mode."""
        widgets = [self.g_bcopyall, self.g_bopen, self.g_mopen, self.g_bsave,
                   self.g_msave, self.g_mcut, self.g_mcopy, self.g_mpaste,
                   self.g_msgtxtview]
        for w in widgets:
            w.set_sensitive(x)
    
    
    # This is called when user tries to copyall or save or en/decrypt or sign/verify
    def test_msgbuff_isempty(self, msg):
        if self.buff.get_char_count() < 1:
            self.infobar("<b>{}</b>".format(msg), gtk.MESSAGE_WARNING, 2)
            return True
    
    def confirm_overwrite_callback(self, chooser):
        outfile = chooser.get_filename()
        if self.in_filename == outfile:
            show_errmsg("Simultaneously reading from & writing to a file is a "
                        "baaad idea. Choose a different output filename.")
            return gtk.FILE_CHOOSER_CONFIRMATION_SELECT_AGAIN
        else:
            return gtk.FILE_CHOOSER_CONFIRMATION_CONFIRM

    
    # Generic file chooser for opening or saving
    def chooser_grab_filename(self, mode, save_suggestion=None):
        """Present file chooser dialog and return filename or None."""
        
        filename = None
        if mode in 'open':   title = "Choose text file to open as input..."
        elif mode in 'save': title = "Choose output filename..."
        
        cmd = ("gtk.FileChooserDialog('{0}', None, gtk.FILE_CHOOSER_ACTION_{1}, "
               "(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))"
               .format(title, mode.upper()))
        chooser = eval(cmd)
        
        if mode in 'open':
            t = gtk.FileFilter() ; t.set_name("Text Files") ; t.add_mime_type("text/*")
            a = gtk.FileFilter() ; a.set_name("All Files") ; a.add_pattern("*")
            chooser.add_filter(t)
            chooser.add_filter(a)
        elif mode in 'save':
            chooser.set_do_overwrite_confirmation(True)
            chooser.connect('confirm-overwrite', self.confirm_overwrite_callback)
            if save_suggestion:  chooser.set_current_name(save_suggestion)
        
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        chooser.destroy()
        return filename
    
    
    def grab_activetext_combobox(self, combobox):
        """Return the text of active combobox selection."""
        cbmodel = combobox.get_model()
        cbindex = combobox.get_active()
        if cbindex == 0:
            return None  # If first choice is selected, i.e. 'Default'
        else:
            return cbmodel[cbindex][0]
    
    
    # This is called by encrypt/decrypt buttons when operating in direct-file mode
    def filemode_get_outfile(self, mode):
        """Use FileChooser to get an output filename for gpg direct enc/dec."""
        outfile = self.chooser_grab_filename('save', self.in_filename)
        if outfile:
            self.out_filename = outfile
            self.launchgpg(mode)
    
    
    #------------------------------------------- HERE BE GTK SIGNAL DEFINITIONS
    
    def on_window1_destroy(self, widget, data=None):    gtk.main_quit()
    def action_quit(self, widget, data=None):         gtk.main_quit()
    
    
    def action_clear(self, widget, data=None):
        """Reset Statusbar, TextBuffer, Entry, gpg input & filenames."""
        self.set_stdstatus()        
        self.filemode_enablewidgets()
        self.buff.set_text                  ('')
        self.buff2.set_text                 ('')
        self.g_pass.set_text                ('')
        self.g_recip.set_text               ('')
        self.g_plaintext.set_sensitive      (False)
        self.g_plaintext.set_active         (True)
        self.g_chk_outfile.set_sensitive    (False)
        self.g_chk_outfile.set_active       (False)
        self.g_chooserbtn.set_filename      ('(None)')
        self.in_filename =                  None
        self.out_filename =                 None
        self.g.stdin =                      None
        while gtk.events_pending(): gtk.main_iteration()
    
    
    def action_clear_entry(self, widget, data=None, whatisthis=None):
        """Clear Entry widget."""
        widget.set_text('')
    
    
    def action_open(self, widget, data=None):
        """Replace contents of msg TextView's TextBuffer with contents of file."""
        filename = self.chooser_grab_filename('open')
        if not filename: return
        try:
            with open(filename) as f:  self.buff.set_text(f.read())
            if self.buff.get_char_count() < 1:
                self.infobar("<b>To operate on binary files, use the External Input File "
                             "chooser button.</b>", gtk.MESSAGE_WARNING)
        except:
            self.infobar("<b>Error opening file <span style='italic' size='smaller' face='monospace'>{}"
                         "</span> for reading.</b>".format(filename), gtk.MESSAGE_ERROR)
    
    
    def action_filemode_chooser_set(self, widget, data=None):
        """Ensure read access of file set by chooserwidget and notify user of next steps."""
        infile = self.g_chooserbtn.get_filename()
        if not access(infile, R_OK):
            self.infobar("<b>Error opening file <span style='italic' size='smaller' face='monospace'>"
                         "{}</span> for reading.</b> Choose a new file."
                         .format(infile), gtk.MESSAGE_ERROR)
            self.g_chooserbtn.set_filename('(None)')
            while gtk.events_pending(): gtk.main_iteration()
            return
        if self.g_signverify.get_active():
            self.g_chk_outfile.set_visible(True)
            # Set sigmode combobox to detached mode, because that seems most likely
            self.g_sigmode.set_active(2)
        # Set plaintext output checkbox state based on whether file is binary
        # Also, allow user to change it
        self.g_plaintext.set_sensitive(True)
        if self.g.test_file_isbinary(infile):
            self.g_plaintext.set_active(False)
        else:
            self.g_plaintext.set_active(True)
        self.g_statusbar.pop(self.status)
        self.g_statusbar.push(self.status, "Choose an action to perform on {!r}".format(infile))
        self.buff.set_text(
            "Ready to pass chosen filename directly to gpg.\n\nNext, choose an "
            "action (i.e., Encrypt, Decrypt, Sign, Verify).\nYou will be prompted "
            "for an output filename if necessary.\n\nClick the Clear button if "
            "you decide not to operate on file.".format(infile))
        self.filemode_enablewidgets(False)
        self.in_filename = infile
    
    
    def action_save(self, widget, data=None):
        """Save contents of msg TextView's TextBuffer to file."""
        if self.test_msgbuff_isempty("There's no text to save."): return
        filename = self.chooser_grab_filename('save')
        if not filename: return
        self.g_statusbar.push(self.status, "Saving {}".format(filename))
        while gtk.events_pending(): gtk.main_iteration()
        buffertext = self.buff.get_text(self.buff.get_start_iter(),
                                        self.buff.get_end_iter())
        try:
            with open(filename, 'w') as f:  f.write(buffertext)
            self.infobar("<b>Saved contents of Message area to file <span style='italic' size='smaller' "
                         "face='monospace'>{}</span></b>".format(filename))
        except:
            self.infobar("<b>Error opening file <span style='italic' size='smaller' face='monospace'>{}"
                         "</span> for writing.</b>".format(filename), gtk.MESSAGE_ERROR)
        self.g_statusbar.pop(self.status)
    
    
    def action_undo(self, widget, data=None):
        pass
    
    
    def action_redo(self, widget, data=None):
        pass
    
    
    def action_cut(self, widget, data=None):
        """Cut msg TextBuffer selection."""
        self.buff.cut_clipboard(gtk.clipboard_get(), True)
    
    
    def action_copy(self, widget, data=None):
        """Copy msg TextBuffer selection."""
        self.buff.copy_clipboard(gtk.clipboard_get())
    
    
    def action_paste(self, widget, data=None):
        """Paste clipboard into msg TextBuffer at selection."""
        self.buff.paste_clipboard(gtk.clipboard_get(), None, True)
    
    
    def action_copyall(self, widget, data=None):
        """Select whole msg TextBuffer contents and copy to clipboard."""
        if self.test_msgbuff_isempty("There's no text to copy."): return
        self.buff.select_range(self.buff.get_start_iter(),
                               self.buff.get_end_iter())
        self.buff.copy_clipboard(gtk.clipboard_get())
        self.infobar("<b>Copied contents of Message area to clipboard.</b>", timeout=3)
    
    
    def action_savecipherpref(self, widget, data=None):
        """Get current cipher setting from ComboBox & save it as default in argv[0]."""
        from sys import argv
        cbindex = self.g_cipher.get_active()
        cmd = split('sed -i "s/^        self.g_cipher.set_active(.)/        '
                    'self.g_cipher.set_active({})/" {}'.format(cbindex, argv[0]))
        try:
            check_output(cmd)
            self.infobar("<b>Successfully modified file <span style='italic' size='smaller' face='monospace'>"
                         "{}</span>, changing default cipher setting.</b>"
                         .format(argv[0]))
        except:
            self.infobar("<b>Saving cipher setting failed.</b> Try again while running "
                         "<span style='italic' size='smaller' face='monospace'>{}</span> as root."
                         .format(argv[0]), gtk.MESSAGE_ERROR, 7)
    
    
    def action_zoom(self, widget, data=None):
        """Increase/decrease font size of TextViews."""
        zoom = widget.get_label()[:7]
        if zoom in 'Increase':
            self.msgfontsz += 1
            self.errfontsz += 1
        elif zoom in 'Decrease':
            self.msgfontsz -= 1
            self.errfontsz -= 1
        self.g_msgtxtview.modify_font(FontDescription('monospace {}'.format(self.msgfontsz)))
        self.g_errtxtview.modify_font(FontDescription('normal {}'.format(self.errfontsz)))
    
    
    # 'Encrypt'/'Sign' button
    def action_encrypt(self, widget, data=None):
        """Encrypt or sign input."""
        if self.g_signverify.get_active():
            # Sign-only mode!
            if self.g_sigmode.get_active() == 0:
                action = 'embedsign'
            elif self.g_sigmode.get_active() == 1:
                action = 'clearsign'
            elif self.g_sigmode.get_active() == 2:
                action = 'detachsign'
            self.launchgpg(action)
        else:
            # Normal enc/dec mode
            self.launchgpg('enc')
    
    
    # 'Decrypt'/'Verify' button
    def action_decrypt(self, widget, data=None):
        """Decrypt or verify input."""
        if self.g_signverify.get_active():
            # Verify mode!
            self.launchgpg('verify')
        else:
            # Normal enc/dec mode
            self.launchgpg('dec')
    
    
    # 'Symmetric' checkbox toggle
    def action_toggle_symmetric(self, widget, data=None):
        """Toggle symmetric encryption (enable/disable certain widgets)."""
        # If entering toggled state, show pass entry, disable Asymm
        if self.g_symmetric.get_active():
            self.g_passlabel.set_sensitive      (True)
            self.g_pass.set_sensitive           (True)
            # If not in advanced mode, disable Asymm
            if not self.g_advanced.get_active():
                self.g_asymmetric.set_active        (False)
        # If leaving toggled state, hide pass entry
        else:
            self.g_passlabel.set_sensitive      (False)
            self.g_pass.set_sensitive           (False)
            # If trying to turn off Symm & Asymm isn't already on, turn it on
            if not self.g_asymmetric.get_active():
                self.g_asymmetric.set_active        (True)
    
    
    # 'Asymmetric' checkbox toggle
    def action_toggle_asymmetric(self, widget, data=None):
        """Toggle asymmetric encryption (enable/disable certain widgets)."""
        def setsensitive_asymmwidgets(x=True):
            self.g_reciplabel.set_sensitive     (x)
            self.g_recip.set_sensitive          (x)
            self.g_enctoself.set_sensitive      (x)
        # If entering toggled state
        if self.g_asymmetric.get_active():
            setsensitive_asymmwidgets           (True)
            self.g_signature.set_sensitive      (True)
            # If not in advanced mode, disable Symm
            if not self.g_advanced.get_active():
                self.g_symmetric.set_active         (False)
        # If leaving toggled state
        else:
            setsensitive_asymmwidgets           (False)
            self.g_enctoself.set_active         (False)
            # If not in advanced mode, unset signature
            if not self.g_advanced.get_active():
                self.g_signature.set_sensitive      (False)
                self.g_signature.set_active         (False)
            # If trying to turn off Asymm & Symm isn't already on, turn it on
            if not self.g_symmetric.get_active():
                self.g_symmetric.set_active         (True)
    
    
    # 'Advanced' checkbox toggle
    def action_toggle_advanced(self, widget, data=None):
        """Enable/disable encryption widgets for advanced mode."""
        # If entering the toggled state
        if self.g_advanced.get_active():
            self.g_signature.set_sensitive      (True)
        # If Leaving the toggled state
        else:
            if self.g_symmetric.get_active():
                if self.g_asymmetric.get_active():
                    self.g_asymmetric.set_active        (False)
                else:
                    self.g_signature.set_sensitive      (False)
                    self.g_signature.set_active         (False)
    
    
    # 'Sign/Verify' radio toggle
    def action_toggle_mode_signverify(self, widget, data=None):
        """Hide/show, change some widgets when switching modes."""
        self.set_stdstatus()
        def setvisible_encryptionwidgets(x=True):
            self.g_symmetric.set_visible    (x)
            self.g_asymmetric.set_visible   (x)
            self.g_advanced.set_visible     (x)
            self.g_enctoolbar.set_visible   (x)
        # If entering the toggled state ...
        if self.g_signverify.get_active():
            # Modify our button labels
            self.g_encrypt.set_label        ("Sign")
            self.g_decrypt.set_label        ("Verify")
            # Hide encryption toolbar & Symmetric, Asymmetric, Adv toggles
            setvisible_encryptionwidgets    (False)
            # Save state of AddSignature for switching back to Enc/Dec mode
            self.encdec_sig_state_sensitive = self.g_signature.get_sensitive()
            self.encdec_sig_state_active    = self.g_signature.get_active()
            # Desensitize AddSignature checkbox and turn it on
            self.g_signature.set_sensitive  (False)
            self.g_signature.set_active     (True)
            # Sensitize sigmode combobox & change active to Clearsign
            self.g_sigmode.set_sensitive    (True)
            if self.in_filename:
                self.g_sigmode.set_active       (2)
                self.g_chk_outfile.set_visible  (True)
            else:
                self.g_sigmode.set_active       (1)
        # If leaving the toggled state, we have some things to reverse
        else:
            self.g_encrypt.set_label        ("_Encrypt")
            self.g_decrypt.set_label        ("_Decrypt")
            self.g_chk_outfile.set_visible  (False)
            setvisible_encryptionwidgets    (True)
            self.g_signature.set_sensitive  (self.encdec_sig_state_sensitive)
            self.g_signature.set_active     (self.encdec_sig_state_active)
            self.g_sigmode.set_sensitive    (False)
            self.g_sigmode.set_active       (0)
    
    
    def action_toggle_defaultkey(self, widget=None, data=None):
        """Hide/show Entry widget for setting localuser."""
        if self.g_chk_defkey.get_active():
            self.g_defaultkey.set_visible   (True)
        else:
            self.g_defaultkey.set_visible   (False)
    
    # 'Add signature' checkbox toggle
    def action_toggle_signature(self, widget, data=None):
        """Hide/show some widgets when toggling adding of a signature to input."""
        def setvisible_signingwidgets(x=True):
            self.g_sigmode.set_visible      (x)
            self.g_hash.set_visible         (x)
            self.g_hashlabel.set_visible    (x)
            self.g_chk_defkey.set_visible   (x)
        # Entering toggled state
        if self.g_signature.get_active():
            setvisible_signingwidgets       (True)
        # Leaving toggled state
        else:
            setvisible_signingwidgets       (False)
            self.g_chk_defkey.set_active    (False)
    
    
    def action_toggle_taskstatus(self, widget, data=None):
        """Show/hide side pane containing gpg stderr output."""
        if self.g_taskstatus.get_active():
            self.g_frame2.set_visible       (True)
        else:
            self.g_frame2.set_visible       (False)
    
    
    def action_toggle_wordwrap(self, widget, data=None):
        """Toggle word wrapping for main message TextView."""
        if self.g_wrap.get_active():
            self.g_msgtxtview.set_wrap_mode(gtk.WRAP_WORD)
        else:
            self.g_msgtxtview.set_wrap_mode(gtk.WRAP_NONE)
    
    
    #-------------------------------------------------------- MAIN GPG FUNCTION
    def launchgpg(self, action):
        """Manage I/O between Gtk objects and our GpgInterface object."""
        
        ### PREPARE GpgInterface.gpg() ARGS
        passwd = None ; recip = None ; localuser = None
        # enctoself
        enctoself =  self.g_enctoself.get_active()
        # symmetric & passwd
        symmetric = self.g_symmetric.get_active()
        if symmetric:
            passwd = self.g_pass.get_text()
            if not passwd:  passwd = None  # If passwd was '' , set to None
            # For now, allowing to skip entering passwd, which triggers gpg-agent
        # recip
        asymmetric = self.g_asymmetric.get_active()
        if asymmetric:
            recip = self.g_recip.get_text()
            if not recip:  recip = None  # If recip was '' , set to None
        # cipher, base64
        cipher = self.grab_activetext_combobox(self.g_cipher)
        base64 = self.g_plaintext.get_active()
        # encsign
        if action in 'enc':
            encsign = self.g_signature.get_active()
        else:
            encsign = False
        # digest
        digest = self.grab_activetext_combobox(self.g_hash)
        # verbose
        verbose = self.g_gpgverbose.get_active()
        # alwaystrust (setting True would allow encrypting to untrusted keys,
        #   which is how the nautilus-encrypt tool from seahorse-plugins works)
        alwaystrust = False
        # localuser
        if self.g_chk_defkey.get_active():
            localuser = self.g_defaultkey.get_text()
            if not localuser:  localuser = None
        
        # FILE INPUT MODE PREP
        if self.in_filename and not self.out_filename:
            
            if base64 or action in 'clearsign':
                outfile = self.in_filename + '.asc'
            elif action in 'detachsign':
                outfile = self.in_filename + '.sig'
            else:
                outfile = self.in_filename + '.gpg'
            
            if action in 'dec':
                outfile = self.in_filename[:-4]
            
            if action not in 'verify':
                if self.g_signverify.get_active() and not self.g_chk_outfile.get_active():
                    pass
                else:
                    outfile = self.chooser_grab_filename('save', outfile)
                    if outfile:
                        self.out_filename = outfile
                    else:
                        return
        
        # TEXT INPUT PREP
        else:
            
            # Make sure textview has a proper message in it
            if self.test_msgbuff_isempty("You haven't entered any input yet."):
                return False
            
            # Make TextView immutable to changes
            self.g_msgtxtview.set_sensitive(False)
            
            # Save textview buffer to GpgInterface.stdin
            self.g.stdin = self.buff.get_text(self.buff.get_start_iter(),
                                              self.buff.get_end_iter())
        
        # Set working status + spinner
        if action in {'embedsign', 'clearsign', 'detachsign'}:
            status = "Signing input ..."
        elif action in 'verify':
            status = "Verifying input ..."
        else:
            status = "{}rypting input ...".format(action.title())
        self.g_statusbar.push(self.status, status)
        self.g_activityspin.set_visible(True)
        self.g_activityspin.start()
        while gtk.events_pending(): gtk.main_iteration()
        
        # ATTEMPT EN-/DECRYPTION
        retval = self.g.gpg(action, encsign, digest, localuser, base64,
                            symmetric, passwd,
                            asymmetric, recip, enctoself, cipher,
                            self.in_filename, self.out_filename,
                            verbose, alwaystrust)
        
        self.g_activityspin.stop()
        self.g_activityspin.set_visible(False)
        self.g_statusbar.pop(self.status)
        self.buff2.set_text(self.g.stderr)
        
        # FILE INPUT MODE CLEANUP
        if self.in_filename:
            
            if retval:  # Success!
                
                self.g_chooserbtn.set_filename('(None)')
                self.filemode_enablewidgets()
                self.g_chk_outfile.set_visible(False)
                if self.g_signverify.get_active():
                    self.g_sigmode.set_active(1)
                else:
                    self.g_sigmode.set_active(0)
                self.set_stdstatus()
                while gtk.events_pending(): gtk.main_iteration()
                
                # Replace textview buffer with success message
                if action in {'enc', 'dec'}:
                    self.infobar("<b>Saved {}rypted copy of input to:\n"
                                 "<span style='italic' size='smaller' face='monospace'>{}</span></b>"
                                 .format(action, self.out_filename))
                
                elif action in {'embedsign', 'clearsign'}:
                    self.infobar("<b>Saved signed copy of input to:\n"
                                 "<span style='italic' size='smaller' face='monospace'>{}</span></b>"
                                 .format(outfile))
                
                elif action in 'detachsign':
                    self.infobar("<b>Saved detached signature of input to:\n"
                                 "<span style='italic' size='smaller' face='monospace'>{}</span></b>"
                                 .format(outfile))
                
                elif action in 'verify':
                    self.infobar("<b>Good signature verified.</b>", timeout=4)
                self.buff.set_text('')
                
                # Reset filenames
                self.in_filename = None ; self.out_filename = None
                
                # Disable plaintext CheckButton
                self.g_plaintext.set_sensitive(False)
                self.g_plaintext.set_active(True)
            
            # Fail!
            else:
                
                if action in 'verify':
                    self.infobar("<b>Signature could not be verified.</b> See<i> Task "
                                 "Status </i> for details.", gtk.MESSAGE_WARNING, 7)
                    """ Not sure about this, but I'm gonna go with forcing user to press Clear for now
                    self.g_chooserbtn.set_filename('(None)')
                    self.g_chk_outfile.set_visible(False)
                    self.filemode_enablewidgets()
                    self.set_stdstatus()
                    self.buff.set_text('')
                    self.in_filename = None
                    self.g_plaintext.set_sensitive(False)
                    self.g_plaintext.set_active(True)
                    """
                    return
                    
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                
                self.infobar("<b>Problem {}ing file.</b> See<i> Task Status </i> for details.\n"
                             "Try again with a different passphrase or select<i> Clear </i> "
                             "to do something else.".format(action), gtk.MESSAGE_ERROR, 8)
        
        # TEXT INPUT MODE CLEANUP
        else:
            
            self.set_stdstatus()
            self.g_msgtxtview.set_sensitive(True)
            self.g.stdin = None
            
            # Success!
            if retval:
                if action in 'verify':
                    self.infobar("<b>Good signature verified.</b>", timeout=4)
                else:
                    # Set TextBuffer to gpg stdout
                    self.buff.set_text(self.g.stdout)
            
            # Fail!
            else:
                if action in 'verify':
                    self.infobar("<b>Signature could not be verified.</b> See<i> "
                                 "Task Status </i> for details.", gtk.MESSAGE_WARNING, 7)
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar("<b>Problem asymmetrically encrypting input.</b> If you don't "
                                 "want to enter recipients and\nyou don't want to select<i> Enc "
                                 "To Self</i>, you must add one of the following to your\ngpg.conf "
                                 "file: <b><span size='smaller' face='monospace'>default-recipient-"
                                 "self</span></b> or <b><span size='smaller' face='monospace'>"
                                 "default-recipient <i>name</i></span></b>",
                                 gtk.MESSAGE_ERROR, 0)
                    return
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar("<b>Problem {}ing input.</b> See<i> Task Status </i> for details."
                             .format(action), gtk.MESSAGE_ERROR)
    
    
    #------------------------------------------------------------- ABOUT DIALOG
    def action_about(self, widget, data=None):
        if self.about_dialog: 
            self.about_dialog.present()
            return
        authors = ["Ryan Sawhill <ryan@b19.org>"]
        about_dialog = gtk.AboutDialog()
        about_dialog.set_transient_for(self.g_window)
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name('a8crypt')
        about_dialog.set_version('0.9.9.12')
        about_dialog.set_copyright("Copyright \xc2\xa9 2012 Ryan Sawhill")
        about_dialog.set_website('http://github.com/ryran/a8crypt')
        about_dialog.set_comments("Encryption, decryption, & signing via gpg/gpg2")
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
        self.g_window.show()
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True
        gtk.main()



if __name__ == "__main__":
    
    a8 = AEightCrypt()
    a8.main()
