#
# Author: Sun Jiang Dong <sunjd@cn.ibm.com>
# Copyright (c) 2005 International Business Machines
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
MAINTAINERCLEANFILES = Makefile.in

INCLUDES                	=	-I$(top_builddir)/include -I$(top_srcdir)/include \
                       			-I$(top_builddir)/linux-ha -I$(top_srcdir)/linux-ha \
					-I$(top_builddir)/libltdl -I$(top_srcdir)/libltdl \
					-I$(top_builddir)          -I$(top_srcdir)

halibdir			=	$(libdir)/@HB_PKG@
guilibdir                       =       $(libdir)/heartbeat-gui
havarlibdir			=	$(localstatedir)/lib/@HB_PKG@
COMMONLIBS			=	$(GLIBLIB)
MGMT_DIR 			=	mgmt
mgmtdir				=	$(HA_VARLIBDIR)/$(HB_PKG)/$(MGMT_DIR)
apigid                          =       @HA_APIGID@

EXTRA_DIST			=	pymgmt.i

lib_LTLIBRARIES = libhbmgmttls.la libhbmgmtclient.la libhbmgmtcommon.la
libhbmgmttls_la_SOURCES = mgmt_tls_lib.c
libhbmgmttls_la_LIBADD  = $(COMMONLIBS)
libhbmgmttls_la_LDFLAGS = $(GNUTLSLIBS)
libhbmgmttls_la_CFLAGS = $(INCLUDES) $(GNUTLSHEAD)

libhbmgmtclient_la_SOURCES = mgmt_client_lib.c
libhbmgmtclient_la_LIBADD = $(COMMONLIBS) libhbmgmttls.la $(top_builddir)/replace/libreplace.la
libhbmgmtclient_la_CFLAGS = $(INCLUDES)

libhbmgmtcommon_la_SOURCES = mgmt_common_lib.c
libhbmgmtcommon_la_LIBADD = $(COMMONLIBS) $(top_builddir)/replace/libreplace.la
libhbmgmtcommon_la_CFLAGS = $(INCLUDES)

guilib_LTLIBRARIES = _pymgmt.la
_pymgmt_la_SOURCES = pymgmt_wrap.c mgmt_client_lib.c mgmt_tls_lib.c mgmt_common_lib.c
_pymgmt_la_CFLAGS = @PYTHON_INCLUDES@ -I$(top_builddir)/include -w
_pymgmt_la_LDFLAGS = -module $(GNUTLSLIBS)
_pymgmt_la_LIBADD = $(top_builddir)/replace/libreplace.la

guilib_SCRIPTS = pymgmt.py

pymgmt_wrap.c pymgmt.py: pymgmt.i
	$(SWIG) -python $^

install-exec-local:
	$(mkinstalldirs) $(DESTDIR)$(mgmtdir)
	-chgrp $(apigid) $(DESTDIR)/$(mgmtdir)
	chmod 770 $(DESTDIR)/$(mgmtdir)
