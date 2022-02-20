%global SLOF_gittagdate 20191022

%global SLOF_gittagcommit 899d9883

%global have_usbredir 1
%global have_spice    1
%global have_opengl   1
%global have_fdt      1
%global have_gluster  1
%global have_kvm_setup 0
%global have_memlock_limits 0



# Release candidate version tracking
# global rcver rc4
%if 0%{?rcver:1}
%global rcrel .%{rcver}
%global rcstr -%{rcver}
%endif

%ifnarch %{ix86} x86_64
    %global have_usbredir 0
%endif

%ifnarch s390x
    %global have_librdma 1
%else
    %global have_librdma 0
%endif

%ifarch %{ix86}
    %global kvm_target    i386
%endif
%ifarch x86_64
    %global kvm_target    x86_64
%else
    %global have_spice   0
    %global have_opengl  0
    %global have_gluster 0
%endif
%ifarch %{power64}
    %global kvm_target    ppc64
    %global have_kvm_setup 1
    %global have_memlock_limits 1
%endif
%ifarch s390x
    %global kvm_target    s390x
    %global have_kvm_setup 1
%endif
%ifarch ppc
    %global kvm_target    ppc
%endif
%ifarch aarch64
    %global kvm_target    aarch64
%endif

#Versions of various parts:

%global requires_all_modules                                     \
%if %{have_spice}                                                \
Requires: %{name}-ui-spice = %{epoch}:%{version}-%{release}      \
%endif                                                           \
%if %{have_opengl}                                               \
Requires: %{name}-ui-opengl = %{epoch}:%{version}-%{release}     \
%endif                                                           \
Requires: %{name}-block-curl = %{epoch}:%{version}-%{release}    \
%if %{have_gluster}                                              \
Requires: %{name}-block-gluster = %{epoch}:%{version}-%{release} \
%endif                                                           \
%if %{have_usbredir}                                             \
Requires: %{name}-hw-usbredir = %{epoch}:%{version}-%{release}   \
%endif                                                           \
Requires: %{name}-block-iscsi = %{epoch}:%{version}-%{release}   \
Requires: %{name}-block-rbd = %{epoch}:%{version}-%{release}     \
Requires: %{name}-block-ssh = %{epoch}:%{version}-%{release}

# Macro to properly setup RHEL/RHEV conflict handling
%define rhev_ma_conflicts()                                      \
Obsoletes: %1-ma <= %{epoch}:%{version}-%{release}               \
Obsoletes: %1-rhev <= %{epoch}:%{version}-%{release}

Summary: QEMU is a machine emulator and virtualizer
Name: qemu-kvm
Version: 6.2.0
Release: 5%{?rcrel}%{?dist}
# Epoch because we pushed a qemu-1.0 package. AIUI this can't ever be dropped
Epoch: 15
License: GPLv2 and GPLv2+ and CC-BY
Group: Development/Tools
URL: http://www.qemu.org/
ExclusiveArch: x86_64 %{power64} aarch64 s390x


Source0: http://wiki.qemu.org/download/qemu-6.2.0.tar.xz

# KSM control scripts
Source4: ksm.service
Source5: ksm.sysconfig
Source6: ksmctl.c
Source7: ksmtuned.service
Source8: ksmtuned
Source9: ksmtuned.conf
Source10: qemu-guest-agent.service
Source11: 99-qemu-guest-agent.rules
Source12: bridge.conf
Source13: qemu-ga.sysconfig
Source21: kvm-setup
Source22: kvm-setup.service
Source23: 85-kvm.preset
Source26: vhost.conf
Source27: kvm.conf
Source28: 95-kvm-memlock.conf
Source30: kvm-s390x.conf
Source31: kvm-x86.conf
Source32: qemu-pr-helper.service
Source33: qemu-pr-helper.socket
Source34: 81-kvm-rhel.rules
Source35: udev-kvm-check.c
Source36: README.tests


Patch0001: 0001-redhat-Adding-slirp-to-the-exploded-tree.patch
Patch0005: 0005-Initial-redhat-build.patch
Patch0006: 0006-Enable-disable-devices-for-RHEL.patch
Patch0007: 0007-Machine-type-related-general-changes.patch
Patch0008: 0008-Add-aarch64-machine-types.patch
Patch0009: 0009-Add-ppc64-machine-types.patch
Patch0010: 0010-Add-s390x-machine-types.patch
Patch0011: 0011-Add-x86_64-machine-types.patch
Patch0012: 0012-Enable-make-check.patch
Patch0013: 0013-vfio-cap-number-of-devices-that-can-be-assigned.patch
Patch0014: 0014-Add-support-statement-to-help-output.patch
Patch0015: 0015-globally-limit-the-maximum-number-of-CPUs.patch
Patch0016: 0016-Use-qemu-kvm-in-documentation-instead-of-qemu-system.patch
Patch0017: 0017-virtio-scsi-Reject-scsi-cd-if-data-plane-enabled-RHE.patch
Patch0018: 0018-BZ1653590-Require-at-least-64kiB-pages-for-downstrea.patch
Patch0019: 0019-compat-Update-hw_compat_rhel_8_5.patch
Patch0020: 0020-redhat-Update-pseries-rhel8.5.0-machine-type.patch
Patch0021: 0021-redhat-virt-rhel8.5.0-Update-machine-type-compatibil.patch
Patch0022: 0022-Fix-virtio-net-pci-vectors-compat.patch
Patch0023: 0023-x86-rhel-machine-types-Add-pc_rhel_8_5_compat.patch
Patch0024: 0024-x86-rhel-machine-types-Wire-compat-into-q35-and-i440.patch
Patch0025: 0025-redhat-Add-s390x-machine-type-compatibility-handling.patch
# For bz#2005325 - Fix CPU Model for new IBM Z Hardware - qemu part
Patch26: kvm-redhat-Add-rhel8.6.0-machine-type-for-s390x.patch
# For bz#2031041 - Add rhel-8.6.0 machine types for RHEL 8.6 [ppc64le]
Patch27: kvm-redhat-Define-pseries-rhel8.6.0-machine-type.patch
# For bz#2031039 - Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64]
Patch28: kvm-hw-arm-virt-Register-iommu-as-a-class-property.patch
# For bz#2031039 - Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64]
Patch29: kvm-hw-arm-virt-Register-its-as-a-class-property.patch
# For bz#2031039 - Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64]
Patch30: kvm-hw-arm-virt-Rename-default_bus_bypass_iommu.patch
# For bz#2031039 - Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64]
Patch31: kvm-hw-arm-virt-Add-8.6-machine-type.patch
# For bz#2031039 - Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64]
Patch32: kvm-hw-arm-virt-Check-no_tcg_its-and-minor-style-changes.patch
# For bz#2029582 - [8.6] machine types: 6.2: Fix prefer_sockets
Patch33: kvm-rhel-machine-types-x86-set-prefer_sockets.patch
# For bz#2036580 - CVE-2021-4158 virt:rhel/qemu-kvm: QEMU: NULL pointer dereference in pci_write() in hw/acpi/pcihp.c [rhel-8]
Patch34: kvm-acpi-validate-hotplug-selector-on-access.patch
# For bz#2031035 - Add rhel-8.6.0 machine types for RHEL 8.6 [x86]
Patch35: kvm-x86-Add-q35-RHEL-8.6.0-machine-type.patch

BuildRequires: wget
BuildRequires: rpm-build
BuildRequires: ninja-build
#BuildRequires: meson >= 0.58.2
BuildRequires: zlib-devel
BuildRequires: glib2-devel
BuildRequires: which
BuildRequires: gnutls-devel
BuildRequires: cyrus-sasl-devel
BuildRequires: libtool
BuildRequires: libaio-devel
BuildRequires: rsync
BuildRequires: python3-devel
BuildRequires: pciutils-devel
BuildRequires: libiscsi-devel
BuildRequires: ncurses-devel
BuildRequires: libattr-devel
BuildRequires: libusbx-devel >= 1.0.23
%if %{have_usbredir}
BuildRequires: usbredir-devel >= 0.7.1
%endif
BuildRequires: texinfo
BuildRequires: python3-sphinx
%if %{have_spice}
BuildRequires: spice-protocol >= 0.12.12
BuildRequires: spice-server-devel >= 0.12.8
BuildRequires: libcacard-devel
# For smartcard NSS support
BuildRequires: nss-devel
%endif
BuildRequires: libseccomp-devel >= 2.4.0
# For network block driver
BuildRequires: libcurl-devel
BuildRequires: libssh-devel
BuildRequires: librados-devel
BuildRequires: librbd-devel
%if %{have_gluster}
# For gluster block driver
BuildRequires: glusterfs-api-devel
BuildRequires: glusterfs-devel
%endif
# We need both because the 'stap' binary is probed for by configure
BuildRequires: systemtap
BuildRequires: systemtap-sdt-devel
# For VNC PNG support
BuildRequires: libpng-devel
# For uuid generation
BuildRequires: libuuid-devel
# For Braille device support
BuildRequires: brlapi-devel
# For test suite
BuildRequires: check-devel
# For virtiofs
BuildRequires: libcap-ng-devel
# Hard requirement for version >= 1.3
BuildRequires: pixman-devel
# Documentation requirement
BuildRequires: perl-podlators
BuildRequires: texinfo
BuildRequires: python3-sphinx
# For rdma
%if 0%{?have_librdma}
BuildRequires: rdma-core-devel
%endif
%if %{have_fdt}
BuildRequires: libfdt-devel >= 1.6.0
%endif
# iasl and cpp for acpi generation (not a hard requirement as we can use
# pre-compiled files, but it's better to use this)
%ifarch %{ix86} x86_64
BuildRequires: iasl
BuildRequires: cpp
%endif
# For compressed guest memory dumps
BuildRequires: lzo-devel snappy-devel
# For NUMA memory binding
%ifnarch s390x
BuildRequires: numactl-devel
%endif
BuildRequires: libgcrypt-devel
# qemu-pr-helper multipath support (requires libudev too)
BuildRequires: device-mapper-multipath-devel
BuildRequires: systemd-devel
# used by qemu-bridge-helper and qemu-pr-helper
BuildRequires: libcap-ng-devel

BuildRequires: diffutils
%ifarch x86_64
BuildRequires: libpmem-devel
Requires: libpmem
%endif

# qemu-keymap
BuildRequires: pkgconfig(xkbcommon)

# For s390-pgste flag
%ifarch s390x
BuildRequires: binutils >= 2.27-16
%endif

%if %{have_opengl}
BuildRequires: pkgconfig(epoxy)
BuildRequires: pkgconfig(libdrm)
BuildRequires: pkgconfig(gbm)
%endif

BuildRequires: perl-Test-Harness

Requires: qemu-kvm-core = %{epoch}:%{version}-%{release}
Requires: qemu-kvm-docs = %{epoch}:%{version}-%{release}
%rhev_ma_conflicts qemu-kvm

%{requires_all_modules}

%define qemudocdir %{_docdir}/%{name}

%description
qemu-kvm is an open source virtualizer that provides hardware
emulation for the KVM hypervisor. qemu-kvm acts as a virtual
machine monitor together with the KVM kernel modules, and emulates the
hardware for a full system such as a PC and its associated peripherals.


%package -n qemu-kvm-core
Summary: qemu-kvm core components
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: qemu-img = %{epoch}:%{version}-%{release}
%ifarch %{ix86} x86_64
Requires: edk2-ovmf
%endif
%ifarch aarch64
Requires: edk2-aarch64
%endif

%ifarch %{power64}
Requires: SLOF >= %{SLOF_gittagdate}-1.git%{SLOF_gittagcommit}
%endif
Requires: libseccomp >= 2.4.0
# For compressed guest memory dumps
Requires: lzo snappy
%if %{have_kvm_setup}
Requires(post): systemd-units
Requires(preun): systemd-units
    %ifarch %{power64}
Requires: powerpc-utils
    %endif
%endif
Requires: libusbx >= 1.0.23
%if %{have_fdt}
Requires: libfdt >= 1.6.0
%endif

%rhev_ma_conflicts qemu-kvm

%description -n qemu-kvm-core
qemu-kvm is an open source virtualizer that provides hardware
emulation for the KVM hypervisor. qemu-kvm acts as a virtual
machine monitor together with the KVM kernel modules, and emulates the
hardware for a full system such as a PC and its associated peripherals.

%package -n qemu-kvm-docs
Summary: qemu-kvm documentation

%description -n qemu-kvm-docs
qemu-kvm-docs provides documentation files regarding qemu-kvm.

%package -n qemu-img
Summary: QEMU command line tool for manipulating disk images
Group: Development/Tools

%rhev_ma_conflicts qemu-img

%description -n qemu-img
This package provides a command line tool for manipulating disk images.

%package -n qemu-kvm-common
Summary: QEMU common files needed by all QEMU targets
Group: Development/Tools
Requires(post): /usr/bin/getent
Requires(post): /usr/sbin/groupadd
Requires(post): /usr/sbin/useradd
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%ifarch %{ix86} x86_64
Requires: seabios-bin >= 1.10.2-1
Requires: sgabios-bin
%endif
%ifnarch aarch64 s390x
Requires: seavgabios-bin >= 1.12.0-3
Requires: ipxe-roms-qemu >= 20170123-1
%endif

%rhev_ma_conflicts qemu-kvm-common

%description -n qemu-kvm-common
qemu-kvm is an open source virtualizer that provides hardware emulation for
the KVM hypervisor.

This package provides documentation and auxiliary programs used with qemu-kvm.


%package -n qemu-guest-agent
Summary: QEMU guest agent
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description -n qemu-guest-agent
qemu-kvm is an open source virtualizer that provides hardware emulation for
the KVM hypervisor.

This package provides an agent to run inside guests, which communicates
with the host over a virtio-serial channel named "org.qemu.guest_agent.0"

This package does not need to be installed on the host OS.

%package tests
Summary: tests for the qemu-kvm package
Requires: %{name} = %{epoch}:%{version}-%{release}

%define testsdir %{_libdir}/%{name}/tests-src

%description tests
The qemu-kvm-tests rpm contains tests that can be used to verify
the functionality of the installed qemu-kvm package

Install this package if you want access to the avocado_qemu
tests, or qemu-iotests.

%package  block-curl
Summary: QEMU CURL block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-curl
This package provides the additional CURL block driver for QEMU.

Install this package if you want to access remote disks over
http, https, ftp and other transports provided by the CURL library.


%if %{have_gluster}
%package  block-gluster
Summary: QEMU Gluster block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}
%description block-gluster
This package provides the additional Gluster block driver for QEMU.

Install this package if you want to access remote Gluster storage.
%endif


%package  block-iscsi
Summary: QEMU iSCSI block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-iscsi
This package provides the additional iSCSI block driver for QEMU.

Install this package if you want to access iSCSI volumes.


%package  block-rbd
Summary: QEMU Ceph/RBD block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-rbd
This package provides the additional Ceph/RBD block driver for QEMU.

Install this package if you want to access remote Ceph volumes
using the rbd protocol.


%package  block-ssh
Summary: QEMU SSH block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-ssh
This package provides the additional SSH block driver for QEMU.

Install this package if you want to access remote disks using
the Secure Shell (SSH) protocol.


%if %{have_spice}
%package  ui-spice
Summary: QEMU spice support
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}
%if %{have_opengl}
Requires: %{name}-ui-opengl%{?_isa} = %{epoch}:%{version}-%{release}
%endif

%description ui-spice
This package provides spice support.
%endif


%if %{have_opengl}
%package  ui-opengl
Summary: QEMU opengl support
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}
Requires: mesa-libGL
Requires: mesa-libEGL
Requires: mesa-dri-drivers

%description ui-opengl
This package provides opengl support.
%endif

%if %{have_usbredir}
%package  hw-usbredir
Summary: QEMU usbredir support
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}
Requires: usbredir >= 0.7.1

%description hw-usbredir
This package provides usbredir support.
%endif


%prep
%setup -q -n qemu-%{version}%{?rcstr}
# Remove slirp content in scratchbuilds because it's being applyed as a patch
rm -fr slirp
mkdir slirp
%autopatch -p1

%global qemu_kvm_build qemu_kvm_build
mkdir -p %{qemu_kvm_build}


%build
%global buildarch %{kvm_target}-softmmu

# --build-id option is used for giving info to the debug packages.
buildldflags="VL_LDFLAGS=-Wl,--build-id"

%global block_drivers_list qcow2,raw,file,host_device,nbd,iscsi,rbd,blkdebug,luks,null-co,nvme,copy-on-read,throttle

%if 0%{have_gluster}
    %global block_drivers_list %{block_drivers_list},gluster
%endif


%define disable_everything         \\\
  --disable-alsa                   \\\
  --disable-attr                   \\\
  --disable-auth-pam               \\\
  --disable-avx2                   \\\
  --disable-avx512f                \\\
  --disable-bochs                  \\\
  --disable-bpf                    \\\
  --disable-brlapi                 \\\
  --disable-bsd-user               \\\
  --disable-bzip2                  \\\
  --disable-cap-ng                 \\\
  --disable-capstone               \\\
  --disable-cfi                    \\\
  --disable-cfi-debug              \\\
  --disable-cloop                  \\\
  --disable-cocoa                  \\\
  --disable-coreaudio              \\\
  --disable-coroutine-pool         \\\
  --disable-crypto-afalg           \\\
  --disable-curl                   \\\
  --disable-curses                 \\\
  --disable-debug-info             \\\
  --disable-debug-mutex            \\\
  --disable-debug-tcg              \\\
  --disable-dmg                    \\\
  --disable-docs                   \\\
  --disable-dsound                 \\\
  --disable-fdt                    \\\
  --disable-fuse                   \\\
  --disable-fuse-lseek             \\\
  --disable-gcrypt                 \\\
  --disable-gettext                \\\
  --disable-gio                    \\\
  --disable-glusterfs              \\\
  --disable-gnutls                 \\\
  --disable-gtk                    \\\
  --disable-guest-agent            \\\
  --disable-guest-agent-msi        \\\
  --disable-hax                    \\\
  --disable-hvf                    \\\
  --disable-iconv                  \\\
  --disable-jack                   \\\
  --disable-kvm                    \\\
  --disable-l2tpv3                 \\\
  --disable-libdaxctl              \\\
  --disable-libiscsi               \\\
  --disable-libnfs                 \\\
  --disable-libpmem                \\\
  --disable-libssh                 \\\
  --disable-libudev                \\\
  --disable-libusb                 \\\
  --disable-libxml2                \\\
  --disable-linux-aio              \\\
  --disable-linux-io-uring         \\\
  --disable-linux-user             \\\
  --disable-live-block-migration   \\\
  --disable-lto                    \\\
  --disable-lzfse                  \\\
  --disable-lzo                    \\\
  --disable-malloc-trim            \\\
  --disable-membarrier             \\\
  --disable-modules                \\\
  --disable-module-upgrades        \\\
  --disable-mpath                  \\\
  --disable-multiprocess           \\\
  --disable-netmap                 \\\
  --disable-nettle                 \\\
  --disable-numa                   \\\
  --disable-nvmm                   \\\
  --disable-opengl                 \\\
  --disable-oss                    \\\
  --disable-pa                     \\\
  --disable-parallels              \\\
  --disable-pie                    \\\
  --disable-pvrdma                 \\\
  --disable-qcow1                  \\\
  --disable-qed                    \\\
  --disable-qom-cast-debug         \\\
  --disable-rbd                    \\\
  --disable-rdma                   \\\
  --disable-replication            \\\
  --disable-rng-none               \\\
  --disable-safe-stack             \\\
  --disable-sanitizers             \\\
  --disable-sdl                    \\\
  --disable-sdl-image              \\\
  --disable-seccomp                \\\
  --disable-selinux                \\\
  --disable-slirp-smbd             \\\
  --disable-smartcard              \\\
  --disable-snappy                 \\\
  --disable-sparse                 \\\
  --disable-spice                  \\\
  --disable-spice-protocol         \\\
  --disable-strip                  \\\
  --disable-system                 \\\
  --disable-tcg                    \\\
  --disable-tools                  \\\
  --disable-tpm                    \\\
  --disable-u2f                    \\\
  --disable-usb-redir              \\\
  --disable-user                   \\\
  --disable-vde                    \\\
  --disable-vdi                    \\\
  --disable-vhost-crypto           \\\
  --disable-vhost-kernel           \\\
  --disable-vhost-net              \\\
  --disable-vhost-scsi             \\\
  --disable-vhost-user             \\\
  --disable-vhost-user-blk-server  \\\
  --disable-vhost-vdpa             \\\
  --disable-vhost-vsock            \\\
  --disable-virglrenderer          \\\
  --disable-virtfs                 \\\
  --disable-virtiofsd              \\\
  --disable-vnc                    \\\
  --disable-vnc-jpeg               \\\
  --disable-vnc-png                \\\
  --disable-vnc-sasl               \\\
  --disable-vte                    \\\
  --disable-vvfat                  \\\
  --disable-werror                 \\\
  --disable-whpx                   \\\
  --disable-xen                    \\\
  --disable-xen-pci-passthrough    \\\
  --disable-xfsctl                 \\\
  --disable-xkbcommon              \\\
  --disable-zstd                   \\\
  --with-git-submodules=ignore

pushd %{qemu_kvm_build}
../configure  \
  --prefix="%{_prefix}" \
  --libdir="%{_libdir}" \
  --datadir="%{_datadir}" \
  --sysconfdir="%{_sysconfdir}" \
  --interp-prefix=%{_prefix}/qemu-%M \
  --localstatedir="%{_localstatedir}" \
  --docdir="%{_docdir}" \
  --libexecdir="%{_libexecdir}" \
  --extra-ldflags="-Wl,--build-id -Wl,-z,relro -Wl,-z,now" \
  --extra-cflags="%{optflags}" \
  --with-pkgversion="%{name}-%{version}-%{release}" \
  --with-suffix="%{name}" \
  --firmwarepath=%{_prefix}/share/qemu-firmware \
  --meson="git" \
  --target-list="%{buildarch}" \
  --block-drv-rw-whitelist=%{block_drivers_list} \
  --audio-drv-list= \
  --block-drv-ro-whitelist=vmdk,vhdx,vpc,https,ssh \
  --with-coroutine=ucontext \
  --with-git=git \
  --tls-priority=@QEMU,SYSTEM \
  %{disable_everything} \
  --enable-attr \
%ifarch %{ix86} x86_64
  --enable-avx2 \
%endif
  --enable-cap-ng \
  --enable-capstone=internal \
  --enable-coroutine-pool \
  --enable-curl \
  --enable-debug-info \
  --enable-docs \
%if 0%{have_fdt}
  --enable-fdt=system \
%endif
  --enable-gcrypt \
%if 0%{have_gluster}
  --enable-glusterfs \
%endif
  --enable-gnutls \
  --enable-guest-agent \
  --enable-iconv \
  --enable-kvm \
  --enable-libiscsi \
%ifarch x86_64
  --enable-libpmem \
%endif
  --enable-libssh \
  --enable-libusb \
  --enable-libudev \
  --enable-linux-aio \
  --enable-lzo \
  --enable-malloc-trim \
  --enable-modules \
  --enable-mpath \
%ifnarch s390x
  --enable-numa \
%endif
%if 0%{have_opengl}
  --enable-opengl \
%endif
  --enable-pie \
  --enable-rbd \
%if 0%{have_librdma}
  --enable-rdma \
%endif
  --enable-seccomp \
  --enable-snappy \
%if 0%{have_spice}
  --enable-smartcard \
  --enable-spice \
  --enable-spice-protocol \
%endif
  --enable-system \
  --enable-tcg \
  --enable-tools \
  --enable-tpm \
  --enable-trace-backend=dtrace \
%if 0%{have_usbredir}
  --enable-usb-redir \
%endif
  --enable-virtiofsd \
  --enable-vhost-kernel \
  --enable-vhost-net \
  --enable-vhost-user \
  --enable-vhost-user-blk-server \
  --enable-vhost-vdpa \
  --enable-vhost-vsock \
  --enable-vnc \
  --enable-vnc-png \
  --enable-vnc-sasl \
  --enable-werror \
  --enable-xkbcommon \
  --with-default-devices \
  --with-devices-%{kvm_target}=%{kvm_target}-rh-devices


echo "qemu-kvm config-host.mak contents:"
echo "==="
cat config-host.mak
echo "==="

make V=1 %{?_smp_mflags} $buildldflags

# Setup back compat qemu-kvm binary
%{__python3} scripts/tracetool.py --backend dtrace --format stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm.stp

%{__python3} scripts/tracetool.py --backends=dtrace --format=log-stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm-log.stp

%{__python3} scripts/tracetool.py --backend dtrace --format simpletrace-stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm-simpletrace.stp

cp -a %{kvm_target}-softmmu/qemu-system-%{kvm_target} qemu-kvm

gcc %{SOURCE6} $RPM_OPT_FLAGS $RPM_LD_FLAGS -o ksmctl
gcc %{SOURCE35} $RPM_OPT_FLAGS $RPM_LD_FLAGS -o udev-kvm-check

%ifarch s390x
    # Copy the built new images into place for "make check":
    cp pc-bios/s390-ccw/s390-ccw.img pc-bios/s390-ccw/s390-netboot.img pc-bios/
%endif

popd

%install
pushd %{qemu_kvm_build}
%define _udevdir %(pkg-config --variable=udevdir udev)
%define _udevrulesdir %{_udevdir}/rules.d

install -D -p -m 0644 %{SOURCE4} $RPM_BUILD_ROOT%{_unitdir}/ksm.service
install -D -p -m 0644 %{SOURCE5} $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/ksm
install -D -p -m 0755 ksmctl $RPM_BUILD_ROOT%{_libexecdir}/ksmctl

install -D -p -m 0644 %{SOURCE7} $RPM_BUILD_ROOT%{_unitdir}/ksmtuned.service
install -D -p -m 0755 %{SOURCE8} $RPM_BUILD_ROOT%{_sbindir}/ksmtuned
install -D -p -m 0644 %{SOURCE9} $RPM_BUILD_ROOT%{_sysconfdir}/ksmtuned.conf
install -D -p -m 0644 %{SOURCE26} $RPM_BUILD_ROOT%{_sysconfdir}/modprobe.d/vhost.conf
%ifarch s390x
    install -D -p -m 0644 %{SOURCE30} $RPM_BUILD_ROOT%{_sysconfdir}/modprobe.d/kvm.conf
%else
%ifarch %{ix86} x86_64
    install -D -p -m 0644 %{SOURCE31} $RPM_BUILD_ROOT%{_sysconfdir}/modprobe.d/kvm.conf
%else
    install -D -p -m 0644 %{SOURCE27} $RPM_BUILD_ROOT%{_sysconfdir}/modprobe.d/kvm.conf
%endif
%endif

mkdir -p $RPM_BUILD_ROOT%{_bindir}/
mkdir -p $RPM_BUILD_ROOT%{_udevrulesdir}/
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}

# Create new directories and put them all under tests-src
mkdir -p $RPM_BUILD_ROOT%{testsdir}/python
mkdir -p $RPM_BUILD_ROOT%{testsdir}/tests
mkdir -p $RPM_BUILD_ROOT%{testsdir}/tests/avocado
mkdir -p $RPM_BUILD_ROOT%{testsdir}/tests/qemu-iotests
mkdir -p $RPM_BUILD_ROOT%{testsdir}/scripts/qmp

install -p -m 0755 udev-kvm-check $RPM_BUILD_ROOT%{_udevdir}
install -p -m 0644 %{SOURCE34} $RPM_BUILD_ROOT%{_udevrulesdir}

install -m 0644 scripts/dump-guest-memory.py \
                $RPM_BUILD_ROOT%{_datadir}/%{name}

