%define _unpackaged_files_terminate_build	1
%define _missing_doc_files_terminate_build	1
%define distro_style_rpms	0
#
%define HB_PKG heartbeat
#
#	Arguments given to configure -- cleaned up by removing
#	libdir definitions, etc.
#
%define cleaned_configure_args  '--prefix=/usr' '--sysconfdir=/etc' '--localstatedir=/var' '--mandir=/usr/share/man' '--disable-rpath' '--disable-ansi' '--enable-mgmt' '--enable-bundled_ltdl'
#
#	Heartbeat features turned on/off
#
%define ENABLE_MGMT	1
%define ENABLE_SNMP_SUBAGENT	0
%define REQUIRE_OPENHPI	1
#
#	Heartbeat-specific defines
#
%if %{ENABLE_SNMP_SUBAGENT}
	%define MIBS_DIR	
%endif
%define HA_CCMUSER hacluster
%define HA_APIGROUP haclient
%define HA_CCMUID 498
%define HA_APIGID 496
%define HB_VERSION 2.1.3
%define SSH /usr/bin/ssh
%define INITDIR /etc/init.d
%define OCF_ROOT_DIR /usr/lib/ocf
%define OCF_RA_DIR /usr/lib/ocf/resource.d/
%define SNMP_RPM_BUILD_REQUIRES BuildRequires: net-snmp openssl tcp_wrappers
%define PING /bin/ping
%if	"" != ""
	%define build_cmpi	1
	%define CIMOM	
	%define CMPI_PROVIDER_DIR	
%else
	%define build_cmpi	0
%endif
%define IPTABLES iptables
%define NOGROUP nobody
%define NOUSER nobody
%define LIBNET_DEVEL libnet,
%define LIBNET	libnet
##############################################################
#
#
#
##############################################################
#
#	Detect OS
%ifos linux
	%define	is_linux	1
%else
	%define	is_linux	0
%endif
%ifos aix
	%define	is_aix	1
%else
	%define	is_aix	0
%endif
%ifos solaris
	%define	is_solaris	1
%else
	%define	is_solaris	0
%endif

#	Detect distro
#
#	I'm sure this code isn't right yet...
#
%define is_suse %(if test -f /etc/SuSE-release; then echo 1; else echo 0;fi)
%define is_fedora %(if test -f /etc/fedora-release; then echo 1; else echo 0;fi)
%define is_rhel %(if test -f /etc/redhat-release; then echo 1; else echo 0;fi)
%if %{is_fedora}
	%undefine is_rhel
	%define is_rhel 0
%endif

%if 0%{?mandriva_version} > 0
	%define	is_mandriva	1
%else
	%define	is_mandriva	0
%endif


%if %{is_rhel}
#	I'm told that executing rpm from rpmbuild is a really bad idea.  Forbidden by Fedora...
	%{!?rhel_ver: %define rhel_ver %(Z=`rpm -q --whatprovides /etc/redhat-release`;A=`rpm -q --qf '%{V}' $Z`; echo ${A:0:1})}
	%if %{rhel_ver} < 6
		%define REQUIRE_OPENHPI	0
	%endif
%endif

%if %{is_suse}
	%define suse_major %(expr %{suse_version} / 100)
	%define suse_minor %(expr %{suse_version} '%' 100)
	%if %suse_version < 1020
		%define REQUIRE_OPENHPI	0
	%endif
%endif

%if !%{is_suse} && !%{is_rhel} && !%{is_fedora} && !%{is_solaris} && !%{is_mandriva} && !%{is_aix} 
	%define	is_other	1
%else
	%define	is_other	0
%endif
#
%define	GUI_PACKAGE 1

%define libdir	%{_libdir}
%define libexecdir	%{_libexecdir}

%if %{distro_style_rpms}
	#	Make it the way the distro wants it
	%define prefix	%{_prefix}
	%define bindir	%{_bindir}
	%define sbindir %{_sbindir}
	%define mandir	%{_mandir}
	%define docdir	%{_docdir}
	%define share	%{_datadir}
	%define sysconfdir	%{_sysconfdir}
	%define localstatedir	%{_localstatedir}
	%define base_includedir	%{_includedir}
	%define RPMREL	1
	%if %{is_suse}
		%undef GUI_PACKAGE
		%define	GUI_PACKAGE 0
	%endif
%else
	#	Make it the way configure wants it
	#	(more or less...)
	%define prefix	/usr
	%define exec_prefix	/usr
	%define bindir	/usr/bin
	%define sbindir /usr/sbin
	%define mandir	/usr/share/man
	%define docdir	/usr/share/doc/heartbeat-2.1.3
	%define share	/usr/share
	%define sysconfdir	/etc
	%define localstatedir	/var
	%define base_includedir	%{prefix}/include
	%define RPMREL	1
	%if "%{prefix}/lib" != "%{_libdir}"
		%define libsuffix %(basename %{_libdir})
		%undefine libdir
		%define libdir %{prefix}/%{libsuffix}
	%endif
	%if "%{prefix}/lib" != "%{_libexecdir}"
		%define libexecsuffix %(basename %{_libexecdir})
		%undefine libexecdir
		%define libexecdir %{prefix}/%{libexecsuffix}
	%endif
%endif

%define PILS_NAME	%{HB_PKG}-pils
%define STONITH_NAME	%{HB_PKG}-stonith
%define GUI_NAME	%{HB_PKG}-gui
%define LDIR_NAME	%{HB_PKG}-ldirectord
%define DEVEL_NAME	%{HB_PKG}-devel
%define CMPI_NAME	%{HB_PKG}-cmpi

%define pkg_group	Utilities
%define	SSLeay	perl-Net-SSLeay
%if %{is_fedora} || %{is_rhel}
	%undefine	PILS_NAME
	%undefine	STONITH_NAME
	%undefine	SSLeay
	%undefine pkg_group
	%define PILS_NAME	pils
	%define STONITH_NAME	stonith
	%define	SSLeay	perl-Net_SSLeay
	%define pkg_group	Productivity/Clustering/HA
%endif
%if %{is_fedora}
	%undefine	LIBNET_DEVEL
	%define		LIBNET_DEVEL	,libnet-devel,
%endif
%if %{is_rhel}
	# Here is a place where CENTOS is different from RHEL.
	# They provide a libnet package, and RHEL does not...
	%undefine	LIBNET_DEVEL
	%define		LIBNET_DEVEL ,
%endif
%if is_suse
	%undefine pkg_group
	%define pkg_group	Productivity/Clustering/HA
%endif

%define	BASE_PROVIDES	ha
%define	PILS_PROVIDES	pils
%define	GUI_PROVIDES	ha-gui
%define	STONITH_PROVIDES	stonith

#
#
# Derived definitions
#
%define locale	%{share}/locale
%define PAMDIR		%{sysconfdir}/pam.d
%define stonith_includedir %{base_includedir}/stonith
%define pils_includedir %{base_includedir}/pils
%define HA_LIBHBDIR	%{libdir}/%{HB_PKG}
%define HA_NOARCHDATAHBDIR	%{share}/%{HB_PKG}
%define pils_plugindir	%{libdir}/pils/plugins
%define HA_VARRUNDIR	%{localstatedir}/run/%{HB_PKG}
%define HA_COREDIR	%{localstatedir}/lib/%{HB_PKG}/cores
%define HA_D_DIR	%{sysconfdir}/ha.d
#
#
#
#
Summary: %{HB_PKG} - The Heartbeat Subsystem for High-Availability Linux
Name:	%{HB_PKG}
Version:	%{HB_VERSION}
Release:	%{RPMREL}%{?dist}
License: GPL/LGPL
URL: http://linux-ha.org/
Group: %{pkg_group}
%if !%{distro_style_rpms}
Packager: Alan Robertson <alanr@unix.sh>
%endif
Source: http://linux-ha.org/download/%{HB_PKG}-%{HB_VERSION}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:	autoconf, automake libtool, libxml2-devel
BuildRequires:	glib2-devel, python, python-devel, perl, %{SSH} , gdbm-devel %{LIBNET_DEVEL} bison, flex
%if %{REQUIRE_OPENHPI}
BuildRequires:	openhpi-devel >= 2.6
%endif
%if %{ENABLE_SNMP_SUBAGENT}
%{SNMP_RPM_BUILD_REQUIRES}
%endif

%if %{is_rhel} && "%{rhel_ver}" >= "5"
BuildRequires: libtool-ltdl-devel
BuildRequires: OpenIPMI-devel
%endif

%if ENABLE_MGMT
#BuildRequires:	libgcrypt-devel
BuildRequires:	gnutls-devel
%endif

%if %{build_cmpi}
%if (%{is_rhel} || %{is_fedora}) && "%{CIMOM}" == "pegasus"
BuildRequires: tog-pegasus
%else
BuildRequires: %{CIMOM}
%endif
%endif

Requires: %{STONITH_NAME} = %{version}-%{release}, %{PILS_NAME} = %{version}-%{release}
Requires: perl, iputils, %{SSH} %{PING} %{IPTABLES}
Requires(pre): /usr/sbin/groupadd /usr/bin/getent /usr/sbin/useradd

%if %{is_suse}
%if %{ENABLE_MGMT} && !%{GUI_PACKAGE}
Requires: python-xml
Requires: python-gtk >= 2.4
%endif
%if 0%{?sles_version} == 9
BuildRequires: pkgconfig
%endif
%if 0%{?suse_version} == 1000
BuildRequires: lzo
%endif
%endif

%if %{is_fedora}
Requires:	PyXML
BuildRequires: 		which OpenIPMI-devel
BuildRequires: bzip2-devel
Requires(pre):          fedora-usermgmt
Requires(postun):       fedora-usermgmt
%endif

%if %{is_rhel}
Requires:	PyXML
BuildRequires: bzip2-devel
%endif

%if %{is_mandriva}
%endif
%if %{is_aix}
%endif
%if %{is_solaris}
%endif

%if %build_cmpi
%package -n %{CMPI_NAME}
Summary:        Heartbeat CIM Provider
Group:          %{pkg_group}
%description cmpi
This package provides the CIM provider for managing heartbeat via
%{CIMOM}.
%endif

%package -n %{DEVEL_NAME}
Summary:        %{HB_PKG} development package 
Group:          %{pkg_group}
Requires:       %{HB_PKG} = %{version}-%{release}

%description devel
%{HB_PKG} development package


%package -n %{LDIR_NAME}
Summary: Monitor daemon for maintaining high availability resources with ipvs (Linux Virtual Server}
Group: %{pkg_group}
Requires: ipvsadm, perl, perl-libwww-perl, perl-Authen-Radius, perl-Crypt-SSLeay, perl-HTML-Parser
Requires: perl-ldap, perl-MailTools, perl-Net-IMAP-Simple, perl-Net-IMAP-Simple-SSL, perl-POP3Client
Requires: perl-libnet, perl-Net-DNS
# Perl modules available from www.ultramonkey.org and others

%if %{is_suse}
%endif
%if %{is_fedora}
%endif
%if %{is_rhel}
%endif
%if %{is_mandriva}
%endif
%if %{is_aix}
%endif
%if %{is_solaris}
%endif

%package -n %{STONITH_NAME}
Requires: telnet, %{SSH} %{PILS_NAME} = %{version}-%{release}
Summary: Provides an interface to Shoot The Other Node In The Head 
Group: %{pkg_group}

%if %{is_suse}
%endif
%if %{is_fedora}
%endif
%if %{is_rhel}
%endif
%if %{is_mandriva}
%endif
%if %{is_aix}
%endif
%if %{is_solaris}
%endif

%package -n %{PILS_NAME}
Summary: Provides a general plugin and interface loading library
Group: %{pkg_group}

%if %{ENABLE_MGMT} && %{GUI_PACKAGE}
%package -n %{GUI_NAME}
Summary: Provides a gui interface to manage heartbeat clusters
Group: %{pkg_group}

%if %{is_suse}
Requires: python-xml
Requires: python-gtk >= 2.4
%endif
%if %{is_fedora}
Requires:	PyXML
Requires:	pygtk2 >= 2.4
%endif
%if %{is_rhel}
Requires:	PyXML
Requires:	pygtk2 >= 2.4
%endif
%if %{is_mandriva}
%endif
%if %{is_aix}
%endif
%if %{is_solaris}
%endif
%endif

%description
%{HB_PKG} is an advanced  high-availability subsystem for Linux-HA.
It supports "n-node" clusters with significant capabilities for 
creating sophisticated policies for managing resources and dependencies.

