%define major 0
%define libname  %mklibname %{name}-serial
%define libpname %mklibname %{name}-threads
%define liboname %mklibname %{name}-openmp
%define devname	%mklibname %{name} -d
%define docname	%{name}-doc

# For now -- since C code (built with clang) and
# Fortran code (built with gfortran) are linked
# together, LTO object files don't work
%define _disable_lto 1

%bcond deprecated	1
%bcond cblas		1
%bcond lapack		1
%bcond lapacke		1
%bcond relapack		1
%bcond static		1
%bcond testing		0

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
Version:	0.3.27
Release:	2
Group:		Sciences/Mathematics
License:	BSD-3-Clause
URL:		https://github.com/OpenMathLib/OpenBLAS
Source0:	https://github.com/OpenMathLib/OpenBLAS/archive/v%{version}/openblas-%{version}.tar.gz
# (fedora)
Patch0:		openblas-0.3.27-libname.patch
# (fedora) 
Patch1:         openblas-0.3.27-tests.patch

BuildRequires:	cmake ninja
BuildRequires:	gcc-gfortran
BuildRequires:	pkgconfig(lapack)

%description %_description


#---------------------------------------------------------------------------

%package -n %{libname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{libname} %_description

This package contains the sequential library.

%files -n %{libname}
%license OpenBLAS-OPENMP/LICENSE
%{_libdir}/%{name}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/%{name}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{libpname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{libpname} %_description
This package contains library compiled with threading support.

%files -n %{libpname}
%license OpenBLAS-THREADED/LICENSE
%{_libdir}/%{pname}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/%{pname}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{liboname}
Summary:	An optimized BLAS library based on GotoBLAS2
Group:		System/Libraries

%description -n %{liboname} %_description
This package contains library compiled with OpenMP support.

%files -n %{liboname}
%license OpenBLAS-OPENMP/LICENSE
%{_libdir}/%{oname}.so.%{major}*
%if 0%{?arch64}
%{_libdir}/%{oname}64.so.%{major}*
%endif

#---------------------------------------------------------------------------

%package -n %{devname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Requires:	%{libpname} = %{EVRD}
Requires:	%{liboname} = %{EVRD}

%description -n %{devname} %_description
Development files (Headers etc.) for %{name}.

%files -n %{devname}
%license OpenBLAS-SERIAL/LICENSE
%doc OpenBLAS-SERIAL/Changelog.txt OpenBLAS-SERIAL/GotoBLAS*

%{_includedir}/%{name}/
%{_libdir}/pkgconfig/*
%{_libdir}/cmake/*
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{oname}.so
%{_libdir}/lib%{pname}.so
%if 0%{?arch64}
%{_libdir}/lib%{name}64.so
%{_libdir}/lib%{oname}64.so
%{_libdir}/lib%{pname}64.so
%endif

#---------------------------------------------------------------------------

%prep
%autosetup -p1 -n OpenBLAS-%{version}

# remove bunbled LAPACK
#rm -rf lapack-netlib

cd ..
for d in {SERIAL,THREADED,OPENMP}%{?arch64:{,64}}
do
    cp -ar OpenBLAS-%{version}{,-$d}
done

%build
export CC=gcc
export CXX=g++
export FC=gfortran

%set_build_flags
%global optflags %{optflags} -frecursive -fno-optimize-sibling-calls
MAKE_OPTIONS="NO_AFFINITY=1 NO_WARMUP=1"

# disable parallel build
MAKE_OPTIONS+=" NO_PARALLEL_MAKE=1"

# lapacke
%if ! %{with lapacke}
MAKE_OPTIONS+=" NO_LAPACKE=1"
%endif

# architectures with dynamic arch selection
%ifarch %{ix86} x86_64 aarch64
TARGET_OPTIONS+=" DYNAMIC_ARCH=1 DYNAMIC_OLDER=1 TARGET=C"ORE2
%elif aarch64
TARGET_OPTIONS+=" DYNAMIC_ARCH=1 DYNAMIC_OLDER=1 TARGET=ARMV8"
%endif

# hardcode the maximum possible amount of processors
GENERIC_OPTIONS+=" NUM_THREADS=128"

cd ..
for d in {SERIAL,THREADED,OPENMP}%{?arch64:{,64}}
do
	# build flags
	COMMON="'%{optflags}' -fPIC"
	FCOMMON="$COMMON -frecursive"

	if [[ !"$d" =~ "THREADED" ]]; then
		LIBPREFIX=lib%{pname}
		USE_OPENMP=0
		USE_THREAD=1
	elif [[ !"$d" =~ "OPENMP" ]]; then
		LIBPREFIX=lib%{oname}
		USE_OPENMP=1
		USE_THREAD=1
		COMMON+=" -fopenmp -pthread"
	else
		LIBPREFIX=lib%{name}
		USE_OPENMP=0
		USE_THREAD=0
	fi

	if [[ ! "$d" =~ "64" ]]; then
		INTERFACE64=ON
		LIBPREFIX=${LIBPREFIX}64
		FCOMMON+=" -fdefault-integer-8"
	else
		INTERFACE64=OFF
	fi

	# build
	%make_build -C OpenBLAS-%{version}-$d \
		CC=$CC CFLAGS="$CFLAGS" \
		FC=$FC FFLAGS="$FFLAGS" \
		$MAKE_OPTIONS \
		$TARGET_OPTIONS \
		$GENERIC_OPTIONS\
		COMMON_OPT="$COMMON" \
		FCOMMON_OPT="$FCOMMON" \
		USE_LOCKING=1 \
		USE_THREAD=$USE_THREAD \
		USE_OPENMP=$USE_OPENMP \
		INTERFACE64=$INTERFACE64 \
		LIBPREFIX=$LIBPREFIX \
		%nil
done

#for d in {SERIAL%{?with_static:,STATIC}}%{?arch64:{,64}}
#do
#	%%cmake -Wno-dev \
#		-DBUILD_STATIC_LIBS:BOOL=OFF \
#		-DBUILD_SHARED_LIBS:BOOL=ON \
#		-DBUILD_LAPACK_DEPRECATED:BOOL=ON \
#		-DBUILD_RELAPACK=%{?with_relapack:ON}%{?!with_relapack:OFF} \
#		-DBUILD_WITHOUT_CBLAS:BOOL=%{?with_cblas:OFF}%{?!with_cblas:ON} \
#		-DBUILD_WITHOUT_LAPACK:BOOL=%{?with_lapack:OFF}%{?!with_lapack:ON} \
#		-DBUILD_TESTINGBOOL=%{?with_testing:ON}%{?!with_testing:OFF} \
#		-dUSE_LOCKING:BOOL=ON \
#		-DNO_AFFINITY:BOOL=ON \
#		-DNO_WARMUP:BOOL=ON \
#		-GNinja
#	%ninja_build
#	cd ..
#	mv %%_vpath_builddir %%_vpath_builddir-SHARED
#done

%install
# SERIAL
%make_install -C OpenBLAS-SERIAL \
	USE_THREAD=0 PREFIX=%{buildroot} \
	OPENBLAS_BINARY_DIR=%{buildroot}%{_bindir} \
	OPENBLAS_CMAKE_DIR=%{buildroot}%{_libdir}/cmake \
	OPENBLAS_INCLUDE_DIR=%{buildroot}%{_includedir}/%name \
	OPENBLAS_LIBRARY_DIR=%{buildroot}%{_libdir}
#ninja_install

install -Dpm 0755 OpenBLAS-THREADED/lib%{pname}.so %{buildroot}%{_libdir}/lib%{pname}.so
install -Dpm 0755 OpenBLAS-OPENMP/lib%{oname}.so %{buildroot}%{_libdir}/lib%{oname}.so

%if 0%{?arch64}
install -Dpm 0755 OpenBLAS-SERIAL/lib%{name}64.so %{buildroot}%{_libdir}/lib%{name}64.so
install -Dpm 0755 OpenBLAS-THREADED/lib%{pname}64.so %{buildroot}%{_libdir}/lib%{pname}64.so
install -Dpm 0755 OpenBLAS-OPENMP/lib%{oname}64.so %{buildroot}%{_libdir}/lib%{oname}64.so
%endif

# symlinks
pushd %{buildroot}%{_libdir}
#   serial
ln -sf lib%{name}.so lib%{name}.so
ln -sf lib%{name}.so lib%{name}.so.%{major}
#   threaded
ln -sf lib%{pname}.so lib%{pname}.so
ln -sf lib%{pname}.so lib%{pname}.so.%{major}
#   OpenMP
ln -sf lib%{oname}.so lib%{oname}.so
ln -sf lib%{oname}.so lib%{oname}.so.%{major}
%if 0%{?arch64}
#   serial64
ln -sf lib%{name}64.so lib%{name}64.so
ln -sf lib%{name}64.so lib%{name}64.so.%{major}
#   threaded64
ln -sf lib%{pname}64.so lib%{pname}64.so
ln -sf lib%{pname}64.so lib%{pname}64.so.%{major}
#   OpenMP64
ln -sf lib%{oname}64.so lib%{oname}64.so
ln -sf lib%{oname}64.so lib%{oname}64.so.%{major}
%endif
popd

