#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# a8crypt v0.9.9.4 last mod 2012/01/22
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
# TODO: Replace Glade xml with real pygtk funness once gui is more finalized
# TODO: Get application icon & icons for encrypt, decrypt, sign, verify buttons
# TODO: Preferences dialog that can save settings to a config file?
# TODO: Opening files just feels clunky. It's not the priority of this app, but
#       still, I'd like to figure out a better way.

# Modules from the Standard Library
import gtk
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
        action=     None,   # One of: enc, dec, sign, signclear, signdetach, verify
        encsign=    False,  # Add '--sign' when encrypting?
        digest=     None,   # One of: sha256, sha1, etc; None == use gpg defaults
        base64=     True,   # Add '--armor' when encrypting/signing?
        symmetric=  False,  # Add '--symmetric'?
        passwd=     None,   # Passphrase for symmetric
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
        
        action=     None,   # One of: enc, dec, sign, signclear, signdetach, verify
        encsign=    False,  # Add '--sign' when encrypting?
        digest=     None,   # One of: sha256, sha1, etc; None == use gpg defaults
        base64=     True,   # Add '--armor' when encrypting/signing?
        symmetric=  False,  # Add '--symmetric'?
        passwd=     None,   # Passphrase for symmetric
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
        enctoself: Self is assumed to be first key returned by gpg --list-secret-keys
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
            if cipher:
                cmd.append('--cipher-algo')
                cmd.append(cipher)
            if enctoself:
                cmd.append('--encrypt')
                cmd.append('--recipient')
                cmd.append(self.get_gpgdefaultkey())
            if recip:
                if not enctoself:   cmd.append('--encrypt')
                while recip[-1] == ' ' or recip[-1] == ';':
                    recip = recip.strip()
                    recip = recip.strip(';')
                for r in recip.split(';'):
                    cmd.append('--recipient')
                    cmd.append(r)
        
        # Decrypt opts
        elif action in 'dec':   cmd.append('--decrypt')
        
        # Sign opts
        elif action in {'sign', 'signclear', 'signdetach'}:
            if action in 'sign':            cmd.append('--sign')
            elif action in 'signclear':     cmd.append('--clearsign')
            elif action in 'signdetach':    cmd.append('--detach-sign')
            if digest:
                cmd.append('--digest-algo')
                cmd.append(digest)
        
        # Verify opts
        elif action in 'verify':        cmd.append('--verify')
        
        # Wouldn't hurt to use armor for all, but it only works with these 3
        if action in {'enc', 'sign', 'signdetach'}:
            if base64:
                cmd.append('--armor')
        
        # Action-independent opts
        if useagent:
            if self.GPG in 'gpg':   cmd.append('--use-agent')
        else:
            if self.GPG in 'gpg':   cmd.append('--no-use-agent')
            else:                   cmd.append('--batch')
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
  <object class="GtkImage" id="image8">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="stock">gtk-media-forward</property>
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
        <col id="0" translatable="yes">SHA512</col>
      </row>
      <row>
        <col id="0" translatable="yes">SHA384</col>
      </row>
      <row>
        <col id="0" translatable="yes">SHA256</col>
      </row>
      <row>
        <col id="0" translatable="yes">SHA224</col>
      </row>
      <row>
        <col id="0" translatable="yes">RIPEMD160</col>
      </row>
      <row>
        <col id="0" translatable="yes">SHA1</col>
      </row>
      <row>
        <col id="0" translatable="yes">MD5</col>
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
    <property name="default_width">680</property>
    <property name="default_height">480</property>
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
                        <signal name="activate" handler="on_save_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_open_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_quit_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_clear_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_cut">
                        <property name="label">gtk-cut</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_cut_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_copy_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_paste_activate" swapped="no"/>
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
                        <signal name="activate" handler="on_savecipherpref_activate" swapped="no"/>
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
                <property name="label" translatable="yes">View</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="viewmenu">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
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
                        <signal name="toggled" handler="on_toggle_taskstatus_toggled" swapped="no"/>
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
            <property name="spacing">1</property>
            <child>
              <object class="GtkLabel" id="space1a">
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
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="on_button_encrypt_clicked" swapped="no"/>
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
                    <property name="use_underline">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="on_button_decrypt_clicked" swapped="no"/>
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
              <object class="GtkRadioButton" id="toggle_mode_encdec">
                <property name="label" translatable="yes">Enc/Dec Mode</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Encrypt/decrypt/encrypt+sign mode</property>
                <property name="use_underline">True</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">3</property>
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
                <signal name="toggled" handler="on_toggle_mode_symmetric_toggled" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">4</property>
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
                <signal name="toggled" handler="on_toggle_mode_asymmetric_toggled" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_advanced">
                <property name="label" translatable="yes">Ad_v.</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Allow mixing symmetric encryption with asymmetric and signing

