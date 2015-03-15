%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress
%define        _vendor  redhat

Summary: The "Hello World" 
Name: foo
Version: 1.0
Release: 1
Source0: %{name}-%{version}.tar.gz
License: GPLv3+
Group: Development/Tools
BuildArch: noarch

%description 
The "Hello World" program,

Buildroot: %{_tmppath}/%{name}-%{version}-root

%prep
%setup -q

%build

%clean
rm -rf $RPM_BUILD_ROOT
