# Makefile.am for OCF RAs
#
# Author: Sun Jing Dong
# Copyright (C) 2004 IBM
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
EXTRA_DIST		= $(ocf_SCRIPTS)

INCLUDES		= -I$(top_srcdir)/include -I$(top_srcdir)/linux-ha

ocfdir		     = @OCF_RA_DIR@/heartbeat

gliblib                 = @GLIBLIB@

if USE_IPV6ADDR
ocf_PROGRAMS           = IPv6addr
else
ocf_PROGRAMS           =
endif

IPv6addr_SOURCES        = IPv6addr.c

IPv6addr_LDADD          = $(top_builddir)/lib/clplumbing/libplumb.la    \
                        $(gliblib) @LIBNETLIBS@



ocf_SCRIPTS	     =  ClusterMon 	\
			Dummy		\
		        IPaddr		\
		        IPaddr2		\
		        drbd		\
			apache		\
			AudibleAlarm	\
			db2		\
			Delay		\
			drbd		\
			eDir88		\
			EvmsSCC		\
			Evmsd		\
			Filesystem	\
			ids		\
			iscsi		\
			ICP		\
			IPsrcaddr	\
			LinuxSCSI	\
			LVM		\
			MailTo		\
			ManageRAID	\
			ManageVE	\
			mysql		\
			o2cb		\
			oracle		\
			oralsnr		\
			pingd		\
			portblock	\
			pgsql		\
			Pure-FTPd	\
			Raid1		\
			rsyncd		\
			SAPDatabase	\
			SAPInstance	\
			SendArp		\
			ServeRAID	\
			Stateful	\
			SysInfo		\
			tomcat		\
			VIPArip		\
			WAS		\
			WAS6		\
			WinPopup	\
			Xen		\
			Xinetd		\
			.ocf-shellfuncs	 \
			.ocf-binaries	 \
			.ocf-directories \
			.ocf-returncodes

commondir	     = @HA_LIBHBDIR@
# Legacy locations
common_SCRIPTS	     = ocf-shellfuncs ocf-returncodes

