#
# RecoveryMgr: Recovery manager plugins for Linux-HA
#
# Copyright (C) 2001 Intel Corporation <andrea.l.brugger@intel.com>
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

INCLUDES                = -I$(top_builddir)/include -I$(top_srcdir)/include \
			-I$(top_builddir)/linux-ha -I$(top_srcdir)/linux-ha  \
			-I$(top_builddir)/libltdl -I$(top_srcdir)/libltdl  \
			-I$(top_builddir)/lib/upmls -I$(top_srcdir)/lib/upmls

## libraries

halibdir		= $(libdir)/@HB_PKG@
plugindir		= $(halibdir)/plugins/AppHBNotification
plugin_LTLIBRARIES	= recmgr.la

recmgr_la_SOURCES	= recmgr.c 
recmgr_la_LIBADD	= $(top_builddir)/lib/recoverymgr/librecoverymgr.la
recmgr_la_LDFLAGS	= -export-dynamic -module -avoid-version


