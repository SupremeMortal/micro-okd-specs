# https://github.com/cri-o/cri-o
%global goipath         github.com/kubernetes-sigs/cri-tools
Version:                1.31.1

%define gobuild(o:) go build -buildmode pie -compiler gc -tags="rpm_crashtraceback libtrust_openssl ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -linkmode=external -compressdwarf=false -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags'" -a -v -x %{?**};

%bcond_without check


%global forgeurl    https://github.com/kubernetes-sigs/cri-tools

%global repo cri-tools
%global import_path sigs.k8s.io/%{repo}

%gometa -f

Name: %{repo}
Release: 1%{?dist}
Summary: CLI and validation tools for Container Runtime Interface
License: ASL 2.0
URL:     https://%{goipath}
Source0: %url/archive/v%{version}/%{name}-%{version}.tar.gz
ExclusiveArch: %{golang_arches}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires: golang
BuildRequires: glibc-static
BuildRequires: git
BuildRequires: go-rpm-macros
Provides: crictl = %{version}-%{release}

%description
%{summary}

%gopkg

%prep
%autosetup  -n %{name}-%{version}

%build
mkdir _build
pushd _build
mkdir -p src/sigs.k8s.io
ln -s ../../../ src/%{import_path}
popd
ln -s vendor src
export GOPATH=$(pwd)/_build:$(pwd)
export GO111MODULE=off
export LDFLAGS+=" -X %{import_path}/pkg/version.Version=%version"

GOPATH=$GOPATH %gobuild -o bin/crictl %{import_path}/cmd/crictl
bin/crictl completion > docs/crictl-completions

%install
# install binaries
install -dp %{buildroot}%{_bindir}
install -p -m 755 ./bin/crictl %{buildroot}%{_bindir}

# install manpage
install -dp %{buildroot}%{_mandir}/man1
install -p -m 644 docs/crictl.1 %{buildroot}%{_mandir}/man1

# install completions
install -dp %{buildroot}%{_datadir}/bash-completion/completions/
install -p -m 644 docs/crictl-completions %{buildroot}%{_datadir}/bash-completion/completions/crictl

%check
%gocheck


%files
%license LICENSE
%doc CHANGELOG.md CONTRIBUTING.md OWNERS README.md RELEASE.md code-of-conduct.md
%doc docs/{benchmark.md,roadmap.md,validation.md}
%{_bindir}/crictl
%{_mandir}/man1/crictl*
%{_datadir}/bash-completion/completions/crictl


%changelog
* Tue Dec 31 2024 Owen howard - 1.31.1-1
- Initial package