In addition it continues to support the older release 1 style of
2-node clustering.
%description -n %{LDIR_NAME}
ldirectord is a stand-alone daemon to monitor services of real 
for virtual services provided by The Linux Virtual Server
(http://www.linuxvirtualserver.org/). It is simple to install 
and works with the heartbeat code (http://www.linux-ha.org/).

%description -n %{STONITH_NAME}
The STONITH module (a.k.a. STOMITH) provides an extensible interface
for remotely powering down a node in the cluster.  The idea is quite simple:
When the software running on one machine wants to make sure another
machine in the cluster is not using a resource, pull the plug on the other 
machine. It's simple and reliable, albeit admittedly brutal.

%description -n %{PILS_NAME}
PILS is an generalized and portable open source
Plugin and Interface Loading System.
PILS was developed as part of the Open Cluster Framework
reference implementation, and is designed
to be directly usable by a wide variety of other applications.
PILS manages both plugins (loadable objects),
and the interfaces these plugins implement.
PILS is designed to support any number of plugins
implementing any number of interfaces.

%if %{ENABLE_MGMT} && %{GUI_PACKAGE}
%description gui
GUI client for Heartbeat clusters
%endif

%prep
###########################################################
%setup

###########################################################
%build
###########################################################
#
#	I think we should make the RPM configured the same way as things
#	were configured by the user.
#
%if %{distro_style_rpms}
%configure
%else
./configure %{cleaned_configure_args} '--libdir=%{libdir}' '--libexecdir=%{libexecdir}'
%endif
make

###########################################################
%install
###########################################################
#make DESTDIR=$RPM_BUILD_ROOT install-strip
make DESTDIR=$RPM_BUILD_ROOT install
%find_lang haclient

###########################################################
%files
###########################################################
%defattr(-,root,root)
%dir %{HA_D_DIR}
%{HA_D_DIR}/harc
%{HA_D_DIR}/shellfuncs
%{HA_D_DIR}/rc.d
%{HA_D_DIR}/README.config
%{HA_LIBHBDIR}
%{libdir}/libapphb.so.*
%{libdir}/libccmclient.so.*
%{libdir}/libcib.so.*
%{libdir}/libclm.so.*
%{libdir}/libcrmcommon.so.*
%{libdir}/libtransitioner.so.*
%{libdir}/libhbclient.so.*
%{libdir}/liblrm.so.*
%{libdir}/libpengine.so.*
%{libdir}/libplumb.so.*
%{libdir}/libplumbgpl.so.*
%{libdir}/librecoverymgr.so.*
%{libdir}/libstonithd.so.*
%{libdir}/libpe_rules.so.*
%{libdir}/libpe_status.so.*
%{HA_NOARCHDATAHBDIR}
%{OCF_ROOT_DIR}
%exclude %{OCF_RA_DIR}/heartbeat/ldirectord
%{HA_D_DIR}/resource.d/
%exclude %{HA_D_DIR}/resource.d/ldirectord
%config %{INITDIR}/heartbeat
%config %{sysconfdir}/logrotate.d/heartbeat
%dir %{localstatedir}/lib/%{HB_PKG}
%dir %{HA_COREDIR}
%dir %attr (0700, root, -) %{HA_COREDIR}/root
%dir %attr (0700, %{NOUSER}, -) %{HA_COREDIR}/%{NOUSER}
%dir %attr (0700, %{HA_CCMUSER}, -) %{HA_COREDIR}/%{HA_CCMUSER}
%dir %{localstatedir}/run
%dir %{localstatedir}/run/%{HB_PKG}
%attr (2555, %{HA_CCMUSER}, %{HA_APIGROUP}) %{bindir}/cl_status
%{bindir}/cl_respawn
%{sbindir}/ciblint
%{sbindir}/ptest 
%{sbindir}/crmadmin 
%{sbindir}/cibadmin 
%{sbindir}/ccm_tool 
%{sbindir}/crm_diff 
%{sbindir}/crm_uuid
%{sbindir}/crm_mon 
%{sbindir}/ocf-tester
%{sbindir}/hb_report
%{sbindir}/iso8601
%{sbindir}/crm_master 
%{sbindir}/crm_standby
%{sbindir}/crm_attribute 
%{sbindir}/crm_resource
%{sbindir}/crm_verify
%{sbindir}/attrd_updater
%{sbindir}/crm_failcount
%{sbindir}/crm_sh
%{sbindir}/ha_logger
%dir %attr (755, %{HA_CCMUSER}, %{HA_APIGROUP}) %{HA_VARRUNDIR}/ccm
%dir %attr (750, %{HA_CCMUSER}, %{HA_APIGROUP}) %{HA_VARRUNDIR}/crm
%dir %attr (750, %{HA_CCMUSER}, %{HA_APIGROUP}) %{localstatedir}/lib/%{HB_PKG}/crm
%dir %attr (750, %{HA_CCMUSER}, %{HA_APIGROUP}) %{localstatedir}/lib/%{HB_PKG}/pengine
%doc %{mandir}/man1/cl_status.1*
%doc %{mandir}/man1/ha_logger.1*
%doc %{mandir}/man1/hb_standby.1*
%doc %{mandir}/man1/hb_takeover.1*
%doc %{mandir}/man1/hb_addnode.1*
%doc %{mandir}/man1/hb_delnode.1*
%doc %{mandir}/man8/crm_resource.8*
%doc %{mandir}/man8/heartbeat.8*
%doc %{mandir}/man8/apphbd.8*
%doc %{mandir}/man8/ha_logd.8*
%doc %{mandir}/man8/cibadmin.8*
%doc %{docdir}
%if %{ENABLE_SNMP_SUBAGENT}
	%{MIBS_DIR}/LINUX-HA-MIB.mib
%endif
%if %{ENABLE_MGMT}
	%{libdir}/libhbmgmt.*
	%{libdir}/libhbmgmtclient.*
	%{libdir}/libhbmgmtcommon.*
	%{libdir}/libhbmgmttls.*
	%{PAMDIR}/hbmgmtd
	%exclude %{share}/heartbeat-gui
	%exclude %{libdir}/heartbeat-gui
%endif

%if %{ENABLE_MGMT}
###########################################################
# Files for the gui
%if %{GUI_PACKAGE}
%files -f haclient.lang -n %{GUI_NAME}
%endif
###########################################################
%defattr(-,root,root)
%{libdir}/heartbeat-gui
%{share}/heartbeat-gui
%{bindir}/hb_gui
%endif

###########################################################
# Files for ldirectord
%files -n %{LDIR_NAME}
###########################################################
%defattr(-,root,root)
%{sbindir}/ldirectord
%{sysconfdir}/logrotate.d/ldirectord
%{INITDIR}/ldirectord
%{HA_D_DIR}/resource.d/ldirectord
%{OCF_RA_DIR}/heartbeat/ldirectord
%doc %{mandir}/man8/ldirectord.8*
%doc ldirectord/ldirectord.cf

###########################################################
# Files for devel package
%files -n %{DEVEL_NAME}
###########################################################
%defattr(-,root,root)
%{base_includedir}/heartbeat/
%{base_includedir}/clplumbing/
%{base_includedir}/saf/
%{base_includedir}/ocf/
%{base_includedir}/stonith/
%{base_includedir}/pils/
%{libdir}/libapphb.so
%{libdir}/libccmclient.so
%{libdir}/libcib.so
%{libdir}/libclm.so
%{libdir}/libcrmcommon.so
%{libdir}/libtransitioner.so
%{libdir}/libhbclient.so
%{libdir}/liblrm.so
%{libdir}/libpengine.so
%{libdir}/libplumb.so
%{libdir}/libplumbgpl.so
%{libdir}/librecoverymgr.so
%{libdir}/libstonithd.so
%{libdir}/libpe_rules.so
%{libdir}/libpe_status.so
%exclude %{libdir}/libapphb.la
%exclude %{libdir}/libccmclient.la
%exclude %{libdir}/libcib.la
%exclude %{libdir}/libclm.la
%exclude %{libdir}/libcrmcommon.la
%exclude %{libdir}/libtransitioner.la
%exclude %{libdir}/libhbclient.la
%exclude %{libdir}/liblrm.la
%exclude %{libdir}/libpengine.la
%exclude %{libdir}/libplumb.la
%exclude %{libdir}/libplumbgpl.la
%exclude %{libdir}/librecoverymgr.la
%exclude %{libdir}/libstonithd.la
%exclude %{libdir}/libpe_rules.la
%exclude %{libdir}/libpe_status.la
%exclude %{libdir}/libapphb.a
%exclude %{libdir}/libccmclient.a
%exclude %{libdir}/libcib.a
%exclude %{libdir}/libclm.a
%exclude %{libdir}/libcrmcommon.a
%exclude %{libdir}/libtransitioner.a
%exclude %{libdir}/libhbclient.a
%exclude %{libdir}/liblrm.a
%exclude %{libdir}/libpengine.a
%exclude %{libdir}/libplumb.a
%exclude %{libdir}/libplumbgpl.a
%exclude %{libdir}/librecoverymgr.a
%exclude %{libdir}/libstonithd.a
%exclude %{libdir}/libpe_rules.a
%exclude %{libdir}/libpe_status.a

###########################################################
# Files for the stonith library
%files -n %{STONITH_NAME}
###########################################################
%defattr(-,root,root)
%{stonith_includedir}
%{libdir}/libstonith.*
%{libdir}/stonith
%{sbindir}/stonith
%{sbindir}/meatclient
%doc %{mandir}/man8/stonith.8*
%doc %{mandir}/man8/meatclient.8*

###########################################################
# Files for the PILS library
%files -n %{PILS_NAME}
###########################################################
%defattr(-,root,root)
%{pils_includedir}
%{libdir}/libpils.*
%{pils_plugindir}

###########################################################
%clean
###########################################################
if
  [ -n "${RPM_BUILD_ROOT}"  -a "${RPM_BUILD_ROOT}" != "/" ]
then
  rm -rf $RPM_BUILD_ROOT
fi
rm -rf $RPM_BUILD_DIR/%{HB_PKG}-%{HB_VERSION}

###########################################################
%pre
###########################################################
# We made some directories into symlinks
# RPM won't update them correctly
for j in %{HA_LIBHBDIR}/cts %{HA_LIBHBDIR}/lrmtest %{HA_LIBHBDIR}/stonithdtest
do test -d $j &&  rm -fr $j; done
#
#	This isn't perfect.  But getting every distribution
#	to agree on group id's seems hard to me :-(
#
if
  getent group %{HA_APIGROUP} >/dev/null
then
  : OK group %{HA_APIGROUP} already present
else
  GROUPOPT="-g %{HA_APIGID}"
  if
    /usr/sbin/groupadd $GROUPOPT %{HA_APIGROUP} 2>/dev/null
  then
    : OK we were able to add group %{HA_APIGROUP}
  else
    /usr/sbin/groupadd %{HA_APIGROUP}
  fi
fi

if
  getent passwd %{HA_CCMUSER} >/dev/null
then
  : OK user %{HA_CCMUSER} already present
else
  USEROPT="-g %{HA_APIGROUP} -u %{HA_CCMUID} -d %{HA_COREDIR}/%{HA_CCMUSER}"
  if
    /usr/sbin/useradd $USEROPT %{HA_CCMUSER} 2>/dev/null \
    || /usr/sbin/useradd -M $USEROPT %{HA_CCMUSER} 2>/dev/null
    # -M to suppress creation of home directory on Red Hat
  then
    : OK we were able to add user %{HA_CCMUSER}
  else
    /usr/sbin/useradd %{HA_CCMUSER}
  fi
fi

###########################################################
%post
###########################################################
true
###########################################################
%preun
###########################################################
true
###########################################################
%postun
###########################################################
true
###########################################################
%changelog
* Fri Dec 21 2007  Alan Robertson <alanr@unix.sh> and MANY others (see doc/AUTHORS file)
+ Version 2.1.3 - bug fixes and enhancements - changelog includes everything after 2.1.2
  + hb_report: heartbeat reporting utility
  + ciblint: new tool to lint a CIB
  + snmp subagent: support for crm
  + RA iscsi: new OCF resource agent (FATE 301250)
  + RA SphinxSearchDaemon: new OCF resource agent
  + RA tomcat: a new OCF agent
  + RA ids: a new Informix OCF resource agent
  + stonith ipmi: new external stonith plugin
  + stonith ibmrsa-telnet: new external stonith plugin
  + Xen RA: new features (memory mgmt, DomU monitor hook)
  + Debian: add libxml2-utils as a dependancy: we need xmllint for the BSC
  + pgsql RA: postmaster confusion
  + apache RA: remove children in case the top process didn't
  + ldirectord: add forking mode
  + ldirectord: Various updates to OCF compatible RA
  + ccm (LF 1806): restart all instead of exiting (low impact)
  + High: Heartbeat: Include an option to start the CRM in respawn mode
  + dopd: make it work with multiple concurrent outdate requests
  + dopd: don't hardcode path of drbdadm; it has to be in the PATH, though.
  + dopd: fix potential segfault due to leakage of invalid/freed pointer
  + LF bug 1795 - timeout control for crm_mon --one-shot
  + CTS - if we can't get all the nodes running again, call an external script
  + fix a problem building on Red Hat with tog-pegasus installed
  + pgsql RA: handle the missing pg software properly
  + LF bugzilla 1667:  ppc64 RPMs contain 32-bit binaries
  + mgmt: Translations for the new parameters of pengine
  + mgmt: Remove the default settings for master_slave from attlist
  + mgmt: Bugfix: Error caused by blank description of parameter
  + mgmt (LF 1724): Prevent saved login information from being corrupted
  + add bzip2-devel as a build dependency for Fedora and RH
  + fixes for fedora: system(3) function return value cannot be ignored
  + Filesystem: Make mount point required for the GUI
  + dopd: don't cl_free variables on local stack
  + build (LF 1803): add -fgnu89-inline to CFLAGS if gcc version is >=4.1.3 and <4.3
  + haresources2cib.py: set default-action-timeout to the default (20s)
  + pgsql RA: move check for root down to enable meta-data for regular users
  + LF 1678: stonith command core dumps with -h option
  + haresources2cib.py: update ra parameters lists
  + Low: lrmd: Make the -r option the default behavior
  + OpenBSD bugs: 1731 1761 1743 1659
  + CTS: changed a test from causing a reboot to not triggering a reboot
  + CTS: increased timeouts and made the stonithd test use the livedangerously option
  + RPM specfile change:  made is_fedora macro turn off is_rhel macro
  + Corrected a warning found on FC8 in the cl_reboot code
  + LF 1794: Modified the external/ssh plugin to have a livedangerously flag
  + LF 1794: external/ssh should first check if the host is reachable
  + RA Filesystem: add lustre to the list of fs which don't need fsck
  + ldirectord: SimpleTCP service check documentation
  + ldirectord: SimpleTCP service check
  + LF Bug 1732: Error handling is bad for comm media
  + High: cib: Make sure everyone uses (add|get)_message_xml() for data fields
  + RA SAPDatabase/SAPInstance: report proper exit codes in case required software is not installed
  + RA mysql: don't look for mysql users in the OS database
  + High: CRM: Compressed XML needs to be retrieved as a binary blob, not a string
  + High: CRM: Future-proof get_message_xml()
  + High: GUI: Fix compilation after changes to update_attr() form the CIB
  + Low: TE: Logging - unconfirmed actions can happen under normal conditions
  + High: heartbeat: Fix getnodes() compilation with gcc 4.3
  + Medium: PE: Create a syntactic shortcut for the common use-case of "{resource} prefers {node} with {score}"
  + High: CIB: Fix the behavior of update_attr() and delete_attr() when the command is ambiguous
  + ipc (LF 1339): enable message compression
  + Changed HIGHLY to STRONGLY in how strongly we recommend STONITH
  + LF bug 1690: there should be a tool to audit (validate) node names in constraints among other things...
  + Low: clplumbing: Fix log message:  size_t != int on 64-bit arch's
  + Low: Admin: crm_standby - Don't complain abot missing values, print the default value instead
  + Low: PE: Update the expected graphs to include the batch-limit option
  + Medium: TE: Allow the CRM to limit the number of resource actions the TE can execute in parallel.
  + Low: crmd: Provide a more informative error when DCs detect other DCs during a join
  + Low: CTS: The Process class requries an integer for triggersreboot
  + High: CRM: In ccm_have_quorum(), an OC_EV_MS_PRIMARY_RESTORED event means we _do_ have quorum
  + Low: crmd: Cleanup - remove all 'return I_NULL' statements from the FSA
  + High: PE: Set next_role recursivly so that group promotion will work
  + High: PE: Introduce a new API call for determining the location of complex resources
  + Medium: PE: Dont make changes to location constraints, when applying to groups, persistent
  + High: crmd: Prevent shutdown hangs caused by pending ops that can't be cancelled - because the no longer exist in the lrm
  + Medium: Do not disconnect blocking write processes, but discard traffic.
  + Novell 293922: Don't use non-blocking writers, but instead don't block
  + Changed the version of RHEL requiring OpenHPI to be 6 or greater...
  + LF Bug 1662: Put in some RHEL changes provided by Keisuke MORI
  + LF bug 1662: PM spec file should be more usable (Fedora changes)
  + Medium: crm: Dont generate core files for non-fatal assert (ie. the CRM_CHECK macro).
  + Low: PE: ptest - Handle malformed inputs more gracefully
  + Low: crmd: Minor logging improvement to update_dc()
  + Low: crm: Handle a few xml-related error conditions without resorting to CRM_ASSERT
  + Low: Admin: Do a full simulation when we have the live CIB - since we'll always have a status section
  + High: PE: Fix a botched commit (cs: 3de5760b06e0) that incorrectly allowed resources to start without quorum or stonith
  + Medium: PE: Disable delete-then-refresh code.  The crmd will remove the resource from the CIB itself making the refresh redundant
  + Medium: PE: All other things being equal, prefer to keep non-failed instances alive
  + Medium: attrd: Bug 1776 - Attrd doesn't exit or reconnect when the CIB is respawned
  + Low: PE: Actions for stonith agents should never default to requiring fencing or quorum
  + High: PE: increment_clone() did not overflow correctly 9->10, 99->100, etc
  + Medium: crmd: Don't remap LRM_OP_PENDING when building full lrm updates
  + Medium: TE: Pending operations shouldn't be processed
  + High: PE: Bug 1765 - Prevent master-master colocation constraints from preventing slaves from starting
  + Low: PE: Reduce logging severity regarding creation of notifications
  + Low: PE: Split the contraint unpacking code into its own file
  + hbagent: reset gMembershipTable on dropping global resources
  + hbagent: fix memory leaks on dropping global resources
  + hbclient: fix memory leaks on signon/signoff
  + RA Xinetd (LF 1742): multiple fixes
  + LRM regression test: make common.filter (sed) script work with non-gnu sed (Darwin)
  + LRM regression test: use LSB_RA_DIR instead of /etc/init.d
  + LF 1766: Heartbeat installs man pages in the wrong directories by default...
  + LF bug 1772: apphbd needs to be able to have clients declare themselves critical resulting in a "fast fail" of the system when they fail
  + debugging for LF bug 1393 - includes a bug fix for the postfork() callback in the GSource.c module for the tempproc trigger Gsource
date:        Fri Nov 09 06:54:25 2007 -0700
  + Put in simple debugging code for CCM negative uptime message - plus made some related code slighly safer.
  + HBcomm: use proper define (MSG_DONTWAIT instead of MSG_NONBLOCK)
  + Novell 293922: Heartbeat network processes would block on full buffers.
  + LF bug 1393 - Cannot rename /var/lib/heartbeat/hostcache.tmp to /var/lib/heartbeat/hostcache (scope, risk and severity: all minor)
  + Trying a different approach to get debug info for LF bug 1393 (low risk, important for debugging)
  + Added -p pidfile option to cl_respawn
  + LF bug 1706 (finishing up associated issues)
  + mgmtd (LF 1719): fix the pam file for suse
  + raised timeouts in CTS to account for a slow machine I own
  + LF bug 1705 - cl_respawn core dumps when given -h or --help
  + ccm: speed up ccm considerably in case a node is alone in the membership
  + LF bugzilla 1757: apache resource agent grep methodology can't handle newlines
  + Added debugging and very minor code improvements for LF bug 1393
  + mysql RA (LF 1760): defaults for OpenBSD
  + BSC (LRM test): replace cron with heartbeat as an lsb agent
  + CTS: changed the code to wait for nodes to come up before we try and get uuid list
  + changed configure.in to force 64-bit objects when on gcc-based ppc64 platform
  + Removed RPM dependency on sysklogd - because package name can vary
  + Moved python gtk dependencies into GUI package
  + ccm (LF 1546): ensure that the membership instance number never decrements
  + stonithd: check for storage size when copying the host list
  + stonithd (LF 1727): shuffle dropping privileges around again
  + [LDIRECTORD] allow per-virtual checkinterval configuration
  + stonithd: drop root privileges earlier
  + Debian: rename ha_logd.cf to logd.cf in debian/heartbeat.files
  + stonithd (LF 1727): fix dropping privileges
  + Low: heartbeat: Use the correct define when choosing to enable valgrind
  + Medium: crmd: Prevent shutdowns initiated immediately after a node is removed from the cluster with hb_delnode from stalling.
  + [DEBIAN] Add dependacy on gawk as it is required by the OCF IPaddr resource
  + [lvs-users] Patch for ldirectord when using mysql service
  + Low: Fix Makefile.am reference (ha_logd.cf -> logd.cf)
  + Low: Rename example ha_logd.cf file to the proper name.
  + Low: cib: Increase the retry interval when connecting to the ccm to 3s
  + Low: cts: Remove the backup CIB too if --clobber-cib is specified
  + Medium: crmd: Bug 1737 - Inconsistent join state detected - Possible fix
  + High: cib: G_main_del_IPC_Channel() doesn't like being called with a NULL pointer and crashes
  + Low: Fix compile of mgmtd (fixes cs 575ceac23368)
  + Medium: mgmt: Use the new bit-field for resource_t objects
  + Low: cib: Set callback_source=NULL after call to G_main_del_IPC_Channel()
  + Low: crm: Reduce severity of digest mismatch message in apply_xml_diff
  + High: crm: Bug 1749 - Make sure the diff-related digests contain the complete CIB, not just the first line
  + Low: PE: Convert all the resource's boolean flags into a single bit-set
  + ccm (LF 1723): fix logging
  + lrmd (LF 1729): revise return codes
  + Low: heartbeat: Some compilers feel that the fcli variable could be used uninitialized - shut them up
  + Low: core: proctrack - Tweak some log messages to be of a similar form to those in heartbeat.c
  + High: PE: Bug 1712 - Ensure manditory ordering constraints can cause complex resources to be shut down
  + Low: cts: Remove patterns that are no longer of interest
  + Medium: Tools: Bug 1738 - the crmd ignores some requests from crm_resource because it exited too quickly
  + Low: PE: Reduce log priority for some development logging
  + Low: cts: Remove erroneous search pattern from component fail test
  + Low: crmd: Use the unaltered rc for timed out operation events from the lrmd
  + Low: Build: Make sure make clean works in the cts directory
  + Medium: cib: Include digests of the cib a diff was made from and verify it when applying
  + High: PE: Prevent use-of-NULL when the admin creates a colocaiton constraint with an empty group
  + LF bug 1712: ha_logd prevented node from shutting down - changed code to use the waitout() primitive
  + Put in a missing include of <memory.h> for the DRBD code
  + LF bug 1700: HA Signon always reports success
  + rpm build change: allow openhpi to be optional, but default it to be required.  Don't require it for SUSE < 10.2
  + stonithd (LF 1727): change attach shmem seg to read only
  + Low: cts: Add a missing comma to the patterns list
  + Low: crmd: Use EXECRA_OK instead of hard-coding rc=0
  + Low: crmd: Increase the retry interval when stalling the FSA to 2s (used when connecting to the ccm, lrmd, cib)
  + Low: crmd: Remove code made redundant by the use of ProcTrack
  + Low: cts: Wait for the cluster to see the node come back before checking for S_IDLE after shooting the ccm.
  + Low: cts: Add an extra ignore pattern for stonithd
  + Low: cts: NearQuorumPoint - only check for Pat:DC_IDLE if there will be nodes up at the end
  + Low: PE: Produce a config error when a clone contains more than one resource/group to clone
  + Low: RA: PureFTPd - Support debian's pure-ftpd-wrapper script
  + Medium: Tools: ocf-tester - Ensure OCF_ROOT is available to the RA subshell
  + Low: contrib: dopd - Remove a pointless and annoying dependancy on the crm
  + Low: TE: Code cleanup
  + stonithd: improve logging
  + LF bug 1502: udpport statement in ha.cf is ignored by heartbeat
  + LF bug 1589: ia64 heartbeat unaligned access messages (SGI965396) - copy fields in structures
  + LF bug 1679: hardcoded heartbeat userid and group in init script
  + LF bug 1681: BSC fails to identify active interface on OpenBSD
  + LF bug 1702: during emergency restarts, heartbeat doesn't close watchdog correctly
  + Updated a specfile dependency to require the minimum version of openhpi
  + LF bug 1734 - removed duplicate return statement as per bug report.
  + LF bug 1731: wrong location of libraries for OpenBSD 64Bit architectures
  + High: crmd: Prevent shutdown hangs by allowing the crmd to forget about pending actions for deleted resources
  + High: PE: Relax an assumption regarding clones that is not true when they are unmanaged
  + Medium: PE: Bug 1722 - By default, exhibit the old start-failures-are-fatal behaviour regardless of how resource-failure-stickines is set
  + Remove one unlink() of the temporary hostcache file.
  + hb_uuid: Remove superfluous sync().
  + STONITH: external/ssh: Disable StrictHostKeyChecking and PasswordAuthentication by default.
  + RA: mysql: Allow arbitrary commandline arguments for mysqld
  + CTS: patterns adjusted for exiting processes (LF 1725).
  + High: PE: Prevent an infinit pe/te loop when reprobing with resources in master mode
  + mgmt: Provide "Default" setting for crm configurations
  + mgmt: Provide complete pengine and crmd configurations with dynamic rendering
  + mgmt: Prevent haclient from falling into an error caused by blank resource metadata
  + mgmt: Add "meta_attributes" support to mgmt
  + mgmt: Resolve target_role problem for sub-resource
  + High: PE: Prevent use of NULL in crm_mon when date_expressions are used by ensuring that data_set->now is always set
  + PE: High: Remove an errant call to exit() than prevented an assert from being triggered
  + Low: Build: Remove unused LDADD entries (libpils.la and libapphb.la)
  + High: PE: Clone colocation fixes
  + Low: PE: Extra debug information
  + Low: PE: Avoid pointless copying of XML items (actions) during graph creation
  + Low: PE: Log the current cluster state at LOG_NOTICE instead of LOG_INFO
  + Medium: PE: Master internal ordering enhancements. Added stopped->start, stopped->promote.
  + Medium: PE: Make sure all slaves (not just re-allocated ones) have role=Slave
  + Medium: PE: Fix minor memory leak when stopping orphaned resources
  + Medium: CRM: Re-evaluate appropriate IPC message queue lengths and throtle IPC _clients_ that hit them
  + High: PE: Missing header file change from previous commit (cs: 0c14cfe57dd9)
  + High: PE: Ensure that resources depending (by order) on a master are not promoted if no master is available
  + Low: PE: Update regression tests - some action numbers changed
  + Low: Tools: crm_resource - send errors to stderr and to regular logging
  + Medium: DTD: Fix comment regarding rsc_ordering constraints
  + High: PE: Fix manditory ordering with m/s resources
  + Low: PE: clones - Remove debug logging and simplify asserts in expand_list()
  + Low: crmd: Update the CIB with the node's version data when it becomes DC
  + mgmt: Prevent clone and master_slave from belonging to group
  + mgmt: Make several fields of rsc_location editable
  + mgmt: Rename "Places" to "Locations" to match with the CIB name
  + mgmt: Specify the default type of added item to correspond to the object that the cursor focused on
  + mgmt: Add boolean_op for location rules in mgmt
  + RA mysql, pgsql: use getent(1) instead of /etc/passwd
  + stonithd (LF 1714,1727): fix a race condition
  + stonithd (LF 1726): a hostlist may be empty
  + stonith/ibmrsa: allow ',' in the hostlist
  + RA: Xinetd: Fix stop/monitor to not fail if service isn't available yet
  + CTS: Fix a path reference to LSBDummy, so that CTS has a chance of working.
  + RA: Raid1: Allow the homehost setting to be specified.
  + Novell 329833: dotted-quad netmask notation broken in findif
  + lrm stonith plugin: fix exit code handling
  + stonith/external: improve logging
  + stonithd/lib: replace cookie generation with uuid
  + stonithd: code review and cleanup
  + LRM test: test xml of stonith agents through stonithd (included in the BSC)
  + stonithd: have -a really mean startup alone
  + Low: Stonith: external/rackpdu - Fix the metadata short descriptions
  + cl_msg: fix a typo
  + stonithd: library code review and cleanup
  + stonithd: increase the maxdispatchtime
  + Debian: heartbeat doesn't depend on libperl-dev
  + lrmd (LF 1715): increase the max dispatch time for lrmd
  + Corrected spelling/grammar errors in BasicSanityCheck
  + Medium: PE: Enact a saner default for rsc_order.score (s/0/INFINITY)
  + High: PE: More generic method of detecting colocation loops in native_merge_weights
  + Medium: Logging: Sanitize and centrally define the log facility used by various subsystems
  + Low: Build: Build the contrib directory last
  + Low: cts: Fix the log facility map
  + Low: CRM: Key of the already set debug_level global variable when setting crm_log_level
  + Low: CRM: Downgrade digest logging now that its under control
  + Low: cib: Logging - version message should not have been an error
  + Low: PE: Logging - Include the transition_magic key when logging changed parameters
  + Low: CTS: Add extra ignore pattern when the CCM is shot - do it properly this time
  + Medium: Core: Ensure heartbeat flushes all its logs before exiting
  + Low: TE: Pause for a moment before trying to reconnect to stonithd
  + Medium: cib: Improved transparency when in operating in degraded mode
  + Low: crmd: Remove redundant code
  + Low: CTS: Add extra ignore pattern when the CCM is shot
  + Low: CTS: Add BadNews pattern - parameters should never change
  + Low: Admin: crmadmin - Logging tweak
  + Low: PE: More efficient logging of orphan resources
  + Medium: PE: Bug 1710 - A resource's failcount was ignored on nodes with no operations for the resource
  + LRM test: various cleanups
  + Added a script for creating the configuration for a single node
  + Low: PE: Prevent users from trying to use on_fail=fence and stonith-enabled=false
  + Low: CIB: Allow notification to remote clients
  + Low: PE: Downgrade logging when we fallback to default option values
  + High: Core: Prevent logging buffer overflow - ensure the entity is NULL terminated
  + High: PE: Make sure only the correct number of cloned groups are started
  + Low: PE: Stop the master placement score from affecting the synapse's priority
  + High: PE: Include preferences of colocated resources when promoting masters
  + High: RA: Remove bashism from Filesystem OCF agent
  + Low: CTS: Limit the number of PE input files created
  + Low: DTD: Include helpful comment for rsc_order constraints
  + Medium: PE: Bug #1705 - Don't segfault when allocating empty groups
  + Low: Stonith: external/ssh - simplify the reset command and wait the same amount of time as the non-external variant
  + Medium: RA: Treat migrating (status 1) as running to avoid
  + Low: Tools: Allow pingd to change identity based on the name of its executable - workaround for Bug #1701
  + High: PE: Ensure manditory ordering constraints behave correctly
  + proctrack/LRM (LF 1697): really remove sources (performance/memory leak fix)
  + mgmtd: allow old clients to connect
  + Low: PE: Regression test for group colocation
  + Medium: PE: Simplify the allocation of group resources
  + High: PE: Optimize the merge_weights functionfor groups
  + High: PE: Make sure the merge_weights function is called for complex resources
  + High: PE: More accurate method of detecting colocation loops in native_merge_weights
  + High: PE: Implement a smarter algorithm for colocation
  + Low: PE: Fold child-loop functions back into the ones doing the actual work
  + Medium: PE: Expose rsc->children which should mean we can delete all the 'loop' functions for complex objects
  + LRM test: report findings if the tests failed
  + RA: Filesystem: VARLIB -> RSCTMP
  + RA: Filesystem: Fix path reference.
  + Move INITDIR to proper include.
  + RA: o2cb: Fix path broken in recent "cleanups".
  + LRM test: include parts of lrm regression testing in the BasicSanityCheck
  + raexecocf: include time.h
  + lrmd: log non-recurring operations
  + lrmd: wrong reference in one debug message
  + stonithd (LF 1615): get the list of hosts from an RA asynchronously
  + High: crmd: Tell the LRM to refresh the resource's default parameters
  + LRM: add capability to copy parameters from op to rsc
  + raexecocf: a fix for bug introduced in 2a787bbd73f6; longer sleep in get_resource_meta
  + Medium: Stonith: prevent superfluous logging
  + High: DTD: Remove stary character that made the DTD invalid
  + Low: Admin: Bug 1691 - crm_resource doesn't complain about empty strings as property values
  + Low: CRM: DTD - Explicitly specify a default for rsc_colocation.symmetrical
  + Low: CRM: DTD - Expand the list of accepted values for boolean fields
  + Low: RA: ManageVE - Fix status when VE files are not persistent
  + lrmd: performance 2: remove unnecessary memstat
  + lrmd: performance 1: replace linear with binary search for msg type.
  + Corrected a directory name in the '%pre' script in the spec file
  + RA apache: drop annoying messages if no configuration files are found
  + Changed the specfile so that it uses only the correct name for python/gtk package according to the distro
  + [LDIRECTORD] Remove supervise-ldirectord-config
  + specfile: converted %elseif chains to %endif %if
  + apache RA (LF 1692): move sourcing /resource.d/heartbeat/.ocf-shellfuncs before var reference
  + detect fedora correctly
  + a number of small fixes to make fedora packages correctly
  + Put in an APCmastersnmp.c patch from Peter Kruse which makes the plugin work with new APC master switches
  + LRM (LF 1684): a meta-data operation fix introducing short sleep on zero reads
  + configure.in: fix for platforms with libc in /lib/tls
  + Updated arguments to crm_log_init to be consistent with new API.
  + LF bug # 1662 - massive heartbeat specfile update - to make it more usable
  + Medium: RA: EvmsSCC - Handle start failures caused by peers starting at the same time
  + Low: logd: Update the default config file to reflect the new default log facility
  + High: clplumbing: Use the correct environment variable when deciding to log via ha_logd
  + Low: Admin: crmadmin - exit with rc=0 when the command completed successfully
  + Medium: PE: Bug 1685 - Supply the correct default for rsc_order constraints
  + Low: PE: Fix a parse error in the attr8 regression test
  + High: TE: target_rc should default to 0 (LRM_OP_DONE) to detect monitor actions that fail the first time they are executed
  + High: PE: Bug 1682 - Prevent use-of-NULL when clones have no active children
  + [STONITH] Disable ipmilan by default
  + [STONITH] ipmilan: fix potential segvfault in options parsing
  + [RA] patch to fix bashism in resources/OCF/pgsql
  + LRM (LF 1458): include timing information in the op data.
  + RA: eDir88: fix to allow meta-data to work in case NDS is not installed
  + Put in updates to the Informix script as supplied by Lars Forseth
  + An open call with the O_CREAT flag was missing the file mode.
  + High: crmd: Sanitize the maintenance of node_state entries
  + High: cib: Support the removal of multiple child objects - required for subsequent commit
  + Low: cts: 'Updating failcount for' is no longer worth tracking (action failures show up as other ERROR logs)
  + Low: TE: Improved logging of unconfirmed actions
  + Medium: TE: Dont modify the failcount for 'pending' action updates (rc=-1)
  + Medium: admin: Set the exit code to non-zero if crmadmin can't connect to the crmd
  + High: PE: Break graph loops involving stonith + regression test
  + Low: PE: Improvements to the graph and .dot creation code
  + Medium: crm: Bug 1680 - parse_xml() can fail to detect mismatching close tags
  + High: PE: all_stopped should only depend on native resources to avoid recursion
  + High: PE: The all_stopped action should only be part of the graph when the stop actions are runnable
  + High: PE: Only create _one_ pseudo op per name (all_stopped/stonith_up)
  + Low: PE: Logging of changed resource definition
  + High: TE: Allow reconnection to stonithd if it is respawned
  + High: stonithd: Sanitize the login/logout functions and add the ability to reset the callback IPC channel
  + [STONITH] ipmilan: accept documented auth and priv values
  + [BUILD] don't remove tarbals in clean target
  + [BUILD] don't ignore errors on install
  + [RA] patch to fix bashism in heartbeat/lib/hb_setsite.in
  + [RA] patch to fix bashism in resources/OCF/pgsql
  + [RA] patch to fix bashism in resources/OCF/o2cb
  + [RA] patch to fix bashism in heartbeat/lib/hb_setweight.in
  + [RA] patch to fix bashism in heartbeat/lib/hb_setsite.in
  + [RA] patch to fix bashism in heartbeat/lib/hb_delnode.in
  + [RA] patch to fix bashism in heartbeat/lib/hb_addnode.in
  + [RA] patch to fix bashism in resources/OCF/eDir
  + [RA] patch to fix bashism in resources/OCF/SysInfo
  + [RA] patch to fix bashism in resources/OCF/Stateful
  + [RA] patch to fix bashism in heartbeat/lib/LRMBasicSanityCheck.in
  + hbagent: add partial configuration
  + tools: ocf-tester: add capability to test with lrmadmin/lrmd
  + Low: PE: Handle the 'fail' task in text2task()
  + Medium: PE: Dont check the parameter digest of orphan operations
  + Low: PE: ptest - dont execute the graph by default
  + High: PE: check_action_definition() - Ensure the meta attributes are also set so that the digest is calculated correctly (and consistently with the crmd)
  + High: CRM: filter_action_parameters() - Make a copy of interval/timeout in as they're about to be free'd
  + Low: PE: Update expected outputs with new version number
  + Low: PE: Warn when multiple nodes have the same uname
  + Low: cib: Refactor reading and writing of the CIB to disk
  + Medium: cib: Ensure fflush() and fsync() are always called when writing XML digests to disk
  + Medium: CRM: Ensure fflush() and fsync() are always called when writing XML to disk
  + High: cib: Allow the CIB to reconnect if the CCM is killed and respawned
  + High: cib: Handle master updates that fail DTD validation
  + High: TE: Allow the TE to reconnect if stonithd is killed and respawned
  + Low: cts: ResourceRecover - Match the interval to that used by crm_resource
  + Low: Stonith: New external plugin for handling 'APC Switched Rack PDU AP7952' devices
  + [DEBIAN] make heartbeat binNMU safe
  + LOW: cts: Remove unneeded argument for DC_IDLE pattern
  + Low: cib: Enhancements to logging of DTD errors
  + Low: cib: Rearrange so code to avoid excessive indenting
  + Low: PE: Correct spelling in log message
  + Low: crm: Let the caller decide how to log DTD validation failures
  + Low: crmd: Ensure our assumption that all resources have a class and type is true
  + Low: cts: Update the expected log patterns and remove dups
  + Low: cts: Resurrect the ComponentFail test
  + Low: cts: make cluster_stable() more informative
  + High: crmd: Simplify node_state maintenance
  + High: CIB: Improved CCM interaction
  + Low: CIB: Minor logging improvement
  + High: crmd: Improvements to shutdown sequence (particularly in response to failures)
  + CTS: Low: Ignore the correct BadNews message in ResourceRecover
  + CTS: Low: Tell NearQuorumPointTest to look for Pat:DC_IDLE before declaring success
  + CTS: Low: Optimize filtering of BadNews
  + Admin: Low: Bug 1603 - Allow CIB digest files to be verified
  + RA: apache - make status quieter
  + [RA] eDir88: include the stop option
  + OSDL bug 1666: in BSC, make sure temp rsc dir exists for RAs
  + Contrib: dopd - Fix usage of crm_log_init() by code that shouldn't be using it
  + Tools: ocf-tester - use the default value for OCF_ROOT if it exists
  + RA: IPaddr2 - Make the check for the modprobe/iptables utilities conditional on the IP being cloned
  + CRM: Update crm/cib feature sets and the set of tags/attributes used for feature set detection
  + crmd: Simplify the detection of active actions and resources at shutdown
  + PE: Use failcount to handle failed stops and starts
  + TE: Set failcount to INFINITY for resources that fail to start or stop
  + CRM: Remove debug code that should not have been committed
  + PE: Add regression test for previous commit
  + PE: Regression: Allow M/S resources to be promoted based solely on rsc_location constraints
  + PE: Fix up the tests now that compare_version() functions correctly (as of cs: 7d69ef94a258)
  + CRM: Fix compare_version() to actually work correctly on a regular basis
  + PE: Update testcases to include all_stopped (added in cs: 800c2fec24ee)
  + crmd: Bug 1655 - crmd can't exit when the PE or TE is killed from underneath it
  + Tools: Bug 1653 - Misc attrd/attrd_updater cleanups
  + Tools: Bug 1653 - Further changes to prevent use of NULL when no attribute is specified
  + CRM: Make logging setup consistent and do not log the command-line to stderr
  + RA: Delay (v1) - Remove extra characters from call to ra_execocf
  + Tools: Bug 1653 - attrd crashes when no attribute is specified
  + OCF: Provide the location of /sbin as used by some agents (HA_SBIN_DIR)
  + PE: Move the creation of stonith shutdown constraints to native_internal_constraints()
  + crmd: Only remap monitor operation status to LRM_OP_DONE under the correct conditions
  + PE: Handle two new actions in text2task
  + CTS: Give stonith devices penty of time to start
  + PE: Include description for the remove-after-stop option
  + PE: Streamline STONITH ordering. Make sure 'all_stopped' depends on all STONITH ops.
  + PE: Aggregate the startup of fencing resources into a stonith_up pseudo-action
  + PE: STONITH Shutdown ordering
  + Bugzilla 1657: Speed up BasicSanityCheck and also make logging inheritance more uniform.
  + OSDL 1449 / Novell 291749: GUI should not overwrite more specific settings of contained resources.
  + Remove autoconf and friends on make distclean

* Mon Jul 30 2007  Alan Robertson <alanr@unix.sh> and MANY others (see doc/AUTHORS file)
+ Version 2.1.2 - packaging changes and a small number of small bug fixes
  + fixed the packaging errors in 2.1.1
  + fixed a bug which caused CIDR netmasks in IPaddr to be ignored - fatal for some R1 configs
  + fixed a bug which kept ipv6addr from being compiled in RHEL4
  + fixed a bug which kept configure from working in Debian
* Mon Jul 23 2007  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.1.1 - bug fixes and enhancements - changelog includes everything after 2.0.8
  + Added vmware STONITH script
  + Added Evmsd, eDir88, and o2cb resource agents
  +++++ OSDL / Linux Foundation bugzilla bugs +++++
  + OSDL bug 393 - Enable build of plugin if OpenHPI present
  + OSDL bug 393 - Update plugin from OpenHPI 2.2 to OpenHPI 2.6
  + OSDL bug 393 - Rename ibmbc to bladehpi
  + OSDL 761: Remove history from heartbeat init script.
  + LF Bug # 960 - rpm: first-time install fails
  + Tools: OSDL #1073 - Add clone support to crm_resource
  + LinuxFoundation bug 1138 - Long delay before CCM propagates membership event (partial fix)
  + Put debug in in support of bugzilla 1154: 2.0.4 BSC failure - select() returns with error
  + OSDL 1268: Fix trailing random byte in log messages (by Keisuke MORI)
  + OSDL 1292 - xSeries STONITH (IBM: 06-R212-175
  + RA apache: a major update (closes Bug 1357)
  + Tools: OSDL #1374 - Check for sane host names when migrating
  + OSDL 1389: Make mgmtd check protocol version on connect (Joachim
  + Stonith: OSDL #1428 - Mixing definitions and code
  + CIB: OSDL #1430 - Allow automatic assignment of object IDs
  + OSDL bug 1457 - Resolve unknown command ha_log
  + Tools: OSDL #1451 - Allow resource meta attributes to be set with crm_admin
  + clplumbing: Bug 1454 - Detect stale PID files where possible
  + Tools: OSDL #1462 - crm_migrate should allow creating temporary rules
  + crmd: Fix for OSDL #1465 - crmd gets stuck if shutdown while starting up
  + CIB: Apply patch for OSDL #1472 - Use-after-free in find_attr_details()
  + OSDL Bug 1482:  stonith command needs a repeat option to make it a better test tool
  + PE: OSDL #1484 - Repair on_fail=stop.  Patch courtesy of YAMAMOTO Takashi.
  + PE: Add a regression test for OSDL #1484 from Takashi YAMAMOTO
  + RA: db2 got new parameter: admin. Fixes Bug 1485.
  + PE: OSDL #1486 - Fix for potential NULL dereference
  + OSDL bug 1488 - Fix passing password to HMC
  + OSDL bug 1489 - Fix HMC errors in hostlist
  + PE: OSDL #1492 - Set common resource attributes before calling the custom unpack function
  + PE: OSDL #1494 - Add node->score to the clone stability function
  + PE: OSDL #1499 - Perform #uname comparisions without case
  + Attrd: OSDL #1500 - repeated call to attrd_updater with dampen absorbs attribute changes
  + Linux Foundation bug 1505: Findif parsing is all screwed up unless all the parameters are passed, not defaulted.
  + OSDL bug 1506 - Add optional plugin parameters to XML
  + OSDL bug 1507 - Allow "stonith -h" to display help for specific device
  + LF Bug 1511 LRM running two actions for the same resource parallel
  + LF Bug 1513 - building RPM from the 2.0.8 tarball fails
  + CCM (bug 1515): wrong function names in logging fixed
  + LF Bugzilla bug 1522: Strt hb_counter on time_t
  + OSDL bug 1523: Plugin performance enhancements
  + LF Bug 1527 - inappropriate warnings about core files logged by heartbeat (SGI961667)
  + Linux Foundation bug 1528: IPaddr2 gives a spurious warning on stop (SGI961736)
  + crmd: OSDL #1532 - Single node cluster shutdown
  + LF bug # 1534 - compiling/installation error on OpenBSD (partial fix?)
  + Fixed LF bug 1539: On Ubuntu, /var/run/heartbeat is missing after reboot (tmpfs)
  + Fixed LF bug 1540: MgmtGUI requires explicit port number when connectingi
  + fix bug 1544: 
  + OSDL bug 1545: stonithd signoff fixes
  + logging: a temp fix for bug 1548.
  + OSDL bug 1550: Suicide plugin returns hostlist containing itself
  + OSDL bug 1553: suicide plugin lacking ST_DEVICENAME
  + crmd: LF Bug #1554 - Wait for the membership to stabilize before starting transitions to prevent unconfirmed actions
  + PE: LF Bug #1554 - Probes should not have priority INFINITY
  + OSDL bug 1563: ssh STONITH plugin cleanup
  + Fixed LF bug 1564: cl_malloc doesn't return NULL on error
  + lrmadmin: skip non-numeric keys for lsb and heartbeat RAs (fixes bug 1571)
  + PE: LF Bug #1572 - Resource ordering not observed under some conditions - final
  + PE: LF Bug #1572 - Resource ordering not observed under some conditions - pt1
  + LRM: fix corrupt global structures (fixes Bugzilla 1574)
  + crmd: Bug #1575 - crmd cannot exit if lrmd is killed and there are pending ops
  + LF Bug 1576: shutdown hangs under certain shells
  + OSDL bug 1581 - no STONITH plugins found on Solaris10/i386
  + OSDL bug 1582: suicide STONITH plugin ignores nodename
  + PE: Bug 1580 - Remove logging inserted during developmental of fix for bug 1572
  + crmd: Bug #1584 - Always restart the join process when membership changes
  + LRM (bug 1585): check input from clients.
  + LRM: reschedule delayed ops (bug 1586).
  + LRM: handle lingering processes (fixes bug 1586)
  + LRM (bug 1594): change handling of cancel, resource delete, and flush ops requests.
  + LF Bug 1595: findif not being useful
  + Fixed LF bug 1597 int and long sizes are different on 64bit linux systems
  + Bug #1601 - PE: Favor correctness over niceties when STONITHing nodes
  + Bug #1602 - CIB: Try and load backup configuration if loading the main one fails
  + CIB: Bug 1602 - Archive invalid/unusable configurations so we can continue
  + OSDL bug 1606: okay for stonith plugins to have no parameters
  + Bugzilla Bug 1612 haresources2cib @substitution@ broken (probably by a global change)
  + Bug 1613 - stonith: convert long/short descriptions to xml.
  + LF Bug # 1617 - Miscellaneous RPM and source cleanups
  + Admin: Bug #1621 - crm_mon should show failed starts of a resource
  + Admin: bug #1622 - crm_attribute: Include --inhibit-policy-engine in the help message
  + crmd: Bug 1624 - Fix the delete op for cancelled operations
  + CRM: Bug 1625 - Cannot update an operation's timeout
  + PE: Bug 1628 - Complain about invalid operation intervals
  + RA: Bug #1630 IPaddr2 - Wrong arguments passed to send_arp (test was mistakenly written as an assignment)
  + Admin: Bug 1632 - Make sure error messages regarding trailing XML input characters are seen
  + CIB: Bug 1633 - Pass the actual error from activateCibXml back to the user
  + Admin: Bug 1635 - crm_failcount should not complain if the attribute was already deleted
  + LF Bug # 1644 - Pinging loopback in BasicSanityCheck fails with EPERM
  + LF bugzilla # 1645: Minimize arch-dependent differences, maintain compatibility
  + LF bug # 1650 - heartbeat should put scripts/non arch specific things in /usr/share
  + LF bug # 1656 - apache RA (LF 1656): include ServerRoot in relative paths.
  + LF bug # 1661 - crm_verify aborts checking and reoccurring crm_abort errors in logs
  + LF bug # 1665 - v1 config totally broken
  +++++ Novell bugzilla bugs +++++
  + RA: EvmsSCC: More fixes from Jo (Novell 199730)
  + PE: Novell #239079 - Ensure action priority is set correctly to ensure notifcations are not lost
  + PE: Novell #239082 - Order promotions after _all_ demotions have completed
  + PE: Novell #239086 - Stable Master placement
  + Admin: Novell #239075 - crm_master uses the same IDs for permanent and transient attributes
  + crmd: Novell #244444 - Free'ing g_alloc() data with cl_free()
  + PE: Novell #246681 - Teach NoRoleChange() how to migrate resource's in the master role
  + Novell bug 250207: SLES10 SP1 beta4 x86_64 problems with Heartbeat 2.0.8
  + RA: Filesystem: Move ocfs2_init out of the generic stop path (Novell 250603).
  + RA: Xen: Fix status function for newer Xen versions (Novell 250625)
  + RA: Novell #250273 - Provide an RA for managing evmsd as a resource
  + PE: Novell #251689 - Avoid needlessly restarting changed monitor operations for stopping resources
  + PE: Novell #252693 - Enable migration in more scenarios
  + PE: Novell #252693 - Teach the PE how to migrate resources in a starting stack
  + Stonith: Novell #266551 - getconfignames returned hostname instead of hostlist
  + doc: Novell #266551 - Bring the stonith man page up-to-date
  + Admin: Novell Bug #270977 - crm_resource ignores --meta in some situations
  + crmd: Novell Bug #286393 - Create resources, if necessary, in the lrmd so they can be stopped.
  +++++ Debian bugzilla bugs +++++
  + RA: Debian Bug #420206 - Bashisms in IPaddr2
  + [DEBIAN] Debian bug #432441 will be closed on the next upload
  +++++ Other changes +++++
  + CRM: Fix ISO date handling for Jan 01 of any year
  + CTS: Look for ha.d in the configured location
  + crmd:  Some more speedups for string comparisions and reload support improvements
  + Util: Fix a botched conversion from CRM_ASSERTs
  + CTS: Cleanup ResourceRecover
  + CTS: Logging change
  + TE: Remove dead code
  + crmd: Only update the voted hashtable with no-votes for the current election
  + Typos in comments and debug logs. (Sorry, I saw these during review and
  + crmd: crm_str_ -> safe_str_
  + Backed out changeset c38fb26a9497ab221688bfbfe6639eebcf29b0dd
  + crmd: add the required extra argument to crm_str_eq
  + crmd: Fix generation of FSA graphs
  + CTS: Explicitly test for the string "1" which means we have quorum
  + crmd: s/crm_str_neq/safe_str_neq/
  + build: Put header files into their correct subdirectories
  + RA: Some improvements to the mysql RA suggested by Achim Stumpf
  + clplumbing: fix compile error
  + PE: First cut at migrate support in _very_ limited situations
  + PE: More migrate code
  + PE: Final pieces of migration support
  + crmd: Make sure only current no-votes count towards election completion
  + DTD: Support the migrate_from value in rsc_op objects
  + crmd: Prepend CCM inputs to avoid a potential deadlock on startup
  + Core: Stop using the old ha_malloc macros for cl_malloc and friends
  + Hg: Update the list of ignored files/patterns
  + PE: Update the regression test outputs with new the feature set version
  + .cvsignore maintenance
  + RA: Fix apache metadata for consistancy
  + More .cvsignore updates
  + crmd: remove dead code from the lrm wrapper
  + PE: Tweak log message
  + CRM: Finalize support for migrate
  + RA: Support reload and migrate-(to|from) in the Dummy OCF agent
  + CTS: option logging improvements
  + CTS: Tweak v2 resource action interpretations
  + CTS: Cleanup CIB generation and add a migratable resource
  + Update comments related to the meaning of CCM callbacks
  + crmd: Correctly handle out-of-order CCM updates
  + Updated spec file in preparation for 2.0.8
  + BSC: LookForString already does grep -i. No need to specify "[Aa][Rr][Pp]"
  + PE: Add the PE part of reload support
  + BSC: Modified strategy for determining which interface to use
  + PE: Allow rsc_colocation constraints to be symmetrical
  + PE: Bug fixes and regression test for reload support
  + PE: No need to regenerate the param-4 outputs every time
  + PE: Fix small memory leak in reload support
  + PE: Make sure lrm_rsc_op IDs in regression tests are correct
  + PE: Add explanitory comment
  + CRM: Logging
  + build: Explicitly set state directory for Darwin in ConfigureMe
  + CTS: Remove unused import
  + BSC: Gracefully fail when python-xml is not available
  + PE: Allow migration and reload for children of complex resources
  + RA: Patch to pgsql.in from Serge Subrouski
  + RA: Patch to oracle agent from Dejan Muhamedagic
  + RA: Patch to allow ServeRAID to function in the real-world. From Jon Fanti.
  + Hg: Merge in RA patches from the community
  + Add migration support to Xen RA.
  + add configure option for the drbd outdate peer daemon
  + Added tag STABLE-2.0.8 for changeset 2d298bca0d0af320752bfa293ac96ed08e2c6463
  + Hg: Fix another botched update from Alan
  + RA: LVS support should always be enabled for the heartbeat IPaddr wrapper
  + Remove uninitialized variable warning on line 116.
  + RA: Xen: Swap migrate_to and _from to match PE.
  + CRM: Add a simple xsl stylesheet for rendering configurations
  + PE: Rename migration variables for clarity
  + RA: Modify the Xen RA to use the new variable names
  + crmd: crm_atoi() needs two arguments :-/
  + PE: Utility functions for finding node's by uuid/uname
  + CRM: Allow retrieval of default config values without a hashtable
  + CRM: Dont skip past the initial '<'
  + CIB: The decision to log failed connection attempts should be left to the client
  + CIB: New error code
  + Tools: Print the duration we parsed
  + CRM: Refactor date printing to allow date -> string conversion
  + Tools: Set a slightly higher default action timeout
  + Silly typo.
  + Add support for overriding the hostname drbd uses based on the clone
  + CRM: Ensure the normalized result of (add|subtract)_time is updated before returning
  + Tools: Place the lifetime rule in the correct location
  + crmd: If we allocated temporary user_data content, we must free it also
  + CTS: Indicate debug log messages
  + PE: Dont waste time checking action definitions on nodes that wont be running resources
  + PE: Small logging change
  + PE: Update the dot file after the previous action definition check change
  + CRM: Changes to fake transition key generation
  + TE: Minor cleanup
  + CTS: Support the setting of a few more options for lrmadmin calls
  + crmd: Remove dead code
  + CTS: Rewrite the ResourceRecover to use asynchronous failures
  + CTS: Move a comment to a more appropriate location
  + CTS: Remove debug message
  + CTS: Rewrite the LSBDummy RA
  + Hg: Merge in some changes related to async failure notifications
  + CTS: Ignore ResourceRecover testing artifacts
  + Core: Allow writing to syslog to be turned off
  + CRM: Correctly handle syslog facility == 0
  + Core: Fix stupid cut/paste error
  + Add some defaults to configure.in to reduce buildrequires.
  + Fix a typo in the default path to scp. (Only mattered if scp wasn't
  + clplumbing: use the result of strcmp correctly
  + PE: Fix group recovery when a group it depends on is restarted
  + PE: Stop regenerating expected test results
  + PE: Have group-group recovery work for the right reasons
  + PE: Rename elements of the pe_ordering enum for clarity
  + PE: Move DeleteRsc to a more appropriate location
  + PE: Shift code out of the PE library that is only used by the PE application
  + PE: Change for code clarity
  + PE: Fix group recovery
  + PE: Allow order_constraint_t to represent multiple ordering conditions concurrently
  + PE: Not all pseudo operations should be included in the graph
  + PE: Correct arguments to CRM_CHECK()
  + PE: Clean up generation of and contents of dot-files
  + PE: Updated regression tests with the revised consistant format
  + PE: Only show elements of the graph in the dot-file by default
  + RA: -eq is for integer comparisions
  + CTS: Remove resource tied to the DC - the #is_dc comparision is irrelevant
  + Build: .cvsignore maintainence
  + CRM: Fix replace_xml_child() when neither child nor update have an id
  + Admin: Auto populate the provider for OCF resources if one is not provided
  + Admin: Include rsc_location details in the resource listing
  + Admin: Use the current node uname by default when invoked as crm_standby
  + RA: Fix up the Dummy metadata
  + Admin: crm_primitive.py: Include all node preferences in the one rsc_location constraint
  + RA: drbd: Fix some issues and work-arounds for drbdadm bugs.
  + RA: IPsrcaddr wrapper: Fix silly typo.
  + RPM: Improved grammar in gui package description
  + DEBIAN: Packaging updates for 2.0.8-1 release
  + CIB: ODSL #1480 - Create synchronous r/w connections correctly
  + DTD: The DTD used "integer" instead of "number" (which was used by the code)
  + CRM: Repair the status_printw macro now that we do logging slightly differently
  + Tools: Dont do ID checks on cibadmin diff's, duplicates are expected
  + Build: Use existing accounts when building on OSX
  + Tools: Help text and input sanity checks for ocf-tester
  + Advertise migrate_from and _to actions. Mention migrate in meta-data.
  + Add heartbeat-2-gui package control files to Makefile
  + Relaxed a stonithd timeout so that start will succeed if it completes in a minute.
  + Finally get a chance to correct lmb's spelling
  + Build: Include the exact version being built even when building an archived tree
  + configure: Check for more pre-requisites of the mgmt/quorum components.
  + Remove a bunch of dead code (Perl/SWIG bindings).
  + Remove a few work-arounds now that notifications work correctly.
  + Core: Allow the malloc tracking code to compile on systems where size_t != int
  + cib: Compile when malloc tracking is enabled
  + CRM: When malloc tracking is enabled, pass through the person that called crm_strdup
  + Tools: Fix a number of memory leaks in attrd
  + Tools: Compile when malloc checking is off, fix last mem leak
  + moved drbd peer outdater into contrib/
  + We _never_ want to trim memory, use -1 instead of 4*size.
  + CRM: Delete dead code, make empty_uuid_cache() safe with NULLs
  + crmd: Resolve a number of memory leaks
  + CRM: Fix memory leak in compare_version()
  + cib: Clean up the list of clients wishing to be notified
  + crmd: Clean up leak in crmd_ccm_msg_callback()
  + crmd: dump newly allocated memory at each state change not only at idle
  + crmd: clean up more data at exit
  + CRM: Remove noisy and inaccurate memory logging
  + cib: Remove more ill-advised memory checking code
  + CRM: Remove the last references to cl_mem_stats from CRM code
  + Core: Add a (disabled) block of code that allows heartbeat to easily run with standard libc malloc-and-friends
  + crmd: Memory leak - Clean up the XML result of the LRM queries
  + crmd: Free the LRM connection at shutdown
  + cib: Memory leak - Free query matches in update_attr()
  + cib: Memory leak - Free intermediate results of find_attr_details()
  + cib: Memory leak - ensure the digest is always cleaned up
  + cib: Free various bits of memory at shutdown
  + PE: Logging
  + TE: Clean up the current graph on exit
  + CRM: Memory leak - Ensure libxml2 objects are always cleaned up in validate_with_dtd()
  + cib: Clean up the libxml2 parser at exit
  + TE: Always exit via mainloop
  + TE: Delete more items at exit
  + TE: Free the transition_timer at exit
  + CIB: Free the channel names at exit
  + CIB: Memory leak - free the digest file handle
  + crmd: Free the metadata hashtable and lrm connection at exit
  + cib: Clean up some hash tables at exit
  + crmd: Memory leak - ensure 'key' is free'd in get_rsc_metadata(), create 'restart' only when required in append_restart_list()
  + crmd: Memory leak - free the metadata list after use
  + CRM: Use unique top-level function names
  + Build: Configure switch to easily enable Valgrind'ing of the CRM
  + cib: Allow forked writer processes to clean themselves up before exiting
  + crmd: Enable Valrind'ing of the PE and TE
  + crmd: Delete the HA connection only at exit
  + Backed out changeset c65afe1e2d9006d0c6ec887359ba31d81bca5671
  + Hg: Backout changeset c65afe1e2d9006d0c6ec887359ba31d81bca5671
  + CRM: Convenience macro for list deletion
  + PE: Valgrind was complaining about this for some reason
  + crmd: Small documentation update
  + crmd: Memory leak - free the ping reply fragment after use
  + cib: Exit the writer process correctly so we'll continue to do write outs
  + crmd: Sort out the whole client deletion business.  Also delete the resources hash at shutdown.
  + cib: Dont examine the group ownership of cib.xml since we set perms to rw-------
  + mgmtd: Certain versions of SWIG do not convert the Python "None" to a
  + Build: Make supplying a Valgrind suppression file simpler
  + Build: Remove redundant and useless items from the build
  + Build: Remove more redundant and useless items from the build
  + crmd: Memory leak - clean up the intermdiate reload data
  + Added count of how many inet lines to use for the diff -B?
  + Enhance Pgsql ocf resource to handle multiple instances
  + Initial implementation of remote CIB connections using TLS and PAM
  + Switch to G_main_add_fd() instead of using io channels directly
  + cib: Support processing of commands sent via remote TLS connections
  + cib: Allow the remote connection code to be used with or without PAM/TLS
  + cib: Hook up the CIB remote connection listener
  + PE: Fix gcc warning - dont ignore the result of mktemp()
  + build: Always check for the presence of PAM an TLS headers
  + cib: Start a remote access listener on a port specified by the user
  + cib: Check for membership of the correct group
  + cib: Attend to various autobuild warnings
  + Coverity 53: Potential NULL pointer dereference.
  + Uninitialized string in heartbeat/findif.c
  + cib: Add but do not install a PAM file for the CIB
  + Build: Not all platforms need -lpam
  + cib: Older versions of gnutls used gnutls_session without the _t
  + CRM: Fixes for Coverty issues: 52, 55-58, 61-66, 68-69, 71-73 in run 240
  + Determine GNUTLS libs centrally in 'configure.in' rather than in individual Makefiles
  + Pulled in current changes from the 'dev' branch
  + Determine GNUTLS cflags centrally (follow-on from 7a742e29e3f8).
  + Use centrally determined GNUTLS cflags and libs
  + Bourne shell 'test' does not support '-e' flag.  Using '-r' instead.
  + libgnutls: if no 'libgnutls-config', try 'AC_CHECK_LIB(...)'
  + Remove CVS artifacts. ($Id$ and $Log$ have no meaning to mercurial.)
  + crm_attribute/master/standby: Always default the uname to the current
  + PE: Make sure things that shouldn't be true are never true (added asserts)
  + Fixes for Coverity issues in Run 243
  + cib: valgrind - Only close the File* if we were able to open the file
  + CRM: Prevent a number of potential use-after-free's by zero'ing out free'd loop variables
  + PE: Simplify the logic in native_rsc_order_rh
  + Put the compression buffers on the heap instead of the stack.
  + Improve portability across versions of 'gcc'.
  + Fix blatant memory leak on non-failure leg ...
  + RA: drbd: When using the nodename-override, drbdadm likes to print an
  + Update ignore files
  + CRM: Make the use of valgrind a run-time option
  + tools: Terminate the attrd process if heartbeat exits from under it
  + crmd: Clean up the voted hash at exit
  + PE: Fix a use-after-free of {key} when the monitor op already existed
  + Build: Always process the Valgrind logging option
  + build: commas mean something in autofoo
  + Core: Sanitize the "crm xyz" option processing.  Dont run valgrind if not using libc malloc
  + Revert 45354b6012c8 a807c29d883a 3de0ed0510d7: For some entirely unclear
  + RA: Filesystem: Increase default suggested timeouts.
  + Core: Better information about valgrind enablement
  + PE: Remove erroneous if-clause
  + crmd: ALL completed actions should be removed from the shutdown_list
  + PE: Prevent a potential NULL deference in clone allocation
  + PE: Provide useful feedback when a cloned resource is found active somewhere it shouldn't be
  + RA: drbd: Make parsing of drbdadm output more robust.
  + PE: Log the transition at a lower level in ptest
  + PE: Re-use StartRsc/StopRsc for consistancy
  + RA: Xen: Add a little reminder to the code.
  + crmd: Downgrade logging
  + Hg: fun with multiple concurrent committers
  + CRM: Fix a use-after-free in parse_time_duration()
  + CIB: Downgrade one log message (Deallocating the CIB.)
  + Part of the reversion of a previous changeset got stuck in here. Doh.
  + TE: Detect changes to attributes of the cib object
  + STONITH: external/riloe misspelled RI_LOGIN variable name.
  + TE: Only a limited number of cib attributes warrent aborting the transition
  + Stonith: Update the rilo RA with enhacements from Tijl Van den broeck and Guy Coates
  + RA: The first argument to os.environ.get() was supposed to be a string
  + Fixed a URL referencing where to find the APC UPS protocol description.
  + CRM: Return defaults correctly when no hash is used
  + Admin: map cib_NOTEXISTS to 0 for crm_failcount
  + RA: Filesystem - When checking ocfs2 is cloned, look for variables that are always set
  + RA: pgsql: Several enhancements to by Keisuke MORI
  + Tools: Centrally define CIB call options so that -f always works in crm_resource
  + RA: pgsql improvements
  + Build: Header-file related cleanup
  + Build: Add lha_internal to c-files that dont include it
  + Build: typo
  + follow-on from Andrew's recent changes
  + Correct omission of <lha_internal.h>
  + Another omission of <lha_internal.h>
  + Build: cvsignore additions
  + Build: include stdlib.h for exit()
  + Build: Fix typo in configure.in
  + Build: Fix recent cleanup.  Dispite the names, HALIB != HA_LIBDIR
  + Build: Fix recent cleanup.  Dispite the names, HALIB != HA_LIBDIR
  + TE: Minor log change
  + TE: Remove dead code
  + TE: Small logging improvement
  + TE: Unpack graph actions correctly
  + RA: Fix variable initialization in pgsql
  + Minor declaration fixes following Andrew's code re-working.
  + RA: Avoid concatination with None in riloe stonith agent
  + RA: Use configured scratch locations in ibmrsa stonith agent
  + Core: Set HA_DIR to the correct location after recent cleanup
  + RA: pgsql fixes and enhacements
  + crm: Gracefully fail when the target XML file is not writable
  + PE: Move Ncurses related defines to a more optimal location and make sure its included by crm_mon
  + RA: LVM: Add some hints for future todo items.
  + Build: Allow debian packages to also be built directly from Hg archives
  + Build: Misc changes to allow building with crm disabled
  + debian: sort out a kink in the configure vs. bootstrap logic
  + debian: reflect the new header locations in .files
  + debian: correct the location of stonith headers in *.files
  + PE: Fix anti-colocation when the RHS is not running
  + tools: Teach crm_uuid to write ascii-form UUIDs to hb_uuid
  + tools: show help text for crm_uuid
  + tools: Better help when an invalid uuid is passed to crm_uuid
  + crm: Check the return code from fflush() when writing xml files - AnÌbal Monsalve Salazar
  + crmd: No need to create the resource if we're trying to delete it
  + build: Add explanatory comment for configure kludge
  + Tools: Include class/type/provider in resource delete commands
  + tools: re-default to read if the are no arguments to crm_uuid
  + CTS: Account for a small timing window in the ResourceRecover test
  + Fix a Linux compiler warn/error
  + PE: Make clones semi-sticky by default
  + Fix typo.
  + crmd: dont update the restart list with unset attributes
  + Trivial documentation fix:  added the --enable-snmp-subagent to the configure help message.
  + crmd: Create the restart digest from an object with the same name that the PE uses
  + build: dopd doesnt build without the crm, disable it if the crm is disabled
  + crmd: remove dead makefile entry
  + Build: Dont install crm-related man pages when --disable-crm is used
  + RA: Return after performing a stop action in the Filesystem agent
  + Eligable is not a word ;-)
  + ocf-tester: Continue if validate-all succeeds.
  + build: Trial a slightly cleaner way of specifying required libraries
  + crm: Fix memory leak in error path
  + build: make life easier on OSX
  + RA: Filesystem: Prune duplicates from active and starting list.
  + Whitespace cleanup and minor fixes ("" for -z arguments, using -ne when
  + Build: Restore build dependencies. (Reverts http://hg.linux-ha.org/dev/rev/27394b5c56e3)
  + Correct a typo.
  + BSC: Test Dummy, IPaddr, IPaddr2, Filesystem RAs.
  + ocf-tester: Exit with appropriate exit code for success or failure.
  + BSC: Skip IPaddr2 test if ip not installed.
  + build: removed unused library dependancies
  + CRM: Comprehensive review of error recovery logic for potentially failed calls to fopen()
  + tools: return the rc we calculated in read_hb_uuid()
  + PE: Make internal group ordering of bullet-proof
  + PE: Code optimization.  No functional change
  + PE: Always print the resource's node scores
  + PE: Avoid a potential NULL dereference in an error path
  + crmd: Indicate the LRM error code if an operation cannot be cancelled
  + Ensure 'awk' is found in runtime environment
  + PE: tweak the dot file handling in ptest
  + Fixed a stupid error in some new (unused) code.
  + Allow data size to be specified
  + Updated version to 2.0.9
  + ocf-tester: Various integers were compared as strings.
  + CRM: LF #1514 - Empty values in cib.xml loses other RA parameters
  + Replace multiple derivations (poor) of locations with direct derivation from configure
  + ipctransient tests: Add some flexibility; rationalise some duplicate code
  + CRM: Make sure buffer is set to NULL after we free it
  + ipcsocket: remove some code duplication; other minor tidy-ups.
  + Make ldirectord's version valid
  + Broken ldirectord reload
  + Use the -w flag to perl to find warnings/errors
  + Remove useless calls to lc()
  + Remove duplicate $recstr
  + Use $arrayOfDNs[0] instead of @arrayOfDNs[0] to get rid of the following
  + Make sure that DEBUG is initialised
  + Change the code around a bit to avoid a warning about code following exec
  + Use $$ instead of (the uninitialised) $pid
  + If weight is not supplied, set it to 1
  + Dont use SIGENT, as it doesn't seem to exist.
  + Use implicit variables in read_config()
  + Handle $line more carefully
  + Make sure that frequency is intialised before it is used
  + CIB: Allow cluster options to be created when the default set is not present
  + Admin: Allow cluster config options to be queried/modified/deleted.  Broken in cs: 13c450735ba7
  + CIB: Prevent node_uuid from having any effect for <crm_config> changes
  + CRM: Dont call fflush() or flclose() if the output stream was NULL
  + PE: Create an implicit "cant run here" constraint if an action returns "not installed"
  + LRM: Inform clients when an RA is not installed on the machine
  + Dev version didn't build RPMs.  Added in missing EXTRA_SOURCES macro for transient-test.sh
  + Brought the web site up to date, and also fixed / finished (hopefully) the multi-language support.
  + Fixed a bug in the changelog date which was pointed out by
  + Cleaned up more of the mess left by a sloppy developer in this changeset:
  + Changed the web site php scripts so that they will substitute the English page if
  + RA: Filesystem: Harmless typo corrected.
  + RA: drbd: If drbd is stopped, demote should fail with NOT_RUNNING.
  + Fixed a bug pointed out by Pavol Gono <palo.gono@gmail.com> where heartbeat
  + RA: Fixed the three pseudo RAs to use ha_pseudo_resource. Extended the Dummy RA to support checks for serialization and to survive the TERM signal.
  + lrmadmin: fix the provider list function: first free data and then the list member.
  + CRM: size_t is always positive... broke error handling in XML parser.
  + bladehpi readme update
  + ConfigureMe: make usage info a little clearer
  + Fixed a bug reported by Max Hofer <max.hofer@apus.co.at> - crm_uuid didn't return proper exit codes.
  + configure: Add closing information to user about '/etc/passwd' and 'make install'
  + Upgraded the web site to accommodate the new version of MoinMoin
  + Fixed a small complaint about unnecessary warnings from Paulo F. Andrade
  + Put in a small fix for to relax some warnings which Paulo F. Andrade complained about.
  + Got embedded (FLASH) objects to work.  Cool!
  + Fixed a couple of minor spelling errors.
  + Fixed our id tags to be unique -- MoinMoin creates each page with a line-1 tag, and when we combine severa
  + Changed the php so that id tags with slashes in them get the slashes removed...
  + Put in changes from _29 to %29 in file names since Moin seems to have changed that...
  + Reverted a misguided change to the web site...  We should NOT replace / with %2f in URLs...
  + Output to stderr works again. Cleanup. A few more fixes.
  + RA: Filesystem: Fix metadata require/unique settings.
  + Reconciling heads within dev.
  + CRM: Use-of-NULL in validate_with_dtd() error path... Only clean up what we created
  + Admin: Allow crm_verify to be used with a named DTD file
  + Fix xml parser bug.
  + crmd: logging
  + crmd: Correctly parse the shutdown timer option
  + RA: Convert SAP* from dos :) Allow ManageRAID to show meta-data at all times.
  + lrmadmin: fixed wording; output to stderr.
  + RA: fix meta-data to conform to XML.
  + RA: fix meta-data to conform to XML.
  + LRM: new regression test (initial)
  + LRM: convert the LSB meta-data to XML.
  + LRM: fix my own fix, it broke lrmd.
  + CIB: Some extra options for developer testing
  + Tools: Add two new views to crm_mon.  Patch by Christofer Edvardsen.
  + Remove an unnecessary 'include' that broke building on some OSes.  It continues to build OK on various OSes.
  + BSC: (1) test IPC before its dependencies; (2) signal-handling: improve and catch some more.
  + PE: Don't start resources until we can verify they're not still running
  + Hg: Update ignore file
  + LRM: regression testing update; a new set of test cases added
  + LRM: regression testing, here the promissed new set of tests
  + LRM: regression testing: documentation update.
  + Switched the to using an IE-specific comment hack instead of javascript.
  + Fixed a stupid option processing error - where some option errors would be ignored.
  + Fixed an error message which used a parameter that hadn't been supplied,
  + LRM: regression testing; warning about security implications.
  + LRM: regression testing: tests could run in background; a new test case to check if ops are serialized.
  + LRM: regression testing: small fixes and update of the serialize test.
  + LRM: regression testing: update comments for the serialize test.
  + Tools: crm_verify - dont complain about missing status section
  + CRM: handle NULL inputs to xml_has_children() gracefully
  + cib: Don't increase the version number if nothing changed
  + cib: Fix stupid compile error
  + cib: Warn at startup if important version information is missing
  + cib: Fix memory leak in cib_config_changed()
  + Correct a comment.
  + Added tag SLE10-SP1 for changeset 906283515e3b
  + Added tag SLE10-SP1 for changeset a5f71c2dea64
  + Added tag SLES10-GA-2.0.7-1.5 for changeset 91de0c9c401c
  + cib: remove dead code
  + PE: Memory leak fixes
  + Added a little code to find out increase process tracking
  + fix compiling warnings
  + Tools: LF #1500 - Calls to attrd_updater with dampen=0 not processed correctly
  + RA: ocf-shellfuncs.in invokes ha_debug instead of ha_log when appropriate.
  + RA: Dummy and Delay fixed to use OCF_RESOURCE_INSTANCE. Dummy got a couple of extra variables to control TERM signal handling and verbosity.
  + LRM regression testing: new features; a new testcase: flood; some fixes; more testcases needed.
  + LRM regression testing: better separation of the driver and the engine---evaltest.sh can be used on console now.
  + LRM regression testing: updated readme.
  + Removed a message about attempt to remove ping node, since this is a "normal" condition.
  + RA: eDirectory: Some cleanups.
  + Add eDirectory RA to configure.in.
  + Wrong closing parenthesis.
  + Renamed eDirectory RA to eDir88.
  + RA: eDir88: Updates from Yan Fitterer.
  + [IPv6addr] send_ua() is leaking l
  + [IPv6addr] create_pid_directory() leaks dir
  + [IPv6addr] overrun in find_if() for 128bit prefixes
  + [IPv6addr] Use memset to set mask in find_if()
  + [IPv6addr] Merge duplicated code from find_if() and get_if() into scan_if()
  + [IPv6addr] devname in scan_if() is too short
  + [IPv6addr] Handle scanf failures in scan_if()
  + [IPv6addr] scan address directly into integers in scan_if()
  + [IPv6addr] Use the 32bit wide field of in6_addr in scan_if()
  + [IPv6addr] Remove resources/heartbeat/IPv6addr.c
  + stonithd: fixed logging to print symbolic names for operation types and results.
  + stonith external: more debugging to show various lists retrieved from a stonith plugin.
  + Dummy: Reverting the poor ole RA to it's previous Dummy state. Perhaps it should loose the delay param too.
  + LRM regression tests: lrmregtest takes place of the ocf RA Dummy.
  + stonithd: mixed up op_result from st_op and ra_op. fixing it back.
  + RA: Return to a simple but correct Dummy RA
  + PE: Logging tweaks
  + PE: Logging
  + crmd: logging
  + PE: Logging
  + PE: Make clones ever so slightly sticky by default
  + CTS: Explain why we're aborting when nodes aren't found in DNS
  + crmd: Logging
  + TE: Tweak logging of unconfirmed actions
  + Fixed a format so that it works without warnings on 32-bit machines also.
  + ec9b93d18e47 had allowed a variable to be possibly uninitialised
  + [IPv6ADDR] Fill in address bytes and use correct endienness
  + [LDIRECTORD] recieved -> received in ldirectord.cf
  + [LDIRECTORD] Fix thinko in range error message
  + [LDIRECTORD] fix copy-paste error in smtp_check's log
  + Merging from upstream (dev)
  + Remove bashim from IPaddr
  + [IPaddr] Switch back to sh now bashims are gone
  + [DEBIAN] Close #420206
  + [DEBIAN] Depend on libsnmp10-dev rather than libsnmp9-dev
  + RA: Make sure eDir88 is installed
  + RA: eDir88 - monitor() returning incorrect exit code when monitoring fails.
  + crmd: Logging
  + CTS: Logging
  + PE: Memory leak fixes
  + Added tag SLE10-SP1 for changeset 558427e03930
  + Hg: Tag maintenance
  + IPaddr/Solaris: code re-factoring (e.g. 026bab6b8384) had lost 'netmask' keyword to 'ifconfig' command
  + IPaddr/monitor: rationalise some duplicated 'ping' code
  + [DEBIAN] Update documentation location
  + Add alternate build dependancy on libsnmp-dev
  + update priority of ldirectord to extra to match dependancies
  + [DEBIAN] Update changelog for 2.0.8-2 release
  + cib: Potential logging of NULL
  + cib: Potential printing of NULL
  + cib: Remove redundant cleanup calls
  + crmd: Logging for improved debuging of parameter changes
  + cib: reduce info-level logging
  + stonith/ibmrsa: improved Bourne shell syntax
  + RA eDir88: meta-data fixed.
  + LRM: regression.sh update for portability.
  + plugins/stonith/{ssh,suicide}.c: Better OS portability
  + Pulled from upstream (dev)
  + Fixed a typo that I made that I have no idea how it went undetected.
  + [DEBIAN] Rename the heartbeat-2 source package heartbeat
  + [DEBIAN] Documentation path of ldirectord should be /usr/share/doc/ldirectord
  + [LDIRECTORD] Make the help text reflect the supported actions
  + [DEBIAN] Make a debian init script for ldirectord
  + [DEBIAN] update priority of ldirectord to extra to match dependancies
  + [DEBIAN] fix rules, fix changelog
  + PE: Remove duplicate function declarations
  + PE: Code formatting and logging
  + Admin: Dont output the transition graph by default when calling ptest
  + Remove Duplicate EXTRA_DIST from ldirectord/init.d/Makefile.am
  + Admin: crm_master: adjust expected return code from uname() to accomodate Solaris
  + uname() return code: add (heartbeat/heartbeat.c) and improve error message (crm/admin/crm_attribute.c)
  + debian: Add missing files to the package list
  + PE: Stop of a partially stopped group failed when there was only two child resources
  + TE: Fix potential printing of NULL
  + [DEBIAN] 2.0.8-4 release
  + [DEBIAN] 2.0.8-5 release
  + Found one of the reasons why cl_malloc was slower than malloc.
  + Fixed a tengine compile error.
  + cib: More accurate logging
  + LRM: replace "agency" with "agent."
  + logd: remove spurious occurence of "ha_logd."
  + LRM: on_op_done simplified. Also fixes 1583.
  + cib: improved logging for the remote listener
  + build: portability and cleanliness updates to configure.in
  + LRM audit: false positives.
  + CTS: Advertise the option to add resources to the CIB.
  + [DEBIAN] 2.0.8-7 release
  + Updated version to 2.1.1
  + configure: Make test for /proc/<pid>/exe functionality more explicit.
  + LF #1588 - Bad string comparision in IsRunning() prevents BSC from passing
  + [PATCH] Use elapsed in G_main_setall_id()
  + [DEBIAN] Add --enable-glib-malloc to configure's arguments
  + [DEBIAN] Use << instead of < for dependancy relations
  + core: handle zero length cl_malloc requests.
  + LRM audit: update and more false positives.
  + LRM: a semantic typo :-|
  + configure: Fix test -L -> -h portability issue.
  + Build: Remove legacy crud
  + build: remove unused Make variable CRM_DEBUG_LIBS
  + crmd: Potentially correct a potential logging of NULL
  + PE: Downgrade logging
  + PE: Add a dummy variable to struct native_variant_data_s so that it has a non-zero size
  + RA: edir88 - Improved monitor action by Yan Fitterer
  + Build: Remove all CRM references to HA_MALLOC_TRACK
  + Complete Andrew's removal of autoconf-2.53.diff
  + PE: Indicate orphan status when displayuing resources
  + Admin: crm_mon - Indicate the correct number of configured resources (excluding orphans)
  + LRM: notify clients on ops with lingering processes.
  + CTS: Update log pattern to match new log message output
  + crmd: make sure fsa_cluster_conn is not NULL before we try to delete it
  + RA eDir88: meta-data fixed again.
  + imported patch wordexp.patch
  + RA: eDir88 - Repair a patch mangled by email
  + RA: ocf-shellfuncs - Add some lockfile-related functions
  + Hg: ignore maintenance
  + CRM: Logging enhancements
  + CRM: Logging enhancements
  + crmd: note-to-self for future handling of cancelled ops
  + LRM audit: resource parameters are not allocated by the clplumbing library.
  + LRM: rename op to rapop in ra_pipe_op_destroy to avoid confusion.
  + configure: lack of 'libgnutls-config' need not stop 'mgmt' and 'quorumd' from building
  + CTS: a new script to collect pe input files for one CTS test.
  + crmd: remove dead cib-related code
  + CRM: Remove unnecessary logging
  + Tools: haresources2cib - Use the correct name for no-quorum-policy
  + RA: IPaddr2 - Refine and fix Cluster IP functionality by Michael Schwartzkopff.
  + TE: Reduce logging
  + CIB: Fix cib_config_changed() for when it becomes enabled
  + CIB: Only write the CIB to disk when the configuration changed (not just the status section)
  + CIB: #undef shouldnt supply a value
  + cl_longclock: Update wrapcount and static data in proper order (by Simon Graham).
  + Add comment explaining why times_longclock() calls cl_log() where it
  + Initial implementation of a STONITH module for VMWare Server guests
  + cib: Remove logging we dont care about
  + STONITH: Improvements to external/vmware
  + cib: More effective mehtod of turning off cib_config_changed() for now
  + [PATCH] Use sys/types.h instead of asm/types.h in configure(.in)
  + [DEBIAN] 2.0.8-8 release
  + [DEBIAN] 2.0.8-9 release
  + Hg: Make it official that SLE10-SP1 == STABLE-2.1.0 since we're working on 2.1.1
  + LRM: fixed timeouts and operations killed by signals.
  + LRM: fix cancel operations.
  + PE: Do not test for changes to dead actions
  + crmd: Delete cancelled operations from the CIB
  + build: Remove dead code as sanctioned by Alan on the Linux-HA Users list Feb 20, 2007
  + Build: Remove one more dead file
  + tools: crm_resource - prevent attempts to clean up non-primitive resources
  + clplumbing: convenience function for logging command invokations
  + LRM: cancel, delete, and flush requests revisited.
  + crmd: crmd changes required by lrmd changeset 58b250732bf1
  + cib: Use a BadNews pattern to catch diff failures instead of ERROR
  + lrmadmin: fix output of op status on monitor.
  + LRM: remove op's history on cancel.
  + Admin: crm_resource - Prevent user's from cleaning up non-failed resources (unless --force is supplied).
  + Admin: Log how various CRM-related CLIs are invoked
  + Logging
  + PE: Provide the call id for ops to be cancelled
  + PE: Ensure stop ops happen before cancelations
  + crmd: Revise operation tracking
  + CRM: Re-impliment asynchronous failures without need of trickery from the lrmd
  + CRM: Additional files part of the async failure reimplimentation
  + Admin: abort only when a host is _not_ set
  + RA: eDir - failed stop doesn't exit with error (Yan Fitterer)
  + lrm: stonith: fix spelling in a log message and lower log level.
  + RA: Filesystem: Improve OCFS2 UUID retrival and error handling
  + Stonith: vmware - fix metadata and optimize
  + Stonith: vmware - Now that it seems to work, allow it to be installed
  + CTS: Consistant and configurable STONITH usage
  + PE: Prevent a potential use of NULL
  + PE: Pre-emptive change anticipating a change in the LRM
  + Stonith: external - Dont make all possible parameters manditory
  + [DEBIAN] Close #420206
  + [DEBIAN] Depend on libsnmp10-dev rather than libsnmp9-dev
  + [DEBIAN] Update documentation location
  + Add alternate build dependancy on libsnmp-dev
  + update priority of ldirectord to extra to match dependancies
  + [DEBIAN] Update changelog for 2.0.8-2 release
  + [DEBIAN] Rename the heartbeat-2 source package heartbeat
  + [DEBIAN] Documentation path of ldirectord should be /usr/share/doc/ldirectord
  + [DEBIAN] Make a debian init script for ldirectord
  + [DEBIAN] update priority of ldirectord to extra to match dependancies
  + [DEBIAN] fix rules, fix changelog
  + debian: Add missing files to the package list
  + [DEBIAN] 2.0.8-4 release
  + [DEBIAN] 2.0.8-5 release
  + Added tag STABLE-2.1.0 for changeset 70067cb78a6e
  + [DEBIAN] 2.0.8-7 release
  + [DEBIAN] Add --enable-glib-malloc to configure's arguments
  + Another patch for LF 1595: findif not being useful
  + cl_malloc: a typo renders cl_malloc unusable.
  + LRM: remove some obsolete audit calls.
  + RA: Filesystem: search the path as well, if needed.
  + cl_malloc: do not allocate zero size blocks.
  + Portability: some OSes lack 'stdint.h'
  + Portability: ulong is the deprecated name for unsigned long
  + CIB: read_attr() can safely always talk to the local CIB
  + Admin: crm_mon: -X has an argument
  + PE: Dont invoke check_action_definitions() if there are no actions to check
  + Build: Change occurances of HB_RC_DIR, missed in a recent cleanup, to HA_RC_DIR
  + Build: CIM - Remove defines that are always included by lha_internal.h
  + Build: Use the correct (and non-deprecated) #define names
  + crmd: Provide useful feedback when the metadata is unreadable
  + CRM: Delete resources from the status section when they're deleted from the LRM
  + CRM: Further optimize removal of resources from the LRM
  + RA: o2cb: Initial version.
  + Admin: crm_attribute - Support --inhibit-policy-engine for delete operations
  + RA: o2cb: Revamp distribution of cluster.conf
  + TE: Log the node's uname instead of UUID for completed actions
  + Admin: crmadmin - include Hg version in --version output
  + PE: Dont log stopped orphaned resources
  + RA: o2cb: Optimize redistribution of cluster.cnf.
  + RA: o2cb: Improve configuration stability.
  + [LDIRECTORD] Use negotiatetimeout for SIP, DNS and Radius checks
  + [LDIRECTORD] Make parsing of the output of ipvsadm more robust
  + [LDIRECTORD] Use an alarm for HTTPS timeouts
  + [LDIRECTORD] Fix bogus detection of combined check
  + [LDIRECTORD] Fix logic bug in _status_down
  + [LDIRECTORD] Remove stale entries on reload
  + [LDIRECTORD] Don't die if Net::FTP times out
  + [LDIRECTORD] Port of last resort for real server checks
  + [LDIRECOTRD] Use globals for service check return values
  + [LDIRECTORD] Tidy up fallback
  + [LDIRECTORD] Make check_sql < 80col wide
  + [LDIRECTORD] Use $dbh->errstr instead of $dbh->err when logging
  + [LDIRECTORD] Use goto for error handling in check_sql
  + [LDIRECTORD] Handle $dbh->prepare() failure in check_sql()
  + [LDIRECTORD] Clean up execute logic in check_sql
  + [LDIRECTORD] Add forwarding mechanism to real server ID
  + [LDIRECTORD] Document that checktimeout is for ping checks too
  + [LDIRECTORD] Status to stdout
  + [LDIRECTORD] Note negotiatetimeout in documentation of checkcount
  + [LDIRECTORD] document port behaviour of real servers
  + [LDIRECTORD] Document expire_quiescent_template
  + [LDIRECTORD] Cosmetic spelling and grammar fixes
  + [LDIRECTORD] Remove trim down very wordy decripton of read_config
  + [LDIRECTORD] Enhance logging in service_set
  + [LDIRECTORD] List checktype and service in alpabetical order in the documentation
  + [LDIRECTORD] rearange parsing of service to make it <= 80col (more often)
  + [LDIRECTORD] Add Oracle check
  + [LDIRECTORD] Add ld_service_to_port()
  + [LDIRECTORD] Remove connecttimeout
  + [LDIRECTORD] Use negotiatetimeout and connecttimeout as mutual defaults
  + [LDIRECTORD] Set default negotiatetimeout to 30s
  + [LDIRECTORD] Use valid string in log message in check_connect()
  + [LDIRECTORD] Don't access CALLBACK unless it is defined
  + [LDIRECTORD] Call ld_emailalert_send() with correct arguments
  + [LDIRECTORD] Enhance ftp check debugging
  + [LDIRECTORD] Add external check
  + [DEBIAN] Update packaging in preparation for 2.1.1-1
  + [BUILD] make sure vmware stonith plugin is distrubuted
  + RA: IPaddr: Fix a few trivial bugs in lvs_support pointed out by Michael Stiller.
  + CRM: Allow cd-ing to the the core directory to be optional
  + CRM: Allow cd-ing to the the core directory to be optional
  + Admin: ptest is useful enough to warrent installation to sbindir
  + CIB: Revise version changes
  + PE: Fix two small memory leaks detected by Valgrind
  + CIB: config_changed always needs to be calculated when processing write commands
  + cib: Add some comments to the code
  + PE: Make sure ptest always does a POSIX sort
  + cib: Clean up diff logging
  + cib: Fix detection of non-status changes
  + CTS: Stonith monitoring is not interesting to us - make sure it doesn't fail
  + RA: Revised handling of directory locations
  + RA: Move all remaining autoconf variables into common files that are automatically included
  + Misc: Move a few shell functions to the only script that uses them
  + RA: Add some extra variables dug out from configure
  + Build: No longer generate RAs now that there is a sane way to set directory locations and find binaries
  + RA: Move some helper files to their new names (.files dont show up as RAs)
  + OCF: Remove conversation from installed script
  + Build: Remove over-use of autoconf variables
  + RA: ServeRAID - remove commented out code
  + RA: prefer the 'test' program rather than the builtin for some reason
  + RA: Use consistent check for required binaries
  + OCF: Remove unused variables
  + configure: Remove unneeded AC_PATH_PROGS checks
  + RA: Convert a number of checks for required binaries
  + OCF: Fixed the check in have_binary. Handle checks for programs with --arguments
  + RA: IPaddr2 - Remove bash-isms
  + RA: IPaddr2 - handle IP_CIP not being defined
  + Build: Fix installation of .ocf-returncodes to its legacy location
  + Build: Remove generated file from EXTRA_DIST
  + Admin: crm_resource - remove an overly simplistic check for when -C can safely be used
  + Contrib: dopd - Fix usage of crm_log_init() by code that shouldn't be using it
  + OCF: Minor builddir v. srcdir adjustment after recent tidy-up
  + OCF build: 'export PATH=...' is Bash; convert to Bourne
  + RA: v1: IPaddr: Unconditionally enabling LVS support is a mistake.
  + OCF definitions: correct minor typo in recent re-ordering
  + [LDIRECTORD] Add OCF wrapper
  + [DEBIAN] Add the ldirectord OCF resource to the ldirectord package
  + [BUILD] the clean target shouldn't die if files are missing
  + [DEBIAN] Update heartbeat package to reflrect the new location of ptest
  + [DEBIAN] Add new dot-ocf files to the heartbeat package
  + CTS: (minor): autoconfiscate a pathname
  + Admin: Allow crm_diff to operate on compressed inputs
  + CRM: Only detect timeout changes for recurring ops
  + pingd: Hard code the name used for logging
  + CTS: Formatting - tabs->spaces
  + CTS: Rewrite the LSB script as a proper wrapper for the OCF Dummy RA
  + OCF: Detect and warn of use of deprecated 'ocf-shellfuncs' and 'ocf-returncodes'.
  + Restored a missing file from configure.in.  Must have been deleted by accident.
  + PE: NoRoleChange shouldn't always call PromoteRsc for master resources
  + PE: Use master scores to determine which clones to start where
  + configure: Generate heartbeat/shellfuncs again.
  + Fix build - add ha_logger to Debian, fix ha_logger installation.
  + configure.in: Further fix NOARCHLIBHBDIR setting.
  + stonith riloe: fix the xml info.
  + CRM: Clean up processes left over by crm_abort().  Initial patch by DAIKI MATSUDA
  + Build: cvsignore maintenance
  + Removed a line I had to add earlier.  Maybe we had a non-obvious merge conflict?
  + Fixed a syntax error in Filesystem:  missing then symbol
  + A little cleanup to make the RAs more uniformly not have $OCF_ROOT paths in them
  + BSC: Bash/Bourne detail
  + CTS: Improve a pathname construction.
  + heartbeat: tidy some error messages
  + OCF: The compatibility wrappers used to be located in libhbdir, not in
  + stonith riloe: another fix for the xml info.
  + stonith riloe: and yet another fix for the xml info (this one the last, promise).
  + Hopefully fixed a long-time SNMP annoyance.  When the membership layer shuts down (as it does in BSC),
  + RA: Filesystem: Unify coding style to match rest of script.
  + LRM plugins: skip dot-files.
  + ibmrsa: fix the xml info.
  + BSC: 'trap' had been continuing instead of exiting
  + Fix location of pingd binary
  + ibmrsa: allow regular users to use it with 'stonith -n' and similar.
  + shellfuncs: 's%:.:%%' should be 's%:.:%:%'; the '.' should be '\.'
  + RA: LSBDummy - Make sure the action is passed to ra_execocf
  + DTD: Add helpful comment regarding rsc_colocation objects
  + CRM: Fix matching of objects with an ID when the match-spec has no ID
  + crmd: No need to log this under normal circumstances
  + Corrected a typo which only matters on 32-bit machines :-(	
  + Corrected so that on *BSD it passes in 2 parameters, instead of 2.	
  + log: avoid handing a null pointer as a '%s' variable	
  + PE: Correct the CRM_CHECK comparision	
  + stonith external/riloe: new comment in the xml on how acpid may affect the performance (thanks to Guy Coates).	
  + RA: Dummy: Just add a comment to make sure people copying from this	
  + OCF: minor Bash/Bourne issue	
  + PE: Fix the handling of remove-after-stop=true - it was causing unnecessary restarts	
  + remove is_stable() condition from drbd-outdate-peer daemon	
  + import /bin/sh fix from David Lee	
  + Pulled over a change from dev branch
  + Corrected a typo which only matters on 32-bit machines :-(
  + Corrected so that on *BSD it passes in 2 parameters, instead of 2.
  + log: avoid handing a null pointer as a '%s' variable
  + PE: Correct the CRM_CHECK comparision
  + stonith external/riloe: new comment in the xml on how acpid may affect the performance (thanks to Guy Coates).
  + RA: Dummy: Just add a comment to make sure people copying from this
  + OCF: minor Bash/Bourne issue
  + PE: Fix the handling of remove-after-stop=true - it was causing unnecessary restarts
  + remove is_stable() condition from drbd-outdate-peer daemon

* Tue Jan 09 2007  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.8 - bug fixes and enhancements
  + Allow colocation based on node attributes other than #id 
  + SAPDatabase and SAPInstance resource agents added.
  + Core/CRM: Improvements to the memory allocation, message, and string
    handling libraries result in an overall speed-up of 65%.
  + CRM: Fix ISO date handling for Jan 01 of any year.
  + CRM: Only update the voted hashtable with no-votes for the current
    election.
  + RA: IPaddr: Support netmask both in CIDR and in dotted-quad notation.
  + logd: Fix trailing random byte in log messages (OSDL 1268).
  + heartbeat:  Work around a glibc/times() bug to prevent failures every
    497 days on 32-bit Linux (OSDL 1407).
  + heartbeat: Retransmits were requested more often than they'd be
    honored (OSDL 1455).
  + CTS/PE: Introduce CRM option "startup_fencing" to disable fencing of
    unseen nodes, because CTS can't handle this.
  + PE: Split-off "network-delay" option from global_timeout to separate
    network delays from action timeouts.
  + PE/CRM: Binaries now support being called with "metadata" command to
    document the complete list of options in the CIB.
  + PE: DTD: Include start_delay as a property of operation objects.
  + PE: Fix implementation of date_spec when no range is specified.
  + PE: Enforce clone_node_max for already running resources.
  + PE: Clones were not being stopped on node shutdown.
  + PE: Allow resource colocation based on node attributes other than #id
    (node_attribute option added to rsc_colocation constraint).
  + PE: Improved handling when timeout < start_delay (OSDL 1421).
  + PE: Pre-notifications for promote occured before start was completed
    (OSDL 1447).
  + PE: Allow any two pairs of actions to be specified for rsc_order (OSDL
    1452).
  + PE: Handle asymmetric clusters where RAs are not installed on all
    nodes.
  + PE: Allow resource stickiness and failure stickiness to change based
    on node attributes.
  + CIB: Fix update_attr() causes attrd to hang at shutdown when there is
    no DC (OSDL 1432).
  + CIB: Corrupted config file prevents heartbeat restart (OSDL 1385).
  + CIB: Startup processing improvements; DTD validation will be
    automatically activated if the CIB on-disk validates.
  + TE: Fix memory leak.
  + TE: Failcount wasn't being updated in all cases.
  + TE: never update the CIB with unconfirmed stop actions (OSDL 1435).
  + CTS/RA: Replace OCFMSDummy with Stateful RA.
  + CCM: Centralize quorum calculation on the transition leader.
  + CCM: Support split-site and external quorum servers.
  + CRM: Ignore status update for non-members (ie, ping nodes).
  + LRM: Don't postpone postponed resources.
  + LRM: Fix restart in case an lrmd is already running (OSDL 1333).
  + LRM: Fix overflow in RA output handling (OSDL 1433).
  + mgmtd: Robustness and memory leak fixes.
  + mgmtd: make the port used configurable (OSDL 1390).
  + haresources2cib.py: Improve v1 to v2 conversion tool (OSDL 1415).
  + GUI: ping nodes appear as failed in gui (OSDL 1394).
  + GUI: Reduce duplicates in RA list by only showing the OCF one if both
    ocf and hb RA exist) (OSDL 1338).
  + GUI: Add new resource to currently selected group (OSDL 1414).
  + GUI: support all attributes of operations (OSDL 1372).
  + GUI: Create first resource along with a new group; delete group when
    last resource is removed (OSDL 1287).
  + GUI: Set defaults for clones and m/s RAs (OSDL 1352).
  + GUI: Use meta-data defaults when creating actions (OSDL 1351).
  + GUI: GUI: start all sub resources when we start a group or a clone
    (OSDL 1449).
  + GUI: support ordered==false or non-collocated==false groups (OSDL
    1257).
  + stonithd: Fix memory leak.
  + stonithd: Remove reliance on farside_pid (OSDL 1412).
  + stonith external/riloe: Make the login name and iLo device address
    configurable.
  + crm_resource: Add manpage.
  + RA: PureFTPd, mysql, ManageVE (to manage an OpenVZ container),
    ManageRAID, WAS6 (Websphere 6) added.
  + RA: Include SAPInstance and SAPDatabase (FATE 2172).
  + RA: IPaddr cleanup to avoid race conditions in the script. Report
    status failure when an IPaddr is active on a different interface but
    allow it to be stopped.
  + RA: IPaddr2 fixes for loopback bound addresses.
  + RA: Filesystem reported wrong status/monitor results for OCFS2 in some
    circumstances (Novell 187080).
  + RA: Improve heartbeat v1 wrappers.
  + RA: Fix db2 monitor operation.
  + RA: ldirectord: Make the emailalert and emailalertfreq options global
    as well as non-global, make checkcount global as well as per-virtual,
    add radius check, improvements to documentation.
  + RA: pgsql: Make server logfile configurable and implement
    validate-all. New parameter ctl_opt added to pgsql to support
    additional options for pg_ctl.
  + CRM: First beginnings of a cluster-wide shell (FATE ...)
  + BEAM / Coverity induced fixes.
  + Minor compatibility fixes (OSDL 1405).
  + Logging improvements all over the place.
  + Extended support for master-slave resources (FATE 300723).
  + OCF RA API compliance checker (FATE 300737).
  + Support weak and uni-directional collocation constraints (FATE
    300792).
  + Many bugfixes.

* Thu Aug 03 2006  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.7 - bug fix and a few enhancements release
  + Important steps:
    - Prior to the update, make sure all elements (instance_attributes
      etc) in the CRM configuration have valid id attributes, or set the
      ignore_dtd option to true. Otherwise, the new version will refuse
      to start.
  + SECURITY FIX:
    - Remote Denial of Service attack (#195068, CVE-2006-3121).
    - Local Denial of Service attack (#194444, CVE-2006-3815).
      (actually fixed in 2.0.6)
  + Enhancements:
    - Improved log messages.
    - ptest can now read compressed XML directly. Do not include
      optional actions and dependancies in ptest output by default.
    - crm_resource will now warn and demand exact specification when
      trying to modify an attribute while several sets are present.
  + Bugfixes:
    - Small fix from Serge Dubrouski <sergefd@gmail.com> for one
      annoying problem when PostgreSQL isn't installed on a box and one
      tries to run the script.
    - stonithd log message did not always indicate an error (OSDL 1379)
    - lrmd now limits itself to a maximum of 4 child processes, to avoid
      overloading the node and causing too long delays.
    - Improvements and fixes for Solaris 10.
    - pengine: Processing of pending probes; should not be treated as if
      the resource is running or in a known state.
    - target_role now is only taken into account for managed resources.
    - cib: Detect more cases where the nodes section needs to be
      refreshed.
    - More accurately determine node status. (OSDL 1369)
    - Filter out stop requests that would require a resource to be
      added. (OSDL 1369)
    - Send filtered resource "stops" as successes as to not block
      waiting for filtered actions.
    - By default pass the TE graph via IPC until its too large for IPC
      to deal with, only then fall back to passing via the disk.
    - Stopping of stonith resources can never require stonith, even if
      the node its running on failed; prevent graph loop. (OSDL 1376)
    - STONITH events need to inputs to start events (not stops), to
      avoid graph loop in combination with "stop before" dependencies
      (ie, groups).
    - crmd: Dont stall the FSA if we try to invoke the TE after we've
      stopped it.
    - Always unpack the correct part of a diff operation; diffs should
      now apply in more cases, reducing the need for full refreshs.
    - Correctly observe --disable-snmp-subagent during build.
    - In some states the membership is invalid and shouldn't be
      referenced. (OSDL 1377)
    - Fix a use-before-null-check issue in lrmd. (Coverity #48)
    - OCF Resource Agents outside the default path were incorrectly
      found to be not executable.
    - ccm: hostcache and delnodecache files should not be authoritative
      if autojoin is disabled. (OSDL 1226)
    - With autojoin, llm_get_nodecount() can't return the real max nodes
      anymore, this may cause memory corruption. (OSDL 1382)
    - Fix a memory corruption in membership layer, more frequently
      observed with larger (>5) clusters.
    - Change the default api-auth for pingd to uid=root
    - Dummy RA now OCF compliant.
    - Fix pingd RA metadata to be XML compliant.
    - Actually use RPMREL in the spec file.
  + KNOWN BUGS:
    - When running a cluster of nodes of very different speeds temporary
      membership anomalies may occasionally be seen.  These correct
      themselves and don't appear to be harmful.  They typically
      include a message something like this:
      WARN: Ignoring HA message (op=vote) from XXX: not in our membership list
    
* Thu Jul 13 2006  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.6 - bug fix and a few enhancements release
  + Added the ability to start/stop groups from the GUI
  + Fixed a few monitoring bugs in the Apache resource agent
  + Changed the name of the netmask parameter to the IPaddr and IPaddr2
	resource agents.  This is because the netmask must be specified
	in CIDR format.  The new name is cidr_netmask.  It will continue
	to work the old way.
  + Changed target_role so that when you stop a resource, all the resources
	which depend on it also stop - all in the proper order.
  + Many enhancements
    default_resource_failure_stickiness
    OCFS2 cluster filesystem support
    new VIPArip resource agent
    new SysInfo resource agent
    new Oracle resource agents
    Add cluster naming directive
    Added node quorum voting weights
    Added site declaration
    ha_propagate command
    allow NFS to run as a cloneable filesystem
    haresources2cib extensions
    added cibadmin man page
    Make startup fencing optional (for the brave)
    Many CIM improvements
  + Many GUI improvements
    added hb_gui symlink in /usr/bin
    significant speedup
    added support for types of groups:
    move resources up/down in groups
    resources default to being stopped
    stonith RA metadata
    basic heartbeat class RA metadata
    reworked resource addition dialog
    right-click menu
    support for clones
  + Bug fixes:
    Fixed a long-standing problem where the .src.rpms weren't usable across
	32/64-bit boundaries
    Many clone resource fixes
    autojoin works now
    target_role is now handled completely differently
    pingd and attrd now work
    OSDL 1221 GUI doesn't always keep the top window on top
    OSDL 1248 Add target_role to group causes pengine fatal assert.
    OSDL 1252  probe for newly added resouces
    Novell 12532 - parent options do NOT take precedence of child
               values Use #default as a special parameter value
    Novell #176014: wait longer before declaring attrd/pingd
           unable to connect
    Novell #178488: Notifications not generated for failed nodes
    Novell #178764 - TE doesn't abort transition
    Novell #179233 - Propagate the status of the heartbeat
                     service toojj
    OSDL 1276 - Broken clones cause segfaults
    OSDL 1275: add signing off
    Novell #180303: Filesystem returned 7 instead of 0 for
           an already unmounted filesystem.
    Novell #180303:  Notification ordering
    Novell #180799: Multiple probes scheduled for non-unique clone
    Novell #180699: Probe anonymous clones correctly
    Novell #183221 - Resource migration
    Deb 372850 migrate IPv6addr binary out of /etc
    OSDL 1280: deal with the situation that the time restart
               is shorter than deadtime
    OSDL 1272: add a new channel for callback APIs
    OSDL 1281: Handle anonymous clone renaming correctly when
               we have too many instances in the status
               section
    OSDL 1183: use the new API of heartbeat to avoid message
               delay; remove redundant code
    OSDL 1318: Add to send back a confirmation of setting up the
               callback channel
    OSDL 1329: Fix for memory leak in CIB_OP_MODIFY
    OSDL 1239: RPM unconditionally included files which were
               only present when mgmtd was build.
    OSDL 1334: When using anonymous clones, send the resource action
               with the name that the clone uses locally, not the
               name we use for it internally.
    OSDL 1301: add the capacity of get_cur_state; polish on
               memory free
    OSDL 1340: Failure to stop a clone
    OSDL 1300: stonithd / lrmd lose their connection
    OSDL 1055: Add missing RPM package dependencies
    OSDL 1349: Fix file descriptor leak on failed fork
    Deb 375941 Don't run deluser and delgrp in postrm
    OSDL 1356: Group colocation fixes when one group cant
               run anywhere
    OSDL 1350: Case sensitive searching for resources
    OSDL 1344: when an admin replaces the nodes section we should
               make sure that all the nodes heartbeat knows about
               are in there.
    OSDL 1356: reordered the "are any resources active" check to
               happen after we've confirmed all resource actions
               are complete
    OSDL 1354: CRM silently ignores trailing characters in XML input
    OSDL 1162: fix memory leak in cl_msg compression code
    Deb 376722 Add missing debian dependencies
    Deb 376786 Add missing debian dependencies
    OSDL 1360: Clones enforce resource_stickiness == INFINITY
               Move clone instances to higher preferred nodes
    OSDL 1364: should restrict rpm-based commands to rpm-based
               systems
    OSDL 1269: STONITH clone stops running after some time ...
  + KNOWN LIMITATIONS and BUGS
    + the GUI core dumps when run using AIX-based X servers

* Sun Apr 23 2006  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.5 - significant bug fixes and a few feature deficits fixed
  + various portability fixes
  + enable GUI to run with pygtk 2.4
  + significant GUI improvements and speedups
  + numerous logging improvements (generally much quieter)
  + speed up CIB processing by writing it to disk asynchronously
  + add CIB on-disk checksums
  + removed dependency on openssl
  + added "failure stickiness" to the CIB/CRM
  + Several fixes to the membership code
  + We now log all output from resource agents
  + fixed STONITHd memory leaks.
  + Added an OCF RA for Xen guests
  + Added email alerts to ldirectord
  + Improvements to the haresources2cib upgrade tool
  + Several fixes to cibadmin
  + Fix some autoadd-related bugs
  + Added Chinese support to the GUI
  + Added a daemon to replace and generalize ipfail
    + Limited testing only
  + Significant improvements to CIM model, including modifying things
  + Extensive Master/slave testing and fixes
  + Use a digest of the parameters used in an action (smaller CIB)
  + Improved detection of "old" events that should be ignored by the PE
    (ensures resource monitoring is active when required)
  + Better detection of required and/or optimal behaviour in mixed
    (and formerly mixed) clusters
  + LRM now supports multiple concurrent monitor operations
  + Optional startup & runtime enforcement of DTD validation
    (Invalid changes are rejected)
  + cibadmin tool overhauled and verified to function correctly
  + Some depreciated CIB features now unsupported
    + Placing nvpair objects in crm_config (must now use cluster_property_set)
    + on_stopfail removed in favor of setting on_fail in the resource's stop operation
    + start_prereq removed in favor of setting prereq in the resource's start operation
  + Minimum required version for performing a rolling upgrade of a
    crm yes" cluster to 2.0.5 is 2.0.4
  + Changed traditional_compression to default to NO.  This new default
	is not compatible in mixed clusters running version 2.0.0-2.0.2.
	If you are upgrading a CRM-based cluster to >= 2.0.5, you
	have to go through 2.0.4 anyway (for other reasons), so this
	shouldn't cause any additional difficulties.
	Non-CRM clusters shouldn't be affected by this because only
	CRM packets are large enough to be compressed.

* Mon Feb 27 2006  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.4 - Bug fix release - worth getting these updates
  + Fixed cpu loop for LRM
  + Fixed minor bugs in Filesystem resource agent (submounts, some
	options)
  + make the Raid1 resource agent more mdadm friendly (Ranjan Gupta), and
	other fix
  + Various small resource agent cleanups
  + Keep CCM from core dumping when certain conditions occur which
	cannot be recovered from.
  + make the Raid1 resource agent more mdadm friendly (Ranjan Gupta), and
	other fix
  + CRM General
    + Fix for a crash where the CRM referenced a NULL pointer.
    + Refine shutdown detection
    + Review and fix the contents and timing of CIB updates that are required
      when nodes appear, leave, and join the CRM.
    + Ask Heartbeat for a list of known nodes and use it to populate the <nodes>
      section in the CIB
    + Stop the CRM shutting down all active resources at exit 
      - it doesn't know if they're managed or not
    + Completely overhaul the CRM shutdown sequence
      - it now shuts down much more reliably
  + TEngine
    + Abstract out the core components into a library
    + Avoid recursion by using Gmainloop
    + Detect un-runnable sections of the graph without the need for timeouts
  + PEngine
    + Add code to support notification data for start/stop actions
	associated with clone resources
    + Link the new TEngine library with the PE testing code and simulate
      the transitions it generates
    + Bug 1084: Nodes that are offline but have active resources listed need
      to be marked as unclean for possible fencing
  + CIB
    + Change the shutdown sequence to prevent updates being lost
    + Handle un-wrapped CIB updates
    + Write out the CIB asynchronously
* Fri Feb 10 2006  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.3 - Bug fixes and significant new features.
  + Management Daemon/Library and GUI client
    + provide a management library for manamgement daemon and CIM provider
    + provide a management daemon and a basic GUI management tool
  + CIM enablement
    + CIM (Common Information Model) enablement - works with
      sblim-sfcb, OpenWBEM, and Pegasus CIMOMs
    - not yet compiled into our binary RPMs because of dependencies
  + CRM (Cluster Resource Manager) General
    + All shutdowns go via the PE/TE - preserves inter-resource ordering
    + Support for future changes to the CIB (depreciation of cib_fragment)
    + Overhaul of IPC and HA channel callback logic
    + Many improvments to the quality and quantity (reduced) of logging
  + CRMd
    + Timerless elections - when everyone has voted we're done
    + Use the replace notification from the CIB to re-update our copy with 
      our view of our peers.
    + Reliably detect if the LRM connection is still active.
    + Elections
      + newer versions defer to older ones in DC elections 
        (opposite of current behavior)
      + this means that only once the complete cluster has been upgraded will
        we start acting like the new version and accept new config options
      + it also means newer PE's and TE's (the most complex pieces) don't need
        "act like the old version" options and can rely on all slaves being at
        least as up-to-date as they are
      + people can run mixed clusters as long as they want
        (until they want the new PE features)
      + new DCs only update the version number in the CIB if they have a 
        higher value
      + nodes that start and have a lower version than that stored in the CIB
        shut themselves down (the CRM part anyway)
      + this prevents an admin from introducing old nodes back into an upgraded
        cluster. It probably doesn't fully understand the config and may not
        support the actions the PE/TE requires.
  + CIB (Common Information Base daemon)
    + Make sure "query only" connections cant modify the CIB
    + Periodically dump some stats about what the CIB has been doing.
    + Verify there are no memory leaks
    + Performance enhancements
    + Prevent a single CIB client from blocking everyone else
    + Clients Can be notified of full CIB replacements
    + record_config_changes option in ha.cf for those worried about 
      the amount of logging.  Defaults to "on".
    + suppress_cib_writes CIB option replaced with in enable_config_writes ha.cf 
      (enable_config_writes to be removed in 2.0.4)
    + Never write the status section to disk
    + Check permissions for the on-disk CIB at startup
    + Dont trash unreadable on-disk CIBs
    + Fix for updates made against the whole CIB (not just one section) 
  + PEngine (Policy Engine)
    + Many improvements to the handling of resource groups
    + Support "anonymous" clones
    + Fix stonith ordering
    + Order DC shutdowns after everyone else's
    + Support short resource names (for group and clone resources)
    + The ordering and colocation of grouped resources is now optional
    + Support probing new nodes for active resources.
    + All "probe" actions are controlled by the PE.
      + No resource may be started until the probing is complete.
      + Do not probe for resources we know to be active on unprobed nodes
    + When looking for monitor ops, only mark it optional if it was already
      active on the node we're interested in.
    + Detect changes to class/type/provider/parameters and force a restart
      of the resource
    + New record_pengine_inputs option in ha.cf for those worried about 
      the amount of logging.  Defaults to "on".
    + Differentiate between config and processing errors
      + reduces the frequency that we need to log the complete CIB
    + Make notify for master/slave work
    + New CIB option: stop_orphan_actions (boolean)
      If a resource is no longer defined, we can optionally stop it
    + New CIB option: stop_orphan_actions (boolean)
      If a monitor op for a given interval is no longer defined, we can
      optionally stop it
    + Add support for time and phase-of-the-moon based constraints
    + Improved failure handling: avoiding false positives
    + Always create orphaned resources - so they show up in crm_mon
    + Do not require sequential clone numbers starting at 0
  + TEngine (transition engine)
    + Detect old stonith ops
  + CLIs (Command Line interfaces)
    + Create a --one-shot option for crm_mon
    + Switch a number of CLI tools to use the new syncronous connections
    + Log errors to stderr where they will be seen and therefore useful
    + Support migration and un-migration of resources and resource groups
    + Create crm_verify for checking configuration validity
    + Simplify the passing of XML to cibadmin
  + Known open bugs worth mentioning:
    + 1075, 1080, 1081, 1084, 1085, 1064, 1069, 756, 984
    + 1050, 1082, 1037, 1079
    

* Thu Sep 22 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.2 - small bug fix only release
  + Fixed a bug in ping directive - it works again
  + Added a check to BasicSanityCheck to check ping and ping_group directives
  + fixed cl_status nodestatus to return 0 if a node has status "ping"
  + fixed a memory leak in the CRM's LRM interface code
  + fixed code which deterimines which version of the CRM becomes
    the DC when basic CIB schema versions differ.  It now prefers
    the older version to be DC instead of the newer version.

* Wed Sep 14 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.1 - 
  + Communication Layer
    + netstring encoding format is changed to be more efficient
    + add compression capability for big messages
  + Add man pages for hb_standby/hb_takeover	
  + The assert triggered by 2.0.0 has been fixed
  + CIB can now contain XML comments and/or be in DOS format	
  + Includes implementation of the ISO8601 date format
  + New CLI tools for changing cluster preferences, node attributes 
    and node standby
  + Improved recovery and placement of group resources
  + Detection of failed nodes by the Policy Engine is fixed
  + New Policy Engine features 
    http://www.linux-ha.org/ClusterResourceManager/DTD1.0/Annotated :
      sections 1.5.[8,9,10,12]
    + Constraints and instance attributes can now be active conditionally
    + Rules can now contain other rules
    + Date/Time based expressions are supported
    + Cloned resources can now optionally be notified before and after
      any of its peers are stopped or started.
    + The cluster can re-evaluate the configuration automatically after
      a defined interval of idleness
  + Removed a flow control message which was very annoying when operating
    in a mixed 1.x/2.x environment
  -- Known Bugs :-( --
    - Bug 859 - FSA took too long to complete action - fully recovered from
    - Bug 882 - IPC channel not connected during shutdown - harmless
    - Bug 879 - Failed actions cause extra election - harmless
 Each of these occurs about once or twice in 5000 test iterations
       - This is probably > 10K failovers
    - rsc_location constraints cannot have rules that contain other rules
      (fixed in CVS after release) 
* Fri Jul 29 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 2.0.0 - First stable release of the next generation of the Linux-HA project
  + Basic Characteristics described here:
	http://linux-ha.org/FactSheetv2
  + Core infrastructure improvments:
    + Messaging (message acknowledging and flow control)
    + Logging   (logging daemon)
  + Release 1.x style (2-node) clusters fully supported
  + Multi-node support (so far up to 16-node clusters tested)
	See http://linux-ha.org/GettingStartedV2 for more information
  + New components:
    + Cluster Information Base    (replicated resource configuration)
    + Cluster Resource Manager    (supporting 1->N nodes)
    + Modular Policy Engine       (controlling resource placement)
    + Local Resource Manager      (policy free, not cluster aware)
    + Stonith Daemon              (stand-alone fencing  subsytem)
  + Support for OCF and LSB resource agents
  + Support for composite resource types (groups, clones)
  + Support for a rich set of resource location and ordering constraints
  + Conversion tool for existing haresources
  + Resources monitored by request
  + Resource "maintenance" mode
  + Several failback, failure and "No Quorum" behaviours to choose from
        (global defaults and per action or resource)
  + Sample cluster state and configuration monitoring tools

  Known issues in 2.0.0:
    - Under some rare circumstances the cluster manager will time out
      while stabilizing a new cluster state.  This appears to be
	otherwise harmless - the cluster is actually fine.
	http://www.osdl.org/developer_bugzilla/show_bug.cgi?id=770
    - Under some rare circumstances, a dev assert will be triggered
	in unpack.c.  This results in the pengine getting restarted.
	This is annoying, but not a disaster.
	http://www.osdl.org/developer_bugzilla/show_bug.cgi?id=797

* Tue May 23 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.5 - Near-final beta of 2.0.0 release
  + many bug fixes - code looks very stable at this point
    -- well tested at this point on 4 and 8 node clusters.

* Thu Apr 07 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.4 - Near-final beta of 2.0.0 release
  + many bug fixes since 1.99.1
  + new external STONITH model - fully supports scripting interface
  + tested through 12 node clusters successfully
  + No serious defects found in testing
  + Easier-to-understand locational constraints model
  + Many bug fixes of many kinds
  + Important bug fixes to OCF IPaddr resource agent
  + Resources are monitored only on request
  + See http://wiki.linux-ha.org/ClusterResourceManager/Setup
    for basic ideas about getting started.
  + Release 1 style (2-node) clusters still fully supported
  + Release 2 style clusters support 1-N node clusters
	(where N is probably something like 8-32)

* Tue Mar 20 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.3 - Near-final beta "technology preview" of 2.0.0 release
  + many bug fixes since 1.99.1
  + tested through 12 node clusters with reasonable success
  + new STONITH API

* Sun Feb 20 2005  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.2 - Near-final beta "technology preview" of 2.0.0 release
  + Many many many changes.  Far too many to describe here.
  + See http://wiki.linux-ha.org/ClusterResourceManager/Setup
    for certain basic ideas about getting started.


* Mon Oct 11 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.1 - *early* beta series - preparing for 2.0.0
  + Andrew provided a number of fixes to the CRM and 2.0 features
  + Fixed a problem with retrying failed STONITH operations

* Mon Oct 11 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.99.0 - *early* beta series - preparing for 2.0.0
  + All STABLE changes noted below have been ported to this branch
  + Included in this release is a beta of the next generation of Heartbeat
	resource manager developed by Andrew Beekhof.  
	http://linuxha.trick.ca/NewHeartbeatDesign is a good place to learn
	more about this effort. Please examine crm/README, crm/test/README
	and crm/crm-1.0.dtd for example usage and configuration.
  + Also included is the L(ocal) R(esource) M(anager) developed by IBM China
	which is an integral part of the NewHeartbeatDesign.
  + Known caveats:
    - STONITH as a whole has seen a code cleanup and should be tested
      carefully.
    - The external STONITH plug-in has undergone major surgery and
      probably doesn't work yet.
    - the new CRM is not perfectly stable with 3 nodes yet.
  + PLEASE see http://osdl.org/developer_bugzilla/enter_bug.cgi?product=Linux-HA
    and use it to report quirks and issues you find!
  
* Sat Sep 18 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.2.3 (stable)
  + fixed a serious error which causes heartbeat to misbehave after about
        10 months of continuous operation
  + Made our ARP packets more RFC compliant
  + Extended apcmastersnmp code to deal with new devices
  + fixed a bug concerning simultaneous stops of both machines causing one
        of them to not shut down.
  + added an option to suppress reporting on packet corruption
  + fixed it so that we don't create the FIFO by the RPM
  + made cl_status setgid so anyone can run it, and fixed exit codes
  + eliminated a serious memory leak associated with client code
  + packaged doc files which had been missed before
  + fixed many many small bugs and memory leaks detected by BEAM
  + added several new test cases
  + fixed longstanding bug in plugin unloading
  + fixed a shutdown hang problem
  + several fixes for Solaris, FreeBSD
  + Solaris packaging now included in base
  + fixed a bug related to the apache resource agent not handling
        quoted parameters
  + added use_apphbd parameter to have heartbeat register
        with apphbd instead of watchdog device when desired
  + changed apphbd to default its config file to /etc
  + added snmp subagent code
  + added hbaping communications plugin
  + added external STONITH plugin
  + ldirectord: fixed a bug where real servers that were are
        present in multiple virtual services will only be added
        to one virtual service.

* Mon May 11 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.2.2 (stable)
  + Fixed several format string errors in communication plugins
  + Fixed a bug which kept us from diagnosing errors in non-aliased interfaces
  + Fixed a bug in ipaddr which caused an infinite loop when auto_failback on
  + Updated Debian things...
  + Added IPv6addr resource agent
  + Added ibmhmc STONITH plugin
  + Added cl_status command
  + Fixed a bug regarding restarts when auto_failback is on...
  + Fixed a couple of bugs in sha1 authentication method for very long keys
  + Fixed a bug in the portblock resource agent so that it no longer blocks
          ports on the loopback interface
  + Increased the time allowed for split brain test before it declares failure

+ Version 1.2.1 (stable)
  + Netstrings can now be used for our on-the-wire data format
  + Perl/SWIG bindings added for some heartbeat libraries
  + Significant improvements to SAF data checkpointing API
  + Implemented unbuffered ipcsocket code for SAF APIs
  + Many Solaris fixes -- except for ipfail, Solaris works
  + Significant library restructuring
  + Watchdog device NOWAYOUT is now overridded if defaulted
  + Watchdog device now kills machine instantly after deadtime
        instead of after one minute
  + Hostnames should now be treated case-independently...
  + Added new client status APIs - client_status() and cstatus_callback()
  + Fixed bug with auto_failback and quick full restarts
  + We now automatically reboot when resources fail to stop correctly...
  + We now check the status of the configured STONITH device hourly...
  + STONITH operations repeat after a 5 second delay, not immediately...
  + Added hb_takeover command - complement to hb_standby
  + Added documentation on how to use evlog/TCP to enable testing to
        take place without losing messages due to UDP message forwarding
  + Several new tests from Mi, Jun - split brain, bandwidth, failure
        detection time.
  + Fix to LVM resource from Harald Milz <hm@muc.de>
  + Fixed FreeBSD authentication problems breaking ipfail
  + Fixed .so loading on Debian
  + Fixed false complaints about resource scripts (from Jens Schmalzing)
  + Fixed false stop failure from LinuxSCSI  (from Jens Schmalzing <j.s@lmu.de>)



* Thu Apr 15 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.3.0 - beta series
  + Netstrings can now be used for our on-the-wire data format
  + Perl/SWIG bindings added for some heartbeat libraries
  + Significant improvements to SAF data checkpointing API
  + Implemented unbuffered ipcsocket code for SAF APIs
  + Many Solaris fixes -- except for ipfail, Solaris works
  + Significant library restructuring
  + Watchdog device NOWAYOUT is now overridded if defaulted
  + Watchdog device now kills machine instantly after deadtime
 	instead of after one minute
  + Hostnames should now be treated case-independently...
  + Added new client status APIs - client_status() and cstatus_callback()
  + Fixed bug with auto_failback and quick full restarts
  + We now automatically reboot when resources fail to stop correctly...
  + We now check the status of the configured STONITH device hourly...
  + STONITH operations repeat after a 5 second delay, not immediately...
  + Added hb_takeover command - complement to hb_standby
  + Added documentation on how to use evlog/TCP to enable testing to
	take place without losing messages due to UDP message forwarding
  + Several new tests from Mi, Jun - split brain, bandwidth, failure
	detection time.
  + Fix to LVM resource from Harald Milz <hm@muc.de>

* Tue Feb 16 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.2.0
  + Replaced the nice_failback option with the auto_failback option.
	THIS OBSOLETES THE NICE_FAILBACK OPTION. READ THE DOCS FOR HOW
	TO UPGRADE SMOOTHLY.
  + Added a new feature to hb_standby which allows you to give up
	  any specific category of resources:  local, foreign, or all.
	The old behavior is "all" which is the default.
	This allows you to put a auto_failback no cluster into
	  an active/active configuration on demand.
  + ipfail now works properly with auto_failback on (active/active)
  + ipfail now has "hysteresis" so that it doesn't respond immediately
	to a network failure, but waits a little while so that the
	damage can be properly assessed and extraneous takeovers avoided
  + Added new ping node timeout directive "deadping"
  + Made sure heartbeat preallocated stack and heap, and printed a
	message if we allocate heap once we're started up...
  + IPMILan STONITH plugin added to CVS
  + Added IPaddr2 resource script
  + Made the APC smart UPS ups code compatible with more UPSes
  + Added a (preliminary?) ordered messaging facility from Yi Zhu
  + Changed IPaddr's method of doing ARPs in background so that
	certain timing windows were closed.
  + Added OCF (wrapper) resource script
  + Allow respawn programs to take arguments
  + Added pinggroups (where any node being up is OK)
  + SIGNIFICANT amount of internal rearchitecture.
  + Many bug fixes.
  + Several documentation updates.

* Tue Feb 10 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.1.5
  + ipfail now has "hysteresis" so that it doesn't respond immediately
	to a network failure, but waits a little while so that the
	damage can be properly assessed and extraneous takeovers avoided
  + Several fixes to cl_poll()
  + More fixes to the IPC code - especially handling data reception
	after EOF
  + removed some unclean code from GSource for treating EOF conditions
  + Several bugs concerning hanging when shutting down early during startup
  + A few BasicSanityCheck bug fixes
  + CTS now allows a single machine to be able to monitor several clusters
  + Most former CTS options are now either unneeded or on the command line
  + Increased number of ARPs and how long they're being sent out
  + Fixed uncommon (authorization) memory leak
  + Some Solaris portability fixes.
  + Made init script handle standby correctly for new config files
  + Improved the fast failure detection test
  + Added some backwards compatibility for nice_failback and some default
	authentication directives
  + Corrected the 1.1.4 change log
  

* Fri Jan 22 2004  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.1.4
  + ipfail now works properly with auto_failback on (active/active)
  + Changed the API to use sockets (IPC library) instead of FIFOs.
  + Added new apiauth directives to provide authorization information
	formerly provided by the FIFO permissions.
  + Added Intel's implementation of the SAF data checkpointing API and daemon
  + Added a cleanup suggested by Emily Ratliff.
  + IPMILan STONITH plugin added to CVS
  + Added IPaddr2 resource script
  + Various cleanups due to horms.
  + Fixed authentication to work on 64-bit platforms(!)
  + Fixed the cl_poll() code to handle corner cases better
  + Made heartbeat close watchdog device before re-execing itself
  + New CTS improvements from Mi, Jun <jun.mi@intel.com>
  + Various minor bug fixes.
      . Several shutdown bugs addressed
      . fixed sendarp to make a pid file, so we can shut it down
          when we shut everything else down in case it's still running.
      . Lots of minor bug fixes to IPC code
      . Lots of minor bug fixes to ipctest program
      . made BasicSanityCheck more tolerant of delays
      . Fixed IPC code to authenticate based on ints, not int*s.
      . Check properly for strnlen instead of strlen...
      . Several signed/unsigned fixes
      . A few uninitialized vars now are inited
      . Switched to compiling lex/yacc sources the automake way
      . Lots of minor CTS fixes...

  + ldirectord bug fixes:
    . When new real servers are added on initialisation or when
        the configuration file is reread they are marked with status
        of -1 (uninitialised) so they will be checked and inserted
        into the virtual service as required
    . All checks use the checkport if set, otherwise the port set for
        the individual real server. This was the case for http and
        connect checks, but others had variations on this theme.
    . When the configuration file is reread because it changed
        on disk and autoreload is set, check the real servers
        immediately rather than waiting for checkinterval to expire
    . Already running message sent to stderr instead of stdout
    . Support alternate server in real-server specific URL
    . Treat the same real server with different weights as a different
        real server. Fixes bug reported by Philip Hayward whereby the same
        real-server would always have the same weight, regardless of
        the ldirectord.cf

* Fri Sep 26 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.1.3
  + Bugfix for heartbeat starting resources twice concurrently if
    auto_failback was set to "legacy".
  + Bugfix for messages getting lost if messages were sent in quick
    succession. (Kurosawa Takahiro)
  + Bugfix for Filesystem resource checking for presence of filesystem
    support before loading the module.
  + BasicSanityCheck extended to cover more basic tests.
  + Bugfix for findif not working correctly for CIDR netmasks.
  + Minor bugfix for ldirectord recognizing new schedulers correctly and
    timeout settings are now being honoured.
  + Enhanced the message giving a better explanation of how to set up node
    names properly when current node not found in the ha.cf file
  + Send a message to the cluster whenever we have a node which doesn't
    need STONITHing - even though it's gone down.  This fix needed
    by CCM, which is in turn needed by EVMS.
  + Enhanced the messages for missing ha.cf and missing haresources files
    explaining that sample config files are found in the documentation. 
  + Fix for memory leak from Forrest Zhao<forrest.zhao@intel.com>
  + Added a (preliminary?) ordered messaging facility from Yi Zhu
  + FAQ updates
  + Added Xinetd resource script
  + Added OCF (wrapper) resource script
  + Allow respawn programs to take arguments
  + Added pinggroups (where any node being up is OK)
  + fixed ldirectord negotiatetimeout for HTTP
  + fixed a bug which caused -d flag to be ignored
  + failing resource scripts are now ERRORs not WARNings
  + now shuts down correctly when auto_failback == legacy


* Mon Jul 13 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.1.2
  + Replaced the nice_failback option with the auto_failback option.
	THIS OBSOLETES THE NICE_FAILBACK OPTION. READ THE DOCS FOR HOW
	TO UPGRADE SMOOTHLY.
  + Changed IPaddr to not do ARPs in background, and shortened time 
	between ARPs.  Also made these things tunable...
  + changed our comm ttys to not become our controlling TTYs
  + Enhanced the ServeRAID script to fix a critical bug by using a new feature
  + Added a new DirectoryMap to CVS - tells where everything is...
  + significantly enhanced the BasicSanityCheck script, and the tests
	it calls.
  + added a new option to use a replacement poll function for improved
	real-time performance.
  + added the ability to have a cluster node's name be different
	from it's uname -n
  + Moved where CTS gets installed to /usr/lib/heartbeat/cts
  + Big improvements to the CTS README from IBM test labs in Austin.
  + bug fixes to the WTI NPS power switch
  + new client API calls:
	return arbitrary configuration parameters
	return current resource status
  + Added a new clplumbing function: mssleep()
  + added new capabilities for supporting pseudo-resources
  + added new messages which come out after initial takeover is done
	 (improves CTS results)
  + LOTS of documentation updates.
  + fixed a security vulnerability
  + fixed a bug where heartbeat would shut down while in the middle
	of processing resource movement requests.
  + changed compilation flags to eliminate similar future security
	issues
  + went to even-more-strict gcc flags
  + fixed several "reload" bugs.  Now reload works ;-)
  + fixed STONITH bug when other node never heard from.
  + Minor bug fixes (cleaned up corrupted message)
  + Two different client API bugs fixed.
  + changed the configure script to test which warning flags are
	supported by the current gcc.
  + enhanced the API test program to test new capabilities...


* Wed May 21 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.1.1
  + Significant restructuring of the processes in heartbeat
  + Added a new feature to hb_standby which allows you to give up
	  any specific category of resources:  local, foreign, or all.
	The old behavior is "all" which is the default.
	This allows you to put a nice_failback cluster into
	  an active/active configuration
  + Enhancements to the ServeRAID code to make it work with the new
    (supported) version of IPSSEND from the ServeRAID folks...
  + Added STONITH code for the Dell remote access controller
  + Fixed a major bug which kept it from taking over correctly after 246
	days or so
  + Fixed a major bug where heartbeat didn't lock itself into memory
	properly
  + Added new ping node timeout directive "deadping"
  + Made sure heartbeat preallocated stack and heap, and printed a
	message if we allocate heap once we're started up...
  + Minor heartbeat API bug fixes
  + Minor documentation fixes
  + Minor fix to allow IP addresses with /32 masks...
  + Fixed a timing window for !nice_failback resource acquisition
  + Added several CCM bug fixes
  + Made the APC smart UPS ups code compatible with more UPSes
  + Fixed a bug in respawn
  + Enhanced internal checking for malloc errors...
  + Added IP alias search optimization from Sean Reifscheneider

* Wed Mar 19 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.0.2:
  + Fixed comment errors in heartbeat init script to allow it to run on RH 8.0
  + Changed apphbd to use poll(2) instead of sigtimedwait(2)
  + Put missing files into tarball
  + Documentation improvements for IPaddr and other things
  + Fixed an error in hb_standby which kept it from working if releasing 
    resources takes more than 10 seconds
  + Added a fix to allow heartbeat to run on systems without writable disk
    (like routers booting from CD-ROM)
  + Added configuration file for apphbd
  + Added fix from Adam Li to keep recoverymgr stop looping at high priority
  + Added fix to ServeRAID resource to make it work with (new) supported 
    hardware
  + Added Delay resource script
  + Added fix to Filesystem to allow it to support NFS mounts and allow
    user to specify mount options
  + Added fix to IPaddr to make tmp directory for restoring loopback device
  + Added fix to ipcsocket code to deal correctly with EAGAIN when sending
    message body

* Mon Feb 17 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.0.1:
  + Fixed some compile errors on different platforms, and library versions
  + Disable ccm from running on 'ping' nodes
  + Put in Steve Snodgrass' fix to send_arp to make it work on non-primary
	interfaces.

* Thu Feb 13 2003  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 1.0.1 beta series

  0.4.9g:
  + Changed default deadtime, warntime, and heartbeat interval
  + Auto* tool updates
  + VIP loopback fixes for IP address takeover
  + Various Solaris and FreeBSD fixes
  + added SNMP agent
  + Several CCM bug fixes
  + two new heartbeat API calls
  + various documentation fixes, including documentation for ipfail
  + Numerous minor cleanups.
  + Fixed a few bugs in the IPC code.
  + Fixed the (IPC) bug which caused apphbd to hang the whole machine.
  + Added a new IPC call (waitout)
  + Wrote a simple IPC test program.
  + Clarified several log messages.
  + Cleaned up the ucast communications plugin
  + Cleaned up for new C compilers
  + Fixed permissions bug in IPC which caused apphbd to not be usable by all
  + Added a new rtprio option to the heartbeat config file
  + updated apphbtest program
  + Changed ipfail to log things at same level heartbeat does


* Sat Nov 30 2002  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
+ Version 0.5 beta series (now renamed to 1.0.1 beta series).
  0.4.9f:
  + Added pre-start, pre-stop, post-stop and pre-stop constructs in init script
  + various IPC fixes
  + Fix to STONITH behavior: STONITH unresponsive node right after we reboot
  + Fixed extreme latency in IPC code
  + various configure.in cleanups
  + Fixed memory leak in IPC socket code
  + Added streamlined mainloop/IPC integration code
  + Moved more heartbeat internal communication to IPC library
  + Added further support for ipfail
  + Added supplementary groups to the respawn-ed clients
  + Added standby to init script actions
  + Lots of minor CCM fixes
  + Split (most) resource management code into a separate file.
  + Fixes to accommodate different versions of libraries
  + Heartbeat API client headers fixup
  + Added new API calls
  + Simplified (and fixed) handling of local status.  This would sometimes cause
	obscure failures on startup.
  + Added new IPsrcaddr resource script

  KNOWN BUGS:
  + apphbd goes into an infinite loop on some platforms

* Wed Oct 9 2002  Alan Robertson <alanr@unix.sh> (see doc/AUTHORS file)
  0.4.9e:
  + Changed client code to keep write file descriptor open at all times
        (realtime improvement)
  + Added a "poll replacement"  function based on sigtimedwait(2), which
        should be faster for those cases that can use it.
  + Added a hb_warntime() call to the application heartbeat API.
  + Changed all times in the configuration file to be in milliseconds
        if specified with "ms" at the end.  (seconds is still the default).
  + Fixes to serious security issue due to Nathan Wallwork <nwallwo@pnm.com>
  + Changed read/write child processes to run as nobody.
  + Fixed a bug where ping packets are printed incorrectly when debugging.
  + Changed heartbeat code to preallocate a some heap space.
  + CCM daemon API restructuring
  + Added ipc_channel_pair() function to the IPC library.
  + Changed everything to use longclock_t instead of clock_t
  + Fixed a bug concerning the ifwalk() call on ping nodes in the API
  + Made apphbd run at high priority and locked into memory
  + Made a library for setting priority up.
  + Made ucast comm module at least be configurable and loadable.
  + Fixed a startup/shutdown timing problem.

  0.4.9d:
  + removed an "open" call for /proc/loadavg (improve realtime behavior)
  + changed API code to not 1-char reads from clients
  + Ignored certain error conditions from API clients
  + fixed an obscure error message about trying to retransmit a packet
	which we haven't sent yet.  This happens after restarts.
  + made the PILS libraries available in a separate package
  + moved the stonith headers to stonith/... when installed
  + improved debugging for NV failure cases...
  + updated AUTHORS file and simplified the changelog authorship
	(look in AUTHORS for the real story)
  + Added Ram Pai's CCM membership code
  + Added the application heartbeat code
  + Added the Kevin Dwyer's ipfail client code to the distribution
  + Many fixes for various tool versions and OS combinations.
  + Fixed a few bugs related to clients disconnecting.
  + Fixed some bugs in the CTS test code.
  + Added BasicSanityCheck script to tell if built objects look good.
  + Added PATH-like capabilities to PILS
  + Changed STONITH to use the new plugin system.
  + *Significantly* improved STONITH usage message (from Lorn Kay)
  + Fixed some bugs related to restarting.
  + Made exit codes more LSB-compliant.
  + Fixed various things so that ping nodes don't break takeovers.

  0.4.9c and before:
  + Cluster partitioning  now handled correctly (really!)
  + Complete rearchitecture of plugin system
  + Complete restructure of build system to use automake and port things
	to AIX, FreeBSD and solaris.
  + Added Lclaudio's "standby" capability to put a node into standby
	mode on demand.
  + Added code to send out gratuitous ARP requests as well as gratuitous
	arp replies during IP address takeover.
  + Suppress stonith operations for nodes which went down gracefully.
  + Significantly improved real-time performance
  + Added new unicast heartbeat type.
  + Added code to make serial ports flush stale data on new connections.
  + The Famous CLK_TCK compile time fixes (really!)
  + Added a document which describes the heartbeat API
  + Changed the code which makes FIFOs to not try and make the FIFOs for
        named clients, and several other minor API client changes.
  + Fixed a fairly rare client API bug where it would shut down the
        client for no apparent reason.
  + Added stonith plugins for: apcmaster, apcmastersnmp switches, and ssh
        module (for test environments only)
  + Integrated support for the Baytech RPC-3 switch into baytech module
  + Fixes to APC UPS plugin
  + Got rid of "control_process: NULL message" message
  + Got rid of the "controlfifo2msg: cannot create message" message
  + Added -h option to give usage message for stonith command...
  + Wait for successful STONITH completion, and retry if its configured.
  + Sped up takeover code.
  + Several potential timing problems eliminated.
  + Cleaned up the shutdown (exit) code considerably.
  + Detect the death of our core child processes.
  + Changed where usage messages go depending on exit status from usage().
  + Made some more functions static.
  + Real-time performance improvement changes
  + Updated the faqntips document
  + Added a feature to heartbeat.h so that log messages get checked as
        printf-style messages on GNU C compilers
  + Changed several log messages to have the right parameters (discovered
        as a result of the change above)
  + Numerous FreeBSD, Solaris and OpenBSD fixes.
  + Added backwards compatibility kludge for udp (versus bcast)
  + Queued messages to API clients instead of throwing them away.
  + Added code to send out messages when clients join, leave.
  + Added support for spawning and monitoring child clients.
  + Cleaned up error messages.
  + Added support for DB2, ServeRAID and WAS, LVM, and Apache (IBMhttp too),
    also ICP Vortex controller.
  + Added locking when creating new IP aliases.
  + Added a "unicast" media option.
  + Added a new SimulStart and standby test case.
  + Diddled init levels around...
  + Added an application-level heartbeat API.
  + Added several new "plumbing" subsystems (IPC, longclock_t, proctrack, etc.)
  + Added a new "contrib" directory.
  + Fixed serious (but trivial) bug in the process tracking code which caused
	it to exit heartbeat - this occured repeatably for STONITH operations.
  + Write a 'v' to the watchdog device to tell it not to reboot us when
	we close the device.
  + Various ldirectord fixes due to Horms
  + Minor patch from Lorn Kay to deal with loopback interfaces which might
	have been put in by LVS direct routing
  + Updated AUTHORS file and moved list of authors over

* Fri Mar 16 2001  Alan Robertson <alanr@unix.sh>
+ Version 0.4.9

  + Split into 3 rpms - heartbeat, heartbeat-stonith heartbeat-ldirectord

  + Made media modules and authentication modules and stonith modules
	dynamically loadable.

  + Added Multicast media support
  + Added ping node/membership/link type for tiebreaking.  This will
	be useful when implementing quorum on 2-node systems.
	(not yet compatible with nice_failback(?))
  + Removed ppp support

  + Heartbeat client API support

  + Added STONITH API library
    +   support for the Baytech RPC-3A power switch
    +   support for the APCsmart UPS
    +   support for the VACM cluster management tool
    +	support for WTI RPS10
    +	support for Night/Ware RPC100S
    +	support for "Meatware" (human intervention) module
    +	support for "null" (testing only) module

  + Fixed startup timing bugs
  + Fixed shutdown sequence bugs: takeover occured before
	resources were released by other system
  + Fixed various logging bugs
  + Closed holes in protection against replay attacks

  + Added checks that complain if all resources aren't idle on startup.
  + IP address takeover fixes
      + Endian fixes
      + Removed the 8-alias limitation
      + Takeovers now occur faster (ARPs occur asynchronously)

  + Port number changes
    + Use our IANA port number (694) by default
    + Recognize our IANA port number ("ha-cluster") if it's in /etc/services

  + Moved several files, etc. from /var/run to /var/lib/heartbeat
  + Incorporated new ldirectord version
  + Added late heartbeat warning for late-arriving heartbeats
  + Added detection of and partial recovery from cluster partitions
  + Accept multiple arguments for resource scripts
  + Added Raid1 and Filesystem resource scripts
  + Added man pages
  + Added debian package support

* Fri Jun 30 2000 Alan Robertson <alanr@unix.sh>
+ Version 0.4.8
  + Incorporated ldirectord version 1.9 (fixes memory leak)
  + Made the order of resource takeover more rational:  Takeover is now
    left-to-right, and giveup is right-to-left
  + Changed the default port number to our official IANA port number (694)
  + Regularized more messages, eliminated some redundant ones.
  + Print the version of heartbeat when starting.
  + Print exhaustive version info when starting with debug on.
  + Hosts now have 3 statuses {down, up, active} active means that it knows
	that all its links are operational, and it's safe to send cluster
	messages
  + Significant revisions to nice_failback (mainly due to lclaudio)
  + More SuSE-compatibility. Thanks to Friedrich Lobenstock <fl@fl.priv.at>
  + Tidied up logging so it can be to files, to syslog or both (Horms)
  + Tidied up build process (Horms)
  + Updated ldirectord to produce and install a man page and be
    compatible with the fwmark options to The Linux Virtual Server (Horms)
  + Added log rotation for ldirectord and heartbeat using logrotate
    if it is installed
  + Added Audible Alarm resource by Kirk Lawson <lklawson@heapy.com> 
    and myself (Horms)
  + Added init script for ldirectord so it can be run independently
    of heartbeat (Horms)
  + Added sample config file for ldirectord (Horms)
  + An empty /etc/ha.d/conf/ is now part of the rpm distribution
    as this is where ldirectord's configuration belongs (Horms)
  + Minor startup script tweaks.  Hopefully, we should be able to make core
    files should we crash in the future.  Thanks to Holger Kiehl for diagnosing
    the problem!
  + Fixed a bug which kept the "logfile" option from ever working.
  + Added a TestCluster test utility.  Pretty primitive so far...
  + Fixed the serial locking code so that it unlocks when it shuts down.
  + Lock heartbeat into memory, and raise our priority
  + Minor, but important fix from lclaudio to init uninited variable.

* Sat Dec 25 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.7
  + Added the nice_failback feature. If the cluster is running when
	the primary starts it acts as a secondary. (Luis Claudio Goncalves)
  + Put in lots of code to make lost packet retransmission happen
  + Stopped trying to use the /proc/ha interface
  + Finished the error recovery in the heartbeat protocol (and got it to work)
  + Added test code for the heartbeat protocol
  + Raised the maximum length of a node name
  + Added Jacob Rief's ldirectord resource type
  + Added Stefan Salzer's <salt@cin.de> fix for a 'grep' in IPaddr which
	wasn't specific enough and would sometimes get IPaddr confused on
	IP addresses that prefix-matched.
  + Added Lars Marowsky-Bree's suggestion to make the code almost completely
	robust with respect to jumping the clock backwards and forwards
  + Added code from Michael Moerz <mike@cubit.at> to keep findif from
	core dumping if /proc/route can't be read.

* Mon Nov 22 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.6
  + Fixed timing problem in "heartbeat restart" so it's reliable now
  + Made start/stop status compatible with SuSE expectations
  + Made resource status detection compatible with SuSE start/stop expectations
  + Fixed a bug relating to serial and ppp-udp authentication (it never worked)
  + added a little more substance to the error recovery for the HB protocol.
  + Fixed a bug for logging from shell scripts
  + Added a little logging for initial resource acquisition
  + Added #!/bin/sh to the front of shell scripts
  + Fixed Makefile, so that the build root wasn't compiled into pathnames
  + Turned on CTSRTS, enabling for flow control for serial ports.
  + Fixed a bug which kept it from working in non-English environments

* Wed Oct 13 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.5
  + Mijta Sarp added a new feature to authenticate heartbeat packets
	using a variety of strong authentication techniques
  + Changed resource acquisition and relinquishment to occur in heartbeat,
       instead of in the start/stop script.  This means you don't *really*
       have to use the start/stop script if you don't want to.
  + Added -k option to gracefully shut down current heartbeat instance
  + Added -r option to cause currently running heartbeat to reread config files
  + Added -s option to report on operational status of "heartbeat"
  + Sped up resource acquisition on master restart.
  + Added validation of ipresources file at startup time.
  + Added code to allow the IPaddr takeover script to be given the
        interface to take over, instead of inferring it.  This was requested
        by Lars Marowsky-Bree
  + Incorporated patch from Guenther Thomsen to implement locking for
        serial ports used for heartbeats
  + Incorporated patch from Guenther Thomsen to clean up logging.
        (you can now use syslog and/or file logs)
  + Improved FreeBSD compatibility.
  + Fixed a bug where the FIFO doesn't get created correctly.
  + Fixed a couple of uninitialized variables in heartbeat and /proc/ha code
  + Fixed longstanding crash bug related to getting a SIGALRM while in malloc
	or free.
  + Implemented new memory management scheme, including memory stats

* Thu Sep 16 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.4
  + Fixed a stupid error in handling CIDR addresses in IPaddr.
  + Updated the documentation with the latest from Rudy.

* Wed Sep 15 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.3
  + Changed startup scripts to create /dev/watchdog if needed
  + Turned off loading of /proc/ha module by default.
  + Incorporated bug fix from Thomas Hepper <th@ant.han.de> to IPaddr for
	PPP configurations
  + Put in a fix from Gregor Howey <ghowey@bremer-nachrichten.de>
	where Gregor found that I had stripped off the ::resourceid part
	of the string in ResourceManager resulting in some bad calls later on.
  +  Made it compliant with the FHS (filesystem hierarchy standard)
  +  Fixed IP address takeover so we can take over on non-eth0 interface
  +  Fixed IP takeover code so we can specify netmasks and broadcast addrs,
	or default them at the user's option.
  +  Added code to report on message buffer usage on SIGUSR[12]
  +  Made SIGUSR1 increment debug level, and SIGUSR2 decrement it.
  +  Incorporated Rudy's latest "Getting Started" document
  +  Made it largely Debian-compliant.  Thanks to Guenther Thomsen, Thomas
	Hepper, Iñaki Fernández Villanueva and others.
  +  Made changes to work better with Red Hat 6.1, and SMP code.
  +  Sometimes it seems that the Master Control Process dies :-(

* Sat Aug 14 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.2
  + Implemented simple resource groups
  + Implemented application notification for groups starting/stopping
  + Eliminated restriction on floating IPs only being associated with eth0
  + Added a uniform resource model, with IP resources being only one kind.
	(Thanks to Lars Marowsky-Bree for a good suggestion)
  + Largely rewrote the IP address takeover code, making it clearer, fit
	into the uniform resource model, and removing some restrictions.
  + Preliminary "Getting Started" document by Rudy Pawul
  + Improved the /proc/ha code
  + Fixed memory leak associated with serial ports, and problem with return
	of control to the "master" node.
	(Thanks to Holger Kiehl for reporting them, and testing fixes!)

* Tue Jul 6 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.1
  + Fixed major memory leak in 0.4.0 (oops!)
  + Added code to eliminate duplicate packets and log lost ones
  + Tightened up PPP/UDP startup/shutdown code
  + Made PPP/UDP peacefully coexist with "normal" udp
  + Made logs more uniform and neater
  + Fixed several other minor bugs
  + Added very preliminary kernel code for monitoring and controlling
	heartbeat via /proc/ha.  Very cool, but not really done yet.

* Wed Jun 30 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.4.0
  + Changed packet format from single line positional parameter style
	to a collection of {name,value} pairs.  A vital change for the future.
  + Fixed some bugs with regard to forwarding data around rings
  + We now modify /etc/ppp/ip-up.local, so PPP-udp works out of the box
	(at least for Red Hat)
  + Includes the first version of Volker Wiegand's Hardware Installation Guide
	(it's pretty good for a first version!)

* Wed Jun 09 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.3.2
  + Added UDP/PPP bidirectional serial ring heartbeat
	(PPP ensures data integrity on the serial links)
  + fixed a stupid bug which caused shutdown to give unpredictable
	results
  + added timestamps to /var/log/ha-log messages
  + fixed a couple of other minor oversights.

* Sun May 10 1999  Alan Robertson <alanr@unix.sh>
+ Version 0.3.1
  + Make ChangeLog file from RPM specfile
  + Made ipresources only install in the DOC directory as a sample

* Sun May 09 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.3.0
  + Added UDP broadcast heartbeat (courtesy of Tom Vogt)
  + Significantly restructured code making it easier to add heartbeat media
  + added new directives to config file:
    + udp interface-name
    + udpport port-number
    + baud    serial-baud-rate
  + made manual daemon shutdown easier (only need to kill one)
  + moved the sample ha.cf file to the Doc directory

* Sat Mar 27 1999 Alan Robertson <alanr@unix.sh>
+ Version 0.2.0
  + Make an RPM out of it
  + Integrated IP address takeover gotten from Horms
  + Added support to tickle a watchdog timer whenever our heart beats
  + Integrated enough basic code to allow a 2-node demo to occur
  + Integrated patches from Andrew Hildebrand <andrew@pdi.com> to allow it
    to run under IRIX.
  - Known Bugs
    - Only supports 2-node clusters
    - Only supports a single IP interface per node in the cluster
    - Doesn't yet include Tom Vogt's ethernet heartbeat code
    - No documentation
    - Not very useful yet :-)

###########################################################
