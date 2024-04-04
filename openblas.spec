%define major 0
%define libname %mklibname openblas
%define devname %mklibname openblas -d

# For now -- since C code (built with clang) and
# Fortran code (built with gfortran) are linked
# together, LTO object files don't work
%define _disable_lto 1

Name: openblas
Version: 0.3.27
Release: 1
Source0: https://github.com/OpenMathLib/OpenBLAS/releases/download/v%{version}/OpenBLAS-%{version}.tar.gz
Summary: Optimized BLAS library
URL: https://github.com/openblas/openblas
License: BSD-3-Clause
Group: System/Libraries
BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	gcc-gfortran

%description
OpenBLAS is an optimized BLAS (Basic Linear Algebra Subprograms) library based
on GotoBLAS2 1.13 BSD version.

%package -n %{libname}
Summary: Optimized BLAS library
Group: System/Libraries

%description -n %{libname}
Optimized BLAS library

%package -n %{devname}
Summary: Development files for %{name}
Group: Development/C
Requires: %{libname} = %{EVRD}

%description -n %{devname}
Development files (Headers etc.) for %{name}.

%prep
%autosetup -p1 -n OpenBLAS-%{version}
%cmake -G Ninja \
	-DBUILD_RELAPACK:BOOL=ON

%build
%ninja_build -C build

%install
%ninja_install -C build

%files

%files -n %{libname}
%{_libdir}/*.so.%{major}*

%files -n %{devname}
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/*
%{_libdir}/cmake/*
