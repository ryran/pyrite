#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# a8crypt v0.0.1 last mod 2012/01/05
# Latest version at <http://github.com/ryran/acrypt>
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
from os.path import isfile, join
from os import environ, pathsep, access, R_OK, X_OK, pipe, write, close
from shlex import split
from subprocess import check_output, check_call, Popen, PIPE
from tempfile import TemporaryFile


def print_errmsg(message):
    """Display message in GTK error dialog or print to terminal stderr."""
    try:
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)
        dialog.run()
        dialog.destroy()
    except:
        stderr.write("{0}\n".format(message))


# If this doesn't contain a huge string of XML, you need to download a8crypt.glade from the
# same place you got this script. At runtime, AEightCrypt looks for the glade XML in that file
# before checking for it here.
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
    
    Overview: This was designed for and tested on Linux only, so the first thing
    it does is use os.environ to check for gpg or gpg2 in $PATH, printing message
    to stderr if they're both unavailable. That's all for __init__.
    
    After that, it's up to you to call the main method of launch_gpg(), giving it
    a passphrase, telling it whether you want encryption or decryption, and
    optionally passing it input and output filenames (see launch_gpg.__doc__ for
    details, but if you don't give filenames to launch_gpg(), you must first save
    your input to class attribute 'inputdata' -- then output is return-ed).
    
    Security: The launch_gpg() method takes a passphrase as an argument, but it
    never stores it on disk (not even in a tempfile); the passphrase is passed to
    gpg via an os file descriptor.
    
    To make this as portable as possible, here is a list of StdLib mods/methods
    used and how they're expected to be named:
        from tempfile import TemporaryFile
        from os.path import isfile, join
        from os import environ, pathsep, access, X_OK, pipe, write, close
        from shlex import split
        from subprocess import check_call, Popen, PIPE
    
    This class is modular enough that you could copy & paste it verbatim into 
    your own script and the only thing you would need to change/define are the
    calls to print_errmsg() -- just replace with print or sys.stderr.write().
    
    """
    
    
    def __init__(self):
        """Confirm os PATH contains gpg or gpg2."""
        
        self.gpg = None                 # Stores the name of our gpg binary + any binary-specific options
        self.inputdata = None           # Stores input text for launch_gpg()
        self.stderr = TemporaryFile()   # For storing stderr generated by gpg
        
        # Check PATH for gpg or else for gpg2
        for d in environ['PATH'] .split(pathsep):
            for p in ('gpg', 'gpg2'):
                if isfile(join(d,p)) and access(join(d,p), X_OK):
                    if p == 'gpg':
                        self.gpg = 'gpg --no-use-agent'
                    else:
                        self.gpg = 'gpg2'
                    break
            if self.gpg: break
        
        # If gpg/gpg2 not found, error out
        if not self.gpg:
            print_errmsg("This program requires gpg or gpg2 to work. Neither were found in your PATH.")
            raise Exception("gpg, gpg2 not found in $PATH")
        
        # Convenience variable
        # Convert 'gpg --opts' or 'gpg2 --opts' to simply 'GPG' or 'GPG2'
        self.gpgupper = self.gpg[:4].upper().strip()
    
    
    def launch_gpg(self, mode, passphrase, in_filename=None, out_filename=None, binarymode=False):
        """Start our GPG/GPG2 subprocess & save or return its output.
        
        Aside from its arguments of a passphrase & a mode of 'en' for encrypt or
        'de' for decrypt, this method can optionally take an argument of two os
        filenames (for input and output). If these optional arguments are not used, 
        input is expected to be in class attribute 'inputdata' (which can contain
        normal non-list data) and the output is return-ed. Any stderr generated
        calling GPG/GPG2 is printed to stderr & stored in class attr 'stderr'.
        
        Of lesser importance is an optional boolean argument of binarymode. This
        defaults to False, which configures gpg to produce ASCII-armored output.
        Note: this setting is only checked when operating in direct mode, i.e.,
        when gpg is saving output directly to files.
        """
        
        # Sanity check arguments
        if mode not in {'en', 'de'}:
            print_errmsg("Improper mode specified! Must be one of 'en' or 'de'.")
            raise Exception("Bad mode chosen for launch_gpg()")
        
        if in_filename and not out_filename:
            print_errmsg("You specified {0!r} as a filename for input but you didn't specify an output filename."
                         .format(in_filename))
            raise Exception("Missing out_filename for launch_gpg()")
        
        if binarymode not in {True, False}:
            print_errmsg("Improper binarymode value specified! Must be either True or False (default: False).")
            raise Exception("Bad binarymode chosen for launch_gpg()")
        
        # Write our passphrase to an os file descriptor
        fd_in, fd_out = pipe()
        write(fd_out, passphrase) ; close(fd_out)
        
        # Set our encryption command
        if mode == 'en':
            
            # General encryption command, including ASCII-armor
            cmd = '{gpg} --batch --no-tty --yes -c --force-mdc --passphrase-fd {fd} -a' \
                  .format(gpg=self.gpg, fd=fd_in)
            
            # If given a filename and binary mode is requested, don't use ASCII-armored mode
            if binarymode:
                cmd = '{gpg} --batch --no-tty --yes -c --force-mdc --passphrase-fd {fd} -o {fout} {fin}' \
                      .format(gpg=self.gpg, fd=fd_in, fout=out_filename, fin=in_filename)
            
            # If given a filename but not in binary mode, we simply need to add filenames to our cmd
            elif in_filename:
                cmd = '{cmd} -o {fout} {fin}'.format(cmd=cmd, fout=out_filename, fin=in_filename)
        
        # Set our decryption command
        elif mode == 'de':
            
            # General decryption command
            cmd = '{gpg} --batch --no-tty --yes -d --passphrase-fd {fd}'.format(gpg=self.gpg, fd=fd_in)
            
            # If given a filename, tweak our cmd a little bit
            if in_filename:
                cmd = '{gpg} --batch --no-tty --yes -d --passphrase-fd {fd} -o {fout} {fin}' \
                      .format(gpg=self.gpg, fd=fd_in, fout=out_filename, fin=in_filename)
        
        # Reset stderr fileobj's data to make sure we overwrite any old errors
        self.stderr.truncate(0)
        
        # If working with files directly, simply call our gpg cmd & let it do the work
        if in_filename:
            try:
                check_call(split(cmd), stderr=self.stderr)
            except:
                retval = False
            else:
                retval = True
        
        # Otherwise, we need to pass 'inputdata' to gpg as input and need to receive output
        else:
            process = Popen(split(cmd), stdin=PIPE, stdout=PIPE, stderr=self.stderr)
            retval = process.communicate(input=self.inputdata)[0]
        
        # Print gpg stderr, close fd, return gpg output (or return True/False if in direct file-mode)
        close(fd_in)
        self.stderr.seek(0) ; stderr.write(self.stderr.read()) ; self.stderr.seek(0)
        return retval



class AEightCrypt:
    """Display GTK window to interact with GPG via GpgInterface object.
    
    Look at GpgInterface.__doc__ for all the juicy non-gui details.
    """
    
    def __init__(self):
        """Build GUI interface from XML, etc."""
        
        # Instantiate GpgInterface, which will raise an exception if gpg and gpg2 are not found
        self.gpgif = GpgInterface()
        self.GPG = self.gpgif.gpgupper
        
        # Default values
        self.about_dialog = None
        self.direct_in_filename = None
        self.direct_out_filename = None
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file("a8crypt.glade") 
        except:
            stderr.write("a8crypt.glade not found; using inline XML\n")
            try:
                gbuild = XmlForGtkBuilder()
                builder.add_from_string(gbuild.inline_gladexmlfile)
            except:
                print_errmsg("Missing a8crypt.glade XML file! Cannot continue.")
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
        self.status_cid = self.statusbar.get_context_id("Acrypt")
        self.statusbar.push(self.status_cid,
                            "[{}] Type/paste text to be encrypted or decrypted".format(self.GPG))
    
    
    # Generic filetype test to see if a file contains binary data or simply text
    def file_isbinary(self, filename):
        """Utilize nix file command to determine if filename type is binary or text."""
        output = check_output(split('file -b -e soft {0}'.format(filename)))
        if output[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    # Used in a couple places; it prints errors and returns False if checks don't pass
    def sanitycheck_textviewbuff(self, choice):
        buff = self.textview.get_buffer()
        # Fail if textview is empty 
        if buff.get_char_count() < 1:
            print_errmsg("You haven't even entered any text yet.")
            return False
        
        # Fail if textview contains a message from direct-file-mode
        if not buff.get_modified():
            if choice == 'save':
                print_errmsg("Saving the buffer at this point would only save a copy of the message you see in the main window.")
            else:
                print_errmsg("Your last file en/decryption operation succeeded. Selecting '{}crypt' at this point "
                "would only save a copy of the message you see in the main window. Either load a new file from "
                "the 'Open large file' menu, or type/paste a new message".format(choice.title()))
            return False
        return True
    
    # Death!
    def on_window1_destroy(self, widget, data=None):
        gtk.main_quit()
    def on_gtk_quit_activate(self, menuitem, data=None):
        gtk.main_quit()
    
    
    # 'Encrypt' button & menu item
    def on_gtk_encrypt_activate(self, menuitem, data=None):
        self.crypt('en')
    
    
    # 'Decrypt' button & menu item
    def on_gtk_decrypt_activate(self, menuitem, data=None):
        self.crypt('de')
    
    
    # 'Save txt buffer' menu item
    def on_gtk_save_activate(self, menuitem, data=None):
        if self.sanitycheck_textviewbuff('save'):
            filename = self.chooser_grab_filename('save')
            if filename: self.write_file(filename)
    
    
    # 'Open large file' menu item
    def on_gtk_open_activate(self, menuitem, data=None):
        self.open_file()
    
    
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
        self.statusbar.pop(self.status_cid)
        self.statusbar.push(self.status_cid,
                            "[{}] Type/paste text to be encrypted or decrypted".format(self.GPG))
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
        if mode == 'open':
            chooser = gtk.FileChooserDialog(
                "Open File...", self.window, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        
        elif mode == 'save':
            chooser = gtk.FileChooserDialog(
                "Save File...", self.window, gtk.FILE_CHOOSER_ACTION_SAVE,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            chooser.set_do_overwrite_confirmation(True)
            if save_suggestion: chooser.set_filename(save_suggestion)
            # TODO: Populate save field with name, but don't unselect file
        
        response = chooser.run()
        if response == gtk.RESPONSE_OK: filename = chooser.get_filename()
        chooser.destroy()
        return filename
    
    
    # Save contents of buffer to file
    def write_file(self, filename):
        """Write TextView buffer to filename."""
        
        # Add message to status bar
        self.statusbar.push(self.status_cid, "Saving {}".format(filename))
        
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
            print_errmsg("Could not save file: {}".format(filename))
        else:
            # Write text from buffer to file
            fout.write(buffertext)
            fout.close()
        
        # Unlock TextView
        self.textview.set_sensitive(True)
        self.textview.set_cursor_visible(True)
        
        # Clear saving status
        self.statusbar.pop(self.status_cid)
    
    
    def open_file(self):
        """Choose a filename to pass directly to GPG (without loading into textview).
        
        For binary files or for very large files, it would be good to avoid pasting
        them into the GtkWindow and loading them into python right?
        
        This method prompts for a filename to open (for gpg input) and then an output
        filename (to save gpg output to) and sets up everything to make it possible
        for crypt() to pass the file NAMES directly to the gpg subprocess, without
        the ever opening the files [in Python].
        """
        
        # Loading message to statusbar, just because we can
        self.statusbar.push(self.status_cid, "[{0}] Choose a file for {0} to load directly".format(self.GPG))
        # Prompt for a file to open
        infilename = self.chooser_grab_filename('open')
        # Reset status
        self.statusbar.pop(self.status_cid)
        if not infilename:
            return  # Return if user hit Cancel
        if not access(infilename, R_OK):
            print_errmsg("Could not open file for reading: {}".format(infilename))
            return  # Return if no read permission
        
        while True:
            # Prompt for name to save output to
            outfilename = self.chooser_grab_filename('save', infilename)
            if not outfilename:
                return  # Return if user hit Cancel
            if infilename == outfilename:
                print_errmsg("Simultaneously reading from & writing to a file is a baaad idea. Choose a different name.")
                # TODO: Handle this problem by tweaking Gtk.FileChooser's confirm-overwrite signal
            else: break
        
        # Ready message to status; disable the text view & replace it with a message
        self.statusbar.push(self.status_cid, "[{0}] Ready to direct-load file: {1}".format(self.GPG, infilename))
        self.textview.set_cursor_visible(False)
        self.textview.set_sensitive(False)
        buff = self.textview.get_buffer()
        buff.set_text("Choose 'Encrypt' or 'Decrypt' to have {0} direct-load file\n   {1}\n"
                      "saving output to file\n   {2}".format(self.GPG, infilename, outfilename))
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
            print_errmsg("You must enter a passphrase.")
            return
        
        # If running in direct-file-load mode, pass filenames to launch_gpg()
        if self.direct_in_filename:
            
            # Make TextView immutable to changes & set statusbar
            self.textview.set_cursor_visible(False)
            self.textview.set_sensitive(False)
            self.statusbar.push(self.status_cid, "[{0}] {1}crypting input ..." .format(self.GPG, mode.title()))
            
            # For encryption only: if our input file is binary, let's not ASCII-armor the output
            if self.file_isbinary(self.direct_in_filename):
                binarymode = True
            else: binarymode = False
            
            if self.gpgif.launch_gpg(mode, passphrase, self.direct_in_filename, self.direct_out_filename, binarymode):
            # If en-/de-cryption succeeds, cleanup & print success
                
                # Clear two statusbar messages
                self.statusbar.pop(self.status_cid) ; self.statusbar.pop(self.status_cid)
                
                # Replace textview buffer with success message
                buff = self.textview.get_buffer()
                buff.set_text("Success!\n\n{0}crypted file:\n{1}\n\nSaved output to file:\n{2}"
                              .format(mode.title(), self.direct_in_filename, self.direct_out_filename))
                buff.set_modified(False)
                
                # Unlock TextView
                self.textview.set_sensitive(True)
                self.textview.set_cursor_visible(True)
            
                # Reset filenames in case user tries to open a new file instead of selecting Clear
                self.direct_in_filename = None
                self.direct_out_filename = None
            
            else:
                # If launch_gpg() returned False, remove '..crypting input...' status and print error
                self.statusbar.pop(self.status_cid)
                print_errmsg("{0}\nProblem {1}crypting\n{2!r}\nTry again with another passphrase or "
                             "press Clear.".format(self.gpgif.stderr.read(), mode, self.direct_in_filename))
        
        # If running in normal text input mode, use textview buffer as input for launch_gpg()
        else:
            
            # Make sure textview has a proper message in it
            if not self.sanitycheck_textviewbuff(mode): return
            
            # Make TextView immutable to changes & set statusbar
            self.textview.set_cursor_visible(False)
            self.textview.set_sensitive(False)
            self.statusbar.push(self.status_cid, "[{0}] {1}crypting input ..." .format(self.GPG, mode.title()))
            
            # Save textview buffer to GpgInterface.inputdata
            buff = self.textview.get_buffer()
            self.gpgif.inputdata = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
            
            # launch_gpg() reads input from 'inputdata' if no filenames given
            gpgoutput = self.gpgif.launch_gpg(mode, passphrase)
            
            # Remove '...crypting input...' status
            self.statusbar.pop(self.status_cid)
            
            # If gpg returned something on stdout, set the buffer
            if gpgoutput:
                buff.set_text(gpgoutput)
            # If output is null, display message with stderr (this could only happen in decrypt mode)
            else:
                print_errmsg("{}\nError in decryption process.".format(self.gpgif.stderr.read()))
            
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
        about_dialog.set_version("0.0.1")
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
    
    
