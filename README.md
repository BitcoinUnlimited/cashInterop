# cashInterop
Bitcoin Cash client interoperability testing. 

Three clients are used for InterOperability teseting
* [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)
* [Bitcoin-ABC](https://github.com/Bitcoin-ABC/bitcoin-abc)
* [Bitcoin-XT](https://github.com/bitcoinxt/bitcoinxt)

# Note: 
Building from source required to install package dependencies for the corresponding client first
For BU, please see the Quick installation instructions section in [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)

Setup
=================
1. Enter the following command for cashInterop project, which has submodules in it.
$ git clone https://github.com/username/cashInterop.git    (Replace username with your own github username)

2. Change directory to cashInterop, and enter the following command to initialize and fetch the submodules
$ git submodule update --init --recursive


Building Project
===================
1. Make sure all package dependencies are installed (see Quick installation instructions section in [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)

2. Building all three clients 
$ make all

3. Building individual client (i.e. bu, xt or abc)
$ make bu
$ make xt
$ make abc

4.Verify client executables (bitcoind and bitcoin-cli) are built successfully

$ ls -la bu/debug/src/bitcoin*
$ ls -la xt/debug/src/bitcoin*
$ ls -la abc/debug/src/bitcoin*
$ ls -la classic/debug/src/bitcoin*


# Note:  
Both BU and XT may fail to build because of missing package dependencies of libgoogle-perftools-dev, and libcurl4-openssl-dev respectively. Install the packages by using sudo apt-get install package-dependency-name-dev

1. Build requirements for BU need to install google perftools since gperf is enabled as shown Makefile
BU_CONF_FLAGS:=$(COMMON_CONF_FLAGS) --enable-gperf

$ sudo apt-get install libgoogle-perftools-dev

2. Build requirements for XT (see [build for Linux](https://github.com/bitcoinxt/bitcoinxt/blob/master/doc/build-unix.md)) 
$ sudo apt-get install libcurl4-openssl-dev