When creating a signed + symmetrically-encrypted message, anything in the passphrase entry box will be ignored -- gpg-agent will need to ask for both the symmetric encryption key (passphrase) and the passphrase to your secret key</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="on_toggle_advanced_toggled" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">6</property>
                <property name="position">6</property>
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
                <property name="padding">4</property>
                <property name="position">7</property>
              </packing>
            </child>
            <child>
              <object class="GtkRadioButton" id="toggle_mode_signverify">
                <property name="label" translatable="yes">Si_gn/Verify Mode</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="tooltip_text" translatable="yes">Sign-only/verify-only mode

For adding a signature to a message without encrypting it or for verifying a signed message that isn't encrypted</property>
                <property name="use_underline">True</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
                <property name="group">toggle_mode_encdec</property>
                <signal name="toggled" handler="on_toggle_mode_signverify_toggled" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">4</property>
                <property name="position">8</property>
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
                <property name="width_chars">8</property>
                <property name="truncate_multiline">True</property>
                <property name="shadow_type">etched-in</property>
                <property name="invisible_char_set">True</property>
                <property name="primary_icon_activatable">False</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="padding">1</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="space2b">
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
                <property name="sensitive">False</property>
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
                <property name="primary_icon_activatable">False</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
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
                <property name="label" translatable="yes">Enc to se_lf</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">Tells gpg to encrypt the message to you (i.e., with your public key) in addition to any other recipients (or if in Advanced mode and performing symmetric encryption with a passphrase, then.. in addition to that)</property>
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
              <object class="GtkLabel" id="space2c">
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
                <property name="tooltip_text" translatable="yes">[ Not used when decrypting or verifying ]

Configures symmetric encryption cipher algorithm

In asymmetric mode, the chosen cipher is used in concert with recipients' pubkeys for encryption

With 'Default', gpg decides the algorithm based on local system settings (weighing them against the preferences of recipient pubkeys if performing asymmetric encryption)</property>
                <property name="model">liststore_ciphers</property>
                <property name="active">0</property>
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
            <property name="position">2</property>
          </packing>
        </child>
        <child>
          <object class="GtkHPaned" id="hpaned1">
            <property name="visible">True</property>
            <property name="can_focus">True</property>
            <property name="position">540</property>
            <property name="position_set">True</property>
            <child>
              <object class="GtkFrame" id="frame1">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="border_width">3</property>
                <property name="label_xalign">0</property>
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
                      </object>
                    </child>
                  </object>
                </child>
                <child type="label">
                  <object class="GtkLabel" id="label1">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <property name="label" translatable="yes">_Message Input/Output</property>
                    <property name="use_underline">True</property>
                    <property name="mnemonic_widget">textview1</property>
                  </object>
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
                    <property name="label" translatable="yes">Task Status</property>
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
            <property name="position">3</property>
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
              <object class="GtkCheckButton" id="toggle_plaintext">
                <property name="label" translatable="yes">Plain_text output</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[ Not used when decrypting or verifying ]

