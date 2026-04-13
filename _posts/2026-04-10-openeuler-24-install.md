---
title: How to compile OpenGauss in OpenEuler 24.03
date: 2026-04-10 15:00:00 +0800
categories: [Tutorial]
tags: [gym, workout, fitness]
pin: false
---


I assume you have a Windows laptop as the host machine, and you are trying to install OpenEuler 24.03 as a virtual machine, then compile opengauss inside this VM. For performance, I recomend VMWare over VirtualBox, but if you just want a free and legal VM software, you can start with VirtualBox. This tutorial will help you install the necessary packages in the OpenEuler 24.03 virtual machine and navigate you to compile the opengauss database system from source code.

## Download the VM's iso file and install the VM in VMWare

First of all, you need to install VMWare Workstation Pro on your Windows host machine. You can pay for the pro version yourself, or easily find a free one on rutracker or somewhere. Anyway, you need to finish this installation by yourself and we can start adding OpenEuler 24.03 into VMWare.

Go to [OpenEuler Download Page](https://www.openeuler.org/en/download/) to download Offline Everything ISO. Install it in VMware Workstation. It has a graphical interface for installation. Make sure you create a root user and a regular user there. And it will log you in into a terminal. The system by default has no graphical user interface.

## Install a graphical user interface for the VM

Then we need to install a graphical user interface. There are no available groups like `Server with GUI` or `GNOME Desktop`, therefore we need to install gnome manually.

Use `dnf group list --hidden` to see what groups packages are available.

First check if the repos are all enabled. You should see `EPOL`, `OS`, `debuginfo`, `everything`, `source`, `update`, `update-source` repos.

```bash
dnf repolist --all
```

If any repo is not enabled, run `sudo dnf config-manager --enable EPOL` to enable it.

Make cache to see available packages.

```bash
sudo dnf clean all
sudo dnf makecache
sudo dnf group list
```

Install the `X Window System` as it is essential for any graphical user interface.

```bash
sudo dnf groupinstall "X Window System" -y
```

Install gnome core packages manually with the following commands.

```bash
sudo dnf install gdm gnome-shell gnome-terminal nautilus gnome-control-center gnome-settings-daemon gnome-session -y
```

Then enable the display manager.

```bash
sudo systemctl enable gdm
sudo systemctl set-default graphical.target
```

And reboot the VM with `sudo reboot`. You should see the gnome graphical user interface for log in. Congratulations!

## Install the VMWare tools

We need to copy and paste between the host machine and the VM, the easiest way is to install `open-vm-tools-desktop` with the following command.

```bash
sudo dnf install open-vm-tools-desktop -y
```

Then you should be able to copy and paste properly. The feature is only available after you have a graphical user interface. You can disply `XDG_SEESION_TYPE` to see what interface you are on. If you follow my instructions to install gnome, you should see `x11` for the output.

```bash
echo $XDG_SESSION_TYPE 
```

## Install general dependencies for development

Install the fundamental dependencies with the following command.

```bash
sudo dnf install -y gcc gcc-c++ libaio-devel ncurses-devel pam-devel libffi-devel \
    python3-devel libtool libtool-devel libtool-ltdl openssl-devel \
    bison python3-setuptools-rust lz4-devel flex glibc-devel patch readline-devel \
    libedit-devel libxml2-devel numactl-devel unixODBC-devel java-1.8.0-openjdk-devel \
    dkms
```


```bash
sudo dnf install -y gcc gcc-c++ glibc-devel glibc-static libstdc++-static \
    kernel-headers kernel-devel make automake libtool bison flex \
    texinfo gmp-devel mpfr-devel libmpc-devel isl-devel
```

Install development tools.

```bash
sudo dnf groupinstall "Development Tools"
```

Install Rust toolchain.

> The network can be a problem. Better to use a proxy on your host machine and turn ot Tun mode to proxy all the network traffic.
{: .prompt-warning }

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

Install cmake3.20.

```bash
wget https://cmake.org/files/v3.20/cmake-3.20.0-linux-x86_64.tar.gz
sudo tar -xzf cmake-3.20.0-linux-x86_64.tar.gz -C /usr/local
export CMAKEROOT=/usr/local/cmake-3.20.0-linux-x86_64
export PATH=$CMAKEROOT/bin:$PATH
```

## (Optional) Compile OpenGauss specific dependencies

> This section is optional because we can download the pre-compiled third-party libraries, which will be elaborated in the next section.
{: .prompt-warning }

OpenGauss requires gcc 10.3. The default gcc version carried by OpenEuler 24.03 is gcc 12.3.1.

```bash
# Download gcc 10.3 source code.
wget https://ftp.gnu.org/gnu/gcc/gcc-10.3.0/gcc-10.3.0.tar.gz
tar -xzf gcc-10.3.0.tar.gz
cd gcc-10.3.0

# patch the gcc includes, otherwise there is a header conflict
wget -O fixincludes.patch 'https://gcc.gnu.org/git/?p=gcc.git;a=patch;h=6bf383c37e6131a8e247e8a0997d55d65c830b6d'
patch -p1 < ./fixincludes.patch 

# Download dependencies and compile gcc 10.3.
./contrib/download_prerequisites
mkdir build && cd build
../configure --prefix=/opt/gcc/gcc10.3 --disable-multilib --enable-languages=c,c++ --disable-libstdcxx-pch
make -j$(nproc)
sudo make install
```

Configure the system to use gcc 10.3 and cmake 3.20 by setting the following environment variables in `~/.bashrc`.

```bash
export GCC_PATH=/opt/gcc/gcc10.3
export CC=$GCC_PATH/bin/gcc
export CXX=$GCC_PATH/bin/g++
export LD_LIBRARY_PATH=$GCC_PATH/lib64:$LD_LIBRARY_PATH
export PATH=$GCC_PATH/bin:$PATH
export CMAKEROOT=/usr/local/cmake-3.20.0-linux-x86_64
export PATH=$CMAKEROOT/bin:$PATH
```

Install the third-party libraries.

```bash
# install git-lfs
sudo dnf install git-lfs
git lfs install

# clone the third-party libraries
git clone https://atomgit.com/muyulinzhong/openGauss-third_party.git
```

Install pyyaml for the sysem python because build_all.sh requires this package.

```bash
sudo dnf install python3-pyyaml -y
```

Copy GCC 10.3 to openGauss-third_party/output/buildtools/. Building third-party libraries requires gcc10.3 to be present.

```bash
cd openGauss-third_party/output 
cp -r /opt/gcc/gcc10.3 output/buildtools/
```

Compile all the third-party components. This can take a very long time, at least several hours.

```bash
cd openGauss-third_party
cd build
sh build_all.sh
```



> It is possible to compile only part of the third-party components. You can choose what to compile with the following commands.
{: .prompt-tip }

```bash
# Compile the build tools
cd ../build_tools && sh build_tools.sh

# Compile platform-related components
cd ../platform/build && sh build_platform.sh

# Compile dependencies
cd ../dependency/build && sh build_dependency.sh

# Compile components
cd ../component/build && sh build_component.sh
```

Compile Python3.

```bash
cd openGauss-third_party/build_tools/python3
sh build.sh
```

## Compile the openGauss database system

To download the precompiled third-party tools we can run the following commands.

```bash
mkdir -p ~/opengauss_workspace
cd ~/opengauss_workspace

wget https://opengauss.obs.cn-south-1.myhuaweicloud.com/latest/binarylibs/gcc10.3/openGauss-third_party_binarylibs_openEuler_x86_64.tar.gz
tar -zxf openGauss-third_party_binarylibs_openEuler_x86_64.tar.gz

# Rename to binarylibs (standard name expected by build scripts)
mv openGauss-third_party_binarylibs_openEuler_x86_64 binarylibs
```

Clone and build openGauss-server using the pre-compiled BINARYLIBS.

```bash
git clone https://gitee.com/opengauss/openGauss-server.git
cd openGauss-server

# Use the following command to build a release/debug version.
sh build.sh -m release -3rd $BINARYLIBS
# sh build.sh -m debug -3rd $BINARYLIBS
```