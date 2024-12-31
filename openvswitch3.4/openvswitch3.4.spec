# Copyright (C) 2009, 2010, 2013, 2014 Nicira Networks, Inc.
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without warranty of any kind.
#
# If tests have to be skipped while building, specify the '--without check'
# option. For example:
# rpmbuild -bb --without check rhel/openvswitch-fedora.spec

# This defines the base package name's version.

%define pkgname openvswitch3.4

%if 0%{?commit:1}
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%endif

# Enable PIE, bz#955181
%global _hardened_build 1

# RHEL-7 doesn't define _rundir macro yet
# Fedora 15 onwards uses /run as _rundir
%if 0%{!?_rundir:1}
%define _rundir /run
%endif

# FIXME Test "STP - flush the fdb and mdb when topology changed" fails on s390x
# FIXME 2 tests fails on ppc64le. They will be hopefully fixed before official 2.11
%ifarch %{ix86} x86_64 aarch64
%bcond_without check
%else
%bcond_with check
%endif
# option to run kernel datapath tests, requires building as root!
%bcond_with check_datapath_kernel
# option to build with libcap-ng, needed for running OVS as regular user
%bcond_without libcapng
# option to build with ipsec support
%bcond_without ipsec

# Build python2 (that provides python) and python3 subpackages on Fedora
# Build only python3 (that provides python) subpackage on RHEL8
# Build only python subpackage on RHEL7
%if 0%{?rhel} > 7 || 0%{?fedora}
# On RHEL8 Sphinx is included in buildroot
%global external_sphinx 1
%else
# Don't use external sphinx (RHV doesn't have optional repositories enabled)
%global external_sphinx 0
%endif

Name: %{pkgname}
Summary: Open vSwitch
Group: System Environment/Daemons daemon/database/utilities
URL: http://www.openvswitch.org/
Version: 3.4.1
Release: 5%{?dist}

# Nearly all of openvswitch is ASL 2.0.  The bugtool is LGPLv2+, and the
# lib/sflow*.[ch] files are SISSL
# datapath/ is GPLv2 (although not built into any of the binary packages)
License: ASL 2.0 and LGPLv2+ and SISSL

%define dpdkver 23.11
%define dpdkdir dpdk
%define dpdksver %(echo %{dpdkver} | cut -d. -f-2)
# NOTE: DPDK does not currently build for s390x
# DPDK on aarch64 is not stable enough to be enabled in FDP
%if 0%{?rhel} > 7 || 0%{?fedora}
%define dpdkarches x86_64 ppc64le
%else
%define dpdkarches
%endif

%if 0%{?commit:1}
Source: https://github.com/openvswitch/ovs/archive/%{commit}.tar.gz#/openvswitch-%{commit}.tar.gz
%else
Source: https://github.com/openvswitch/ovs/archive/v%{version}.tar.gz#/openvswitch-%{version}.tar.gz
%endif
Source2: %{pkgname}.sysusers
Source3: %{pkgname}-hugetlbfs.sysusers
Source10: https://fast.dpdk.org/rel/dpdk-%{dpdkver}.tar.xz

%define docutilsver 0.12
%define pygmentsver 1.4
%define sphinxver   1.2.3
%define pyelftoolsver 0.27
Source100: https://pypi.io/packages/source/d/docutils/docutils-%{docutilsver}.tar.gz
Source101: https://pypi.io/packages/source/P/Pygments/Pygments-%{pygmentsver}.tar.gz
Source102: https://pypi.io/packages/source/S/Sphinx/Sphinx-%{sphinxver}.tar.gz
Source103: https://pypi.io/packages/source/p/pyelftools/pyelftools-%{pyelftoolsver}.tar.gz

%define apply_patch %(test -s %{_sourcedir}/%{pkgname}-%{version}.patch && echo 1 || echo 0)

%if %{apply_patch}
Patch0: %{pkgname}-%{version}.patch
%endif

# The DPDK is designed to optimize througput of network traffic using, among
# other techniques, carefully crafted assembly instructions.  As such it
# needs extensive work to port it to other architectures.
ExclusiveArch: x86_64 aarch64 ppc64le s390x

# Do not enable this otherwise YUM will break on any upgrade.
# Provides: openvswitch
Conflicts: openvswitch < 3.4
Conflicts: openvswitch-dpdk < 3.4
Conflicts: openvswitch2.10
Conflicts: openvswitch2.11
Conflicts: openvswitch2.12
Conflicts: openvswitch2.13
Conflicts: openvswitch2.14
Conflicts: openvswitch2.15
Conflicts: openvswitch2.16
Conflicts: openvswitch2.17
Conflicts: openvswitch3.0
Conflicts: openvswitch3.1
Conflicts: openvswitch3.2
Conflicts: openvswitch3.3

# FIXME Sphinx is used to generate some manpages, unfortunately, on RHEL, it's
# in the -optional repository and so we can't require it directly since RHV
# doesn't have the -optional repository enabled and so TPS fails
%if %{external_sphinx}
BuildRequires: python3-sphinx
%else
# Sphinx dependencies
BuildRequires: python-devel
BuildRequires: python-setuptools
#BuildRequires: python2-docutils
BuildRequires: python-jinja2
BuildRequires: python-nose
#BuildRequires: python2-pygments
# docutils dependencies
BuildRequires: python-imaging
# pygments dependencies
BuildRequires: python-nose
%endif

BuildRequires: gcc gcc-c++ make
BuildRequires: autoconf automake libtool
BuildRequires: systemd-units systemd-rpm-macros openssl openssl-devel
BuildRequires: python3-devel python3-setuptools
BuildRequires: desktop-file-utils
BuildRequires: groff-base graphviz
BuildRequires: unbound-devel
BuildRequires: systemtap-sdt-devel
# make check dependencies
BuildRequires: procps-ng
%if %{with check_datapath_kernel}
BuildRequires: nmap-ncat
# would be useful but not available in RHEL or EPEL
#BuildRequires: pyftpdlib
%endif

%if %{with libcapng}
BuildRequires: libcap-ng libcap-ng-devel
%endif

%ifarch %{dpdkarches}
BuildRequires: meson
%if 0%{?rhel} > 8 || 0%{?fedora}
BuildRequires: python3-pyelftools
%endif
# DPDK driver dependencies
BuildRequires: zlib-devel numactl-devel libarchive-devel
# libarchive static dependencies
BuildRequires: bzip2-devel libacl-devel libxml2-devel libzstd-devel lz4-devel xz-devel
%ifarch x86_64
BuildRequires: rdma-core-devel >= 15 libmnl-devel
%endif

# Required by packaging policy for the bundled DPDK
Provides: bundled(dpdk) = %{dpdkver}
%endif

Requires: openssl iproute module-init-tools
#Upstream kernel commit 4f647e0a3c37b8d5086214128614a136064110c3
#Requires: kernel >= 3.15.0-0
Requires: openvswitch-selinux-extra-policy

%{?sysusers_requires_compat}
Requires(post): /bin/sed
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Obsoletes: openvswitch-controller <= 0:2.1.0-1

%if 0%{?rhel}
# sortedcontainers are not packaged on RHEL yet, but ovs includes it
%global __requires_exclude ^python%{python3_version}dist\\(sortedcontainers\\)$
%endif

%description
Open vSwitch provides standard network bridging functions and
support for the OpenFlow protocol for remote per-flow control of
traffic.

%package -n python3-%{pkgname}
Summary: Open vSwitch python3 bindings
License: ASL 2.0
Requires: %{pkgname} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides: python-%{pkgname} = %{?epoch:%{epoch}:}%{version}-%{release}

%description -n python3-%{pkgname}
Python bindings for the Open vSwitch database

%package test
Summary: Open vSwitch testing utilities
License: ASL 2.0
BuildArch: noarch
Requires: python3-%{pkgname} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: tcpdump

%description test
Utilities that are useful to diagnose performance and connectivity
issues in Open vSwitch setup.

%package devel
Summary: Open vSwitch OpenFlow development package (library, headers)
License: ASL 2.0
Requires: %{pkgname} = %{?epoch:%{epoch}:}%{version}-%{release}

%description devel
This provides shared library, libopenswitch.so and the openvswitch header
files needed to build an external application.

%if 0%{?rhel} == 8 || 0%{?fedora} > 28
%package -n network-scripts-%{name}
Summary: Open vSwitch legacy network service support
License: ASL 2.0
Requires: network-scripts
Supplements: (%{name} and network-scripts)

%description -n network-scripts-%{name}
This provides the ifup and ifdown scripts for use with the legacy network
service.
%endif

%if %{with ipsec}
%package ipsec
Summary: Open vSwitch IPsec tunneling support
License: ASL 2.0
Requires: python3-%{pkgname} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: libreswan

%description ipsec
This package provides IPsec tunneling support for OVS tunnels.
%endif

%prep
%if 0%{?commit:1}
%setup -q -n ovs-%{commit} -a 10
%else
%setup -q -n ovs-%{version} -a 10
%endif
%if ! %{external_sphinx}
%if 0%{?commit:1}
%setup -n ovs-%{commit} -q -D -T -a 100 -a 101 -a 102
%else
%setup -n ovs-%{version} -q -D -T -a 100 -a 101 -a 102
%endif
%endif
%if 0%{?rhel} && 0%{?rhel} < 9
%if 0%{?commit:1}
%setup -n ovs-%{commit} -q -D -T -a 103
%else
%setup -n ovs-%{version} -q -D -T -a 103
%endif
%endif

