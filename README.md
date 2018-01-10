# cashInterop
Bitcoin Cash client interoperability testing

Three clients are used for InterOperability testing

* [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)
* [Bitcoin-ABC](https://github.com/Bitcoin-ABC/bitcoin-abc)
* [Bitcoin-XT](https://github.com/bitcoinxt/bitcoinxt)


Setup
===========

1. Enter the following command for cashInterop project, which has submodules in it.Replace username with your github username

	```
	$ git clone https://github.com/username/cashInterop.git
	```

2. Change directory to cashInterop, and enter the following command to initialize and fetch the submodules 

	```
	$ git submodule update --init --recursive
	```

Building Project
=====================
Make sure all package dependencies are installed (see Quick installation instructions section in [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)

1. Building all three clients 

	```
	$ make all
	```

2. Building individual client (i.e. bu, xt or abc) 

	```
	$ make bu 
	$ make xt 
	$ make abc
	```

3.Verify client executables (bitcoind and bitcoin-cli) are built successfully

	```
	$ ls -la bu/debug/src/bitcoin* 
	$ ls -la xt/debug/src/bitcoin* 
	$ ls -la abc/debug/src/bitcoin* 
	```

Note:
Both BU and XT may fail to build because of missing package dependencies of libgoogle-perftools-dev, and libcurl4-openssl-dev respectively. 

Since google perftools "gperf" is enabled in as shown in Makefile  
	```
	Makefile BU_CONF_FLAGS:=$(COMMON_CONF_FLAGS) --enable-gperf
	```
	```
	$ sudo apt-get install libgoogle-perftools-dev
	```

Build requirements for XT (see build for Linux) 
	```
	$ sudo apt-get install libcurl4-openssl-dev
	```


