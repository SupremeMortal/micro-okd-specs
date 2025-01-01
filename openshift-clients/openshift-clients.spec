#debuginfo not supported with Go
%global debug_package %{nil}
# modifying the Go binaries breaks the DWARF debugging
%global __os_install_post %{_rpmconfigdir}/brp-compress

%global gopath      %{_datadir}/gocode
%global import_path github.com/openshift/oc

%global golang_version 1.19

%global version_major 4
%global version_minor 18
%global version_patch 0

%{!?commit:
%global commit c64c430e48013ced1705344bb95ba1bdfb2a1a0b
}
%global shortcommit %(c=%{commit}; echo ${c:0:7})

%{!?version: %global version %{version_major}.%{version_minor}.%{version_patch}}
%{!?release: %global release 5.git%{shortcommit}}

%if ! 0%{?os_git_vars:1}
%global os_git_vars OS_GIT_VERSION=%{version}-%{release} OS_GIT_COMMIT=%{commit} OS_GIT_MAJOR=%{version_major} OS_GIT_MINOR=%{version_minor} OS_GIT_PATCH=%{version_patch} OS_GIT_TREE_STATE=clean
%endif

%if "%{os_git_vars}" == "ignore"
%global make make
%else
%global make %{os_git_vars} && make SOURCE_GIT_TAG:="${OS_GIT_VERSION}" SOURCE_GIT_COMMIT:="${OS_GIT_COMMIT}" SOURCE_GIT_MAJOR:="${OS_GIT_MAJOR}" SOURCE_GIT_MINOR:="${OS_GIT_MINOR}" SOURCE_GIT_PATCH:="${OS_GIT_PATCH}" SOURCE_GIT_TREE_STATE:="${OS_GIT_TREE_STATE}"
%endif

Name:           openshift-clients
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        OpenShift client binaries
License:        ASL 2.0
URL:            https://%{import_path}
Source0:        https://%{import_path}/archive/%{commit}/oc-%{commit}.tar.gz

# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:  x86_64 aarch64 ppc64le s390x
%endif

BuildRequires:  golang >= %{golang_version}
BuildRequires:  krb5-devel
BuildRequires:  rsync

Provides:       atomic-openshift-clients = %{version}
Obsoletes:      atomic-openshift-clients <= %{version}
Provides:       origin-clients = %{version}
Obsoletes:      origin-clients <= %{version}
Provides:       okd-clients = %{version}
Obsoletes:      okd-clients <= %{version}
Provides:       oc = %{version}
Obsoletes:      oc <= %{version}

Requires:       bash-completion

%description
%{summary}

%package redistributable
Summary:        OpenShift Client binaries for Linux, Mac OSX, and Windows
Provides:       atomic-openshift-clients-redistributable = %{version}
Obsoletes:      atomic-openshift-clients-redistributable <= %{version}
Provides:       origin-clients-redistributable = %{version}
Obsoletes:      origin-clients-redistributable <= %{version}
Provides:       okd-clients-redistributable = %{version}
Obsoletes:      okd-clients-redistributable <= %{version}
Provides:       oc-redistributable = %{version}
Obsoletes:      oc-redistributable <= %{version}

%description redistributable
%{summary}

%prep
%if ! 0%{?local_build:1}
%setup -q -n oc-%{commit}
%endif

%build
%if ! 0%{?local_build:1}
mkdir -p "$(dirname __gopath/src/%{import_path})"
mkdir -p "$(dirname __gopath/src/%{import_path})"
ln -s "$(pwd)" "__gopath/src/%{import_path}"
export GOPATH=$(pwd)/__gopath:%{gopath}
cd "__gopath/src/%{import_path}"
%endif

%ifarch %{ix86}
GOOS=linux
GOARCH=386
%endif
%ifarch ppc64le
GOOS=linux
GOARCH=ppc64le
%endif
%ifarch %{arm} aarch64
GOOS=linux
GOARCH=arm64
%endif
%ifarch s390x
GOOS=linux
GOARCH=s390x
%endif

%{make} build GO_BUILD_PACKAGES:='./cmd/oc ./tools/genman'

#%ifarch x86_64
#  # Create Binaries for all supported arches
#  %{make} cross-build-darwin-amd64 cross-build-windows-amd64 GO_BUILD_PACKAGES:='./cmd/oc'
#%endif