mv dpdk-*/ %{dpdkdir}/

%if %{apply_patch}
%patch0 -p 1
%endif

%build
%if 0%{?rhel} && 0%{?rhel} < 9
export PYTHONPATH="${PWD}/pyelftools-%{pyelftoolsver}"
%endif
# Build Sphinx on RHEL
%if ! %{external_sphinx}
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}%{_builddir}/pytmp/lib/python"
for x in docutils-%{docutilsver} Pygments-%{pygmentsver} Sphinx-%{sphinxver}; do
    pushd "$x"
    python2 setup.py install --home %{_builddir}/pytmp
    popd
done

export PATH="$PATH:%{_builddir}/pytmp/bin"
%endif

./boot.sh

%ifarch %{dpdkarches}    # build dpdk
# Lets build DPDK first
cd %{dpdkdir}

ENABLED_DRIVERS=(
    bus/pci
    bus/vdev
    mempool/ring
    net/failsafe
    net/i40e
    net/ring
    net/vhost
    net/virtio
    net/tap
)

%ifarch x86_64
ENABLED_DRIVERS+=(
    baseband/acc
    bus/auxiliary
    bus/vmbus
    common/iavf
    common/mlx5
    common/nfp
    net/bnxt
    net/enic
    net/iavf
    net/ice
    net/mlx5
    net/netvsc
    net/nfp
    net/qede
    net/vdev_netvsc
)
%endif

%ifarch aarch64 x86_64
ENABLED_DRIVERS+=(
    net/e1000
    net/ixgbe
)
%endif

for driver in "${ENABLED_DRIVERS[@]}"; do
    enable_drivers="${enable_drivers:+$enable_drivers,}"$driver
done

# If doing any updates, this must be aligned with:
# https://access.redhat.com/articles/3538141
ENABLED_LIBS=(
    bbdev
    bitratestats
    bpf
    cmdline
    cryptodev
    dmadev
    gro
    gso
    hash
    ip_frag
    latencystats
    member
    meter
    metrics
    pcapng
    pdump
    security
    stack
    vhost
)

for lib in "${ENABLED_LIBS[@]}"; do
    enable_libs="${enable_libs:+$enable_libs,}"$lib
done

%set_build_flags
%__meson --prefix=%{_builddir}/dpdk-build \
         --buildtype=plain \
         -Denable_libs="$enable_libs" \
         -Ddisable_apps="*" \
         -Denable_drivers="$enable_drivers" \
         -Dplatform=generic \
         -Dmax_ethports=1024 \
         -Dmax_numa_nodes=8 \
         -Dtests=false \
         %{_vpath_builddir}
%meson_build
%__meson install -C %{_vpath_builddir} --no-rebuild

