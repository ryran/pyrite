#!/usr/bin/env python3
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

# StdLib:
import gi

gi.require_version('GLib', '2.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Pango

# gtk.gdk.threads_init()
import glib
# glib.threads_init()
from threading import Thread
from sys import stderr
from os import access, R_OK, read, close, pipe
from os.path import isfile
from urllib.request import url2pathname
from shlex import split
from subprocess import check_output
from time import sleep
# Custom Modules:
from . import cfg
from . import prefs
from . import crypt_interface
from .messages import MESSAGE_DICT

# Important variables
SIGSTOP, SIGCONT = 19, 18
TARGET_TYPE_URI_LIST = 80


class Pyrite:
    """Display GTK+ window to interact with gpg or openssl via Xface object."""

    def show_errmsg(self, msg, dialog=Gtk.MessageType.ERROR, parent=None):
        """Display msg with GtkMessageDialog."""
        d = Gtk.MessageDialog(
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=msg
        )
        d.run()
        d.destroy()

    def __init__(self, cmdlineargs):
        """Build GUI interface from XML, etc."""
        self.x = None
        self.filemode_saved_buff = None
        self.encdec_sig_state_active = False
        self.encdec_sig_state_sensitive = False
        self.canceled = False
        self.paused = False

        # Use GtkBuilder to build our GUI from the XML file 
        builder = Gtk.Builder()
        try:
            builder.add_from_file(cfg.ASSETDIR + 'ui/main.glade')
        except:
            self.show_errmsg(
                "Problem loading GtkBuilder UI definition file at:\n    " +
                cfg.ASSETDIR + "ui/main.glade\nCannot continue.")
            raise

        # GET WIDGETS!
        # Main window
        self.g_window = builder.get_object('window1')
        # Toolbars
        self.g_maintoolbar = builder.get_object('hbox1')
        self.g_modetoolbar = builder.get_object('hbox2')
        self.g_enctoolbar = builder.get_object('hbox3')
        self.g_sigtoolbar = builder.get_object('hbox4')
        # Menu items
        self.g_mclear = builder.get_object('mnu_clear')
        self.g_mopen = builder.get_object('mnu_open')
        self.g_msave = builder.get_object('mnu_save')
        self.g_mengine = builder.get_object('mnu_switchengine')
        self.g_mcut = builder.get_object('mnu_cut')
        self.g_mcopy = builder.get_object('mnu_copy')
        self.g_mpaste = builder.get_object('mnu_paste')
        self.g_mprefs = builder.get_object('mnu_preferences')
        self.g_wrap = builder.get_object('toggle_wordwrap')
        self.g_taskstatus = builder.get_object('toggle_taskstatus')
        self.g_taskverbose = builder.get_object('toggle_gpgverbose')
        # Top action toolbar
        self.g_encrypt = builder.get_object('btn_encrypt')
        self.g_decrypt = builder.get_object('btn_decrypt')
        self.g_bclear = builder.get_object('btn_clear')
        self.g_progbar = builder.get_object('progressbar')
        self.g_cancel = builder.get_object('btn_cancel')
        self.g_pause = builder.get_object('btn_pause')
        self.g_slider = builder.get_object('opacity_slider')
        # Mode-setting toolbar
        self.g_signverify = builder.get_object('toggle_mode_signverify')
        self.g_chk_outfile = builder.get_object('toggle_sign_chooseoutput')
        self.g_encdec = builder.get_object('toggle_mode_encdec')
        self.g_symmetric = builder.get_object('toggle_mode_symmetric')
        self.g_asymmetric = builder.get_object('toggle_mode_asymmetric')
        self.g_advanced = builder.get_object('toggle_advanced')
        # Encryption toolbar
        self.g_passlabel = builder.get_object('label_entry_pass')
        self.g_pass = builder.get_object('entry_pass')
        self.g_reciplabel = builder.get_object('label_entry_recip')
        self.g_recip = builder.get_object('entry_recip')
        self.g_enctoself = builder.get_object('toggle_enctoself')
        self.g_cipherlabel = builder.get_object('label_combobox_cipher')
        self.g_cipher = builder.get_object('combobox_cipher')
        # Middle input area
        self.g_bopen = builder.get_object('btn_open')
        self.g_bsave = builder.get_object('btn_save')
        self.g_bcopyall = builder.get_object('btn_copyall')
        self.g_msgtxtview = builder.get_object('textview1')
        self.buff = self.g_msgtxtview.get_buffer()
        self.vbox_ibar = builder.get_object('vbox_ibar')
        self.vbox_ibar2 = builder.get_object('vbox_ibar2')
        self.g_expander = builder.get_object('expander_filemode')
        self.g_chooserbtn = builder.get_object('btn_filechooser')
        self.g_plaintext = builder.get_object('toggle_plaintext')
        self.g_frame2 = builder.get_object('frame2')
        self.g_errtxtview = builder.get_object('textview2')
        self.buff2 = self.g_errtxtview.get_buffer()
        # Signing toolbar
        self.g_signature = builder.get_object('toggle_signature')
        self.g_sigmode = builder.get_object('combobox_sigmode')
        self.g_digestlabel = builder.get_object('label_combobox_digest')
        self.g_digest = builder.get_object('combobox_digest')
        self.g_chk_defkey = builder.get_object('toggle_defaultkey')
        self.g_defaultkey = builder.get_object('entry_defaultkey')
        # Statusbar
        self.g_statusbar = builder.get_object('statusbar')
        self.g_activityspin = builder.get_object('spinner1')

        # Set app icon to something halfway-decent
        Gtk.Window.set_default_icon_name("dialog-password")

        # Connect signals
        builder.connect_signals(self)

        # Other class attributes
        self.ib_filemode = None
        self.engine = 'missing_backend'
        self.quiting = False
        self.working_widgets_filemode = [
            self.g_mclear, self.g_mprefs, self.g_encrypt, self.g_decrypt, self.g_bclear,
            self.g_modetoolbar, self.g_enctoolbar, self.g_expander, self.g_sigtoolbar]
        self.working_widgets_textmode = [
            self.g_mclear, self.g_mprefs, self.g_encrypt, self.g_decrypt, self.g_bclear,
            self.g_modetoolbar, self.g_enctoolbar, self.g_expander, self.g_sigtoolbar,
            self.g_mengine, self.g_bcopyall, self.g_bopen, self.g_mopen, self.g_bsave,
            self.g_msave, self.g_mcut, self.g_mcopy, self.g_mpaste]

        # Initialize main Statusbar
        self.status = self.g_statusbar.get_context_id('main')
        self.g_statusbar.push(self.status, "Enter message to encrypt/decrypt")

        # Sensitivity for these GtkEntrys not defaulted to False in xml because
        #   that makes their icons stay insensitive-looking forever
        self.g_pass.set_sensitive(False)
        self.g_recip.set_sensitive(False)

        # LOAD PREFERENCES AND SET WIDGET STATES!
        self.preferences = prefs.Preferences()

        # Make a clone of preferences dictionary
        self.p = self.preferences.p

        # Launch gpg/openssl interface
        if cmdlineargs and cmdlineargs.backend:
            backend = cmdlineargs.backend
        else:
            backend = None

        self.instantiate_xface(preferred=backend, startup=True)

        # DRAG AND DROP FUNNESS
        dnd_list = [('text/uri-list', 0, TARGET_TYPE_URI_LIST)]
        # self.g_msgtxtview.drag_dest_set(
        #     Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT,
        #     dnd_list, Gdk.DragAction.COPY)

        # CMDLINE ARGUMENTS
        if cmdlineargs:
            a = cmdlineargs

            if a.input:
                # Direct-file mode arg broken until GtkFileChooserButton bug gets fixed
                if a.direct_file:
                    self.g_chooserbtn.set_filename(a.input)
                    self.g_expander.set_expanded(True)
                elif a.text_input:
                    self.buff.set_text(a.input)
                else:
                    self.open_in_txtview(a.input)

            if self.engine not in 'OpenSSL':
                if a.recipients:
                    self.g_recip.set_text(a.recipients)
                    self.g_asymmetric.set_active(True)
                if a.symmetric:
                    if a.recipients:
                        self.g_advanced.set_active(True)
                    self.g_symmetric.set_active(True)
                if a.defaultkey:
                    self.g_defaultkey.set_text(a.defaultkey)
                    self.g_chk_defkey.set_active(True)
                if a.encdec:
                    self.g_encdec.set_active(True)
                elif a.signverify:
                    self.g_signverify.set_active(True)

    # OUR LOVELY COMM DEVICE
    def infobar(self, id, filename=None, customtext=None, vbox=None):
        """Popup a new auto-hiding InfoBar."""

        # Find the needed dictionary inside our message dict, by id
        MSG = MESSAGE_DICT[id]
        # Use value from MSG type & icon to lookup Gtk constant, e.g. Gtk.MessageType.INFO
        msgtype = cfg.MSGTYPES[MSG['type']]
        imgtype = cfg.IMGTYPES[MSG['icon']]
        # Replace variables in message text & change text color
        message = ("<span foreground='#2E2E2E'>" +
                   MSG['text'].format(filename=filename, customtext=customtext) +
                   "</span>")

        # Now that we have all the data we need, START creating!
        ibar = Gtk.InfoBar()
        ibar.set_message_type(msgtype)
        if vbox:
            # If specific vbox requested: assume ibar for filemode, add cancel button
            ibar.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            ibar.connect('response', self.cleanup_filemode)
        else:
            # If no specific vbox requested: do normal ibar at the top of message area
            vbox = self.vbox_ibar
            ibar.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            ibar.connect('response', lambda *args: ibar.destroy())
        vbox.pack_end(ibar, False, False, 0)
        content = ibar.get_content_area()
        img = Gtk.Image()
        img.set_from_stock(imgtype, Gtk.IconSize.LARGE_TOOLBAR)
        content.pack_start(img, False, False, 0)
        img.show()
        label = Gtk.Label()
        label.set_markup(message)
        content.pack_start(label, False, False, 0)
        label.show()
        # FIXME: Why doesn't Esc trigger this close signal?
        ibar.connect('close', lambda *args: ibar.destroy())
        ibar.show()
        if MSG['timeout'] > 0:
            GLib.timeout_add_seconds(MSG['timeout'], ibar.destroy)
        return ibar

    # BRING UP GPG/OPENSSL
    def instantiate_xface(self, preferred=None, startup=False):
        """Instantiate Gpg or Openssl interface."""

        # If we weren't passed preferred argument, set desired interface to backend pref
        if not preferred:
            b = ['gpg', 'openssl']
            # self.p['backend'] contains 0, 1, or 2, corresponding to the above items in b
            # Desired: convert the number setting to the human-readable name and store as b
            b = b[self.p['backend']]
            preferred = b

        # Loading gpg
        def gpg(fallback=False):
            self.x = crypt_interface.Gpg()
            self.engine = 'GPG'
            self.g_mengine.set_label("Use OpenSSL as Engine")
            if fallback:
                self.g_mengine.set_sensitive(False)
                self.infobar('engine_openssl_missing')

        # Loading openssl
        def openssl(fallback=False):
            self.x = crypt_interface.Openssl()
            self.engine = 'OpenSSL'
            self.g_mengine.set_label("Use GnuPG as Engine")
            if fallback:
                self.g_mengine.set_sensitive(False)
                self.infobar('engine_gpg_missing')
            else:
                self.infobar('engine_openssl_notice')

        # Setup for neutered-run (when missing all backends)
        def err_allmissing():
            self.infobar('engine_all_missing')
            self.g_mengine.set_sensitive(False)
            for w in self.g_encrypt, self.g_decrypt:
                w.set_sensitive(False)

            class dummy:
                pass

            self.x = dummy()
            self.x.io = dict(stdin='', stdout='', gstatus=0, infile=0, outfile=0)

        # Get it done!
        if preferred in 'openssl':
            # If loading openssl, try that first, then fallback to gpg
            try:
                openssl()
            except:
                try:
                    gpg(fallback=True)
                except:
                    err_allmissing()
        else:
            # If loading gpg, try that first, then fallback to openssl
            try:
                gpg()
            except:
                try:
                    openssl(fallback=True)
                except:
                    err_allmissing()

        self.g_window.set_title("Pyrite [{}]".format(self.engine))

        self.buff2.set_text("Any output generated from calls to {} will be "
                            "displayed here.\n\n"
                            "In the View menu you can change "
                            "the verbosity level, hide this pane, or simply change "
                            "the font size.".format(self.engine))

        self.set_defaults_from_prefs(startup)

    # SET OPMODES, ETC, FROM PREFS
    def set_defaults_from_prefs(self, startup=False):
        """Set window toggle states via preferences."""

        if self.p['enctype'] == 0:
            self.g_symmetric.set_active(True)
        elif self.p['enctype'] == 1:
            self.g_asymmetric.set_active(True)
        elif self.p['enctype'] == 2:
            self.g_advanced.set_active(True)
            self.g_symmetric.set_active(True)
            self.g_asymmetric.set_active(True)

        if self.p['advanced']:
            self.g_advanced.set_active(True)

        if self.p['advanced'] or self.p['enctype'] > 0:
            if self.p['addsig']:
                self.g_signature.set_active(True)
            if self.p['enctoself']:
                self.g_enctoself.set_active(True)

        if self.p['opmode']:
            self.g_signverify.set_active(True)

        if not self.g_expander.get_expanded():
            self.g_expander.set_expanded(self.p['expander'])

        self.g_cipher.set_active(self.p['cipher'])
        self.g_digest.set_active(self.p['digest'])
        self.g_chk_defkey.set_active(self.p['defkey'])
        self.g_defaultkey.set_text(self.p['defkeytxt'])

        if startup:
            self.g_taskstatus.set_active(self.p['taskstatus'])
            self.g_taskverbose.set_active(self.p['verbose'])
            self.g_wrap.set_active(self.p['wrap'])

            # Set TextView fonts, sizes, and colors
            self.g_msgtxtview.modify_font(
                Pango.FontDescription("monospace {}".format(self.p['msgfntsize'])))
            self.g_errtxtview.modify_font(
                Pango.FontDescription("normal {}".format(self.p['errfntsize'])))

            bg_color = Gdk.Color(0, 0, 0)
            bg_color.parse(self.p['color_bg'])
            fg_color = Gdk.Color(0, 0, 0)
            fg_color.parse(self.p['color_fg'])
            self.g_msgtxtview.modify_base(
                Gtk.StateType.NORMAL, bg_color)
            self.g_msgtxtview.modify_text(
                Gtk.StateType.NORMAL, fg_color)

            if self.p['opc_slider']:
                self.g_slider.set_range(0, 100)
                self.g_slider.set_value(self.p['opacity'])
                self.g_slider.set_tooltip_text("Change window opacity (current:{}%)".format(self.p['opacity']))
                self.g_slider.set_visible(True)
            else:
                self.g_window.set_opacity(self.p['opacity'] / 100.0)

        # These are all the widgets that can't be used in openssl mode
        def setsensitive_gpgwidgets(x=True):
            self.g_signverify.set_sensitive(x)
            self.g_symmetric.set_sensitive(x)
            self.g_asymmetric.set_sensitive(x)
            self.g_advanced.set_sensitive(x)
            self.g_chk_defkey.set_sensitive(x)
            self.g_taskverbose.set_visible(x)  # OpenSSL doesn't have verbosity

        if self.engine in 'OpenSSL':
            self.g_encdec.set_active(True)
            self.g_symmetric.set_active(True)
            self.g_advanced.set_active(False)
            self.g_chk_defkey.set_active(False)
            if startup or self.g_cipher.get_active() in {0, 2}:
                # If starting up, or current cipher set to 'Default' or 'Twofish'
                if self.p['cipher'] not in {0, 2}:
                    # Set cipher to preference unless pref is 'Default' or 'Twofish'
                    self.g_cipher.set_active(self.p['cipher'])
                else:
                    # Otherwise, set to AES
                    self.g_cipher.set_active(1)
            setsensitive_gpgwidgets(False)
        else:
            setsensitive_gpgwidgets(True)

    # HELPER FUNCTIONS

    def fix_msgtxtview_color(self, sensitive):
        """Change Message area text to black when TextView insensitive."""
        if sensitive:
            fg_color = Gdk.Color(0, 0, 0)
            fg_color.parse(self.p['color_fg'])
            self.g_msgtxtview.modify_text(
                Gtk.StateType.NORMAL, fg_color)
        else:
            fg_color = Gdk.Color(0, 0, 0)
            fg_color.parse('black')
            self.g_msgtxtview.modify_text(
                Gtk.StateType.NORMAL, fg_color)

    def get_file_path_from_dnd_dropped_uri(self, uri):
        path = ''
        if uri.startswith('file:\\\\\\'):  # windows
            path = uri[8:]  # 8 is len('file:///')
        elif uri.startswith('file://'):  # nautilus, rox
            path = uri[7:]  # 7 is len('file://')
        elif uri.startswith('file:'):  # xffm
            path = uri[5:]  # 5 is len('file:')
        path = url2pathname(path)  # escape special chars
        path = path.strip('\r\n\x00')  # remove \r\n and NULL
        return path

    def set_stdstatus(self):
        """Set a standard mode-dependent status message."""
        self.g_statusbar.pop(self.status)
        if self.g_signverify.get_active():
            s = "Enter message to sign or verify"
        else:
            s = "Enter message to encrypt or decrypt"
        self.g_statusbar.push(self.status, s)

    def test_file_is_plain_text(self, filename):
        """Utilize nix file cmd to determine if filename is binary or text."""
        cmd = split("file -b -e soft '{}'".format(filename))
        output = check_output(cmd)
        return output[:4] in (b'ASCI', b'UTF-')

    def open_in_txtview(self, filename):
        """Replace contents of msg TextView's TextBuffer with contents of file."""
        try:
            with open(filename) as f:
                self.buff.set_text(f.read())
            if self.buff.get_char_count() < 1:
                self.infobar('txtview_fileopen_binary_error')
        except:
            self.infobar('txtview_fileopen_error', filename)

    # This is called when entering & exiting direct-file mode
    def filemode_enablewidgets(self, x=True):
        """Enable/disable certain widgets due to working in direct-file mode."""
        widgets = [self.g_mengine, self.g_bcopyall, self.g_bopen, self.g_mopen,
                   self.g_bsave, self.g_msave, self.g_mcut, self.g_mcopy,
                   self.g_mpaste, self.g_msgtxtview]
        for w in widgets:
            w.set_sensitive(x)
        self.fix_msgtxtview_color(x)

    # This is called when user tries to copyall, save, or {en,de}crypt/sign/verify
    def test_msgbuff_isempty(self, message):
        """Return True + show infobar containing msg if Message area is empty."""
        if self.buff.get_char_count() < 1:
            self.infobar('txtview_empty', customtext=message)
            return True

    def confirm_overwrite_callback(self, chooser):
        """In filechooser, disallow output file being the input file."""
        outfile = chooser.get_filename()
        if self.x.io['infile'] == outfile:
            self.show_errmsg(
                "Simultaneously reading from & writing to a file is a baaad idea. "
                "Choose a different output filename.", parent=chooser)
            return Gtk.FileChooserConfirmation.SELECT_AGAIN
        else:
            return Gtk.FileChooserConfirmation.CONFIRM

    # Generic file chooser for opening or saving
    def chooser_grab_filename(self, mode, save_suggestion=None):
        """Present file chooser dialog and return filename or None."""

        filename = None
        if mode in 'open':
            title = "Choose text file to open as input..."
        elif mode in 'save':
            title = "Choose output filename..."
        cmd = ("Gtk.FileChooserDialog('{0}', None, Gtk.FileChooserAction.{1}, "
               "(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))"
               .format(title, mode.upper()))
        chooser = eval(cmd)

        if mode in 'open':
            # Setup file filters
            t = Gtk.FileFilter()
            t.set_name("Text Files")
            t.add_mime_type("text/*")
            a = Gtk.FileFilter()
            a.set_name("All Files")
            a.add_pattern("*")
            chooser.add_filter(t)
            chooser.add_filter(a)
        elif mode in 'save':
            # Setup overwrite-confirmation cb + current filename
            chooser.set_do_overwrite_confirmation(True)
            chooser.connect('confirm-overwrite', self.confirm_overwrite_callback)
            if save_suggestion:
                chooser.set_current_name(save_suggestion)

        if chooser.run() == Gtk.ResponseType.OK:
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
        """Use FileChooser to get an output filename for direct enc/dec."""

        # Prompt for output file
        outfile = self.chooser_grab_filename('save', self.x.io['infile'])

        # Kick off processing unless user canceled
        if outfile:
            self.x.io['outfile'] = outfile
            self.launchxface(mode)

    def initiate_filemode(self):
        """Ensure read access of file set by chooser widget and notify user of next steps."""

        # Prompt for filename but err out if file can't be read
        infile = self.g_chooserbtn.get_filename()
        if not access(infile, R_OK):
            self.infobar('filemode_fileopen_error', infile)
            return

        # Tweak some widgets if in Sign/Verify mode
        if self.g_signverify.get_active():
            self.g_chk_outfile.set_visible(True)
            self.g_chk_outfile.set_active(self.p['svoutfiles'])
            self.g_sigmode.set_active(self.p['file_sigmode'])

        # Configure state of plaintext output checkbox via user-settings
        self.g_plaintext.set_sensitive(True)

        if self.p['txtoutput'] == 0:  # Autodetect
            self.g_plaintext.set_active(self.test_file_is_plain_text(infile))
        elif self.p['txtoutput'] == 1:  # Always Binary
            self.g_plaintext.set_active(False)
        elif self.p['txtoutput'] == 2:  # Always Text
            self.g_plaintext.set_active(True)

        # Set statusbar w/ filemode status
        self.g_statusbar.pop(self.status)
        self.g_statusbar.push(self.status, "Choose an action to perform on {!r}".format(infile))

        if self.ib_filemode:
            # If filemode infobar already present: user picked a new file, so destroy old ibar
            self.ib_filemode.destroy()
        else:
            # Otherwise, save TextView buffer for later and then blow it away
            self.filemode_saved_buff = self.buff.get_text(self.buff.get_start_iter(),
                                                          self.buff.get_end_iter(),
                                                          False)
            self.buff.set_text('')
            self.filemode_enablewidgets(False)

        # Create filemode infobar with cancel button
        self.ib_filemode = self.infobar('filemode_blue_banner', infile, vbox=self.vbox_ibar2)

        # Set input file
        self.x.io['infile'] = infile

    def cleanup_filemode(self, *args):
        """Revert the changes (to widgets, etc) that filemode causes."""
        # Restore message buffer
        self.buff.set_text(self.filemode_saved_buff)
        del self.filemode_saved_buff
        # Destroy persistent filemode infobar
        self.ib_filemode.destroy()
        self.ib_filemode = None
        # Enable/sensitize widgets
        self.filemode_enablewidgets(True)
        self.g_chk_outfile.set_visible(False)
        # Ensure sigmode combobox is back to proper 'normal'
        if self.g_signverify.get_active():
            self.g_sigmode.set_active(self.p['text_sigmode'])
        else:
            self.g_sigmode.set_active(0)
        # Set statusbar
        self.set_stdstatus()
        # while Gtk.events_pending():
        Gtk.main_iteration()
        # Reset filenames
        self.x.io['infile'] = 0
        self.x.io['outfile'] = 0
        # Disable plaintext CheckButton
        self.g_plaintext.set_sensitive(False)
        self.g_plaintext.set_active(True)

    # HERE BE GTK SIGNAL CBs

    # Called by window destroy / Quit menu item
    def action_quit(self, w):
        """Shutdown application and any child process."""
        self.quiting = True
        if self.x.childprocess and self.x.childprocess.returncode is None:
            if self.paused:
                self.x.childprocess.send_signal(SIGCONT)
            self.x.childprocess.terminate()
            stderr.write("<Quiting>\n")
            # sleep(0.2)
        Gtk.main_quit()

    # Called when dnd occurs on Message TextView
    def action_drag_data_received(self, w, context, x, y, selection, target_type, timestamp):
        """Read dragged text file into Message area."""
        if target_type == TARGET_TYPE_URI_LIST:
            uri = selection.data.strip('\r\n\x00')
            uri = uri.split()[0]
            path = self.get_file_path_from_dnd_dropped_uri(uri)
            if isfile(path):
                self.open_in_txtview(path)

    # Called by changing opacity hscale
    def action_opacity_slider(self, w):
        """Actions to perform when opacity scale is changed."""
        val = w.get_value()
        self.g_window.set_opacity(val / 100.0)
        w.set_tooltip_text(
            "Change window opacity (current:{:.1f}%)".format(val))

    # Called by SwitchEngine menu item
    def action_switch_engine(self, w):
        """Switch backend between openssl & gpg."""
        if self.engine in 'OpenSSL':
            self.instantiate_xface('gpg')
        else:
            self.instantiate_xface('openssl')

    # Called by About menu item
    def action_about(self, w):
        """Launch About dialog."""
        builder = Gtk.Builder()
        builder.add_from_file(cfg.ASSETDIR + 'ui/about.glade')
        about = builder.get_object('aboutdialog')
        about.set_logo_icon_name(Gtk.STOCK_DIALOG_AUTHENTICATION)
        # about.set_transient_for(self.g_window)
        about.set_version(cfg.VERSION)
        about.connect('response', lambda *args: about.destroy())
        about.show()

    # Called by Preferences menu item
    def action_preferences(self, w):
        """Launch preferences window."""

        # Run preferences window method from already-open pref instance
        self.preferences.open_preferences_window(parentwindow=self.g_window)

        # CB for pref window's save button
        def savepref(*args):
            # Attempt to save preferences
            if self.preferences.save_prefs():
                # If success: destroy pref window, show infobar
                self.preferences.window.destroy()
                self.infobar('preferences_save_success', cfg.USERPREF_FILE)

        # CB for pref window's apply button
        def applypref(*args):
            # Attempt to save preferences
            if self.preferences.save_prefs():
                # If success, destroy pref window, import new prefs, show infobar
                self.preferences.window.destroy()
                self.p = self.preferences.p
                if self.x.io['infile']:
                    self.cleanup_filemode()
                self.instantiate_xface(startup=True)
                self.infobar('preferences_apply_success', cfg.USERPREF_FILE)

        # Connect signals
        self.preferences.btn_save.connect('clicked', savepref)
        self.preferences.btn_apply.connect('clicked', applypref)

    # Called by Clear toolbar btn or menu item
    def action_clear(self, w):
        """Reset Statusbar, filemode stuff, TextView buffers."""
        if self.x.io['infile']:
            self.cleanup_filemode()
        else:
            self.set_stdstatus()
        self.buff.set_text('')
        self.buff2.set_text('')
        self.x.io = dict(stdin='', stdout='', gstatus=0, infile=0, outfile=0)

    # Called when user clicks the entry_icon in any of the entry widgets
    def action_clear_entry(self, entry, *args):
        """Clear TextEntry widget."""
        entry.set_text('')

    # Called by Open toolbar btn or menu item
    def action_open(self, w):
        """Read in a text file and push its contents to our TextView."""
        filename = self.chooser_grab_filename('open')
        if filename:
            self.open_in_txtview(filename)

    # Called when direct-file-mode FileChooserButton gets a new file set,
    #   either because of dnd or manual selection
    def action_chooserbtn_file_set(self, w):
        print("[on_file-set] FileChooserButton.get_filename() output:\n{!r}\n".format(w.get_filename()))
        self.initiate_filemode()

    # Called by Save toolbar btn or menu item
    def action_save(self, w):
        """Save contents of msg TextView's TextBuffer to file."""

        # If Message area is empty, err out
        if self.test_msgbuff_isempty("No text to save."):
            return

        # Prompt for filename to save to; cancel if user cancels
        filename = self.chooser_grab_filename('save')
        if not filename:
            return

        # Set saving status
        self.g_statusbar.push(self.status, "Saving {}".format(filename))
        # while Gtk.events_pending():
        Gtk.main_iteration()

        # Grab text from buffer
        buffertext = self.buff.get_text(self.buff.get_start_iter(),
                                        self.buff.get_end_iter(),
                                        False)
        try:
            # If can open file for writing, show success infobar
            with open(filename, 'w') as f:
                f.write(buffertext)
            self.infobar('txtview_save_success', filename)
        except:
            # Otherwise, show error
            self.infobar('txtview_save_error', filename)

        # Clear saving status
        self.g_statusbar.pop(self.status)

    def action_undo(self, w):
        pass

    def action_redo(self, w):
        pass

    # Called by Cut toolbar btn or menu item
    def action_cut(self, w):
        """Cut msg TextBuffer selection."""
        self.buff.cut_clipboard(Gtk.clipboard_get(), True)

    # Called by Copy toolbar btn or menu item
    def action_copy(self, w):
        """Copy msg TextBuffer selection."""
        self.buff.copy_clipboard(Gtk.clipboard_get())

    # Called by Paste toolbar btn or menu item
    def action_paste(self, w):
        """Paste clipboard into msg TextBuffer at selection."""
        self.buff.paste_clipboard(Gtk.clipboard_get(), None, True)

    # Called by Copyall toolbar btn
    def action_copyall(self, w):
        """Select whole msg TextBuffer contents and copy it to clipboard."""
        if self.test_msgbuff_isempty("No text to copy."):
            return
        self.buff.select_range(self.buff.get_start_iter(),
                               self.buff.get_end_iter())
        self.buff.copy_clipboard(Gtk.clipboard_get())
        self.infobar('txtview_copyall_success')

    # Called by Zoom menu items
    def action_zoom(self, w):
        """Increase/decrease font size of TextViews."""
        zoom = w.get_label()[:7]
        if zoom in 'Increase':
            self.p['msgfntsize'] += 1
            self.p['errfntsize'] += 1
        elif zoom in 'Decrease':
            self.p['msgfntsize'] -= 1
            self.p['errfntsize'] -= 1
        self.g_msgtxtview.modify_font(
            Pango.FontDescription("monospace {}".format(self.p['msgfntsize'])))
        self.g_errtxtview.modify_font(
            Pango.FontDescription("normal {}".format(self.p['errfntsize'])))

    # Called when Cipher combobox selection is changed
    def action_cipher_changed(self, w):
        """Disallow certain cipher selections in OpenSSL mode."""
        if self.engine in 'OpenSSL':
            cipher = self.grab_activetext_combobox(self.g_cipher)
            if not cipher:
                self.g_cipher.set_active(1)
                self.infobar('cipher_openssl_no_default')
            elif cipher in 'Twofish':
                self.g_cipher.set_active(1)
                self.infobar('cipher_openssl_no_twofish')
            elif cipher in 'AES':
                self.infobar('cipher_openssl_aes_note')

    # Called by Encrypt/Sign toolbar btn
    def action_encrypt(self, w):
        """Encrypt or sign input."""
        if self.g_signverify.get_active():
            # If in sign-only mode, figure out which sig-type
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

    # Called by Decrypt/Verify toolbar btn
    def action_decrypt(self, w):
        """Decrypt or verify input."""
        if self.g_signverify.get_active():
            # If in sign-only mode, do verify
            self.launchxface('verify')
        else:
            # Normal enc/dec mode
            self.launchxface('dec')

    # Called by Symmetric checkbox toggle
    def action_toggle_symmetric(self, w):
        """Toggle symmetric encryption (enable/disable certain widgets)."""

        symm_widgets = [self.g_passlabel, self.g_pass]

        if w.get_active():
            # If entering toggled state, allow pass entry
            for widget in symm_widgets:
                widget.set_sensitive(True)
            if not self.g_advanced.get_active():
                # If not in advanced mode, disable Asymmetric
                self.g_asymmetric.set_active(False)

        else:
            # If leaving toggled state, hide pass entry
            for widget in symm_widgets:
                widget.set_sensitive(False)
            if not self.g_asymmetric.get_active():
                # If unchecking Symm & Asymm isn't already on, turn it on
                self.g_asymmetric.set_active(True)

    # Called by Asymmetric checkbox toggle
    def action_toggle_asymmetric(self, w):
        """Toggle asymmetric encryption (enable/disable certain widgets)."""

        asymm_widgets = [self.g_reciplabel, self.g_recip, self.g_enctoself]

        if w.get_active():
            # If entering toggled state, allow recip entry, enctoself
            for widget in asymm_widgets:
                widget.set_sensitive(True)
            self.g_signature.set_sensitive(True)
            if not self.g_advanced.get_active():
                # If not in advanced mode, disable Symmetric
                self.g_symmetric.set_active(False)
            self.load_recipients_autocmplete()
        else:
            # If leaving toggled state, hide recip entry, enctoself
            for widget in asymm_widgets:
                widget.set_sensitive(False)
            self.g_enctoself.set_active(False)
            if not self.g_advanced.get_active():
                # If not in advanced mode, ensure add signature is unchecked
                self.g_signature.set_sensitive(False)
                self.g_signature.set_active(False)
            if not self.g_symmetric.get_active():
                # If unchecking Asymm & Symm isn't already on, turn it on
                self.g_symmetric.set_active(True)

    # Called by Advanced checkbox toggle
    def action_toggle_advanced(self, w):
        """Enable/disable encryption widgets for advanced mode."""

        if w.get_active():
            # If entering the toggled state, allow adding signature
            self.g_signature.set_sensitive(True)

        else:
            # If leaving the toggled state...
            if self.g_symmetric.get_active():
                # We have some things to do if Symmetric is checked...
                if self.g_asymmetric.get_active():
                    # If Asymmetric is also checked, disable it
                    self.g_asymmetric.set_active(False)
                else:
                    # If Asymmetric isn't checked, ensure addsig is disabled
                    self.g_signature.set_sensitive(False)
                    self.g_signature.set_active(False)

    # Called by Sign/Verify radio toggle
    def action_toggle_mode_signverify(self, w):
        """Hide/show, change some widgets when switching modes."""

        enc_widgets = [self.g_symmetric, self.g_asymmetric, self.g_advanced, self.g_enctoolbar]

        # Change statusbar
        self.set_stdstatus()

        if w.get_active():
            # If entering the toggled state: modify buttons, hide & show widgets
            # Modify Encrypt/Decrypt button labels
            self.g_encrypt.set_label("Sign")
            self.g_decrypt.set_label("Verify")
            # Hide encryption toolbar & Symmetric, Asymmetric, Adv toggles
            for widget in enc_widgets:
                widget.set_visible(False)
            # Save state of AddSignature for switching back to Enc/Dec mode
            self.encdec_sig_state_sensitive = self.g_signature.get_sensitive()
            self.encdec_sig_state_active = self.g_signature.get_active()
            # Desensitize AddSignature checkbox and turn it on
            self.g_signature.set_sensitive(False)
            self.g_signature.set_active(True)
            # Sensitize sigmode combobox
            self.g_sigmode.set_sensitive(True)
            # Set sigmode combobox via user prefs
            if self.x.io['infile']:
                self.g_sigmode.set_active(self.p['file_sigmode'])
                self.g_chk_outfile.set_visible(True)
            else:
                self.g_sigmode.set_active(self.p['text_sigmode'])

        else:
            # If leaving the toggled state, we have some things to reverse
            self.g_encrypt.set_label("_Encrypt")
            self.g_decrypt.set_label("_Decrypt")
            self.g_chk_outfile.set_visible(False)
            for widget in enc_widgets:
                widget.set_visible(True)
            self.g_signature.set_sensitive(self.encdec_sig_state_sensitive)
            self.g_signature.set_active(self.encdec_sig_state_active)
            self.g_sigmode.set_sensitive(False)
            self.g_sigmode.set_active(0)  # Reset to 'Embedded' type for Enc/Dec mode

    # Called by 'Change Default Key' checkbox toggle
    def action_toggle_defaultkey(self, w):
        """Hide/show Entry widget for setting gpg 'localuser' argument."""

        if w.get_active():
            # If entering toggled state, show default key TextEntry
            self.g_defaultkey.set_visible(True)
        else:
            # If leaving toggled state, hide default key TextEntry
            self.g_defaultkey.set_visible(False)

    # Called by 'Add Signature' checkbox toggle
    def action_toggle_signature(self, w):
        """Hide/show some widgets when toggling adding of a signature to input."""

        sig_widgets = [self.g_sigmode, self.g_digest, self.g_digestlabel]

        if w.get_active():
            # If entering toggled state, show sig toolbar widgets
            for widget in sig_widgets:
                widget.set_visible(True)
        else:
            # If leaving toggled state, hide sig toolbar widgets
            for widget in sig_widgets:
                widget.set_visible(False)

    # Called by 'Task Status Side Panel' checkbox toggle
    def action_toggle_taskstatus(self, w):
        """Show/hide side pane containing gpg stderr output."""
        if w.get_active():
            # If entering toggled state, show Task Status TextView frame
            self.g_frame2.set_visible(True)
        else:
            # If leaving toggled state, hide Task Status TextView frame
            self.g_frame2.set_visible(False)

    # Called by 'Text Wrapping' checkbox toggle
    def action_toggle_wordwrap(self, w):
        """Toggle word wrapping for main message TextView."""
        if w.get_active():
            # If entering toggled state, enable word wrapping
            self.g_msgtxtview.set_wrap_mode(Gtk.WrapMode.WORD)
        else:
            # If leaving toggled state, disable word wrapping
            self.g_msgtxtview.set_wrap_mode(Gtk.WrapMode.NONE)

    # Called by [processing progbar] Cancel button
    def action_cancel_child_process(self, btn):
        """Terminate gpg/openssl subprocess."""

        stderr.write("Canceling Operation\n")
        self.canceled = True
        for w in self.g_cancel, self.g_pause:
            w.set_sensitive(False)
        self.g_progbar.set_text("Canceling Operation...")
        self.g_activityspin.stop()
        Gtk.main_iteration()
        while not self.x.childprocess:
            Gtk.main_iteration()
        if self.paused:
            self.x.childprocess.send_signal(SIGCONT)
        self.x.childprocess.terminate()
        self.show_working_progress(False)

    # Called by [processing progbar] Pause button
    def action_pause_child_process(self, btn):
        """Suspend/resume gpg/openssl subprocess with SIGSTOP/SIGCONT."""

        # We can't pause childprocess until it actually starts
        while not self.x.childprocess:
            Gtk.main_iteration()

        if self.paused:
            # Already paused, so, time to unpause
            stderr.write("<Unpausing>\n")
            self.paused = False
            btn.set_relief(Gtk.ReliefStyle.NONE)
            self.g_progbar.set_text("{} working...".format(self.engine))
            self.g_activityspin.start()
            self.x.childprocess.send_signal(SIGCONT)
        else:
            # Time to pause
            stderr.write("<Pausing>\n")
            self.paused = True
            btn.set_relief(Gtk.ReliefStyle.NORMAL)
            self.g_progbar.set_text("Operation PAUSED")
            self.g_activityspin.stop()
            self.x.childprocess.send_signal(SIGSTOP)

    # MAIN XFACE FUNCTION
    def launchxface(self, action):
        """Manage I/O between Gtk objects and our GpgXface or OpensslXface object."""
        # User Canceled
        self.canceled = False
        self.paused = False
        self.x.childprocess = None

        # PREPARE Xface ARGS
        passwd = None
        recip = None
        localuser = None
        # symmetric & passwd
        symmetric = self.g_symmetric.get_active()
        if symmetric:
            passwd = self.g_pass.get_text()
            if not passwd:
                if self.engine in 'OpenSSL':
                    self.infobar('x_missing_passphrase')
                    return
                passwd = None  # If passwd was '' , set to None, which will trigger gpg-agent if necessary

        # INTERLUDE: If operating in textinput mode, check for input text
        if not self.x.io['infile']:
            # Make sure textview has a proper message in it
            if self.test_msgbuff_isempty("Input your message text first."):
                return False
            # Make TextView immutable to changes
            self.g_msgtxtview.set_sensitive(False)
            self.fix_msgtxtview_color(False)

        # enctoself
        enctoself = self.g_enctoself.get_active()
        # recip
        asymmetric = self.g_asymmetric.get_active()
        if asymmetric:
            recip = self.g_recip.get_text()
            if not recip:
                recip = None  # If recip was '' , set to None
        # cipher, base64
        cipher = self.grab_activetext_combobox(self.g_cipher)
        base64 = self.g_plaintext.get_active()
        # encsign
        if action in 'enc':
            encsign = self.g_signature.get_active()
        else:
            encsign = False
        # digest
        digest = self.grab_activetext_combobox(self.g_digest)
        # verbose
        verbose = self.g_taskverbose.get_active()
        # alwaystrust (setting True would allow encrypting to untrusted keys,
        #   which is how the nautilus-encrypt tool from seahorse-plugins works)
        alwaystrust = True
        # localuser
        if self.g_chk_defkey.get_active():
            localuser = self.g_defaultkey.get_text()
            if not localuser:
                localuser = None

        # INITIAL FILE INPUT MODE PREP
        if self.x.io['infile'] and not self.x.io['outfile']:
            if base64 or action in 'clearsign':
                outfile = self.x.io['infile'] + '.asc'
            elif self.engine in 'OpenSSL':
                outfile = self.x.io['infile']
            elif action in 'detachsign':
                outfile = self.x.io['infile'] + '.sig'
            else:
                outfile = self.x.io['infile'] + '.gpg'

            if action in 'dec':
                outfile = self.x.io['infile'][:-4]

            if action not in 'verify':
                if self.g_signverify.get_active() and not self.g_chk_outfile.get_active():
                    pass
                else:
                    outfile = self.chooser_grab_filename('save', outfile)
                    if outfile:
                        self.x.io['outfile'] = outfile
                    else:
                        return

            working_widgets = self.working_widgets_filemode
            for w in working_widgets:
                w.set_sensitive(False)
            self.ib_filemode.hide()

        # FILE INPUT MODE PREP WHEN ALREADY HAVE OUTPUT FILE
        elif self.x.io['infile'] and self.x.io['outfile']:
            working_widgets = self.working_widgets_filemode
            for w in working_widgets:
                w.set_sensitive(False)
            self.ib_filemode.hide()

        # TEXT INPUT MODE PREP
        else:
            working_widgets = self.working_widgets_textmode
            for w in working_widgets:
                w.set_sensitive(False)
            # Save textview buffer to Xface stdin
            self.x.io['stdin'] = self.buff.get_text(self.buff.get_start_iter(),
                                                    self.buff.get_end_iter(),
                                                    False)

        # Set working status + spinner + progress bar
        self.show_working_progress(True, action)
        # Clear Task Status
        self.buff2.set_text('')

        # Setup stderr file descriptors & update task status while processing
        self.x.io['stderr'] = pipe()
        GLib.io_add_watch(
            self.x.io['stderr'][0],
            GLib.IOCondition.IN | GLib.IOCondition.HUP,
            self.update_task_status)

        if self.engine in 'OpenSSL':
            # ATTEMPT EN-/DECRYPTION w/OPENSSL
            Thread(
                target=self.x.openssl,
                args=(action, passwd, base64, cipher)
            ).start()

        else:
            # GPG
            if verbose:
                # Setup gpg-status file descriptors & update terminal while processing
                self.x.io['gstatus'] = pipe()
                GLib.io_add_watch(
                    self.x.io['gstatus'][0],
                    GLib.IOCondition.IN | GLib.IOCondition.HUP,
                    self.update_task_status, 'term')
            # ATTEMPT EN-/DECRYPTION w/GPG
            Thread(
                target=self.x.gpg,
                args=(action, encsign, digest, localuser, base64, symmetric, passwd,
                      asymmetric, recip, enctoself, cipher, verbose, alwaystrust)
            ).start()

        # Wait for subprocess to finish or for Cancel button to be clicked
        c = 0
        while not self.x.childprocess or self.x.childprocess.returncode is None:
            if self.canceled:
                break
            if c % 15 == 0 and not self.paused:
                self.g_progbar.pulse()
            Gtk.main_iteration()
            c += 1
        if self.quiting:
            # If application is shutting down
            return
        # Restore widgets to normal states
        for w in working_widgets:
            w.set_sensitive(True)
        self.show_working_progress(False)

        # FILE INPUT MODE CLEANUP
        if self.x.io['infile']:
            if self.canceled:  # User Canceled!
                self.ib_filemode.show()
                if action in {'enc', 'dec'}:
                    action = "{}rypt".format(action.title())
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = "Sign"
                elif action in 'verify':
                    action = action.title()
                self.infobar('x_canceled_filemode', customtext=action)
            elif self.x.childprocess.returncode == 0:  # File Success!
                if self.engine in 'OpenSSL' and action in 'enc':
                    self.infobar('x_opensslenc_success_filemode', self.x.io['outfile'], cipher)
                elif action in {'enc', 'dec'}:
                    self.infobar('x_crypt_success_filemode', self.x.io['outfile'], action)
                elif action in {'embedsign', 'clearsign'}:
                    self.infobar('x_sign_success_filemode', self.x.io['outfile'])
                elif action in 'detachsign':
                    self.infobar('x_detachsign_success_filemode', self.x.io['outfile'])
                elif action in 'verify':
                    self.infobar('x_verify_success')
                self.cleanup_filemode()
            else:  # File Fail!
                self.ib_filemode.show()
                if action in 'verify':
                    self.infobar('x_verify_failed')
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar('x_missing_recip')
                    return
                elif action in {'enc', 'dec'}:
                    action += 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar('x_generic_failed_filemode', customtext=action)

        # TEXT INPUT MODE CLEANUP
        else:
            self.set_stdstatus()
            self.g_msgtxtview.set_sensitive(True)
            self.fix_msgtxtview_color(True)
            if self.canceled:  # User Canceled!
                if action in {'enc', 'dec'}:
                    action = "{}rypt".format(action.title())
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = "Sign"
                elif action in 'verify':
                    action = action.title()
                self.infobar('x_canceled_textmode', customtext=action)
            elif self.x.childprocess.returncode == 0:  # Text Success!
                if action in 'verify':
                    self.infobar('x_verify_success')
                else:
                    # Set TextBuffer to gpg stdout
                    b = self.x.io['stdout'].decode('utf-8')
                    self.buff.set_text(b)
                    self.x.io['stdout'] = 0
                    if self.engine in 'OpenSSL' and action in 'enc':
                        self.infobar('x_opensslenc_success_textmode', customtext=cipher)
            else:  # Text Fail!
                if action in 'verify':
                    self.infobar('x_verify_failed')
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar('x_missing_recip')
                    return
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar('x_generic_failed_textmode', customtext=action)

    # HELPERS FOR MAIN XFACE FUNCTION

    # CB for GLib.io_add_watch()
    def update_task_status(self, fd, condition, output='task'):
        """Read data waiting in file descriptor; close fd if other end hangs up."""

        # If there's data to be read, let's read it
        if condition == GLib.IOCondition.IN:
            b = read(fd, 1024).decode('utf-8')
            if output in 'task':
                # Output to Task Status
                self.buff2.insert(self.buff2.get_end_iter(), b)
            else:
                # Output to stderr (will show if run from terminal)
                stderr.write(b)
            return True
        # If other end of pipe hangs up, close our fd and destroy the watcher
        elif condition == GLib.IOCondition.HUP:
            if output in 'term':
                stderr.write("\n")
            close(fd)
            return False

    # Called when gpg/openssl begins and ends processing
    def show_working_progress(self, show=True, action=None):
        """Hide/show progress widgets; set/unset working status + activity spinner."""

        # Show/hide progress bar & its buttons
        for w in self.g_progbar, self.g_cancel, self.g_pause:
            w.set_visible(show)

        if show:
            # If beginning processing: set progbar text + working status, start spinner
            self.g_progbar.set_text("{} working...".format(self.engine))
            if action in {'embedsign', 'clearsign', 'detachsign'}:
                status = "Signing input ..."
            elif action in 'verify':
                status = "Verifying input ..."
            else:
                status = "{}rypting input ...".format(action.title())
            self.g_statusbar.push(self.status, status)
            self.g_activityspin.set_visible(True)
            self.g_activityspin.start()
            Gtk.main_iteration()
        else:
            # If finished processing: ensure progbar buttons are normal, reset status, stop spinner
            for w in self.g_cancel, self.g_pause:
                w.set_sensitive(True)
                w.set_relief(Gtk.ReliefStyle.NONE)
            self.g_activityspin.stop()
            self.g_activityspin.set_visible(False)
            self.g_statusbar.pop(self.status)


    def loadmails_string_list(self):
        """Return emails from all known keys."""
        mails = list()
        if self.engine == 'OpenSSL':
            return mails
        cmd = split("gpg --list-public-keys --with-colons")
        keys_string = check_output(cmd).decode('utf-8')
        keys_all = keys_string.split('\n')
        for line in keys_all:
            line_fields = line.split(':')
            if line_fields[0] == 'uid':
                name_email = line_fields[9]
                mails.append(name_email)
        return mails

    # Loading names and emails for the recipient menu completion
    def load_recipients_autocmplete(self):
        mails = Gtk.ListStore(str)
        for mail in self.loadmails_string_list():
            mails.append([mail])
        completion = Gtk.EntryCompletion()
        completion.set_model(mails)
        completion.set_text_column(0)
        completion.set_match_func(self.recipient_contains, None)
        self.g_recip.set_completion(completion)

    def recipient_contains(self, completion, key_string, iter, data):
        model = completion.get_model()
        # get the completion strings
        modelstr = model[iter][0]
        return key_string in modelstr

    # RUN MAIN APPLICATION WINDOW
    def main(self):
        """Show main window, and start GTK+ main loop."""
        self.g_window.show()
        self.g_window.connect("destroy", Gtk.main_quit)
        self.g_window.show_all()
        Gtk.main()