Tells gpg to output text instead of binary data when encrypting and signing

This is kind of output is commonly called 'base64-encoded' or 'ASCII-armored'

On opening a file, this is set based on whether the file is detected as binary data or text, but it can be overridden</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="active">True</property>
                <property name="draw_indicator">True</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkVSeparator" id="vseparator3a">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="padding">12</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkCheckButton" id="toggle_signature">
                <property name="label" translatable="yes">Add sig_nature:</property>
                <property name="use_action_appearance">False</property>
                <property name="visible">True</property>
                <property name="sensitive">False</property>
                <property name="can_focus">True</property>
                <property name="receives_default">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[ Not used when decrypting or verifying ]

Tells gpg to use your secret key to sign the input

This will likely require you to interact with gpg-agent -- gpg needs your secret key's passphrase in order to use your key to sign the message</property>
                <property name="use_underline">True</property>
                <property name="focus_on_click">False</property>
                <property name="draw_indicator">True</property>
                <signal name="toggled" handler="on_toggle_signature_toggled" swapped="no"/>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">3</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_sigmode">
                <property name="sensitive">False</property>
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[ Not used when decrypting or verifying ]

This allows you to choose the signature type for signing in Sign/Verify mode

Embedded: encodes the signature and message together (this is most often used along with encryption)

Clearsign: wraps the message with a plaintext signature

Detached: creates a separate signature that does not contain the message</property>
                <property name="model">liststore_sigmodes</property>
                <property name="active">0</property>
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
                <property name="position">4</property>
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
                <property name="position">5</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_combobox_hash">
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">Digest _Hash:</property>
                <property name="use_underline">True</property>
                <property name="mnemonic_widget">combobox_hash</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">6</property>
              </packing>
            </child>
            <child>
              <object class="GtkComboBox" id="combobox_hash">
                <property name="can_focus">False</property>
                <property name="has_tooltip">True</property>
                <property name="tooltip_text" translatable="yes">[ Not used when decrypting or verifying ]

Configures message digest algorithm (used for hashing message, i.e., creating your signature)

