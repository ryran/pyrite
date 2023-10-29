install:
	DESTDIR=$(DESTDIR) ./INSTALL.sh
uninsall:
	rm -rf "$(DESTDIR)/usr/share/pyrite/ui"
	rm -rf "$(DESTDIR)/usr/lib/python3/dist-packages/pyrite"
	rm -f "$(DESTDIR)/usr/share/applications/pyrite.desktop"
	rm -f "$(DESTDIR)/usr/share/icons/hicolor/scalable/apps/pyrite.svg"
	rm -f "$(DESTDIR)/usr/bin/pyrite"
