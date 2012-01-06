#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# a8crypt v0.0.3 last mod 2012/01/06
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
# TODO: What to say here? It's all said in the comments and docstrings. ...


import gtk
from pango import FontDescription
from sys import stderr
from os import access, R_OK, pipe, write, close
from shlex import split
from subprocess import check_output, Popen, PIPE
from tempfile import TemporaryFile



def show_errmsg(message):
    """Display message in GTK error dialog or print to terminal stderr."""
    dialog = gtk.MessageDialog(
        None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
    dialog.run() ; dialog.destroy()



# If this doesn't contain a huge string of XML, you need to download a8crypt.glade
# from the same place you got this script. On __init__, AEightCrypt looks for the
# glade XML in said file before checking for it here.
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
  <object class="GtkWindow" id="window1">
    <property name="can_focus">False</property>
    <property name="title" translatable="yes">a8crypt</property>
    <property name="window_position">center</property>
    <property name="default_width">540</property>
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
                  <object class="GtkMenu" id="menu1">
                    <property name="visible">True</property>
                    <property name="can_focus">False</property>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_encrypt">
                        <property name="label" translatable="yes">E_ncrypt</property>
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
                        <property name="use_underline">True</property>
                        <property name="image">image3</property>
                        <property name="use_stock">False</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_save_activate" swapped="no"/>
                      </object>
                    </child>
                    <child>
                      <object class="GtkImageMenuItem" id="menu_open">
                        <property name="label" translatable="yes">_Open large file</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
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
                <property name="label" translatable="yes">_Edit</property>
                <property name="use_underline">True</property>
                <child type="submenu">
                  <object class="GtkMenu" id="menu2">
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
                        <property name="label">gtk-clear</property>
                        <property name="use_action_appearance">False</property>
                        <property name="visible">True</property>
                        <property name="can_focus">False</property>
                        <property name="use_underline">True</property>
                        <property name="use_stock">True</property>
                        <property name="always_show_image">True</property>
                        <signal name="activate" handler="on_gtk_clear_activate" swapped="no"/>
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
                  <object class="GtkMenu" id="menu3">
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
              <object class="GtkHButtonBox" id="hbuttonbox1">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="layout_style">edge</property>
                <child>
                  <object class="GtkButton" id="button_encrypt">
                    <property name="label" translatable="yes">E_ncrypt</property>
                    <property name="use_action_appearance">False</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">False</property>
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
                <child>
                  <object class="GtkButton" id="button_clear">
                    <property name="label">gtk-clear</property>
                    <property name="use_action_appearance">False</property>
                    <property name="visible">True</property>
                    <property name="can_focus">True</property>
                    <property name="receives_default">False</property>
                    <property name="use_stock">True</property>
                    <property name="focus_on_click">False</property>
                    <signal name="clicked" handler="on_gtk_clear_activate" swapped="no"/>
                  </object>
                  <packing>
                    <property name="expand">False</property>
                    <property name="fill">False</property>
                    <property name="position">2</property>
                  </packing>
                </child>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">False</property>
                <property name="position">0</property>
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
                <property name="position">1</property>
              </packing>
            </child>
            <child>
              <object class="GtkLabel" id="label_passphrase">
                <property name="visible">True</property>
                <property name="can_focus">False</property>
                <property name="label" translatable="yes">Enter _passphrase: </property>
                <property name="use_underline">True</property>
                <property name="justify">right</property>
                <property name="mnemonic_widget">entry_passphrase</property>
              </object>
              <packing>
                <property name="expand">False</property>
                <property name="fill">True</property>
                <property name="position">2</property>
              </packing>
            </child>
            <child>
              <object class="GtkEntry" id="entry_passphrase">
                <property name="visible">True</property>
                <property name="can_focus">True</property>
                <property name="visibility">False</property>
                <property name="invisible_char">●</property>
                <property name="truncate_multiline">True</property>
                <property name="primary_icon_activatable">False</property>
                <property name="secondary_icon_activatable">False</property>
                <property name="primary_icon_sensitive">True</property>
                <property name="secondary_icon_sensitive">True</property>
              </object>
              <packing>
                <property name="expand">True</property>
                <property name="fill">True</property>
                <property name="position">3</property>
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
              <object class="GtkTextView" id="textview1">
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
          <object class="GtkStatusbar" id="statusbar">
            <property name="visible">True</property>
            <property name="can_focus">False</property>
            <property name="spacing">2</property>
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



class GpgInterface():
    """GPG/GPG2 interface for simple symmetric encryption/decryption.
    
    First thing: use subprocess module to call a gpg or gpg2 process, ensuring
    that one of them is available on the system; if not, of course we have to
    quit (raise exception). Either way, that's all for __init__.
    
    After that, it's up to you to call the main method of launch_gpg(), giving it
    a passphrase, telling it whether you want encryption or decryption, and
    optionally passing it input and output filenames (see launch_gpg.__doc__ for
    details, but if you don't give filenames to launch_gpg(), you must first save
    your input to class attribute 'inputdata' -- then output is return-ed).
    
    Security: The launch_gpg() method takes a passphrase as an argument, but it
    never stores it on disk (not even in a tempfile); the passphrase is passed to
    gpg via an os file descriptor. Also, AES256 is used by default as the
    symmetric cipher algorithm for encryption (in contrast to GPG/GPG2's standard
    behavior of using CAST5).
    
    To make this as portable as possible, here is a list of StdLib mods/methods
    used and how they're expected to be named:
        from tempfile import TemporaryFile
        from sys import stderr
        from os import pipe, write, close
        from shlex import split
        from subprocess import check_output, Popen, PIPE
    
    This class is modular enough that you can copy & paste it verbatim into your
    own script and the only thing you need to change/define is the one call to
    show_errmsg() -- just replace that with print or sys.stderr.write().
    """
    
    
    def __init__(self):
        """Confirm we can run gpg or gpg2."""
        try:
            Popen(['gpg', '--version']) ; self.gpg = 'gpg --no-use-agent'
        except:
            try:
                Popen(['gpg2', '--version']) ; self.gpg = 'gpg2'
            except:
                show_errmsg("This program requires either gpg or gpg2. Neither "
                            "were found on your system.")
                raise Exception("gpg, gpg2 not found")
        
        # Convert 'gpg --opts' or 'gpg2 --opts' to simply 'GPG' or 'GPG2'
        self.gpgupper = self.gpg[:4].upper().strip()
        self.inputdata = None           # Stores input text for launch_gpg()
        self.stderr = TemporaryFile()   # For storing stderr generated by gpg
    
    
    def launch_gpg(self, mode, passphrase, in_filename=None, out_filename=None,
            binarymode=False, cipheralgo='aes256'):
        """Start our GPG/GPG2 subprocess & save or return its output.
        
        Aside from its arguments of a passphrase & a mode of 'en' for encrypt or
        'de' for decrypt, this method can optionally take an argument of two os
        filenames (for input and output). If these optional arguments are not used, 
        input is expected to be in class attribute 'inputdata' (which can contain
        normal non-list data) and the output is return-ed. Any stderr generated
        calling GPG is printed to stderr & stored in class attr fileobj 'stderr'.
        
        Of lesser importance are the last two optional arguments.
        First, the  boolean argument of binarymode: defaults to False, which
        configures gpg to produce ASCII-armored output. A setting of True is only
        honored when operating in direct file-reading/-writing mode, i.e., when
        gpg is saving output directly to files.
        Second, the str argument cipheralgo: defaults to aes256, but other good
        choices would be cast5 (gpg's default), twofish, or camellia256.
        """
        
        # Sanity checking of arguments and input
        # This isn't necessary of course, but as a courtesy...
        if mode not in {'en', 'de'}:
            stderr.write("Improper mode specified! Must be one of 'en' or 'de'.")
            raise Exception("Bad mode chosen")
        
        if in_filename and not out_filename:
            stderr.write("You specified {0!r} as a filename for input but you didn't "
                         "specify an output filename.".format(in_filename))
            raise Exception("Missing out_filename")
        
        if in_filename and in_filename == out_filename:
            stderr.write("Same filename for both input and output, eh? Is it "
                         "going to work? NOPE. Chuck Testa.")
            raise Exception("in_filename, out_filename must be different")
        
        if not in_filename and not self.inputdata:
            stderr.write("You need to save input to class attr 'inputdata' first. "
                         "Or specify an input filename.")
            raise Exception("Missing GpgInterface.inputdata")
        
        if binarymode not in {True, False}:
            stderr.write("Improper binarymode value specified! Must be either "
                         "True or False (default: False).")
            raise Exception("Bad binarymode chosen")
        
        # Write our passphrase to an os file descriptor
        fd_in, fd_out = pipe()
        write(fd_out, passphrase) ; close(fd_out)
        
        # Set our encryption command
        if mode in 'en':
            
            # General encryption command, including ASCII-armor option
            cmd = '{gpg} --batch --no-tty --yes --symmetric --force-mdc '\
                  '--cipher-algo {algo} --passphrase-fd {fd} -a'\
                  .format(gpg=self.gpg, algo=cipheralgo, fd=fd_in)
            
            # If given a filename & binary mode requested, don't set ASCII-armored output
            if in_filename and binarymode:
                cmd = '{gpg} --batch --no-tty --yes --symmetric --force-mdc '\
                      '--cipher-algo {algo} --passphrase-fd {fd} -o {fout} {fin}'\
                      .format(gpg=self.gpg, algo=cipheralgo, fd=fd_in, fout=out_filename, fin=in_filename)
            
            # If given a filename but not in binary mode, simply add filenames to our cmd
            elif in_filename:
                cmd = '{cmd} -o {fout} {fin}'\
                      .format(cmd=cmd, fout=out_filename, fin=in_filename)
        
        # Set our decryption command
        elif mode in 'de':
            
            # General decryption command
            cmd = '{gpg} --batch --no-tty --yes -d --passphrase-fd {fd}'\
                  .format(gpg=self.gpg, fd=fd_in)
            
            # If given a filename, simply add filenames to our cmd
            if in_filename:
                cmd = '{gpg} --batch --no-tty --yes -d --passphrase-fd {fd} '\
                      '-o {fout} {fin}'\
                      .format(gpg=self.gpg, fd=fd_in, fout=out_filename, fin=in_filename)
        
        # Reset stderr fileobj's data to avoid duplicate errors
        # TODO: Grok why truncate(0) doesn't work the same as seek(0)+truncate()
        self.stderr.seek(0) ; self.stderr.truncate()
        
        # If working with files directly, simply call our gpg cmd & let it do the work
        if in_filename:
            try:
                check_output(split(cmd), stderr=self.stderr)
                retval = True
            except:
                retval = False
        
        # Otherwise, need to pass 'inputdata' to gpg as input & need to receive output
        else:
            try:
                process = Popen(split(cmd), stdin=PIPE, stdout=PIPE, stderr=self.stderr)
                retval = process.communicate(input=self.inputdata)[0]
            except:
                retval = False
        
        # Close fd, print stderr, return process output
        close(fd_in)
        self.stderr.seek(0) ; stderr.write(self.stderr.read()) ; self.stderr.seek(0)
        return retval



class AEightCrypt:
    """Display GTK window to interact with GPG via GpgInterface object.
    
    Look at GpgInterface.__doc__ for all the juicy non-gui details.
    """
    
    def __init__(self):
        """Build GUI interface from XML, etc."""
        
        # Instantiate GpgInterface, which will check for gpg/gpg2
        self.gpgif = GpgInterface()
        self.GPG = self.gpgif.gpgupper
        
        self.about_dialog = None
        self.direct_in_filename = None
        self.direct_out_filename = None
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file("a8crypt.glade") 
        except:
            try:
                gbuild = XmlForGtkBuilder()
                builder.add_from_string(gbuild.inline_gladexmlfile)
            except:
                show_errmsg("Missing a8crypt.glade XML file! Cannot continue.")
                raise Exception("Missing GtkBuilder XML")
        
        # Get widgets which will be referenced in callbacks
        self.window = builder.get_object("window1")
        self.passentry = builder.get_object("entry_passphrase")
        self.textview = builder.get_object("textview1")
        self.statusbar = builder.get_object("statusbar")
        
        # Connect signals
        builder.connect_signals(self)
        
        # Set TextView font
        self.textview.modify_font(FontDescription("monospace 10"))
        
        # Set the app icon
        gtk.window_set_default_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # Initialize statusbar
        self.status = self.statusbar.get_context_id("main")
        self.statusbar.push(self.status, "[{0}] Type/paste text to be encrypted "
                            "or decrypted".format(self.GPG))
    
    
    # Generic filetype test to see if a file contains binary data or simply text
    def file_isbinary(self, filename):
        """Utilize file command to determine if filename's type is binary or text."""
        output = check_output(split('file -b -e soft {0}'.format(filename)))
        if output[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    
    # This is called when user tries to save or en/decrypt
    def sanitycheck_textviewbuff(self, choice):
        buff = self.textview.get_buffer()
        # Fail if textview is empty 
        if buff.get_char_count() < 1:
            show_errmsg("You haven't even entered any text yet.")
            return False
        # Fail if textview contains a message from direct-file-mode
        if not buff.get_modified():
            if choice in 'save':
                show_errmsg("Saving the buffer at this point would only save "
                            "a copy of the message you see in the main window.")
            else:
                show_errmsg(
                    "Your last file en/decryption operation succeeded. Selecting "
                    "'{0}crypt' at this point would only save a copy of the message "
                    "you see in the main window. Either load a new file from the "
                    "'Open large file' menu, or type/paste a new message"
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
    
    
    # 'Open large file' menu item
    def on_gtk_open_activate(self, menuitem, data=None):    self.open_file()
    
    
    # 'Save txt buffer' menu item
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
        """Reset statusbar, textview, passphrase, gpg inputdata & filename."""
        self.statusbar.pop(self.status)
        self.statusbar.push(self.status, "[{0}] Type/paste text to be encrypted "
                            "or decrypted".format(self.GPG))
        buff = self.textview.get_buffer()
        buff.set_text('')
        buff.set_modified(False)
        self.passentry.set_text('')
        self.textview.set_sensitive(True)
        self.textview.set_cursor_visible(True)
        self.direct_in_filename = None
        self.direct_out_filename = None
        self.gpgif.inputdata = None
    
    
    # Generic file chooser for opening or saving
    def chooser_grab_filename(self, mode, save_suggestion=None):
        """Present file chooser dialog and return filename or None."""
        
        filename = None
        if mode in 'open':
            chooser = gtk.FileChooserDialog(
                "Open File...", self.window, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        elif mode in 'save':
            chooser = gtk.FileChooserDialog(
                "Save File...", self.window, gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        """FIXME: Figure out how replace above with below.
        choosercmd = '"{0} File...", self.window, gtk.FILE_CHOOSER_ACTION_{1}, '\
                     '(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, '\
                     'gtk.RESPONSE_OK)'.format(mode.title(), mode.upper())
        chooser = gtk.FileChooserDialog(choosercmd)"""
        
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
        self.statusbar.push(self.status, "Saving {0}".format(filename))
        
        while gtk.events_pending(): gtk.main_iteration()
        
        # Disable textview & save contents of buffer
        self.textview.set_cursor_visible(False)
        self.textview.set_sensitive(False)
        buff = self.textview.get_buffer()
        buffertext = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
        
        try:
            # Try to open filename for writing
            fout = open(filename, 'w')
        except:
            # Error opening file, show message to user
            show_errmsg("Could not save file: {0}".format(filename))
        else:
            # Write text from buffer to file
            fout.write(buffertext)
            fout.close()
        
        # Unlock TextView
        self.textview.set_sensitive(True)
        self.textview.set_cursor_visible(True)
        
        # Clear saving status
        self.statusbar.pop(self.status)
    
    
    def open_file(self):
        """Choose a filename to pass directly to GPG (without loading into textview).
        
        For binary files or for very large files, it would be good to avoid pasting
        them into the GtkWindow and loading them into python right?
        
        This method prompts for a filename to open (for gpg input) and then an output
        filename (to save gpg output to) and sets up everything to make it possible
        for crypt() to pass the file NAMES directly to the gpg subprocess, without
        the ever opening the files [in Python].
        """
        
        # Loading message to statusbar
        self.statusbar.push(self.status, "[{0}] Choose a file for {0} to load "
                            "directly".format(self.GPG))
        # Prompt for a file to open
        infilename = self.chooser_grab_filename('open')
        self.statusbar.pop(self.status)  # Reset status
        if not infilename:
            return  # Return if user hit Cancel
        if not access(infilename, R_OK):
            show_errmsg("Could not open file for reading: {0}".format(infilename))
            return  # Return if no read permission
        
        while True:
            # Prompt for name to save output to
            outfilename = self.chooser_grab_filename('save', infilename)
            if not outfilename:
                return  # Return if user hit Cancel
            if infilename == outfilename:
                show_errmsg("Simultaneously reading from & writing to a file is "
                            "a baaad idea. Choose a different output filename.")
                # TODO: Learn about Gtk.FileChooser's confirm-overwrite signal to handle this problem
            else: break
        
        # Ready message to status; disable text view & replace it with a message
        self.statusbar.push(self.status, "[{0}] Ready to direct-load file: {1}"
                            .format(self.GPG, infilename))
        self.textview.set_cursor_visible(False)
        self.textview.set_sensitive(False)
        buff = self.textview.get_buffer()
        buff.set_text("Choose 'Encrypt' or 'Decrypt' to have {0} direct-load file\n"
                      "   {1}\nsaving output to file\n   {2}"
                      .format(self.GPG, infilename, outfilename))
        buff.set_modified(False)
        
        # Promote our filenames
        self.direct_in_filename = infilename
        self.direct_out_filename = outfilename
    
    
    def crypt(self, mode):
        """Manage I/O between Gtk objects and our GpgInterface object.
        
        This method is called with argument of 'en' or 'de' for encryption or
        decryption (just like GpgInterface.launch_gpg) when the user selects one
        of the Encrypt or Decrypt Gtk menu items or toolbar buttons.
        
        It reads the passphrase from our GtkTextEntry box, ensuring it's not null;
        then it reads in the buffer from TextView, if needed (not necessary if the
        user already chose a file for direct-loading by gpg); then it passes
        everything over to launch_gpg().
        """
        
        # Get passphrase from TextEntry
        passphrase = self.passentry.get_text()
        if not passphrase:
            show_errmsg("You must enter a passphrase.")
            return
        
        # If running in direct-file-load mode, pass filenames to launch_gpg()
        if self.direct_in_filename:
            
            # Make TextView immutable to changes & set statusbar
            self.textview.set_cursor_visible(False)
            self.textview.set_sensitive(False)
            self.statusbar.push(self.status, "[{0}] {1}crypting input ..."
                                .format(self.GPG, mode.title()))
            
            # Encryption only: if input file is binary, don't ASCII-armor output
            if self.file_isbinary(self.direct_in_filename):
                binarymode = True
            else: binarymode = False
            
            # Attempt en-/de-cryption; if succeeds, cleanup & print success
            if self.gpgif.launch_gpg(mode, passphrase, self.direct_in_filename,
                                     self.direct_out_filename, binarymode):
                
                # Clear last two statusbar messages to get back to default
                self.statusbar.pop(self.status) ; self.statusbar.pop(self.status)
                
                # Replace textview buffer with success message
                buff = self.textview.get_buffer()
                buff.set_text("Success!\n\n{0}crypted file:\n{1}\n\nSaved output "
                              "to file:\n{2}".format(mode.title(),
                              self.direct_in_filename, self.direct_out_filename))
                buff.set_modified(False)
                
                # Unlock TextView
                self.textview.set_sensitive(True)
                self.textview.set_cursor_visible(True)
            
                # Reset filenames
                self.direct_in_filename = None
                self.direct_out_filename = None
            
            # If launch_gpg() returns False, remove last status and print error
            else:
                self.statusbar.pop(self.status)
                show_errmsg("Problem {1}crypting {2!r}\nTry again with another "
                            "passphrase or press Clear.\n\n{0}".format(
                            self.gpgif.stderr.read(), mode, self.direct_in_filename))
        
        # If not running in file-mode ...
        else:
            
            # Make sure textview has a proper message in it
            if not self.sanitycheck_textviewbuff(mode): return
            
            # Make TextView immutable to changes & set statusbar
            self.textview.set_cursor_visible(False)
            self.textview.set_sensitive(False)
            self.statusbar.push(self.status, "[{0}] {1}crypting input ..."
                                .format(self.GPG, mode.title()))
            
            # Save textview buffer to GpgInterface.inputdata
            buff = self.textview.get_buffer()
            self.gpgif.inputdata = buff.get_text(buff.get_start_iter(),
                                                 buff.get_end_iter())
            
            # launch_gpg() reads input from 'inputdata' if no filenames given
            gpgoutput = self.gpgif.launch_gpg(mode, passphrase)
            
            # Remove '...crypting input...' status
            self.statusbar.pop(self.status)
            
            # If gpg returned something on stdout, set the buffer
            if gpgoutput:
                buff.set_text(gpgoutput)
            
            # Otherwise, show error, incl gpg stderr
            # (this could only happen in decrypt mode)
            else:
                show_errmsg("Error in decryption process.\n{0}"
                            .format(self.gpgif.stderr.read()))
            
            # Unlock TextView
            self.textview.set_sensitive(True)
            self.textview.set_cursor_visible(True)
            
            # Reset inputdata
            self.gpgif.inputdata = None
    
    
    # About dialog
    def on_gtk_about_activate(self, menuitem, data=None):
        if self.about_dialog: 
            self.about_dialog.present()
            return
        authors = ["Ryan Sawhill <ryan@b19.org>"]
        about_dialog = gtk.AboutDialog()
        about_dialog.set_transient_for(self.window)
        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("a8crypt")
        about_dialog.set_version("0.0.3")
        about_dialog.set_copyright("Copyright \xc2\xa9 2012 Ryan Sawhill")
        about_dialog.set_website("http://github.com/ryran/a8crypt")
        about_dialog.set_comments("Symmetric encryption via GPG/GPG2")
        about_dialog.set_authors(authors)
        about_dialog.set_logo_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # callbacks for destroying the dialog
        def close(dialog, response, self):
            self.about_dialog = None
            dialog.destroy()
        def delete_event(dialog, event, self):
            self.about_dialog = None
            return True
        
        about_dialog.connect("response", close, self)
        about_dialog.connect("delete-event", delete_event, self)
        
        self.about_dialog = about_dialog
        about_dialog.show()
    
    
    # Run main application window
    def main(self):
        self.window.show()
        gtk.main()




if __name__ == "__main__":
    a8 = AEightCrypt()
    a8.main()
    
    
