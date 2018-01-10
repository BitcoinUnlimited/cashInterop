# cashInterop
Bitcoin Cash client interoperability testing

Three clients are used for InterOperability testing

* [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)
* [Bitcoin-ABC](https://github.com/Bitcoin-ABC/bitcoin-abc)
* [Bitcoin-XT](https://github.com/bitcoinxt/bitcoinxt)


Setup
===========
Enter the following command for cashInterop project, which has submodules in it. 
	```elisp
	$ git clone https://github.com/username/cashInterop.git (Replace username with your own github username)
	```
Change directory to cashInterop, and enter the following command to initialize and fetch the submodules 
	```elisp
	$ git submodule update --init --recursive
	```
Building Project
=====================
Make sure all package dependencies are installed (see Quick installation instructions section in [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)

Building all three clients 
	```elisp
	$ make all
	```

Building individual client (i.e. bu, xt or abc) 
	```bash
	$ make bu 
	$ make xt 
	$ make abc
	```
4.Verify client executables (bitcoind and bitcoin-cli) are built successfully

	```bash
	$ ls -la bu/debug/src/bitcoin* 
	$ ls -la xt/debug/src/bitcoin* 
	$ ls -la abc/debug/src/bitcoin* 
	```

Note:
Both BU and XT may fail to build because of missing package dependencies of libgoogle-perftools-dev, and libcurl4-openssl-dev respectively. 

Build requirements for BU need to install google perftools since gperf is enabled 
as shown Makefile BU_CONF_FLAGS:=$(COMMON_CONF_FLAGS) --enable-gperf
	```elisp
	$ sudo apt-get install libgoogle-perftools-dev
	```

Build requirements for XT (see build for Linux) 
	```elisp
	$ sudo apt-get install libcurl4-openssl-dev
	```


