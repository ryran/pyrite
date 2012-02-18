#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/19
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
import glib
import cPickle as pickle
from sys import stderr
from os import access, R_OK, getenv


# Important variables
assetdir                = ''
userpref_file           = getenv('HOME') + '/.pyrite'
userpref_format_info    = {'version':'Must6fa'}



class Preferences:
    """Preferences system.
    
    Try to read preferences from user preferences file; failing that, initialize
    good defaults. This class also includes the Preferences setting window.
    """
    
    
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
        
        # CB for destroy timeout
        def destroy_ibar():
            self.ibar_timeout = 0
            self.ibar.destroy()
            self.window.resize(1,1)
        
        # If infobar already active: delete old timeout, destroy old ibar
        if self.ibar_timeout > 0:
            glib.source_remove(self.ibar_timeout)
            destroy_ibar()
        
        # Unpack message type, image type
        msgtype, imgtype = config
        
        # Figure out what type of infobar was called
        if   msgtype == 1:  msgtype = gtk.MESSAGE_INFO
        elif msgtype == 2:  msgtype = gtk.MESSAGE_QUESTION
        elif msgtype == 3:  msgtype = gtk.MESSAGE_WARNING
        elif msgtype == 4:  msgtype = gtk.MESSAGE_ERROR
        
        # Figure out what kind of icon to show on the left of ibar
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
        self.ibar_timeout       = glib.timeout_add_seconds(timeout, destroy_ibar)
    
    
    def open_preferences_window(self, parentwindow):
        """Show the preferences window. Duh."""
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
        # TODO: Advanced tab
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
        """Set state of widgets in prefs window via preferences."""
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
        """Capture current state of widgets in prefs window & save as preferences."""
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
    
    
    # Called by Save button
    def save_prefs(self):
        """Attempt to save user prefs to homedir prefs file."""
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
    
    
    # Called by Cancel button
    def action_cancel_prefs(self, w):
        """Close prefs window without doing anything."""
        self.window.destroy()
    
    
    # Called by Revert button
    def action_revert_prefs(self, w):
        """Reset state of widgets in prefs window via external preferences file, if avail."""
        self.__init__()
        self.populate_pref_window_prefs()
        self.infobar("<b>Reverted to user-saved preferences.</b>", (1,0), 3)
    
    
    # Called by Defaults button
    def action_default_prefs(self, w):
        """Reset state of widgets in prefs window to predefined defaults."""
        self.__init__(reset_defaults=True)
        self.populate_pref_window_prefs()
        self.infobar("<b>Preferences reset to defaults. You still need to <i>Save</i> or "
                     "<i>Apply</i>.</b>", (1,0), 3)
    
    
    def action_tg_enctoself(self, w):
        """Show some info when user enables enctoself toggle."""
        if w.get_active():
            self.infobar("<b>If you want <i>Encrypt to Self</i> on in Symmetric mode, "
                         "you must set\n<i>Encryption Type</i> to 'Both'.</b>")
    
    
    def action_tg_addsig(self, w):
        """Show some info when user enables addsig toggle."""
        if w.get_active():
            self.infobar("<b>If you want <i>Add Signature</i> on in Symmetric mode, "
                         "you must also enable\n<i>Advanced</i></b>.")
    
    
    def action_cb_enctype(self, w):
        """Show some info when user chooses 'Both' in  enctype combobox."""
        if w.get_active() == 2:
            self.infobar("<b>In order for both encryption types to be on by default, "
                         "<i>Advanced</i> will also be\nturned on, whether or not you "
                         "select it now.</b>")

