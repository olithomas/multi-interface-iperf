<h1>Multi-Interface Iperf Wrapper for Python</h1>
<p>
This is a wrapper for <a href="https://sourceforge.net/projects/iperf/">IPERF</a> - a network throughput test tool - written in Python 2.7. This was developed to address a set of very specific problems to do with Mobile Network Testing using multiple mobile devices connected to the computer:
</p>
<ol>
<li>When testing with multiple mobile devices on the same machine, and where the IP addresses for each device are allocated via DHCP, it becomes combersome to manage those IP addresses when running the IPERF commands. The SysEnvironment.py class was written using the WMI API for Windows in order to dynamically query the allocated IP addresses and interface names at run-time and allow them to be used in the Iperf commands for the test without the user having to manually run ipconfig or something else to get them.</li>
<li>Running downlink throughput tests requires that the user is logged into the test server (somewhere on the network) in order to issue the iperf command. When testing with multiple devices this becomes un-manageable, and so this script automated this process using the Python Paramiko SSH library to log into the server and run the necessary commands.</li>
<li>iperf default logging is just to print the output to the console, which is unhelpful to say the least. This script records all the log output from both the server and local machine iperf instances, and saves them in properly named and structured text files.</li>
</ol>
<p>
In short - this script allows the user, by specifying a config file, to run multi-interface, fully logged, automated throughput tests in either the DL or UL with one click.
</p>
<p>
<h2>To Install and use the Load Test Script, complete the following steps:</h2>
<hr>
<ol>
<li>Install Python 2.7 64-bit</li>
<li>Install the packages listed in 'python_modules.txt' in the Dependencies folder. The syntax is such that pip can be used directly with the file</li>
<li>Install the pre-compiled binaries in the Dependencies folder for PyWin32 and PyCrypto packages (64-bit)</li>
<li>Copy the 'loadtest' folder to the 'site-packages' directory of the Python install (usually 'C:\Python27\Lib\site-packages\')</li>
<li>Make sure PYTHONPATH is correct and includes the site-packages directory (run the following in IDLE: import sys, print sys.path)</li>
<li>Copy the iperf binary (included) to a location included in the PATH environment variable, so it can be called from the script directly.</li>
<li>The TestLauncher.py file can be anywhere (save in the same place as the config file for easy calling of the script)</li>
<li>Connect the UEs, and rename the network connections in Windows to something logical (UE1, UE2, UE3 etc.)</li>
<li>Complete the config file as instructed (see the example config file)</li>
<li>Call the script in a command prompt (something like 'python TestLauncher.py config.ini')</li>
</ol>