With 'Default', gpg decides the algorithm based on local system settings, weighing them against the preferences of your secret key</property>
                <property name="model">liststore_hashes</property>
                <property name="active">0</property>
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
                <property name="position">7</property>
              </packing>
            </child>
          </object>
          <packing>
            <property name="expand">False</property>
            <property name="fill">True</property>
            <property name="position">4</property>
          </packing>
        </child>
        <child>
          <object class="GtkHBox" id="hbox4">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <child>
              <object class="GtkSpinner" id="spinner1">
                <property name="width_request">16</property>
                <property name="visible">False</property>
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
            <property name="position">5</property>
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
        self.g_window = builder.get_object('window1')
        # Menu items
        self.g_taskstatus = builder.get_object('toggle_taskstatus')
        self.g_gpgverbose = builder.get_object('toggle_gpgverbose')
        # Top toolbar
        self.g_encrypt = builder.get_object('button_encrypt')
        self.g_decrypt = builder.get_object('button_decrypt')
        self.g_symmetric = builder.get_object('toggle_mode_symmetric')
        self.g_asymmetric = builder.get_object('toggle_mode_asymmetric')
        self.g_advanced = builder.get_object('toggle_advanced')
        self.g_signverify = builder.get_object('toggle_mode_signverify')
        # Second top toolbar
        self.g_enctoolbar = builder.get_object('hbox2')
        self.g_passlabel = builder.get_object('label_entry_pass')
        self.g_pass = builder.get_object('entry_pass')
        self.g_reciplabel = builder.get_object('label_entry_recip')
        self.g_recip = builder.get_object('entry_recip')
        self.g_enctoself = builder.get_object('toggle_enctoself')
        self.g_cipherlabel = builder.get_object('label_combobox_cipher')
        self.g_cipher = builder.get_object('combobox_cipher')
        # Middle input
        self.g_msgtextview = builder.get_object('textview1')
        self.g_frame2 = builder.get_object('frame2')
        self.g_stderrtextview = builder.get_object('textview2')
        # Bottom toolbar
        self.g_plaintext = builder.get_object('toggle_plaintext')
        self.g_signature = builder.get_object('toggle_signature')
        self.g_sigmode = builder.get_object('combobox_sigmode')
        self.g_hashlabel = builder.get_object('label_combobox_hash')
        self.g_hash = builder.get_object('combobox_hash')
        # Statusbar
        self.g_statusbar = builder.get_object('statusbar')
        self.g_activityspinner = builder.get_object('spinner1')
        
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
        
        # Set TextView fonts
        self.g_msgtextview.modify_font(FontDescription('monospace 10'))
        self.g_stderrtextview.modify_font(FontDescription('monospace 8'))
        
        buff2 = self.g_stderrtextview.get_buffer()
        buff2.set_text("Output from each call to gpg will be displayed here. "
                       "Check out the View menu for some choices.")
        
        # Initialize main Statusbar
        self.status = self.g_statusbar.get_context_id('main')
        self.g_statusbar.push(self.status, "Enter message to encrypt/decrypt")
    
    
    #------------------------------------------- HERE BE GTK SIGNAL DEFINITIONS    
    
    # Death!
    def on_window1_destroy(self, widget, data=None):    gtk.main_quit()
    def on_quit_activate(self, menuitem, data=None):    gtk.main_quit()
    
    
    # 'Open file' menu item
    def on_open_activate(self, menuitem, data=None):    self.open_file()
    
    
    # 'Save text buffer' menu item
    def on_save_activate(self, menuitem, data=None):
        if self.sanitycheck_textviewbuff('save'):
            filename = self.chooser_grab_filename('save')
            if filename: self.write_file(filename)
    
    
    # 'Cut' menu item
    def on_cut_activate(self, menuitem, data=None):
        buff = self.g_msgtextview.get_buffer()
        buff.cut_clipboard(gtk.clipboard_get(), True)
    
    
    # 'Copy' menu item
    def on_copy_activate(self, menuitem, data=None):
        buff = self.g_msgtextview.get_buffer()
        buff.copy_clipboard(gtk.clipboard_get())
    
    
    # 'Paste' menu item
    def on_paste_activate(self, menuitem, data=None):
        buff = self.g_msgtextview.get_buffer()
        buff.paste_clipboard(gtk.clipboard_get(), None, True)
    
    
    # 'Clear' menu item 
    def on_clear_activate(self, menuitem, data=None):
        """Reset Statusbar, TextBuffer, Entry, gpg input & filename."""
        self.g_statusbar.pop(self.status)
        if self.g_signverify.get_active():
            status = "Enter message to sign/verify"
        else:
            status = "Enter message to encrypt/decrypt"
        self.g_statusbar.push(self.status, status)
        buff = self.g_msgtextview.get_buffer()
        buff.set_text('')
        buff.set_modified(False)
        self.g_msgtextview.set_sensitive(True)
        buff2 = self.g_stderrtextview.get_buffer()
        buff2.set_text('')
        self.g_pass.set_text('')
        self.g_recip.set_text('')
        self.g_plaintext.set_sensitive(False)
        self.g_plaintext.set_active(True)
        self.in_filename = None
        self.out_filename = None
        self.g.stdin = None
    
    
    # 'Make cipher selection default' menu item
    def on_savecipherpref_activate(self, menuitem, data=None):
        """Get current cipher setting from ComboBox & save it as default in argv[0]."""
        from sys import argv
        cbindex = self.g_cipher.get_active()
        cmd = split('sed -i "s/^        self.g_cipher.set_active(.)/        '
                    'self.g_cipher.set_active({})/" {}'.format(cbindex, argv[0]))
        try:
            check_output(cmd)
        except:
            show_errmsg("Saving cipher setting failed. Try again while running {} "
                        "as root.".format(argv[0]))
    
    
    # 'Encrypt' button
    def on_button_encrypt_clicked(self, menuitem, data=None):
        if self.g_signverify.get_active():
            # Sign-only mode!
            if self.g_sigmode.get_active() == 0:
                action = 'sign'
            elif self.g_sigmode.get_active() == 1:
                action = 'signclear'
            elif self.g_sigmode.get_active() == 2:
                action = 'signdetach'
            self.launchgpg(action)
        else:
            # Normal enc/dec mode
            self.launchgpg('enc')
    
    
    # 'Decrypt' button
    def on_button_decrypt_clicked(self, menuitem, data=None):
        if self.g_signverify.get_active():
            # Verify mode!
            self.launchgpg('verify')
        else:
            # Normal enc/dec mode
            self.launchgpg('dec')
    
    
    # 'Symmetric' radio toggle
    def on_toggle_mode_symmetric_toggled(self, widget, data=None):
        
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
    
    
    # 'Asymmetric' radio toggle
    def on_toggle_mode_asymmetric_toggled(self, widget, data=None):
        
        # If entering toggled state, show recip entry + addtl checkboxes
        if self.g_asymmetric.get_active():
            self.g_reciplabel.set_sensitive     (True)
            self.g_recip.set_sensitive          (True)
            self.g_enctoself.set_sensitive      (True)
            self.g_signature.set_sensitive      (True)
            # If not in advanced mode, disable Symm
            if not self.g_advanced.get_active():
                self.g_symmetric.set_active         (False)
        
        # If leaving toggled state, hide recip entry
        else:
            self.g_reciplabel.set_sensitive     (False)
            self.g_recip.set_sensitive          (False)
            self.g_enctoself.set_sensitive      (False)
            self.g_enctoself.set_active         (False)
            # If not in advanced mode, unset signature
            if not self.g_advanced.get_active():
                self.g_signature.set_sensitive      (False)
                self.g_signature.set_active         (False)
            # If trying to turn off Asymm & Symm isn't already on, turn it on
            if not self.g_symmetric.get_active():
                self.g_symmetric.set_active         (True)
    
    
    # 'Advanced' checkbox toggle
    def on_toggle_advanced_toggled(self, widget, data=None):
                
        if self.g_advanced.get_active():    # If entering the toggled state
            #if self.g_symmetric.get_active():
            self.g_signature.set_sensitive      (True)
        
        else:                               # If Leaving the toggled state
            if self.g_symmetric.get_active():
                if self.g_asymmetric.get_active():
                    self.g_asymmetric.set_active        (False)
                else:
                    self.g_signature.set_sensitive      (False)
                    self.g_signature.set_active         (False)
    
    
    # 'Sign/Verify' radio toggle
    def on_toggle_mode_signverify_toggled(self, widget, data=None):
        
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
            self.encdec_sig_state_active = self.g_signature.get_active()
            # Desensitize AddSignature checkbox and turn it on
            self.g_signature.set_sensitive  (False)
            self.g_signature.set_active     (True)
            # Sensitize sigmode combobox & change active to Clearsign
            self.g_sigmode.set_sensitive    (True)
            self.g_sigmode.set_active       (1)
            # Status
            self.g_statusbar.push           (self.status, "Enter message to sign/verify")
        
        # If leaving the toggled state, we have some things to reverse
        else:
            self.g_encrypt.set_label        ("_Encrypt")
            self.g_decrypt.set_label        ("_Decrypt")
            setvisible_encryptionwidgets    (True)
            self.g_signature.set_sensitive  (self.encdec_sig_state_sensitive)
            self.g_signature.set_active     (self.encdec_sig_state_active)
            self.g_sigmode.set_sensitive    (False)
            self.g_sigmode.set_active       (0)
            self.g_statusbar.pop            (self.status)
    
    
    # 'Add signature' toggle    
    def on_toggle_signature_toggled(self, widget, data=None):
        
        # Entering toggled state
        if self.g_signature.get_active():
            self.g_hash.set_visible         (True)
            self.g_hashlabel.set_visible    (True)
            self.g_sigmode.set_visible      (True)
        
        # Leaving toggled state
        else:
            self.g_hash.set_visible         (False)
            self.g_hashlabel.set_visible    (False)
            self.g_sigmode.set_visible      (False)
    
    
    # 'Task Status' checkbox toggle
    def on_toggle_taskstatus_toggled(self, menuitem, data=None):
        if self.g_taskstatus.get_active():
            self.g_frame2.set_visible       (True)
        else:
            self.g_frame2.set_visible       (False)
    
    
    #--------------------------------------------------------- HELPER FUNCTIONS
    
    # This is called when user tries to save or en/decrypt or sign/verify
    def sanitycheck_textviewbuff(self, choice):
        buff = self.g_msgtextview.get_buffer()
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
                if choice in {'enc','dec'}:     choice = "{}rypt".format(choice)
                elif not choice in 'verify':    choice = "Sign"
                show_errmsg(
                    "Your last file en/decryption operation succeeded. Selecting "
                    "{!r} at this point would only attempt to {} the message you "
                    "see in the main window. Either load a new file from the "
                    "'Open file' menu, or type/paste a new message"
                    .format(choice.title(), choice))
            return False
        return True


    # Generic file chooser for opening or saving
    def chooser_grab_filename(self, mode, save_suggestion=None):
        """Present file chooser dialog and return filename or None."""
        
        filename = None
        
        cmd = ("gtk.FileChooserDialog('{0} File...', self.g_window, "
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
        self.g_statusbar.push(self.status, "Saving {}".format(filename))
        
        while gtk.events_pending(): gtk.main_iteration()
        
        # Get contents of buffer
        buff = self.g_msgtextview.get_buffer()
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
        self.g_statusbar.pop(self.status)
    
    
    def open_file(self):
        """Choose a filename to pass directly to gpg (without loading into textview).
        
        For very large files, it would be good to avoid pasting them into the
        GtkWindow and then having to pass that input (and resulting output) through
        Popen.communicate() ... right? Not to mention binary files.
        
        This method prompts for a filename to open (for gpg input) and then an output
        filename (to save gpg output to) and sets up everything to make it possible
        for AEightCrypt.launchgpg() to pass the file NAMES directly to the gpg
        subprocess, without ever opening the files in Python.
        """
        
        infile = None ; outfile = None
        
        while True:
            # Prompt for a file to open
            infile = self.chooser_grab_filename('open')
            if not infile: return  # Cancel opening if user hit Cancel
            if access(infile, R_OK): break  # We're done if we can read infile
            show_errmsg("Could not open file {0!r} for reading. Choose a new file."
                        .format(infile))
        
        while True:
            if self.g_signverify.get_active(): break
            # Prompt for name to save output to
            outfile = self.chooser_grab_filename('save', infile)
            if not outfile: return  # Return if user hit Cancel
            # TODO: Get Gtk.FileChooser's confirm-overwrite signal to handle this:
            if infile != outfile: break  # We're done if we got 2 different files
            show_errmsg("Simultaneously reading from & writing to a file is a "
                        "baaad idea. Choose a different output filename.")
        
        # Set plaintext CheckButton toggle
        self.g_plaintext.set_sensitive(True)
        if self.g.test_file_isbinary(infile):
            self.g_plaintext.set_active(False)
        
        # Ready message to status; disable text view & replace it with a message
        if self.g_signverify.get_active():
            status = "Ready to sign or verify file: {}".format(infile)
            msg = ("Choose 'Sign' or 'Verify' to have {0} load file"
                   "\n   {1!r}\nas input.\n\nIf signing, output file will have the same "
                   "name with a new\nextension appended -- if using plaintext output, "
                   "'.asc';\notherwise, either '.sig' for detached signatures, or"
                   "\n'.gpg' for embedded ones.\n\nIf verifying, no new files are "
                   "created; gpg just checks that\nthe signature is good."
                   .format(self.g.GPG.upper(), infile))
        else:
            status = "Ready to encrypt or decrypt file: {}".format(infile)
            msg = ("Choose 'Encrypt' or 'Decrypt' to have {0} load file"
                   "\n   {1!r}\nas input, saving output to file\n   {2!r}"
                   .format(self.g.GPG.upper(), infile, outfile))
        self.g_statusbar.push(self.status, status)
        self.g_msgtextview.set_sensitive(False)
        buff = self.g_msgtextview.get_buffer()
        buff.set_text(msg)
        buff.set_modified(False)
        
        # Promote our filenames
        self.in_filename = infile
        self.out_filename = outfile
    
    
    def grab_activetext_combobox(self, combobox):
        cbmodel = combobox.get_model()
        cbindex = combobox.get_active()
        if cbindex == 0:
            return None  # If first choice is selected, i.e. 'Default'
        else:
            return cbmodel[cbindex][0]
    
    
    #-------------------------------------------------------- MAIN GPG FUNCTION
    def launchgpg(self, action):
        """Manage I/O between Gtk objects and our GpgInterface object."""

        ### PREPARE GpgInterface.gpg() ARGS
        passwd = None ; recip = None
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
            if not recip:
                recip = None  # If recip was '' , set to None
                if not enctoself and action in 'enc':
                    show_errmsg("For asymmetric encryption, you must either select "
                                "'Enc to self' or enter at least one recipient.")
                    return False
        # cipher, base64
        cipher = self.grab_activetext_combobox(self.g_cipher)
        base64 = self.g_plaintext.get_active()
        # encsign
        if action in 'encrypt':
            encsign = self.g_signature.get_active()
        else:
            encsign = False
        # digest
        digest = self.grab_activetext_combobox(self.g_hash)
        # verbose
        verbose = self.g_gpgverbose.get_active()
        # alwaystrust
        alwaystrust = False
        
        buff = self.g_msgtextview.get_buffer()
        
        # TEXT INPUT PREP
        if not self.in_filename:
            
            # Make sure textview has a proper message in it
            if not self.sanitycheck_textviewbuff(action):
                return False
            
            # Make TextView immutable to changes
            self.g_msgtextview.set_sensitive(False)
            
            # Save textview buffer to GpgInterface.stdin
            self.g.stdin = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
        
        # Set working status + spinner
        if action in {'sign', 'signclear', 'signdetach'}:
            status = "Signing input ..."
        elif action in 'verify':
            status = "Verifying input ..."
        else:
            status = "{}rypting input ...".format(action.title())
        self.g_statusbar.push(self.status, status)
        self.g_activityspinner.set_visible(True)
        self.g_activityspinner.start()
        while gtk.events_pending(): gtk.main_iteration()
        
        # ATTEMPT EN-/DECRYPTION
        retval = self.g.gpg(action, encsign, digest, base64,
                            symmetric, passwd, recip, enctoself, cipher,
                            self.in_filename, self.out_filename,
                            verbose, alwaystrust)
        
        self.g_activityspinner.stop()
        self.g_activityspinner.set_visible(False)
        buff2 = self.g_stderrtextview.get_buffer()
        buff2.set_text(self.g.stderr)
        
        # FILE INPUT MODE CLEANUP
        if self.in_filename:
            
            # Success!
            if retval:
                
                # Clear last two statusbar messages to get back to default
                # 'crypting input' and 'Ready to encrypt or decrypt file'
                self.g_statusbar.pop(self.status) ; self.g_statusbar.pop(self.status)
                
                # Replace textview buffer with success message
                if action in {'enc', 'dec'}:
                    msg = ("SUCCESS!\n\n{} saved new {}rypted file to:\n{}"
                           .format(self.g.GPG.upper(), action, self.out_filename))
                
                elif action in {'sign', 'signclear'}:
                    if base64 or action in signclear:
                        outfile = "{}.asc".format(self.in_filename)
                    else:
                        outfile = "{}.gpg".format(self.in_filename)
                    msg = ("SUCCESS!\n\n{} saved new signed file to:\n{}"
                           .format(self.g.GPG.upper(), outfile))
                
                elif action in 'signdetach':
                    if base64:
                        outfile = "{}.asc".format(self.in_filename)
                    else:
                        outfile = "{}.sig".format(self.in_filename)
                    msg = ("SUCCESS!\n\n{} saved new detached signature to:\n{}"
                           .format(self.g.GPG.upper(), outfile))
                
                elif action in 'verify':
                    msg = "SUCCESS!\n\n{} verified signature.".format(self.g.GPG.upper())
                buff.set_text(msg)
                buff.set_modified(False)
                
                # Unlock TextView
                self.g_msgtextview.set_sensitive(True)
                
                # Reset filenames
                self.in_filename = None ; self.out_filename = None
                
                # Disable plaintext CheckButton
                self.g_plaintext.set_sensitive(False)
                self.g_plaintext.set_active(True)
            
            # Fail!
            else:
                
                self.g_statusbar.pop(self.status)
                if action in 'verify':
                    self.g_statusbar.pop(self.status)
                    msg = ("Signature couldn't be verified.\nHave a look at "
                           "'Task Status' output on the right for more info."
                           .format(self.g.GPG.upper()))
                    buff.set_text(msg)
                    buff.set_modified(False)
                    self.g_msgtextview.set_sensitive(True)
                    self.in_filename = None
                    self.g_plaintext.set_sensitive(False)
                    self.g_plaintext.set_active(True)
                    return
                
                elif action in {'enc', 'dec'}:
                    err = ("{}Problem {}rypting {!r}\nTry again with another "
                            "passphrase or select Clear from the Edit menu."
                            .format(self.g.stderr, action, self.in_filename))
                
                elif action in {'sign', 'signclear', 'signdetach'}:
                    err = ("{}Problem signing {!r}\nTry again with another "
                            "passphrase or select Clear from the Edit menu."
                            .format(self.g.stderr, self.in_filename))
                
                show_errmsg(err)
        
        # TEXT INPUT MODE CLEANUP
        else:
            
            # Remove '...crypting input...' status
            self.g_statusbar.pop(self.status)
            
            # Unlock TextView
            self.g_msgtextview.set_sensitive(True)
            
            # Reset inputdata
            self.g.stdin = None
            
            # Success!
            if retval:
                if action in 'verify':
                    show_errmsg(self.g.stderr, dialogtype=gtk.MESSAGE_INFO)
                else:
                    # Set TextBuffer to gpg stdout
                    buff.set_text(self.g.stdout)
            
            # Fail!
            else:
                show_errmsg(self.g.stderr)
    
    
    #------------------------------------------------------------- ABOUT DIALOG
    def on_gtk_about_activate(self, menuitem, data=None):
        if self.about_dialog: 
            self.about_dialog.present()
            return
        authors = ["Ryan Sawhill <ryan@b19.org>"]
        about_dialog = gtk.AboutDialog()
        about_dialog.set_transient_for(self.g_window)
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name('a8crypt')
        about_dialog.set_version('0.9.9.4')
        about_dialog.set_copyright("Copyright \xc2\xa9 2012 Ryan Sawhill")
        about_dialog.set_website('http://github.com/ryran/a8crypt')
        about_dialog.set_comments("Encryption, decryption, & signing via GPG/GPG2")
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
        gtk.main()



if __name__ == "__main__":
    
    a8 = AEightCrypt()
    a8.main()
    