%install
install -d %{buildroot}%{_bindir}

# Install for the local platform
install -p -m 755 ./oc %{buildroot}%{_bindir}/oc
ln -s ./oc %{buildroot}%{_bindir}/kubectl
[[ -e %{buildroot}%{_bindir}/kubectl ]]

%ifarch x86_64
# Install client executable for windows and mac
install -d %{buildroot}%{_datadir}/%{name}/{linux,macosx,windows}
install -p -m 755 ./oc %{buildroot}%{_datadir}/%{name}/linux/oc
ln -s ./oc %{buildroot}%{_datadir}/%{name}/linux/kubectl
[[ -e %{buildroot}%{_datadir}/%{name}/linux/kubectl ]]
install -p -m 755 ./_output/bin/darwin_amd64/oc %{buildroot}/%{_datadir}/%{name}/macosx/oc
ln -s ./oc %{buildroot}/%{_datadir}/%{name}/macosx/kubectl
[[ -e %{buildroot}/%{_datadir}/%{name}/macosx/kubectl ]]
install -p -m 755 ./_output/bin/windows_amd64/oc.exe %{buildroot}/%{_datadir}/%{name}/windows/oc.exe
ln -s ./oc.exe %{buildroot}/%{_datadir}/%{name}/windows/kubectl.exe
[[ -e %{buildroot}/%{_datadir}/%{name}/windows/kubectl.exe ]]
%endif

# Install man1 man pages
install -d -m 0755 %{buildroot}%{_mandir}/man1
./genman %{buildroot}%{_mandir}/man1 oc

 # Install bash completions
install -d -m 755 %{buildroot}%{_sysconfdir}/bash_completion.d/
for bin in oc kubectl
do
  echo "+++ INSTALLING BASH COMPLETIONS FOR ${bin} "
  %{buildroot}%{_bindir}/${bin} completion bash > %{buildroot}%{_sysconfdir}/bash_completion.d/${bin}
  chmod 644 %{buildroot}%{_sysconfdir}/bash_completion.d/${bin}
done

%files
%license LICENSE
%{_bindir}/oc
%{_bindir}/kubectl
%{_sysconfdir}/bash_completion.d/oc
%{_sysconfdir}/bash_completion.d/kubectl
%dir %{_mandir}/man1/
%{_mandir}/man1/oc*

%ifarch x86_64
%files redistributable
%license LICENSE
%dir %{_datadir}/%{name}/linux/
%dir %{_datadir}/%{name}/macosx/
%dir %{_datadir}/%{name}/windows/
%{_datadir}/%{name}/linux/oc
%{_datadir}/%{name}/linux/kubectl
%{_datadir}/%{name}/macosx/oc
%{_datadir}/%{name}/macosx/kubectl
%{_datadir}/%{name}/windows/oc.exe
%{_datadir}/%{name}/windows/kubectl.exe
%endif

%changelog
* Wed Jan 01 2025 SupremeMortal 4.18.0-5.gitc64c430
- Remove cross compiled binaries
  (6178101+SupremeMortal@users.noreply.github.com)

* Wed Jan 01 2025 SupremeMortal 4.18.0-4.gitc64c430
- export PATH for goversioninfo
  (6178101+SupremeMortal@users.noreply.github.com)

* Wed Jan 01 2025 SupremeMortal 4.18.0-3.gitc64c430
- Install goversioninfo manually
  (6178101+SupremeMortal@users.noreply.github.com)

* Wed Jan 01 2025 SupremeMortal 4.18.0-2.gitc64c430
- Bump release (6178101+SupremeMortal@users.noreply.github.com)
- Remove goversioninfo build requirement
  (6178101+SupremeMortal@users.noreply.github.com)

* Wed Jan 01 2025 SupremeMortal 4.18.0-1.gitc64c430
- new package built with tito

* Wed Jan 01 2025 Owen Howard - 4.18.0-1
- Version 4.18

* Fri May 26 2023 Christian Glombek <cglombek@redhat.com> - 4.14.0-1
- Version 4.14

* Fri May 26 2023 Christian Glombek <cglombek@redhat.com> - 4.13.0-1
- Imported spec from https://github.com/openshift/oc/blob/68c710f5c29d795a8706d1e40de9099d278c059b/oc.spec
- Adapted for CentOS
