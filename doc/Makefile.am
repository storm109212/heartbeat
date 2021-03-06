#
# doc: Linux-HA heartbeat code
#
# Copyright (C) 2001 Michael Moerz
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
MAINTAINERCLEANFILES    = Makefile.in

docdir 			= $(datadir)/doc/@HB_PKG@-@VERSION@

htmlfiles		= HardwareGuide.html	\
			GettingStarted.html	\
			Requirements.html	\
			faqntips.html		\
			hb_report.html	\
			heartbeat_api.html	\
			rsync.html

txtfiles                = $(htmlfiles:.html=.txt)

CLEANFILES              = ChangeLog $(txtfiles)

SPECSRC 		= $(top_builddir)/heartbeat.spec

OTHER_DOCS              = AUTHORS COPYING COPYING.LGPL ChangeLog \
                                README authkeys ha.cf startstop haresources \
				DirectoryMap.txt apphbd.cf logd.cf

doc_DATA		= $(OTHER_DOCS) $(txtfiles) $(htmlfiles) 

man_MANS		= heartbeat.8 apphbd.8 cl_status.1 ha_logd.8 ha_logger.1 \
			 hb_standby.1 hb_takeover.1 hb_addnode.1 hb_delnode.1

if CRM_BUILD
man_MANS		+= cibadmin.8 crm_resource.8
endif

EXTRA_DIST = $(txtfiles) $(htmlfiles) $(man_MANS) $(OTHER_DOCS)

ChangeLog: $(SPECSRC)
	rm -fr ChangeLog
	sed -e '1,/^%changelog/d' -e '/^%/,$$d' < $(SPECSRC) > $@

hb_report.txt: hb_report.html
    @true : in this case .txt is the master source

%.txt: %.html
	if [ "X$(HTML2TXT)" = "X" ]; then echo "Lynx or w3m or user-defined HTML2TXT required to convert $< to $@" >$@ ; else $(HTML2TXT) -dump $< >$@ ; fi
