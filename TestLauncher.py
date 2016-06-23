#!/usr/local/bin/python2.7
# encoding: utf-8
'''
The Load Test Script - VERSION 1.0 - MAY 2014

Change history:
Version 0.1 - Jan 2014 - Basic UDP testing implemented. No logging
Version 1.0 - May 2014 - Full re-write of TestInstance, included support for logging and TCP tests and Ctrl-C test cancellation

TestLauncher -- Launch a new load test. Will perform any number of UE DL or UL tests to different FTP servers simultaneously.

TestLauncher is a CLI launcher for the Load Test suite. It is the entry point of the script.
The Load Test script will perform data testing with multiple handsets on the same machine. It was written after the author had enough of trying to 
manage the Windows Routing table plus multiple iPerf sessions when trying to test with multiple handsets - a not very enviable task if done manually!

To use the script, the user must pass the path to a valid configuration file as the only parameter to the script. (see ConfigExample.ini). This
configuration file contains all details necessary to form the iPerf test string and log into the FTP server.
The script will first obtain a list of the active interfaces and their IP addresses from the system using the Windows Management Instrumentation framework (WMI).
Using this information, plus the FTP server and test config entered by the user, it will then form the iPerf strings, and execute them on both the 
local machine and the remote server. As of version 1.0, logging is now supported as well as TCP testing!!

TestLauncher.py implements the following classes and methods:
__name__ == "__main__"
- This is the entry point to the script. When the Python interpreter starts to interpret the file, the global environment variable __name__ will equal 
__main__ and therefore the code in this block will execute. The code simply calls the System Exit function and in turn calls the main() function as argument.

main()
Handles command line arguments and exception handling. Calls the initialize() function with the path to the config file.

initialize()
Creates a new instance of SysEnvironment, then creates a new instance of TestInstance using the SysEnvironment instance, and the path to the config file.
Then runs the run_test() method of the newly created TestInstance object.

@author:     Oliver Thomas

@copyright:  2014 EE. All rights reserved.

@license:    Apache License 2.0

@contact:    oliver.thomas@ee.co.uk
@deffield    updated: 23/05/2014

'''

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import os
import sys

from loadtest.SysEnvironment import SysEnvironment
from loadtest.TestInstance import TestInstance


__all__ = []
__version__ = 1.0
__date__ = '2014-05-23'
__updated__ = '2014-05-23'

DEBUG = 1
TESTRUN = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Oli on %s.
  Copyright 2014 EE. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    if TESTRUN:
        '''
        Then statically define some location for the config file and call initialize()
        '''
        config_file = 'C:\\Users\\Oli\\Documents\\Dropbox\\Eclipse\\LoadTestSuite\\test1.ini'
        initialize(config_file)
        return 0
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="path", help="path to Test Config File test#.ini", metavar="path")
    
        # Process arguments
        args = parser.parse_args()
    
        config_file = args.path
    
        initialize(config_file)
        
        return 0
    except Exception, e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
    
def initialize(config_file):
    '''
    Instantiate SysEnvironment (which will hold current interface and IP address information)
    '''
    
    env = SysEnvironment()
    test = TestInstance(config_file, env)
    test.run_test()

if __name__ == "__main__":
    sys.exit(main())