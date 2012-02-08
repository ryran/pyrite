Pyrite - GnuPG encrypting, decrypting, signing, & verifying [GTK+/Python frontend for gpg, gpg2, openssl]
===============================================================

v1.0.0_dev8:

![](http://b19.org/linux/pyrite/1enc_txt.png)
![](http://b19.org/linux/pyrite/2clearsign_txt.png)
![](http://b19.org/linux/pyrite/3enc_prog.png)
![](http://b19.org/linux/pyrite/4dec_txt.png)
![](http://b19.org/linux/pyrite/5openssl_txt.png)
![](http://b19.org/linux/pyrite/6prefs.png)

Possibly more screenshots at: http://b19.org/linux/pyrite



DEPENDENCIES
------------
designed for linux;
need Python2.7 and pygtk; 
need gpg or gpg2 or openssl


INSTALLATION
------------
1) Clone the repo with `git clone git://github.com/ryran/pyrite.git` OR [download a zip of the source](/ryran/pyrite/zipball/master).

2) Execute the interactive INSTALL script OR if you just want to try it out, you can simply run the executable script `pyrite` from the root source folder (it's the file that's executable).


FEATURES
----------
Pyrite acts as a frontend for GnuPG, doing symmetric or asymmetric encrypting/decrypting, as well as signing and verifying. Additionally, it can use OpenSSL for simple symmetric encryption/decryption.

Pyrite can operate on text input or can take input and output filenames (text or binary) to pass directly to the backend program (i.e., gpg/gpg2 or openssl).

As you can see from the screenshots, Pyrite can utilize virtually all of the encrypting features of GnuPG -- you can mix and match passphrase & public-key encryption & signing with one file, just like gpg, which will require interacting with your gpg-agent. Or you can keep it simple and just use a passphrase as a shared key, in which case gpg-agent is bypassed and you only have to type the passphrase once.

Also shown in the screenshots is a Sign/Verify mode, where you can choose between the three types of signing: normal (Pyrite calls it "embedded"), where a signed copy of the message is created; clearsign, where the message is wrapped with a plaintext ASCII sig; or detached-sign, where a separate sig file is created.

If you're operating directly on files (in sign or encrypt mode) instead of ASCII text in the Pyrite window, you can choose what kind of output you want -- ASCII-armored (base64-encoded) text or normal binary output.

Not shown in the screenshots is drag & drop. You can drag text files onto the Message area and they are loaded up and you can drag text or binary files onto the *Input File For Direct Operation* button to set that.

If you end up working on very large input, you'll get a chance to *really* see the progress bar + pause/cancel buttons. At the moment the progress bar doesn't report actual progress (that's coming), but the buttons do what they advertise, pausing or canceling the backend processing.

To top it all off, everything is configurable. There's a preferences dialog that lets you play with all the settings, from tweaking gpg verbosity to setting the default operating mode to choosing your favorite cipher to configuring font size/color and window opacity.


BUGS
----------
1) After launching Pyrite, the **first** drag/drop of a file onto the *Input File For Direct Operation* GtkFileChooserButton fails. After that the button works properly. I've been seeking out expertise on this weird bug but I haven't gotten anywhere. If you have any hints, hit me up, or check out [my post about it on stackoverflow](http://stackoverflow.com/questions/9047844/pygtk-troubles-with-drag-and-drop-file-to-gtkfilechooserbutton).

2) No undo. It wasn't a top priority at the beginning, but I think it's pretty essential for an application that basically contains a text editor to have an undo/redo stack. I'll do it eventually.


BACKGROUND
----------

The original goal of this project was to make symmetric {en,de}cryption more accessible and easy to use. While GPG rocks if you're comfortable on the commandline (for both symmetric & public-key), and there are GUI encryption options for public-key encryption (seahorse-plugins for nautilus being the best, in my opinion), there's not much out there for people who need to do the simplest kind of encryption -- with a shared passphrase.

After creating a few simple apps with BASH scripting, I decided it was time to learn Python. After the first few days I was in love.

Long story short, after a couple weeks of learning, I released my first version of this project in January 2012, quickly added public-key encryption, signing, & verifying, and have been improving it ever since. This being my first learning experience with GTK+, I have lots more to learn, but I'm damn proud of Pyrite.

PLEASE contact me (or post on the tracker) with any suggestions, feedback, bug reports, or questions!


AUTHORS
-------

For now, just me.
[ryran](https://github.com/ryran)

Feel free to contribute!
The project could really use a little assistance from an artist -- it doesn't have an application icon. (!) Also, it could use icons for the encrypt, decrypt, sign, and verify buttons.



LICENSE
-------

Copyright (C) 2012 [Ryan Sawhill](http://b19.org) aka [ryran](https://github.com/ryran)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License @[gnu.org/licenses/gpl.html](http://gnu.org/licenses/gpl.html>) for more details.




--------


Hmmmm. You're still here?

Oh. You must be wondering why the name [*Pyrite*](http://en.wikipedia.org/wiki/Pyrite), eh?

Well, I'll let my friend River--who came up with the name--explain it to you:

*"It should be 'Pyrite', because people think they are getting your data, but really it's just gibberish to them. Fool's gold."*