# FIXME currently with LTO enabled OVS tries to link with both static and shared libraries
rm -v %{_builddir}/dpdk-build/%{_lib}/*.so*

# Generate a list of supported drivers, its hard to tell otherwise.
cat << EOF > README.DPDK-PMDS
DPDK drivers included in this package:

EOF

for f in %{_builddir}/dpdk-build/%{_lib}/librte_net_*.a; do
    basename ${f} | cut -c12- | cut -d. -f1 | tr [:lower:] [:upper:]
done >> README.DPDK-PMDS

cat << EOF >> README.DPDK-PMDS

For further information about the drivers, see
http://dpdk.org/doc/guides-%{dpdksver}/nics/index.html
EOF

cd -
%endif    # build dpdk

# And now for OVS...
mkdir build-shared build-static
pushd build-shared
ln -s ../configure
%configure \
%if %{with libcapng}
        --enable-libcapng \
%else
        --disable-libcapng \
%endif
        --disable-static \
        --enable-shared \
        --enable-ssl \
        --with-pkidir=%{_sharedstatedir}/openvswitch/pki \
        --enable-usdt-probes \
        --disable-afxdp \
        --with-version-suffix=-%{release}
make %{?_smp_mflags}
popd
pushd build-static
ln -s ../configure
%ifarch %{dpdkarches}
PKG_CONFIG_PATH=%{_builddir}/dpdk-build/%{_lib}/pkgconfig \
%endif
%configure \
%if %{with libcapng}
        --enable-libcapng \
%else
        --disable-libcapng \
%endif
        --enable-ssl \
%ifarch %{dpdkarches}
        --with-dpdk=static \
%endif
        --with-pkidir=%{_sharedstatedir}/openvswitch/pki \
        --enable-usdt-probes \
        --disable-afxdp \
        --with-version-suffix=-%{release}
make %{?_smp_mflags}
popd

/usr/bin/python3 build-aux/dpdkstrip.py \
        --dpdk \
        < rhel/usr_lib_systemd_system_ovs-vswitchd.service.in \
        > rhel/usr_lib_systemd_system_ovs-vswitchd.service

%install
rm -rf $RPM_BUILD_ROOT
make -C build-shared install sbin_PROGRAMS=ovsdb/ovsdb-server DESTDIR=$RPM_BUILD_ROOT
make -C build-static install bin_PROGRAMS= sbin_PROGRAMS=vswitchd/ovs-vswitchd DESTDIR=$RPM_BUILD_ROOT

install -d -m 0755 $RPM_BUILD_ROOT%{_rundir}/openvswitch
install -d -m 0750 $RPM_BUILD_ROOT%{_localstatedir}/log/openvswitch
install -d -m 0755 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch

install -p -D -m 0644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysusersdir}/openvswitch.conf
%ifarch %{dpdkarches}
install -p -D -m 0644 %{SOURCE3} $RPM_BUILD_ROOT%{_sysusersdir}/openvswitch-hugetlbfs.conf
%endif

install -p -D -m 0644 rhel/usr_lib_udev_rules.d_91-vfio.rules \
        $RPM_BUILD_ROOT%{_udevrulesdir}/91-vfio.rules

install -p -D -m 0644 \
        rhel/usr_share_openvswitch_scripts_systemd_sysconfig.template \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/openvswitch

for service in openvswitch ovsdb-server ovs-vswitchd \
               ovs-delete-transient-ports; do
        install -p -D -m 0644 \
                        rhel/usr_lib_systemd_system_${service}.service \
                        $RPM_BUILD_ROOT%{_unitdir}/${service}.service
done

%if %{with ipsec}
install -p -D -m 0644 rhel/usr_lib_systemd_system_openvswitch-ipsec.service \
                      $RPM_BUILD_ROOT%{_unitdir}/openvswitch-ipsec.service
%endif

install -m 0755 rhel/etc_init.d_openvswitch \
        $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/openvswitch.init

install -p -D -m 0644 rhel/etc_openvswitch_default.conf \
        $RPM_BUILD_ROOT/%{_sysconfdir}/openvswitch/default.conf

install -p -D -m 0644 rhel/etc_logrotate.d_openvswitch \
        $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/openvswitch

install -m 0644 vswitchd/vswitch.ovsschema \
        $RPM_BUILD_ROOT/%{_datadir}/openvswitch/vswitch.ovsschema

%if 0%{?rhel} < 9
install -d -m 0755 $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifdown-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
install -p -m 0755 rhel/etc_sysconfig_network-scripts_ifup-ovs \
        $RPM_BUILD_ROOT/%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%endif

install -d -m 0755 $RPM_BUILD_ROOT%{python3_sitelib}
cp -a $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/ovstest \
        $RPM_BUILD_ROOT%{python3_sitelib}

# Build the JSON C extension for the Python lib (#1417738)
pushd python
(
export CPPFLAGS="-I ../include -I ../build-shared/include"
export LDFLAGS="%{__global_ldflags} -L $RPM_BUILD_ROOT%{_libdir}"
%py3_build
%py3_install
[ -f "$RPM_BUILD_ROOT/%{python3_sitearch}/ovs/_json$(python3-config --extension-suffix)" ]
)
popd

rm -rf $RPM_BUILD_ROOT/%{_datadir}/openvswitch/python/

install -d -m 0755 $RPM_BUILD_ROOT/%{_sharedstatedir}/openvswitch

install -d -m 0755 $RPM_BUILD_ROOT%{_prefix}/lib/firewalld/services/

install -p -D -m 0755 \
        rhel/usr_share_openvswitch_scripts_ovs-systemd-reload \
        $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/ovs-systemd-reload

touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/conf.db
# The db needs special permission as IPsec Pre-shared keys are stored in it.
chmod 0640 $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/conf.db

touch $RPM_BUILD_ROOT%{_sysconfdir}/openvswitch/system-id.conf

# remove unpackaged files
rm -f $RPM_BUILD_ROOT/%{_bindir}/ovs-benchmark \
        $RPM_BUILD_ROOT/%{_bindir}/ovs-docker \
        $RPM_BUILD_ROOT/%{_bindir}/ovs-parse-backtrace \
        $RPM_BUILD_ROOT/%{_bindir}/ovs-testcontroller \
        $RPM_BUILD_ROOT/%{_sbindir}/ovs-vlan-bug-workaround \
        $RPM_BUILD_ROOT/%{_mandir}/man1/ovs-benchmark.1* \
        $RPM_BUILD_ROOT/%{_mandir}/man8/ovs-testcontroller.* \
        $RPM_BUILD_ROOT/%{_mandir}/man8/ovs-vlan-bug-workaround.8*

%if ! %{with ipsec}
rm -f $RPM_BUILD_ROOT/%{_datadir}/openvswitch/scripts/ovs-monitor-ipsec
%endif

# remove ovn unpackages files
rm -f $RPM_BUILD_ROOT%{_bindir}/ovn*
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/ovn*
rm -f $RPM_BUILD_ROOT%{_mandir}/man5/ovn*
rm -f $RPM_BUILD_ROOT%{_mandir}/man7/ovn*
rm -f $RPM_BUILD_ROOT%{_mandir}/man8/ovn*
rm -f $RPM_BUILD_ROOT%{_datadir}/openvswitch/ovn*
rm -f $RPM_BUILD_ROOT%{_datadir}/openvswitch/scripts/ovn*
rm -f $RPM_BUILD_ROOT%{_includedir}/ovn/*

%check
%if %{with check}
    pushd build-static
    touch resolv.conf
    export OVS_RESOLV_CONF=$(pwd)/resolv.conf
    if make check TESTSUITEFLAGS='%{_smp_mflags}' ||
       make check TESTSUITEFLAGS='--recheck'; then :;
    else
        cat tests/testsuite.log
        exit 1
    fi
    popd
%endif
%if %{with check_datapath_kernel}
    pushd build-static
    if make check-kernel RECHECK=yes; then :;
    else
        cat tests/system-kmod-testsuite.log
        exit 1
    fi
    popd
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%preun
%if 0%{?systemd_preun:1}
    %systemd_preun openvswitch.service
%else
    if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
        /bin/systemctl --no-reload disable openvswitch.service >/dev/null 2>&1 || :
        /bin/systemctl stop openvswitch.service >/dev/null 2>&1 || :
    fi
%endif

%pre
%sysusers_create_compat %{SOURCE2}
%ifarch %{dpdkarches}
%sysusers_create_compat %{SOURCE3}
%endif

%post
if [ $1 -eq 1 ]; then
    sed -i 's:^#OVS_USER_ID=:OVS_USER_ID=:' /etc/sysconfig/openvswitch

%ifarch %{dpdkarches}
    sed -i \
        's@OVS_USER_ID="openvswitch:openvswitch"@OVS_USER_ID="openvswitch:hugetlbfs"@'\
        /etc/sysconfig/openvswitch
%endif
fi
chown -R openvswitch:openvswitch /etc/openvswitch

%if 0%{?systemd_post:1}
    %systemd_post openvswitch.service
%else
    # Package install, not upgrade
    if [ $1 -eq 1 ]; then
        /bin/systemctl daemon-reload >dev/null || :
    fi
%endif

%postun
%if 0%{?systemd_postun:1}
    %systemd_postun openvswitch.service
%else
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%triggerun -- openvswitch < 2.5.0-22.git20160727%{?dist}
# old rpm versions restart the service in postun, but
# due to systemd some preparation is needed.
if systemctl is-active openvswitch >/dev/null 2>&1 ; then
    /usr/share/openvswitch/scripts/ovs-ctl stop >/dev/null 2>&1 || :
    systemctl daemon-reload >/dev/null 2>&1 || :
    systemctl stop openvswitch ovsdb-server ovs-vswitchd >/dev/null 2>&1 || :
    systemctl start openvswitch >/dev/null 2>&1 || :
fi
exit 0

%files -n python3-%{pkgname}
%{python3_sitearch}/ovs
%{python3_sitearch}/ovs-*.egg-info
%doc LICENSE

%files test
%{_bindir}/ovs-pcap
%{_bindir}/ovs-tcpdump
%{_bindir}/ovs-tcpundump
%{_datadir}/openvswitch/scripts/usdt/*
%{_mandir}/man1/ovs-pcap.1*
%{_mandir}/man8/ovs-tcpdump.8*
%{_mandir}/man1/ovs-tcpundump.1*
%{_bindir}/ovs-test
%{_bindir}/ovs-vlan-test
%{_bindir}/ovs-l3ping
%{_mandir}/man8/ovs-test.8*
%{_mandir}/man8/ovs-vlan-test.8*
%{_mandir}/man8/ovs-l3ping.8*
%{python3_sitelib}/ovstest

%files devel
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
%{_includedir}/openvswitch/*
%{_includedir}/openflow/*
%exclude %{_libdir}/*.a
%exclude %{_libdir}/*.la

%if 0%{?rhel} == 8 || 0%{?fedora} > 28
%files -n network-scripts-%{name}
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%endif

%files
%defattr(-,openvswitch,openvswitch)
%dir %{_sysconfdir}/openvswitch
%{_sysconfdir}/openvswitch/default.conf
%config %ghost %verify(not owner group md5 size mtime) %{_sysconfdir}/openvswitch/conf.db
%ghost %attr(0600,-,-) %verify(not owner group md5 size mtime) %{_sysconfdir}/openvswitch/.conf.db.~lock~
%config %ghost %{_sysconfdir}/openvswitch/system-id.conf
%defattr(-,root,root)
%config(noreplace) %verify(not md5 size mtime) %{_sysconfdir}/sysconfig/openvswitch
%{_sysconfdir}/bash_completion.d/ovs-appctl-bashcomp.bash
%{_sysconfdir}/bash_completion.d/ovs-vsctl-bashcomp.bash
%config(noreplace) %{_sysconfdir}/logrotate.d/openvswitch
%{_unitdir}/openvswitch.service
%{_unitdir}/ovsdb-server.service
%{_unitdir}/ovs-vswitchd.service
%{_unitdir}/ovs-delete-transient-ports.service
%{_datadir}/openvswitch/scripts/openvswitch.init
%{_datadir}/openvswitch/scripts/ovs-check-dead-ifs
%{_datadir}/openvswitch/scripts/ovs-lib
%{_datadir}/openvswitch/scripts/ovs-save
%{_datadir}/openvswitch/scripts/ovs-vtep
%{_datadir}/openvswitch/scripts/ovs-ctl
%{_datadir}/openvswitch/scripts/ovs-kmod-ctl
%{_datadir}/openvswitch/scripts/ovs-systemd-reload
%config %{_datadir}/openvswitch/local-config.ovsschema
%config %{_datadir}/openvswitch/vswitch.ovsschema
%config %{_datadir}/openvswitch/vtep.ovsschema
%{_bindir}/ovs-appctl
%{_bindir}/ovs-dpctl
%{_bindir}/ovs-ofctl
%{_bindir}/ovs-vsctl
%{_bindir}/ovsdb-client
%{_bindir}/ovsdb-tool
%{_bindir}/ovs-pki
%{_bindir}/vtep-ctl
%{_libdir}/*.so.*
%{_sbindir}/ovs-vswitchd
%{_sbindir}/ovsdb-server
%{_mandir}/man1/ovsdb-client.1*
%{_mandir}/man1/ovsdb-server.1*
%{_mandir}/man1/ovsdb-tool.1*
%{_mandir}/man5/ovsdb.5*
%{_mandir}/man5/ovsdb.local-config.5*
%{_mandir}/man5/ovsdb-server.5.*
%{_mandir}/man5/ovs-vswitchd.conf.db.5*
%{_mandir}/man5/vtep.5*
%{_mandir}/man7/ovsdb-server.7*
%{_mandir}/man7/ovsdb.7*
%{_mandir}/man7/ovs-actions.7*
%{_mandir}/man7/ovs-fields.7*
%{_mandir}/man8/vtep-ctl.8*
%{_mandir}/man8/ovs-appctl.8*
%{_mandir}/man8/ovs-ctl.8*
%{_mandir}/man8/ovs-dpctl.8*
%{_mandir}/man8/ovs-kmod-ctl.8.*
%{_mandir}/man8/ovs-ofctl.8*
%{_mandir}/man8/ovs-pki.8*
%{_mandir}/man8/ovs-vsctl.8*
%{_mandir}/man8/ovs-vswitchd.8*
%{_mandir}/man8/ovs-parse-backtrace.8*
%{_udevrulesdir}/91-vfio.rules
%doc LICENSE NOTICE README.rst NEWS rhel/README.RHEL.rst
%ifarch %{dpdkarches}
%doc %{dpdkdir}/README.DPDK-PMDS
%attr(750,openvswitch,hugetlbfs) %verify(not owner group) /var/log/openvswitch
%else
%attr(750,openvswitch,openvswitch) %verify(not owner group) /var/log/openvswitch
%endif
/var/lib/openvswitch
%ghost %attr(755,root,root) %verify(not owner group) %{_rundir}/openvswitch
%{_datadir}/openvswitch/bugtool-plugins/
%{_datadir}/openvswitch/scripts/ovs-bugtool-*
%{_bindir}/ovs-dpctl-top
%{_sbindir}/ovs-bugtool
%{_mandir}/man8/ovs-dpctl-top.8*
%{_mandir}/man8/ovs-bugtool.8*
%if (0%{?rhel} && 0%{?rhel} <= 7) || (0%{?fedora} && 0%{?fedora} < 29)
%{_sysconfdir}/sysconfig/network-scripts/ifup-ovs
%{_sysconfdir}/sysconfig/network-scripts/ifdown-ovs
%endif
%{_sysusersdir}/openvswitch.conf
%ifarch %{dpdkarches}
%{_sysusersdir}/openvswitch-hugetlbfs.conf
%endif

%if %{with ipsec}
%files ipsec
%{_datadir}/openvswitch/scripts/ovs-monitor-ipsec
%{_unitdir}/openvswitch-ipsec.service
%endif

%changelog
* Tue Dec 31 2024 SupremeMortal 3.4.1-4
- 

* Tue Dec 31 2024 SupremeMortal 3.4.1-3
- Use source directory (6178101+SupremeMortal@users.noreply.github.com)

* Tue Dec 31 2024 SupremeMortal <6178101+SupremeMortal@users.noreply.github.com>
- Use source directory (6178101+SupremeMortal@users.noreply.github.com)

* Tue Dec 31 2024 SupremeMortal 3.4.1-2
- Fix build (6178101+SupremeMortal@users.noreply.github.com)

* Tue Dec 31 2024 SupremeMortal <6178101+SupremeMortal@users.noreply.github.com>
- Fix build (6178101+SupremeMortal@users.noreply.github.com)

* Tue Dec 31 2024 SupremeMortal 3.4.1-1
- new package built with tito

* Tue Dec 31 2024 SupremeMortal 3.4.1-1
- new package built with tito

* Fri Dec 13 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-27
- Merging upstream branch-3.4 [RH git: 9cfbb9a33d]
    Commit list:
    5346c14b9f m4: Fix check for Python 3.6 version.


* Fri Dec 13 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-26
- Merging upstream branch-3.4 [RH git: 4f020a4eb1]
    Commit list:
    84a98a8ba4 ofproto: Fix default pmd_id for ofproto/detrace.
    65efbaa56a github: Skip clang-analyze when reference generation fails.


* Thu Dec 12 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-25
- Merging upstream branch-3.4 [RH git: 513b808a85]
    Commit list:
    069f5a7763 netdev-dpdk: Restore outer UDP checksum for Intel nics.


* Wed Dec 11 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-24
- Merging upstream branch-3.4 [RH git: 99590fdaef]
    Commit list:
    acee757306 cirrus: Update to FreeBSD 14.2 and 13.4.
    eb98e20da3 bridge: Fix log spam about prefixes.


* Mon Dec 02 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-23
- Merging upstream branch-3.4 [RH git: 222ad449f6]
    Commit list:
    a234629c33 netdev: Always clear struct ifreq before ioctl.
    118b4f2076 netdev-native-tnl: Fix use of uninitialized RSS hash.
    49d8d3066c tests: Use OVS_CHECK_XT6 for all applicable IPv6 tests.
    8886c64c1f tests: Use OVS_CHECK_XT for all applicable IPv4 tests.
    985f7ee313 classifier: Fix the fieldspec comment in the prefix tracking section.
    07720bc3f6 tests: Handle marks using nft if available.
    f3de3ab1b6 tests: Add nft support to ADD_EXTERNAL_CT.
    5931c6feb7 tests: Add nft accept support.
    e4d76aacd9 ovs-macros.at: Correctly delete iptables rule on_exit.
    2cdd886fc0 system-traffic: Do not rely on conncount for already tracked packets. (FDP-708)


* Mon Dec 02 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-22
- Merging upstream branch-3.4 [RH git: 9f3c002b41]
    Commit list:
    2463a1bf90 system-traffic: Fix syntax errors in FTP and IPv6 curl calls.


* Fri Nov 29 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-21
- Merging upstream branch-3.4 [RH git: ac163d63af]
    Commit list:
    77e82fa315 ovsdb-idl: Fix use of uninitialized datum for graph consistency check.
    fb1dad5be1 db-ctl-base: Fix uninitialized datum fields while checking conditions.
    9bda0df40e ovsdb-types: Fix use of uninitialized reference type.
    3ed582f4a8 ofproto-dpif-upcall: Fix use of uninitialized missed dumps counter.
    fcc8c2a917 ovs-vsctl, vtep-ctl: Silence memory sanitizer warning for longindex.
    76c3deb141 tests: multipath: Fix use of uninitialized wildcards.
    b359f1cf78 stream: replay: Fix potential NULL dereference on write failure.
    4d8155a5c1 ofp-actions: Fix use of uninitialized padding in set-field.


* Fri Nov 29 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-20
- Merging upstream branch-3.4 [RH git: 6ad38fd5b2]
    Commit list:
    6d02d8749c system-traffic: Standardize by replacing all wget instances with curl.
    a946d61f57 system-traffic: Replace wget with curl for negative and ftp tests.


* Wed Nov 27 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-19
- Merging upstream branch-3.4 [RH git: f70b3859b4]
    Commit list:
    87efb3c94b classifier: Increase the maximum number of prefixes (tries).
    5338f3ebeb Revert "github: Skip FTP SNAT orig tuple tests due to broken Ubuntu kernel."


* Mon Nov 18 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-18
- Merging dpdk subtree [RH git: 8d84b5400c]
    Commit list:
    78610a5530 net/iavf: delay VF reset command (FDP-957)


* Sat Nov 16 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-17
- Merging upstream branch-3.4 [RH git: 4def588584]
    Commit list:
    c25085f3d7 Prepare for 3.4.2.
    22a6b1110a Set release date for 3.4.1.


* Fri Nov 15 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-16
- Merging upstream branch-3.4 [RH git: ee85c64e6a]
    Commit list:
    fde8912b00 tests: Fix transient failure in ping6 header modify. ()
    5cefc11140 github: Build Libreswan v5.1 from sources.


* Mon Nov 11 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-15
- Merging upstream branch-3.4 [RH git: bbc8d4cbb1]
    Commit list:
    3d0246e3c3 ci: Update GitHub actions runner from Ubuntu 22.04 to 24.04.
    5c13ad0002 dpdk: Fix dpdk logs being split over multiple lines.


* Mon Nov 04 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-14
- Merging upstream branch-3.4 [RH git: d3616fbd62]
    Commit list:
    c6fc230a5d ipsec: libreswan: Reduce chances for crossing streams.
    e9f9e1eff5 tests: ipsec: Check that nodes can ping each other in the NxN test.
    94aeab7de2 tests: ipsec: Add NxN + reconciliation test.
    992e09e4d1 system-tests: Verbose cleanup of ports and namespaces.
    a5b5fce084 ipsec: Make command timeout configurable.
    49b066b5c4 ipsec: libreswan: Avoid monitor hanging on stuck ipsec commands. (FDP-846)
    729b4813c4 ipsec: libreswan: Try to bring non-active connections up.
    cb981fdb3e ipsec: libreswan: Reconcile missing connections periodically.
    f95b566dba ipsec: libreswan: Fix regexp for connections waiting on child SA.
    f1fcf08b37 ipsec: Add a helper function to run commands from the monitor.


* Wed Oct 30 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-13
- Merging upstream branch-3.4 [RH git: 41fa65f465]
    Commit list:
    77dc74395e meta-flow: Fix nw_frag mask while parsing from string.
    7e6a298c0e ci: Remove dependency on libpcap.
    b2d2ca05c0 github: Remove ASLR entropy workaround.
    b00d1115c5 bond: Always revalidate unbalanced bonds when active member changes. (FDP-845)
    d9f1469317 ofproto-dpif-upcall: Fix redundant mirror on metadata modification. (FDP-699)


* Thu Oct 24 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-12
- Merging dpdk subtree [RH git: 270d3c6ce7]
    Commit list:
    e8eb14e00d version: 23.11.2
    8401a3e84b version: 23.11.2-rc2
    50e50f1d99 net/ice/base: fix preparing PHY for timesync command
    7302cab07c net/nfp: fix firmware abnormal cleanup
    92c5aa4387 net/nfp: forbid offload flow rules with empty action list
    e9c4dbd5be crypto/openssl: make per-QP auth context clones
    729e0848b7 examples: fix port ID restriction
    3fc9eb2f4f examples: fix lcore ID restriction
    776c4e37ee doc: add baseline mode in l3fwd-power guide
    8437250f9f doc: fix DMA performance test invocation
    d01561713d doc: describe mlx5 HWS actions order
    1ef3097094 doc: add power uncore in API index
    09ccd86606 doc: fix mbuf flags
    613a4879b4 examples/ipsec-secgw: revert SA salt endianness
    8b87ae54ed doc: remove reference to mbuf pkt field
    938afb0ab2 examples: fix queue ID restriction
    80da81b6f9 net/ice/base: fix temporary failures reading NVM
    034f533709 net/hns3: fix uninitialized variable in FEC query
    5fa2084ac3 examples/l3fwd: fix crash on multiple sockets
    1708229729 examples/l3fwd: fix crash in ACL mode for mixed traffic
    bef8327055 bus/vdev: fix device reinitialization
    971d455e59 malloc: fix multi-process wait condition handling
    b53fb811c0 power: fix number of uncore frequencies
    52bf7488c3 app/pdump: handle SIGTERM and SIGHUP
    6bed8020a3 app/dumpcap: handle SIGTERM and SIGHUP
    eacf416207 dma/hisilicon: remove support for HIP09 platform
    a5375f4492 bus/pci: fix FD in secondary process
    c076f02992 bus/pci: fix UIO resource mapping in secondary process
    ca12727f09 app/testpmd: fix build on signed comparison
    b858eb7a55 net/gve: fix Tx queue state on queue start
    7ff9eeeb71 ethdev: fix device init without socket-local memory
    890b02b907 app/testpmd: add postpone option to async flow destroy
    fbd7ac3b83 net/netvsc: use ethdev API to set VF MTU
    e8746659b2 ethdev: fix GENEVE option item conversion
    e2b3b0a5d4 net/ark: fix index arithmetic
    7deaec6ac8 net/hns3: check Rx DMA address alignmnent
    6bf4a626e4 net/mlx5: fix disabling E-Switch default flow rules
    3b60ef3db6 common/mlx5: remove unneeded field when modify RQ table
    1988c32194 net/mlx5: fix uplink port probing in bonding mode
    07ad92c1a6 net/mlx5: fix end condition of reading xstats
    b7c9a02306 net/mlx5/hws: remove unused variable
    1163643a1e net/mlx5/hws: fix port ID on root item convert
    4a80ab31f0 net/mlx5/hws: fix deletion of action vport
    dcd02c715e net/mlx5/hws: fix check of range templates
    3c9aff8fbf net/mlx5/hws: fix memory leak in modify header
    85eeb293b3 net/mlx5: fix MTU configuration
    c1792007ff net/mlx5: fix Arm build with GCC 9.1
    a8331ab8b2 net/mlx5: fix shared Rx queue data access race
    15e2b0e736 net/ice: fix return value for raw pattern parsing
    17e800edd1 net/ice: fix memory leaks in raw pattern parsing
    8f23521ad7 common/cnxk: fix integer overflow
    a408bd0bcb crypto/qat: fix placement of OOP offset
    b2acb5218f test/crypto: fix modex comparison
    d308cefc96 test/crypto: fix asymmetric capability test
    adffcf4383 test/crypto: remove unused stats in setup
    4b0d806bab doc: fix typo in l2fwd-crypto guide
    0e19bfa703 crypto/qat: fix log message typo
    5d66d4a3f0 test/crypto: fix allocation comment
    9fef0db81b crypto/ipsec_mb: fix function comment
    c6111cb5fd crypto/qat: fix GEN4 write
    f707532cde net/nfp: fix disabling 32-bit build
    de0c58c4b8 doc: update AF_XDP device plugin repository
    811fcdf23a net/nfp: adapt reverse sequence card
    ea7085704a net/nfp: remove unneeded logic for VLAN layer
    4c45c694ca doc: update metadata description in nfp guide
    174b2b5a9a net/nfp: fix getting firmware version
    241976029a net/nfp: remove redundant function call
    c90d304f0e net/gve: fix RSS hash endianness in DQO format
    316baf3f0b net/ena: fix checksum handling
    ffba3914ad net/ena: fix return value check
    db4ca6f1cb net/ena: fix bad checksum handling
    5453c7a0b0 net/nfp: fix repeat disable port
    51d6936232 net/nfp: fix dereference of null pointer
    d0d759188e net/nfp: disable ctrl VNIC queues on close
    c22c079e1c net/ionic: fix mbuf double-free when emptying array
    2e84f93745 net/nfp: fix flow mask table entry
    8df473a653 net/nfp: fix allocation of switch domain
    2a50559bfd net/netvsc: fix MTU set
    e2ef427581 net/nfp: fix IPv6 TTL and DSCP flow action
    3762e1ed03 net/vmxnet3: fix init logs
    fdc5f6074b net/txgbe: fix Rx interrupt
    2dfb54ff33 net/ngbe: fix memory leaks
    638e12515a net/txgbe: fix memory leaks
    d0a84e43b3 net/ngbe: fix MTU range
    0fe77d1de3 net/txgbe: fix MTU range
    db50b74b3c net/ngbe: fix hotplug remove
    5de5204582 net/txgbe: fix hotplug remove
    6d224307f6 net/ngbe: keep PHY power down while device probing
    658060fffe net/ngbe: add special config for YT8531SH-CA PHY
    85bd339e19 net/txgbe: fix VF promiscuous and allmulticast
    ea62ead19d net/txgbe: reconfigure more MAC Rx registers
    55d8be2055 net/txgbe: restrict configuration of VLAN strip offload
    ed2250e120 net/txgbe: fix Tx hang on queue disable
    6ea637699a net/txgbe: fix flow filters in VT mode
    842a7baf9c net/txgbe: fix tunnel packet parsing
    708d5a261b net/mana: fix uninitialized return value
    e113512712 app/testpmd: fix parsing for connection tracking item
    11b6493c45 doc: remove empty section from testpmd guide
    f11711212c app/testpmd: handle IEEE1588 init failure
    e7f8c62dfc net/cpfl: fix 32-bit build
    ec9de9db2d net/cpfl: add checks on control queue messages
    39b2b4c7de common/idpf: fix PTP message validation
    e0f453462f common/idpf: fix flex descriptor mask
    bd5b88d172 net/ice/base: fix masking when reading context
    67a40ce4ef net/ice/base: fix board type definition
    5167b4d2d3 net/ice/base: fix potential TLV length overflow
    abd055ea63 net/ice/base: fix check for existing switch rule
    fddfbdbf49 net/ice/base: fix return type of bitmap hamming weight
    c9eae16d5e net/ice/base: fix GCS descriptor field offsets
    8bc9ae6b59 net/ice/base: fix size when allocating children arrays
    1257bf9a7c net/ice/base: fix sign extension
    2458257e56 net/ice/base: fix resource leak
    7a6c0e6212 net/ice/base: fix memory leak in firmware version check
    87d7cf4082 net/ice/base: fix pointer to variable outside scope
    aafeb830bc buildtools: fix build with clang 17 and ASan
    a4e8a4f488 fbarray: fix finding for unaligned length
    d88beb497f net/mlx5: fix start without duplicate flow patterns
    77231b2598 net/dpaa: forbid MTU configuration for shared interface
    d21248db89 bus/dpaa: remove redundant file descriptor check
    bb85c1fd72 common/dpaax: fix node array overrun
    90c9f938e5 common/dpaax: fix IOVA table cleanup
    0b4bc3a5d1 bus/dpaa: fix memory leak in bus scan
    d36efdb2cd bus/dpaa: fix bus scan for DMA devices
    daa0d9edd1 app/testpmd: fix help string of BPF load command
    7353cb767f dma/idxd: fix setup with Ubuntu 24.04
    f563086258 eal/linux: lower log level on allocation attempt failure
    8ccf607fad devtools: fix symbol listing
    997166395e fbarray: fix lookbehind ignore mask handling
    8baf379032 fbarray: fix lookahead ignore mask handling
    24869bf93c fbarray: fix incorrect lookbehind behavior
    5e66590575 fbarray: fix incorrect lookahead behavior
    427fa07238 examples/ipsec-secgw: fix SA salt endianness
    d0d02993de crypto/dpaa2_sec: fix event queue user context
    6e2def6ca9 crypto/dpaa_sec: fix IPsec descriptor
    b977583692 common/dpaax/caamflib: fix PDCP AES-AES watchdog error
    5089ef6c28 common/dpaax/caamflib: fix PDCP-SDAP watchdog error
    4af94ab6e2 crypto/openssl: set cipher padding once
    4f8c97e941 crypto/openssl: make per-QP cipher context clones
    ee88b9496c crypto/openssl: optimize 3DES-CTR context init
    eb6a1a85e6 crypto/openssl: fix GCM and CCM thread unsafe contexts
    cc8ca588a0 examples/fips_validation: fix dereference and out-of-bound
    9b3e235581 cryptodev: validate crypto callbacks from next node
    578ee20720 cryptodev: fix build without crypto callbacks
    fbb350108f crypto/cnxk: fix minimal input normalization
    7978b75d1b test/crypto: validate modex from first non-zero
    ede34a4359 app/crypto-perf: fix result for asymmetric
    7469762567 app/crypto-perf: remove redundant local variable
    e585a0db98 crypto/cnxk: fix ECDH public key verification
    6034788bd6 crypto/cnxk: fix out-of-bound access
    ea90bc49fc net/virtio-user: fix control queue allocation for non-vDPA
    15d3dfa07a baseband/la12xx: forbid secondary process
    f798848548 telemetry: fix connection parameter parsing
    713520f91d bpf: fix load hangs with six IPv6 addresses
    59523f029e bpf: fix MOV instruction evaluation
    c9071e44b7 mbuf: fix dynamic fields copy
    c13a819a44 graph: fix mcore dispatch walk
    777f0bc1a5 vdpa/sfc: remove dead code
    583796e298 dmadev: fix structure alignment
    d859544e45 common/cnxk: fix flow aging on application exit
    c343cb088f app/bbdev: fix interrupt tests
    0c99a3d922 app/bbdev: fix MLD output size computation
    179f1c6e6b app/bbdev: fix TB logic
    acdd88c4f9 build: use builtin helper for python dependencies
    edfa6a87c8 config: fix warning for cross build with meson >= 1.3.0
    151a54d0b6 v23.11.2-rc1
    61b7d1f4c1 doc: fix link to hugepage mapping from Linux guide
    0e68080faf telemetry: lower log level on socket error
    4fe42b5bd5 test/crypto: fix enqueue/dequeue callback case
    4dc08a4d14 test/crypto: fix RSA cases in QAT suite
    f1e088abb9 net/mlx5/hws: fix matcher reconnect
    db0c8afc11 net/mlx5: fix crash on counter pool destroy
    59e27c048f net/mlx5: support jump in meter hierarchy
    15d0fcf1ac net/mlx5: fix access to flow template operations
    7cc4f4359e net/mlx5: break flow resource release loop
    8f7a4c4861 net/mlx5: fix flow template indirect action failure
    0caa8332a4 net/mlx5: fix hash Rx queue release in flow sample
    5546ccbefe net/mlx5: fix indexed pool with invalid index
    c12bd3ffbf net/mlx5/hws: fix action template dump
    096734a9b5 net/mlx5/hws: set default miss when replacing table
    df8e365511 net/mlx5/hws: extend tag saving for match and jumbo
    9b84b09d4a net/mlx5/hws: add template match none flag
    8b2eb11323 net/mlx5/hws: fix spinlock release on context open
    3811ef8d25 net/mlx5/hws: fix function comment
    21c0e76d5a common/mlx5: fix PRM structs
    aec70880d8 net/mlx5/hws: decrease log level for creation failure
    b4d5b769a9 common/mlx5: fix unsigned/signed mismatch
    5405ea2f7a hash: fix RCU reclamation size
    2f62695370 bpf: disable on 32-bit x86
    61c4175079 graph: fix stats retrieval while destroying a graph
    e022af0b88 graph: fix ID collisions
    4541f5810c net/cnxk: fix promiscuous state after MAC change
    144a806a1b net/cnxk: fix outbound security with higher packet burst
    01d4a05a9f net/cnxk: update SA userdata and keep original cookie
    802a3a7d74 net/cnxk: fix extbuf handling for multisegment packet
    67a8e5ba52 common/cnxk: fix segregation of logs based on module
    c99b186412 common/cnxk: fix flow aging cleanup
    af85590165 net/cnxk: fix RSS config
    1e2d3032e2 net/ixgbe/base: fix PHY ID for X550
    b371343ddc net/ixgbe/base: fix 5G link speed reported on VF
    3d128f41b7 net/ixgbe/base: revert advertising for X550 2.5G/5G
    7ec2441a3e net/e1000/base: fix link power down
    4c8436297f net/ixgbe: do not create delayed interrupt handler twice
    f683115cef net/ixgbe: do not update link status in secondary process
    0fc2747f6c net/ice: fix VLAN stripping in double VLAN mode
    729144bdae net/fm10k: fix cleanup during init failure
    bb9096e474 net/iavf: fix VF reset when using DCF
    b6e445d0d4 eventdev/crypto: fix opaque field handling
    32c7c20981 event/sw: fix warning from useless snprintf
    614773e8c7 baseband/acc: fix memory barrier
    ac1bd05172 net/virtio: fix MAC table update
    eb821e0ed1 net/virtio-user: fix control queue allocation
    6e4de6f224 net/virtio-user: fix shadow control queue notification init
    1d824e440e net/virtio-user: fix control queue destruction
    2fdb8840ee vhost: cleanup resubmit info before inflight setup
    8c020a6f4d vhost: fix build with GCC 13
    1af612de7e hash: check name when creating a hash
    9616fce23b hash: fix return code description in Doxygen
    44bcfd6b38 net/nfp: fix xstats for multi PF firmware
    8bf40f1d11 app/testpmd: fix lcore ID restriction
    80c5c9789b net/iavf: remove outer UDP checksum offload for X710 VF
    1970a0ca45 net/i40e: fix outer UDP checksum offload for X710
    e8c2cccfbd net: fix outer UDP checksum in Intel prepare helper
    dda814c495 app/testpmd: fix outer IP checksum offload
    4d57f72a5b net/ice: fix check for outer UDP checksum offload
    c61b23292e net/axgbe: fix linkup in PHY status
    b7eddfc563 net/axgbe: delay AN timeout during KR training
    388f022054 net/axgbe: fix Tx flow on 30H HW
    e3632f6bbb net/axgbe: check only minimum speed for cables
    141a4ff6d5 net/axgbe: fix connection for SFP+ active cables
    4eda15db34 net/axgbe: fix SFP codes check for DAC cables
    d72913dcad net/axgbe: enable PLL control for fixed PHY modes only
    3cf40bf1c3 net/axgbe: disable RRC for yellow carp devices
    ec06a8c3d4 net/axgbe: disable interrupts during device removal
    a2be089e35 net/axgbe: update DMA coherency values
    17290bc90b net/axgbe: fix fluctuations for 1G Bel Fuse SFP
    a61b3c008a net/axgbe: reset link when link never comes back
    498a5720e3 net/axgbe: fix MDIO access for non-zero ports and CL45 PHYs
    dea5481a8f net/tap: fix file descriptor check in isolated flow
    c22f99f86c net/nfp: fix configuration BAR
    ab2e5cf865 net/nfp: fix resource leak in secondary process
    442ca8b2ec net/af_xdp: remove unused local statistic
    b0a4771394 net/af_xdp: fix stats reset
    fdda0d4d83 net/af_xdp: count mbuf allocation failures
    c6891273d3 net/af_xdp: fix port ID in Rx mbuf
    60f2e572ea doc: fix testpmd ring size command
    bd69f5a43d net/af_packet: align Rx/Tx structs to cache line
    e9da7f4655 net/vmxnet3: add missing register command
    e754c1c6d8 ethdev: fix strict aliasing in link up
    b1be619a77 net/af_xdp: fix multi-interface support for k8s
    3bbccce3a9 doc: fix AF_XDP device plugin howto
    02d2453afc net/hns3: disable SCTP verification tag for RSS hash input
    6e37e43fe3 net/hns3: fix variable overflow
    16a24e9f99 net/hns3: fix double free for Rx/Tx queue
    78e4da4546 net/hns3: fix Rx timestamp flag
    c491084749 net/hns3: fix offload flag of IEEE 1588
    beda536606 app/testpmd: fix indirect action flush
    dae924d0a2 net/bonding: fix failover time of LACP with mode 4
    453e0c281b net/nfp: fix representor port queue release
    83149f4fea latencystats: fix literal float suffix
    50b99c8b12 eal/windows: install sched.h file
    11af26df38 net/virtio-user: add memcpy check
    eb02060534 pcapng: add memcpy check
    2dd9223248 eal/unix: support ZSTD compression for firmware
    09e70301ee eal: fix type in destructor macro for MSVC
    338632b663 bus/pci: fix build with musl 1.2.4 / Alpine 3.19
    a6ec5765cf version: 23.11.1
    51783c9b60 version: 23.11.1-rc2
    152600d10e net/mlx5/hws: fix tunnel protocol checks
    67f3179f5c net/mlx5: fix rollback on failed flow configure
    750d393405 net/mlx5: fix async flow create error handling
    41c5baeffc net/mlx5/hws: fix port ID for root table
    cfa8a4cb90 net/ena/base: fix metrics excessive memory consumption
    a20a3c1129 dts: strip whitespaces from stdout and stderr
    abc6816134 examples/ipsec-secgw: fix typo in error message
    cf631810bf test/cfgfile: fix typo in error messages
    f48e923b46 test/power: fix typo in error message
    ed3a625fe6 doc: fix typo in packet framework guide
    e85092f875 doc: fix typo in profiling guide
    df1119d4a9 net/mlx5: fix sync flow meter action
    aeebcd33c0 net/mlx5/hws: fix memory access in L3 decapsulation
    0291a1f49e net/igc: fix timesync disable
    07fde8240d net/vmxnet3: ignore Rx queue interrupt setup on FreeBSD
    d2d309e5cf net/ena: fix mbuf double free in fast free mode
    f7d1b5cff3 app/testpmd: fix auto-completion for indirect action list
    4aa1a64204 net/nfp: fix uninitialized variable
    a5ac9baa7a doc: fix default IP fragments maximum in programmer guide
    f7909e3c75 examples/ipsec-secgw: fix Rx queue ID in Rx callback
    0a44e64c41 net/bnxt: fix number of Tx queues being created
    5a8ca987e9 net/mlx5: fix warning about copy length
    2864fd3102 net/mlx5: fix drop action release timing
    9aba4dee4d net/mlx5: fix age position in hairpin split
    fc12ccc047 net/mlx5: prevent ioctl failure log flooding
    8117b4b2f7 net/mlx5: fix flow configure validation
    b1749f6ed2 net/mlx5: fix template clean up of FDB control flow rule
    3735e8e88c net/mlx5/hws: fix direct index insert on depend WQE
    859bafedf3 net/mlx5: fix DR context release ordering
    9a9f0acac6 net/mlx5: fix IP-in-IP tunnels recognition
    c551015ebb net/mlx5: remove duplication of L3 flow item validation
    a8b06881d9 net/mlx5: fix meter policy priority
    78d38b5d67 net/mlx5: fix VLAN ID in flow modify
    f01fd28181 doc: update link to Windows DevX in mlx5 guide
    af41defcf7 net/mlx5: fix non-masked indirect list meter translation
    1994df02c9 net/mlx5: fix indirect action async job initialization
    7192f0ed82 net/mlx5: fix sync meter processing in HWS
    50eb03f8d3 net/mlx5: fix HWS meter actions availability
    fe697bbce3 net/hns3: support new device
    97089aa02e app/testpmd: fix error message for invalid option
    92c08367ea app/testpmd: fix burst option parsing
    6c2174ad80 app/testpmd: fix --stats-period option check
    0884b3bd36 net/nfp: fix initialization failure flow
    dd48153b15 net/nfp: fix switch domain free check
    aa850bad00 net/ena/base: restructure interrupt handling
    e1abac3de0 net/ena/base: limit exponential backoff
    2fa8497bd3 net/ena: fix fast mbuf free
    5f75adca7e net/nfp: fix IPsec data endianness
    bec3117648 net/nfp: fix getting firmware VNIC version
    5853ebb3b9 doc: add link speeds configuration in features table
    15952c71eb app/testpmd: fix async indirect action list creation
    166c5df810 doc: add traffic manager in features table
    cadb90f711 net/hns3: enable PFC for all user priorities
    72d3dfa9de crypto/qat: fix crash with CCM null AAD pointer
    90d0e13d7d examples/ipsec-secgw: fix cryptodev to SA mapping
    9796ac2ab8 build: pass cflags in subproject
    7105c8a299 net/virtio: fix vDPA device init advertising control queue
    587143897e examples/l3fwd: fix Rx queue configuration
    2f8836901c dts: fix smoke tests driver regex
    ce95b8c9cd examples/l3fwd: fix Rx over not ready port
    10296d5f50 examples/packet_ordering: fix Rx with reorder mode disabled
    e8dccbca30 test: do not count skipped tests as executed
    5c5df0f292 test: assume C source files are UTF-8 encoded
    de3976eb27 test/mbuf: fix external mbuf case with assert enabled
    ced51dd5ef config: fix CPU instruction set for cross-build
    6148604a43 bus/vdev: fix devargs in secondary process
    ef4c8a57f3 test: fix probing in secondary process
    272feb8eb9 net/mlx5: remove device status check in flow creation
    a10a65c396 net/mlx5: fix flow action template expansion
    0c31d1220f net/mlx5: fix counters map in bonding mode
    091234f3cb net/mlx5: fix flow counter cache starvation
    b90c42e4ff net/mlx5: fix parameters verification in HWS table create
    0198b11a11 net/mlx5: fix VLAN handling in meter split
    86c66608c2 net/mlx5/hws: enable multiple integrity items
    ca1084cd48 net/mlx5: fix HWS registers initialization
    527857d5c2 net/mlx5: fix connection tracking action validation
    1d65510ff6 net/mlx5: fix conntrack action handle representation
    a5d0545e5d net/mlx5: fix condition of LACP miss flow
    17f644b4a8 net/mlx5/hws: fix VLAN inner type
    99be466799 net/mlx5: prevent querying aged flows on uninit port
    bfa6cbba4c net/mlx5: fix error packets drop in regular Rx
    213cb88068 net/mlx5: fix use after free when releasing Tx queues
    a06ab8044a net/mlx5/hws: fix VLAN item in non-relaxed mode
    21d51e8848 net/mlx5/hws: check not supported fields in VXLAN
    b80ca5960e net/mlx5/hws: skip item when inserting rules by index
    2368f82fd8 doc: fix aging poll frequency option in cnxk guide
    630dbc8a92 net/cnxk: improve Tx performance for SW mbuf free
    37256aa1bf common/cnxk: fix possible out-of-bounds access
    9172348240 common/cnxk: remove dead code
    9cb9b9c8a0 common/cnxk: fix link config for SDP
    6f05d2d461 net/cnxk: fix mbuf fields in multi-segment Tx
    a6bd2f39c1 common/cnxk: fix mbox struct attributes
    e5450b2bba net/cnxk: add cookies check for multi-segment offload
    0e5159a223 net/cnxk: fix indirect mbuf handling in Tx
    6c6cd1fe53 common/cnxk: fix RSS RETA configuration
    f4c83ba01c net/cnxk: fix MTU limit
    3e73021b35 common/cnxk: fix Tx MTU configuration
    e71ac13a38 net/cnxk: fix buffer size configuration
    fbfaa5ae04 common/cnxk: remove CN9K inline IPsec FP opcodes
    b3ef799286 net/bnx2x: fix warnings about memcpy lengths
    2d11f389b0 net/cnxk: fix Rx packet format check condition
    8bc81d5447 common/cnxk: fix inline device pointer check
    dbdcd8bb85 net/ice: remove incorrect 16B descriptor read block
    72093d3d41 net/iavf: remove incorrect 16B descriptor read block
    542c8410cb net/i40e: remove incorrect 16B descriptor read block
    33b5bed057 net/ixgbe: increase VF reset timeout
    eefc0111de net/iavf: remove error logs for VLAN offloading
    2aa5a75750 net/ixgbevf: fix RSS init for x550 NICs
    a71de447a2 net/bnxt: fix null pointer dereference
    1d5bfd9fdf net/tap: fix traffic control handle calculation
    e9462a5690 net/tap: do not overwrite flow API errors
    4a1ffc9b02 app/testpmd: fix async flow create failure handling
    92ab2d6da2 app/testpmd: return if no packets in GRO heavy weight mode
    61ce57b13a net/mlx5: fix modify flex item
    4d1331e972 app/testpmd: fix flow modify tag typo
    c2d52df599 net/af_xdp: fix leak on XSK configuration failure
    b2dba501cf vhost: fix VDUSE device destruction failure
    af414b892d common/qat: fix legacy flag
    6cacd0e502 doc: fix typos in cryptodev overview
    14c38e2db1 app/crypto-perf: add missing op resubmission
    a1f1843146 app/crypto-perf: fix out-of-place mbuf size
    f0cfffc636 app/crypto-perf: fix copy segment size
    b2cd908926 eventdev/crypto: fix enqueueing
    e5ed464710 eventdev: fix Doxygen processing of vector struct
    2faf71417f eventdev: improve Doxygen comments on configure struct
    7721c9f498 test/event: fix crash in Tx adapter freeing
    524c60f422 event/dlb2: remove superfluous memcpy
    4e8d39a298 doc: fix configuration in baseband 5GNR driver guide
    b0b971bf66 23.11.1-rc1
    05bea47b81 app/testpmd: fix GRO packets flush on timeout
    cc670c7833 net/nfp: fix NFDk metadata process
    8e79562a0e net/nfp: fix NFD3 metadata process
    1f3f996269 net/mlx5: fix stats query crash in secondary process
    5982bea06b net/mlx5: fix GENEVE option item translation
    22653f6966 net/mlx5: remove GENEVE options length limitation
    06c494555f common/mlx5: fix query sample info capability
    10061b4047 common/mlx5: fix duplicate read of general capabilities
    1825629903 net/mlx5: fix GENEVE TLV option management
    c3eb862979 net/mlx5/hws: fix ESP flow matching validation
    d25716a8a0 net/mlx5: fix flow tag modification
    7c8f2e719a net/mlx5: fix jump action validation
    01c5db8d99 net/cnxk: fix aged flow query
    ecdb679c52 common/cnxk: fix VLAN check for inner header
    4f69dab88c common/cnxk: fix mbox region copy
    0e5798d30b net/thunderx: fix DMAC control register update
    874fd28866 net/cnxk: fix flow RSS configuration
    f047cea926 ml/cnxk: fix xstats calculation
    a77f545bd7 net/bnxt: fix deadlock in ULP timer callback
    d9e1762f07 net/bnxt: modify locking for representor Tx
    c26cb2a644 net/bnxt: fix backward firmware compatibility
    1fb50b8baa net/bnxt: fix speed change from 200G to 25G on Thor
    e1f8152ede net/bnxt: fix 50G and 100G forced speed
    3fa018b15a net/bnxt: fix array overflow
    c3ccbda492 net/netvsc: fix VLAN metadata parsing
    de2d362411 net: add macros for VLAN metadata parsing
    561a3f508f net/gve: fix DQO for chained descriptors
    de543e342a net/softnic: fix include of log library
    edaeda9ef7 net/memif: fix extra mbuf refcnt update in zero copy Tx
    c7b50f40e1 common/sfc_efx/base: use C11 static assert
    216918c28c net/mana: handle MR cache expansion failure
    6679de7a8f net/mana: fix memory leak on MR allocation
    3fb4840708 net/bonding: fix flow count query
    1ce60b941d net/ionic: fix device close
    9583f634f3 net/ionic: fix RSS query
    2ea5bde557 net/ionic: fix missing volatile type for cqe pointers
    49b4ce1f94 app/testpmd: fix crash in multi-process forwarding
    db4ba50b3a drivers/net: fix buffer overflow for packet types list
    7de2520f2d net/mana: prevent values overflow returned from RDMA layer
    84e9d93f57 net/nfp: free switch domain ID on close
    a581442d9b net/nfp: fix device resource freeing
    52bd57a03b net/nfp: fix device close
    c65a2bfc26 net/vmxnet3: fix initialization on FreeBSD
    edc0e91ffc app/testpmd: hide --bitrate-stats in help if disabled
    ec2260423e doc: add --latencystats option in testpmd guide
    e670d64d34 net/hns3: remove QinQ insert support for VF
    48fe88cb3c net/nfp: fix Rx descriptor
    e024c471f9 net/nfp: fix Rx memory leak
    cb1cef89c4 net/hns3: fix reset level comparison
    a3584fcde6 net/hns3: fix disable command with firmware
    48d9241bbd net/hns3: fix VF multiple count on one reset
    8abf8591dc net/hns3: refactor handle mailbox function
    1be4ad59be net/hns3: refactor send mailbox function
    f876981e54 net/hns3: refactor PF mailbox message struct
    c1c62366ed net/hns3: refactor VF mailbox message struct
    9cf299a873 net/memif: fix crash with Tx burst larger than 255
    01809245ba net/af_xdp: fix memzone leak on config failure
    c2a5c0d085 net/nfp: fix resource leak for VF
    ddeb9d64a9 net/nfp: fix resource leak for exit of flower firmware
    e65a677895 net/nfp: fix resource leak for exit of CoreNIC firmware
    09e1df883a net/nfp: fix resource leak for flower firmware
    02916557c1 net/nfp: fix resource leak for PF initialization
    1d53d5495b net/nfp: fix resource leak for CoreNIC firmware
    f2ee31d52c net/nfp: fix resource leak for device initialization
    8610d2715d ethdev: fix NVGRE encap flow action description
    d06a344524 doc: fix commands in eventdev test tool guide
    9350513462 test/event: skip test if no driver is present
    6ccd84cf16 event/cnxk: fix dequeue timeout configuration
    b7fd1f73fe app/crypto-perf: fix encrypt operation verification
    04d9dfd665 app/crypto-perf: fix data comparison
    dfc9d45365 app/crypto-perf: fix next segment mbuf
    8988726643 crypto/cnxk: fix CN9K ECDH public key verification
    ea096d3e48 common/cnxk: fix memory leak in CPT init
    f5d6c54154 examples/ipsec-secgw: fix width of variables
    96d48b5b40 cryptodev: remove unused extern variable
    e951bbbd18 vhost: fix memory leak in Virtio Tx split path
    19f0cf0927 vdpa/mlx5: fix queue enable drain CQ
    5eb1dd92dc vhost: fix deadlock during vDPA SW live migration
    33fbddf9a4 net/virtio: remove duplicate queue xstats
    c8e7cd6c6d vhost: fix virtqueue access check in vhost-user setup
    692a7a0034 vhost: fix virtqueue access check in VDUSE setup
    bbba917213 vhost: fix virtqueue access check in datapath
    c139df70dd net: fix TCP/UDP checksum with padding data
    c30a4f8b31 rcu: fix acked token in debug log
    94b20c14a6 rcu: use atomic operation on acked token
    8878a84e2e build: link static libs with whole-archive in subproject
    5e24d7f2de build: fix linker warnings about undefined symbols
    63241d7662 net/sfc: fix calloc parameters
    acad009eed net/nfp: fix calloc parameters
    238a03cdec net/bnx2x: fix calloc parameters
    e3ae3295ee common/mlx5: fix calloc parameters
    7c10528d68 rawdev: fix calloc parameters
    ad881b0db8 dmadev: fix calloc parameters
    9173abff75 eventdev: fix calloc parameters
    600e30b793 pipeline: fix calloc parameters
    5331b41382 examples/vhost: verify strdup return
    88f1c9af33 examples/qos_sched: fix memory leak in args parsing
    fbd04d26f3 test: verify strdup return
    c830d9e2af app/testpmd: verify strdup return
    8d5327fcfd app/dma-perf: verify strdup return
    fefe40a5ed app/crypto-perf: verify strdup return
    e0fd44c6ab app/pdump: verify strdup return
    1387327fa4 app/dumpcap: verify strdup return
    c6790ef542 net/nfp: verify strdup return
    2044a179a7 net/failsafe: fix memory leak in args parsing
    cedf721f24 event/cnxk: verify strdup return
    df74839ea1 dma/idxd: verify strdup return
    b4943e7a51 bus/vdev: verify strdup return
    82d4ba69f2 bus/fslmc: verify strdup return
    8c8e7aeb90 bus/dpaa: verify strdup return
    2feed5de50 eal: verify strdup return
    bb34c79bf4 doc: remove cmdline polling mode deprecation notice
    5f30c47cc5 eal/x86: add AMD vendor check for TSC calibration
    a9e8fc49d9 ci: update versions of actions in GHA
    d7a30d20c4 gro: fix reordering of packets
    b5c580913f telemetry: fix empty JSON dictionaries
    cbd1c165bb telemetry: fix connected clients count
    d7dc480432 app/graph: fix build reason
    7872a7b0bd build: fix reasons conflict
    54e4045c78 kernel/freebsd: fix module build on FreeBSD 14
    943de5c27e net/ice: fix memory leaks
    9aa2da4c02 net/iavf: fix crash on VF start
    0a72821dd9 net/iavf: fix no polling mode switching
    c321ba6a9d net/ice: fix tunnel TSO capabilities
    48efa16873 net/ice: fix link update
    c655f20c8f net/ixgbe: fix memoy leak after device init failure
    3defa10a78 net/iavf: fix memory leak on security context error
    ca47a866b5 net/i40e: remove redundant judgment in flow parsing
    ec5fe01a28 dma/dpaa2: fix logtype register
    fd6f07da94 lib: remove redundant newline from logs
    ec5e780f09 lib: add newline in logs
    e421bcd708 lib: use dedicated logtypes and macros
    f1e3dec4b4 regexdev: fix logtype register
    dc0428a5e4 hash: remove some dead code
    2c512fe65a buildtools/cmdline: fix IP address initializer
    3cedd8b9e4 buildtools/cmdline: fix generated code for IP addresses


* Wed Oct 23 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-11
- Merging upstream branch-3.4 [RH git: c1a17e3dc6]
    Commit list:
    7e0f702fd3 dpdk: Use DPDK 23.11.2 release for OVS 3.4.


* Wed Oct 23 2024 Timothy Redaelli <tredaelli@redhat.com> - 3.4.0-10
- Add OVS_SHA_REF to correctly point to v3.4.0 commit [RH git: 69a101f196]
    This is needed since the current starting commit includes also
    "Prepare for 3.4.1." and this breaks any commits that includes changes
    on NEWS file


* Mon Oct 07 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-9
- Merging upstream branch-3.4 [RH git: fd0f5ba088]
    Commit list:
    a15ce086d4 ofproto-dpif: Improve load balancing in dp_hash select groups. (FDP-826)


* Thu Oct 03 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-8
- Merging upstream branch-3.4 [RH git: af82ab5cba]
    Commit list:
    f6329c4280 Revert "ci: Use sarif-tools v3.0.1 due to issues in earlier versions."
    b7a277b732 ci: Use sarif-tools v3.0.1 due to issues in earlier versions.


* Mon Sep 23 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-7
- Merging upstream branch-3.4 [RH git: d05a073041]
    Commit list:
    d17dbccf03 netdev-dpdk: Disable outer udp checksum offload for txgbe driver.


* Fri Sep 20 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-6
- Merging upstream branch-3.4 [RH git: 0037d59a9b]
    Commit list:
    e05a769314 selinux: Update policy file.


* Fri Sep 20 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-5
- Merging upstream branch-3.4 [RH git: 17b80cd265]
    Commit list:
    7d074979f3 github: Skip FTP SNAT orig tuple tests due to broken Ubuntu kernel.


* Mon Sep 16 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-4
- Merging upstream branch-3.4 [RH git: 743a772569]
    Commit list:
    76ba41b5c2 vconn: Always properly free flow stats reply.
    fa840997f5 mcast-snooping: Properly check group_get_lru return code.
    64cb905077 ovsdb-idl: Fix IDL memory leak.
    9e9433ec5b ofproto/bond: Preserve active bond member over restarts.
    05b7520826 ofproto-dpif-upcall: Avoid stale ukeys leaks.
    a91553ef0e ci: Use previous sarif-tools release due to issue in latest release.


* Thu Aug 29 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-3
- Merging upstream branch-3.4 [RH git: 7e8c8356c9]
    Commit list:
    a67c12d515 userspace: Correctly set ip offload flag in native tunneling.


* Tue Aug 27 2024 Open vSwitch CI <ovs-ci@redhat.com> - 3.4.0-2
- Merging upstream branch-3.4 [RH git: 0f5878ad5e]
    Commit list:
    32ff65ac6f docs: Fix argument formatting in ovs-appctl(8) man page.


* Thu Aug 15 2024 Michael Santana <msantana@redhat.com> - 3.4.0-1
- redhat: Use official 3.4.0 tarball [RH git: fc198c51c1]
    Signed-off-by: Michael Santana <msantana@redhat.com>