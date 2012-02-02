Pyrite - GnuPG encrypting, decrypting, signing, & verifying [GTK+/Python frontend for gpg, gpg2, openssl]
===============================================================

*As River--who came up with the name--said: "Pyrite, because people think they are getting your data--your gold, but really it's just gibberish to them. Fool's gold."*

v1.0.0_dev:

![](http://b19.org/linux/pyrite/1enc_txt.png)
![](http://b19.org/linux/pyrite/2clearsign_txt.png)
![](http://b19.org/linux/pyrite/3sign_file.png)
![](http://b19.org/linux/pyrite/4dec_txt.png)
![](http://b19.org/linux/pyrite/5openssl.png)
![](http://b19.org/linux/pyrite/6pref.png)

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

