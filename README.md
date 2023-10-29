Pyrite - Python/GTK+ encryption/signing frontend for GnuPG and OpenSSL
======================================================================

![](http://b19.org/linux/pyrite/1enc_txt.png)

## FEATURES

Pyrite acts as a frontend for GnuPG, doing symmetric or asymmetric encrypting/decrypting, as well as signing and verifying.
Additionally, it can use OpenSSL for simple symmetric encryption/decryption.

Pyrite can operate on text input or can take input and output filenames (text or binary) to pass directly to the backend program (i.e., gpg or openssl).

As you can see from the screenshots, Pyrite can utilize virtually all the encrypting features of GnuPG -- you can mix and match passphrase & public-key encryption & signing with one file, just like gpg, which will require interacting with your gpg-agent.
Or you can keep it simple and just use a passphrase as a shared key, in which case gpg-agent is bypassed and you only have to type the passphrase once.

Also shown in the screenshots is a Sign/Verify mode, where you can choose between the three types of signing: normal (Pyrite calls it "embedded"), where a signed copy of the message is created; clearsign, where the message is wrapped with a plaintext ASCII sig; or detached-sign, where a separate sig file is created.

If you're operating directly on files (in sign or encrypt mode) instead of ASCII text in the Pyrite window, you can choose what kind of output you want -- ASCII-armored (base64-encoded) text or normal binary output.

Not shown in the screenshots is drag & drop. You can drag text files onto the Message area and they are loaded up and you can drag text or binary files onto the *Input File For Direct Operation* button to set that.

If you end up working on very large input, you'll get a chance to *really* see the progress bar + pause/cancel buttons.
At the moment the progress bar doesn't report actual progress (that's coming), but the buttons do what they advertise, pausing or canceling the backend processing.

To top it all off, everything is configurable.
There's a preferences dialog that lets you play with all the settings, from tweaking gpg verbosity to setting the default operating mode to choosing your favorite cipher to configuring font size/color and window opacity.

If you find yourself wondering about a particular feature, just hover your mouse over its widget -- there are detailed tooltips for everything.


## FEDORA/RHEL7 INSTALLATION
There's an RPM (and yum repository) @ [people.redhat.com/rsawhill/rpms](https://people.redhat.com/rsawhill/rpms/). To configure it and install Pyrite, simply run the following as root:

```
yum install https://people.redhat.com/rsawhill/rpms/latest-rsawaroha-release.rpm
yum install pyrite
```

Requirements and package names:

- GTK3: `gtk3`
- Python3: `python3`
- `python3-gi`, `python3-gi-cairo`
- PGP `gnupg` or OpenSSL `openssl`


## DEBIAN/UBUNTU/OTHER LINUX INSTALLATION

There is a simple interactive shell installer.

If requirements are met, clone the Pyrite repo with `git clone https://github.com/ryran/pyrite.git` **OR** [download a zip of the source](https://github.com/ryran/pyrite/archive/master.zip).

From the root source folder execute the interactive `INSTALL` script.


## MORE SCREENSHOTS (v1.0.1):

![](http://b19.org/linux/pyrite/2clearsign_txt.png)
![](http://b19.org/linux/pyrite/3enc_prog.png)
![](http://b19.org/linux/pyrite/4dec_txt.png)
![](http://b19.org/linux/pyrite/5openssl_txt.png)
![](http://b19.org/linux/pyrite/6prefs.png)


## `pyrite` command-line options
Type `pyrite --help`:
```
usage: pyrite [-h] [-d | -t] [-e | -s] [-c] [-r RECIP] [-k KEYUID]
              [-b {gpg,openssl}]
              [INPUT]

GnuPG/OpenSSL GUI to encrypt, decrypt, sign, or verify files/ASCII text input.

positional arguments:
  INPUT                 ascii input file to populate Message area with (NOTE:
                        treatment of INPUT is modified by '-t' & '-d')

optional arguments:
  -h, --help            show this help message and exit
  -d, --direct-file     flag INPUT as a file path to open in direct-mode
  -t, --text-input      flag INPUT as text instead of a file path
  -e, --encdec          enable encrypt/decrypt mode
  -s, --signverify      enable sign/verify mode
  -c, --symmetric       enable symmetric encryption mode
  -r RECIP, --recipients RECIP
                        recipients for asymmetric mode (semicolon-separated)
  -k KEYUID, --defaultkey KEYUID
                        override default gpg private key
  -b {gpg,openssl}, --backend {gpg,openssl}
                        backend program to use as encryption engine
```


## BUGS and TODO

- No undo. It wasn't a top priority at the beginning, but I think it's pretty essential for an application that basically contains a text editor to have an undo/redo stack. I'll do it eventually.
- Icons for encrypt, decrypt, sign, verify buttons, application
- Update notifications

PLEASE contact me (or [post a new issue on the tracker](/ryran/pyrite/issues)) with any suggestions, feedback, bug reports, or questions!


## AUTHORS

As far as direct contributions go, so far it's just me, [ryran](/ryran), aka rsaw, aka [Ryan Sawhill Aroha](http://b19.org).

Feel free to contribute!
The project could really use a little assistance from an artist -- it doesn't have an application icon. (!) Also, it could use icons for the encrypt, decrypt, sign, and verify buttons.



## LICENSE

Copyright (C) 2012, 2013 [Ryan Sawhill Aroha](http://b19.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License @[gnu.org/licenses/gpl.html](https://gnu.org/licenses/gpl.html>) for more details.


--------

Hmmmm. You're still here?

Oh. You must be wondering why the name [*Pyrite*](https://en.wikipedia.org/wiki/Pyrite), eh?

Well, I'll let my friend River who came up with the name explain it to you:

> It should be 'Pyrite', because people think they are getting your data, but really it's just gibberish to them.
> Fool's gold.

