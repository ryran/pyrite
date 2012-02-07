#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/07
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



# StdLib:
import gtk
import cPickle as pickle
from sys import stderr
from glib import timeout_add_seconds, source_remove
from pango import FontDescription
from os import access, R_OK, getenv
from os.path import isfile
from urllib import url2pathname
from shlex import split
from subprocess import check_output
from threading import Thread
gtk.gdk.threads_init()


# Important variables
version                 = 'v1.0.0_dev9'
assetdir                = ''
userpref_file           = getenv('HOME') + '/.pyrite'
userpref_format_info    = {'version':'Must6fa'}
SIGSTOP, SIGCONT        = 19, 18

    

class Preferences:
    """Preferences system. Fun."""
    
    
    def __init__(self, reset_defaults=False):
        try:
            if reset_defaults:
                raise Exception
            with open(userpref_file, 'rb') as f:
                v = pickle.load(f)
                if v['version'] != userpref_format_info['version']:
                    raise Exception
                self.p = dict(pickle.load(f))
            stderr.write("Pyrite loaded preferences from file {!r}\n".format(userpref_file))
        except:
            stderr.write("Pyrite loaded default preferences\n")
            # Default preferences
            self.p = dict(
                # Main Operation Mode
                opmode=0,
                # Engine
                backend=0,
                # Enc/Dec Mode
                enctype=0,
                advanced=False,
                enctoself=False,
                cipher=1,
                addsig=False,
                # Mode-Independent
                digest=0,
                defkey=False,
                defkeytxt='',
                txtoutput=0,
                expander=False,
                # Sign/Verify Mode
                svoutfiles=False,
                text_sigmode=1,
                file_sigmode=2,
                # Display
                taskstatus=True,
                verbose=False,
                wrap=True,
                opc_slider=False,
                opacity=100,
                msgfntsize=9,
                errfntsize=7,
                color_fg='#000000000000',
                color_bg='#ffffffffffff')
    
    
    def infobar(self, msg=None, config=(1,1), timeout=8):
        """Instantiate a new auto-hiding InfoBar with a Label of msg."""
        
        def destroy_ibar():
            self.ibar_timeout = 0
            self.ibar.destroy()
            self.window.resize(1,1)
        
        if self.ibar_timeout > 0:
            source_remove(self.ibar_timeout)
            destroy_ibar()
        
        msgtype, imgtype = config
        
        if   msgtype == 1:  msgtype = gtk.MESSAGE_INFO
        elif msgtype == 2:  msgtype = gtk.MESSAGE_QUESTION
        elif msgtype == 3:  msgtype = gtk.MESSAGE_WARNING
        elif msgtype == 4:  msgtype = gtk.MESSAGE_ERROR
        
        if   imgtype == 0:  imgtype = gtk.STOCK_APPLY
        elif imgtype == 1:  imgtype = gtk.STOCK_DIALOG_INFO
        elif imgtype == 2:  imgtype = gtk.STOCK_DIALOG_QUESTION
        elif imgtype == 3:  imgtype = gtk.STOCK_DIALOG_WARNING
        elif imgtype == 4:  imgtype = gtk.STOCK_DIALOG_ERROR
        
        self.ibar                   = gtk.InfoBar()
        self.ibar.set_message_type  (msgtype)
        self.vbox_ib.pack_end   (self.ibar, False, False)
        img                     = gtk.Image()
        img.set_from_stock      (imgtype, gtk.ICON_SIZE_LARGE_TOOLBAR)
        label                   = gtk.Label()
        label.set_markup        ("<span foreground='#2E2E2E'>{}</span>".format(msg))
        content                 = self.ibar.get_content_area()
        content.pack_start      (img, False, False)
        content.pack_start      (label, False, False)
        img.show                ()
        label.show              ()
        self.ibar.show          ()
        self.ibar_timeout       = timeout_add_seconds(timeout, destroy_ibar)
    
    
    def open_preferences_window(self, parentwindow):
        self.ibar_timeout = 0
        builder = gtk.Builder()
        builder.add_from_file(assetdir + 'ui/preferences.glade')
        # Main window
        self.window         = builder.get_object('window1')
        self.btn_save       = builder.get_object('btn_save')
        self.btn_apply      = builder.get_object('btn_apply')
        self.vbox_ib        = builder.get_object('vbox_ib')
        # Main Operation Mode
        self.cb_opmode      = builder.get_object('cb_opmode')
        # Engine
        self.cb_backend     = builder.get_object('cb_backend')
        # Enc/Dec Mode
        self.cb_enctype     = builder.get_object('cb_enctype')
        self.tg_advanced    = builder.get_object('tg_advanced')
        self.tg_enctoself   = builder.get_object('tg_enctoself')
        self.cb_cipher      = builder.get_object('cb_cipher')
        self.tg_addsig      = builder.get_object('tg_addsig')
        # Mode-Independent
        self.cb_digest      = builder.get_object('cb_digest')
        self.tg_defkey      = builder.get_object('tg_defkey')
        self.ent_defkey     = builder.get_object('ent_defkey')
        self.cb_txtoutput   = builder.get_object('cb_txtoutput')
        self.tg_expander    = builder.get_object('tg_expander')
        # Sign/Verify Mode
        self.tg_svoutfiles  = builder.get_object('tg_svoutfiles')
        self.cb_text_sigmode= builder.get_object('cb_text_sigmode')
        self.cb_file_sigmode= builder.get_object('cb_file_sigmode')
        # Display
        self.tg_taskstatus  = builder.get_object('tg_taskstatus')
        self.tg_verbose     = builder.get_object('tg_verbose')
        self.tg_wrap        = builder.get_object('tg_wrap')
        self.tg_opc_slider  = builder.get_object('tg_opc_slider')
        self.sp_opacity     = builder.get_object('sp_opacity')
        self.sp_msgfntsize  = builder.get_object('sp_msgfntsize')
        self.sp_errfntsize  = builder.get_object('sp_errfntsize')
        self.btn_color_fg   = builder.get_object('btn_color_fg')
        self.btn_color_bg   = builder.get_object('btn_color_bg')
        # TODO: Advanced
        #self.tg_args_gpg_e  = builder.get_object('tg_args_gpg_e')
        #self.en_args_gpg_e  = builder.get_object('en_args_gpg_e')
        self.window.set_transient_for(parentwindow)
        if access(userpref_file, R_OK):
            btn_revert = builder.get_object('btn_revert')
            btn_revert.set_sensitive(True)
        self.populate_pref_window_prefs()
        builder.connect_signals(self)
        self.window.show()
    
    
    def populate_pref_window_prefs(self):
        # Main Operation Mode
        self.cb_opmode.set_active       (self.p['opmode'])
        # Engine
        self.cb_backend.set_active      (self.p['backend'])
        # Enc/Dec Mode
        self.cb_enctype.set_active      (self.p['enctype'])
        self.tg_advanced.set_active     (self.p['advanced'])
        self.tg_enctoself.set_active    (self.p['enctoself'])
        self.cb_cipher.set_active       (self.p['cipher'])
        self.tg_addsig.set_active       (self.p['addsig'])
        # Mode-Independent
        self.cb_digest.set_active       (self.p['digest'])
        self.tg_defkey.set_active       (self.p['defkey'])
        self.ent_defkey.set_text        (self.p['defkeytxt'])
        self.cb_txtoutput.set_active    (self.p['txtoutput'])
        self.tg_expander.set_active     (self.p['expander'])
        # Sign/Verify Mode
        self.tg_svoutfiles.set_active   (self.p['svoutfiles'])
        self.cb_text_sigmode.set_active (self.p['text_sigmode'])
        self.cb_file_sigmode.set_active (self.p['file_sigmode'])
        # Display
        self.tg_taskstatus.set_active   (self.p['taskstatus'])
        self.tg_verbose.set_active      (self.p['verbose'])
        self.tg_wrap.set_active         (self.p['wrap'])
        self.tg_opc_slider.set_active   (self.p['opc_slider'])
        self.sp_opacity.set_value       (self.p['opacity'])
        self.sp_msgfntsize.set_value    (self.p['msgfntsize'])
        self.sp_errfntsize.set_value    (self.p['errfntsize'])
        self.btn_color_fg.set_color     (gtk.gdk.color_parse(self.p['color_fg']))
        self.btn_color_bg.set_color     (gtk.gdk.color_parse(self.p['color_bg']))
    
    
    def capture_current_prefs(self):
        self.p = {
        # Main Operation Mode
        'opmode'      : self.cb_opmode.get_active(),
        # Engine
        'backend'     : self.cb_backend.get_active(),
        # Enc/Dec Mode
        'enctype'     : self.cb_enctype.get_active(),
        'advanced'    : self.tg_advanced.get_active(),
        'enctoself'   : self.tg_enctoself.get_active(),
        'cipher'      : self.cb_cipher.get_active(),
        'addsig'      : self.tg_addsig.get_active(),
        # Mode-Independent
        'digest'      : self.cb_digest.get_active(),
        'defkey'      : self.tg_defkey.get_active(),
        'defkeytxt'   : self.ent_defkey.get_text(),
        'txtoutput'   : self.cb_txtoutput.get_active(),
        'expander'    : self.tg_expander.get_active(),
        # Sign/Verify Mode
        'svoutfiles'  : self.tg_svoutfiles.get_active(),
        'text_sigmode': self.cb_text_sigmode.get_active(),
        'file_sigmode': self.cb_file_sigmode.get_active(),
        # Display
        'taskstatus'  : self.tg_taskstatus.get_active(),
        'verbose'     : self.tg_verbose.get_active(),
        'wrap'        : self.tg_wrap.get_active(),
        'opc_slider'  : self.tg_opc_slider.get_active(),
        'opacity'     : self.sp_opacity.get_value(),
        'msgfntsize'  : self.sp_msgfntsize.get_value(),
        'errfntsize'  : self.sp_errfntsize.get_value(),
        'color_fg'    : self.btn_color_fg.get_color().to_string(),
        'color_bg'    : self.btn_color_bg.get_color().to_string()}
        return self.p
    
    
    def save_prefs(self):
        try:
            with open(userpref_file, 'wb') as f:
                pickle.dump(userpref_format_info, f, protocol=2)
                pickle.dump(self.capture_current_prefs(), f, protocol=2)
                stderr.write("Pyrite saved preferences to file {!r}\n".format(userpref_file))
        except:
            self.infobar("<b>Saving preferences failed.</b>\nUnable to open config file "
                         "<i><tt><small>{} </small></tt></i> for writing."
                         .format(userpref_file), (4,3), 20)
            return False
        return True
    
    
    def action_cancel_prefs(self, widget, data=None):
        self.window.destroy()
    
    
    def action_revert_prefs(self, widget, data=None):
        self.__init__()
        self.populate_pref_window_prefs()
        self.infobar("<b>Reverted to user-saved preferences.</b>", (1,0), 3)
    
    
    def action_default_prefs(self, widget, data=None):
        self.__init__(reset_defaults=True)
        self.populate_pref_window_prefs()
        self.infobar("<b>Preferences reset to defaults. You still need to <i>Save</i> or "
                     "<i>Apply</i>.</b>", (1,0), 3)
    
    
    def action_tg_enctoself(self, widget, data=None):
        if self.tg_enctoself.get_active():
            self.infobar("<b>If you want <i>Encrypt to Self</i> on in Symmetric mode, "
                         "you must set\n<i>Encryption Type</i> to 'Both'.</b>")
    
    
    def action_tg_addsig(self, widget, data=None):
        if self.tg_addsig.get_active():
            self.infobar("<b>If you want <i>Add Signature</i> on in Symmetric mode, "
                         "you must also enable\n<i>Advanced</i></b>.")
    
    
    def action_cb_enctype(self, widget, data=None):
        if self.cb_enctype.get_active() == 2:
            self.infobar("<b>In order for both encryption types to be on by default, "
                         "<i>Advanced</i> will also be\nturned on, whether or not you "
                         "select it now.</b>")




