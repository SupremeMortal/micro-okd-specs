%global with_debug 0

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider github
%global provider_tld com
%global project opencontainers
%global repo runc
# https://github.com/opencontainers/runc
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path %{provider_prefix}
%global git0 https://github.com/opencontainers/runc

Name: %{repo}
Epoch: 2
Version: 1.2.3
Release: %autorelease
Summary: CLI for running Open Containers
License: Apache-2.0 and BSD-2-Clause and BSD-3-Clause and MIT
URL: %{git0}
Source0: %{git0}/archive/v%{version}/%{name}-%{version}.tar.gz
ExclusiveArch:  %{golang_arches_future}
BuildRequires: golang
BuildRequires: pkgconfig(libseccomp)
BuildRequires: go-md2man
BuildRequires: make
Provides: oci-runtime

Recommends: container-selinux >= 2:2.85-1

%ifnarch s390x
Recommends: criu
%endif

%description
The runc command can be used to start containers which are packaged
in accordance with the Open Container Initiative's specifications,
and to manage containers running under runc.

%prep
%autosetup -p1 -n %{name}-%{version}
sed -i 's/ -trimpath//g' Makefile

%build
%set_build_flags
export CGO_CFLAGS=$CFLAGS
# These extra flags present in $CFLAGS have been skipped for now as they break the build
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-flto=auto//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-Wp,D_GLIBCXX_ASSERTIONS//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-specs=\/usr\/lib\/rpm\/redhat\/redhat-annobin-cc1//g')

%ifarch x86_64
export CGO_CFLAGS+=" -m64 -mtune=generic -fcf-protection=full"
%endif

mkdir -p GOPATH
pushd GOPATH
    mkdir -p src/%{provider}.%{provider_tld}/%{project}
    ln -s $(dirs +1 -l) src/%{import_path}
popd

pushd GOPATH/src/%{import_path}
export GOPATH=$(pwd)/GOPATH

%make_build runc

sed -i '/\#\!\/bin\/bash/d' contrib/completions/bash/%{name}

%install
install -d -p %{buildroot}%{_bindir}
install -p -m 755 %{name} %{buildroot}%{_bindir}

# generate man pages
man/md2man-all.sh

# install man pages
install -d -p %{buildroot}%{_mandir}/man8
install -p -m 0644 man/man8/*.8 %{buildroot}%{_mandir}/man8/.
# install bash completion
install -d -p %{buildroot}%{_datadir}/bash-completion/completions
install -p -m 0644 contrib/completions/bash/%{name} %{buildroot}%{_datadir}/bash-completion/completions

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE vendor/modules.txt
%doc MAINTAINERS_GUIDE.md PRINCIPLES.md README.md CONTRIBUTING.md
%{_bindir}/%{name}
%{_mandir}/man8/%{name}*
%{_datadir}/bash-completion/completions/%{name}

%changelog
* Mon Dec 30 2024 Owen Howard <owen@ziax.com> - 1.2.3-1
- Initial package
