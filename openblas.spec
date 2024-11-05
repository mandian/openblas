# For now -- since C code (built with clang) and
# Fortran code (built with gfortran) are linked
# together, LTO object files don't work
#%%global _disable_lto 0

%define major 0
%define libname	%mklibname %{name}-serial
%define libpname %mklibname %{name}-threads
%define liboname %mklibname %{name}-openmp
%define devname	%mklibname %{name} -d
%define docname	%{name}-doc

%bcond deprecated	1
%bcond cblas		1
%bcond lapack		1
%bcond lapacke		1
%bcond relapack		0
%bcond static		0
%bcond testing		1

%global optflags %{optflags} -O3

%if %{?__isa_bits:%{__isa_bits}}%{!?__isa_bits:32} == 64
%global arch64 1
%else
%global arch64 0
%endif

%global pname %{name}p
%global oname %{name}o

%global _description %{expand:
OpenBLAS is an optimized BLAS library based on GotoBLAS2 1.13 BSD
version. The project is supported by the Lab of Parallel Software and
Computational Science, ISCAS. http://www.rdcps.ac.cn.
}

Summary:	An optimized BLAS library based on GotoBLAS2
Name:		openblas
Version:	0.3.28
Release:	2
Group:		Sciences/Mathematics
License:	BSD-3-Clause
URL:		https://github.com/OpenMathLib/OpenBLAS
Source0:	https://github.com/OpenMathLib/OpenBLAS/archive/v%{version}/openblas-%{version}.tar.gz
Patch0:		openblas-0.3.28-suffix.patch

BuildRequires:	cmake ninja
BuildRequires:	gcc-gfortran
BuildRequires:	pkgconfig(lapack)
BuildRequires:	gomp-devel

%description %_description


#---------------------------------------------------------------------------

%package -n %{libname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{libname} %_description

This package contains the sequential library.

%files -n %{libname}
%license LICENSE
%{_libdir}/lib%{name}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/lib%{name}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{libpname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{libpname} %_description
This package contains library compiled with threading support.

%files -n %{libpname}
%license LICENSE
%{_libdir}/lib%{pname}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/lib%{pname}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{liboname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{liboname} %_description
This package contains library compiled with OpenMP support.

%files -n %{liboname}
%license LICENSE
%{_libdir}/lib%{oname}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/lib%{oname}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{devname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Requires:	%{libpname} = %{EVRD}
Requires:	%{liboname} = %{EVRD}
Provides:	%{name}-devel

%description -n %{devname} %_description
Development files (Headers etc.) for %{name}.

%files -n %{devname}
%license LICENSE
%doc Changelog.txt GotoBLAS*

%{_includedir}/%{name}/
%{_libdir}/pkgconfig/*
%{_libdir}/cmake/*
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{oname}.so
%{_libdir}/lib%{pname}.so
%if 0%{?arch64}
%{_includedir}/%{name}64/
%{_libdir}/lib%{name}64.so
%{_libdir}/lib%{oname}64.so
%{_libdir}/lib%{pname}64.so
%endif

#---------------------------------------------------------------------------

%prep
%autosetup -p1 -n OpenBLAS-%{version}

%build
%global optflags %{optflags} -fno-optimize-sibling-calls 
export CC=gcc
export CXX=g++
export FC=gfortran

# architectures
%ifarch %{ix86} x86_64 znver1
TARGET="CORE2"
%endif
%ifarch aarch64
TARGET="ARMV8"
%endif

# hardcode the maximum possible amount of processors
GENERIC_OPTIONS+=" "

for d in {SERIAL,THREADED,OPENMP}%{?arch64:{,64}}
do
	# build flags
	COMMON="%{optflags} -fPIC"
	FCOMMON="$COMMON -frecursive"

	if [[ "$d" =~ "THREADED" ]]; then
		LIBPREFIX=libp%{pname}
		LIBSUFFFIX=p
		USE_LOCKING=0
		USE_OPENMP=0
		USE_THREAD=1
	elif [[ "$d" =~ "OPENMP" ]]; then
		LIBPREFIX=libo%{oname}
		LIBSUFFFIX=o
		USE_LOCKING=0
		USE_OPENMP=1
		USE_THREAD=1
		FCOMMON+=" -fopenmp"
	else
		LIBPREFIX=lib%{name}
		LIBSUFFFIX=
		USE_LOCKING=1
		USE_OPENMP=0
		USE_THREAD=0
	fi

	if [[ "$d" =~ "64" ]]; then
		INTERFACE64=1
		FCOMMON+=" -fdefault-integer-8"
	else
		INTERFACE64=0
	fi

	%cmake -Wno-dev \
		-DBUILD_STATIC_LIBS:BOOL=%{?with_static:ON}%{?!with_static:OFF} \
		-DBUILD_SHARED_LIBS:BOOL=ON \
		-DBUILD_LAPACK_DEPRECATED:BOOL=%{?with_deprecated:ON}%{?!with_deprecated:OFF} \
		-DBUILD_RELAPACK=%{?with_relapack:ON}%{?!with_relapack:OFF} \
		-DBUILD_WITHOUT_CBLAS:BOOL=%{?with_cblas:OFF}%{?!with_cblas:ON} \
		-DBUILD_WITHOUT_LAPACK:BOOL=%{?with_lapack:OFF}%{?!with_lapack:ON} \
		-DBUILD_TESTING:BOOL=%{?with_testing:ON}%{?!with_testing:OFF} \
		-DDYNAMIC_ARCH:BOOL=ON \
		-DDYNAMIC_OLDER:BOOL=ON \
		-DUSE_OPENMP:BOOL=$USE_OPENMP \
		-DUSE_LOCKING:BOOL=$USE_LOCKING \
		-DNO_AFFINITY:BOOL=ON \
		-DNO_WARMUP:BOOL=ON \
		-DTARGET:STRING=$TARGET \
		-DUSE_THREAD:BOOL=$USE_THREAD \
		-DNUM_THREADS=128 \
		-DINTERFACE64:BOOL=$INTERFACE64 \
		-DLIBNAMESUFFIX:STRING=$LIBSUFFFIX \
		-DCMAKE_Fortran_COMPILER=$FC \
		-GNinja
	%ninja_build

	cd ..
	mv %_vpath_builddir %_vpath_builddir-$d
done

%install
for d in {SERIAL,THREADED,OPENMP}%{?arch64:{,64}}
do
	ln -fs %_vpath_builddir-$d build
	%ninja_install -C build
	rm build
done

%check
%if %{with testing}
for d in {SERIAL,THREADED,OPENMP}%{?arch64:{,64}}
do
	ln -fs %_vpath_builddir-$d build
	pushd build
	ctest
	popd 1>/dev/null
	rm build
done
%endif

