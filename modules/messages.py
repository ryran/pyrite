#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# This file is part of Pyrite.
# Last file mod: 2012/02/29
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

DEFAULT_TIMEOUT = 5
SUCCESS         = 0
INFO            = 1
QUESTION        = 2
WARNING         = 3
ERROR           = 4


#============================================= INFOBAR MESSAGES FOR MAIN WINDOW
MESSAGE_DICT = dict(
    
    #----------------------------------------------------------- Backend Engine
    
    engine_openssl_missing = dict(
        text="<b>Shockingly, your system does not appear to have OpenSSL.</b>",
        type=INFO,
        icon=WARNING,
        timeout=DEFAULT_TIMEOUT
        ),
    
    engine_gpg_missing = dict(
        text=("<b>GnuPG not found. Operating in OpenSSL fallback-mode.</b>\n"
              "<small>To make full use of this program you need either <tt>gpg</tt> or <tt>gpg2</tt> installed.\n"
              "Without one of them, you won't have access key-based functions like\n"
              "asymmetric encryption or singing.</small>"),
        type=INFO,
        icon=WARNING,
        timeout=20
        ),
    
    engine_all_missing = dict(
        text=("<b>This program requires one of: <tt>gpg</tt>, <tt>gpg2</tt>, or <tt>openssl</tt></b>\n"
              "<small>None of these were found on your system. You can look around\n"
              "the interface, but to have real fun you'll need to install <tt>gpg</tt> or <tt>gpg2</tt>\n"
              "from your linux distribution's software repository.</small>"),
        type=ERROR,
        icon=WARNING,
        timeout=0
        ),
    
    engine_openssl_notice = dict(
        text=("<b>OpenSSL only supports symmetric {{en,de}}cryption.</b>\n"
              "<small>All key-based functions are disabled.</small>"), 
        type=INFO,
        icon=INFO,
        timeout=7
        ),
    
    
    #----------------------------------------- Textview Message Area Operations
    
    txtview_empty = dict(
        text="<b>{customtext}</b>",
        type=INFO,
        icon=WARNING,
        timeout=2
        ),
    
    txtview_fileopen_error = dict(
        text=("<b>Error. Could not open file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=WARNING,
        icon=ERROR,
        timeout=DEFAULT_TIMEOUT
        ),
    
    txtview_fileopen_binary_error = dict(
        text=("<b>To operate on binary files, use the\n"
              "<i>Input File For Direct Operation </i> chooser button.</b>"),
        type=INFO,
        icon=WARNING,
        timeout=8
        ),
    
    txtview_save_success = dict(
        text=("<b>Saved contents of Message area to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    txtview_save_error = dict(
        text=("<b>Error. Could not save to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=WARNING,
        icon=ERROR,
        timeout=DEFAULT_TIMEOUT
        ),

    txtview_copyall_success = dict(
        text="<b>Copied contents of Message area to clipboard.</b>",
        type=INFO,
        icon=SUCCESS,
        timeout=3
        ),
    
    
    #------------------------------------------------------ Filemode Operations
    
    filemode_fileopen_error = dict(
        text=("<b>Error. Could not open file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>\n"
              "<small>Choose a new file.</small>"),
        type=WARNING,
        icon=ERROR,
        timeout=DEFAULT_TIMEOUT
        ),
    
    filemode_blue_banner = dict(
        text=("<b><i>Encrypt</i>, <i>Decrypt</i>, <i>Sign</i>, or <i>Verify</i>?</b>\n"
              "<small>Ready to operate on file:\n"
              "<i><tt>{filename}</tt></i>\n"
              "You will be prompted for an output filename if necessary.</small>"),
        type=QUESTION,
        icon=QUESTION,
        timeout=0
        ),
    
    
    #------------------------------ Main xface (Enc/Dec/Sign/Verify) Operations
    
    x_missing_passphrase= dict(
        text="<b>Passphrase?</b>",
        type=INFO,
        icon=QUESTION,
        timeout=3
        ),
    
    x_canceled_filemode = dict(
        text=("<b>{customtext} operation canceled.</b>\n"
              "<small>To choose different input or output filenames, select <i>Cancel</i>\n"
              "from the blue bar below.</small>"),
        type=INFO,
        icon=WARNING,
        timeout=6
        ),
    
    x_canceled_textmode = dict(
        text="<b>{customtext} operation canceled.</b>",
        type=INFO,
        icon=WARNING,
        timeout=4
        ),

    x_opensslenc_success_filemode = dict(
        text=("<b>OpenSSL encrypted input file with {customtext} cipher;\n"
              "saved output to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>\n"
              "<small>In order to decrypt that file in the future, you will need to \n"
              "remember which cipher you used .. or guess until you figure it out.</small>"),
        type=INFO,
        icon=SUCCESS,
        timeout=10
        ),
    
    x_opensslenc_success_textmode = dict(
        text=("<b>OpenSSL encrypted input using {customtext} cipher.</b>\n"
              "<small>In order to decrypt the output in the future, you will need to \n"
              "remember which cipher you used .. or guess until you figure it out.</small>"),
        type=INFO,
        icon=SUCCESS,
        timeout=9
        ),
    
    x_crypt_success_filemode = dict(
        text=("<b>Saved {customtext}rypted copy of input to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    x_sign_success_filemode = dict(
        text=("<b>Saved signed copy of input to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    x_detachsign_success_filemode = dict(
        text=("<b>Saved detached signature of input to file:\n"
              "<i><tt><small>{filename}</small></tt></i></b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    x_verify_success = dict(
        text="<b>Signature verified. Data integrity intact.</b>",
        type=INFO,
        icon=SUCCESS,
        timeout=4
        ),
    
    x_verify_failed = dict(
        text=("<b>Signature or data integrity could not be verified.</b>\n"
              "<small>See<i> Task Status </i> for details.</small>"),
        type=WARNING,
        icon=ERROR,
        timeout=7
        ),
    
    x_missing_recip = dict(
        text=("<b>For whom do you want to encrypt your message?</b>\n"
              "<small>If you don't want to enter recipients and you don't want to select\n"
              "<i> Enc. To Self</i>, you must add one of the directives\n"
              "\t<b><tt>default-recipient-self\n"
              "\tdefault-recipient <i>name</i></tt></b>\n"
              "to your <i><tt>gpg.conf</tt></i> file.</small>"),
        type=WARNING,
        icon=QUESTION,
        timeout=0
        ),
    
    x_generic_failed_filemode = dict(
        text=("<b>Problem {customtext}ing file.</b>\n"
              "<small>See<i> Task Status </i> for details. Try a different passphrase or <i>Cancel</i>.</small>"),
        type=WARNING,
        icon=ERROR,
        timeout=8
        ),
    
    x_generic_failed_textmode = dict(
        text=("<b>Problem {customtext}ing input.</b>\n"
              "<small>See<i> Task Status </i> for details.</small>"),
        type=WARNING,
        icon=ERROR,
        timeout=DEFAULT_TIMEOUT
        ),
    
    
    #-------------------------------------------------- OpenSSL Cipher Warnings
    
    cipher_openssl_no_default = dict(
        text=("<b>OpenSSL has no default cipher.</b>\n"
              "<small>AES256 is a good choice.</small>"),
        type=INFO,
        icon=INFO,
        timeout=7
        ),
    
    cipher_openssl_no_twofish = dict(
        text="<b>OpenSSL has no support for the Twofish cipher.</b>",
        type=INFO,
        icon=INFO,
        timeout=DEFAULT_TIMEOUT
        ),
    
    cipher_openssl_aes_note = dict(
        text=("<b>Note for the command-line geeks:</b>\n"
              "<small><i>AES</i> translates to OpenSSL's <i>aes-128-cbc</i>.</small>"),
        type=INFO,
        icon=INFO,
        timeout=DEFAULT_TIMEOUT
        ),
    
    
    #------------------------------------------------------ Preferences Actions
    
    preferences_save_success = dict(
        text=("<b>Saved preferences to <i><tt><small>{filename}</small></tt></i>\n"
              "but no changes made to current session.</b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    preferences_apply_success = dict(
        text=("<b>Saved preferences to <i><tt><small>{filename}</small></tt></i>\n"
              "and applied them to current session.</b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=DEFAULT_TIMEOUT
        ),
    
    )



#====================================== INFOBAR MESSAGES FOR PREFERENCES DIALOG
PREFS_MESSAGE_DICT = dict(
    
    prefs_save_failed = dict(
        text=("<b>Saving preferences failed.</b>\n"
              "Unable to open config file <i><tt><small>{filename} </small></tt></i> for writing."),
        type=ERROR,
        icon=WARNING,
        timeout=10
        ),
    
    prefs_reverted = dict(
        text=("<b>Reverted to user-saved preferences.</b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=3
        ),
    
    prefs_reset_to_defaults = dict(
        text=("<b>Preferences reset to defaults. You still need to <i>Save</i> or <i>Apply</i>.</b>"),
        type=INFO,
        icon=SUCCESS,
        timeout=3
        ),
    
    prefs_notice_enctoself = dict(
        text=("<b>If you want <i>Encrypt to Self</i> on in Symmetric mode, you must set\n"
              "<i>Encryption Type</i> to 'Both'.</b>"),
        type=INFO,
        icon=INFO,
        timeout=DEFAULT_TIMEOUT
        ),
    
    prefs_notice_addsig = dict(
        text=("<b>If you want <i>Add Signature</i> on in Symmetric mode, you must also enable\n"
              "<i>Advanced</i></b>."),
        type=INFO,
        icon=INFO,
        timeout=DEFAULT_TIMEOUT
        ),
    
    prefs_notice_enc_both = dict(
        text=("<b>In order for both encryption types to be on by default, <i>Advanced</i> will also be\n"
              "turned on, whether or not you select it now.</b>"),
        type=INFO,
        icon=INFO,
        timeout=DEFAULT_TIMEOUT
        ),
    
    )
