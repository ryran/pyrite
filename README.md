Pyrite - GnuPG encrypting, decrypting, signing, & verifying [GTK+/Python frontend for gpg, gpg2, openssl]
===============================================================

v1.0.0_dev:

![](http://b19.org/linux/pyrite/1enc_txt.png)
![](http://b19.org/linux/pyrite/2clearsign_txt.png)
![](http://b19.org/linux/pyrite/3sign_file.png)
![](http://b19.org/linux/pyrite/4dec_txt.png)
![](http://b19.org/linux/pyrite/5openssl.png)

Possibly more screenshots at: http://b19.org/linux/pyrite

DEPENDENCIES
------------
designed for linux
need Python2.7 and pygtk
need gpg or gpg2 or openssl


INSTALLATION
------------
Clone the repo or download the source and execute the interactive INSTALL script (or if you just want to try it out, you can run pyrite.py from wherever you download it to -- just make sure all of the other files are in the same dir).


BACKGROUND
----------

The original goal of this project was to make symmetric {en,de}cryption more accessible and easy to use. While GPG rocks if you're comfortable on the commandline (for both symmetric & public-key), and there are GUI encryption options for public-key encryption (seahorse-plugins for nautilus being the best, in my opinion), there's not much out there for people who need to do the simplest kind of encryption -- with a shared passphrase.

After creating a few simple apps with BASH scripting, I decided it was time to learn Python. After the first few days I was in love.

Long story short, after a couple weeks of learning, I released my first version of this project in January 2012, and have been improving it ever since. Have lots more to learn (I was also new to GTK+), but I'm damn proud of Pyrite.

PLEASE contact me (or post on the tracker) with any suggestions, feedback, bug reports, or questions!


AUTHORS
-------

For now, just me.
[ryran](https://github.com/ryran)

Feel free to contribute!


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