class Pyrite:
    """Display GTK window to interact with gpg via GpgXface object.
    
    For now, we build the gui from a Glade-generated gtk builder xml file.
    Once things are more finalized, we'll add the pygtk calls in here.
    """
    
    
    def show_errmsg(self, msg, dialog=gtk.MESSAGE_ERROR, parent=None):
        """Display msg with GtkMessageDialog."""
        d = gtk.MessageDialog(parent,
                              gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                              dialog, gtk.BUTTONS_OK, msg)
        d.run()
        d.destroy()
    
    
    def __init__(self):
        """Build GUI interface from XML, etc."""        
        
        # Use GtkBuilder to build our GUI from the XML file 
        builder = gtk.Builder()
        try: builder.add_from_file(assetdir + 'ui/main.glade') 
        except:
            self.show_errmsg(
                "Problem loading GtkBuilder UI definition! Cannot continue.\n\n"
                "Possible causes:\n\n1) You haven't downloaded the whole Pyrite "
                "package (pyrite.py needs the .glade files in the ui subdirectory).\n\n"
                "2) You didn't use the INSTALL script to install Pyrite. This is OK as "
                "long as you execute 'pyrite' from the pyrite directory."
                "\n\n3) You moved the "
                "pyrite dir after installing it.\n\nIn all cases, this could be solved "
                "by simply downloading the package again from github.com/ryran/pyrite "
                "and running INSTALL, following the directions.\n\nHowever, if you just "
                "want to try out Pyrite and you're sure you downloaded the whole "
                "package, you can avoid this error (as #2 says) by making sure you're "
                "in the pyrite directory when you execute ie, i.e.,\n"
                "'cd pyrite ; ./pyrite'")
            raise
        
        #--------------------------------------------------------- GET WIDGETS!
        
        # Main window
        self.g_window       = builder.get_object('window1')
        # Toolbars
        self.g_maintoolbar  = builder.get_object('hbox1')
        self.g_modetoolbar  = builder.get_object('hbox2')
        self.g_enctoolbar   = builder.get_object('hbox3')
        self.g_sigtoolbar   = builder.get_object('hbox4')
        # Menu items
        self.g_mclear       = builder.get_object('mnu_clear')
        self.g_mopen        = builder.get_object('mnu_open')
        self.g_msave        = builder.get_object('mnu_save')
        self.g_mcut         = builder.get_object('mnu_cut')
        self.g_mcopy        = builder.get_object('mnu_copy')
        self.g_mpaste       = builder.get_object('mnu_paste')
        self.g_mengine      = builder.get_object('mnu_switchengine')
        self.g_wrap         = builder.get_object('toggle_wordwrap')
        self.g_taskstatus   = builder.get_object('toggle_taskstatus')
        self.g_taskverbose  = builder.get_object('toggle_gpgverbose')
        # Top action toolbar
        self.g_encrypt      = builder.get_object('btn_encrypt')
        self.g_decrypt      = builder.get_object('btn_decrypt')
        self.g_bclear       = builder.get_object('btn_clear')
        self.g_progbar      = builder.get_object('progressbar')
        self.g_cancel       = builder.get_object('btn_cancel')
        self.g_pause        = builder.get_object('btn_pause')
        self.g_slider       = builder.get_object('opacity_slider')
        # Mode-setting toolbar
        self.g_signverify   = builder.get_object('toggle_mode_signverify')
        self.g_chk_outfile  = builder.get_object('toggle_sign_chooseoutput')
        self.g_encdec       = builder.get_object('toggle_mode_encdec')
        self.g_symmetric    = builder.get_object('toggle_mode_symmetric')
        self.g_asymmetric   = builder.get_object('toggle_mode_asymmetric')
        self.g_advanced     = builder.get_object('toggle_advanced')
        # Encryption toolbar
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
        self.vbox_ibar      = builder.get_object('vbox_ibar')
        self.vbox_ibar2     = builder.get_object('vbox_ibar2')
        self.g_expander     = builder.get_object('expander_filemode')
        self.g_chooserbtn   = builder.get_object('btn_filechooser')
        self.g_plaintext    = builder.get_object('toggle_plaintext')
        self.g_frame2       = builder.get_object('frame2')
        self.g_errtxtview   = builder.get_object('textview2')
        self.buff2          = self.g_errtxtview.get_buffer()
        # Signing toolbar
        self.g_signature    = builder.get_object('toggle_signature')
        self.g_sigmode      = builder.get_object('combobox_sigmode')
        self.g_digestlabel  = builder.get_object('label_combobox_digest')
        self.g_digest       = builder.get_object('combobox_digest')
        self.g_chk_defkey   = builder.get_object('toggle_defaultkey')
        self.g_defaultkey   = builder.get_object('entry_defaultkey')
        # Statusbar
        self.g_statusbar    = builder.get_object('statusbar')
        self.g_activityspin = builder.get_object('spinner1')
        
        # Set app icon to something halfway-decent
        gtk.window_set_default_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        
        # Connect signals
        builder.connect_signals(self)
        
        # Other class attributes
        self.ib_filemode    = None
        self.engine         = 'missing_backend'
        
        # Initialize main Statusbar
        self.status = self.g_statusbar.get_context_id('main')
        self.g_statusbar.push(self.status, "Enter message to encrypt/decrypt")
        
        # Sensitivity for these GtkEntrys not defaulted to False in xml because
        #   that makes their icons stay insensitive-looking forever
        self.g_pass.set_sensitive           (False)
        self.g_recip.set_sensitive          (False)

        #------------------------------ LOAD PREFERENCES AND SET WIDGET STATES!
        
        self.pref = Preferences()
        
        # Make a clone of preferences dictionary
        self.p = self.pref.p
        
        # Launch gpg/openssl interface
        self.instantiate_xface(startup=True)
        
        #------------------------------------------------ DRAG AND DROP FUNNESS
        
        TARGET_TYPE_URI_LIST = 80
        dnd_list = [ ( 'text/uri-list', 0, TARGET_TYPE_URI_LIST ) ]
        
        self.g_msgtxtview.drag_dest_set(
            gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT,
            dnd_list, gtk.gdk.ACTION_COPY)
        self.g_chooserbtn.drag_dest_set(
            gtk.DEST_DEFAULT_ALL,
            dnd_list, gtk.gdk.ACTION_COPY)
    
     
    def infobar(self, message=None, config=(1,1), timeout=5, vbox=None):
        """Instantiate a new auto-hiding InfoBar with a Label of message."""
        
        msgtype, imgtype = config
        
        if   msgtype == 1:  msgtype = gtk.MESSAGE_INFO
        elif msgtype == 2:  msgtype = gtk.MESSAGE_QUESTION
        elif msgtype == 3:  msgtype = gtk.MESSAGE_WARNING
        elif msgtype == 4:  msgtype = gtk.MESSAGE_ERROR
        
        if   imgtype == 0:  imgtype = gtk.STOCK_APPLY
        elif imgtype == 1:  imgtype = gtk.STOCK_DIALOG_INFO
        elif imgtype == 2:  imgtype = gtk.STOCK_DIALOG_QUESTION
        elif imgtype == 3:  imgtype = gtk.STOCK_DIALOG_WARNING
        elif imgtype == 4:  imgtype = gtk.STOCK_DIALOG_ERROR
            
        ibar                    = gtk.InfoBar()
        ibar.set_message_type   (msgtype)
        if vbox:
            ibar.add_button     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            ibar.connect        ('response', self.cleanup_filemode)
        else:
            vbox = self.vbox_ibar
            ibar.add_button     (gtk.STOCK_OK, gtk.RESPONSE_OK)
            ibar.connect        ('response', lambda *args: ibar.destroy())
        vbox.pack_end           (ibar, False, False)
        content                 = ibar.get_content_area()
        img                     = gtk.Image()
        img.set_from_stock      (imgtype, gtk.ICON_SIZE_LARGE_TOOLBAR)
        content.pack_start      (img, False, False)
        img.show                ()
        if message:
            message = "<span foreground='#2E2E2E'>" + message + "</span>"
            label               = gtk.Label()
            label.set_markup    (message)
            content.pack_start  (label, False, False)
            label.show          ()
        # FIXME: Why doesn't Esc trigger this close signal?
        ibar.connect            ('close', lambda *args: ibar.destroy())
        ibar.show()
        if timeout:
            timeout_add_seconds(timeout, ibar.destroy)
        return ibar
    
    
    #----------------------------------------------------- BRING UP GPG/OPENSSL
    
    def instantiate_xface(self, xface=None, startup=False):
        """Instantiate Gpg or Openssl interface."""        
        
        self.set_defaults_from_prefs(startup)
        
        # These are all the widgets that can't be used in openssl mode
        def setsensitive_gpgwidgets(x=True):
            self.g_signverify.set_sensitive (x)
            self.g_symmetric.set_sensitive  (x)
            self.g_asymmetric.set_sensitive (x)
            self.g_advanced.set_sensitive   (x)
            self.g_taskverbose.set_visible  (x)
        
        
        b = ['gpg2', 'gpg', 'openssl']
        # self.p['backend'] contains 0, 1, or 2, corresponding to the above items in b
        # Desired: convert the number to the value and store in b
        b = b[any(n for n in xrange(3) if self.p['backend'] == n)]
        
        # If we weren't passed xface argument, set desired interface to backend preference
        if not xface:  xface = b
        
        # Loading gpg
        def gpg(backend_pref=b, fallback=False):
            import xgpg
            self.x = xgpg.Xface(firstchoice=backend_pref)
            self.engine = self.x.GPG.upper()
            self.g_mengine.set_label        ("Use OpenSSL as Engine")
            if fallback:
                self.g_mengine.set_sensitive(False)
                self.infobar("<b>Shockingly, your system does not appear to have "
                             "OpenSSL.</b>", (1,3))
            setsensitive_gpgwidgets         (True)
        
        # Loading openssl
        def openssl(fallback=False):
            import xopenssl
            self.x = xopenssl.Xface()
            self.engine = 'OpenSSL'
            self.g_mengine.set_label("Use GnuPG as Engine")
            if fallback:
                self.g_mengine.set_sensitive(False)
                self.infobar("<b>GnuPG not found. Operating in OpenSSL fallback-mode.</b>\n"
                             "<small>To make full use of this program you need either "
                             "<tt>gpg</tt> or <tt>gpg2</tt> installed.\nWithout one of them, "
                             "you won't have access key-based functions like\nasymmetric "
                             "encryption or singing.</small>", (1,3), 20)
            else:
                self.infobar("<b>OpenSSL only supports symmetric {en,de}cryption.</b>\n<small>"
                             "All key-based functions are disabled.</small>", (1,1), 7) 
            self.g_encdec.set_active        (True)
            self.g_symmetric.set_active     (True)
            self.g_advanced.set_active      (False)
            setsensitive_gpgwidgets         (False)
            if startup or self.g_cipher.get_active() in {0, 2}:
                # If starting up, or current cipher set to 'Default' or 'Twofish'
                if self.p['cipher'] not in {0, 2}:
                    # Set cipher to preference unless pref is 'Default' or 'Twofish'
                    self.g_cipher.set_active        (self.p['cipher'])   
                else:
                    # Otherwise, set to AES
                    self.g_cipher.set_active        (1)
        
        # Setup for neutered-run (when missing all backends)
        def err_allmissing():
            self.infobar("<b>This program requires one of: <tt>gpg</tt>, <tt>gpg2</tt>, or <tt>openssl</tt></b>\n"
                         "<small>None of these were found on your system. You can look around\n"
                         "the interface, but to have real fun you'll need to install <tt>gpg</tt> or <tt>gpg2</tt>\n"
                         "from your linux distribution's software repository.</small>", (4,3), 0)
            self.g_mengine.set_sensitive(False)
            for w in self.g_encrypt, self.g_decrypt:  w.set_sensitive(False)
            class dummy:  pass
            self.x = dummy()
            self.x.io = dict(stdin='', stdout='', stderr='', infile=0, outfile=0)

        
        # Get it done!
        if xface in 'openssl':
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
                            "displayed here.\n\nIn the View menu you can change "
                            "the verbosity level, hide this pane, or simply change "
                            "the font size.".format(self.engine.lower()))
    
    
    #--------------------------------------------- SET OPMODES, ETC, FROM PREFS
    
    def set_defaults_from_prefs(self, startup=False):
        """Set window toggle states via preferences."""

        if self.p['opmode']:
            self.g_signverify.set_active    (True)
        
        if self.p['advanced']:
            self.g_advanced.set_active      (True)
        
        if self.p['addsig']:
            self.g_signature.set_active     (True)
        
        if self.p['enctoself']:
            self.g_enctoself.set_active     (True)
        
        if self.p['enctype'] == 0:
            self.g_symmetric.set_active     (True)
        elif self.p['enctype'] == 1:
            self.g_asymmetric.set_active    (True)
        elif self.p['enctype'] == 2:
            self.g_advanced.set_active      (True)
            self.g_symmetric.set_active     (True)
            self.g_asymmetric.set_active    (True)
            
        if not self.g_expander.get_expanded():
            self.g_expander.set_expanded    (self.p['expander'])
        
        self.g_digest.set_active            (self.p['digest'])
        self.g_chk_defkey.set_active        (self.p['defkey'])
        self.g_defaultkey.set_text          (self.p['defkeytxt'])
        self.g_cipher.set_active            (self.p['cipher'])
        
        if startup:
            self.g_taskstatus.set_active        (self.p['taskstatus'])
            self.g_taskverbose.set_active       (self.p['verbose'])
            self.g_wrap.set_active              (self.p['wrap'])
            
            # Set TextView fonts, sizes, and colors
            self.g_msgtxtview.modify_font(
                FontDescription("monospace {}".format(self.p['msgfntsize'])))
            self.g_errtxtview.modify_font(
                FontDescription("normal {}".format(self.p['errfntsize'])))
            self.g_msgtxtview.modify_base(
                gtk.STATE_NORMAL, gtk.gdk.color_parse(self.p['color_bg']))
            self.g_msgtxtview.modify_text(
                gtk.STATE_NORMAL, gtk.gdk.color_parse(self.p['color_fg']))
            
            if self.p['opc_slider']:
                self.g_slider.set_range         (0, 100)
                self.g_slider.set_value         (self.p['opacity'])
                self.g_slider.set_tooltip_text  ("Change window opacity (current:{}%)".format(self.p['opacity']))
                self.g_slider.set_visible       (True)
            else:
                self.g_window.set_opacity(self.p['opacity']/100.0)
    
    
    #--------------------------------------------------------- HELPER FUNCTIONS
    
    
    def fix_msgtxtviewcolor(self, sensitive):
        if sensitive:
            self.g_msgtxtview.modify_text(
                gtk.STATE_NORMAL, gtk.gdk.color_parse(self.p['color_fg']))
        else:
            self.g_msgtxtview.modify_text(
                gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
    
    
    def get_file_path_from_dnd_dropped_uri(self, uri):
        path = ''
        if uri.startswith('file:\\\\\\'): # windows
            path = uri[8:] # 8 is len('file:///')
        elif uri.startswith('file://'): # nautilus, rox
            path = uri[7:] # 7 is len('file://')
        elif uri.startswith('file:'): # xffm
            path = uri[5:] # 5 is len('file:')
        path = url2pathname(path) # escape special chars
        path = path.strip('\r\n\x00') # remove \r\n and NULL
        return path
    
    
    def set_stdstatus(self):
        """Set a standard mode-depenedent status message."""
        self.g_statusbar.pop(self.status)
        if self.g_signverify.get_active():
            s = "Enter message to sign or verify"
        else:
            s = "Enter message to encrypt or decrypt"
        self.g_statusbar.push(self.status, s)
    
    
    def test_file_isbinary(self, filename):
        """Utilize nix file cmd to determine if filename is binary or text."""
        cmd = split("file -b -e soft '{}'".format(filename))
        if check_output(cmd)[:4] in {'ASCI', 'UTF-'}:
            return False
        return True
    
    
    # This is called when entering & exiting direct-file mode.
    def filemode_enablewidgets(self, x=True):
        """Enable/disable certain widgets due to working in direct-file mode."""
        widgets = [self.g_mengine, self.g_bcopyall, self.g_bopen, self.g_mopen,
                   self.g_bsave, self.g_msave, self.g_mcut, self.g_mcopy,
                   self.g_mpaste, self.g_msgtxtview]
        for w in widgets:
            w.set_sensitive(x)
        self.fix_msgtxtviewcolor(x)
    
    
    # This is called when user tries to copyall or save or en/decrypt or sign/verify
    def test_msgbuff_isempty(self, msg):
        if self.buff.get_char_count() < 1:
            self.infobar("<b>{}</b>".format(msg), (1,3), 2)
            return True
    
    
    def confirm_overwrite_callback(self, chooser):
        outfile = chooser.get_filename()
        if self.x.io['infile'] == outfile:
            self.show_errmsg("Simultaneously reading from & writing to a file is a "
                             "baaad idea. Choose a different output filename.",
                             parent=chooser)
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
        """Use FileChooser to get an output filename for direct enc/dec."""
        outfile = self.chooser_grab_filename('save', self.x.io['infile'])
        if outfile:
            self.x.io['outfile'] = outfile
            self.launchxface(mode)
    
    
    def initiate_filemode(self):
        """Ensure read access of file set by chooserwidget and notify user of next steps."""
        infile = self.g_chooserbtn.get_filename()
        if not access(infile, R_OK):
            self.infobar("<b>Error. Could not open file:\n<i><tt><small>{}</small></tt></i></b>\n"
                         "<small>Choose a new file.</small>".format(infile), (3,4))
            return
        if self.g_signverify.get_active():
            self.g_chk_outfile.set_visible  (True)
            self.g_chk_outfile.set_active   (self.p['svoutfiles'])
            self.g_sigmode.set_active       (self.p['file_sigmode'])
        
        self.g_plaintext.set_sensitive  (True)
        if self.p['txtoutput'] == 0:  # Autodetect
            if self.test_file_isbinary(infile):  self.g_plaintext.set_active (False)
            else:                                self.g_plaintext.set_active (True)
        elif self.p['txtoutput'] == 1:  # Always Binary
            self.g_plaintext.set_active     (False)
        elif self.p['txtoutput'] == 2:  # Always Text
            self.g_plaintext.set_active     (True)

        self.g_statusbar.pop(self.status)
        self.g_statusbar.push(self.status, "Choose an action to perform on {!r}".format(infile))
        
        if self.ib_filemode:
            # If already in filemode, but user just picked a new file, destroy filemode banner
            self.ib_filemode.destroy()
        else:
            # Otherwise, save TextView buffer for later and then blow it away
            self.filemode_saved_buff = self.buff.get_text(self.buff.get_start_iter(),
                                                          self.buff.get_end_iter())
            self.buff.set_text('')
            self.filemode_enablewidgets(False)
            
        self.ib_filemode = self.infobar(
            "<b><i>Encrypt</i>, <i>Decrypt</i>, <i>Sign</i>, or <i>Verify</i>?</b>\n"
            "<small>Ready to operate on file:\n"
            "<i><tt>{}</tt></i>\n"
            "You will be prompted for an output filename if necessary.</small>"
            .format(infile), (2,2), 0, self.vbox_ibar2)
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
        self.filemode_enablewidgets         (True)
        self.g_chk_outfile.set_visible      (False)
        if self.g_signverify.get_active():
            self.g_sigmode.set_active       (1)
        else:
            self.g_sigmode.set_active       (0)
        self.set_stdstatus()
        #while gtk.events_pending():
        gtk.main_iteration()
        # Reset filenames
        self.x.io['infile'] = 0
        self.x.io['outfile'] = 0
        # Disable plaintext CheckButton
        self.g_plaintext.set_sensitive      (False)
        self.g_plaintext.set_active         (True)
            
    
    #------------------------------------------- HERE BE GTK SIGNAL DEFINITIONS
    
    def on_window1_destroy  (self, widget):
        gtk.main_quit()
    def action_quit         (self, widget):
        gtk.main_quit()
    
    
    def action_drag_data_received(self, widget, context, x, y, selection, target_type, timestamp):
        if target_type == 80:
            uri = selection.data.strip('\r\n\x00')
            uri = uri.split()[0]
            path = self.get_file_path_from_dnd_dropped_uri(uri)
            if isfile(path):
                if widget.get_name() in 'GtkTextView':
                    self.open_in_txtview(path)
                elif widget.get_name() in 'GtkFileChooserButton':
                    print "\n[on_drag_data_received]\narg passed to FileChooserButton.set_filename() is:\n'{}'".format(path)
                    print "\nFileChooserButton.set_filename() return value: ", widget.set_filename(path)
                    print "\nFileChooserButton.get_filename() returns:\n'{}'\n".format(widget.get_filename())
                    self.initiate_filemode()
    
    
    def action_opacity_slider(self, widget):
        """Actions to perform when opacity scale is changed."""
        val = widget.get_value()
        self.g_window.set_opacity(val/100.0)
        widget.set_tooltip_text(
            "Change window opacity (current:{:.1f}%)".format(val))
    
    
    def action_switch_engine(self, widget, data=None):
        if self.engine in 'OpenSSL':
            self.instantiate_xface('gpg')
        else:
            self.instantiate_xface('openssl')
    
    
    def action_about(self, widget, data=None):
        """Launch About dialog."""
        builder = gtk.Builder()
        builder.add_from_file(assetdir + 'ui/about.glade') 
        about = builder.get_object('aboutdialog')
        about.set_logo_icon_name(gtk.STOCK_DIALOG_AUTHENTICATION)
        about.set_transient_for(self.g_window)
        about.set_version(version)
        about.connect('response', lambda *args: about.destroy())
        about.show()
    
    
    def action_preferences(self, widget, data=None):
        """Launch our preferences window."""
        self.pref.open_preferences_window(parentwindow=self.g_window)
        def savepref(*args):
            if self.pref.save_prefs():
                self.pref.window.destroy()
                self.infobar("<b>Saved preferences to <i><tt><small>{}</small></tt></i>\n"
                             "but no changes made to current session.</b>".format(userpref_file), (1,0))
        def applypref(*args):
            if self.pref.save_prefs():
                self.pref.window.destroy()
                self.p = self.pref.p
                if self.x.io['infile']:  self.cleanup_filemode()
                self.instantiate_xface(startup=True)
                self.infobar("<b>Saved preferences to <i><tt><small>{}</small></tt></i>\n"
                             "and applied them to current session.</b>".format(userpref_file), (1,0))
        self.pref.btn_save.connect  ('clicked', savepref)
        self.pref.btn_apply.connect ('clicked', applypref)
        
    
    def action_clear(self, widget, data=None):
        """Reset Statusbar, filemode stuff, TextView buffers."""
        if self.x.io['infile']:
            self.cleanup_filemode()
        else:
            self.set_stdstatus()
        self.buff.set_text                  ('')
        self.buff2.set_text                 ('')
        self.x.io = dict(stdin='', stdout='', stderr='', infile=0, outfile=0)
    
    
    def action_clear_entry(self, widget, data=None, whatisthis=None):
        """Clear Entry widget."""
        widget.set_text('')
    
    
    def action_open(self, widget, data=None):
        """Read in a file and push its contents to our TextView."""
        filename = self.chooser_grab_filename('open')
        if filename:
            self.open_in_txtview(filename)
    
    
    def open_in_txtview(self, filename):
        """Replace contents of msg TextView's TextBuffer with contents of file."""
        try:
            with open(filename) as f:  self.buff.set_text(f.read())
            if self.buff.get_char_count() < 1:
                self.infobar("<b>To operate on binary files, use the\n<i>Input File For "
                             "Direct Operation </i> chooser button.</b>", 
                             (1,3), 8)
        except:
            self.infobar("<b>Error. Could not open file:\n<i><tt><small>{}</small></tt></i></b>"
                         .format(filename), (3,4))
    
    
    def action_filemode_chooser_set(self, widget, data=None):
        self.initiate_filemode()
    
    
    def action_save(self, widget, data=None):
        """Save contents of msg TextView's TextBuffer to file."""
        if self.test_msgbuff_isempty("No text to save."): return
        filename = self.chooser_grab_filename('save')
        if not filename: return
        self.g_statusbar.push(self.status, "Saving {}".format(filename))
        #while gtk.events_pending(): 
        gtk.main_iteration()
        buffertext = self.buff.get_text(self.buff.get_start_iter(),
                                        self.buff.get_end_iter())
        try:
            with open(filename, 'w') as f:  f.write(buffertext)
            self.infobar("<b>Saved contents of Message area to file:\n"
                         "<i><tt><small>{}</small></tt></i></b>".format(filename), (1,0))
        except:
            self.infobar("<b>Error. Could not save to file:\n<i><tt><small>{}</small></tt></i></b>"
                         .format(filename), (3,4))
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
        if self.test_msgbuff_isempty("No text to copy."): return
        self.buff.select_range(self.buff.get_start_iter(),
                               self.buff.get_end_iter())
        self.buff.copy_clipboard(gtk.clipboard_get())
        self.infobar("<b>Copied contents of Message area to clipboard.</b>", (1,0), 3)
    
    
    def action_zoom(self, widget, data=None):
        """Increase/decrease font size of TextViews."""
        zoom = widget.get_label()[:7]
        if zoom in 'Increase':
            self.p['msgfntsize'] += 1
            self.p['errfntsize'] += 1
        elif zoom in 'Decrease':
            self.p['msgfntsize'] -= 1
            self.p['errfntsize'] -= 1
        self.g_msgtxtview.modify_font(
            FontDescription("monospace {}".format(self.p['msgfntsize'])))
        self.g_errtxtview.modify_font(
            FontDescription("normal {}".format(self.p['errfntsize'])))
    
    
    def action_cipher_changed(self, widget=None, data=None):
        """Disallow certain cipher selections in OpenSSL mode."""
        if self.engine in 'OpenSSL':
            cipher = self.grab_activetext_combobox(self.g_cipher)
            if not cipher:
                self.g_cipher.set_active(1)
                self.infobar("<b>OpenSSL has no default cipher.</b>\n<small>AES256 is "
                             "a good choice.</small>", (1,1), 7)
            elif cipher in 'Twofish':
                self.g_cipher.set_active(1)
                self.infobar("<b>OpenSSL has no support for the Twofish cipher.</b>", (1,1))
            elif cipher in 'AES':
                self.infobar("<b>Note for the command-line geeks:</b>\n<small><i>AES</i> translates "
                             "to OpenSSL's <i>aes-128-cbc</i>.</small>", (1,1))
    
    
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
        asymm_widgets = [self.g_reciplabel, self.g_recip, self.g_enctoself]
        # If entering toggled state
        if self.g_asymmetric.get_active():
            for w in asymm_widgets:
                w.set_sensitive                 (True)
            self.g_signature.set_sensitive      (True)
            # If not in advanced mode, disable Symm
            if not self.g_advanced.get_active():
                self.g_symmetric.set_active     (False)
        # If leaving toggled state
        else:
            for w in asymm_widgets:
                w.set_sensitive                 (False)
            self.g_enctoself.set_active         (False)
            # If not in advanced mode, unset signature
            if not self.g_advanced.get_active():
                self.g_signature.set_sensitive  (False)
                self.g_signature.set_active     (False)
            # If trying to turn off Asymm & Symm isn't already on, turn it on
            if not self.g_symmetric.get_active():
                self.g_symmetric.set_active     (True)
    
    
    # 'Advanced' checkbox toggle
    def action_toggle_advanced(self, widget, data=None):
        """Enable/disable encryption widgets for advanced mode."""
        # If entering the toggled state
        if self.g_advanced.get_active():
            self.g_signature.set_sensitive          (True)
        # If Leaving the toggled state
        else:
            if self.g_symmetric.get_active():
                if self.g_asymmetric.get_active():
                    self.g_asymmetric.set_active    (False)
                else:
                    self.g_signature.set_sensitive  (False)
                    self.g_signature.set_active     (False)
    
    
    # 'Sign/Verify' radio toggle
    def action_toggle_mode_signverify(self, widget, data=None):
        """Hide/show, change some widgets when switching modes."""
        self.set_stdstatus()
        enc_widgets = [self.g_symmetric, self.g_asymmetric, self.g_advanced, self.g_enctoolbar]
        # If entering the toggled state ...
        if self.g_signverify.get_active():
            # Modify our button labels
            self.g_encrypt.set_label        ("Sign")
            self.g_decrypt.set_label        ("Verify")
            # Hide encryption toolbar & Symmetric, Asymmetric, Adv toggles
            for w in enc_widgets:
                w.set_visible               (False)
            # Save state of AddSignature for switching back to Enc/Dec mode
            self.encdec_sig_state_sensitive = self.g_signature.get_sensitive()
            self.encdec_sig_state_active    = self.g_signature.get_active()
            # Desensitize AddSignature checkbox and turn it on
            self.g_signature.set_sensitive  (False)
            self.g_signature.set_active     (True)
            # Sensitize sigmode combobox & change active to Clearsign
            self.g_sigmode.set_sensitive    (True)
            if self.x.io['infile']:
                self.g_sigmode.set_active       (self.p['file_sigmode'])
                self.g_chk_outfile.set_visible  (True)
            else:
                self.g_sigmode.set_active       (self.p['text_sigmode'])
        # If leaving the toggled state, we have some things to reverse
        else:
            self.g_encrypt.set_label        ("_Encrypt")
            self.g_decrypt.set_label        ("_Decrypt")
            self.g_chk_outfile.set_visible  (False)
            for w in enc_widgets:
                w.set_visible               (True)
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
        sig_widgets = [self.g_sigmode, self.g_digest, self.g_digestlabel, self.g_chk_defkey]
        # Entering toggled state
        if self.g_signature.get_active():
            for w in sig_widgets:  w.set_visible(True)
        # Leaving toggled state
        else:
            for w in sig_widgets:  w.set_visible(False)
            self.g_chk_defkey.set_active        (False)
    
    
    def action_toggle_taskstatus(self, widget, data=None):
        """Show/hide side pane containing gpg stderr output."""
        if self.g_taskstatus.get_active():
            self.g_frame2.set_visible   (True)
        else:
            self.g_frame2.set_visible   (False)
    
    
    def action_toggle_wordwrap(self, widget, data=None):
        """Toggle word wrapping for main message TextView."""
        if self.g_wrap.get_active():
            self.g_msgtxtview.set_wrap_mode(gtk.WRAP_WORD)
        else:
            self.g_msgtxtview.set_wrap_mode(gtk.WRAP_NONE)
    
    
    #-------------------------------------------------------- MAIN GPG FUNCTION
    def launchxface(self, action):
        """Manage I/O between Gtk objects and our GpgXface or OpensslXface object."""
        self.canceled       = False
        self.paused         = False
        self.x.childprocess = None
        
        ### PREPARE Xface ARGS
        passwd      = None
        recip       = None
        localuser   = None
        # symmetric & passwd
        symmetric = self.g_symmetric.get_active()
        if symmetric:
            passwd = self.g_pass.get_text()
            if not passwd:
                if self.engine in 'OpenSSL':
                    self.infobar("<b>Passphrase?</b>", (1,2), 3)
                    return
                passwd = None  # If passwd was '' , set to None, which will trigger gpg-agent if necessary
        
        # INTERLUDE: If operating in textinput mode, check for input text
        if not self.x.io['infile']:
            # Make sure textview has a proper message in it
            if self.test_msgbuff_isempty("Input your message text first."):
                return False
            # Make TextView immutable to changes
            self.g_msgtxtview.set_sensitive(False)
            self.fix_msgtxtviewcolor(False)
            
        # enctoself
        enctoself = self.g_enctoself.get_active()
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
        digest = self.grab_activetext_combobox(self.g_digest)
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

            working_widgets = [self.g_mclear, self.g_encrypt, self.g_decrypt, self.g_bclear, self.g_modetoolbar, self.g_enctoolbar, self.g_expander, self.g_sigtoolbar]
            for w in working_widgets:  w.set_sensitive(False)
            self.ib_filemode.hide()

        
        elif self.x.io['infile'] and self.x.io['outfile']:
            working_widgets = [self.g_mclear, self.g_encrypt, self.g_decrypt, self.g_bclear, self.g_modetoolbar, self.g_enctoolbar, self.g_expander, self.g_sigtoolbar]
            for w in working_widgets:  w.set_sensitive(False)
            self.ib_filemode.hide()
        
        # TEXT INPUT PREP
        else:
            
            working_widgets = [
                self.g_mclear, self.g_encrypt, self.g_decrypt, self.g_bclear, self.g_modetoolbar, self.g_enctoolbar, self.g_expander, self.g_sigtoolbar,
                self.g_mengine, self.g_bcopyall, self.g_bopen, self.g_mopen, self.g_bsave, self.g_msave,
                self.g_mcut, self.g_mcopy, self.g_mpaste]
            for w in working_widgets:  w.set_sensitive(False)
            
            # Save textview buffer to Xface.stdin
            self.x.io['stdin'] = self.buff.get_text(self.buff.get_start_iter(),
                                                    self.buff.get_end_iter())
        
        # Set working status + spinner + progress bar
        self.show_working_progress(True, action)
        
        # ATTEMPT EN-/DECRYPTION        
        if self.engine in 'OpenSSL':
            Thread(target=self.x.openssl, args=(action, passwd, base64, cipher)).start()
        
        else:
            Thread(target=self.x.gpg, args=(action,
                                            encsign,
                                            digest,
                                            localuser,
                                            base64,
                                            symmetric, passwd,
                                            asymmetric, recip, enctoself,
                                            cipher,
                                            verbose,
                                            alwaystrust)).start()
        
        # Wait for subprocess to finish or for cancel button to be clicked
        c = 0
        while not self.x.childprocess or self.x.childprocess.returncode == None:
            if self.canceled:  break
            if c % 10 == 0 and not self.paused:
                self.g_progbar.pulse()
            gtk.main_iteration()
            c += 1
        
        for w in working_widgets:  w.set_sensitive(True)
        self.show_working_progress(False)
        self.buff2.set_text(self.x.io['stderr'])
        
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
                    
                self.infobar("<b>{} operation canceled.</b>\n<small>To choose different input or "
                             "output filenames, select <i>Cancel</i>\nfrom the blue bar below.</small>"
                             .format(action), (1,3), 6)
            
            elif self.x.childprocess.returncode == 0:  # File Success!

                if self.engine in 'OpenSSL' and action in 'enc':
                    self.infobar("<b>OpenSSL encrypted input file with {} cipher;\nsaved output to file:\n"
                                 "<i><tt><small>{}</small></tt></i></b>\n"
                                 "<small>In order to decrypt that file in the future, you will need to \n"
                                 "remember which cipher you used .. or guess until you figure it out.</small>"
                                 .format(cipher, self.x.io['outfile']), (1,0), 10)

                elif action in {'enc', 'dec'}:
                    self.infobar("<b>Saved {}rypted copy of input to file:\n"
                                 "<i><tt><small>{}</small></tt></i></b>"
                                 .format(action, self.x.io['outfile']), (1,0))
                
                elif action in {'embedsign', 'clearsign'}:
                    self.infobar("<b>Saved signed copy of input to file:\n"
                                 "<i><tt><small>{}</small></tt></i></b>"
                                 .format(self.x.io['outfile']), (1,0))
                
                elif action in 'detachsign':
                    self.infobar("<b>Saved detached signature of input to file:\n"
                                 "<i><tt><small>{}</small></tt></i></b>"
                                 .format(self.x.io['outfile']), (1,0))
                
                elif action in 'verify':
                    self.infobar("<b>Signature verified. Data integrity intact.</b>", (1,0), 4)
                
                self.cleanup_filemode()
            
            else:  # File Fail!
                
                self.ib_filemode.show()
                if action in 'verify':
                    self.infobar("<b>Signature or data integrity could not be verified.</b>\n<small>See<i> Task "
                                 "Status </i> for details.</small>", (3,4), 7)
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar("<b>For whom do you want to encrypt your message?</b>\n<small>If you don't "
                                 "want to enter recipients and you don't want to select\n<i> Enc. To "
                                 "Self</i>, you must add one of the directives\n"
                                 "\t<b><tt>default-recipient-self\n\tdefault-recipient <i>name</i></tt></b>\n"
                                 "to your <i><tt>gpg.conf</tt></i> file.</small>", (3,2), 0)
                    return
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar("<b>Problem {}ing file.</b>\n<small>See<i> Task Status </i> for "
                             "details. Try a different passphrase or <i>Cancel</i>.</small>"
                             .format(action), (3,4), 8)
        
        # TEXT INPUT MODE CLEANUP
        else:
            
            self.set_stdstatus()
            self.g_msgtxtview.set_sensitive(True)
            self.fix_msgtxtviewcolor(True)
            
            if self.canceled:  # User Canceled!
                
                if action in {'enc', 'dec'}:
                    action = "{}rypt".format(action.title())
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = "Sign"
                elif action in 'verify':
                    action = action.title()
                    
                self.infobar("<b>{} operation canceled.</b>".format(action), (1,3), 5)
            
            elif self.x.childprocess.returncode == 0:  # Text Success!
                
                if action in 'verify':
                    self.infobar("<b>Signature verified. Data integrity intact.</b>", (1,0), 4)
                else:
                    # Set TextBuffer to gpg stdout
                    self.buff.set_text(self.x.io['stdout'])
                    self.x.io['stdout'] = 0
                    if self.engine in 'OpenSSL' and action in 'enc':
                        self.infobar("<b>OpenSSL encrypted input using {} cipher.</b>\n"
                                     "<small>In order to decrypt the output in the future, you will need to \n"
                                     "remember which cipher you used .. or guess until you figure it out.</small>"
                                     .format(cipher), (1,0), 9)
            
            else:  # Text Fail!
                
                if action in 'verify':
                    self.infobar("<b>Signature or data integrity could not be verified.</b>\n<small>See<i> "
                                 "Task Status </i> for details.</small>", (3,4), 7)
                    return
                elif action in 'enc' and asymmetric and not recip and not enctoself:
                    self.infobar("<b>For whom do you want to encrypt your message?</b>\n<small>If you don't "
                                 "want to enter recipients and you don't want to select\n<i> Enc. To "
                                 "Self</i>, you must add one of the directives\n"
                                 "\t<b><tt>default-recipient-self\n\tdefault-recipient <i>name</i></tt></b>\n"
                                 "to your <i><tt>gpg.conf</tt></i> file.</small>",
                                 (3,2), 0)
                    return
                elif action in {'enc', 'dec'}:
                    action = action + 'rypt'
                elif action in {'embedsign', 'clearsign', 'detachsign'}:
                    action = 'sign'
                self.infobar("<b>Problem {}ing input.</b>\n<small>See<i> Task Status </i>"
                             "for details.</small>".format(action), (3,4))
    
    
    def show_working_progress(self, show=True, action=None):
        for w in self.g_progbar, self.g_cancel, self.g_pause:
            w.set_visible(show)
        if show:
            self.g_progbar.set_text ("{} working...".format(self.engine))
            if action in {'embedsign', 'clearsign', 'detachsign'}:
                status = "Signing input ..."
            elif action in 'verify':
                status = "Verifying input ..."
            else:
                status = "{}rypting input ...".format(action.title())
            self.g_statusbar.push(self.status, status)
            self.g_activityspin.set_visible(True)
            self.g_activityspin.start()
            gtk.main_iteration()
        else:
            for w in self.g_cancel, self.g_pause:
                w.set_sensitive(True)
                w.set_relief(gtk.RELIEF_NONE)
            self.g_activityspin.stop()
            self.g_activityspin.set_visible(False)
            self.g_statusbar.pop(self.status)
    
    
    def cancel_child_process(self, button):
        stderr.write            ("Canceling Operation\n")
        self.canceled           = True
        for w in self.g_cancel, self.g_pause:
            w.set_sensitive     (False)
        self.g_progbar.set_text ("Canceling Operation...")
        self.g_activityspin.stop()
        gtk.main_iteration()
        while not self.x.childprocess:
            gtk.main_iteration()
        if self.paused:
            self.x.childprocess.send_signal(SIGCONT)
        self.x.childprocess.terminate()
        self.show_working_progress(False)
    
    
    def pause_child_process(self, button):
        while not self.x.childprocess:
            gtk.main_iteration()
        if self.canceled:
            pass
        elif self.paused:
            stderr.write            ("Unpausing\n")
            self.paused             = False
            button.set_relief       (gtk.RELIEF_NONE)
            self.g_progbar.set_text ("{} working...".format(self.engine))
            self.g_activityspin.start()
            self.x.childprocess.send_signal(SIGCONT)
        else:
            stderr.write            ("Pausing\n")
            self.paused             = True            
            button.set_relief       (gtk.RELIEF_NORMAL)
            self.g_progbar.set_text ("Operation PAUSED")
            self.g_activityspin.stop()
            self.x.childprocess.send_signal(SIGSTOP)
    
    
    # Run main application window
    def main(self):
        self.g_window.show()
        settings = gtk.settings_get_default()
        settings.props.gtk_button_images = True
        gtk.main()



