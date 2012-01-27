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
#
# TODO: Dialog with progress bar & cancel button when working
# TODO: Get icons for for encrypt, decrypt, sign, verify buttons, application
# TODO: Preferences dialog that can save settings to a config file?
# TODO: Implement undo stack. Blech. Kill me.
# TODO: Implement update notifications.
# TODO: CHOOSE A PROPER PROJECT NAME.

# StdLib:
import gtk
from glib import timeout_add_seconds
from pango import FontDescription
from os import access, R_OK
from shlex import split
from subprocess import check_output
# Custom:
import gpg

version = 'v1.0.0_dev'
assetdir = ''


def show_errmsg(message, dialogtype=gtk.MESSAGE_ERROR):
    """Display message with GtkMessageDialog."""
    dialog = gtk.MessageDialog(
        None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        dialogtype, gtk.BUTTONS_OK, message)
    dialog.run()
    dialog.destroy()



class Pyrite:
    """Display GTK window to interact with gpg via GpgXface object.
    
    For now, we build the gui from a Glade-generated gtk builder xml file.
    Once things are more finalized, we'll add the pygtk calls in here.
    """
    
    
    def __init__(self):
        """Build GUI interface from XML, etc."""        
        
        # Other class attributes
        self.in_filename  = None
        self.out_filename = None
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file(assetdir + 'main.glade') 
        except:
            show_errmsg("Problem loading GtkBuilder UI definition! "
                        "Cannot continue.")
            raise
        
        #--------------------------------------------------------- GET WIDGETS!
        
        # Main window
        self.g_window       = builder.get_object('window1')
        # Menu items
        self.g_mopen        = builder.get_object('mnu_open')
        self.g_msave        = builder.get_object('mnu_save')
        self.g_mcut         = builder.get_object('mnu_cut')
        self.g_mcopy        = builder.get_object('mnu_copy')
        self.g_mpaste       = builder.get_object('mnu_paste')
        self.g_mengine      = builder.get_object('mnu_switchengine')
        self.g_wrap         = builder.get_object('toggle_wordwrap')
        self.g_taskstatus   = builder.get_object('toggle_taskstatus')
        self.g_taskverbose   = builder.get_object('toggle_gpgverbose')
        # Top action toolbar
        self.g_encrypt      = builder.get_object('button_encrypt')
        self.g_decrypt      = builder.get_object('button_decrypt')
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
        self.g_bopen        = builder.get_object('btn_open')
        self.g_bsave        = builder.get_object('btn_save')
        self.g_bcopyall     = builder.get_object('btn_copyall')
        self.g_msgtxtview   = builder.get_object('textview1')
        self.buff           = self.g_msgtxtview.get_buffer()
        self.g_vb_ibar      = builder.get_object('vbox_ibar')
        self.g_ibar         = None
        self.g_chooserbtn   = builder.get_object('btn_filechooser')
        self.g_plaintext    = builder.get_object('toggle_plaintext')
        self.g_frame2       = builder.get_object('frame2')
        self.g_errtxtview   = builder.get_object('textview2')
        self.buff2          = self.g_errtxtview.get_buffer()
        # Signing toolbar
        self.g_signature    = builder.get_object('toggle_signature')
        self.g_sigmode      = builder.get_object('combobox_sigmode')
        self.g_hashlabel    = builder.get_object('label_combobox_hash')
        self.g_hash         = builder.get_object('combobox_hash')
        self.g_chk_defkey   = builder.get_object('toggle_defaultkey')
        self.g_defaultkey   = builder.get_object('entry_defaultkey')
        # Statusbar
        self.g_statusbar    = builder.get_object('statusbar')
        self.g_activityspin = builder.get_object('spinner1')
        
        # Set app icon to something halfway-decent
        gtk.window_set_default_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # Override Pyrite's default cipher by setting ComboBox active item index
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
        
        # Initialize main Statusbar
        self.status = self.g_statusbar.get_context_id('main')
        self.g_statusbar.push(self.status, "Enter message to encrypt/decrypt")
    
        self.instantiate_xface(startup=True)
    
    
    def instantiate_xface(self, xface='gpg', startup=False):
        """Instantiate Gpg or Openssl interface."""
        
        if startup:
            try:
                self.x = gpg.Xface()
                self.engine = self.x.GPG.upper()
            except:
                try:
                    import openssl
                    self.x = openssl.Xface()
                    self.engine = 'OpenSSL'
                    self.g_mengine.set_label("Use GnuPG as Engine")
                    self.g_mengine.set_sensitive(False)
                    self.infobar("<b>To make full use of this program you need either gpg\n"
                                 "or gpg2, neither of which were found on your system.</b>\n"
                                 "Operating in openssl fallback-mode with reduced functionality.",
                                 gtk.MESSAGE_WARNING, 11)
                except:
                    show_errmsg("To use this program you need either gpg, gpg2, or "
                                "openssl, none of which were found on your system.")
                    raise
        
        else:
            if xface in 'gpg':
                self.x = gpg.Xface()
                self.engine = self.x.GPG.upper()
                self.g_mengine.set_label("Use OpenSSL as Engine")
            else:
                try:
                    import openssl
                    self.x = openssl.Xface()
                    self.g_mengine.set_label("Use GnuPG as Engine")
                    self.engine = 'OpenSSL'
                    self.infobar("<b>Quite a few things are disabled in OpenSSL mode.</b>\n"
                                 "You can still have fun though.", icon=gtk.STOCK_DIALOG_INFO)
                except:
                    self.g_mengine.set_sensitive(False)
                    self.infobar("<b>Shockingly, your system does not appear to have "
                                 "OpenSSL.</b>", gtk.MESSAGE_WARNING)
                    return
        
        self.g_window.set_title("Pyrite [{}]".format(self.engine))
        def setsensitive_gpgwidgets(x=True):
            self.g_signverify.set_sensitive (x)
            self.g_symmetric.set_sensitive  (x)
            self.g_asymmetric.set_sensitive (x)
            self.g_advanced.set_sensitive   (x)
            self.g_chooserbtn.set_sensitive (x)
            self.g_taskverbose.set_visible  (x)
        if self.engine in 'OpenSSL':
            setsensitive_gpgwidgets (False)
        else:
            setsensitive_gpgwidgets (True)
        
        self.buff2.set_text("Any output generated from calls to {} will be "
                            "displayed here.\n\nIn the View menu you can change "
                            "the verbosity level, hide this pane, or simply change "
                            "the font size.".format(self.engine.lower()))
        
    
    #--------------------------------------------------------- HELPER FUNCTIONS
    
    def action_switch_engine(self, widget, data=None):
        if self.engine in 'OpenSSL':
            self.instantiate_xface('gpg')
        else:
            self.instantiate_xface('openssl')    
    
    
    def set_stdstatus(self):
        """Set a standard status message that is mode-depenedent."""
        self.g_statusbar.pop(self.status)
        if self.g_signverify.get_active():
            s = "Enter message to sign/verify"
        else:
            s = "Enter message to encrypt/decrypt"
        self.g_statusbar.push(self.status, s)
    
    
    def test_file_isbinary(self, filename):
        """Utilize nix file cmd to determine if filename is binary or text."""
        cmd = split("file -b -e soft '{}'".format(filename))
        if check_output(cmd)[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    
    def infobar(self, message, msgtype=gtk.MESSAGE_INFO, timeout=5, icon=None):
        """Instantiate a new auto-hiding InfoBar with a Label of message."""
        
        message = "<span foreground='#2E2E2E'>" + message + "</span>"
        if icon:                                pass
        elif msgtype == gtk.MESSAGE_INFO:       icon = gtk.STOCK_APPLY
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
            self.launchxface(mode)
    
    
    #------------------------------------------- HERE BE GTK SIGNAL DEFINITIONS
    
    def on_window1_destroy  (self, widget, data=None):  gtk.main_quit()
    def action_quit         (self, widget, data=None):  gtk.main_quit()
    
    
    def action_about(self, widget, data=None):
        builder = gtk.Builder()
        builder.add_from_file(assetdir + 'about.glade') 
        about_dialog = builder.get_object('aboutdialog')
        about_dialog.set_logo_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        about_dialog.set_transient_for(self.g_window)
        about_dialog.set_version(version)
        def close(dialog, response, self):
            about_dialog.destroy()
        about_dialog.connect('response', close, self)
        about_dialog.show()
    
    
    def action_clear(self, widget, data=None):
        """Reset Statusbar, TextBuffer, Entry, gpg input & filenames."""
        self.set_stdstatus()        
        self.filemode_enablewidgets         (True)
        self.buff.set_text                  ('')
        self.buff2.set_text                 ('')
        self.g_pass.set_text                ('')
        self.g_recip.set_text               ('')
        self.g_defaultkey.set_text          ('')
        self.g_plaintext.set_sensitive      (False)
        self.g_plaintext.set_active         (True)
        self.g_chk_outfile.set_visible      (False)
        self.g_chk_outfile.set_active       (False)
        self.g_chooserbtn.set_filename      ('(None)')
        self.in_filename =                  None
        self.out_filename =                 None
        self.x.stdin =                      None
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
                         "{}</span> for reading.</b>\nChoose a new file."
                         .format(infile), gtk.MESSAGE_ERROR)
            return
        if self.g_signverify.get_active():
            self.g_chk_outfile.set_visible(True)
            # Set sigmode combobox to detached mode, because that seems most likely
            self.g_sigmode.set_active(2)
        # Set plaintext output checkbox state based on whether file is binary
        # Also, allow user to change it
        self.g_plaintext.set_sensitive(True)
        if self.test_file_isbinary(infile):
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
        from shlex import split
        from subprocess import check_output
        cbindex = self.g_cipher.get_active()
        cmd = split('sed -i "s/^        self.g_cipher.set_active(.)/        '
                    'self.g_cipher.set_active({})/" {}'.format(cbindex, argv[0]))
        try:
            check_output(cmd)
            self.infobar("<b>Successfully modified file <span style='italic' size='smaller' face='monospace'>"
                         "{}</span>, changing default cipher setting.</b>"
                         .format(argv[0]))
        except:
            self.infobar("<b>Saving cipher setting failed.</b>\nTry again while running "
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
    
    
    def action_cipher_changed(self, widget, data=None):
        if self.engine in 'OpenSSL':
            cipher = self.grab_activetext_combobox(self.g_cipher)
            if not cipher:
                self.g_cipher.set_active(1)
                self.infobar("<b>OpenSSL doesn't have a default cipher.</b>\nAES256 "
                             "is recommended.", gtk.MESSAGE_WARNING, 7)
            elif cipher in 'Twofish':
                self.g_cipher.set_active(1)
                self.infobar("<b>Twofish is not supported by OpenSSL.</b>\nSelect "
                             "a different cipher.", gtk.MESSAGE_WARNING, 7)
            elif cipher in 'AES':
                self.infobar("<b>Note for the commandline peeps:</b>\n'AES' "
                             "translates to aes128.", icon=gtk.STOCK_DIALOG_INFO)
    
    
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
            self.launchxface(action)
        else:
            # Normal enc/dec mode
            self.launchxface('enc')
    
    
    # 'Decrypt'/'Verify' button
    def action_decrypt(self, widget, data=None):
        """Decrypt or verify input."""
        if self.g_signverify.get_active():
            # Verify mode!
            self.launchxface('verify')
        else:
            # Normal enc/dec mode
            self.launchxface('dec')
    
    
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
    def launchxface(self, action):
        """Manage I/O between Gtk objects and our GpgXface or OpensslXface object."""
        
        ### PREPARE GpgXface.gpg() ARGS
        passwd = None ; recip = None ; localuser = None
        # enctoself
        enctoself =  self.g_enctoself.get_active()
        # symmetric & passwd
        symmetric = self.g_symmetric.get_active()
        if symmetric:
            passwd = self.g_pass.get_text()
            if not passwd:
                if self.engine in 'OpenSSL':
                    self.infobar("<b>You must enter a passphrase.</b>", gtk.MESSAGE_WARNING, 3)
                    return
                passwd = None  # If passwd was '' , set to None, which will trigger gpg-agent if necessary
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
        verbose = self.g_taskverbose.get_active()
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
            
            # Save textview buffer to Xface.stdin
            self.x.stdin = self.buff.get_text(self.buff.get_start_iter(),
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
        if self.engine in 'OpenSSL':
            retval = self.x.openssl(action, passwd, cipher)
        else:
            retval = self.x.gpg(action, encsign, digest, localuser, base64,
                                symmetric, passwd,
                                asymmetric, recip, enctoself, cipher,
                                self.in_filename, self.out_filename,
                                verbose, alwaystrust)
        
        self.g_activityspin.stop()
        self.g_activityspin.set_visible(False)
        self.g_statusbar.pop(self.status)
        self.buff2.set_text(self.x.stderr)
        
        # FILE INPUT MODE CLEANUP
        if self.in_filename:
            
            if retval:  # Success!
                
                #self.g_chooserbtn.set_filename('(None)')
                self.filemode_enablewidgets     (True)
                self.g_chk_outfile.set_visible  (False)
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
                    self.infobar("<b>Signature could not be verified.</b>\nSee<i> Task "
                                 "Status </i> for details.", gtk.MESSAGE_WARNING, 7)
                    """ Not sure about this, but I'm gonna go with forcing user to press Clear for now
                    self.g_chooserbtn.set_filename('(None)')
                    self.g_chk_outfile.set_visible(False)
                    self.filemode_enablewidgets(True)
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
                
                self.infobar("<b>Problem {}ing file.</b>\nSee<i> Task Status </i> for details.\n"
                             "Select<i> Clear </i> to do something else, or try again with a "
                             "different passphrase.".format(action), gtk.MESSAGE_ERROR, 8)
        
        # TEXT INPUT MODE CLEANUP
        else:
            
            self.set_stdstatus()
            self.g_msgtxtview.set_sensitive(True)
            self.x.stdin = None
            
            # Success!
            if retval:
                if action in 'verify':
                    self.infobar("<b>Good signature verified.</b>", timeout=4)
                else:
                    # Set TextBuffer to gpg stdout
                    self.buff.set_text(self.x.stdout)
                    if self.engine in 'OpenSSL' and action in 'enc':
                        self.infobar("<b>OpenSSL encrypted input with {} cipher.</b>\n"
                                     "In order to decrypt the output in the future, you will need\n"
                                     "to remember which cipher you used (or try them all)."
                                     .format(cipher), timeout=9)
            
            # Fail!
            else:
                if action in 'verify':
                    self.infobar("<b>Signature could not be verified.</b>\nSee<i> "
                                 "Task Status </i> for details.", gtk.MESSAGE_WARNING, 7)
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar("<b>Problem asymmetrically encrypting input.</b>\nIf you don't "
                                 "want to enter recipients and you don't want to select\n<i> Enc "
                                 "To Self</i>, you must add one of the following to your\ngpg.conf "
                                 "file:\n<b><span size='smaller' face='monospace'>default-recipient-"
                                 "self</span></b> or <b><span size='smaller' face='monospace'>"
                                 "default-recipient <i>name</i></span></b>",
                                 gtk.MESSAGE_ERROR, 0)
                    return
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar("<b>Problem {}ing input.</b>\nSee<i> Task Status </i> for details."
                             .format(action), gtk.MESSAGE_ERROR)
    
    
    
    # Run main application window
    def main(self):
        self.g_window.show()
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True
        gtk.main()



if __name__ == "__main__":
    
    p = Pyrite()
    try:
        p.main()
    except KeyboardInterrupt:
        print
        exit()
    except:
        raise
    
