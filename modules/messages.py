#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/03/04
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

SUCCESS         = 0
INFO            = 1
QUESTION        = 2
WARNING         = 3
ERROR           = 4

def msg(text, type, icon, timeout=5):
    """Dictionar-ify input arguments."""
    return {'text': text, 'type': type, 'icon': icon, 'timeout': timeout}


#------------------------------------------------------------------------------
                                             # INFOBAR MESSAGES FOR MAIN WINDOW
MESSAGE_DICT = dict(
    
    #- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - Backend Engine
    engine_openssl_missing = msg(
        ("<b>Shockingly, your system does not appear to have OpenSSL.</b>"),
        INFO, WARNING),
    
    engine_gpg_missing = msg(
        ("<b>GnuPG not found. Operating in OpenSSL fallback-mode.</b>\n"
            "<small>To make full use of this program you need either <tt>gpg</tt> or <tt>gpg2</tt> installed.\n"
            "Without one of them, you won't have access key-based functions like\n"
            "asymmetric encryption or singing.</small>"),
        INFO, WARNING, 20),
    
    engine_all_missing = msg(
        ("<b>This program requires one of: <tt>gpg</tt>, <tt>gpg2</tt>, or <tt>openssl</tt></b>\n"
            "<small>None of these were found on your system. You can look around\n"
            "the interface, but to have real fun you'll need to install <tt>gpg</tt> or <tt>gpg2</tt>\n"
            "from your linux distribution's software repository.</small>"),
        ERROR, WARNING, 0),
    
    engine_openssl_notice = msg(
        ("<b>OpenSSL only supports symmetric {{en,de}}cryption.</b>\n"
            "<small>All key-based functions are disabled.</small>"), 
        INFO, INFO, 7),
    
    #- - - - - - - - - - - - - - - - - - - - - Textview Message Area Operations
    txtview_empty = msg(
        ("<b>{customtext}</b>"),
        INFO, WARNING, 2),
    
    txtview_fileopen_error = msg(
        ("<b>Error. Could not open file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        WARNING, ERROR),
    
    txtview_fileopen_binary_error = msg(
        ("<b>To operate on binary files, use the\n"
            "<i>Input File For Direct Operation </i> chooser button.</b>"),
        INFO, WARNING, 8),
    
    txtview_save_success = msg(
        ("<b>Saved contents of Message area to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        INFO, SUCCESS),
    
    txtview_save_error = msg(
        ("<b>Error. Could not save to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        WARNING, ERROR),

    txtview_copyall_success = msg(
        ("<b>Copied contents of Message area to clipboard.</b>"),
        INFO, SUCCESS, 3),
    
    #- - - - - - - - - - - - - - - - - - - - - - - - - - -  Filemode Operations
    filemode_fileopen_error = msg(
        ("<b>Error. Could not open file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>\n"
            "<small>Choose a new file.</small>"),
        WARNING, ERROR),
    
    filemode_blue_banner = msg(
        ("<b><i>Encrypt</i>, <i>Decrypt</i>, <i>Sign</i>, or <i>Verify</i>?</b>\n"
            "<small>Choose an action to perform on file:\n"
            "<i><tt>{filename}</tt></i>\n"
            "You will be prompted for an output filename if necessary.</small>"),
        QUESTION, QUESTION, 0),
    
    #- - - - - - - - - - - - - - -  Main xface (Enc/Dec/Sign/Verify) Operations
    x_missing_passphrase= msg(
        ("<b>Passphrase?</b>"),
        INFO, QUESTION, 3),
    
    x_canceled_filemode = msg(
        ("<b>{customtext} operation canceled.</b>\n"
            "<small>To choose different input or output filenames, select <i>Cancel</i>\n"
            "from the blue bar below.</small>"),
        INFO, WARNING, 6),
    
    x_canceled_textmode = msg(
        ("<b>{customtext} operation canceled.</b>"),
        INFO, WARNING, 4),

    x_opensslenc_success_filemode = msg(
        ("<b>OpenSSL encrypted input file with {customtext} cipher;\n"
            "saved output to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>\n"
            "<small>In order to decrypt that file in the future, you will need to \n"
            "remember which cipher you used .. or guess until you figure it out.</small>"),
        INFO, SUCCESS, 10),
    
    x_opensslenc_success_textmode = msg(
        ("<b>OpenSSL encrypted input using {customtext} cipher.</b>\n"
            "<small>In order to decrypt the output in the future, you will need to \n"
            "remember which cipher you used .. or guess until you figure it out.</small>"),
        INFO, SUCCESS, 9),
    
    x_crypt_success_filemode = msg(
        ("<b>Saved {customtext}rypted copy of input to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        INFO, SUCCESS),
    
    x_sign_success_filemode = msg(
        ("<b>Saved signed copy of input to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        INFO, SUCCESS),
    
    x_detachsign_success_filemode = msg(
        ("<b>Saved detached signature of input to file:\n"
            "<i><tt><small>{filename}</small></tt></i></b>"),
        INFO, SUCCESS),
    
    x_verify_success = msg(
        ("<b>Signature verified. Data integrity intact.</b>"),
        INFO, SUCCESS, 4),
    
    x_verify_failed = msg(
        ("<b>Signature or data integrity could not be verified.</b>\n"
            "<small>See<i> Task Status </i> for details.</small>"),
        WARNING, ERROR, 7),
    
    x_missing_recip = msg(
        ("<b>For whom do you want to encrypt your message?</b>\n"
            "<small>If you don't want to enter recipients and you don't want to select\n"
            "<i> Enc. To Self</i>, you must add one of the directives\n"
            "\t<b><tt>default-recipient-self\n"
            "\tdefault-recipient <i>name</i></tt></b>\n"
            "to your <i><tt>gpg.conf</tt></i> file.</small>"),
        WARNING, QUESTION, 0),
    
    x_generic_failed_filemode = msg(
        ("<b>Problem {customtext}ing file.</b>\n"
            "<small>See<i> Task Status </i> for details. Try a different passphrase or <i>Cancel</i>.</small>"),
        WARNING, ERROR, 8),
    
    x_generic_failed_textmode = msg(
        ("<b>Problem {customtext}ing input.</b>\n"
            "<small>See<i> Task Status </i> for details.</small>"),
        WARNING, ERROR),
    
    #- - - - - - - - - - - - - - - - - - - - - - - - -  OpenSSL Cipher Warnings
    cipher_openssl_no_default = msg(
        ("<b>OpenSSL has no default cipher.</b>\n"
            "<small>AES256 is a good choice.</small>"),
        INFO, INFO, 7),
    
    cipher_openssl_no_twofish = msg(
        ("<b>OpenSSL has no support for the Twofish cipher.</b>"),
        INFO, INFO),
    
    cipher_openssl_aes_note = msg(
        ("<b>Note for the command-line geeks:</b>\n"
            "<small><i>AES</i> translates to OpenSSL's <i>aes-128-cbc</i>.</small>"),
        INFO, INFO),
    
    #- - - - - - - - - - - - - - - - - - - - - - - - - - -  Preferences Actions
    preferences_save_success = msg(
        ("<b>Saved preferences to <i><tt><small>{filename}</small></tt></i>\n"
            "but no changes made to current session.</b>"),
        INFO, SUCCESS),
    
    preferences_apply_success = msg(
        ("<b>Saved preferences to <i><tt><small>{filename}</small></tt></i>\n"
            "and applied them to current session.</b>"),
        INFO, SUCCESS),
    
    )



#------------------------------------------------------------------------------
                                      # INFOBAR MESSAGES FOR PREFERENCES DIALOG
PREFS_MESSAGE_DICT = dict(
    
    prefs_save_failed = msg(
        ("<b>Saving preferences failed.</b>\n"
            "Unable to open config file <i><tt><small>{filename} </small></tt></i> for writing."),
        ERROR, WARNING, 10),
    
    prefs_reverted = msg(
        ("<b>Reverted to user-saved preferences.</b>"),
        INFO, SUCCESS, 3),
    
    prefs_reset_to_defaults = msg(
        ("<b>Preferences reset to defaults. You still need to <i>Save</i> or <i>Apply</i>.</b>"),
        INFO, SUCCESS, 3),
    
    prefs_notice_enctoself = msg(
        ("<b>If you want <i>Encrypt to Self</i> on in Symmetric mode, you must set\n"
            "<i>Encryption Type</i> to 'Both'.</b>"),
        INFO, INFO),
    
    prefs_notice_addsig = msg(
        ("<b>If you want <i>Add Signature</i> on in Symmetric mode, you must also enable\n"
            "<i>Advanced</i></b>."),
        INFO, INFO),
    
    prefs_notice_enc_both = msg(
        ("<b>In order for both encryption types to be on by default, <i>Advanced</i> will also be\n"
            "turned on, whether or not you select it now.</b>"),
        INFO, INFO),
    
    )
