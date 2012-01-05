a8crypt - GTK/Python frontend for GPG/GPG2 symmetric encryption
==========================================================

SCREENSHOTS
-----------
![](http://b19.org/linux/a8crypt/txtoutput.png)

See a few more screenshots at: http://b19.org/linux/a8crypt

DEPENDENCIES
------------
designed for linux; need GTK2, Python, & gpg or gpg2


BACKGROUND
----------

The original goal of this project was to make symmetric text {en,de}cryption more accessible and easy to use. While GPG rocks (for both symmetric & public-key) if you're comfortable on the commandline, and there are GUI encryption options for key-based, there's not much out there for people who need to do the simplest kind of encryption -- with a shared passphrase.

First I developed a super-simple wrapper for the commandline. (To see an evolution of that, check out [a3crypt](/ryran/a7crypt/blob/master/a3crypt-noX). Screenshots of terminal action at the end of the [moarSCREENSHOTS](/ryran/a7crypt/blob/master/moarSCREENSHOTS.md) page.) Once that was complete, I decided it was time to the fill the hole of a GUI for symmetric encryption, and began fleshing it out and adding features, quickly adding the ability to pick files (and have the script automatically choose ASCII or binary output type based on the chosen file). I implemented that in BASH with the help of Zenity and called it [a7crypt](/ryran/a7crypt/) (screenshots there).

Separately from all this, I decided it was time to learn Python and what better way to learn than to have a project... so first I implemented a3crypt in Python (i.e., a non-gui terminal app) as [a4crypt](/ryran/a8crypt/blob/master/a4crypt.py). Much cooler than a3crypt. I was in love with Python.

Next I decided to try to implement it with GTK. So here we are. Have lots more to learn, but I'm damn proud of v0.0.1 of a8crypt. While it doesn't have some of the features of a7crypt (sticking to GPG/GPG2 only; no OpenSSL), it's much better in most ways. I used to love programming in BASH, but that was before learning Python ... oh the code is so lovely.

Feel free to hit me/the tracker up if you have any questions or suggestions!


AUTHORS
-------

[ryran](https://github.com/ryran)

And so far, that's it. Feel free to contribute!


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

