# https://github.com/cri-o/cri-o
%global goipath         github.com/cri-o/cri-o
%global service_name    crio

# Related: github.com/cri-o/cri-o/issues/3684
%global build_timestamp %(date -u +'%Y-%m-%dT%H:%M:%SZ')
%global git_tree_state  clean
%global criocli_path    ""

Version:        1.31.3

%define gobuild(o:) %{expand:
  # https://bugzilla.redhat.com/show_bug.cgi?id=995136#c12
  %global _dwz_low_mem_die_limit 0
  %ifnarch ppc64
  go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${BASE_LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %else
  go build                -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${BASE_LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %endif
}
%bcond_with check


# Commit for the builds
%global commit0 b7f3c240bcbda6fae8d43561694d18317e09e167

Name:           cri-o
Epoch:          0
Release:        1%{?dist}
Summary:        Open Container Initiative-based implementation of Kubernetes Container Runtime Interface

# Upstream license specification: Apache-2.0
# Automatically converted from old format: ASL 2.0 - review is highly recommended.
License:        Apache-2.0
URL:            https://github.com/cri-o/cri-o
Source0:        %url/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  golang >= 1.19
BuildRequires:  git-core
BuildRequires:  glib2-devel
BuildRequires:  glibc-static
BuildRequires:  go-md2man
BuildRequires:  gpgme-devel
BuildRequires:  libassuan-devel
BuildRequires:  libseccomp-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  make

Requires:       container-selinux
Requires:       containers-common >= 1:0.1.31-14

Recommends:     runc >= 1.0.0-16
Suggests:       containernetworking-plugins >= 1.0.0-1

Requires:       conmon >= 2.0.2-1
Requires:       socat

Obsoletes:      ocid <= 0.3
Provides:       ocid = %{epoch}:%{version}-%{release}
Provides:       %{service_name} = %{epoch}:%{version}-%{release}

%description
Open Container Initiative-based implementation of Kubernetes Container Runtime
Interface.

%prep
%autosetup -p1 -n %{name}-%{version}

sed -i 's/install.config: crio.conf/install.config:/' Makefile
sed -i 's/install.bin: binaries/install.bin:/' Makefile
sed -i 's/install.man: $(MANPAGES)/install.man:/' Makefile
sed -i 's/\.gopathok //' Makefile
sed -i 's/module_/module-/' internal/version/version.go
sed -i 's/\/local//' contrib/systemd/%{service_name}.service
sed -i 's/\/local//' contrib/systemd/%{service_name}-wipe.service

%build
export GO111MODULE=on
export GOFLAGS=-mod=vendor

export BUILDTAGS="$(hack/btrfs_installed_tag.sh)
$(hack/btrfs_tag.sh) $(hack/libdm_installed.sh)
$(hack/libdm_no_deferred_remove_tag.sh)
$(hack/seccomp_tag.sh)
$(hack/selinux_tag.sh)"

BUILDTAGS="$BUILDTAGS containers_image_openpgp"

export BASE_LDFLAGS="-X %{goipath}/internal/pkg/criocli.DefaultsPath=%{criocli_path}
-X  %{goipath}/internal/version.buildDate=%{build_timestamp}
-X  %{goipath}/internal/version.gitCommit=%{commit0}
-X  %{goipath}/internal/version.version=%{version}
-X  %{goipath}/internal/version.gitTreeState=%{git_tree_state} "

for cmd in cmd/* ; do
  %gobuild -o bin/$(basename $cmd) %{goipath}/$cmd
done

export CFLAGS="$CFLAGS -std=c99"
%make_build bin/pinns
GO_MD2MAN=go-md2man make docs

%install
sed -i 's/\/local//' contrib/systemd/%{service_name}.service
bin/%{service_name} \
      --selinux \
      --cni-plugin-dir /opt/cni/bin \
      --cni-plugin-dir "%{_libexecdir}/cni" \
      --enable-metrics \
      --metrics-port 9537 \
      config > %{service_name}.conf

# install binaries
install -dp %{buildroot}{%{_bindir},%{_libexecdir}/%{service_name}}
install -p -m 755 bin/%{service_name} %{buildroot}%{_bindir}

# install conf files
install -dp %{buildroot}%{_sysconfdir}/cni/net.d
install -p -m 644 contrib/cni/10-crio-bridge.conflist %{buildroot}%{_sysconfdir}/cni/net.d/100-crio-bridge.conflist
install -p -m 644 contrib/cni/99-loopback.conflist %{buildroot}%{_sysconfdir}/cni/net.d/200-loopback.conflist

install -dp %{buildroot}%{_sysconfdir}/%{service_name}
install -dp %{buildroot}%{_datadir}/containers/oci/hooks.d
install -dp %{buildroot}%{_datadir}/oci-umount/oci-umount.d
install -p -m 644 crio.conf %{buildroot}%{_sysconfdir}/%{service_name}
#install -p -m 644 seccomp.json %%{buildroot}%%{_sysconfdir}/%%{service_name}
install -p -m 644 crio-umount.conf %{buildroot}%{_datadir}/oci-umount/oci-umount.d/%{service_name}-umount.conf
install -p -m 644 crictl.yaml %{buildroot}%{_sysconfdir}

%make_install PREFIX=%{buildroot}%{_prefix} \
            install.bin \
            install.completions \
            install.config \
            install.man \
            install.systemd

install -dp %{buildroot}%{_sharedstatedir}/containers

%post
%systemd_post %{service_name}

%preun
%systemd_preun %{service_name}

%postun
%systemd_postun_with_restart %{service_name}

%files
%license LICENSE vendor/modules.txt
%doc docs code-of-conduct.md tutorial.md ADOPTERS.md CONTRIBUTING.md README.md
%doc awesome.md transfer.md
%{_bindir}/%{service_name}
%{_bindir}/pinns
%{_mandir}/man5/%{service_name}.conf*5*
%{_mandir}/man8/%{service_name}*.8*
%dir %{_sysconfdir}/%{service_name}
%config(noreplace) %{_sysconfdir}/%{service_name}/%{service_name}.conf
%config(noreplace) %{_sysconfdir}/cni/net.d/100-%{service_name}-bridge.conflist
%config(noreplace) %{_sysconfdir}/cni/net.d/200-loopback.conflist
%config(noreplace) %{_sysconfdir}/crictl.yaml
%dir %{_libexecdir}/%{service_name}
%{_unitdir}/%{service_name}.service
%{_unitdir}/%{service_name}-wipe.service
%dir %{_sharedstatedir}/containers
%dir %{_datadir}/containers
%dir %{_datadir}/containers/oci
%dir %{_datadir}/containers/oci/hooks.d
%dir %{_datadir}/oci-umount
%dir %{_datadir}/oci-umount/oci-umount.d
%{_datadir}/oci-umount/oci-umount.d/%{service_name}-umount.conf
%{_datadir}/bash-completion/completions/%{service_name}*
%{_datadir}/fish/completions/%{service_name}*.fish
%{_datadir}/zsh/site-functions/_%{service_name}*

%changelog
* Mon Dec 30 2024 Owen Howard <owen@ziax.com> - 0.1-1
- Initial build
