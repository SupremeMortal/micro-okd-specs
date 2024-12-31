
%global with_debug 0

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

# It is only necessary to override %%gobuild to include the buildtags on RHEL 8 and below
# or where %%gobuild is otherwise undefined
%if ! 0%{?gobuild:1} || (%{defined rhel} && 0%{?rhel} <= 8)
%define gobuild(o:) go build -tags="$BUILDTAGS" -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%endif

%global provider github
%global provider_tld com
%global project kubernetes-sigs
%global repo %{name}
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path %{provider_prefix}

Name: cri-tools
Version: 1.31.1
Release: 1%{?dist}
Summary: CLI and validation tools for Container Runtime Interface
License: Apache-2.0
URL: https://%{provider_prefix}
Source0: https://%{provider_prefix}/archive/v%{version}/%{name}-%{version}.tar.gz
# no ppc64
ExclusiveArch: %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
BuildRequires: golang
BuildRequires: glibc-static
BuildRequires: go-md2man
BuildRequires: go-rpm-macros
Provides: crictl = %{version}-%{release}

%description
%{summary}.

%prep
%autosetup -p1

# can be used instead of the GO_LDFLAGS export below
# sed -i 's/"unknown"/"%{ version }"/' ./pkg/version/version.go

%build
%global gomodulesmode GO111MODULE=on
# Exporting %%{gomodulesmode} is only necessary on RHEL 8 and below
export %{gomodulesmode}
export GOFLAGS="-mod=vendor"
export BUILDTAGS="selinux seccomp"

# the export below fixes the crictl -v unknown version result
export GO_LDFLAGS="-X %{import_path}/pkg/version.Version=%{version}"

%gobuild -o bin/crictl %{import_path}/cmd/crictl
go-md2man -in docs/crictl.md -out docs/crictl.1

%install
# install binaries
install -dp %{buildroot}%{_bindir}
install -p -m 755 ./bin/crictl %{buildroot}%{_bindir}

# install manpage
install -dp %{buildroot}%{_mandir}/man1
install -p -m 644 docs/crictl.1 %{buildroot}%{_mandir}/man1

%check

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE vendor/modules.txt
%doc CHANGELOG.md CONTRIBUTING.md OWNERS README.md RELEASE.md code-of-conduct.md
%doc docs/{benchmark.md,roadmap.md,validation.md}
%{_bindir}/crictl
%{_mandir}/man1/crictl*.1*

%changelog
* Tue Dec 31 2024 SupremeMortal 1.31.1-1
- new package built with tito

* Mon Dec 30 2024 Owen Howard <owen@ziax.com> - 1.30.0-1
- Initial package