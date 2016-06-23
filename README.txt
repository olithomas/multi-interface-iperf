To Install and use the Load Test Script, complete the following steps:
======================================================================
1) Install Python 2.7 64-bit
2) Install the packages listed in 'python_modules.txt' in the Dependencies folder. The syntax is such that pip can be used directly with the file
3) Install the pre-compiled binaries in the Dependencies folder for PyWin32 and PyCrypto packages (64-bit)
4) Copy the 'loadtest' folder to the 'site-packages' directory of the Python install (usually 'C:\Python27\Lib\site-packages\')
5) Make sure PYTHONPATH is correct and includes the site-packages directory (run the following in IDLE: import sys, print sys.path)
6)Copy the iperf binary (included) to a location included in the PATH environment variable, so it can be called from the script directly.
5) The TestLauncher.py file can be anywhere (save in the same place as the config file for easy calling of the script)
6) Connect the UEs, and rename the network connections in Windows to something logical (UE1, UE2, UE3 etc.)
7) Complete the config file as instructed (see the example config file)
8) Call the script in a command prompt (something like 'python TestLauncher.py config.ini')
9) Any problems contact me.
======================================================================
Oliver Thomas
07786622696
oliver.thomas@ee.co.uk