# Install avocado_qemu tests
cp -R tests/avocado/* $RPM_BUILD_ROOT%{testsdir}/tests/avocado/

# Install qemu.py and qmp/ scripts required to run avocado_qemu tests
cp -R python/qemu $RPM_BUILD_ROOT%{testsdir}/python
cp -R scripts/qmp/* $RPM_BUILD_ROOT%{testsdir}/scripts/qmp
install -p -m 0755 ../tests/Makefile.include $RPM_BUILD_ROOT%{testsdir}/tests/

# Install qemu-iotests
cp -R ../tests/qemu-iotests/* $RPM_BUILD_ROOT%{testsdir}/tests/qemu-iotests/
cp -ur tests/qemu-iotests/* $RPM_BUILD_ROOT%{testsdir}/tests/qemu-iotests/
# Avoid ambiguous 'python' interpreter name
find $RPM_BUILD_ROOT%{testsdir}/tests/qemu-iotests/* -maxdepth 1 -type f -exec sed -i -e '1 s+/usr/bin/env \(python\|python3\)+%{__python3}+' {} \;
find $RPM_BUILD_ROOT%{testsdir}/scripts/qmp/* -maxdepth 1 -type f -exec sed -i -e '1 s+/usr/bin/env \(python\|python3\)+%{__python3}+' {} \;
find $RPM_BUILD_ROOT%{testsdir}/scripts/qmp/* -maxdepth 1 -type f -exec sed -i -e '1 s+/usr/bin/\(python\|python3\)+%{__python3}+' {} \;

install -p -m 0644 %{SOURCE36} $RPM_BUILD_ROOT%{testsdir}/README

make DESTDIR=$RPM_BUILD_ROOT \
    sharedir="%{_datadir}/%{name}" \
    datadir="%{_datadir}/%{name}" \
    install

mkdir -p $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset

# Move vhost-user JSON files to the standard "qemu" directory
mkdir -p $RPM_BUILD_ROOT%{_datadir}/qemu
mv $RPM_BUILD_ROOT%{_datadir}/%{name}/vhost-user $RPM_BUILD_ROOT%{_datadir}/qemu/

# Install qemu-guest-agent service and udev rules
install -m 0644 %{_sourcedir}/qemu-guest-agent.service %{buildroot}%{_unitdir}
install -m 0644 %{_sourcedir}/qemu-ga.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/qemu-ga
install -m 0644 %{_sourcedir}/99-qemu-guest-agent.rules %{buildroot}%{_udevrulesdir}

# - the fsfreeze hook script:
install -D --preserve-timestamps \
            scripts/qemu-guest-agent/fsfreeze-hook \
            $RPM_BUILD_ROOT%{_sysconfdir}/qemu-ga/fsfreeze-hook
# Workaround for the missing /etc/qemu-kvm/fsfreeze-hook
# Please, do not carry this over to RHEL-9
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/qemu-kvm/
ln -s %{_sysconfdir}/qemu-ga/fsfreeze-hook \
      $RPM_BUILD_ROOT%{_sysconfdir}/qemu-kvm/fsfreeze-hook

# - the directory for user scripts:
mkdir $RPM_BUILD_ROOT%{_sysconfdir}/qemu-ga/fsfreeze-hook.d

# - and the fsfreeze script samples:
mkdir --parents $RPM_BUILD_ROOT%{_datadir}/%{name}/qemu-ga/fsfreeze-hook.d/
install --preserve-timestamps --mode=0644 \
             scripts/qemu-guest-agent/fsfreeze-hook.d/*.sample \
             $RPM_BUILD_ROOT%{_datadir}/%{name}/qemu-ga/fsfreeze-hook.d/

# - Install dedicated log directory:
mkdir -p -v $RPM_BUILD_ROOT%{_localstatedir}/log/qemu-ga/

mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -c -m 0755  qga/qemu-ga ${RPM_BUILD_ROOT}%{_bindir}/qemu-ga

mkdir -p $RPM_BUILD_ROOT%{_mandir}/man8

install -m 0755 %{kvm_target}-softmmu/qemu-system-%{kvm_target} $RPM_BUILD_ROOT%{_libexecdir}/qemu-kvm
install -m 0644 qemu-kvm.stp $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/
install -m 0644 qemu-kvm-log.stp $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/
install -m 0644 qemu-kvm-simpletrace.stp $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/
install -d -m 0755 "$RPM_BUILD_ROOT%{_datadir}/%{name}/systemtap/script.d"
install -c -m 0644 scripts/systemtap/script.d/qemu_kvm.stp "$RPM_BUILD_ROOT%{_datadir}/%{name}/systemtap/script.d/"
install -d -m 0755 "$RPM_BUILD_ROOT%{_datadir}/%{name}/systemtap/conf.d"
install -c -m 0644 scripts/systemtap/conf.d/qemu_kvm.conf "$RPM_BUILD_ROOT%{_datadir}/%{name}/systemtap/conf.d/"


rm $RPM_BUILD_ROOT/%{_datadir}/applications/qemu.desktop
rm $RPM_BUILD_ROOT%{_bindir}/qemu-system-%{kvm_target}
rm $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}.stp
rm $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}-simpletrace.stp
rm $RPM_BUILD_ROOT%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}-log.stp
rm $RPM_BUILD_ROOT%{_bindir}/elf2dmp

# Install simpletrace
install -m 0755 scripts/simpletrace.py $RPM_BUILD_ROOT%{_datadir}/%{name}/simpletrace.py
# Avoid ambiguous 'python' interpreter name
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool
install -m 0644 -t $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool scripts/tracetool/*.py
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool/backend
install -m 0644 -t $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool/backend scripts/tracetool/backend/*.py
mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool/format
install -m 0644 -t $RPM_BUILD_ROOT%{_datadir}/%{name}/tracetool/format scripts/tracetool/format/*.py

mkdir -p $RPM_BUILD_ROOT%{qemudocdir}
install -p -m 0644 -t ${RPM_BUILD_ROOT}%{qemudocdir} ../README.rst ../README.systemtap ../COPYING ../COPYING.LIB ../LICENSE ../docs/interop/qmp-spec.txt

# Rename man page
pushd ${RPM_BUILD_ROOT}%{_mandir}/man1/
for fn in qemu.1*; do
     mv $fn "qemu-kvm${fn#qemu}"
done
popd
chmod -x ${RPM_BUILD_ROOT}%{_mandir}/man1/*
chmod -x ${RPM_BUILD_ROOT}%{_mandir}/man8/*

install -D -p -m 0644 ../qemu.sasl $RPM_BUILD_ROOT%{_sysconfdir}/sasl2/%{name}.conf

# Install keymaps
pushd pc-bios/keymaps
for kmp in *; do
   install $kmp ${RPM_BUILD_ROOT}%{_datadir}/%{name}/keymaps/
done
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/keymaps/*.stamp
popd

# Provided by package openbios
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-ppc
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-sparc32
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/openbios-sparc64
# Provided by package SLOF
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/slof.bin

# Remove unpackaged files.
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/palcode-clipper
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/petalogix*.dtb
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/bamboo.dtb
rm -f ${RPM_BUILD_ROOT}%{_datadir}/%{name}/ppc_rom.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/s390-zipl.rom
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/u-boot.e500
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/qemu_vga.ndrv
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/skiboot.lid
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/qboot.rom

rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/s390-ccw.img
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/s390-netboot.img
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/hppa-firmware.img
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/canyonlands.dtb
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/u-boot-sam460-20100605.bin

rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/firmware
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/edk2-*.fd
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/edk2-licenses.txt

rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv32-sifive_u-fw_jump.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv32-virt-fw_jump.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv32-generic-fw_dynamic.*
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv64-sifive_u-fw_jump.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv64-virt-fw_jump.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/opensbi-riscv64-generic-fw_dynamic.*
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/qemu-nsis.bmp
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/npcm7xx_bootrom.bin

rm -rf ${RPM_BUILD_ROOT}%{_libdir}/qemu-kvm/ui-spice-app.so

# Remove virtfs-proxy-helper files
rm -rf ${RPM_BUILD_ROOT}%{_libexecdir}/virtfs-proxy-helper
rm -rf ${RPM_BUILD_ROOT}%{_mandir}/man1/virtfs-proxy-helper*

%ifarch s390x
    # Use the s390-*.imgs that we've just built, not the pre-built ones
    install -m 0644 pc-bios/s390-ccw/s390-ccw.img $RPM_BUILD_ROOT%{_datadir}/%{name}/
    install -m 0644 pc-bios/s390-ccw/s390-netboot.img $RPM_BUILD_ROOT%{_datadir}/%{name}/
%else
    rm -rf ${RPM_BUILD_ROOT}%{_libdir}/qemu-kvm/hw-s390x-virtio-gpu-ccw.so
%endif

%ifnarch x86_64
    rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/kvmvapic.bin
    rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/linuxboot.bin
    rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/multiboot.bin
    rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/multiboot_dma.bin
    rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/pvh.bin
%endif

# Remove sparc files
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/QEMU,tcx.bin
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/QEMU,cgthree.bin

# Remove ivshmem example programs
rm -rf ${RPM_BUILD_ROOT}%{_bindir}/ivshmem-client
rm -rf ${RPM_BUILD_ROOT}%{_bindir}/ivshmem-server

# Remove efi roms
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/efi*.rom

# Provided by package ipxe
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/pxe*rom
# Provided by package vgabios
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/vgabios*bin
# Provided by package seabios
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/bios*.bin
# Provided by package sgabios
rm -rf ${RPM_BUILD_ROOT}%{_datadir}/%{name}/sgabios.bin

# the pxe gpxe images will be symlinks to the images on
# /usr/share/ipxe, as QEMU doesn't know how to look
# for other paths, yet.
pxe_link() {
    ln -s ../ipxe.efi/$2.rom %{buildroot}%{_datadir}/%{name}/efi-$1.rom
}

%ifnarch aarch64 s390x
pxe_link e1000 8086100e
pxe_link ne2k_pci 10ec8029
pxe_link pcnet 10222000
pxe_link rtl8139 10ec8139
pxe_link virtio 1af41000
pxe_link e1000e 808610d3
%endif

rom_link() {
    ln -s $1 %{buildroot}%{_datadir}/%{name}/$2
}

%ifnarch aarch64 s390x
  rom_link ../seavgabios/vgabios-isavga.bin vgabios.bin
  rom_link ../seavgabios/vgabios-cirrus.bin vgabios-cirrus.bin
  rom_link ../seavgabios/vgabios-qxl.bin vgabios-qxl.bin
  rom_link ../seavgabios/vgabios-stdvga.bin vgabios-stdvga.bin
  rom_link ../seavgabios/vgabios-vmware.bin vgabios-vmware.bin
  rom_link ../seavgabios/vgabios-virtio.bin vgabios-virtio.bin
  rom_link ../seavgabios/vgabios-ramfb.bin vgabios-ramfb.bin
  rom_link ../seavgabios/vgabios-bochs-display.bin vgabios-bochs-display.bin
%endif
%ifarch x86_64
  rom_link ../seabios/bios.bin bios.bin
  rom_link ../seabios/bios-256k.bin bios-256k.bin
  rom_link ../sgabios/sgabios.bin sgabios.bin
%endif

%if 0%{have_kvm_setup}
    install -D -p -m 755 %{SOURCE21} $RPM_BUILD_ROOT%{_prefix}/lib/systemd/kvm-setup
    install -D -p -m 644 %{SOURCE22} $RPM_BUILD_ROOT%{_unitdir}/kvm-setup.service
    install -D -p -m 644 %{SOURCE23} $RPM_BUILD_ROOT%{_presetdir}/85-kvm.preset
%endif

%if 0%{have_memlock_limits}
    install -D -p -m 644 %{SOURCE28} $RPM_BUILD_ROOT%{_sysconfdir}/security/limits.d/95-kvm-memlock.conf
%endif

# Install rules to use the bridge helper with libvirt's virbr0
install -D -m 0644 %{SOURCE12} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/bridge.conf

# Install qemu-pr-helper service
install -m 0644 %{_sourcedir}/qemu-pr-helper.service %{buildroot}%{_unitdir}
install -m 0644 %{_sourcedir}/qemu-pr-helper.socket %{buildroot}%{_unitdir}

find $RPM_BUILD_ROOT -name '*.la' -or -name '*.a' | xargs rm -f

# We need to make the block device modules and other qemu SO files executable
# otherwise RPM won't pick up their dependencies.
chmod +x $RPM_BUILD_ROOT%{_libdir}/qemu-kvm/*.so

# Remove buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/interop/.buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/system/.buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/tools/.buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/user/.buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/devel/.buildinfo
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/.buildinfo

# Remove spec
rm -rf $RPM_BUILD_ROOT%{qemudocdir}/specs

popd

%check
pushd %{qemu_kvm_build}
echo "Testing qemu-kvm-build"
export DIFF=diff; make check V=1
popd

%post -n qemu-kvm-common
%systemd_post ksm.service
%systemd_post ksmtuned.service

getent group kvm >/dev/null || groupadd -g 36 -r kvm
getent group qemu >/dev/null || groupadd -g 107 -r qemu
getent passwd qemu >/dev/null || \
useradd -r -u 107 -g qemu -G kvm -d / -s /sbin/nologin \
  -c "qemu user" qemu

# load kvm modules now, so we can make sure no reboot is needed.
# If there's already a kvm module installed, we don't mess with it
%udev_rules_update
sh %{_sysconfdir}/sysconfig/modules/kvm.modules &> /dev/null || :
    udevadm trigger --subsystem-match=misc --sysname-match=kvm --action=add || :
%if %{have_kvm_setup}
    systemctl daemon-reload # Make sure it sees the new presets and unitfile
    %systemd_post kvm-setup.service
    if systemctl is-enabled kvm-setup.service > /dev/null; then
        systemctl start kvm-setup.service
    fi
%endif

%preun -n qemu-kvm-common
%systemd_preun ksm.service
%systemd_preun ksmtuned.service
%if %{have_kvm_setup}
%systemd_preun kvm-setup.service
%endif

%postun -n qemu-kvm-common
%systemd_postun_with_restart ksm.service
%systemd_postun_with_restart ksmtuned.service

%post -n qemu-guest-agent
%systemd_post qemu-guest-agent.service
%preun -n qemu-guest-agent
%systemd_preun qemu-guest-agent.service
%postun -n qemu-guest-agent
%systemd_postun_with_restart qemu-guest-agent.service

%files
# Deliberately empty

%files -n qemu-kvm-docs
%defattr(-,root,root)
%dir %{qemudocdir}
%doc %{qemudocdir}/genindex.html
%doc %{qemudocdir}/search.html
%doc %{qemudocdir}/objects.inv
%doc %{qemudocdir}/searchindex.js
%doc %{qemudocdir}/README.rst
%doc %{qemudocdir}/COPYING
%doc %{qemudocdir}/COPYING.LIB
%doc %{qemudocdir}/LICENSE
%doc %{qemudocdir}/README.systemtap
%doc %{qemudocdir}/qmp-spec.txt
%doc %{qemudocdir}/interop/*
%doc %{qemudocdir}/index.html
%doc %{qemudocdir}/about/*
%doc %{qemudocdir}/system/*
%doc %{qemudocdir}/tools/*
%doc %{qemudocdir}/user/*
%doc %{qemudocdir}/devel/*
%doc %{qemudocdir}/_static/*

%files -n qemu-kvm-common
%defattr(-,root,root)
%{_mandir}/man7/qemu-qmp-ref.7*
%{_mandir}/man7/qemu-cpu-models.7*
%{_bindir}/qemu-keymap
%{_bindir}/qemu-pr-helper
%{_bindir}/qemu-edid
%{_bindir}/qemu-trace-stap
%{_unitdir}/qemu-pr-helper.service
%{_unitdir}/qemu-pr-helper.socket
%{_mandir}/man7/qemu-ga-ref.7*
%{_mandir}/man8/qemu-pr-helper.8*
%{_mandir}/man1/virtiofsd.1*

%dir %{_datadir}/%{name}/
%{_datadir}/%{name}/keymaps/
%{_mandir}/man1/%{name}.1*
%{_mandir}/man1/qemu-trace-stap.1*
%{_mandir}/man7/qemu-block-drivers.7*
%attr(4755, -, -) %{_libexecdir}/qemu-bridge-helper
%config(noreplace) %{_sysconfdir}/sasl2/%{name}.conf
%{_unitdir}/ksm.service
%{_libexecdir}/ksmctl
%config(noreplace) %{_sysconfdir}/sysconfig/ksm
%{_unitdir}/ksmtuned.service
%{_sbindir}/ksmtuned
%{_udevdir}/udev-kvm-check
%{_udevrulesdir}/81-kvm-rhel.rules
%ghost %{_sysconfdir}/kvm
%config(noreplace) %{_sysconfdir}/ksmtuned.conf
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/bridge.conf
%config(noreplace) %{_sysconfdir}/modprobe.d/vhost.conf
%config(noreplace) %{_sysconfdir}/modprobe.d/kvm.conf
%{_datadir}/%{name}/simpletrace.py*
%{_datadir}/%{name}/tracetool/*.py*
%{_datadir}/%{name}/tracetool/backend/*.py*
%{_datadir}/%{name}/tracetool/format/*.py*

%ifarch x86_64
    %{_datadir}/%{name}/bios.bin
    %{_datadir}/%{name}/bios-256k.bin
    %{_datadir}/%{name}/linuxboot.bin
    %{_datadir}/%{name}/multiboot.bin
    %{_datadir}/%{name}/multiboot_dma.bin
    %{_datadir}/%{name}/kvmvapic.bin
    %{_datadir}/%{name}/sgabios.bin
    %{_datadir}/%{name}/pvh.bin
%endif
%ifarch s390x
    %{_datadir}/%{name}/s390-ccw.img
    %{_datadir}/%{name}/s390-netboot.img
%endif
%ifnarch aarch64 s390x
    %{_datadir}/%{name}/vgabios.bin
    %{_datadir}/%{name}/vgabios-cirrus.bin
    %{_datadir}/%{name}/vgabios-qxl.bin
    %{_datadir}/%{name}/vgabios-stdvga.bin
    %{_datadir}/%{name}/vgabios-vmware.bin
    %{_datadir}/%{name}/vgabios-virtio.bin
    %{_datadir}/%{name}/vgabios-ramfb.bin
    %{_datadir}/%{name}/vgabios-bochs-display.bin
    %{_datadir}/%{name}/efi-e1000.rom
    %{_datadir}/%{name}/efi-e1000e.rom
    %{_datadir}/%{name}/efi-virtio.rom
    %{_datadir}/%{name}/efi-pcnet.rom
    %{_datadir}/%{name}/efi-rtl8139.rom
    %{_datadir}/%{name}/efi-ne2k_pci.rom
    %{_libdir}/qemu-kvm/hw-display-virtio-vga.so
%endif
    %{_libdir}/%{name}/hw-display-virtio-gpu-gl.so
%ifnarch s390x
    %{_libdir}/%{name}/hw-display-virtio-gpu-pci-gl.so
%endif
%ifarch x86_64 %{power64}
    %{_libdir}/%{name}/hw-display-virtio-vga-gl.so
%endif
    %{_libdir}/%{name}/accel-qtest-%{kvm_target}.so
%ifarch x86_64
    %{_libdir}/%{name}/accel-tcg-%{kvm_target}.so
%endif
%{_libdir}/%{name}/hw-usb-host.so
%{_datadir}/icons/*
%{_datadir}/%{name}/linuxboot_dma.bin
%{_datadir}/%{name}/dump-guest-memory.py*
%{_datadir}/%{name}/trace-events-all
%if 0%{have_kvm_setup}
    %{_prefix}/lib/systemd/kvm-setup
    %{_unitdir}/kvm-setup.service
    %{_presetdir}/85-kvm.preset
%endif
%if 0%{have_memlock_limits}
    %{_sysconfdir}/security/limits.d/95-kvm-memlock.conf
%endif
%{_libexecdir}/virtiofsd

# This is the standard location for vhost-user JSON files defined in the
# vhost-user specification for interoperability with other software. Unlike
# most other paths we use it's "qemu" instead of "qemu-kvm".
%{_datadir}/qemu/vhost-user/50-qemu-virtiofsd.json

%files -n qemu-kvm-core
%defattr(-,root,root)
%{_libexecdir}/qemu-kvm
%{_datadir}/systemtap/tapset/qemu-kvm.stp
%{_datadir}/systemtap/tapset/qemu-kvm-log.stp
%{_datadir}/systemtap/tapset/qemu-kvm-simpletrace.stp
%{_datadir}/%{name}/systemtap/script.d/qemu_kvm.stp
%{_datadir}/%{name}/systemtap/conf.d/qemu_kvm.conf

%{_libdir}/qemu-kvm/hw-display-virtio-gpu.so
%ifarch s390x
    %{_libdir}/qemu-kvm/hw-s390x-virtio-gpu-ccw.so
%else
    %{_libdir}/qemu-kvm/hw-display-virtio-gpu-pci.so
%endif

%files -n qemu-img
%defattr(-,root,root)
%{_bindir}/qemu-img
%{_bindir}/qemu-io
%{_bindir}/qemu-nbd
%{_bindir}/qemu-storage-daemon
%{_mandir}/man1/qemu-img.1*
%{_mandir}/man8/qemu-nbd.8*
%{_mandir}/man1/qemu-storage-daemon.1*
%{_mandir}/man7/qemu-storage-daemon-qmp-ref.7*

%files -n qemu-guest-agent
%defattr(-,root,root,-)
%doc COPYING README.rst
%{_bindir}/qemu-ga
%{_mandir}/man8/qemu-ga.8*
%{_unitdir}/qemu-guest-agent.service
%{_udevrulesdir}/99-qemu-guest-agent.rules
%config(noreplace) %{_sysconfdir}/sysconfig/qemu-ga
%{_sysconfdir}/qemu-ga
%{_sysconfdir}/qemu-kvm/fsfreeze-hook
%{_datadir}/%{name}/qemu-ga
%dir %{_localstatedir}/log/qemu-ga

%files tests
%{testsdir}

%files block-curl
%{_libdir}/qemu-kvm/block-curl.so

%if %{have_gluster}
%files block-gluster
%{_libdir}/qemu-kvm/block-gluster.so
%endif

%files block-iscsi
%{_libdir}/qemu-kvm/block-iscsi.so

%files block-rbd
%{_libdir}/qemu-kvm/block-rbd.so

%files block-ssh
%{_libdir}/qemu-kvm/block-ssh.so

%if 0%{have_spice}
%files ui-spice
    %{_libdir}/qemu-kvm/hw-usb-smartcard.so
    %{_libdir}/qemu-kvm/audio-spice.so
    %{_libdir}/qemu-kvm/ui-spice-core.so
    %{_libdir}/qemu-kvm/chardev-spice.so
%ifarch x86_64
    %{_libdir}/qemu-kvm/hw-display-qxl.so
%endif
%endif

%if 0%{have_opengl}
%files ui-opengl
    %{_libdir}/qemu-kvm/ui-egl-headless.so
    %{_libdir}/qemu-kvm/ui-opengl.so
%endif

%if %{have_usbredir}
%files hw-usbredir
    %{_libdir}/qemu-kvm/hw-usb-redirect.so
%endif


%changelog
* Tue Jan 25 2022 Jon Maloy <jmaloy@redhat.com> - 6.2.0-5
- kvm-acpi-validate-hotplug-selector-on-access.patch [bz#2036580]
- kvm-x86-Add-q35-RHEL-8.6.0-machine-type.patch [bz#2031035]
- Resolves: bz#2036580
  (CVE-2021-4158 virt:rhel/qemu-kvm: QEMU: NULL pointer dereference in pci_write() in hw/acpi/pcihp.c [rhel-8])
- Resolves: bz#2031035
  (Add rhel-8.6.0 machine types for RHEL 8.6 [x86])

* Mon Jan 17 2022 Jon Maloy <jmaloy@redhat.com> - 6.2.0-4
- kvm-hw-arm-virt-Register-iommu-as-a-class-property.patch [bz#2031039]
- kvm-hw-arm-virt-Register-its-as-a-class-property.patch [bz#2031039]
- kvm-hw-arm-virt-Rename-default_bus_bypass_iommu.patch [bz#2031039]
- kvm-hw-arm-virt-Add-8.6-machine-type.patch [bz#2031039]
- kvm-hw-arm-virt-Check-no_tcg_its-and-minor-style-changes.patch [bz#2031039]
- kvm-rhel-machine-types-x86-set-prefer_sockets.patch [bz#2029582]
- Resolves: bz#2031039
  (Add rhel-8.6.0 machine types for RHEL 8.6 [aarch64])
- Resolves: bz#2029582
  ([8.6] machine types: 6.2: Fix prefer_sockets)

* Mon Jan 03 2022 Jon Maloy <jmaloy@redhat.com> - 6.2.0-2
- kvm-redhat-Add-rhel8.6.0-machine-type-for-s390x.patch [bz#2005325]
- kvm-redhat-Define-pseries-rhel8.6.0-machine-type.patch [bz#2031041]
- Resolves: bz#2005325
  (Fix CPU Model for new IBM Z Hardware - qemu part)
- Resolves: bz#2031041
  (Add rhel-8.6.0 machine types for RHEL 8.6 [ppc64le])

* Thu Dec 16 2021 Jon Maloy  <jmaloy@redhat.com> - 6.2.0-1.el8
- Rebase to qemu-kvm 6.2.0
- Resolves bz#2027716

* Mon Nov 22 2021 Jon Maloy <jmaloy@redhat.com> - 6.1.0-5
- kvm-e1000-fix-tx-re-entrancy-problem.patch [bz#1930092]
- kvm-hw-scsi-scsi-disk-MODE_PAGE_ALLS-not-allowed-in-MODE.patch [bz#2020720]
- Resolves: bz#1930092
  (CVE-2021-20257 virt:rhel/qemu-kvm: QEMU: net: e1000: infinite loop while processing transmit descriptors [rhel-8.5.0])
- Resolves: bz#2020720
  (CVE-2021-3930 virt:rhel/qemu-kvm: QEMU: off-by-one error in mode_sense_page() in hw/scsi/scsi-disk.c [rhel-8])

* Thu Oct 21 2021 Jon Maloy <jmaloy@redhat.com> - 6.1.0-4
- kvm-spec-Remove-qemu-kiwi-build.patch [bz#2002694]
- kvm-hw-arm-virt-Add-hw_compat_rhel_8_5-to-8.5-machine-ty.patch [bz#1998947]
- Resolves: bz#2002694
  (remove qemu-kiwi rpm from qemu-kvm sources in rhel-8.6)
- Resolves: bz#1998947
  (Add machine type compatibility update for 6.1 rebase [aarch64])

* Tue Oct 12 2021 Jon Maloy <jmaloy@redhat.com> - 6.1.0-3
- kvm-virtio-net-fix-use-after-unmap-free-for-sg.patch [bz#1999221]
- Resolves: bz#1999221
  (CVE-2021-3748 virt:rhel/qemu-kvm: QEMU: virtio-net: heap use-after-free in virtio_net_receive_rcu [rhel-8])

* Fri Oct 01 2021 Jon Maloy <jmaloy@redhat.com> - 6.1.0-2
- kvm-qxl-fix-pre-save-logic.patch [bz#2002907]
- kvm-redhat-Define-hw_compat_rhel_8_5.patch [bz#1998949]
- kvm-redhat-Update-pseries-rhel8.5.0.patch [bz#1998949]
- kvm-redhat-Add-s390x-machine-type-compatibility-update-f.patch [bz#1998950]
- Resolves: bz#2002907
  (Unexpectedly failed when managedsave the guest which has qxl video device)
- Resolves: bz#1998949
  (Add machine type compatibility update for 6.1 rebase [ppc64le])
- Resolves: bz#1998950
  (Add machine type compatibility update for 6.1 rebase [s390x])

* Wed Aug 25 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-29.el8
- kvm-file-posix-Cap-max_iov-at-IOV_MAX.patch [bz#1994494]
- kvm-migration-Move-yank-outside-qemu_start_incoming_migr.patch [bz#1974366]
- Resolves: bz#1994494
  (VM remains in paused state when trying to write on a resized disk resides on iscsi)
- Resolves: bz#1974366
  (Fail to set migrate incoming for 2nd time after the first time failed)

* Wed Aug 18 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-28.el8
- kvm-iotests-Improve-and-rename-test-291-to-qemu-img-bitm.patch [bz#1946084]
- kvm-qemu-img-Fail-fast-on-convert-bitmaps-with-inconsist.patch [bz#1946084]
- kvm-qemu-img-Add-skip-broken-bitmaps-for-convert-bitmaps.patch [bz#1946084]
- kvm-audio-Never-send-migration-section.patch [bz#1991671]
- Resolves: bz#1946084
  (qemu-img convert --bitmaps fail if a bitmap is inconsistent)
- Resolves: bz#1991671
  (vmstate differs between -audiodev and QEMU_AUDIO_DRV when no sound frontends devs present.)

* Wed Aug 04 2021 Miroslav Rezanina <mrezanin@redhat.com> - 6.0.0-27
- kvm-migration-move-wait-unplug-loop-to-its-own-function.patch [bz#1976852]
- kvm-migration-failover-continue-to-wait-card-unplug-on-e.patch [bz#1976852]
- kvm-aarch64-Add-USB-storage-devices.patch [bz#1974579]
- Resolves: bz#1976852
  ([failover vf migration]  The failover vf will be unregistered  if canceling the migration whose status is "wait-unplug")
- Resolves: bz#1974579
  (It's not possible to start installation from a virtual USB device on aarch64)

* Thu Jul 29 2021 Miroslav Rezanina <mrezanin@redhat.com> - 6.0.0-26
- kvm-acpi-pc-revert-back-to-v5.2-PCI-slot-enumeration.patch [bz#1977798]
- kvm-migration-failover-reset-partially_hotplugged.patch [bz#1787194]
- kvm-hmp-Fix-loadvm-to-resume-the-VM-on-success-instead-o.patch [bz#1959676]
- kvm-migration-Move-bitmap_mutex-out-of-migration_bitmap_.patch [bz#1959729]
- kvm-i386-cpu-Expose-AVX_VNNI-instruction-to-guest.patch [bz#1924822]
- kvm-ratelimit-protect-with-a-mutex.patch [bz#1838221]
- kvm-Update-Linux-headers-to-5.13-rc4.patch [bz#1838221]
- kvm-i386-Add-ratelimit-for-bus-locks-acquired-in-guest.patch [bz#1838221]
- kvm-iothread-generalize-iothread_set_param-iothread_get_.patch [bz#1930286]
- kvm-iothread-add-aio-max-batch-parameter.patch [bz#1930286]
- kvm-linux-aio-limit-the-batch-size-using-aio-max-batch-p.patch [bz#1930286]
- kvm-block-nvme-Fix-VFIO_MAP_DMA-failed-No-space-left-on-.patch [bz#1848881]
- Resolves: bz#1977798
  (RHEL8.5 guest network interface name changed after upgrade to qemu-6.0)
- Resolves: bz#1787194
  (After canceling the migration of a vm with VF which enables failover, using "migrate -d tcp:invalid uri" to re-migrating the vm will cause the VF in vm to be hot-unplug.)
- Resolves: bz#1959676
  (guest status is paused after loadvm on rhel8.5.0)
- Resolves: bz#1959729
  (SAP/3TB VM migration slowness [idle db])
- Resolves: bz#1924822
  ([Intel 8.5 FEAT] qemu-kvm AVX2 VNNI - Fast Train)
- Resolves: bz#1838221
  ([Intel 8.5 FEAT]  qemu-kvm Bus Lock VM Exit - Fast Train)
- Resolves: bz#1930286
  (randread and randrw regression with virtio-blk multi-queue)
- Resolves: bz#1848881
  (nvme:// block driver can exhaust IOMMU DMAs, hanging the VM, possible data loss)

* Tue Jul 20 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-25.el8
- kvm-s390x-cpumodel-add-3931-and-3932.patch [bz#1976171]
- kvm-file-posix-fix-max_iov-for-dev-sg-devices.patch [bz#1943653]
- kvm-scsi-generic-pass-max_segments-via-max_iov-field-in-.patch [bz#1943653]
- kvm-osdep-provide-ROUND_DOWN-macro.patch [bz#1943653]
- kvm-block-backend-align-max_transfer-to-request-alignmen.patch [bz#1943653]
- kvm-block-add-max_hw_transfer-to-BlockLimits.patch [bz#1943653]
- kvm-file-posix-try-BLKSECTGET-on-block-devices-too-do-no.patch [bz#1943653]
- Resolves: bz#1976171
  ([IBM 8.5 FEAT] CPU Model for new IBM Z Hardware - qemu part)
- Resolves: bz#1943653
  (RHV VM pauses due to 'qemu-kvm' getting EINVAL on i/o to a direct lun with scsi passthrough enabled)

* Fri Jul 16 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-24.el8
- kvm-s390x-css-Introduce-an-ESW-struct.patch [bz#1968326]
- kvm-s390x-css-Split-out-the-IRB-sense-data.patch [bz#1968326]
- kvm-s390x-css-Refactor-IRB-construction.patch [bz#1968326]
- kvm-s390x-css-Add-passthrough-IRB.patch [bz#1968326]
- kvm-vhost-user-blk-Fail-gracefully-on-too-large-queue-si.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-blk-Make-sure-to-set-Error-on-realize-fai.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-blk-Don-t-reconnect-during-initialisation.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-blk-Improve-error-reporting-in-realize.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-blk-Get-more-feature-flags-from-vhost-dev.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-virtio-Fail-if-iommu_platform-is-requested-but-unsup.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-blk-Check-that-num-queues-is-supported-by.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- kvm-vhost-user-Fix-backends-without-multiqueue-support.patch [bz#1935014 bz#1935019 bz#1935020 bz#1935031]
- Resolves: bz#1968326
  ([vfio_ccw] I/O error when checking format - dasdfmt requires --force in quick mode when passed through)
- Resolves: bz#1935014
  (qemu crash when attach vhost-user-blk-pci with option queue-size=4096)
- Resolves: bz#1935019
  (qemu guest failed boot when attach vhost-user-blk-pci with option iommu_platform=on)
- Resolves: bz#1935020
  (qemu guest failed boot when attach vhost-user-blk-pci with option packed=on)
- Resolves: bz#1935031
  (qemu guest failed boot when attach vhost-user-blk-pci with unmatched num-queues with qsd)

* Thu Jul 08 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-23.el8
- kvm-Add-mtod_check.patch [bz#1970823 bz#1970842 bz#1970850 bz#1970858]
- kvm-bootp-limit-vendor-specific-area-to-input-packet-mem.patch [bz#1970823 bz#1970842 bz#1970850 bz#1970858]
- kvm-bootp-check-bootp_input-buffer-size.patch [bz#1970823]
- kvm-upd6-check-udp6_input-buffer-size.patch [bz#1970842]
- kvm-tftp-check-tftp_input-buffer-size.patch [bz#1970850]
- kvm-tftp-introduce-a-header-structure.patch [bz#1970823 bz#1970842 bz#1970850 bz#1970858]
- kvm-udp-check-upd_input-buffer-size.patch [bz#1970858]
- kvm-Fix-DHCP-broken-in-libslirp-v4.6.0.patch [bz#1970823 bz#1970842 bz#1970850 bz#1970858]
- kvm-redhat-use-the-standard-vhost-user-JSON-path.patch [bz#1804196]
- Resolves: bz#1970823
  (CVE-2021-3592 virt:av/qemu-kvm: QEMU: slirp: invalid pointer initialization may lead to information disclosure (bootp) [rhel-av-8])
- Resolves: bz#1970842
  (CVE-2021-3593 virt:av/qemu-kvm: QEMU: slirp: invalid pointer initialization may lead to information disclosure (udp6) [rhel-av-8])
- Resolves: bz#1970850
  (CVE-2021-3595 virt:av/qemu-kvm: QEMU: slirp: invalid pointer initialization may lead to information disclosure (tftp) [rhel-av-8])
- Resolves: bz#1970858
  (CVE-2021-3594 virt:av/qemu-kvm: QEMU: slirp: invalid pointer initialization may lead to information disclosure (udp) [rhel-av-8])
- Resolves: bz#1804196
  (inconsistent paths for interop json files)

* Fri Jul 02 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-22.el8
- kvm-redhat-Expose-upstream-machines-pc-4.2-and-pc-2.11.patch [bz#1897923]
- kvm-redhat-Enable-FDC-device-for-upstream-machines-too.patch [bz#1897923]
- kvm-redhat-Add-hw_compat_4_2_extra-and-apply-to-upstream.patch [bz#1897923]
- kvm-ppc-pef.c-initialize-cgs-ready-in-kvmppc_svm_init.patch [bz#1789757]
- kvm-virtio-gpu-handle-partial-maps-properly.patch [bz#1932279]
- kvm-redhat-Fix-unversioned-Obsoletes-warning.patch [bz#1950405 bz#1967330]
- kvm-redhat-Move-qemu-kvm-docs-dependency-to-qemu-kvm.patch [bz#1950405 bz#1967330]
- kvm-redhat-introducting-qemu-kvm-hw-usbredir.patch [bz#1950405 bz#1967330]
- kvm-spapr-Fix-EEH-capability-issue-on-KVM-guest-for-PCI-.patch [bz#1976015]
- Resolves: bz#1897923
  (support Live Migration from Ubuntu 18.04 i440fx to RHEL)
- Resolves: bz#1789757
  ([IBM 8.5 FEAT] Add machine option to enable secure VM support)
- Resolves: bz#1932279
  ([aarch64] qemu core dumped when using smmuv3 and iommu_platform enabling at virtio-gpu-pci)
- Resolves: bz#1950405
  (review qemu-kvm-core dependencies)
- Resolves: bz#1967330
  (Make qemu-kvm use versioned obsoletes for qemu-kvm-ma and qemu-kvm-rhev)
- Resolves: bz#1976015
  (spapr: Fix EEH capability issue on KVM guest for PCI passthru)

* Wed Jun 23 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-21.el8
- kvm-block-backend-add-drained_poll.patch [bz#1960137]
- kvm-nbd-server-Use-drained-block-ops-to-quiesce-the-serv.patch [bz#1960137]
- kvm-disable-CONFIG_USB_STORAGE_BOT.patch [bz#1866133]
- kvm-doc-Fix-some-mistakes-in-the-SEV-documentation.patch [bz#1954750]
- kvm-docs-Add-SEV-ES-documentation-to-amd-memory-encrypti.patch [bz#1954750]
- kvm-docs-interop-firmware.json-Add-SEV-ES-support.patch [bz#1954750]
- Resolves: bz#1960137
  ([incremental backup] qemu-kvm hangs when Rebooting the VM during full backup)
- Resolves: bz#1866133
  (Disable usb-bot device in QEMU (unsupported))
- Resolves: bz#1954750
  (firmware scheme for sev-es)

* Mon Jun 21 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-20.el8
- kvm-x86-Add-x86-rhel8.5-machine-types.patch [bz#1957838]
- kvm-redhat-x86-Enable-kvm-asyncpf-int-by-default.patch [bz#1967603]
- kvm-yank-Unregister-function-when-using-TLS-migration.patch [bz#1964326]
- Resolves: bz#1957838
  (8.5 machine types for x86)
- Resolves: bz#1967603
  (Enable interrupt based asynchronous page fault mechanism by default)
- Resolves: bz#1964326
  (Qemu core dump when do tls migration via tcp protocol)

* Fri Jun 11 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-19.el8
- kvm-pc-bios-s390-ccw-don-t-try-to-read-the-next-block-if.patch [bz#1965626]
- kvm-redhat-Install-the-s390-netboot.img-that-we-ve-built.patch [bz#1966463]
- kvm-sockets-update-SOCKET_ADDRESS_TYPE_FD-listen-2-backl.patch [bz#1967177]
- kvm-target-i386-sev-add-support-to-query-the-attestation.patch [bz#1957022]
- kvm-spapr-Don-t-hijack-current_machine-boot_order.patch [bz#1960119]
- kvm-target-i386-Add-CPU-model-versions-supporting-xsaves.patch [bz#1942914]
- kvm-spapr-Remove-stale-comment-about-power-saving-LPCR-b.patch [bz#1940731]
- kvm-spapr-Set-LPCR-to-current-AIL-mode-when-starting-a-n.patch [bz#1940731]
- Resolves: bz#1965626
  (RHEL8.2 - QEMU BIOS fails to read stage2 loader (kvm))
- Resolves: bz#1966463
  (Rebuild the s390-netboot.img for downstream instead of shipping the upstream image)
- Resolves: bz#1967177
  (QEMU 6.0.0 socket_get_fd() fails with the error "socket_get_fd: too many connections")
- Resolves: bz#1957022
  (SEV: Add support to query the attestation report)
- Resolves: bz#1960119
  ([regression]Failed to reset guest)
- Resolves: bz#1942914
  ([Hyper-V][RHEL8.4]Nested Hyper-V on KVM: On Intel CPU L1 2016 can not start with cpu model Skylake-Server-noTSX-IBRS or Skylake-Client-noTSX-IBRS)
- Resolves: bz#1940731
  ([ppc64le] Hotplug vcpu device hit call trace:[qemu output] KVM: unknown exit, hardware reason 7fff9ce87ed8)

* Tue Jun 01 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-18.el8
- kvm-virtio-net-failover-add-missing-remove_migration_sta.patch [bz#1953045]
- kvm-hw-arm-virt-Add-8.5-machine-type.patch [bz#1957667]
- kvm-hw-arm-virt-Disable-PL011-clock-migration-through-hw.patch [bz#1957667]
- kvm-arm-virt-Register-highmem-and-gic-version-as-class-p.patch [bz#1957667]
- kvm-virtio-blk-Fix-rollback-path-in-virtio_blk_data_plan.patch [bz#1927108]
- kvm-virtio-blk-Configure-all-host-notifiers-in-a-single-.patch [bz#1927108]
- kvm-virtio-scsi-Set-host-notifiers-and-callbacks-separat.patch [bz#1927108]
- kvm-virtio-scsi-Configure-all-host-notifiers-in-a-single.patch [bz#1927108]
- kvm-hw-arm-smmuv3-Another-range-invalidation-fix.patch [bz#1929720]
- Resolves: bz#1953045
  (qemu-kvm NULL pointer de-reference  during migration at migrate_fd_connect ->...-> notifier_list_notify)
- Resolves: bz#1957667
  ([aarch64] Add 8.5 machine type)
- Resolves: bz#1927108
  (It's too slow to load scsi  disk when use 384 vcpus)
- Resolves: bz#1929720
  ([aarch64] Handle vsmmuv3 IOTLB invalidation with non power of 2 size)

* Tue May 25 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-17.el8
- kvm-redhat-s390x-add-rhel-8.5.0-compat-machine.patch [bz#1951476]
- kvm-redhat-add-missing-entries-in-hw_compat_rhel_8_4.patch [bz#1957834]
- kvm-redhat-Define-pseries-rhel8.5.0-machine-type.patch [bz#1957834]
- Resolves: bz#1951476
  ([s390x] RHEL AV 8.5 new machine type for s390x)
- Resolves: bz#1957834
  ([ppc64le] RHEL AV 8.5 new machine type for ppc64le)

* Mon May 03 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 6.0.0-16.el8
- Rebase to qemu-kvm 6.0.0

* Wed Apr 28 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-16.el8
- kvm-virtio-pci-compat-page-aligned-ATS.patch [bz#1942362]
- Resolves: bz#1942362
  (Live migration with iommu from rhel8.3.1 to rhel8.4 fails: qemu-kvm: get_pci_config_device: Bad config data)

* Mon Apr 12 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-15.el8_4
- kvm-block-Simplify-qmp_block_resize-error-paths.patch [bz#1903511]
- kvm-block-Fix-locking-in-qmp_block_resize.patch [bz#1903511]
- kvm-block-Fix-deadlock-in-bdrv_co_yield_to_drain.patch [bz#1903511]
- Resolves: bz#1903511
  (no response on  QMP command 'block_resize')

* Sat Mar 20 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-14.el8
- kvm-vhost-user-blk-fix-blkcfg-num_queues-endianness.patch [bz#1937004]
- kvm-block-export-fix-blk_size-double-byteswap.patch [bz#1937004]
- kvm-block-export-use-VIRTIO_BLK_SECTOR_BITS.patch [bz#1937004]
- kvm-block-export-fix-vhost-user-blk-export-sector-number.patch [bz#1937004]
- kvm-block-export-port-virtio-blk-discard-write-zeroes-in.patch [bz#1937004]
- kvm-block-export-port-virtio-blk-read-write-range-check.patch [bz#1937004]
- kvm-spec-ui-spice-sub-package.patch [bz#1936373]
- kvm-spec-ui-opengl-sub-package.patch [bz#1936373]
- Resolves: bz#1937004
  (vhost-user-blk server endianness and input validation fixes)
- Resolves: bz#1936373
  (move spice & opengl modules to rpm subpackages)

* Tue Mar 16 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-13.el8
- kvm-i386-acpi-restore-device-paths-for-pre-5.1-vms.patch [bz#1934158]
- Resolves: bz#1934158
  (Windows guest looses network connectivity when NIC was configured with static IP)

* Mon Mar 15 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-12.el8
- kvm-scsi-disk-move-scsi_handle_rw_error-earlier.patch [bz#1927530]
- kvm-scsi-disk-do-not-complete-requests-early-for-rerror-.patch [bz#1927530]
- kvm-scsi-introduce-scsi_sense_from_errno.patch [bz#1927530]
- kvm-scsi-disk-pass-SCSI-status-to-scsi_handle_rw_error.patch [bz#1927530]
- kvm-scsi-disk-pass-guest-recoverable-errors-through-even.patch [bz#1927530]
- kvm-hw-intc-arm_gic-Fix-interrupt-ID-in-GICD_SGIR-regist.patch [bz#1936948]
- Resolves: bz#1927530
  (RHEL8 Hypervisor - OVIRT  - Issues seen on a virtualization guest with direct passthrough LUNS  pausing when a host gets a Thin threshold warning)
- Resolves: bz#1936948
  (CVE-2021-20221 virt:av/qemu-kvm: qemu: out-of-bound heap buffer access via an interrupt ID field [rhel-av-8.4.0])

* Mon Mar 08 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-11.el8
- kvm-qxl-set-qxl.ssd.dcl.con-on-secondary-devices.patch [bz#1932190]
- kvm-qxl-also-notify-the-rendering-is-done-when-skipping-.patch [bz#1932190]
- kvm-virtiofsd-Save-error-code-early-at-the-failure-calls.patch [bz#1935071]
- kvm-virtiofs-drop-remapped-security.capability-xattr-as-.patch [bz#1935071]
- Resolves: bz#1932190
  (Timeout when dump the screen from 2nd VGA)
- Resolves: bz#1935071
  (CVE-2021-20263 virt:8.4/qemu-kvm: QEMU: virtiofsd: 'security.capabilities' is not dropped with xattrmap option [rhel-av-8])

* Wed Mar 03 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-10.el8
- kvm-migration-dirty-bitmap-Use-struct-for-alias-map-inne.patch [bz#1930757]
- kvm-migration-dirty-bitmap-Allow-control-of-bitmap-persi.patch [bz#1930757]
- kvm-qemu-iotests-300-Add-test-case-for-modifying-persist.patch [bz#1930757]
- kvm-failover-fix-indentantion.patch [bz#1819991]
- kvm-failover-Use-always-atomics-for-primary_should_be_hi.patch [bz#1819991]
- kvm-failover-primary-bus-is-only-used-once-and-where-it-.patch [bz#1819991]
- kvm-failover-Remove-unused-parameter.patch [bz#1819991]
- kvm-failover-Remove-external-partially_hotplugged-proper.patch [bz#1819991]
- kvm-failover-qdev_device_add-returns-err-or-dev-set.patch [bz#1819991]
- kvm-failover-Rename-bool-to-failover_primary_hidden.patch [bz#1819991]
- kvm-failover-g_strcmp0-knows-how-to-handle-NULL.patch [bz#1819991]
- kvm-failover-Remove-primary_device_opts.patch [bz#1819991]
- kvm-failover-remove-standby_id-variable.patch [bz#1819991]
- kvm-failover-Remove-primary_device_dict.patch [bz#1819991]
- kvm-failover-Remove-memory-leak.patch [bz#1819991]
- kvm-failover-simplify-virtio_net_find_primary.patch [bz#1819991]
- kvm-failover-should_be_hidden-should-take-a-bool.patch [bz#1819991]
- kvm-failover-Rename-function-to-hide_device.patch [bz#1819991]
- kvm-failover-virtio_net_connect_failover_devices-does-no.patch [bz#1819991]
- kvm-failover-Rename-to-failover_find_primary_device.patch [bz#1819991]
- kvm-failover-simplify-qdev_device_add-failover-case.patch [bz#1819991]
- kvm-failover-simplify-qdev_device_add.patch [bz#1819991]
- kvm-failover-make-sure-that-id-always-exist.patch [bz#1819991]
- kvm-failover-remove-failover_find_primary_device-error-p.patch [bz#1819991]
- kvm-failover-split-failover_find_primary_device_id.patch [bz#1819991]
- kvm-failover-We-don-t-need-to-cache-primary_device_id-an.patch [bz#1819991]
- kvm-failover-Caller-of-this-two-functions-already-have-p.patch [bz#1819991]
- kvm-failover-simplify-failover_unplug_primary.patch [bz#1819991]
- kvm-failover-Remove-primary_dev-member.patch [bz#1819991]
- kvm-virtio-net-add-missing-object_unref.patch [bz#1819991]
- kvm-x86-cpu-Populate-SVM-CPUID-feature-bits.patch [bz#1926785]
- kvm-i386-Add-the-support-for-AMD-EPYC-3rd-generation-pro.patch [bz#1926785]
- Resolves: bz#1930757
  (Allow control of block-dirty-bitmap persistence via 'block-bitmap-mapping')
- Resolves: bz#1819991
  (Hostdev type interface with net failover enabled exists in domain xml and doesn't reattach to host after hot-unplug)
- Resolves: bz#1926785
  ([RFE] AMD Milan - Add KVM/support for EPYC-Milan CPU Model - Fast Train)

* Mon Mar 01 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-9.el8
- kvm-docs-generate-qemu-storage-daemon-qmp-ref-7-man-page.patch [bz#1901323]
- kvm-docs-add-qemu-storage-daemon-1-man-page.patch [bz#1901323]
- kvm-docs-Add-qemu-storage-daemon-1-manpage-to-meson.buil.patch [bz#1901323]
- kvm-qemu-storage-daemon-Enable-object-add.patch [bz#1901323]
- kvm-spec-Package-qemu-storage-daemon.patch [bz#1901323]
- kvm-default-configs-Enable-vhost-user-blk.patch [bz#1930033]
- kvm-qemu-nbd-Use-SOMAXCONN-for-socket-listen-backlog.patch [bz#1925345]
- kvm-pcie-don-t-set-link-state-active-if-the-slot-is-empt.patch [bz#1917654]
- Resolves: bz#1901323
  (QSD (QEMU Storage Daemon): basic support - TechPreview)
- Resolves: bz#1930033
  (enable vhost-user-blk device)
- Resolves: bz#1925345
  (qemu-nbd needs larger backlog for Unix socket listen())
- Resolves: bz#1917654
  ([failover vf migration][RHEL84 vm] After start a vm with a failover vf + a failover virtio net device, the failvoer vf do not exist in the vm)

* Fri Feb 19 2021 Eduardo Lima (Etrunko) <elima@redhat.com> - 5.2.0-8.el8
- kvm-block-nbd-only-detach-existing-iochannel-from-aio_co.patch [bz#1887883]
- kvm-block-nbd-only-enter-connection-coroutine-if-it-s-pr.patch [bz#1887883]
- kvm-nbd-make-nbd_read-return-EIO-on-error.patch [bz#1887883]
- kvm-virtio-move-use-disabled-flag-property-to-hw_compat_.patch [bz#1907255]
- kvm-virtiofsd-extract-lo_do_open-from-lo_open.patch [bz#1920740]
- kvm-virtiofsd-optionally-return-inode-pointer-from-lo_do.patch [bz#1920740]
- kvm-virtiofsd-prevent-opening-of-special-files-CVE-2020-.patch [bz#1920740]
- kvm-spapr-Adjust-firmware-path-of-PCI-devices.patch [bz#1920941]
- kvm-pci-reject-too-large-ROMs.patch [bz#1917830]
- kvm-pci-add-romsize-property.patch [bz#1917830]
- kvm-redhat-Add-some-devices-for-exporting-upstream-machi.patch [bz#1917826]
- kvm-vhost-Check-for-valid-vdev-in-vhost_backend_handle_i.patch [bz#1880299]
- Resolves: bz#1887883
  (qemu blocks client progress with various NBD actions)
- Resolves: bz#1907255
  (Migrate failed with vhost-vsock-pci from RHEL-AV 8.3.1 to RHEL-AV 8.2.1)
- Resolves: bz#1920740
  (CVE-2020-35517 virt:8.4/qemu-kvm: QEMU: virtiofsd: potential privileged host device access from guest [rhel-av-8.4.0])
- Resolves: bz#1920941
  ([ppc64le] [AV]--disk cdimage.iso,bus=usb fails to boot)
- Resolves: bz#1917830
  (Add romsize property to qemu-kvm)
- Resolves: bz#1917826
  (Add extra device support to qemu-kvm, but not to rhel machine types)
- Resolves: bz#1880299
  (vhost-user mq connection fails to restart after kill host testpmd which acts as vhost-user client)

* Fri Feb 12 2021 Eduardo Lima (Etrunko) <elima@redhat.com> - 5.2.0-7.el8
- kvm-virtio-Add-corresponding-memory_listener_unregister-.patch [bz#1903521]
- kvm-block-Honor-blk_set_aio_context-context-requirements.patch [bz#1918966 bz#1918968]
- kvm-nbd-server-Quiesce-coroutines-on-context-switch.patch [bz#1918966 bz#1918968]
- kvm-block-Avoid-processing-BDS-twice-in-bdrv_set_aio_con.patch [bz#1918966 bz#1918968]
- kvm-storage-daemon-Call-bdrv_close_all-on-exit.patch [bz#1918966 bz#1918968]
- kvm-block-move-blk_exp_close_all-to-qemu_cleanup.patch [bz#1918966 bz#1918968]
- Resolves: bz#1903521
  (hot unplug vhost-user cause qemu crash: qemu-kvm: ../softmmu/memory.c:2818: do_address_space_destroy: Assertion `QTAILQ_EMPTY(&as->listeners)' failed.)
- Resolves: bz#1918966
  ([incremental_backup] qemu aborts if guest reboot during backup when using virtio-blk: "aio_co_schedule: Co-routine was already scheduled in 'aio_co_schedule'")
- Resolves: bz#1918968
  ([incremental_backup] qemu deadlock after poweroff in guest during backup in nbd_export_close_all())

* Tue Feb 09 2021 Eduardo Lima (Etrunko) <elima@redhat.com> - 5.2.0-6.el8
- kvm-scsi-fix-device-removal-race-vs-IO-restart-callback-.patch [bz#1854811]
- kvm-tracetool-also-strip-l-and-ll-from-systemtap-format-.patch [bz#1907264]
- kvm-redhat-moving-all-documentation-files-to-qemu-kvm-do.patch [bz#1881170 bz#1924766]
- kvm-hw-arm-smmuv3-Fix-addr_mask-for-range-based-invalida.patch [bz#1834152]
- kvm-redhat-makes-qemu-respect-system-s-crypto-profile.patch [bz#1902219]
- kvm-vhost-Unbreak-SMMU-and-virtio-iommu-on-dev-iotlb-sup.patch [bz#1925028]
- kvm-docs-set-CONFDIR-when-running-sphinx.patch [bz#1902537]
- Resolves: bz#1854811
  (scsi-bus.c: use-after-free due to race between device unplug and I/O operation causes guest crash)
- Resolves: bz#1907264
  (systemtap: invalid or missing conversion specifier at the trace event vhost_vdpa_set_log_base)
- Resolves: bz#1881170
  (split documentation from the qemu-kvm-core package to its own subpackage)
- Resolves: bz#1924766
  (split documentation from the qemu-kvm-core package to its own subpackage [av-8.4.0])
- Resolves: bz#1834152
  ([aarch64] QEMU SMMUv3 device: Support range invalidation)
- Resolves: bz#1902219
  (QEMU doesn't honour system crypto policies)
- Resolves: bz#1925028
  (vsmmuv3/vhost and virtio-iommu/vhost regression)
- Resolves: bz#1902537
  (The default fsfreeze-hook path from man page and qemu-ga --help command are different)

* Tue Feb 02 2021 Eduardo Lima (Etrunko) <elima@redhat.com> - 5.2.0-5.el8
- kvm-spapr-Allow-memory-unplug-to-always-succeed.patch [bz#1914069]
- kvm-spapr-Improve-handling-of-memory-unplug-with-old-gue.patch [bz#1914069]
- kvm-x86-cpu-Add-AVX512_FP16-cpu-feature.patch [bz#1838738]
- kvm-q35-Increase-max_cpus-to-710-on-pc-q35-rhel8-machine.patch [bz#1904268]
- kvm-config-enable-VFIO_CCW.patch [bz#1922170]
- Resolves: bz#1914069
  ([ppc64le] have this fix for rhel8.4 av (spapr: Allow memory unplug to always succeed))
- Resolves: bz#1838738
  ([Intel 8.4 FEAT] qemu-kvm Sapphire Rapids (SPR) New Instructions (NIs) - Fast Train)
- Resolves: bz#1904268
  ([RFE] [HPEMC] qemu-kvm: support up to 710 VCPUs)
- Resolves: bz#1922170
  (Enable vfio-ccw in AV)

* Wed Jan 27 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-4.el8
- kvm-Drop-bogus-IPv6-messages.patch [bz#1918061]
- Resolves: bz#1918061
  (CVE-2020-10756 virt:rhel/qemu-kvm: QEMU: slirp: networking out-of-bounds read information disclosure vulnerability [rhel-av-8])

* Mon Jan 18 2021 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-3.el8
- kvm-block-nvme-Implement-fake-truncate-coroutine.patch [bz#1848834]
- kvm-spec-find-system-python-via-meson.patch [bz#1899619]
- kvm-build-system-use-b_staticpic-false.patch [bz#1899619]
- kvm-spapr-Fix-buffer-overflow-in-spapr_numa_associativit.patch [bz#1908693]
- kvm-usb-hcd-xhci-pci-Fixup-capabilities-ordering-again.patch [bz#1912846]
- kvm-qga-commands-posix-Send-CCW-address-on-s390x-with-th.patch [bz#1755075]
- kvm-AArch64-machine-types-cleanup.patch [bz#1895276]
- kvm-hw-arm-virt-Add-8.4-Machine-type.patch [bz#1895276]
- kvm-udev-kvm-check-remove-the-exceeded-subscription-limi.patch [bz#1914463]
- kvm-memory-Rename-memory_region_notify_one-to-memory_reg.patch [bz#1845758]
- kvm-memory-Add-IOMMUTLBEvent.patch [bz#1845758]
- kvm-memory-Add-IOMMU_NOTIFIER_DEVIOTLB_UNMAP-IOMMUTLBNot.patch [bz#1845758]
- kvm-intel_iommu-Skip-page-walking-on-device-iotlb-invali.patch [bz#1845758]
- kvm-memory-Skip-bad-range-assertion-if-notifier-is-DEVIO.patch [bz#1845758]
- kvm-RHEL-Switch-pvpanic-test-to-q35.patch [bz#1885555]
- kvm-8.4-x86-machine-type.patch [bz#1885555]
- kvm-memory-clamp-cached-translation-in-case-it-points-to.patch [bz#1904392]
- Resolves: bz#1848834
  (Failed to create luks format image on NVMe device)
- Resolves: bz#1899619
  (QEMU 5.2 is built with PIC objects instead of PIE)
- Resolves: bz#1908693
  ([ppc64le]boot up a guest with 128 numa nodes ,qemu got coredump)
- Resolves: bz#1912846
  (qemu-kvm: Failed to load xhci:parent_obj during migration)
- Resolves: bz#1755075
  ([qemu-guest-agent] fsinfo doesn't return disk info on s390x)
- Resolves: bz#1895276
  (Machine types update for aarch64 for QEMU 5.2.0)
- Resolves: bz#1914463
  (Remove KVM guest count and limit info message)
- Resolves: bz#1845758
  (qemu core dumped: qemu-kvm: /builddir/build/BUILD/qemu-4.2.0/memory.c:1928: memory_region_notify_one: Assertion `entry->iova >= notifier->start && entry_end <= notifier->end' failed.)
- Resolves: bz#1885555
  (8.4 machine types for x86)
- Resolves: bz#1904392
  (CVE-2020-27821 virt:8.4/qemu-kvm: QEMU: heap buffer overflow in msix_table_mmio_write() in hw/pci/msix.c [rhel-av-8])

* Tue Dec 15 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.2.0-2.el8
- kvm-redhat-Define-hw_compat_8_3.patch [bz#1893935]
- kvm-redhat-Add-spapr_machine_rhel_default_class_options.patch [bz#1893935]
- kvm-redhat-Define-pseries-rhel8.4.0-machine-type.patch [bz#1893935]
- kvm-redhat-s390x-add-rhel-8.4.0-compat-machine.patch [bz#1836282]
- Resolves: bz#1836282
  (New machine type for qemu-kvm on s390x in RHEL-AV)
- Resolves: bz#1893935
  (New machine type on RHEL-AV 8.4 for ppc64le)

* Wed Dec 09 2020 Miroslav Rezanina <mrezanin@redhat.com> - 5.2.0-1.el8
- Rebase to QEMU 5.2.0 [bz#1905933]
- Resolves: bz#1905933
  (Rebase qemu-kvm to version 5.2.0)

* Tue Dec 01 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-16.el8
- kvm-redhat-introduces-disable_everything-macro-into-the-.patch [bz#1884611]
- kvm-redhat-scripts-extract_build_cmd.py-Avoid-listing-em.patch [bz#1884611]
- kvm-redhat-Removing-unecessary-configurations.patch [bz#1884611]
- kvm-redhat-Fixing-rh-local-build.patch [bz#1884611]
- kvm-redhat-allow-Makefile-rh-prep-builddep-to-fail.patch [bz#1884611]
- kvm-redhat-adding-rh-rpm-target.patch [bz#1884611]
- kvm-redhat-move-shareable-files-from-qemu-kvm-core-to-qe.patch [bz#1884611]
- kvm-redhat-Add-qemu-kiwi-subpackage.patch [bz#1884611]
- Resolves: bz#1884611
  (Build kata-specific version of qemu)

* Mon Nov 16 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-15.el8
- kvm-redhat-add-un-pre-install-systemd-hooks-for-qemu-ga.patch [bz#1882719]
- kvm-rcu-Implement-drain_call_rcu.patch [bz#1812399 bz#1866707]
- kvm-libqtest-Rename-qmp_assert_error_class-to-qmp_expect.patch [bz#1812399 bz#1866707]
- kvm-qtest-rename-qtest_qmp_receive-to-qtest_qmp_receive_.patch [bz#1812399 bz#1866707]
- kvm-qtest-Reintroduce-qtest_qmp_receive-with-QMP-event-b.patch [bz#1812399 bz#1866707]
- kvm-qtest-remove-qtest_qmp_receive_success.patch [bz#1812399 bz#1866707]
- kvm-device-plug-test-use-qtest_qmp-to-send-the-device_de.patch [bz#1812399 bz#1866707]
- kvm-qtest-switch-users-back-to-qtest_qmp_receive.patch [bz#1812399 bz#1866707]
- kvm-qtest-check-that-drives-are-really-appearing-and-dis.patch [bz#1812399 bz#1866707]
- kvm-qemu-iotests-qtest-rewrite-test-067-as-a-qtest.patch [bz#1812399 bz#1866707]
- kvm-qdev-add-check-if-address-free-callback-for-buses.patch [bz#1812399 bz#1866707]
- kvm-scsi-scsi_bus-switch-search-direction-in-scsi_device.patch [bz#1812399 bz#1866707]
- kvm-device_core-use-drain_call_rcu-in-in-qmp_device_add.patch [bz#1812399 bz#1866707]
- kvm-device-core-use-RCU-for-list-of-children-of-a-bus.patch [bz#1812399 bz#1866707]
- kvm-scsi-switch-to-bus-check_address.patch [bz#1812399 bz#1866707]
- kvm-device-core-use-atomic_set-on-.realized-property.patch [bz#1812399 bz#1866707]
- kvm-scsi-scsi-bus-scsi_device_find-don-t-return-unrealiz.patch [bz#1812399]
- kvm-scsi-scsi_bus-Add-scsi_device_get.patch [bz#1812399 bz#1866707]
- kvm-virtio-scsi-use-scsi_device_get.patch [bz#1812399 bz#1866707]
- kvm-scsi-scsi_bus-fix-races-in-REPORT-LUNS.patch [bz#1812399 bz#1866707]
- kvm-tests-migration-fix-memleak-in-wait_command-wait_com.patch [bz#1812399 bz#1866707]
- kvm-libqtest-fix-the-order-of-buffered-events.patch [bz#1812399 bz#1866707]
- kvm-libqtest-fix-memory-leak-in-the-qtest_qmp_event_ref.patch [bz#1812399 bz#1866707]
- kvm-iotests-add-filter_qmp_virtio_scsi-function.patch [bz#1812399 bz#1866707]
- kvm-iotests-rewrite-iotest-240-in-python.patch [bz#1812399 bz#1866707]
- Resolves: bz#1812399
  (Qemu crash when detach disk with cache="none" discard="ignore" io="native")
- Resolves: bz#1866707
  (qemu-kvm is crashing with error "scsi_target_emulate_report_luns: Assertion `i == n + 8' failed")
- Resolves: bz#1882719
  (qemu-ga service still active and can work after qemu-guest-agent been removed)

* Tue Oct 13 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-14.el8_3
- kvm-virtiofsd-avoid-proc-self-fd-tempdir.patch [bz#1884276]
- Resolves: bz#1884276
  (Pod with kata-runtime won't start, QEMU: "vhost_user_dev init failed, Operation not permitted" [mkdtemp failing in sandboxing])

* Thu Oct 08 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-13.el8_3
- kvm-x86-lpc9-let-firmware-negotiate-CPU-hotplug-with-SMI.patch [bz#1846886]
- kvm-x86-cpuhp-prevent-guest-crash-on-CPU-hotplug-when-br.patch [bz#1846886]
- kvm-x86-cpuhp-refuse-cpu-hot-unplug-request-earlier-if-n.patch [bz#1846886]
- Resolves: bz#1846886
  (Guest hit soft lockup or reboots if hotplug vcpu under ovmf)

* Mon Oct 05 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-12.el8_3
- kvm-virtio-skip-legacy-support-check-on-machine-types-le.patch [bz#1868449]
- kvm-vhost-vsock-pci-force-virtio-version-1.patch [bz#1868449]
- kvm-vhost-user-vsock-pci-force-virtio-version-1.patch [bz#1868449]
- kvm-vhost-vsock-ccw-force-virtio-version-1.patch [bz#1868449]
- Resolves: bz#1868449
  (vhost_vsock error: device is modern-only, use disable-legacy=on)

* Mon Oct 05 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-11.el8_3
- kvm-migration-increase-max-bandwidth-to-128-MiB-s-1-Gib-.patch [bz#1874004]
- kvm-redhat-Make-all-generated-so-files-executable-not-on.patch [bz#1876635]
- Resolves: bz#1874004
  (Live migration performance is poor during guest installation process on power host)
- Resolves: bz#1876635
  (VM fails to start with a passthrough smartcard)

* Mon Sep 28 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-10.el8
- kvm-qemu-img-Support-bitmap-merge-into-backing-image.patch [bz#1877209]
- Resolves: bz#1877209
  ('qemu-img bitmaps --merge' failed when trying to merge top volume bitmap to base volume bitmap)

* Mon Sep 21 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-9.el8
- kvm-hw-nvram-fw_cfg-fix-FWCfgDataGeneratorClass-get_data.patch [bz#1688978]
- Resolves: bz#1688978
  (RFE: forward host preferences for cipher suites and CA certs to guest firmware)

* Thu Sep 17 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-8.el8
- kvm-redhat-link-etc-qemu-ga-fsfreeze-hook-to-etc-qemu-kv.patch [bz#1738820]
- kvm-seccomp-fix-killing-of-whole-process-instead-of-thre.patch [bz#1752376]
- kvm-Revert-Drop-bogus-IPv6-messages.patch [bz#1867075]
- kvm-block-rbd-add-namespace-to-qemu_rbd_strong_runtime_o.patch [bz#1821528]
- Resolves: bz#1738820
  ('-F' option of qemu-ga command  cause the guest-fsfreeze-freeze command doesn't work)
- Resolves: bz#1752376
  (qemu use SCMP_ACT_TRAP even SCMP_ACT_KILL_PROCESS is available)
- Resolves: bz#1821528
  (missing namespace attribute when access the rbd image with namespace)
- Resolves: bz#1867075
  (CVE-2020-10756 virt:8.3/qemu-kvm: QEMU: slirp: networking out-of-bounds read information disclosure vulnerability [rhel-av-8])

* Tue Sep 15 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-7.el8
- kvm-target-ppc-Add-experimental-option-for-enabling-secu.patch [bz#1789757 bz#1870384]
- kvm-target-arm-Move-start-powered-off-property-to-generi.patch [bz#1849483]
- kvm-target-arm-Move-setting-of-CPU-halted-state-to-gener.patch [bz#1849483]
- kvm-ppc-spapr-Use-start-powered-off-CPUState-property.patch [bz#1849483]
- Resolves: bz#1789757
  ([IBM 8.4 FEAT] Add machine option to enable secure VM support)
- Resolves: bz#1849483
  (Failed to boot up guest when hotplugging vcpus on bios stage)
- Resolves: bz#1870384
  ([IBM 8.3 FEAT] Add interim/unsupported machine option to enable secure VM support for testing purposes)

* Thu Sep 10 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-6.el8
- kvm-spec-Move-qemu-pr-helper-back-to-usr-bin.patch [bz#1869635]
- kvm-Bump-required-libusbx-version.patch [bz#1856591]
- Resolves: bz#1856591
  (libusbx isn't updated with qemu-kvm)
- Resolves: bz#1869635
  ('/usr/bin/qemu-pr-helper' is not a suitable pr helper: No such file or directory)

* Tue Sep 08 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-5.el8
- kvm-Revert-i386-Fix-pkg_id-offset-for-EPYC-cpu-models.patch [bz#1873417]
- kvm-Revert-target-i386-Enable-new-apic-id-encoding-for-E.patch [bz#1873417]
- kvm-Revert-hw-i386-Move-arch_id-decode-inside-x86_cpus_i.patch [bz#1873417]
- kvm-Revert-i386-Introduce-use_epyc_apic_id_encoding-in-X.patch [bz#1873417]
- kvm-Revert-hw-i386-Introduce-apicid-functions-inside-X86.patch [bz#1873417]
- kvm-Revert-target-i386-Cleanup-and-use-the-EPYC-mode-top.patch [bz#1873417]
- kvm-Revert-hw-386-Add-EPYC-mode-topology-decoding-functi.patch [bz#1873417]
- kvm-nvram-Exit-QEMU-if-NVRAM-cannot-contain-all-prom-env.patch [bz#1867739]
- kvm-usb-fix-setup_len-init-CVE-2020-14364.patch [bz#1869715]
- kvm-Remove-explicit-glusterfs-api-dependency.patch [bz#1872853]
- kvm-disable-virgl.patch [bz#1831271]
- Resolves: bz#1831271
  (Drop virgil acceleration support and remove virglrenderer dependency)
- Resolves: bz#1867739
  (-prom-env does not validate input)
- Resolves: bz#1869715
  (CVE-2020-14364 qemu-kvm: QEMU: usb: out-of-bounds r/w access issue while processing usb packets [rhel-av-8.3.0])
- Resolves: bz#1872853
  (move the glusterfs dependency out of qemu-kvm-core to the glusterfs module)
- Resolves: bz#1873417
  (AMD/NUMA topology - revert 5.1 changes)

* Thu Aug 27 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-4.el8
- kvm-Drop-bogus-IPv6-messages.patch [bz#1867075]
- kvm-machine-types-numa-set-numa_mem_supported-on-old-mac.patch [bz#1849707]
- kvm-machine_types-numa-compatibility-for-auto_enable_num.patch [bz#1849707]
- kvm-migration-Add-block-bitmap-mapping-parameter.patch [bz#1790492]
- kvm-iotests.py-Let-wait_migration-return-on-failure.patch [bz#1790492]
- kvm-iotests-Test-node-bitmap-aliases-during-migration.patch [bz#1790492]
- Resolves: bz#1790492
  ('dirty-bitmaps' migration capability should allow configuring target nodenames)
- Resolves: bz#1849707
  (8.3 machine types for x86 - 5.1 update)
- Resolves: bz#1867075
  (CVE-2020-10756 virt:8.3/qemu-kvm: QEMU: slirp: networking out-of-bounds read information disclosure vulnerability [rhel-av-8])

* Wed Aug 19 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-3.el8
- kvm-redhat-Update-hw_compat_8_2.patch [bz#1843348]
- kvm-redhat-update-pseries-rhel8.2.0-machine-type.patch [bz#1843348]
- kvm-Disable-TPM-passthrough-backend-on-ARM.patch [bz#1801242]
- kvm-Require-libfdt-1.6.0.patch [bz#1867847]
- Resolves: bz#1801242
  ([aarch64] vTPM support in machvirt)
- Resolves: bz#1843348
  (8.3 machine types for POWER)
- Resolves: bz#1867847
  ([ppc] virt module 7629: /usr/libexec/qemu-kvm: undefined symbol: fdt_check_full, version LIBFDT_1.2)

* Wed Aug 12 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-2.el8
- kvm-redhat-define-hw_compat_8_2.patch [bz#1853265]
- Resolves: bz#1853265
  (Forward and backward migration from rhel-av-8.3.0(qemu-kvm-5.0.0) to rhel-av-8.2.1(qemu-kvm-4.2.0) failed with "qemu-kvm: error while loading state for instance 0x0 of device 'spapr'")

* Wed Aug 12 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-1.el8
- Quick changelog fix to reflect the current fixes:
- Resolve: bz#1781911
- Resolve: bz#1841529
- Resolve: bz#1842902
- Resolve: bz#1818843
- Resolve: bz#1819292
- Resolve: bz#1801242

* Wed Aug 12 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 5.1.0-0.el8
- Rebase to 5.1.0
- Resolves: bz#1809650

* Tue Jul 07 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-29.el8
- kvm-virtio-net-fix-removal-of-failover-device.patch [bz#1820120]
- Resolves: bz#1820120
  (After hotunplugging the vitrio device and netdev, hotunpluging the failover VF will cause qemu core dump)

* Sun Jun 28 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-28.el8
- kvm-virtio-blk-Refactor-the-code-that-processes-queued-r.patch [bz#1812765]
- kvm-virtio-blk-On-restart-process-queued-requests-in-the.patch [bz#1812765]
- kvm-Fix-use-afte-free-in-ip_reass-CVE-2020-1983.patch [bz#1838082]
- Resolves: bz#1812765
  (qemu with iothreads enabled crashes on resume after enospc pause for disk extension)
- Resolves: bz#1838082
  (CVE-2020-1983 virt:8.2/qemu-kvm: QEMU: slirp: use-after-free in ip_reass() function in ip_input.c [rhel-av-8])

* Thu Jun 18 2020 Eduardo Lima (Etrunko) <elima@redhat.com> - 4.2.0-27.el8
- kvm-hw-pci-pcie-Move-hot-plug-capability-check-to-pre_pl.patch [bz#1820531]
- kvm-spec-Fix-python-shenigans-for-tests.patch [bz#1845779]
- kvm-target-i386-Add-ARCH_CAPABILITIES-related-bits-into-.patch [bz#1840342]
- Resolves: bz#1820531
  (qmp command query-pci get wrong result after hotplug device under hotplug=off controller)
- Resolves: bz#1840342
  ([Intel 8.2.1 Bug] qemu-kvm Add ARCH_CAPABILITIES to Icelake-Server cpu model - Fast Train)
- Resolves: bz#1845779
  (Install 'qemu-kvm-tests' failed as nothing provides /usr/libexec/platform-python3 - virt module 6972)

* Wed Jun 17 2020 Eduardo Lima (Etrunko) <elima@redhat.com> - 4.2.0-26.el8
- kvm-nbd-server-Avoid-long-error-message-assertions-CVE-2.patch [bz#1845384]
- kvm-block-Call-attention-to-truncation-of-long-NBD-expor.patch [bz#1845384]
- Resolves: bz#1845384
  (CVE-2020-10761 virt:8.2/qemu-kvm: QEMU: nbd: reachable assertion failure in nbd_negotiate_send_rep_verr via remote client [rhel-av-8])

* Tue Jun 09 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-25.el8
- kvm-enable-ramfb.patch [bz#1841068]
- kvm-block-Add-flags-to-BlockDriver.bdrv_co_truncate.patch [bz#1780574]
- kvm-block-Add-flags-to-bdrv-_co-_truncate.patch [bz#1780574]
- kvm-block-backend-Add-flags-to-blk_truncate.patch [bz#1780574]
- kvm-qcow2-Support-BDRV_REQ_ZERO_WRITE-for-truncate.patch [bz#1780574]
- kvm-raw-format-Support-BDRV_REQ_ZERO_WRITE-for-truncate.patch [bz#1780574]
- kvm-file-posix-Support-BDRV_REQ_ZERO_WRITE-for-truncate.patch [bz#1780574]
- kvm-block-truncate-Don-t-make-backing-file-data-visible.patch [bz#1780574]
- kvm-iotests-Add-qemu_io_log.patch [bz#1780574]
- kvm-iotests-Filter-testfiles-out-in-filter_img_info.patch [bz#1780574]
- kvm-iotests-Test-committing-to-short-backing-file.patch [bz#1780574]
- kvm-qcow2-Forward-ZERO_WRITE-flag-for-full-preallocation.patch [bz#1780574]
- kvm-i386-Add-MSR-feature-bit-for-MDS-NO.patch [bz#1769912]
- kvm-i386-Add-macro-for-stibp.patch [bz#1769912]
- kvm-target-i386-Add-new-bit-definitions-of-MSR_IA32_ARCH.patch [bz#1769912]
- kvm-i386-Add-new-CPU-model-Cooperlake.patch [bz#1769912]
- kvm-target-i386-Add-missed-features-to-Cooperlake-CPU-mo.patch [bz#1769912]
- Resolves: bz#1769912
  ([Intel 8.2.1 Feature] introduce Cooper Lake cpu model - qemu-kvm Fast Train)
- Resolves: bz#1780574
  (Data corruption with resizing short overlay over longer backing files)
- Resolves: bz#1841068
  (RFE: please support the "ramfb" display device model)

* Mon Jun 08 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-24.el8
- kvm-target-i386-set-the-CPUID-level-to-0x14-on-old-machi.patch [bz#1513681]
- kvm-block-curl-HTTP-header-fields-allow-whitespace-aroun.patch [bz#1841038]
- kvm-block-curl-HTTP-header-field-names-are-case-insensit.patch [bz#1841038]
- kvm-MAINTAINERS-fix-qcow2-bitmap.c-under-Dirty-Bitmaps-h.patch [bz#1779893 bz#1779904]
- kvm-iotests-Let-_make_test_img-parse-its-parameters.patch [bz#1779893 bz#1779904]
- kvm-qemu_img-add-cvtnum_full-to-print-error-reports.patch [bz#1779893 bz#1779904]
- kvm-block-Make-it-easier-to-learn-which-BDS-support-bitm.patch [bz#1779893 bz#1779904]
- kvm-blockdev-Promote-several-bitmap-functions-to-non-sta.patch [bz#1779893 bz#1779904]
- kvm-blockdev-Split-off-basic-bitmap-operations-for-qemu-.patch [bz#1779893 bz#1779904]
- kvm-qemu-img-Add-bitmap-sub-command.patch [bz#1779893 bz#1779904]
- kvm-iotests-Fix-test-178.patch [bz#1779893 bz#1779904]
- kvm-qcow2-Expose-bitmaps-size-during-measure.patch [bz#1779893 bz#1779904]
- kvm-qemu-img-Factor-out-code-for-merging-bitmaps.patch [bz#1779893 bz#1779904]
- kvm-qemu-img-Add-convert-bitmaps-option.patch [bz#1779893 bz#1779904]
- kvm-iotests-Add-test-291-to-for-qemu-img-bitmap-coverage.patch [bz#1779893 bz#1779904]
- kvm-iotests-Add-more-skip_if_unsupported-statements-to-t.patch [bz#1778593]
- kvm-iotests-don-t-use-format-for-drive_add.patch [bz#1778593]
- kvm-iotests-055-refactor-compressed-backup-to-vmdk.patch [bz#1778593]
- kvm-iotests-055-skip-vmdk-target-tests-if-vmdk-is-not-wh.patch [bz#1778593]
- kvm-backup-Improve-error-for-bdrv_getlength-failure.patch [bz#1778593]
- kvm-backup-Make-sure-that-source-and-target-size-match.patch [bz#1778593]
- kvm-iotests-Backup-with-different-source-target-size.patch [bz#1778593]
- kvm-iotests-109-Don-t-mirror-with-mismatched-size.patch [bz#1778593]
- kvm-iotests-229-Use-blkdebug-to-inject-an-error.patch [bz#1778593]
- kvm-mirror-Make-sure-that-source-and-target-size-match.patch [bz#1778593]
- kvm-iotests-Mirror-with-different-source-target-size.patch [bz#1778593]
- Resolves: bz#1513681
  ([Intel 8.2.1 Feat] qemu-kvm PT VMX -- Fast Train)
- Resolves: bz#1778593
  (Qemu coredump when backup to a existing small size image)
- Resolves: bz#1779893
  (RFE: Copy bitmaps with qemu-img convert)
- Resolves: bz#1779904
  (RFE: ability to estimate bitmap space utilization for qcow2)
- Resolves: bz#1841038
  (qemu-img: /var/tmp/v2vovl56bced.qcow2: CURL: Error opening file: Server does not support 'range' (byte ranges) with HTTP/2 server in VMware ESXi 7)

* Thu Jun 04 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-23.el8
- kvm-target-arm-Fix-PAuth-sbox-functions.patch [bz#1813940]
- kvm-Don-t-leak-memory-when-reallocation-fails.patch [bz#1749737]
- kvm-Replace-remaining-malloc-free-user-with-glib.patch [bz#1749737]
- kvm-Revert-RHEL-disable-hostmem-memfd.patch [bz#1839030]
- kvm-block-introducing-bdrv_co_delete_file-interface.patch [bz#1827630]
- kvm-block.c-adding-bdrv_co_delete_file.patch [bz#1827630]
- kvm-crypto.c-cleanup-created-file-when-block_crypto_co_c.patch [bz#1827630]
- Resolves: bz#1749737
  (CVE-2019-15890 qemu-kvm: QEMU: Slirp: use-after-free during packet reassembly [rhel-av-8])
- Resolves: bz#1813940
  (CVE-2020-10702 virt:8.1/qemu-kvm: qemu: weak signature generation in Pointer Authentication support for ARM [rhel-av-8])
- Resolves: bz#1827630
  (volume creation leaving uncleaned stuff behind on error (vol-clone/libvirt/qemu-kvm))
- Resolves: bz#1839030
  (RFE: enable the "memfd" memory backend)

* Mon May 25 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-22.el8
- kvm-block-always-fill-entire-LUKS-header-space-with-zero.patch [bz#1775462]
- kvm-numa-remove-not-needed-check.patch [bz#1600217]
- kvm-numa-properly-check-if-numa-is-supported.patch [bz#1600217]
- kvm-numa-Extend-CLI-to-provide-initiator-information-for.patch [bz#1600217]
- kvm-numa-Extend-CLI-to-provide-memory-latency-and-bandwi.patch [bz#1600217]
- kvm-numa-Extend-CLI-to-provide-memory-side-cache-informa.patch [bz#1600217]
- kvm-hmat-acpi-Build-Memory-Proximity-Domain-Attributes-S.patch [bz#1600217]
- kvm-hmat-acpi-Build-System-Locality-Latency-and-Bandwidt.patch [bz#1600217]
- kvm-hmat-acpi-Build-Memory-Side-Cache-Information-Struct.patch [bz#1600217]
- kvm-tests-numa-Add-case-for-QMP-build-HMAT.patch [bz#1600217]
- kvm-tests-bios-tables-test-add-test-cases-for-ACPI-HMAT.patch [bz#1600217]
- kvm-ACPI-add-expected-files-for-HMAT-tests-acpihmat.patch [bz#1600217]
- Resolves: bz#1600217
  ([Intel 8.2.1 FEAT] KVM ACPI HMAT support - qemu-kvm  Fast Train)
- Resolves: bz#1775462
  (Creating luks-inside-qcow2 images with cluster_size=2k/4k will get a corrupted image)

* Mon May 11 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-21.el8
- kvm-hw-pci-pcie-Forbid-hot-plug-if-it-s-disabled-on-the-.patch [bz#1820531]
- kvm-hw-pci-pcie-Replace-PCI_DEVICE-casts-with-existing-v.patch [bz#1820531]
- kvm-tools-virtiofsd-passthrough_ll-Fix-double-close.patch [bz#1817445]
- kvm-virtiofsd-add-rlimit-nofile-NUM-option.patch [bz#1817445]
- kvm-virtiofsd-stay-below-fs.file-max-sysctl-value-CVE-20.patch [bz#1817445]
- kvm-virtiofsd-jail-lo-proc_self_fd.patch [bz#1817445]
- kvm-virtiofsd-Show-submounts.patch [bz#1817445]
- kvm-virtiofsd-only-retain-file-system-capabilities.patch [bz#1817445]
- kvm-virtiofsd-drop-all-capabilities-in-the-wait-parent-p.patch [bz#1817445]
- Resolves: bz#1817445
  (CVE-2020-10717 virt:8.2/qemu-kvm: QEMU: virtiofsd: guest may open maximum file descriptor to cause DoS [rhel-av-8])
- Resolves: bz#1820531
  (qmp command query-pci get wrong result after hotplug device under hotplug=off controller)

* Fri May 01 2020 Jon Maloy <jmaloy@redhat.com> - 4.2.0-20.el8
- kvm-pcie_root_port-Add-hotplug-disabling-option.patch [bz#1790899]
- kvm-compat-disable-edid-for-virtio-gpu-ccw.patch [bz#1816793]
- Resolves: bz#1790899
  ([RFE] QEMU devices should have the option to enable/disable hotplug/unplug)
- Resolves: bz#1816793
  ('edid' compat handling missing for virtio-gpu-ccw)

* Tue Apr 14 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-19.el8_2
- kvm-target-i386-do-not-set-unsupported-VMX-secondary-exe.patch [bz#1822682]
- Resolves: bz#1822682
  (QEMU-4.2 fails to start a VM on Azure)

* Thu Apr 09 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-18.el8_2
- kvm-job-take-each-job-s-lock-individually-in-job_txn_app.patch [bz#1817621]
- kvm-replication-assert-we-own-context-before-job_cancel_.patch [bz#1817621]
- kvm-backup-don-t-acquire-aio_context-in-backup_clean.patch [bz#1817621]
- kvm-block-backend-Reorder-flush-pdiscard-function-defini.patch [bz#1817621]
- kvm-block-Increase-BB.in_flight-for-coroutine-and-sync-i.patch [bz#1817621]
- kvm-block-Fix-blk-in_flight-during-blk_wait_while_draine.patch [bz#1817621]
- Resolves: bz#1817621
  (Crash and deadlock with block jobs when using io-threads)

* Mon Mar 30 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-17.el8
- kvm-block-pass-BlockDriver-reference-to-the-.bdrv_co_cre.patch [bz#1816007]
- kvm-block-trickle-down-the-fallback-image-creation-funct.patch [bz#1816007]
- kvm-Revert-mirror-Don-t-let-an-operation-wait-for-itself.patch [bz#1794692]
- kvm-mirror-Wait-only-for-in-flight-operations.patch [bz#1794692]
- Resolves: bz#1794692
  (Mirror block job stops making progress)
- Resolves: bz#1816007
  (qemu-img convert failed to convert with block device as target)

* Tue Mar 24 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-16.el8
- kvm-migration-Rate-limit-inside-host-pages.patch [bz#1814336]
- kvm-build-sys-do-not-make-qemu-ga-link-with-pixman.patch [bz#1811670]
- Resolves: bz#1811670
  (Unneeded qemu-guest-agent dependency on pixman)
- Resolves: bz#1814336
  ([POWER9] QEMU migration-test triggers a kernel warning)

* Tue Mar 17 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-15.el8
- kvm-block-nbd-Fix-hang-in-.bdrv_close.patch [bz#1640894]
- kvm-block-Generic-file-creation-fallback.patch [bz#1640894]
- kvm-file-posix-Drop-hdev_co_create_opts.patch [bz#1640894]
- kvm-iscsi-Drop-iscsi_co_create_opts.patch [bz#1640894]
- kvm-iotests-Add-test-for-image-creation-fallback.patch [bz#1640894]
- kvm-block-Fix-leak-in-bdrv_create_file_fallback.patch [bz#1640894]
- kvm-iotests-Use-complete_and_wait-in-155.patch [bz#1790482 bz#1805143]
- kvm-block-Introduce-bdrv_reopen_commit_post-step.patch [bz#1790482 bz#1805143]
- kvm-block-qcow2-Move-bitmap-reopen-into-bdrv_reopen_comm.patch [bz#1790482 bz#1805143]
- kvm-iotests-Refactor-blockdev-reopen-test-for-iothreads.patch [bz#1790482 bz#1805143]
- kvm-block-bdrv_reopen-with-backing-file-in-different-Aio.patch [bz#1790482 bz#1805143]
- kvm-block-Versioned-x-blockdev-reopen-API-with-feature-f.patch [bz#1790482 bz#1805143]
- kvm-block-Make-bdrv_get_cumulative_perm-public.patch [bz#1790482 bz#1805143]
- kvm-block-Relax-restrictions-for-blockdev-snapshot.patch [bz#1790482 bz#1805143]
- kvm-iotests-Fix-run_job-with-use_log-False.patch [bz#1790482 bz#1805143]
- kvm-iotests-Test-mirror-with-temporarily-disabled-target.patch [bz#1790482 bz#1805143]
- kvm-block-Fix-cross-AioContext-blockdev-snapshot.patch [bz#1790482 bz#1805143]
- kvm-iotests-Add-iothread-cases-to-155.patch [bz#1790482 bz#1805143]
- kvm-qapi-Add-allow-write-only-overlay-feature-for-blockd.patch [bz#1790482 bz#1805143]
- kvm-exec-rom_reset-Free-rom-data-during-inmigrate-skip.patch [bz#1809380]
- Resolves: bz#1640894
  (Fix generic file creation fallback for qemu-img nvme:// image creation support)
- Resolves: bz#1790482
  (bitmaps in backing images can't be modified)
- Resolves: bz#1805143
  (allow late/lazy opening of backing chain for shallow blockdev-mirror)
- Resolves: bz#1809380
  (guest hang during reboot process after migration from RHEl7.8 to RHEL8.2.0.)

* Wed Mar 11 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-14.el8
- kvm-hw-smbios-set-new-default-SMBIOS-fields-for-Windows-.patch [bz#1782529]
- kvm-migration-multifd-clean-pages-after-filling-packet.patch [bz#1738451]
- kvm-migration-Make-sure-that-we-don-t-call-write-in-case.patch [bz#1738451]
- kvm-migration-multifd-fix-nullptr-access-in-terminating-.patch [bz#1738451]
- kvm-migration-multifd-fix-destroyed-mutex-access-in-term.patch [bz#1738451]
- kvm-multifd-Make-sure-that-we-don-t-do-any-IO-after-an-e.patch [bz#1738451]
- kvm-qemu-file-Don-t-do-IO-after-shutdown.patch [bz#1738451]
- kvm-migration-Don-t-send-data-if-we-have-stopped.patch [bz#1738451]
- kvm-migration-Create-migration_is_running.patch [bz#1738451]
- kvm-migration-multifd-fix-nullptr-access-in-multifd_send.patch [bz#1738451]
- kvm-migration-Maybe-VM-is-paused-when-migration-is-cance.patch [bz#1738451]
- kvm-virtiofsd-Remove-fuse_req_getgroups.patch [bz#1797064]
- kvm-virtiofsd-fv_create_listen_socket-error-path-socket-.patch [bz#1797064]
- kvm-virtiofsd-load_capng-missing-unlock.patch [bz#1797064]
- kvm-virtiofsd-do_read-missing-NULL-check.patch [bz#1797064]
- kvm-tools-virtiofsd-fuse_lowlevel-Fix-fuse_out_header-er.patch [bz#1797064]
- kvm-virtiofsd-passthrough_ll-cleanup-getxattr-listxattr.patch [bz#1797064]
- kvm-virtiofsd-Fix-xattr-operations.patch [bz#1797064]
- Resolves: bz#1738451
  (qemu on src host core dump after set multifd-channels and do migration twice (first migration execute migrate_cancel))
- Resolves: bz#1782529
  (Windows Update Enablement with default smbios strings in qemu)
- Resolves: bz#1797064
  (virtiofsd: Fixes)

* Sat Feb 29 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-13.el8
- kvm-target-i386-kvm-initialize-feature-MSRs-very-early.patch [bz#1791648]
- kvm-target-i386-add-a-ucode-rev-property.patch [bz#1791648]
- kvm-target-i386-kvm-initialize-microcode-revision-from-K.patch [bz#1791648]
- kvm-target-i386-fix-TCG-UCODE_REV-access.patch [bz#1791648]
- kvm-target-i386-check-for-availability-of-MSR_IA32_UCODE.patch [bz#1791648]
- kvm-target-i386-enable-monitor-and-ucode-revision-with-c.patch [bz#1791648]
- kvm-qcow2-Fix-qcow2_alloc_cluster_abort-for-external-dat.patch [bz#1703907]
- kvm-mirror-Store-MirrorOp.co-for-debuggability.patch [bz#1794692]
- kvm-mirror-Don-t-let-an-operation-wait-for-itself.patch [bz#1794692]
- Resolves: bz#1703907
  ([upstream]QEMU coredump when converting to qcow2: external data file images on block devices with copy_offloading)
- Resolves: bz#1791648
  ([RFE] Passthrough host CPU microcode version to KVM guest if using CPU passthrough)
- Resolves: bz#1794692
  (Mirror block job stops making progress)

* Mon Feb 24 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-12.el8
- kvm-vhost-user-gpu-Drop-trailing-json-comma.patch [bz#1805334]
- Resolves: bz#1805334
  (vhost-user/50-qemu-gpu.json is not valid JSON)

* Sun Feb 23 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-11.el8
- kvm-spapr-Enable-DD2.3-accelerated-count-cache-flush-in-.patch [bz#1796240]
- kvm-util-add-slirp_fmt-helpers.patch [bz#1798994]
- kvm-tcp_emu-fix-unsafe-snprintf-usages.patch [bz#1798994]
- kvm-virtio-add-ability-to-delete-vq-through-a-pointer.patch [bz#1791590]
- kvm-virtio-make-virtio_delete_queue-idempotent.patch [bz#1791590]
- kvm-virtio-reset-region-cache-when-on-queue-deletion.patch [bz#1791590]
- kvm-virtio-net-delete-also-control-queue-when-TX-RX-dele.patch [bz#1791590]
- Resolves: bz#1791590
  ([Q35] No "DEVICE_DELETED" event in qmp after unplug virtio-net-pci device)
- Resolves: bz#1796240
  (Enable hw accelerated cache-count-flush by default for POWER9 DD2.3 cpus)
- Resolves: bz#1798994
  (CVE-2020-8608 qemu-kvm: QEMU: Slirp: potential OOB access due to unsafe snprintf() usages [rhel-av-8.2.0])

* Fri Feb 14 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-10.el8
- kvm-i386-Resolve-CPU-models-to-v1-by-default.patch [bz#1779078 bz#1787291 bz#1779078 bz#1779078]
- kvm-iotests-Support-job-complete-in-run_job.patch [bz#1781637]
- kvm-iotests-Create-VM.blockdev_create.patch [bz#1781637]
- kvm-block-Activate-recursively-even-for-already-active-n.patch [bz#1781637]
- kvm-hmp-Allow-using-qdev-ID-for-qemu-io-command.patch [bz#1781637]
- kvm-iotests-Test-external-snapshot-with-VM-state.patch [bz#1781637]
- kvm-iotests.py-Let-wait_migration-wait-even-more.patch [bz#1781637]
- kvm-blockdev-fix-coding-style-issues-in-drive_backup_pre.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-blockdev-unify-qmp_drive_backup-and-drive-backup-tra.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-blockdev-unify-qmp_blockdev_backup-and-blockdev-back.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-blockdev-honor-bdrv_try_set_aio_context-context-requ.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-backup-top-Begin-drain-earlier.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-block-backup-top-Don-t-acquire-context-while-droppin.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-blockdev-Acquire-AioContext-on-dirty-bitmap-function.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-blockdev-Return-bs-to-the-proper-context-on-snapshot.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-iotests-Test-handling-of-AioContexts-with-some-block.patch [bz#1745606 bz#1746217 bz#1773517 bz#1779036 bz#1782111 bz#1782175 bz#1783965]
- kvm-target-arm-monitor-query-cpu-model-expansion-crashed.patch [bz#1801320]
- kvm-docs-arm-cpu-features-Make-kvm-no-adjvtime-comment-c.patch [bz#1801320]
- Resolves: bz#1745606
  (Qemu hang when do incremental live backup in transaction mode without bitmap)
- Resolves: bz#1746217
  (Src qemu hang when do storage vm migration during guest installation)
- Resolves: bz#1773517
  (Src qemu hang when do storage vm migration with dataplane enable)
- Resolves: bz#1779036
  (Qemu coredump when do snapshot in transaction mode with one snapshot path not exist)
- Resolves: bz#1779078
  (RHVH 4.4: Failed to run VM on 4.3/4.4 engine (Exit message: the CPU is incompatible with host CPU: Host CPU does not provide required features: hle, rtm))
- Resolves: bz#1781637
  (qemu crashed when do mem and disk snapshot)
- Resolves: bz#1782111
  (Qemu hang when do full backup on multi-disks with one job's 'job-id' missed in transaction mode(data plane enable))
- Resolves: bz#1782175
  (Qemu core dump when add persistent bitmap(data plane enable))
- Resolves: bz#1783965
  (Qemu core dump when do backup with sync: bitmap and no bitmap provided)
- Resolves: bz#1787291
  (RHVH 4.4: Failed to run VM on 4.3/4.4 engine (Exit message: the CPU is incompatible with host CPU: Host CPU does not provide required features: hle, rtm) [rhel-8.1.0.z])
- Resolves: bz#1801320
  (aarch64: backport query-cpu-model-expansion and adjvtime document fixes)

* Mon Feb 10 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-9.el8
- kvm-ppc-Deassert-the-external-interrupt-pin-in-KVM-on-re.patch [bz#1776638]
- kvm-xics-Don-t-deassert-outputs.patch [bz#1776638]
- kvm-ppc-Don-t-use-CPUPPCState-irq_input_state-with-moder.patch [bz#1776638]
- kvm-trace-update-qemu-trace-stap-to-Python-3.patch [bz#1787395]
- kvm-redhat-Remove-redundant-fix-for-qemu-trace-stap.patch [bz#1787395]
- kvm-iscsi-Cap-block-count-from-GET-LBA-STATUS-CVE-2020-1.patch [bz#1794503]
- kvm-tpm-ppi-page-align-PPI-RAM.patch [bz#1787444]
- kvm-target-arm-kvm-trivial-Clean-up-header-documentation.patch [bz#1647366]
- kvm-target-arm-kvm64-kvm64-cpus-have-timer-registers.patch [bz#1647366]
- kvm-tests-arm-cpu-features-Check-feature-default-values.patch [bz#1647366]
- kvm-target-arm-kvm-Implement-virtual-time-adjustment.patch [bz#1647366]
- kvm-target-arm-cpu-Add-the-kvm-no-adjvtime-CPU-property.patch [bz#1647366]
- kvm-migration-Define-VMSTATE_INSTANCE_ID_ANY.patch [bz#1529231]
- kvm-migration-Change-SaveStateEntry.instance_id-into-uin.patch [bz#1529231]
- kvm-apic-Use-32bit-APIC-ID-for-migration-instance-ID.patch [bz#1529231]
- Resolves: bz#1529231
  ([q35] VM hangs after migration with 200 vCPUs)
- Resolves: bz#1647366
  (aarch64: Add support for the kvm-no-adjvtime ARM CPU feature)
- Resolves: bz#1776638
  (Guest failed to boot up after system_reset  20 times)
- Resolves: bz#1787395
  (qemu-trace-stap list : TypeError: startswith first arg must be bytes or a tuple of bytes, not str)
- Resolves: bz#1787444
  (Broken postcopy migration with vTPM device)
- Resolves: bz#1794503
  (CVE-2020-1711 qemu-kvm: QEMU: block: iscsi: OOB heap access via an unexpected response of iSCSI Server [rhel-av-8.2.0])

* Fri Jan 31 2020 Miroslav Rezanina <mrezanin@redhat.com> - 4.2.0-8.el8
- kvm-target-arm-arch_dump-Add-SVE-notes.patch [bz#1725084]
- kvm-vhost-Add-names-to-section-rounded-warning.patch [bz#1779041]
- kvm-vhost-Only-align-sections-for-vhost-user.patch [bz#1779041]
- kvm-vhost-coding-style-fix.patch [bz#1779041]
- kvm-virtio-fs-fix-MSI-X-nvectors-calculation.patch [bz#1694164]
- kvm-vhost-user-fs-remove-vhostfd-property.patch [bz#1694164]
- kvm-build-rename-CONFIG_LIBCAP-to-CONFIG_LIBCAP_NG.patch [bz#1694164]
- kvm-virtiofsd-Pull-in-upstream-headers.patch [bz#1694164]
- kvm-virtiofsd-Pull-in-kernel-s-fuse.h.patch [bz#1694164]
- kvm-virtiofsd-Add-auxiliary-.c-s.patch [bz#1694164]
- kvm-virtiofsd-Add-fuse_lowlevel.c.patch [bz#1694164]
- kvm-virtiofsd-Add-passthrough_ll.patch [bz#1694164]
- kvm-virtiofsd-Trim-down-imported-files.patch [bz#1694164]
- kvm-virtiofsd-Format-imported-files-to-qemu-style.patch [bz#1694164]
- kvm-virtiofsd-remove-mountpoint-dummy-argument.patch [bz#1694164]
- kvm-virtiofsd-remove-unused-notify-reply-support.patch [bz#1694164]
- kvm-virtiofsd-Remove-unused-enum-fuse_buf_copy_flags.patch [bz#1694164]
- kvm-virtiofsd-Fix-fuse_daemonize-ignored-return-values.patch [bz#1694164]
- kvm-virtiofsd-Fix-common-header-and-define-for-QEMU-buil.patch [bz#1694164]
- kvm-virtiofsd-Trim-out-compatibility-code.patch [bz#1694164]
- kvm-vitriofsd-passthrough_ll-fix-fallocate-ifdefs.patch [bz#1694164]
- kvm-virtiofsd-Make-fsync-work-even-if-only-inode-is-pass.patch [bz#1694164]
- kvm-virtiofsd-Add-options-for-virtio.patch [bz#1694164]
- kvm-virtiofsd-add-o-source-PATH-to-help-output.patch [bz#1694164]
- kvm-virtiofsd-Open-vhost-connection-instead-of-mounting.patch [bz#1694164]
- kvm-virtiofsd-Start-wiring-up-vhost-user.patch [bz#1694164]
- kvm-virtiofsd-Add-main-virtio-loop.patch [bz#1694164]
- kvm-virtiofsd-get-set-features-callbacks.patch [bz#1694164]
- kvm-virtiofsd-Start-queue-threads.patch [bz#1694164]
- kvm-virtiofsd-Poll-kick_fd-for-queue.patch [bz#1694164]
- kvm-virtiofsd-Start-reading-commands-from-queue.patch [bz#1694164]
- kvm-virtiofsd-Send-replies-to-messages.patch [bz#1694164]
- kvm-virtiofsd-Keep-track-of-replies.patch [bz#1694164]
- kvm-virtiofsd-Add-Makefile-wiring-for-virtiofsd-contrib.patch [bz#1694164]
- kvm-virtiofsd-Fast-path-for-virtio-read.patch [bz#1694164]
- kvm-virtiofsd-add-fd-FDNUM-fd-passing-option.patch [bz#1694164]
- kvm-virtiofsd-make-f-foreground-the-default.patch [bz#1694164]
- kvm-virtiofsd-add-vhost-user.json-file.patch [bz#1694164]
- kvm-virtiofsd-add-print-capabilities-option.patch [bz#1694164]
- kvm-virtiofs-Add-maintainers-entry.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-create-new-files-in-caller-.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-lo_map-for-ino-fh-indir.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-ino_map-to-hide-lo_inod.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-dirp_map-to-hide-lo_dir.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-fd_map-to-hide-file-des.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-fallback-for-racy-ops.patch [bz#1694164]
- kvm-virtiofsd-validate-path-components.patch [bz#1694164]
- kvm-virtiofsd-Plumb-fuse_bufvec-through-to-do_write_buf.patch [bz#1694164]
- kvm-virtiofsd-Pass-write-iov-s-all-the-way-through.patch [bz#1694164]
- kvm-virtiofsd-add-fuse_mbuf_iter-API.patch [bz#1694164]
- kvm-virtiofsd-validate-input-buffer-sizes-in-do_write_bu.patch [bz#1694164]
- kvm-virtiofsd-check-input-buffer-size-in-fuse_lowlevel.c.patch [bz#1694164]
- kvm-virtiofsd-prevent-.-escape-in-lo_do_lookup.patch [bz#1694164]
- kvm-virtiofsd-prevent-.-escape-in-lo_do_readdir.patch [bz#1694164]
- kvm-virtiofsd-use-proc-self-fd-O_PATH-file-descriptor.patch [bz#1694164]
- kvm-virtiofsd-sandbox-mount-namespace.patch [bz#1694164]
- kvm-virtiofsd-move-to-an-empty-network-namespace.patch [bz#1694164]
- kvm-virtiofsd-move-to-a-new-pid-namespace.patch [bz#1694164]
- kvm-virtiofsd-add-seccomp-whitelist.patch [bz#1694164]
- kvm-virtiofsd-Parse-flag-FUSE_WRITE_KILL_PRIV.patch [bz#1694164]
- kvm-virtiofsd-cap-ng-helpers.patch [bz#1694164]
- kvm-virtiofsd-Drop-CAP_FSETID-if-client-asked-for-it.patch [bz#1694164]
- kvm-virtiofsd-set-maximum-RLIMIT_NOFILE-limit.patch [bz#1694164]
- kvm-virtiofsd-fix-libfuse-information-leaks.patch [bz#1694164]
- kvm-virtiofsd-add-syslog-command-line-option.patch [bz#1694164]
- kvm-virtiofsd-print-log-only-when-priority-is-high-enoug.patch [bz#1694164]
- kvm-virtiofsd-Add-ID-to-the-log-with-FUSE_LOG_DEBUG-leve.patch [bz#1694164]
- kvm-virtiofsd-Add-timestamp-to-the-log-with-FUSE_LOG_DEB.patch [bz#1694164]
- kvm-virtiofsd-Handle-reinit.patch [bz#1694164]
- kvm-virtiofsd-Handle-hard-reboot.patch [bz#1694164]
- kvm-virtiofsd-Kill-threads-when-queues-are-stopped.patch [bz#1694164]
- kvm-vhost-user-Print-unexpected-slave-message-types.patch [bz#1694164]
- kvm-contrib-libvhost-user-Protect-slave-fd-with-mutex.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-add-renameat2-support.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-disable-readdirplus-on-cach.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-control-readdirplus.patch [bz#1694164]
- kvm-virtiofsd-rename-unref_inode-to-unref_inode_lolocked.patch [bz#1694164]
- kvm-virtiofsd-fail-when-parent-inode-isn-t-known-in-lo_d.patch [bz#1694164]
- kvm-virtiofsd-extract-root-inode-init-into-setup_root.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-clean-up-cache-related-opti.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-use-hashtable.patch [bz#1694164]
- kvm-virtiofsd-Clean-up-inodes-on-destroy.patch [bz#1694164]
- kvm-virtiofsd-support-nanosecond-resolution-for-file-tim.patch [bz#1694164]
- kvm-virtiofsd-fix-error-handling-in-main.patch [bz#1694164]
- kvm-virtiofsd-cleanup-allocated-resource-in-se.patch [bz#1694164]
- kvm-virtiofsd-fix-memory-leak-on-lo.source.patch [bz#1694164]
- kvm-virtiofsd-add-helper-for-lo_data-cleanup.patch [bz#1694164]
- kvm-virtiofsd-Prevent-multiply-running-with-same-vhost_u.patch [bz#1694164]
- kvm-virtiofsd-enable-PARALLEL_DIROPS-during-INIT.patch [bz#1694164]
- kvm-virtiofsd-fix-incorrect-error-handling-in-lo_do_look.patch [bz#1694164]
- kvm-Virtiofsd-fix-memory-leak-on-fuse-queueinfo.patch [bz#1694164]
- kvm-virtiofsd-Support-remote-posix-locks.patch [bz#1694164]
- kvm-virtiofsd-use-fuse_lowlevel_is_virtio-in-fuse_sessio.patch [bz#1694164]
- kvm-virtiofsd-prevent-fv_queue_thread-vs-virtio_loop-rac.patch [bz#1694164]
- kvm-virtiofsd-make-lo_release-atomic.patch [bz#1694164]
- kvm-virtiofsd-prevent-races-with-lo_dirp_put.patch [bz#1694164]
- kvm-virtiofsd-rename-inode-refcount-to-inode-nlookup.patch [bz#1694164]
- kvm-libvhost-user-Fix-some-memtable-remap-cases.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-fix-refcounting-on-remove-r.patch [bz#1694164]
- kvm-virtiofsd-introduce-inode-refcount-to-prevent-use-af.patch [bz#1694164]
- kvm-virtiofsd-do-not-always-set-FUSE_FLOCK_LOCKS.patch [bz#1694164]
- kvm-virtiofsd-convert-more-fprintf-and-perror-to-use-fus.patch [bz#1694164]
- kvm-virtiofsd-Reset-O_DIRECT-flag-during-file-open.patch [bz#1694164]
- kvm-virtiofsd-Fix-data-corruption-with-O_APPEND-write-in.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-Use-cache_readdir-for-direc.patch [bz#1694164]
- kvm-virtiofsd-add-definition-of-fuse_buf_writev.patch [bz#1694164]
- kvm-virtiofsd-use-fuse_buf_writev-to-replace-fuse_buf_wr.patch [bz#1694164]
- kvm-virtiofsd-process-requests-in-a-thread-pool.patch [bz#1694164]
- kvm-virtiofsd-prevent-FUSE_INIT-FUSE_DESTROY-races.patch [bz#1694164]
- kvm-virtiofsd-fix-lo_destroy-resource-leaks.patch [bz#1694164]
- kvm-virtiofsd-add-thread-pool-size-NUM-option.patch [bz#1694164]
- kvm-virtiofsd-Convert-lo_destroy-to-take-the-lo-mutex-lo.patch [bz#1694164]
- kvm-virtiofsd-passthrough_ll-Pass-errno-to-fuse_reply_er.patch [bz#1694164]
- kvm-virtiofsd-stop-all-queue-threads-on-exit-in-virtio_l.patch [bz#1694164]
- kvm-virtiofsd-add-some-options-to-the-help-message.patch [bz#1694164]
- kvm-redhat-ship-virtiofsd-vhost-user-device-backend.patch [bz#1694164]
- Resolves: bz#1694164
  (virtio-fs: host<->guest shared file system (qemu))
- Resolves: bz#1725084
  (aarch64: support dumping SVE registers)
- Resolves: bz#1779041
  (netkvm: no connectivity Windows guest with q35 + hugepages + vhost + hv_synic)

* Tue Jan 21 2020 Miroslav Rezanina <mrezanin@redhat.com> - 4.2.0-7.el8
- kvm-tcp_emu-Fix-oob-access.patch [bz#1791568]
- kvm-slirp-use-correct-size-while-emulating-IRC-commands.patch [bz#1791568]
- kvm-slirp-use-correct-size-while-emulating-commands.patch [bz#1791568]
- kvm-RHEL-hw-i386-disable-nested-PERF_GLOBAL_CTRL-MSR-sup.patch [bz#1559846]
- Resolves: bz#1559846
  (Nested KVM: limit VMX features according to CPU models - Fast Train)
- Resolves: bz#1791568
  (CVE-2020-7039 qemu-kvm: QEMU: slirp: OOB buffer access while emulating tcp protocols in tcp_emu() [rhel-av-8.2.0])

* Wed Jan 15 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-6.el8
- kvm-spapr-Don-t-trigger-a-CAS-reboot-for-XICS-XIVE-mode-.patch [bz#1733893]
- kvm-vfio-pci-Don-t-remove-irqchip-notifier-if-not-regist.patch [bz#1782678]
- kvm-virtio-don-t-enable-notifications-during-polling.patch [bz#1789301]
- kvm-usbredir-Prevent-recursion-in-usbredir_write.patch [bz#1790844]
- kvm-xhci-recheck-slot-status.patch [bz#1790844]
- Resolves: bz#1733893
  (Boot a guest with "-prom-env 'auto-boot?=false'", SLOF failed to enter the boot entry after input "boot" followed by "0 > " on VNC)
- Resolves: bz#1782678
  (qemu core dump after hot-unplugging the   XXV710/XL710 PF)
- Resolves: bz#1789301
  (virtio-blk/scsi: fix notification suppression during AioContext polling)
- Resolves: bz#1790844
  (USB related fixes)

* Tue Jan 07 2020 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-5.el8
- kvm-i386-Remove-cpu64-rhel6-CPU-model.patch [bz#1741345]
- kvm-Reallocate-dirty_bmap-when-we-change-a-slot.patch [bz#1772774]
- Resolves: bz#1741345
  (Remove the "cpu64-rhel6" CPU from qemu-kvm)
- Resolves: bz#1772774
  (qemu-kvm core dump during migration+reboot ( Assertion `mem->dirty_bmap' failed ))

* Fri Dec 13 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.2.0-4.el8
- Rebase to qemu-4.2
- Resolves: bz#1783250
  (rebase qemu-kvm to 4.2)

* Tue Dec 10 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-18.el8
- kvm-LUKS-support-preallocation.patch [bz#1534951]
- kvm-nbd-add-empty-.bdrv_reopen_prepare.patch [bz#1718727]
- kvm-qdev-qbus-add-hidden-device-support.patch [bz#1757796]
- kvm-pci-add-option-for-net-failover.patch [bz#1757796]
- kvm-pci-mark-devices-partially-unplugged.patch [bz#1757796]
- kvm-pci-mark-device-having-guest-unplug-request-pending.patch [bz#1757796]
- kvm-qapi-add-unplug-primary-event.patch [bz#1757796]
- kvm-qapi-add-failover-negotiated-event.patch [bz#1757796]
- kvm-migration-allow-unplug-during-migration-for-failover.patch [bz#1757796]
- kvm-migration-add-new-migration-state-wait-unplug.patch [bz#1757796]
- kvm-libqos-tolerate-wait-unplug-migration-state.patch [bz#1757796]
- kvm-net-virtio-add-failover-support.patch [bz#1757796]
- kvm-vfio-unplug-failover-primary-device-before-migration.patch [bz#1757796]
- kvm-net-virtio-fix-dev_unplug_pending.patch [bz#1757796]
- kvm-net-virtio-return-early-when-failover-primary-alread.patch [bz#1757796]
- kvm-net-virtio-fix-re-plugging-of-primary-device.patch [bz#1757796]
- kvm-net-virtio-return-error-when-device_opts-arg-is-NULL.patch [bz#1757796]
- kvm-vfio-don-t-ignore-return-value-of-migrate_add_blocke.patch [bz#1757796]
- kvm-hw-vfio-pci-Fix-double-free-of-migration_blocker.patch [bz#1757796]
- Resolves: bz#1534951
  (RFE: Support preallocation mode for luks format)
- Resolves: bz#1718727
  (Committing changes to the backing file over NBD fails with reopening files not supported)
- Resolves: bz#1757796
  (RFE: support for net failover devices in qemu)

* Mon Dec 02 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-17.el8
- kvm-qemu-pr-helper-fix-crash-in-mpath_reconstruct_sense.patch [bz#1772322]
- Resolves: bz#1772322
  (qemu-pr-helper: fix crash in mpath_reconstruct_sense)

* Wed Nov 27 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-16.el8
- kvm-curl-Keep-pointer-to-the-CURLState-in-CURLSocket.patch [bz#1745209]
- kvm-curl-Keep-socket-until-the-end-of-curl_sock_cb.patch [bz#1745209]
- kvm-curl-Check-completion-in-curl_multi_do.patch [bz#1745209]
- kvm-curl-Pass-CURLSocket-to-curl_multi_do.patch [bz#1745209]
- kvm-curl-Report-only-ready-sockets.patch [bz#1745209]
- kvm-curl-Handle-success-in-multi_check_completion.patch [bz#1745209]
- kvm-curl-Check-curl_multi_add_handle-s-return-code.patch [bz#1745209]
- kvm-vhost-user-save-features-if-the-char-dev-is-closed.patch [bz#1738768]
- kvm-block-snapshot-Restrict-set-of-snapshot-nodes.patch [bz#1658981]
- kvm-iotests-Test-internal-snapshots-with-blockdev.patch [bz#1658981]
- kvm-qapi-Add-feature-flags-to-commands-in-qapi-introspec.patch [bz#1658981]
- kvm-qapi-Allow-introspecting-fix-for-savevm-s-cooperatio.patch [bz#1658981]
- kvm-block-Remove-backing-null-from-bs-explicit_-options.patch [bz#1773925]
- kvm-iotests-Test-multiple-blockdev-snapshot-calls.patch [bz#1773925]
- Resolves: bz#1658981
  (qemu failed to create internal snapshot via 'savevm' when using blockdev)
- Resolves: bz#1738768
  (Guest fails to recover receiving packets after vhost-user reconnect)
- Resolves: bz#1745209
  (qemu-img gets stuck when stream-converting from http)
- Resolves: bz#1773925
  (Fail to do blockcommit with more than one snapshots)

* Thu Nov 14 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-15.el8
- kvm-virtio-blk-Add-blk_drain-to-virtio_blk_device_unreal.patch [bz#1706759]
- kvm-Revert-qcow2-skip-writing-zero-buffers-to-empty-COW-.patch [bz#1772473]
- kvm-coroutine-Add-qemu_co_mutex_assert_locked.patch [bz#1772473]
- kvm-qcow2-Fix-corruption-bug-in-qcow2_detect_metadata_pr.patch [bz#1772473]
- Resolves: bz#1706759
  (qemu core dump when unplug a 16T GPT type disk from win2019 guest)
- Resolves: bz#1772473
  (Import fixes from 8.1.0 into 8.1.1 branch)

* Tue Oct 29 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-14.el8
- kvm-Revert-qcow2-skip-writing-zero-buffers-to-empty-COW-.patch [bz#1751934]
- kvm-coroutine-Add-qemu_co_mutex_assert_locked.patch [bz#1764721]
- kvm-qcow2-Fix-corruption-bug-in-qcow2_detect_metadata_pr.patch [bz#1764721]
- Resolves: bz#1751934
  (Fail to install guest when xfs is the host filesystem)
- Resolves: bz#1764721
  (qcow2 image corruption due to incorrect locking in preallocation detection)

* Fri Sep 27 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-13.el8
- kvm-nbd-server-attach-client-channel-to-the-export-s-Aio.patch [bz#1748253]
- kvm-virtio-blk-schedule-virtio_notify_config-to-run-on-m.patch [bz#1744955]
- Resolves: bz#1744955
  (Qemu hang when block resize a qcow2 image)
- Resolves: bz#1748253
  (QEMU crashes (core dump) when using the integrated NDB server with data-plane)

* Thu Sep 26 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-12.el8
- kvm-block-Use-QEMU_IS_ALIGNED.patch [bz#1745922]
- kvm-block-qcow2-Fix-corruption-introduced-by-commit-8ac0.patch [bz#1745922]
- kvm-block-qcow2-refactor-encryption-code.patch [bz#1745922]
- kvm-qemu-iotests-Add-test-for-bz-1745922.patch [bz#1745922]
- Resolves: bz#1745922
  (Luks-inside-qcow2 snapshot cannot boot after 'qemu-img rebase')

* Mon Sep 23 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-11.el8
- kvm-blockjob-update-nodes-head-while-removing-all-bdrv.patch [bz#1746631]
- kvm-hostmem-file-fix-pmem-file-size-check.patch [bz#1724008 bz#1736788]
- kvm-memory-fetch-pmem-size-in-get_file_size.patch [bz#1724008 bz#1736788]
- kvm-pr-manager-Fix-invalid-g_free-crash-bug.patch [bz#1753992]
- Resolves: bz#1724008
  (QEMU core dumped "memory_region_get_ram_ptr: Assertion `mr->ram_block' failed")
- Resolves: bz#1736788
  (QEMU core dumped if boot guest with nvdimm backed by /dev/dax0.0 and option pmem=off)
- Resolves: bz#1746631
  (Qemu core dump when do block commit under stress)
- Resolves: bz#1753992
  (core dump when testing persistent reservation in guest)

* Mon Sep 16 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-10.el8
- kvm-spapr-xive-Mask-the-EAS-when-allocating-an-IRQ.patch [bz#1748725]
- kvm-block-create-Do-not-abort-if-a-block-driver-is-not-a.patch [bz#1746267]
- kvm-virtio-blk-Cancel-the-pending-BH-when-the-dataplane-.patch [bz#1717321]
- kvm-Using-ip_deq-after-m_free-might-read-pointers-from-a.patch [bz#1749737]
- Resolves: bz#1717321
  (qemu-kvm core dumped when repeat "system_reset" multiple times during guest boot)
- Resolves: bz#1746267
  (qemu coredump: qemu-kvm: block/create.c:68: qmp_blockdev_create: Assertion `drv' failed)
- Resolves: bz#1748725
  ([ppc][migration][v6.3-rc1-p1ce8930]basic migration failed with "qemu-kvm: KVM_SET_DEVICE_ATTR failed: Group 3 attr 0x0000000000001309: Device or resource busy")
- Resolves: bz#1749737
  (CVE-2019-15890 qemu-kvm: QEMU: Slirp: use-after-free during packet reassembly [rhel-av-8])

* Tue Sep 10 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-9.el8
- kvm-migration-always-initialise-ram_counters-for-a-new-m.patch [bz#1734316]
- kvm-migration-add-qemu_file_update_transfer-interface.patch [bz#1734316]
- kvm-migration-add-speed-limit-for-multifd-migration.patch [bz#1734316]
- kvm-migration-update-ram_counters-for-multifd-sync-packe.patch [bz#1734316]
- kvm-spapr-pci-Consolidate-de-allocation-of-MSIs.patch [bz#1750200]
- kvm-spapr-pci-Free-MSIs-during-reset.patch [bz#1750200]
- Resolves: bz#1734316
  (multifd migration does not honour speed limits, consumes entire bandwidth of NIC)
- Resolves: bz#1750200
  ([RHEL8.1][QEMU4.1]boot up guest with vf device,then system_reset guest,error prompt(qemu-kvm: Can't allocate MSIs for device 2800: IRQ 4904 is not free))

* Mon Sep 09 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-8.el8
- kvm-migration-Do-not-re-read-the-clock-on-pre_save-in-ca.patch [bz#1747836]
- kvm-ehci-fix-queue-dev-null-ptr-dereference.patch [bz#1746790]
- kvm-spapr-Use-SHUTDOWN_CAUSE_SUBSYSTEM_RESET-for-CAS-reb.patch [bz#1743477]
- kvm-file-posix-Handle-undetectable-alignment.patch [bz#1749134]
- kvm-block-posix-Always-allocate-the-first-block.patch [bz#1749134]
- kvm-iotests-Test-allocate_first_block-with-O_DIRECT.patch [bz#1749134]
- Resolves: bz#1743477
  (Since bd94bc06479a "spapr: change default interrupt mode to 'dual'", QEMU resets the machine to select the appropriate interrupt controller. And -no-reboot prevents that.)
- Resolves: bz#1746790
  (qemu core dump while migrate from RHEL7.6 to RHEL8.1)
- Resolves: bz#1747836
  (Call traces after guest migration due to incorrect handling of the timebase)
- Resolves: bz#1749134
  (I/O error when virtio-blk disk is backed by a raw image on 4k disk)

* Fri Sep 06 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-7.el8
- kvm-trace-Clarify-DTrace-SystemTap-help-message.patch [bz#1516220]
- kvm-socket-Add-backlog-parameter-to-socket_listen.patch [bz#1726898]
- kvm-socket-Add-num-connections-to-qio_channel_socket_syn.patch [bz#1726898]
- kvm-socket-Add-num-connections-to-qio_channel_socket_asy.patch [bz#1726898]
- kvm-socket-Add-num-connections-to-qio_net_listener_open_.patch [bz#1726898]
- kvm-multifd-Use-number-of-channels-as-listen-backlog.patch [bz#1726898]
- kvm-pseries-Fix-compat_pvr-on-reset.patch [bz#1744107]
- kvm-spapr-Set-compat-mode-in-spapr_core_plug.patch [bz#1744107]
- Resolves: bz#1516220
  (-trace help prints an incomplete list of trace events)
- Resolves: bz#1726898
  (Parallel migration fails with error "Unable to write to socket: Connection reset by peer" now and then)
- Resolves: bz#1744107
  (Migration from P8(qemu4.1) to P9(qemu4.1), after migration, qemu crash on destination with error message "qemu-kvm: error while loading state for instance 0x1 of device 'cpu'")

* Wed Sep 04 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-6.el8
- kvm-memory-Refactor-memory_region_clear_coalescing.patch [bz#1743142]
- kvm-memory-Split-zones-when-do-coalesced_io_del.patch [bz#1743142]
- kvm-memory-Remove-has_coalesced_range-counter.patch [bz#1743142]
- kvm-memory-Fix-up-memory_region_-add-del-_coalescing.patch [bz#1743142]
- kvm-enable-virgl-for-real-this-time.patch [bz#1559740]
- Resolves: bz#1559740
  ([RFE] Enable virgl as TechPreview (qemu))
- Resolves: bz#1743142
  (Boot guest with multiple e1000 devices, qemu will crash after several guest reboots: kvm_mem_ioeventfd_add: error adding ioeventfd: No space left on device (28))

* Tue Aug 27 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-5.el8
- kvm-redhat-s390x-Rename-s390-ccw-virtio-rhel8.0.0-to-s39.patch [bz#1693772]
- kvm-redhat-s390x-Add-proper-compatibility-options-for-th.patch [bz#1693772]
- kvm-enable-virgl.patch [bz#1559740]
- kvm-redhat-update-pseries-rhel8.1.0-machine-type.patch [bz#1744170]
- kvm-Do-not-run-iotests-on-brew-build.patch [bz#1742197 bz#1742819]
- Resolves: bz#1559740
  ([RFE] Enable virgl as TechPreview (qemu))
- Resolves: bz#1693772
  ([IBM zKVM] RHEL AV 8.1.0 machine type update for s390x)
- Resolves: bz#1742197
  (Remove iotests from qemu-kvm builds [RHEL AV 8.1.0])
- Resolves: bz#1742819
  (Remove iotests from qemu-kvm builds [RHEL 8.1.0])
- Resolves: bz#1744170
  ([IBM Power] New 8.1.0 machine type for pseries)

* Tue Aug 20 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-4.el8
- kvm-RHEL-disable-hostmem-memfd.patch [bz#1738626 bz#1740797]
- Resolves: bz#1738626
  (Disable memfd in QEMU)
- Resolves: bz#1740797
  (Disable memfd in QEMU)

* Mon Aug 19 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-3.el8
- kvm-x86-machine-types-pc_rhel_8_0_compat.patch [bz#1719649]
- kvm-x86-machine-types-q35-Fixup-units_per_default_bus.patch [bz#1719649]
- kvm-x86-machine-types-Fixup-dynamic-sysbus-entries.patch [bz#1719649]
- kvm-x86-machine-types-add-pc-q35-rhel8.1.0.patch [bz#1719649]
- kvm-machine-types-Update-hw_compat_rhel_8_0-from-hw_comp.patch [bz#1719649]
- kvm-virtio-Make-disable-legacy-disable-modern-compat-pro.patch [bz#1719649]
- Resolves: bz#1719649
  (8.1 machine type for x86)

* Mon Aug 19 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.1.0-2.el8
- kvm-spec-Update-seavgabios-dependency.patch [bz#1725664]
- kvm-pc-Don-t-make-die-id-mandatory-unless-necessary.patch [bz#1741451]
- kvm-display-bochs-fix-pcie-support.patch [bz#1733977 bz#1740692]
- kvm-spapr-Reset-CAS-IRQ-subsystem-after-devices.patch [bz#1733977]
- kvm-spapr-xive-Fix-migration-of-hot-plugged-CPUs.patch [bz#1733977]
- kvm-riscv-roms-Fix-make-rules-for-building-sifive_u-bios.patch [bz#1733977 bz#1740692]
- kvm-Update-version-for-v4.1.0-release.patch [bz#1733977 bz#1740692]
- Resolves: bz#1725664
  (Update seabios dependency)
- Resolves: bz#1733977
  (Qemu core dumped: /home/ngu/qemu/hw/intc/xics_kvm.c:321: ics_kvm_set_irq: Assertion `kernel_xics_fd != -1' failed)
- Resolves: bz#1740692
  (Backport QEMU 4.1.0 rc5 & ga patches)
- Resolves: bz#1741451
  (Failed to hot-plug vcpus)

* Wed Aug 14 2019 Miroslav Rezanina <mrezanin@redhat.com> - 4.1.0-1.el8
- Rebase to qemu 4.1.0 rc4 [bz#1705235]
- Resolves: bz#1705235
  (Rebase qemu-kvm for RHEL-AV 8.1.0)

* Tue Jul 23 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.0.0-6.el8
- kvm-x86_64-rh-devices-add-missing-TPM-passthrough.patch [bz#1519013]
- kvm-x86_64-rh-devices-enable-TPM-emulation.patch [bz#1519013]
- kvm-vfio-increase-the-cap-on-number-of-assigned-devices-.patch [bz#1719823]
- Resolves: bz#1519013
  ([RFE] QEMU Software TPM support (vTPM, or TPM emulation))
- Resolves: bz#1719823
  ([RHEL 8.1] [RFE] increase the maximum of vfio devices to more than 32 in qemu-kvm)

* Mon Jul 08 2019 Miroslav Rezanina <mrezanin@redhat.com> - 4.0.0-5.el8
- kvm-qemu-kvm.spec-bump-libseccomp-2.4.0.patch [bz#1720306]
- kvm-qxl-check-release-info-object.patch [bz#1712717]
- kvm-target-i386-add-MDS-NO-feature.patch [bz#1722839]
- kvm-block-file-posix-Unaligned-O_DIRECT-block-status.patch [bz#1588356]
- kvm-iotests-Test-unaligned-raw-images-with-O_DIRECT.patch [bz#1588356]
- kvm-rh-set-CONFIG_BOCHS_DISPLAY-y-for-x86.patch [bz#1707118]
- Resolves: bz#1588356
  (qemu crashed on the source host when do storage migration with source qcow2 disk created by 'qemu-img')
- Resolves: bz#1707118
  (enable device: bochs-display (QEMU))
- Resolves: bz#1712717
  (CVE-2019-12155 qemu-kvm: QEMU: qxl: null pointer dereference while releasing spice resources [rhel-av-8])
- Resolves: bz#1720306
  (VM failed to start with error "failed to install seccomp syscall filter in the kernel")
- Resolves: bz#1722839
  ([Intel 8.1 FEAT] MDS_NO exposure to guest - Fast Train)

* Tue Jun 11 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.0.0-4.el8
- kvm-Disable-VXHS-support.patch [bz#1714937]
- kvm-aarch64-Add-virt-rhel8.1.0-machine-type-for-ARM.patch [bz#1713735]
- kvm-aarch64-Allow-ARM-VIRT-iommu-option-in-RHEL8.1-machi.patch [bz#1713735]
- kvm-usb-call-reset-handler-before-updating-state.patch [bz#1713679]
- kvm-usb-host-skip-reset-for-untouched-devices.patch [bz#1713679]
- kvm-usb-host-avoid-libusb_set_configuration-calls.patch [bz#1713679]
- kvm-aarch64-Compile-out-IOH3420.patch [bz#1627283]
- kvm-vl-Fix-drive-blockdev-persistent-reservation-managem.patch [bz#1714891]
- kvm-vl-Document-why-objects-are-delayed.patch [bz#1714891]
- Resolves: bz#1627283
  (Compile out IOH3420 on aarch64)
- Resolves: bz#1713679
  (Detached device when trying to upgrade USB device firmware when in doing USB Passthrough via QEMU)
- Resolves: bz#1713735
  (Allow ARM VIRT iommu option in RHEL8.1 machine)
- Resolves: bz#1714891
  (Guest with persistent reservation manager for a disk fails to start)
- Resolves: bz#1714937
  (Disable VXHS support)

* Tue May 28 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.0.0-3.el8
- kvm-redhat-fix-cut-n-paste-garbage-in-hw_compat-comments.patch [bz#1709726]
- kvm-compat-Generic-hw_compat_rhel_8_0.patch [bz#1709726]
- kvm-redhat-sync-pseries-rhel7.6.0-with-rhel-av-8.0.1.patch [bz#1709726]
- kvm-redhat-define-pseries-rhel8.1.0-machine-type.patch [bz#1709726]
- Resolves: bz#1709726
  (Forward and backward migration failed with "qemu-kvm: error while loading state for instance 0x0 of device 'spapr'")

* Sat May 25 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 4.0.0-2.el8
- kvm-target-i386-define-md-clear-bit.patch [bz#1703297 bz#1703304 bz#1703310 bz#1707274]
- Resolves: bz#1703297
  (CVE-2018-12126 virt:8.0.0/qemu-kvm: hardware: Microarchitectural Store Buffer Data Sampling (MSBDS) [rhel-av-8])
- Resolves: bz#1703304
  (CVE-2018-12130 virt:8.0.0/qemu-kvm: hardware: Microarchitectural Fill Buffer Data Sampling (MFBDS) [rhel-av-8])
- Resolves: bz#1703310
  (CVE-2018-12127 virt:8.0.0/qemu-kvm: hardware: Micro-architectural Load Port Data Sampling - Information Leak (MLPDS) [rhel-av-8])
- Resolves: bz#1707274
  (CVE-2019-11091 virt:8.0.0/qemu-kvm: hardware: Microarchitectural Data Sampling Uncacheable Memory (MDSUM) [rhel-av-8.1.0])

* Wed May 15 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-26.el8
- kvm-target-ppc-spapr-Add-SPAPR_CAP_LARGE_DECREMENTER.patch [bz#1698711]
- kvm-target-ppc-spapr-Add-workaround-option-to-SPAPR_CAP_.patch [bz#1698711]
- kvm-target-ppc-spapr-Add-SPAPR_CAP_CCF_ASSIST.patch [bz#1698711]
- kvm-target-ppc-tcg-make-spapr_caps-apply-cap-cfpc-sbbc-i.patch [bz#1698711]
- kvm-target-ppc-spapr-Enable-mitigations-by-default-for-p.patch [bz#1698711]
- kvm-slirp-ensure-there-is-enough-space-in-mbuf-to-null-t.patch [bz#1693076]
- kvm-slirp-don-t-manipulate-so_rcv-in-tcp_emu.patch [bz#1693076]
- Resolves: bz#1693076
  (CVE-2019-6778 qemu-kvm: QEMU: slirp: heap buffer overflow in tcp_emu() [rhel-av-8])
- Resolves: bz#1698711
  (Enable Spectre / Meltdown mitigations by default in pseries-rhel8.0.0 machine type)

* Mon May 06 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-25.el8
- kvm-redhat-enable-tpmdev-passthrough.patch [bz#1688312]
- kvm-exec-Only-count-mapped-memory-backends-for-qemu_getr.patch [bz#1680492]
- kvm-Enable-libpmem-to-support-nvdimm.patch [bz#1705149]
- Resolves: bz#1680492
  (Qemu quits suddenly while system_reset after hot-plugging unsupported memory by compatible guest on P9 with 1G huge page set)
- Resolves: bz#1688312
  ([RFE] enable TPM passthrough at compile time (qemu-kvm))
- Resolves: bz#1705149
  (libpmem support is not enabled in qemu-kvm)

* Fri Apr 26 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-24.el8
- kvm-x86-host-phys-bits-limit-option.patch [bz#1688915]
- kvm-rhel-Set-host-phys-bits-limit-48-on-rhel-machine-typ.patch [bz#1688915]
- Resolves: bz#1688915
  ([Intel 8.0 Alpha] physical bits should  <= 48  when host with 5level paging &EPT5 and qemu command with "-cpu qemu64" parameters.)

* Tue Apr 23 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-23.el8
- kvm-device_tree-Fix-integer-overflowing-in-load_device_t.patch [bz#1693173]
- Resolves: bz#1693173
  (CVE-2018-20815 qemu-kvm: QEMU: device_tree: heap buffer overflow while loading device tree blob [rhel-av-8])

* Mon Apr 15 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-22.el8
- kvm-i386-kvm-Disable-arch_capabilities-if-MSR-can-t-be-s.patch [bz#1687578]
- kvm-i386-Make-arch_capabilities-migratable.patch [bz#1687578]
- Resolves: bz#1687578
  (Incorrect CVE vulnerabilities reported on Cascade Lake cpus)

* Thu Apr 11 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-21.el8
- kvm-Remove-7-qcow2-and-luks-iotests-that-are-taking-25-s.patch [bz#1683473]
- kvm-spapr-fix-out-of-bounds-write-in-spapr_populate_drme.patch [bz#1674438]
- kvm-qcow2-include-LUKS-payload-overhead-in-qemu-img-meas.patch [bz#1655065]
- kvm-iotests-add-LUKS-payload-overhead-to-178-qemu-img-me.patch [bz#1655065]
- kvm-vnc-detect-and-optimize-pageflips.patch [bz#1666206]
- kvm-Load-kvm-module-during-boot.patch [bz#1676907 bz#1685995]
- kvm-hostmem-file-reject-invalid-pmem-file-sizes.patch [bz#1669053]
- kvm-iotests-Fix-test-200-on-s390x-without-virtio-pci.patch [bz#1687582]
- kvm-block-file-posix-do-not-fail-on-unlock-bytes.patch [bz#1652572]
- Resolves: bz#1652572
  (QEMU core dumped if stop nfs service during migration)
- Resolves: bz#1655065
  ([rhel.8.0][fast train]'qemu-img measure' size does not match the real allocated size for luks-inside-qcow2 image)
- Resolves: bz#1666206
  (vnc server should detect page-flips and avoid sending fullscreen updates then.)
- Resolves: bz#1669053
  (Guest call trace when boot with nvdimm device backed by /dev/dax)
- Resolves: bz#1674438
  (RHEL8.0 - Guest reboot fails after memory hotplug multiple times (kvm))
- Resolves: bz#1676907
  (/dev/kvm device exists but kernel module is not loaded on boot up causing VM start to fail in libvirt)
- Resolves: bz#1683473
  (Remove 7 qcow2 & luks iotests from rhel8 fast train build %check phase)
- Resolves: bz#1685995
  (/dev/kvm device exists but kernel module is not loaded on boot up causing VM start to fail in libvirt)
- Resolves: bz#1687582
  (QEMU IOTEST 200 fails with 'virtio-scsi-pci is not a valid device model name')

* Fri Mar 15 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-20.el8
- kvm-i386-Add-stibp-flag-name.patch [bz#1686260]
- Resolves: bz#1686260
  (stibp is missing on qemu 3.0 and qemu 3.1)

* Fri Mar 15 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-19.el8
- kvm-migration-Fix-cancel-state.patch [bz#1608649]
- kvm-migration-rdma-Fix-qemu_rdma_cleanup-null-check.patch [bz#1608649]
- Resolves: bz#1608649
  (Query-migrate get "failed" status after migrate-cancel)

* Tue Feb 26 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-18.el8
- kvm-target-i386-Disable-MPX-support-on-named-CPU-models.patch [bz#1661030]
- kvm-i386-remove-the-new-CPUID-PCONFIG-from-Icelake-Serve.patch [bz#1661515]
- kvm-i386-remove-the-INTEL_PT-CPUID-bit-from-named-CPU-mo.patch [bz#1661515]
- kvm-Revert-i386-Add-CPUID-bit-for-PCONFIG.patch [bz#1661515]
- Resolves: bz#1661030
  (Remove MPX support from 8.0 machine types)
- Resolves: bz#1661515
  (Remove PCONFIG and INTEL_PT from Icelake-* CPU models)

* Tue Feb 26 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-17.el8
- kvm-block-Apply-auto-read-only-for-ro-whitelist-drivers.patch [bz#1678968]
- Resolves: bz#1678968
  (-blockdev: auto-read-only is ineffective for drivers on read-only whitelist)

* Mon Feb 25 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-16.el8
- kvm-fdc-Revert-downstream-disablement-of-device-floppy.patch [bz#1664997]
- kvm-fdc-Restrict-floppy-controllers-to-RHEL-7-machine-ty.patch [bz#1664997]
- Resolves: bz#1664997
  (Restrict floppy device to RHEL-7 machine types)

* Wed Feb 13 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-15.el8
- kvm-Add-raw-qcow2-nbd-and-luks-iotests-to-run-during-the.patch [bz#1664855]
- kvm-Introduce-the-qemu-kvm-tests-rpm.patch [bz#1669924]
- Resolves: bz#1664855
  (Run iotests in qemu-kvm build %check phase)
- Resolves: bz#1669924
  (qemu-kvm packaging: Package the avocado_qemu tests and qemu-iotests in a new rpm)

* Tue Feb 12 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-14.el8
- kvm-doc-fix-the-configuration-path.patch [bz#1644985]
- Resolves: bz#1644985
  (The "fsfreeze-hook" script path shown by command "qemu-ga --help" or "man qemu-ga" is wrong - Fast Train)

* Mon Feb 11 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-13.el8
- kvm-Acceptance-tests-add-Linux-initrd-checking-test.patch [bz#1669922]
- kvm-mmap-alloc-unfold-qemu_ram_mmap.patch [bz#1671519]
- kvm-mmap-alloc-fix-hugetlbfs-misaligned-length-in-ppc64.patch [bz#1671519]
- kvm-BZ1653590-Require-at-least-64kiB-pages-for-downstrea.patch [bz#1653590]
- kvm-block-Fix-invalidate_cache-error-path-for-parent-act.patch [bz#1673014]
- kvm-virtio-scsi-Move-BlockBackend-back-to-the-main-AioCo.patch [bz#1656276 bz#1662508]
- kvm-scsi-disk-Acquire-the-AioContext-in-scsi_-_realize.patch [bz#1656276 bz#1662508]
- kvm-virtio-scsi-Forbid-devices-with-different-iothreads-.patch [bz#1656276 bz#1662508]
- Resolves: bz#1653590
  ([Fast train]had better stop qemu immediately while guest was making use of an improper page size)
- Resolves: bz#1656276
  (qemu-kvm core dumped after hotplug the deleted disk with iothread parameter)
- Resolves: bz#1662508
  (Qemu core dump when start guest with two disks using same drive)
- Resolves: bz#1669922
  (Backport avocado-qemu tests for QEMU 3.1)
- Resolves: bz#1671519
  (RHEL8.0 Snapshot3 - qemu doesn't free up hugepage memory when hotplug/hotunplug using memory-backend-file (qemu-kvm))
- Resolves: bz#1673014
  (Local VM and migrated VM on the same host can run with same RAW file as visual disk source while without shareable configured or lock manager enabled)

* Fri Feb 08 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-12.el8
- kvm-io-ensure-UNIX-client-doesn-t-unlink-server-socket.patch [bz#1665896]
- kvm-scsi-disk-Don-t-use-empty-string-as-device-id.patch [bz#1668248]
- kvm-scsi-disk-Add-device_id-property.patch [bz#1668248]
- Resolves: bz#1665896
  (VNC unix listener socket is deleted after first client quits)
- Resolves: bz#1668248
  ("An unknown error has occurred" when using cdrom to install the system with two blockdev disks.(when choose installation destination))

* Thu Jan 31 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-11.el8
- kvm-Fix-fsfreeze-hook-path-in-the-man-page.patch [bz#1644985]
- kvm-json-Fix-handling-when-not-interpolating.patch [bz#1668244]
- Resolves: bz#1644985
  (The "fsfreeze-hook" script path shown by command "qemu-ga --help" or "man qemu-ga" is wrong - Fast Train)
- Resolves: bz#1668244
  (qemu-img: /var/tmp/v2vovl9951f8.qcow2: CURL: Error opening file: The requested URL returned error: 404 Not Found)

* Tue Jan 29 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-10.el8
- kvm-throttle-groups-fix-restart-coroutine-iothread-race.patch [bz#1655947]
- kvm-iotests-add-238-for-throttling-tgm-unregister-iothre.patch [bz#1655947]
- Resolves: bz#1655947
  (qemu-kvm core dumped after unplug the device which was set io throttling parameters)

* Tue Jan 29 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-9.el8
- kvm-migration-rdma-unregister-fd-handler.patch [bz#1666601]
- kvm-s390x-tod-Properly-stop-the-KVM-TOD-while-the-guest-.patch [bz#1659127]
- kvm-hw-s390x-Fix-bad-mask-in-time2tod.patch [bz#1659127]
- Resolves: bz#1659127
  (Stress guest and stop it, then do live migration, guest hit call trace on destination end)
- Resolves: bz#1666601
  ([q35] dst qemu core dumped when do rdma migration with Mellanox IB QDR card)

* Thu Jan 24 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-7.el8
- kvm-i386-kvm-expose-HV_CPUID_ENLIGHTMENT_INFO.EAX-and-HV.patch [bz#1653511]
- kvm-i386-kvm-add-a-comment-explaining-why-.feat_names-ar.patch [bz#1653511]
- Resolves: bz#1653511
  (qemu doesn't report all support cpu features which cause libvirt cannot get the support status of hv_tlbflush)

* Wed Jan 23 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-6.el8
- kvm-spapr-Fix-ibm-max-associativity-domains-property-num.patch [bz#1653114]
- kvm-cpus-ignore-ESRCH-in-qemu_cpu_kick_thread.patch [bz#1668205]
- Resolves: bz#1653114
  (Incorrect NUMA nodes passed to qemu-kvm guest in ibm,max-associativity-domains property)
- Resolves: bz#1668205
  (Guest quit with error when hotunplug cpu)

* Mon Jan 21 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-5.el8
- kvm-virtio-Helper-for-registering-virtio-device-types.patch [bz#1648023]
- kvm-virtio-Provide-version-specific-variants-of-virtio-P.patch [bz#1648023]
- kvm-globals-Allow-global-properties-to-be-optional.patch [bz#1648023]
- kvm-virtio-Make-disable-legacy-disable-modern-compat-pro.patch [bz#1648023]
- kvm-aarch64-Add-virt-rhel8.0.0-machine-type-for-ARM.patch [bz#1656504]
- kvm-aarch64-Set-virt-rhel8.0.0-max_cpus-to-512.patch [bz#1656504]
- kvm-aarch64-Use-256MB-ECAM-region-by-default.patch [bz#1656504]
- Resolves: bz#1648023
  (Provide separate device types for transitional virtio PCI devices - Fast Train)
- Resolves: bz#1656504
  (Machine types for qemu-kvm based on rebase to qemu-3.1 (aarch64))

* Fri Jan 11 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-4.el8
- kvm-hw-s390x-s390-virtio-ccw-Add-machine-types-for-RHEL8.patch [bz#1656510]
- kvm-spapr-Add-H-Call-H_HOME_NODE_ASSOCIATIVITY.patch [bz#1661967]
- kvm-redhat-Fixing-.gitpublish-to-include-AV-information.patch []
- Resolves: bz#1656510
  (Machine types for qemu-kvm based on rebase to qemu-3.1 (s390x))
- Resolves: bz#1661967
  (Kernel prints the message "VPHN is not supported. Disabling polling...")

* Thu Jan 03 2019 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-3.el8
- kvm-redhat-define-pseries-rhel8.0.0-machine-type.patch [bz#1656508]
- Resolves: bz#1656508
  (Machine types for qemu-kvm based on rebase to qemu-3.1 (ppc64le))

* Fri Dec 21 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-2.el8
- kvm-pc-7.5-compat-entries.patch [bz#1655820]
- kvm-compat-Generic-HW_COMPAT_RHEL7_6.patch [bz#1655820]
- kvm-pc-PC_RHEL7_6_COMPAT.patch [bz#1655820]
- kvm-pc-Add-compat-for-pc-i440fx-rhel7.6.0-machine-type.patch [bz#1655820]
- kvm-pc-Add-pc-q35-8.0.0-machine-type.patch [bz#1655820]
- kvm-pc-Add-x-migrate-smi-count-off-to-PC_RHEL7_6_COMPAT.patch [bz#1655820]
- kvm-clear-out-KVM_ASYNC_PF_DELIVERY_AS_PF_VMEXIT-for.patch [bz#1659604]
- kvm-Add-edk2-Requires-to-qemu-kvm.patch [bz#1660208]
- Resolves: bz#1655820
  (Can't migarate between rhel8 and rhel7 when guest has device "video")
- Resolves: bz#1659604
  (8->7 migration failed: qemu-kvm: error: failed to set MSR 0x4b564d02 to 0x27fc13285)
- Resolves: bz#1660208
  (qemu-kvm: Should depend on the architecture-appropriate guest firmware)

* Thu Dec 13 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 3.1.0-1.el8
- Rebase to qemu-kvm 3.1.0

* Tue Dec 11 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-47
- kvm-Disable-CONFIG_IPMI-and-CONFIG_I2C-for-ppc64.patch [bz#1640044]
- kvm-Disable-CONFIG_CAN_BUS-and-CONFIG_CAN_SJA1000.patch [bz#1640042]
- Resolves: bz#1640042
  (Disable CONFIG_CAN_BUS and CONFIG_CAN_SJA1000 config switches)
- Resolves: bz#1640044
  (Disable CONFIG_I2C and CONFIG_IPMI in default-configs/ppc64-softmmu.mak)

* Tue Dec 11 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-46 
- kvm-qcow2-Give-the-refcount-cache-the-minimum-possible-s.patch [bz#1656507]
- kvm-docs-Document-the-new-default-sizes-of-the-qcow2-cac.patch [bz#1656507]
- kvm-qcow2-Fix-Coverity-warning-when-calculating-the-refc.patch [bz#1656507]
- kvm-include-Add-IEC-binary-prefixes-in-qemu-units.h.patch [bz#1656507]
- kvm-qcow2-Options-documentation-fixes.patch [bz#1656507]
- kvm-include-Add-a-lookup-table-of-sizes.patch [bz#1656507]
- kvm-qcow2-Make-sizes-more-humanly-readable.patch [bz#1656507]
- kvm-qcow2-Avoid-duplication-in-setting-the-refcount-cach.patch [bz#1656507]
- kvm-qcow2-Assign-the-L2-cache-relatively-to-the-image-si.patch [bz#1656507]
- kvm-qcow2-Increase-the-default-upper-limit-on-the-L2-cac.patch [bz#1656507]
- kvm-qcow2-Resize-the-cache-upon-image-resizing.patch [bz#1656507]
- kvm-qcow2-Set-the-default-cache-clean-interval-to-10-min.patch [bz#1656507]
- kvm-qcow2-Explicit-number-replaced-by-a-constant.patch [bz#1656507]
- kvm-block-backend-Set-werror-rerror-defaults-in-blk_new.patch [bz#1657637]
- kvm-qcow2-Fix-cache-clean-interval-documentation.patch [bz#1656507]
- Resolves: bz#1656507
  ([RHEL.8] qcow2 cache is too small)
- Resolves: bz#1657637
  (Wrong werror default for -device drive=<node-name>)

* Thu Dec 06 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-45
- kvm-target-ppc-add-basic-support-for-PTCR-on-POWER9.patch [bz#1639069]
- kvm-linux-headers-Update-for-nested-KVM-HV-downstream-on.patch [bz#1639069]
- kvm-target-ppc-Add-one-reg-id-for-ptcr.patch [bz#1639069]
- kvm-ppc-spapr_caps-Add-SPAPR_CAP_NESTED_KVM_HV.patch [bz#1639069]
- kvm-Re-enable-CONFIG_HYPERV_TESTDEV.patch [bz#1651195]
- kvm-qxl-use-guest_monitor_config-for-local-renderer.patch [bz#1610163]
- kvm-Declare-cirrus-vga-as-deprecated.patch [bz#1651994]
- kvm-Do-not-build-bluetooth-support.patch [bz#1654651]
- kvm-vfio-helpers-Fix-qemu_vfio_open_pci-crash.patch [bz#1645840]
- kvm-balloon-Allow-multiple-inhibit-users.patch [bz#1650272]
- kvm-Use-inhibit-to-prevent-ballooning-without-synchr.patch [bz#1650272]
- kvm-vfio-Inhibit-ballooning-based-on-group-attachment-to.patch [bz#1650272]
- kvm-vfio-ccw-pci-Allow-devices-to-opt-in-for-ballooning.patch [bz#1650272]
- kvm-vfio-pci-Handle-subsystem-realpath-returning-NULL.patch [bz#1650272]
- kvm-vfio-pci-Fix-failure-to-close-file-descriptor-on-err.patch [bz#1650272]
- kvm-postcopy-Synchronize-usage-of-the-balloon-inhibitor.patch [bz#1650272]
- Resolves: bz#1610163
  (guest shows border blurred screen with some resolutions when qemu boot with -device qxl-vga ,and guest on rhel7.6 has no  such question)
- Resolves: bz#1639069
  ([IBM 8.0 FEAT] POWER9 - Nested virtualization in RHEL8.0 KVM for ppc64le - qemu-kvm side)
- Resolves: bz#1645840
  (Qemu core dump when hotplug nvme:// drive via -blockdev)
- Resolves: bz#1650272
  (Ballooning is incompatible with vfio assigned devices, but not prevented)
- Resolves: bz#1651195
  (Re-enable hyperv-testdev device)
- Resolves: bz#1651994
  (Declare the "Cirrus VGA" device emulation of QEMU as deprecated in RHEL8)
- Resolves: bz#1654651
  (Qemu: hw: bt: keep bt/* objects from building [rhel-8.0])

* Tue Nov 27 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-43
- kvm-block-Make-more-block-drivers-compile-time-configura.patch [bz#1598842 bz#1598842]
- kvm-RHEL8-Add-disable-configure-options-to-qemu-spec-fil.patch [bz#1598842]
- Resolves: bz#1598842
  (Compile out unused block drivers)

* Mon Nov 26 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-43

- kvm-configure-add-test-for-libudev.patch [bz#1636185]
- kvm-qga-linux-report-disk-serial-number.patch [bz#1636185]
- kvm-qga-linux-return-disk-device-in-guest-get-fsinfo.patch [bz#1636185]
- kvm-qemu-error-introduce-error-warn-_report_once.patch [bz#1625173]
- kvm-intel-iommu-start-to-use-error_report_once.patch [bz#1625173]
- kvm-intel-iommu-replace-more-vtd_err_-traces.patch [bz#1625173]
- kvm-intel_iommu-introduce-vtd_reset_caches.patch [bz#1625173]
- kvm-intel_iommu-better-handling-of-dmar-state-switch.patch [bz#1625173]
- kvm-intel_iommu-move-ce-fetching-out-when-sync-shadow.patch [bz#1625173 bz#1629616]
- kvm-intel_iommu-handle-invalid-ce-for-shadow-sync.patch [bz#1625173 bz#1629616]
- kvm-block-remove-bdrv_dirty_bitmap_make_anon.patch [bz#1518989]
- kvm-block-simplify-code-around-releasing-bitmaps.patch [bz#1518989]
- kvm-hbitmap-Add-advance-param-to-hbitmap_iter_next.patch [bz#1518989]
- kvm-test-hbitmap-Add-non-advancing-iter_next-tests.patch [bz#1518989]
- kvm-block-dirty-bitmap-Add-bdrv_dirty_iter_next_area.patch [bz#1518989]
- kvm-blockdev-backup-add-bitmap-argument.patch [bz#1518989]
- kvm-dirty-bitmap-switch-assert-fails-to-errors-in-bdrv_m.patch [bz#1518989]
- kvm-dirty-bitmap-rename-bdrv_undo_clear_dirty_bitmap.patch [bz#1518989]
- kvm-dirty-bitmap-make-it-possible-to-restore-bitmap-afte.patch [bz#1518989]
- kvm-blockdev-rename-block-dirty-bitmap-clear-transaction.patch [bz#1518989]
- kvm-qapi-add-transaction-support-for-x-block-dirty-bitma.patch [bz#1518989]
- kvm-block-dirty-bitmaps-add-user_locked-status-checker.patch [bz#1518989]
- kvm-block-dirty-bitmaps-fix-merge-permissions.patch [bz#1518989]
- kvm-block-dirty-bitmaps-allow-clear-on-disabled-bitmaps.patch [bz#1518989]
- kvm-block-dirty-bitmaps-prohibit-enable-disable-on-locke.patch [bz#1518989]
- kvm-block-backup-prohibit-backup-from-using-in-use-bitma.patch [bz#1518989]
- kvm-nbd-forbid-use-of-frozen-bitmaps.patch [bz#1518989]
- kvm-bitmap-Update-count-after-a-merge.patch [bz#1518989]
- kvm-iotests-169-drop-deprecated-autoload-parameter.patch [bz#1518989]
- kvm-block-qcow2-improve-error-message-in-qcow2_inactivat.patch [bz#1518989]
- kvm-bloc-qcow2-drop-dirty_bitmaps_loaded-state-variable.patch [bz#1518989]
- kvm-dirty-bitmaps-clean-up-bitmaps-loading-and-migration.patch [bz#1518989]
- kvm-iotests-improve-169.patch [bz#1518989]
- kvm-iotests-169-add-cases-for-source-vm-resuming.patch [bz#1518989]
- kvm-pc-dimm-turn-alignment-assert-into-check.patch [bz#1630116]
- Resolves: bz#1518989
  (RFE: QEMU Incremental live backup)
- Resolves: bz#1625173
  ([NVMe Device Assignment] Guest could not boot up with q35+iommu)
- Resolves: bz#1629616
  (boot guest with q35+vIOMMU+ device assignment, qemu terminal shows "qemu-kvm: VFIO_UNMAP_DMA: -22" when return assigned network devices from vfio driver to ixgbe in guest)
- Resolves: bz#1630116
  (pc_dimm_get_free_addr: assertion failed: (QEMU_ALIGN_UP(address_space_start, align) == address_space_start))
- Resolves: bz#1636185
  ([RFE] Report disk device name and serial number (qemu-guest-agent on Linux))

* Mon Nov 05 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-42.el8
- kvm-luks-Allow-share-rw-on.patch [bz#1629701]
- kvm-redhat-reenable-gluster-support.patch [bz#1599340]
- kvm-redhat-bump-libusb-requirement.patch [bz#1627970]
- Resolves: bz#1599340
  (Reenable glusterfs in qemu-kvm once BZ#1567292 gets fixed)
- Resolves: bz#1627970
  (symbol lookup error: /usr/libexec/qemu-kvm: undefined symbol: libusb_set_option)
- Resolves: bz#1629701
  ("share-rw=on" does not work for luks format image - Fast Train)

* Tue Oct 16 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-41.el8
- kvm-block-rbd-pull-out-qemu_rbd_convert_options.patch [bz#1635585]
- kvm-block-rbd-Attempt-to-parse-legacy-filenames.patch [bz#1635585]
- kvm-block-rbd-add-deprecation-documentation-for-filename.patch [bz#1635585]
- kvm-block-rbd-add-iotest-for-rbd-legacy-keyvalue-filenam.patch [bz#1635585]
- Resolves: bz#1635585
  (rbd json format of 7.6 is incompatible with 7.5)

* Tue Oct 16 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-40.el8

- kvm-vnc-call-sasl_server_init-only-when-required.patch [bz#1609327]
- kvm-nbd-server-fix-NBD_CMD_CACHE.patch [bz#1636142]
- kvm-nbd-fix-NBD_FLAG_SEND_CACHE-value.patch [bz#1636142]
- kvm-test-bdrv-drain-bdrv_drain-works-with-cross-AioConte.patch [bz#1637976]
- kvm-block-Use-bdrv_do_drain_begin-end-in-bdrv_drain_all.patch [bz#1637976]
- kvm-block-Remove-recursive-parameter-from-bdrv_drain_inv.patch [bz#1637976]
- kvm-block-Don-t-manually-poll-in-bdrv_drain_all.patch [bz#1637976]
- kvm-tests-test-bdrv-drain-bdrv_drain_all-works-in-corout.patch [bz#1637976]
- kvm-block-Avoid-unnecessary-aio_poll-in-AIO_WAIT_WHILE.patch [bz#1637976]
- kvm-block-Really-pause-block-jobs-on-drain.patch [bz#1637976]
- kvm-block-Remove-bdrv_drain_recurse.patch [bz#1637976]
- kvm-test-bdrv-drain-Add-test-for-node-deletion.patch [bz#1637976]
- kvm-block-Drain-recursively-with-a-single-BDRV_POLL_WHIL.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-node-deletion-in-subtree-recurs.patch [bz#1637976]
- kvm-block-Don-t-poll-in-parent-drain-callbacks.patch [bz#1637976]
- kvm-test-bdrv-drain-Graph-change-through-parent-callback.patch [bz#1637976]
- kvm-block-Defer-.bdrv_drain_begin-callback-to-polling-ph.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-that-bdrv_drain_invoke-doesn-t-.patch [bz#1637976]
- kvm-block-Allow-AIO_WAIT_WHILE-with-NULL-ctx.patch [bz#1637976]
- kvm-block-Move-bdrv_drain_all_begin-out-of-coroutine-con.patch [bz#1637976]
- kvm-block-ignore_bds_parents-parameter-for-drain-functio.patch [bz#1637976]
- kvm-block-Allow-graph-changes-in-bdrv_drain_all_begin-en.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-graph-changes-in-drain_all-sect.patch [bz#1637976]
- kvm-block-Poll-after-drain-on-attaching-a-node.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-bdrv_append-to-drained-node.patch [bz#1637976]
- kvm-block-linux-aio-acquire-AioContext-before-qemu_laio_.patch [bz#1637976]
- kvm-util-async-use-qemu_aio_coroutine_enter-in-co_schedu.patch [bz#1637976]
- kvm-job-Fix-nested-aio_poll-hanging-in-job_txn_apply.patch [bz#1637976]
- kvm-job-Fix-missing-locking-due-to-mismerge.patch [bz#1637976]
- kvm-blockjob-Wake-up-BDS-when-job-becomes-idle.patch [bz#1637976]
- kvm-aio-wait-Increase-num_waiters-even-in-home-thread.patch [bz#1637976]
- kvm-test-bdrv-drain-Drain-with-block-jobs-in-an-I-O-thre.patch [bz#1637976]
- kvm-test-blockjob-Acquire-AioContext-around-job_cancel_s.patch [bz#1637976]
- kvm-job-Use-AIO_WAIT_WHILE-in-job_finish_sync.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-AIO_WAIT_WHILE-in-completion-ca.patch [bz#1637976]
- kvm-block-Add-missing-locking-in-bdrv_co_drain_bh_cb.patch [bz#1637976]
- kvm-block-backend-Add-.drained_poll-callback.patch [bz#1637976]
- kvm-block-backend-Fix-potential-double-blk_delete.patch [bz#1637976]
- kvm-block-backend-Decrease-in_flight-only-after-callback.patch [bz#1637976]
- kvm-blockjob-Lie-better-in-child_job_drained_poll.patch [bz#1637976]
- kvm-block-Remove-aio_poll-in-bdrv_drain_poll-variants.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-nested-poll-in-bdrv_drain_poll_.patch [bz#1637976]
- kvm-job-Avoid-deadlocks-in-job_completed_txn_abort.patch [bz#1637976]
- kvm-test-bdrv-drain-AIO_WAIT_WHILE-in-job-.commit-.abort.patch [bz#1637976]
- kvm-test-bdrv-drain-Fix-outdated-comments.patch [bz#1637976]
- kvm-block-Use-a-single-global-AioWait.patch [bz#1637976]
- kvm-test-bdrv-drain-Test-draining-job-source-child-and-p.patch [bz#1637976]
- kvm-qemu-img-Fix-assert-when-mapping-unaligned-raw-file.patch [bz#1639374]
- kvm-iotests-Add-test-221-to-catch-qemu-img-map-regressio.patch [bz#1639374]
- Resolves: bz#1609327
  (qemu-kvm[37046]: Could not find keytab file: /etc/qemu/krb5.tab: Unknown error 49408)
- Resolves: bz#1636142
  (qemu NBD_CMD_CACHE flaws impacting non-qemu NBD clients)
- Resolves: bz#1637976
  (Crashes and hangs with iothreads vs. block jobs)
- Resolves: bz#1639374
  (qemu-img map 'Aborted (core dumped)' when specifying a plain file)

* Tue Oct 16 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 
- kvm-linux-headers-update.patch [bz#1508142]
- kvm-s390x-cpumodel-Set-up-CPU-model-for-AP-device-suppor.patch [bz#1508142]
- kvm-s390x-kvm-enable-AP-instruction-interpretation-for-g.patch [bz#1508142]
- kvm-s390x-ap-base-Adjunct-Processor-AP-object-model.patch [bz#1508142]
- kvm-s390x-vfio-ap-Introduce-VFIO-AP-device.patch [bz#1508142]
- kvm-s390-doc-detailed-specifications-for-AP-virtualizati.patch [bz#1508142]
- Resolves: bz#1508142
  ([IBM 8.0 FEAT] KVM: Guest-dedicated Crypto Adapters - qemu part)

* Mon Oct 15 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-38.el8
- kvm-Revert-hw-acpi-build-build-SRAT-memory-affinity-stru.patch [bz#1609235]
- kvm-add-udev-kvm-check.patch [bz#1552663]
- kvm-aio-posix-Don-t-count-ctx-notifier-as-progress-when-.patch [bz#1623085]
- kvm-aio-Do-aio_notify_accept-only-during-blocking-aio_po.patch [bz#1623085]
- kvm-aio-posix-fix-concurrent-access-to-poll_disable_cnt.patch [bz#1632622]
- kvm-aio-posix-compute-timeout-before-polling.patch [bz#1632622]
- kvm-aio-posix-do-skip-system-call-if-ctx-notifier-pollin.patch [bz#1632622]
- kvm-intel-iommu-send-PSI-always-even-if-across-PDEs.patch [bz#1450712]
- kvm-intel-iommu-remove-IntelIOMMUNotifierNode.patch [bz#1450712]
- kvm-intel-iommu-add-iommu-lock.patch [bz#1450712]
- kvm-intel-iommu-only-do-page-walk-for-MAP-notifiers.patch [bz#1450712]
- kvm-intel-iommu-introduce-vtd_page_walk_info.patch [bz#1450712]
- kvm-intel-iommu-pass-in-address-space-when-page-walk.patch [bz#1450712]
- kvm-intel-iommu-trace-domain-id-during-page-walk.patch [bz#1450712]
- kvm-util-implement-simple-iova-tree.patch [bz#1450712]
- kvm-intel-iommu-rework-the-page-walk-logic.patch [bz#1450712]
- kvm-i386-define-the-ssbd-CPUID-feature-bit-CVE-2018-3639.patch [bz#1633928]
- Resolves: bz#1450712
  (Booting nested guest with vIOMMU, the assigned network devices can not receive packets (qemu))
- Resolves: bz#1552663
  (81-kvm-rhel.rules is no longer part of initscripts)
- Resolves: bz#1609235
  (Win2016 guest can't recognize pc-dimm hotplugged to node 0)
- Resolves: bz#1623085
  (VM doesn't boot from HD)
- Resolves: bz#1632622
  (~40% virtio_blk disk performance drop for win2012r2 guest when comparing qemu-kvm-rhev-2.12.0-9 with qemu-kvm-rhev-2.12.0-12)
- Resolves: bz#1633928
  (CVE-2018-3639 qemu-kvm: hw: cpu: speculative store bypass [rhel-8.0])

* Fri Oct 12 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-37.el8
- kvm-block-for-jobs-do-not-clear-user_paused-until-after-.patch [bz#1635583]
- kvm-iotests-Add-failure-matching-to-common.qemu.patch [bz#1635583]
- kvm-block-iotest-to-catch-abort-on-forced-blockjob-cance.patch [bz#1635583]
- Resolves: bz#1635583
  (Quitting VM causes qemu core dump once the block mirror job paused for no enough target space)

* Fri Oct 12 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - qemu-kvm-2.12.0-36
- kvm-check-Only-test-ivshm-when-it-is-compiled-in.patch [bz#1621817]
- kvm-Disable-ivshmem.patch [bz#1621817]
- kvm-mirror-Fail-gracefully-for-source-target.patch [bz#1637963]
- kvm-commit-Add-top-node-base-node-options.patch [bz#1637970]
- kvm-qemu-iotests-Test-commit-with-top-node-base-node.patch [bz#1637970]
- Resolves: bz#1621817
  (Disable IVSHMEM in RHEL 8)
- Resolves: bz#1637963
  (Segfault on 'blockdev-mirror' with same node as source and target)
- Resolves: bz#1637970
  (allow using node-names with block-commit)

* Thu Oct 11 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-35.el8
- kvm-redhat-make-the-plugins-executable.patch [bz#1638304]
- Resolves: bz#1638304
  (the driver packages lack all the library Requires)

* Thu Oct 11 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-34.el8
- kvm-seccomp-allow-sched_setscheduler-with-SCHED_IDLE-pol.patch [bz#1618356]
- kvm-seccomp-use-SIGSYS-signal-instead-of-killing-the-thr.patch [bz#1618356]
- kvm-seccomp-prefer-SCMP_ACT_KILL_PROCESS-if-available.patch [bz#1618356]
- kvm-configure-require-libseccomp-2.2.0.patch [bz#1618356]
- kvm-seccomp-set-the-seccomp-filter-to-all-threads.patch [bz#1618356]
- kvm-memory-cleanup-side-effects-of-memory_region_init_fo.patch [bz#1600365]
- Resolves: bz#1600365
  (QEMU core dumped when hotplug memory exceeding host hugepages and with discard-data=yes)
- Resolves: bz#1618356
  (qemu-kvm: Qemu: seccomp: blacklist is not applied to all threads [rhel-8])

* Fri Oct 05 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-33.el8
- kvm-migration-postcopy-Clear-have_listen_thread.patch [bz#1608765]
- kvm-migration-cleanup-in-error-paths-in-loadvm.patch [bz#1608765]
- kvm-jobs-change-start-callback-to-run-callback.patch [bz#1632939]
- kvm-jobs-canonize-Error-object.patch [bz#1632939]
- kvm-jobs-add-exit-shim.patch [bz#1632939]
- kvm-block-commit-utilize-job_exit-shim.patch [bz#1632939]
- kvm-block-mirror-utilize-job_exit-shim.patch [bz#1632939]
- kvm-jobs-utilize-job_exit-shim.patch [bz#1632939]
- kvm-block-backup-make-function-variables-consistently-na.patch [bz#1632939]
- kvm-jobs-remove-ret-argument-to-job_completed-privatize-.patch [bz#1632939]
- kvm-jobs-remove-job_defer_to_main_loop.patch [bz#1632939]
- kvm-block-commit-add-block-job-creation-flags.patch [bz#1632939]
- kvm-block-mirror-add-block-job-creation-flags.patch [bz#1632939]
- kvm-block-stream-add-block-job-creation-flags.patch [bz#1632939]
- kvm-block-commit-refactor-commit-to-use-job-callbacks.patch [bz#1632939]
- kvm-block-mirror-don-t-install-backing-chain-on-abort.patch [bz#1632939]
- kvm-block-mirror-conservative-mirror_exit-refactor.patch [bz#1632939]
- kvm-block-stream-refactor-stream-to-use-job-callbacks.patch [bz#1632939]
- kvm-tests-blockjob-replace-Blockjob-with-Job.patch [bz#1632939]
- kvm-tests-test-blockjob-remove-exit-callback.patch [bz#1632939]
- kvm-tests-test-blockjob-txn-move-.exit-to-.clean.patch [bz#1632939]
- kvm-jobs-remove-.exit-callback.patch [bz#1632939]
- kvm-qapi-block-commit-expose-new-job-properties.patch [bz#1632939]
- kvm-qapi-block-mirror-expose-new-job-properties.patch [bz#1632939]
- kvm-qapi-block-stream-expose-new-job-properties.patch [bz#1632939]
- kvm-block-backup-qapi-documentation-fixup.patch [bz#1632939]
- kvm-blockdev-document-transactional-shortcomings.patch [bz#1632939]
- Resolves: bz#1608765
  (After postcopy migration,  do savevm and loadvm, guest hang and call trace)
- Resolves: bz#1632939
  (qemu blockjobs other than backup do not support job-finalize or job-dismiss)

* Fri Sep 28 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-32.el8
- kvm-Re-enable-disabled-Hyper-V-enlightenments.patch [bz#1625185]
- kvm-Fix-annocheck-issues.patch [bz#1624164]
- kvm-exec-check-that-alignment-is-a-power-of-two.patch [bz#1630746]
- kvm-curl-Make-sslverify-off-disable-host-as-well-as-peer.patch [bz#1575925]
- Resolves: bz#1575925
  ("SSL: no alternative certificate subject name matches target host name" error even though sslverify = off)
- Resolves: bz#1624164
  (Review annocheck distro flag failures in qemu-kvm)
- Resolves: bz#1625185
  (Re-enable disabled Hyper-V enlightenments)
- Resolves: bz#1630746
  (qemu_ram_mmap: Assertion `is_power_of_2(align)' failed)

* Tue Sep 11 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-31.el8
- kvm-i386-Disable-TOPOEXT-by-default-on-cpu-host.patch [bz#1619804]
- kvm-redhat-enable-opengl-add-build-and-runtime-deps.patch [bz#1618412]
- Resolves: bz#1618412
  (Enable opengl (for intel vgpu display))
- Resolves: bz#1619804
  (kernel panic in init_amd_cacheinfo)

* Wed Sep 05 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-30.el8
- kvm-redhat-Disable-vhost-crypto.patch [bz#1625668]
- Resolves: bz#1625668
  (Decide if we should disable 'vhost-crypto' or not)

* Wed Sep 05 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-29.el8
- kvm-target-i386-sev-fix-memory-leaks.patch [bz#1615717]
- kvm-i386-Fix-arch_query_cpu_model_expansion-leak.patch [bz#1615717]
- kvm-redhat-Update-build-configuration.patch [bz#1573156]
- Resolves: bz#1573156
  (Update build configure for QEMU 2.12.0)
- Resolves: bz#1615717
  (Memory leaks)

* Wed Aug 29 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-27.el8
- kvm-Fix-libusb-1.0.22-deprecated-libusb_set_debug-with-l.patch [bz#1622656]
- Resolves: bz#1622656
  (qemu-kvm fails to build due to libusb_set_debug being deprecated)

* Fri Aug 17 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-26.el8
- kvm-redhat-remove-extra-in-rhel_rhev_conflicts-macro.patch [bz#1618752]
- Resolves: bz#1618752
  (qemu-kvm can't be installed in RHEL-8 as it Conflicts with itself.)

* Thu Aug 16 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-25.el8
- kvm-Migration-TLS-Fix-crash-due-to-double-cleanup.patch [bz#1594384]
- Resolves: bz#1594384
  (2.12 migration fixes)

* Tue Aug 14 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-24.el8
- kvm-Add-qemu-keymap-to-qemu-kvm-common.patch [bz#1593117]
- Resolves: bz#1593117
  (add qemu-keymap utility)

* Fri Aug 10 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-23.el8
- Fixing an issue with some old command in the spec file

* Fri Aug 10 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-22.el8
- Fix an issue with the build_configure script.
- Resolves: bz#1425820
  (Improve QEMU packaging layout with modularization of the block layer)


* Fri Aug 10 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-20.el8
- kvm-migration-stop-compressing-page-in-migration-thread.patch [bz#1594384]
- kvm-migration-stop-compression-to-allocate-and-free-memo.patch [bz#1594384]
- kvm-migration-stop-decompression-to-allocate-and-free-me.patch [bz#1594384]
- kvm-migration-detect-compression-and-decompression-error.patch [bz#1594384]
- kvm-migration-introduce-control_save_page.patch [bz#1594384]
- kvm-migration-move-some-code-to-ram_save_host_page.patch [bz#1594384]
- kvm-migration-move-calling-control_save_page-to-the-comm.patch [bz#1594384]
- kvm-migration-move-calling-save_zero_page-to-the-common-.patch [bz#1594384]
- kvm-migration-introduce-save_normal_page.patch [bz#1594384]
- kvm-migration-remove-ram_save_compressed_page.patch [bz#1594384]
- kvm-migration-block-dirty-bitmap-fix-memory-leak-in-dirt.patch [bz#1594384]
- kvm-migration-fix-saving-normal-page-even-if-it-s-been-c.patch [bz#1594384]
- kvm-migration-update-index-field-when-delete-or-qsort-RD.patch [bz#1594384]
- kvm-migration-introduce-decompress-error-check.patch [bz#1594384]
- kvm-migration-Don-t-activate-block-devices-if-using-S.patch [bz#1594384]
- kvm-migration-not-wait-RDMA_CM_EVENT_DISCONNECTED-event-.patch [bz#1594384]
- kvm-migration-block-dirty-bitmap-fix-dirty_bitmap_load.patch [bz#1594384]
- kvm-s390x-add-RHEL-7.6-machine-type-for-ccw.patch [bz#1595718]
- kvm-s390x-cpumodel-default-enable-bpb-and-ppa15-for-z196.patch [bz#1595718]
- kvm-linux-headers-asm-s390-kvm.h-header-sync.patch [bz#1612938]
- kvm-s390x-kvm-add-etoken-facility.patch [bz#1612938]
- Resolves: bz#1594384
  (2.12 migration fixes)
- Resolves: bz#1595718
  (Add ppa15/bpb to the default cpu model for z196 and higher in the 7.6 s390-ccw-virtio machine)
- Resolves: bz#1612938
  (Add etoken support to qemu-kvm for s390x KVM guests)

* Fri Aug 10 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-18.el8
  Mass import from RHEL 7.6 qemu-kvm-rhev, including fixes to the following BZs:

- kvm-AArch64-Add-virt-rhel7.6-machine-type.patch [bz#1558723]
- kvm-cpus-Fix-event-order-on-resume-of-stopped-guest.patch [bz#1566153]
- kvm-qemu-img-Check-post-truncation-size.patch [bz#1523065]
- kvm-vga-catch-depth-0.patch [bz#1575541]
- kvm-Fix-x-hv-max-vps-compat-value-for-7.4-machine-type.patch [bz#1583959]
- kvm-ccid-card-passthru-fix-regression-in-realize.patch [bz#1584984]
- kvm-Use-4-MB-vram-for-cirrus.patch [bz#1542080]
- kvm-spapr_pci-Remove-unhelpful-pagesize-warning.patch [bz#1505664]
- kvm-rpm-Add-nvme-VFIO-driver-to-rw-whitelist.patch [bz#1416180]
- kvm-qobject-Use-qobject_to-instead-of-type-cast.patch [bz#1557995]
- kvm-qobject-Ensure-base-is-at-offset-0.patch [bz#1557995]
- kvm-qobject-use-a-QObjectBase_-struct.patch [bz#1557995]
- kvm-qobject-Replace-qobject_incref-QINCREF-qobject_decre.patch [bz#1557995]
- kvm-qobject-Modify-qobject_ref-to-return-obj.patch [bz#1557995]
- kvm-rbd-Drop-deprecated-drive-parameter-filename.patch [bz#1557995]
- kvm-iscsi-Drop-deprecated-drive-parameter-filename.patch [bz#1557995]
- kvm-block-Add-block-specific-QDict-header.patch [bz#1557995]
- kvm-qobject-Move-block-specific-qdict-code-to-block-qdic.patch [bz#1557995]
- kvm-block-Fix-blockdev-for-certain-non-string-scalars.patch [bz#1557995]
- kvm-block-Fix-drive-for-certain-non-string-scalars.patch [bz#1557995]
- kvm-block-Clean-up-a-misuse-of-qobject_to-in-.bdrv_co_cr.patch [bz#1557995]
- kvm-block-Factor-out-qobject_input_visitor_new_flat_conf.patch [bz#1557995]
- kvm-block-Make-remaining-uses-of-qobject-input-visitor-m.patch [bz#1557995]
- kvm-block-qdict-Simplify-qdict_flatten_qdict.patch [bz#1557995]
- kvm-block-qdict-Tweak-qdict_flatten_qdict-qdict_flatten_.patch [bz#1557995]
- kvm-block-qdict-Clean-up-qdict_crumple-a-bit.patch [bz#1557995]
- kvm-block-qdict-Simplify-qdict_is_list-some.patch [bz#1557995]
- kvm-check-block-qdict-Rename-qdict_flatten-s-variables-f.patch [bz#1557995]
- kvm-check-block-qdict-Cover-flattening-of-empty-lists-an.patch [bz#1557995]
- kvm-block-Fix-blockdev-blockdev-add-for-empty-objects-an.patch [bz#1557995]
- kvm-rbd-New-parameter-auth-client-required.patch [bz#1557995]
- kvm-rbd-New-parameter-key-secret.patch [bz#1557995]
- kvm-block-mirror-honor-ratelimit-again.patch [bz#1572856]
- kvm-block-mirror-Make-cancel-always-cancel-pre-READY.patch [bz#1572856]
- kvm-iotests-Add-test-for-cancelling-a-mirror-job.patch [bz#1572856]
- kvm-iotests-Split-214-off-of-122.patch [bz#1518738]
- kvm-block-Add-COR-filter-driver.patch [bz#1518738]
- kvm-block-BLK_PERM_WRITE-includes-._UNCHANGED.patch [bz#1518738]
- kvm-block-Add-BDRV_REQ_WRITE_UNCHANGED-flag.patch [bz#1518738]
- kvm-block-Set-BDRV_REQ_WRITE_UNCHANGED-for-COR-writes.patch [bz#1518738]
- kvm-block-quorum-Support-BDRV_REQ_WRITE_UNCHANGED.patch [bz#1518738]
- kvm-block-Support-BDRV_REQ_WRITE_UNCHANGED-in-filters.patch [bz#1518738]
- kvm-iotests-Clean-up-wrap-image-in-197.patch [bz#1518738]
- kvm-iotests-Copy-197-for-COR-filter-driver.patch [bz#1518738]
- kvm-iotests-Add-test-for-COR-across-nodes.patch [bz#1518738]
- kvm-qemu-io-Use-purely-string-blockdev-options.patch [bz#1576598]
- kvm-qemu-img-Use-only-string-options-in-img_open_opts.patch [bz#1576598]
- kvm-iotests-Add-test-for-U-force-share-conflicts.patch [bz#1576598]
- kvm-qemu-io-Drop-command-functions-return-values.patch [bz#1519617]
- kvm-qemu-io-Let-command-functions-return-error-code.patch [bz#1519617]
- kvm-qemu-io-Exit-with-error-when-a-command-failed.patch [bz#1519617]
- kvm-iotests.py-Add-qemu_io_silent.patch [bz#1519617]
- kvm-iotests-Let-216-make-use-of-qemu-io-s-exit-code.patch [bz#1519617]
- kvm-qcow2-Repair-OFLAG_COPIED-when-fixing-leaks.patch [bz#1527085]
- kvm-iotests-Repairing-error-during-snapshot-deletion.patch [bz#1527085]
- kvm-block-Make-bdrv_is_writable-public.patch [bz#1588039]
- kvm-qcow2-Do-not-mark-inactive-images-corrupt.patch [bz#1588039]
- kvm-iotests-Add-case-for-a-corrupted-inactive-image.patch [bz#1588039]
- kvm-main-loop-drop-spin_counter.patch [bz#1168213]
- kvm-target-ppc-Factor-out-the-parsing-in-kvmppc_get_cpu_.patch [bz#1560847]
- kvm-target-ppc-Don-t-require-private-l1d-cache-on-POWER8.patch [bz#1560847]
- kvm-ppc-spapr_caps-Don-t-disable-cap_cfpc-on-POWER8-by-d.patch [bz#1560847]
- kvm-qxl-fix-local-renderer-crash.patch [bz#1567733]
- kvm-qemu-img-Amendment-support-implies-create_opts.patch [bz#1537956]
- kvm-block-Add-Error-parameter-to-bdrv_amend_options.patch [bz#1537956]
- kvm-qemu-option-Pull-out-Supported-options-print.patch [bz#1537956]
- kvm-qemu-img-Add-print_amend_option_help.patch [bz#1537956]
- kvm-qemu-img-Recognize-no-creation-support-in-o-help.patch [bz#1537956]
- kvm-iotests-Test-help-option-for-unsupporting-formats.patch [bz#1537956]
- kvm-iotests-Rework-113.patch [bz#1537956]
- kvm-qemu-img-Resolve-relative-backing-paths-in-rebase.patch [bz#1569835]
- kvm-iotests-Add-test-for-rebasing-with-relative-paths.patch [bz#1569835]
- kvm-qemu-img-Special-post-backing-convert-handling.patch [bz#1527898]
- kvm-iotests-Test-post-backing-convert-target-behavior.patch [bz#1527898]
- kvm-migration-calculate-expected_downtime-with-ram_bytes.patch [bz#1564576]
- kvm-sheepdog-Fix-sd_co_create_opts-memory-leaks.patch [bz#1513543]
- kvm-qemu-iotests-reduce-chance-of-races-in-185.patch [bz#1513543]
- kvm-blockjob-do-not-cancel-timer-in-resume.patch [bz#1513543]
- kvm-nfs-Fix-error-path-in-nfs_options_qdict_to_qapi.patch [bz#1513543]
- kvm-nfs-Remove-processed-options-from-QDict.patch [bz#1513543]
- kvm-blockjob-drop-block_job_pause-resume_all.patch [bz#1513543]
- kvm-blockjob-expose-error-string-via-query.patch [bz#1513543]
- kvm-blockjob-Fix-assertion-in-block_job_finalize.patch [bz#1513543]
- kvm-blockjob-Wrappers-for-progress-counter-access.patch [bz#1513543]
- kvm-blockjob-Move-RateLimit-to-BlockJob.patch [bz#1513543]
- kvm-blockjob-Implement-block_job_set_speed-centrally.patch [bz#1513543]
- kvm-blockjob-Introduce-block_job_ratelimit_get_delay.patch [bz#1513543]
- kvm-blockjob-Add-block_job_driver.patch [bz#1513543]
- kvm-blockjob-Update-block-job-pause-resume-documentation.patch [bz#1513543]
- kvm-blockjob-Improve-BlockJobInfo.offset-len-documentati.patch [bz#1513543]
- kvm-job-Create-Job-JobDriver-and-job_create.patch [bz#1513543]
- kvm-job-Rename-BlockJobType-into-JobType.patch [bz#1513543]
- kvm-job-Add-JobDriver.job_type.patch [bz#1513543]
- kvm-job-Add-job_delete.patch [bz#1513543]
- kvm-job-Maintain-a-list-of-all-jobs.patch [bz#1513543]
- kvm-job-Move-state-transitions-to-Job.patch [bz#1513543]
- kvm-job-Add-reference-counting.patch [bz#1513543]
- kvm-job-Move-cancelled-to-Job.patch [bz#1513543]
- kvm-job-Add-Job.aio_context.patch [bz#1513543]
- kvm-job-Move-defer_to_main_loop-to-Job.patch [bz#1513543]
- kvm-job-Move-coroutine-and-related-code-to-Job.patch [bz#1513543]
- kvm-job-Add-job_sleep_ns.patch [bz#1513543]
- kvm-job-Move-pause-resume-functions-to-Job.patch [bz#1513543]
- kvm-job-Replace-BlockJob.completed-with-job_is_completed.patch [bz#1513543]
- kvm-job-Move-BlockJobCreateFlags-to-Job.patch [bz#1513543]
- kvm-blockjob-Split-block_job_event_pending.patch [bz#1513543]
- kvm-job-Add-job_event_.patch [bz#1513543]
- kvm-job-Move-single-job-finalisation-to-Job.patch [bz#1513543]
- kvm-job-Convert-block_job_cancel_async-to-Job.patch [bz#1513543]
- kvm-job-Add-job_drain.patch [bz#1513543]
- kvm-job-Move-.complete-callback-to-Job.patch [bz#1513543]
- kvm-job-Move-job_finish_sync-to-Job.patch [bz#1513543]
- kvm-job-Switch-transactions-to-JobTxn.patch [bz#1513543]
- kvm-job-Move-transactions-to-Job.patch [bz#1513543]
- kvm-job-Move-completion-and-cancellation-to-Job.patch [bz#1513543]
- kvm-block-Cancel-job-in-bdrv_close_all-callers.patch [bz#1513543]
- kvm-job-Add-job_yield.patch [bz#1513543]
- kvm-job-Add-job_dismiss.patch [bz#1513543]
- kvm-job-Add-job_is_ready.patch [bz#1513543]
- kvm-job-Add-job_transition_to_ready.patch [bz#1513543]
- kvm-job-Move-progress-fields-to-Job.patch [bz#1513543]
- kvm-job-Introduce-qapi-job.json.patch [bz#1513543]
- kvm-job-Add-JOB_STATUS_CHANGE-QMP-event.patch [bz#1513543]
- kvm-job-Add-lifecycle-QMP-commands.patch [bz#1513543]
- kvm-job-Add-query-jobs-QMP-command.patch [bz#1513543]
- kvm-blockjob-Remove-BlockJob.driver.patch [bz#1513543]
- kvm-iotests-Move-qmp_to_opts-to-VM.patch [bz#1513543]
- kvm-qemu-iotests-Test-job-with-block-jobs.patch [bz#1513543]
- kvm-vdi-Fix-vdi_co_do_create-return-value.patch [bz#1513543]
- kvm-vhdx-Fix-vhdx_co_create-return-value.patch [bz#1513543]
- kvm-job-Add-error-message-for-failing-jobs.patch [bz#1513543]
- kvm-block-create-Make-x-blockdev-create-a-job.patch [bz#1513543]
- kvm-qemu-iotests-Add-VM.get_qmp_events_filtered.patch [bz#1513543]
- kvm-qemu-iotests-Add-VM.qmp_log.patch [bz#1513543]
- kvm-qemu-iotests-Add-iotests.img_info_log.patch [bz#1513543]
- kvm-qemu-iotests-Add-VM.run_job.patch [bz#1513543]
- kvm-qemu-iotests-iotests.py-helper-for-non-file-protocol.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-206-for-blockdev-create-job.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-207-for-blockdev-create-job.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-210-for-blockdev-create-job.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-211-for-blockdev-create-job.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-212-for-blockdev-create-job.patch [bz#1513543]
- kvm-qemu-iotests-Rewrite-213-for-blockdev-create-job.patch [bz#1513543]
- kvm-block-create-Mark-blockdev-create-stable.patch [bz#1513543]
- kvm-jobs-fix-stale-wording.patch [bz#1513543]
- kvm-jobs-fix-verb-references-in-docs.patch [bz#1513543]
- kvm-iotests-Fix-219-s-timing.patch [bz#1513543]
- kvm-iotests-improve-pause_job.patch [bz#1513543]
- kvm-rpm-Whitelist-copy-on-read-block-driver.patch [bz#1518738]
- kvm-rpm-add-throttle-driver-to-rw-whitelist.patch [bz#1591076]
- kvm-usb-host-skip-open-on-pending-postload-bh.patch [bz#1572851]
- kvm-i386-Define-the-Virt-SSBD-MSR-and-handling-of-it-CVE.patch [bz#1574216]
- kvm-i386-define-the-AMD-virt-ssbd-CPUID-feature-bit-CVE-.patch [bz#1574216]
- kvm-block-file-posix-Pass-FD-to-locking-helpers.patch [bz#1519144]
- kvm-block-file-posix-File-locking-during-creation.patch [bz#1519144]
- kvm-iotests-Add-creation-test-to-153.patch [bz#1519144]
- kvm-vhost-user-add-Net-prefix-to-internal-state-structur.patch [bz#1526645]
- kvm-virtio-support-setting-memory-region-based-host-noti.patch [bz#1526645]
- kvm-vhost-user-support-receiving-file-descriptors-in-sla.patch [bz#1526645]
- kvm-osdep-add-wait.h-compat-macros.patch [bz#1526645]
- kvm-vhost-user-bridge-support-host-notifier.patch [bz#1526645]
- kvm-vhost-allow-backends-to-filter-memory-sections.patch [bz#1526645]
- kvm-vhost-user-allow-slave-to-send-fds-via-slave-channel.patch [bz#1526645]
- kvm-vhost-user-introduce-shared-vhost-user-state.patch [bz#1526645]
- kvm-vhost-user-support-registering-external-host-notifie.patch [bz#1526645]
- kvm-libvhost-user-support-host-notifier.patch [bz#1526645]
- kvm-block-Introduce-API-for-copy-offloading.patch [bz#1482537]
- kvm-raw-Check-byte-range-uniformly.patch [bz#1482537]
- kvm-raw-Implement-copy-offloading.patch [bz#1482537]
- kvm-qcow2-Implement-copy-offloading.patch [bz#1482537]
- kvm-file-posix-Implement-bdrv_co_copy_range.patch [bz#1482537]
- kvm-iscsi-Query-and-save-device-designator-when-opening.patch [bz#1482537]
- kvm-iscsi-Create-and-use-iscsi_co_wait_for_task.patch [bz#1482537]
- kvm-iscsi-Implement-copy-offloading.patch [bz#1482537]
- kvm-block-backend-Add-blk_co_copy_range.patch [bz#1482537]
- kvm-qemu-img-Convert-with-copy-offloading.patch [bz#1482537]
- kvm-qcow2-Fix-src_offset-in-copy-offloading.patch [bz#1482537]
- kvm-iscsi-Don-t-blindly-use-designator-length-in-respons.patch [bz#1482537]
- kvm-file-posix-Fix-EINTR-handling.patch [bz#1482537]
- kvm-usb-storage-Add-rerror-werror-properties.patch [bz#1595180]
- kvm-numa-clarify-error-message-when-node-index-is-out-of.patch [bz#1578381]
- kvm-qemu-iotests-Update-026.out.nocache-reference-output.patch [bz#1528541]
- kvm-qcow2-Free-allocated-clusters-on-write-error.patch [bz#1528541]
- kvm-qemu-iotests-Test-qcow2-not-leaking-clusters-on-writ.patch [bz#1528541]
- kvm-qemu-options-Add-missing-newline-to-accel-help-text.patch [bz#1586313]
- kvm-xhci-fix-guest-triggerable-assert.patch [bz#1594135]
- kvm-virtio-gpu-tweak-scanout-disable.patch [bz#1589634]
- kvm-virtio-gpu-update-old-resource-too.patch [bz#1589634]
- kvm-virtio-gpu-disable-scanout-when-backing-resource-is-.patch [bz#1589634]
- kvm-block-Don-t-silently-truncate-node-names.patch [bz#1549654]
- kvm-pr-helper-fix-socket-path-default-in-help.patch [bz#1533158]
- kvm-pr-helper-fix-assertion-failure-on-failed-multipath-.patch [bz#1533158]
- kvm-pr-manager-helper-avoid-SIGSEGV-when-writing-to-the-.patch [bz#1533158]
- kvm-pr-manager-put-stubs-in-.c-file.patch [bz#1533158]
- kvm-pr-manager-add-query-pr-managers-QMP-command.patch [bz#1533158]
- kvm-pr-manager-helper-report-event-on-connection-disconn.patch [bz#1533158]
- kvm-pr-helper-avoid-error-on-PR-IN-command-with-zero-req.patch [bz#1533158]
- kvm-pr-helper-Rework-socket-path-handling.patch [bz#1533158]
- kvm-pr-manager-helper-fix-memory-leak-on-event.patch [bz#1533158]
- kvm-object-fix-OBJ_PROP_LINK_UNREF_ON_RELEASE-ambivalenc.patch [bz#1556678]
- kvm-usb-hcd-xhci-test-add-a-test-for-ccid-hotplug.patch [bz#1556678]
- kvm-Revert-usb-release-the-created-buses.patch [bz#1556678]
- kvm-file-posix-Fix-creation-locking.patch [bz#1599335]
- kvm-file-posix-Unlock-FD-after-creation.patch [bz#1599335]
- kvm-ahci-trim-signatures-on-raise-lower.patch [bz#1584914]
- kvm-ahci-fix-PxCI-register-race.patch [bz#1584914]
- kvm-ahci-don-t-schedule-unnecessary-BH.patch [bz#1584914]
- kvm-qcow2-Fix-qcow2_truncate-error-return-value.patch [bz#1595173]
- kvm-block-Convert-.bdrv_truncate-callback-to-coroutine_f.patch [bz#1595173]
- kvm-qcow2-Remove-coroutine-trampoline-for-preallocate_co.patch [bz#1595173]
- kvm-block-Move-bdrv_truncate-implementation-to-io.c.patch [bz#1595173]
- kvm-block-Use-tracked-request-for-truncate.patch [bz#1595173]
- kvm-file-posix-Make-.bdrv_co_truncate-asynchronous.patch [bz#1595173]
- kvm-block-Fix-copy-on-read-crash-with-partial-final-clus.patch [bz#1590640]
- kvm-block-fix-QEMU-crash-with-scsi-hd-and-drive_del.patch [bz#1599515]
- kvm-virtio-rng-process-pending-requests-on-DRIVER_OK.patch [bz#1576743]
- kvm-file-posix-specify-expected-filetypes.patch [bz#1525829]
- kvm-iotests-add-test-226-for-file-driver-types.patch [bz#1525829]
- kvm-block-dirty-bitmap-add-lock-to-bdrv_enable-disable_d.patch [bz#1207657]
- kvm-qapi-add-x-block-dirty-bitmap-enable-disable.patch [bz#1207657]
- kvm-qmp-transaction-support-for-x-block-dirty-bitmap-ena.patch [bz#1207657]
- kvm-qapi-add-x-block-dirty-bitmap-merge.patch [bz#1207657]
- kvm-qapi-add-disabled-parameter-to-block-dirty-bitmap-ad.patch [bz#1207657]
- kvm-block-dirty-bitmap-add-bdrv_enable_dirty_bitmap_lock.patch [bz#1207657]
- kvm-dirty-bitmap-fix-double-lock-on-bitmap-enabling.patch [bz#1207657]
- kvm-block-qcow2-bitmap-fix-free_bitmap_clusters.patch [bz#1207657]
- kvm-qcow2-add-overlap-check-for-bitmap-directory.patch [bz#1207657]
- kvm-blockdev-enable-non-root-nodes-for-backup-source.patch [bz#1207657]
- kvm-iotests-add-222-to-test-basic-fleecing.patch [bz#1207657]
- kvm-qcow2-Remove-dead-check-on-ret.patch [bz#1207657]
- kvm-block-Move-request-tracking-to-children-in-copy-offl.patch [bz#1207657]
- kvm-block-Fix-parameter-checking-in-bdrv_co_copy_range_i.patch [bz#1207657]
- kvm-block-Honour-BDRV_REQ_NO_SERIALISING-in-copy-range.patch [bz#1207657]
- kvm-backup-Use-copy-offloading.patch [bz#1207657]
- kvm-block-backup-disable-copy-offloading-for-backup.patch [bz#1207657]
- kvm-iotests-222-Don-t-run-with-luks.patch [bz#1207657]
- kvm-block-io-fix-copy_range.patch [bz#1207657]
- kvm-block-split-flags-in-copy_range.patch [bz#1207657]
- kvm-block-add-BDRV_REQ_SERIALISING-flag.patch [bz#1207657]
- kvm-block-backup-fix-fleecing-scheme-use-serialized-writ.patch [bz#1207657]
- kvm-nbd-server-Reject-0-length-block-status-request.patch [bz#1207657]
- kvm-nbd-server-fix-trace.patch [bz#1207657]
- kvm-nbd-server-refactor-NBDExportMetaContexts.patch [bz#1207657]
- kvm-nbd-server-add-nbd_meta_empty_or_pattern-helper.patch [bz#1207657]
- kvm-nbd-server-implement-dirty-bitmap-export.patch [bz#1207657]
- kvm-qapi-new-qmp-command-nbd-server-add-bitmap.patch [bz#1207657]
- kvm-docs-interop-add-nbd.txt.patch [bz#1207657]
- kvm-nbd-server-introduce-NBD_CMD_CACHE.patch [bz#1207657]
- kvm-nbd-server-Silence-gcc-false-positive.patch [bz#1207657]
- kvm-nbd-server-Fix-dirty-bitmap-logic-regression.patch [bz#1207657]
- kvm-nbd-server-fix-nbd_co_send_block_status.patch [bz#1207657]
- kvm-nbd-client-Add-x-dirty-bitmap-to-query-bitmap-from-s.patch [bz#1207657]
- kvm-iotests-New-test-223-for-exporting-dirty-bitmap-over.patch [bz#1207657]
- kvm-hw-char-serial-Only-retry-if-qemu_chr_fe_write-retur.patch [bz#1592817]
- kvm-hw-char-serial-retry-write-if-EAGAIN.patch [bz#1592817]
- kvm-throttle-groups-fix-hang-when-group-member-leaves.patch [bz#1535914]
- kvm-Disable-aarch64-devices-reappeared-after-2.12-rebase.patch [bz#1586357]
- kvm-Disable-split-irq-device.patch [bz#1586357]
- kvm-Disable-AT24Cx-i2c-eeprom.patch [bz#1586357]
- kvm-Disable-CAN-bus-devices.patch [bz#1586357]
- kvm-Disable-new-superio-devices.patch [bz#1586357]
- kvm-Disable-new-pvrdma-device.patch [bz#1586357]
- kvm-qdev-add-HotplugHandler-post_plug-callback.patch [bz#1607891]
- kvm-virtio-scsi-fix-hotplug-reset-vs-event-race.patch [bz#1607891]
- kvm-e1000-Fix-tso_props-compat-for-82540em.patch [bz#1608778]
- kvm-slirp-correct-size-computation-while-concatenating-m.patch [bz#1586255]
- kvm-s390x-sclp-fix-maxram-calculation.patch [bz#1595740]
- kvm-redhat-Make-gitpublish-profile-the-default-one.patch [bz#1425820]
- Resolves: bz#1168213
  (main-loop: WARNING: I/O thread spun for 1000 iterations while doing stream block device.)
- Resolves: bz#1207657
  (RFE: QEMU Incremental live backup - push and pull modes)
- Resolves: bz#1416180
  (QEMU VFIO based block driver for NVMe devices)
- Resolves: bz#1425820
  (Improve QEMU packaging layout with modularization of the block layer)
- Resolves: bz#1482537
  ([RFE] qemu-img copy-offloading (convert command))
- Resolves: bz#1505664
  ("qemu-kvm: System page size 0x1000000 is not enabled in page_size_mask (0x11000). Performance may be slow" show up while using hugepage as guest's memory)
- Resolves: bz#1513543
  ([RFE] Add block job to create format on a storage device)
- Resolves: bz#1518738
  (Add 'copy-on-read' filter driver for use with blockdev-add)
- Resolves: bz#1519144
  (qemu-img: image locking doesn't cover image creation)
- Resolves: bz#1519617
  (The exit code should be non-zero when qemu-io reports an error)
- Resolves: bz#1523065
  ("qemu-img resize" should fail to decrease the size of logical partition/lvm/iSCSI image with raw format)
- Resolves: bz#1525829
  (can not boot up a scsi-block passthrough disk via -blockdev with error "cannot get SG_IO version number: Operation not supported.  Is this a SCSI device?")
- Resolves: bz#1526645
  ([Intel 7.6 FEAT] vHost Data Plane Acceleration (vDPA) - vhost user client - qemu-kvm-rhev)
- Resolves: bz#1527085
  (The copied flag should be updated during  '-r leaks')
- Resolves: bz#1527898
  ([RFE] qemu-img should leave cluster unallocated if it's read as zero throughout the backing chain)
- Resolves: bz#1528541
  (qemu-img check reports tons of leaked clusters after re-start nfs service to resume writing data in guest)
- Resolves: bz#1533158
  (QEMU support for libvirtd restarting qemu-pr-helper)
- Resolves: bz#1535914
  (Disable io throttling for one member disk of a group during io will induce the other one hang with io)
- Resolves: bz#1537956
  (RFE: qemu-img amend should list the true supported options)
- Resolves: bz#1542080
  (Qemu core dump at cirrus_invalidate_region)
- Resolves: bz#1549654
  (Reject node-names which would be truncated by the block layer commands)
- Resolves: bz#1556678
  (Hot plug usb-ccid for the 2nd time with the same ID as the 1st time failed)
- Resolves: bz#1557995
  (QAPI schema for RBD storage misses the 'password-secret' option)
- Resolves: bz#1558723
  (Create RHEL-7.6 QEMU machine type for AArch64)
- Resolves: bz#1560847
  ([Power8][FW b0320a_1812.861][rhel7.5rc2 3.10.0-861.el7.ppc64le][qemu-kvm-{ma,rhev}-2.10.0-21.el7_5.1.ppc64le] KVM guest does not default to ori type flush even with pseries-rhel7.5.0-sxxm)
- Resolves: bz#1564576
  (Pegas 1.1 - Require to backport qemu-kvm patch that fixes expected_downtime calculation during migration)
- Resolves: bz#1566153
  (IOERROR pause code lost after resuming a VM while I/O error is still present)
- Resolves: bz#1567733
  (qemu abort when migrate during guest reboot)
- Resolves: bz#1569835
  (qemu-img get wrong backing file path after rebasing image with relative path)
- Resolves: bz#1572851
  (Core dumped after migration when with usb-host)
- Resolves: bz#1572856
  ('block-job-cancel' can not cancel a "drive-mirror" job)
- Resolves: bz#1574216
  (CVE-2018-3639 qemu-kvm-rhev: hw: cpu: speculative store bypass [rhel-7.6])
- Resolves: bz#1575541
  (qemu core dump while installing win10 guest)
- Resolves: bz#1576598
  (Segfault in qemu-io and qemu-img with -U --image-opts force-share=off)
- Resolves: bz#1576743
  (virtio-rng hangs when running on recent (2.x) QEMU versions)
- Resolves: bz#1578381
  (Error message need update when specify numa distance with node index >=128)
- Resolves: bz#1583959
  (Incorrect vcpu count limit for 7.4 machine types for windows guests)
- Resolves: bz#1584914
  (SATA emulator lags and hangs)
- Resolves: bz#1584984
  (Vm starts failed with 'passthrough' smartcard)
- Resolves: bz#1586255
  (CVE-2018-11806 qemu-kvm-rhev: QEMU: slirp: heap buffer overflow while reassembling fragmented datagrams [rhel-7.6])
- Resolves: bz#1586313
  (-smp option is not easily found in the output of qemu help)
- Resolves: bz#1586357
  (Disable new devices in 2.12)
- Resolves: bz#1588039
  (Possible assertion failure in qemu when a corrupted image is used during an incoming migration)
- Resolves: bz#1589634
  (Migration failed when rebooting guest with multiple virtio videos)
- Resolves: bz#1590640
  (qemu-kvm: block/io.c:1098: bdrv_co_do_copy_on_readv: Assertion `skip_bytes < pnum' failed.)
- Resolves: bz#1591076
  (The driver of 'throttle' is not whitelisted)
- Resolves: bz#1592817
  (Retrying on serial_xmit if the pipe is broken may compromise the Guest)
- Resolves: bz#1594135
  (system_reset many times linux guests cause qemu process Aborted)
- Resolves: bz#1595173
  (blockdev-create is blocking)
- Resolves: bz#1595180
  (Can't set rerror/werror with usb-storage)
- Resolves: bz#1595740
  (RHEL-Alt-7.6 - qemu has error during migration of larger guests)
- Resolves: bz#1599335
  (Image creation locking is too tight and is not properly released)
- Resolves: bz#1599515
  (qemu core-dump with aio_read via hmp (util/qemu-thread-posix.c:64: qemu_mutex_lock_impl: Assertion `mutex->initialized' failed))
- Resolves: bz#1607891
  (Hotplug events are sometimes lost with virtio-scsi + iothread)
- Resolves: bz#1608778
  (qemu/migration: migrate failed from RHEL.7.6 to RHEL.7.5 with e1000-82540em)

* Mon Aug 06 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-17.el8
- kvm-linux-headers-Update-to-include-KVM_CAP_S390_HPAGE_1.patch [bz#1610906]
- kvm-s390x-Enable-KVM-huge-page-backing-support.patch [bz#1610906]
- kvm-redhat-s390x-add-hpage-1-to-kvm.conf.patch [bz#1610906]
- Resolves: bz#1610906
  ([IBM 8.0 FEAT] KVM: Huge Pages - libhugetlbfs Enablement - qemu-kvm part)

* Tue Jul 31 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-16.el8
- kvm-spapr-Correct-inverted-test-in-spapr_pc_dimm_node.patch [bz#1601671]
- kvm-osdep-powerpc64-align-memory-to-allow-2MB-radix-THP-.patch [bz#1601317]
- kvm-RHEL-8.0-Add-pseries-rhel7.6.0-sxxm-machine-type.patch [bz#1595501]
- kvm-i386-Helpers-to-encode-cache-information-consistentl.patch [bz#1597739]
- kvm-i386-Add-cache-information-in-X86CPUDefinition.patch [bz#1597739]
- kvm-i386-Initialize-cache-information-for-EPYC-family-pr.patch [bz#1597739]
- kvm-i386-Add-new-property-to-control-cache-info.patch [bz#1597739]
- kvm-i386-Clean-up-cache-CPUID-code.patch [bz#1597739]
- kvm-i386-Populate-AMD-Processor-Cache-Information-for-cp.patch [bz#1597739]
- kvm-i386-Add-support-for-CPUID_8000_001E-for-AMD.patch [bz#1597739]
- kvm-i386-Fix-up-the-Node-id-for-CPUID_8000_001E.patch [bz#1597739]
- kvm-i386-Enable-TOPOEXT-feature-on-AMD-EPYC-CPU.patch [bz#1597739]
- kvm-i386-Remove-generic-SMT-thread-check.patch [bz#1597739]
- kvm-i386-Allow-TOPOEXT-to-be-enabled-on-older-kernels.patch [bz#1597739]
- Resolves: bz#1595501
  (Create pseries-rhel7.6.0-sxxm machine type)
- Resolves: bz#1597739
  (AMD EPYC/Zen SMT support for KVM / QEMU guest (qemu-kvm))
- Resolves: bz#1601317
  (RHEL8.0 - qemu patch to align memory to allow 2MB THP)
- Resolves: bz#1601671
  (After rebooting guest,all the hot plug memory will be assigned to the 1st numa node.)

* Tue Jul 24 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-15.el8
- kvm-spapr-Add-ibm-max-associativity-domains-property.patch [bz#1599593]
- kvm-Revert-spapr-Don-t-allow-memory-hotplug-to-memory-le.patch [bz#1599593]
- kvm-simpletrace-Convert-name-from-mapping-record-to-str.patch [bz#1594969]
- kvm-tests-fix-TLS-handshake-failure-with-TLS-1.3.patch [bz#1602403]
- Resolves: bz#1594969
  (simpletrace.py fails when running with Python 3)
- Resolves: bz#1599593
  (User can't hotplug memory to less memory numa node on rhel8)
- Resolves: bz#1602403
  (test-crypto-tlssession unit test fails with assertions)

* Mon Jul 09 2018 Danilo Cesar Lemes de Paula <ddepaula@redhat.com> - 2.12.0-14.el8
- kvm-vfio-pci-Default-display-option-to-off.patch [bz#1590511]
- kvm-python-futurize-f-libfuturize.fixes.fix_print_with_i.patch [bz#1571533]
- kvm-python-futurize-f-lib2to3.fixes.fix_except.patch [bz#1571533]
- kvm-Revert-Defining-a-shebang-for-python-scripts.patch [bz#1571533]
- kvm-spec-Fix-ambiguous-python-interpreter-name.patch [bz#1571533]
- kvm-qemu-ga-blacklisting-guest-exec-and-guest-exec-statu.patch [bz#1518132]
- kvm-redhat-rewrap-build_configure.sh-cmdline-for-the-rh-.patch []
- kvm-redhat-remove-the-VTD-LIVE_BLOCK_OPS-and-RHV-options.patch []
- kvm-redhat-fix-the-rh-env-prep-target-s-dependency-on-th.patch []
- kvm-redhat-remove-dead-code-related-to-s390-not-s390x.patch []
- kvm-redhat-sync-compiler-flags-from-the-spec-file-to-rh-.patch []
- kvm-redhat-sync-guest-agent-enablement-and-tcmalloc-usag.patch []
- kvm-redhat-fix-up-Python-3-dependency-for-building-QEMU.patch []
- kvm-redhat-fix-up-Python-dependency-for-SRPM-generation.patch []
- kvm-redhat-disable-glusterfs-dependency-support-temporar.patch []
- Resolves: bz#1518132
  (Ensure file access RPCs are disabled by default)
- Resolves: bz#1571533
  (Convert qemu-kvm python scripts to python3)
- Resolves: bz#1590511
  (Fails to start guest with Intel vGPU device)

* Thu Jun 21 2018 Danilo C. L. de Paula <ddepaula@redhat.com> - 2.12.0-13.el8
- Resolves: bz#1508137
  ([IBM 8.0 FEAT] KVM: Interactive Bootloader (qemu))
- Resolves: bz#1513558
  (Remove RHEL6 machine types)
- Resolves: bz#1568600
  (pc-i440fx-rhel7.6.0 and pc-q35-rhel7.6.0 machine types (x86))
- Resolves: bz#1570029
  ([IBM 8.0 FEAT] KVM: 3270 Connectivity - qemu part)
- Resolves: bz#1578855
  (Enable Native Ceph support on non x86_64 CPUs)
- Resolves: bz#1585651
  (RHEL 7.6 new pseries machine type (ppc64le))
- Resolves: bz#1592337
  ([IBM 8.0 FEAT] KVM: CPU Model z14 ZR1 (qemu-kvm))

* Tue May 15 2018 Danilo C. L. de Paula <ddepaula@redhat.com> - 2.12.0-11.el8.1
- Resolves: bz#1576468
  (Enable vhost_user in qemu-kvm 2.12)

* Wed May 09 2018 Danilo de Paula <ddepaula@redhat.com> - 2.12.0-11.el8
- Resolves: bz#1574406
  ([RHEL 8][qemu-kvm] Failed to find romfile "efi-virtio.rom")
- Resolves: bz#1569675
  (Backwards compatibility of pc-*-rhel7.5.0 and older machine-types)
- Resolves: bz#1576045
  (Fix build issue by using python3)
- Resolves: bz#1571145
  (qemu-kvm segfaults on RHEL 8 when run guestfsd under TCG)

* Fri Apr 20 2018 Danilo de Paula <ddepaula@redhat.com> - 2.12.0-10.el
- Fixing some issues with packaging.
- Rebasing to 2.12.0-rc4

* Fri Apr 13 2018 Danilo de Paula <ddepaula@redhat.com> - 2.11.0-7.el8
- Bumping epoch for RHEL8 and dropping self-obsoleting

* Thu Apr 12 2018 Danilo de Paula <ddepaula@redhat.com> - 2.11.0-6.el8
- Rebuilding

* Mon Mar 05 2018 Danilo de Paula <ddepaula@redhat.com> - 2.11.0-5.el8
- Prepare building on RHEL-8.0
