# cashInterop
Three bitcoin clients are used for InterOperability testing

* [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)
* [Bitcoin-ABC](https://github.com/Bitcoin-ABC/bitcoin-abc)
* [Bitcoin-XT](https://github.com/bitcoinxt/bitcoinxt)


Setup
===========

1. Enter the following command for cashInterop project, which has submodules in it. Replace username with your github username

	```
	$ git clone https://github.com/username/cashInterop.git
	```

2. Change directory to cashInterop, and enter the following command to initialize and fetch the submodules 

	```
	$ git submodule update --init --recursive
	```

Dependencies
=====================
Make sure all package dependencies are installed (see Quick installation instructions section in [BitcoinUnlimited](https://github.com/BitcoinUnlimited/BitcoinUnlimited)). 

Both BU and XT may fail to build because of missing package dependencies of libgoogle-perftools-dev, and libcurl4-openssl-dev respectively. 

1. Since --enable-gperf is enabled in the Makefile for BU, install dependency by

	```
	$ sudo apt-get install libgoogle-perftools-dev
	```

2. Build requirements for XT

	```
	$ sudo apt-get install libcurl4-openssl-dev
	```
3. Download and install Base58 for converting bitcoin cash legacy addresses. ["base58-0.2.5-py3-none-any.whl"](https://pypi.python.org/pypi/base58)

	```
	$ sudo apt install python3-pip
	$ pip3 install base58-0.2.5-py3-none-any.whl
	```
Building Project
=====================
1. Building individual client (i.e. bu, xt or abc) 

	```
	$ make bu 
	$ make xt 
	$ make abc
	```

2. Building all three clients 

	```
	$ make all
	```

3. Verify client executables (bitcoind and bitcoin-cli) are built successfully within debug folder

	```
	$ ls -la bucash/debug/src/bitcoin* 
	$ ls -la xt/debug/src/bitcoin* 
	$ ls -la abc/debug/src/bitcoin* 
	```

Running tests
=================
1. All available tests are located in the test folder. 
Default folder location for storing bitcoin data and log files is set to /tmp/cashInterop

2. You can overwrite this location by using option --tmpdir=<folder_location>. Please note that no
space is allowed before and after the equal sign. 
Second example below creates folder "testlogs" in the same place as the script.

	```
	$ ./example_test.py --tmpdir=/tmp/logfolder
	$ ./example_test.py --tmpdir=testlogs
	```
