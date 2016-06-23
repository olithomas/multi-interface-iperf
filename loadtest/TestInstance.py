'''
The Load Test Script - VERSION 1.0 - MAY 2014

Change history:
Version 0.1 - Jan 2014 - Basic UDP testing implemented. No logging
Version 1.0 - May 2014 - Full re-write of TestInstance, included support for logging and TCP tests and Ctrl-C test cancelation

loadtest.TestInstance  instantiates the TestConfig class which reads the config file. 
It also implements the run_test() method whereby the test is executed. 
The run_test() method uses Timer threads to set up each test according to the configuration.
Logging of iperf output on both client and server sides is supported.
UDP and TCP tests are supported.

TestInstance.py implements the TestInstance class and methods, as well as the run_ue_test thread target method.

TODO: For future developers:
- iperf is very CPU-hungary. Maybe use a different more integrated byte-slinging method??
- Improve the structure of the code. Very procedural and long-winded at the moment.
- Zero error handling at the moment. Frankly, I couldn't be arsed.
- Add Telnet support for servers??

@author: Oliver Thomas
'''

import subprocess
import time
import os
import logging
from datetime import datetime
from threading import Timer
from threading import Event

import paramiko

from loadtest.TestConfig import TestConfig

# Change to logging.DEBUG for development:
# Default (production) = WARNING
log_level = logging.WARNING

logging.basicConfig(level=log_level, format='(%(threadName)-10s) %(message)s',)
logging.getLogger('paramiko').setLevel(logging.WARNING)


class TestInstance(object): #{
    '''
    class TestInstance(object):
    Sub-class of:                    object
    Private instance variables:
        __config = Instance of TestConfig object, which generates a dict of all the UE configs from the file.
        __ue_configs = UE config dict obtained from the __config
        __globals = Global config dict obtained from the __config (contains default values defined in TestConfig if no [Globals] element is present)
        __env = SysEnvironment instance passed to the constructor. Contains the UE IP addresses.
        __interrupt_event = threading.Event for signalling a Ctrl-C event to the child threads from the main thread.
    
    Overview:
    TestInstance instantiates the TestConfig. It then loops for each UE config in the config file.
    In each loop it builds a test_config dict for use by the thread method.
    It then creates the Threads and adds them to a list, starting them all at the same time.
    The thread obnjects are Timers, with the 2nd phase test being delayed by t1 seconds (if needed)

    '''


    def __init__(self, config_file, env): #{
        '''
        Constructor:
            config_file = path string of the location and name of the config file to be parsed.
            env = SysEnvironment object containing computer network adapter current information
        '''
        self.__config = TestConfig(config_file)
        self.__ue_configs = self.__config.get_full_ue_configs()
        self.__globals = self.__config.get_globals()
        self.__env = env
        self.__interrupt_event = Event()
    #} End method __init__

    def run_test(self): #{
        ue_tests = []
        max_duration = 0
        is_logging = self.__globals['logging']
        
        # Set up test-specific log directories, if user indicated logging was needed:
        if is_logging: # User wants logging
            if not os.path.exists(self.__globals['logdir']): os.mkdir(self.__globals['logdir'])
            test_logs = 'LoadTestLogs_' + str(datetime.now().strftime('%d-%m-%Y_%H%M%S'))
            test_logs_abs = os.path.join(self.__globals['logdir'], test_logs)
            os.mkdir(test_logs_abs)
        
        # Now loop through each UE config
        for ue_config in self.__ue_configs:
            ue_ip = self.__env.get_addr_of(ue_config['adaptername'])
            
            # Set up ue-specific log directories, if user indicated logging was needed:
            if is_logging: # User wants logging
                ue_logs = ue_config['adaptername'] + '_' + str(datetime.now().strftime('%d-%m-%Y_%H%M%S'))
                ue_logs_abs = os.path.join(test_logs_abs, ue_logs)
                os.mkdir(ue_logs_abs)
                
            # Convenience booleans for test_config and run_ue_test methods
            is_dl = False
            is_ul = False
            if ue_config['testtype'] == 'DL' or ue_config['testtype'] == 'SIM': is_dl = True
            if ue_config['testtype'] == 'UL' or ue_config['testtype'] == 'SIM': is_ul = True
            
            # Now get the test configs
            phase0_ue_test_config = self.get_test_config(ue_config, ue_ip, 0, is_dl, is_ul)
            phase1_ue_test_config = self.get_test_config(ue_config, ue_ip, 1, is_dl, is_ul)
            
            # Set up UE-specific log file path and file name prefix attributes, if user indicated logging was needed:
            if is_logging: # User wants logging
                phase0_ue_test_config['logpath'] = ue_logs_abs
                phase0_ue_test_config['logname'] = self.__globals['logprefix'] + ue_config['adaptername'] + '_Phase0'
                phase1_ue_test_config['logpath'] = ue_logs_abs
                phase1_ue_test_config['logname'] = self.__globals['logprefix'] + ue_config['adaptername'] + '_Phase1'
            
            # max_duration should contain the highest duration value from all UE tests
            # If the UE test is TCP then the total test duration is t1
            # If the UE test is UDP then the total test duration is t2
            if ue_config['traffictype'] == 'UDP':
                if int(ue_config['t2']) > max_duration: max_duration = int(ue_config['t2'])
            else:
                if int(ue_config['t1']) > max_duration: max_duration = int(ue_config['t1'])
            # Create Timer threads for each phase, delayed by the phase delay, passing in test_config and the interrupt event:
            phase0Process = Timer(phase0_ue_test_config['delay'], run_ue_test, [self.__interrupt_event, phase0_ue_test_config, is_dl, is_ul, is_logging])
            # Name the threads for debug purposes
            phase0Process.setName(ue_config['adaptername'] + '-phase0')
            phase1Process = Timer(phase1_ue_test_config['delay'], run_ue_test, [self.__interrupt_event, phase1_ue_test_config, is_dl, is_ul, is_logging])
            phase1Process.setName(ue_config['adaptername'] + '-phase1')
            # And add it to the list of threads:
            # All the tests are started at the same time, but are timed to start when needed using Timer threads:
            ue_tests.append(phase0Process)
            # Only add Phase 1 if testing UDP:
            if ue_config['traffictype'] == 'UDP': ue_tests.append(phase1Process)

        # Now run all the threads together:
        for t in ue_tests:
            t.start()
        try:
            # Wait for end of test, or until user hits Ctrl-C
            time.sleep(max_duration + 5)
            logging.debug('Total test waiting finished after ' + str(max_duration + 5) + ' seconds')
        except KeyboardInterrupt:
            # Inform all the threads an interrupt was encountered:
            self.__interrupt_event.set()
            # And cancel any Timer threads still waiting:
            for t in ue_tests: t.cancel()
            logging.warning('Process interrupted by user.\n')
            logging.warning('Tearing down processes and closing logs...\n')
    
    def get_test_config(self, ue_config, ue_ip, phase, is_dl, is_ul):
        test_config = {}
        # Copy some needed attributes straight into test config:
        test_config['test_type'] = ue_config['testtype']
        test_config['ftpserver'] = ue_config['ftpserver']
        # phase_str is used to form parts of the iperf strings:
        phase_str = 't' + str(phase)
        
        if phase == 0: # First phase of UDP test, or total test duration if TCP
            test_config['delay'] = int(ue_config['t0'])
            test_config['duration'] = int(ue_config['t1'])
        else:
            test_config['delay'] = int(ue_config['t1'])
            test_config['duration'] = int(ue_config['t2']) - int(ue_config['t1'])
        
        # Calculate port numbers in a way that avoids conflict between UEs, phases etc.:
        dl_port = str(5000 + ((phase + 1) * 30) + int(ue_config['ueid']))
        ul_port = str(5000 + ((phase + 1) * 90) + int(ue_config['ueid']))

        # Create the iperf strings:
        if is_dl:
            if ue_config['traffictype'] == 'UDP':
                test_config['dl_client_str'] = 'iperf' + \
                    ' -p ' + dl_port + \
                    ' -c ' + ue_ip + \
                    ' -t ' + str(test_config['duration']) + \
                    ' -b ' + ue_config[phase_str+'dlthroughput'] + \
                    ' -l ' + ue_config[phase_str+'dllen'] + \
                    ' -B ' + ue_config['ftpserver'][0] + \
                    ' -u -i 1 -P 1 -f k -w 8M'
                test_config['dl_server_str'] = 'iperf -s' + \
                    ' -p ' + dl_port + \
                    ' -B ' + ue_ip + \
                    ' -l ' + ue_config[phase_str+'dllen'] + \
                    ' -u -U -i 1 -P 0 -f k -w 8M'
            if ue_config['traffictype'] == 'TCP':
                test_config['dl_client_str'] = 'iperf' + \
                    ' -p ' + dl_port + \
                    ' -c ' + ue_ip + \
                    ' -t ' + str(test_config['duration']) + \
                    ' -B ' + ue_config['ftpserver'][0] + \
                    ' -i 1 -P 1 -f k -w 8M'
                test_config['dl_server_str'] = 'iperf -s' + \
                    ' -p ' + dl_port + \
                    ' -B ' + ue_ip + \
                    ' -i 1 -P 0 -f k -w 8M'
            # String needed to kill the client process in case user hits Ctrl-C
            test_config['dl_client_kill_str'] = \
                "kill -9 `ps -ef | grep 'iperf -p " + dl_port + "' | grep -v grep | awk '{print $2}'`"
        if is_ul:
            if ue_config['traffictype'] == 'UDP':
                test_config['ul_server_str'] = 'iperf -s' + \
                    ' -p ' + ul_port + \
                    ' -l ' + ue_config[phase_str+'dllen'] + \
                    ' -u -U -i 1 -P 0 -f k -w 8M'
                test_config['ul_client_str'] = 'iperf' + \
                    ' -B ' + ue_ip + \
                    ' -c ' + ue_config['ftpserver'][0] + \
                    ' -t ' + str(test_config['duration']) + \
                    ' -b ' + ue_config[phase_str+'ulthroughput'] + \
                    ' -p ' + ul_port + \
                    ' -l ' + ue_config[phase_str+'ullen'] + \
                    ' -u -i 1 -P 1 -f k -w 8M'
            if ue_config['traffictype'] == 'TCP':
                test_config['ul_server_str'] = 'iperf -s' + \
                    ' -p ' + ul_port + \
                    ' -i 1 -P 0 -f k -w 8M' # ' -B ' + ue_config['ftpserver'][0] + \
                test_config['ul_client_str'] = 'iperf' + \
                    ' -p ' + ul_port + \
                    ' -c ' + ue_config['ftpserver'][0] + \
                    ' -t ' + str(test_config['duration']) + \
                    ' -B ' + ue_ip + \
                    ' -i 1 -P 1 -f k -w 8M'
            # String needed to kill the server process before exiting (to avoid leaving orphaned process)
            test_config['ul_server_kill_str'] = \
                "kill -9 `ps -ef | grep 'iperf -s -p " + ul_port + "' | grep -v grep | awk '{print $2}'`"
        
        return test_config

    #} End method run_test
#} End class TestInstance

def run_ue_test(interrupt, test_config, is_dl, is_ul, is_logging): #{
    
    # the ftpServer item of the UE config contains a list of three values specifying the IP, Username and Password of the FTP server
    server_ip = test_config['ftpserver'][0]
    server_uname = test_config['ftpserver'][1]
    server_passw = test_config['ftpserver'][2]
    server = paramiko.SSHClient()
    # Stop paramiko from halting the program if the local key is not authorised:
    server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server.load_system_host_keys()

    # And then connect to the server.
    # TODO: Only SSH support at the moment. Add Telnet support if needed.
    server.connect(server_ip, username=server_uname, password=server_passw)
    
    if is_dl:    
        if is_logging: # Set up the DL logs:
            dl_client_log_path = test_config['logpath'] + os.path.sep + test_config['logname'] + '_dl_client.log'
            dl_server_log_path = test_config['logpath'] + os.path.sep + test_config['logname'] + '_dl_server.log'
            dl_client_log = open(dl_client_log_path, 'w', 1) # Open for writing and line-buffered
            dl_server_log = open(dl_server_log_path, 'w', 1) # Open for writing and line-buffered
            logging.debug('dl logs created')
        if not is_logging: # Set logs to write to null device:
            dl_client_log = open(os.devnull, 'w')
            dl_server_log = open(os.devnull, 'w')
        # Start the local server:
        dl_server_log.write('\n-----------Executing command - ' + test_config['dl_server_str'] + '--------------\n\n')
        dl_server_log.flush() # Have to flush to make sure the header line appears at the head!
        dl_local_pid = subprocess.Popen \
            (test_config['dl_server_str'],stdout=dl_server_log,stderr=subprocess.STDOUT,bufsize=0)
        logging.debug('dl server started (local) with pid = ' + str(dl_local_pid.pid))
        # And start the remote client:
        dl_client_log.write('\n-----------Executing command - ' + test_config['dl_client_str'] + '--------------\n\n')
        dl_client_log.flush() # Have to flush to make sure the header line appears at the head!
        dl_client_input, dl_client_output, _ = server.exec_command(test_config['dl_client_str'])
        logging.debug('dl client started (remote)')
    if is_ul:
        if is_logging: # Set up the DL logs:
            ul_client_log_path = test_config['logpath'] + os.path.sep + test_config['logname'] + '_ul_client.log'
            ul_server_log_path = test_config['logpath'] + os.path.sep + test_config['logname'] + '_ul_server.log'
            ul_client_log = open(ul_client_log_path, 'w', 1) # Open for writing and line-buffered
            ul_server_log = open(ul_server_log_path, 'w', 1) # Open for writing and line-buffered
            logging.debug('ul logs created')
        if not is_logging: # Set logs to write to null device:
            ul_client_log = open(os.devnull, 'w')
            ul_server_log = open(os.devnull, 'w')
        # Start the remote server:
        ul_server_log.write('\n-----------Executing command - ' + test_config['ul_server_str'] + '--------------\n\n')
        ul_server_log.write('\n-----------NOTE: IF RUNNING UPLINK TCP TEST, VALUES MAY BE ZERO DUE TO SERVER PERMISSIONS--------------\n\n')
        ul_server_log.flush() # Have to flush to make sure the header line appears at the head!
        ul_server_input, ul_server_output, _ = server.exec_command(test_config['ul_server_str'])
        logging.debug('ul server started (remote)')
        # And start the local client:
        ul_client_log.write('\n-----------Executing command - ' + test_config['ul_client_str'] + '--------------\n\n')
        ul_client_log.flush() # Have to flush to make sure the header line appears at the head!
        ul_local_pid = subprocess.Popen(test_config['ul_client_str'],stdout=ul_client_log,stderr=subprocess.STDOUT,bufsize=0)
        logging.debug('ul client started (local) with pid = ' + str(ul_local_pid.pid))
    
    # Wait for duration of test but break if there is a keyboard interrupt detected in the main thread (interrupt event is set)
    is_interrupted = interrupt.wait(test_config['duration'] + 3)
    logging.debug('interrupt waiting ended with status ' + str(is_interrupted) + ' after ' + str(test_config['duration'] + 3) + ' seconds')

    # If an interrupt is signalled from the main thread then kill the client processes early:
    if is_interrupted and is_ul: ul_local_pid.kill() # Kill the UL client process
    if is_interrupted and is_dl: server.exec_command(test_config['dl_client_kill_str']) # Kill the DL client process
    
    if is_ul:
        # kill the UL server process using the kill string (nasty, but it works)
        server.exec_command(test_config['ul_server_kill_str'])
        logging.debug('UL Server process killed')
        # and write the UL server log (no flush required as file closed next)
        for line in ul_server_output: ul_server_log.write(line)
        logging.debug('UL Server Log finished writing')
    if is_dl:
        # kill the DL server process
        dl_local_pid.terminate()
        logging.debug('Local DL server process killed')    
        # and write the DL client log (no flush required as file closed next)
        for line in dl_client_output: dl_client_log.write(line)
        logging.debug('DL Client Log finished writing')
        
    # Kill the SSH connection
    server.close()
    logging.debug('Server closed')
    # if interrupt then write a final note to the logs:   
    if is_interrupted and is_dl: dl_server_log.write('\nProcess Interrupted by User.\n')
    if is_interrupted and is_dl: dl_client_log.write('\nProcess Interrupted by User.\n')
    if is_interrupted and is_ul: ul_client_log.write('\nProcess Interrupted by User.\n')
    if is_interrupted and is_ul: ul_server_log.write('\nProcess Interrupted by User.\n')
    # and close the files before you go!
    if is_ul: ul_client_log.close()
    if is_ul: ul_server_log.close()
    if is_dl: dl_client_log.close()
    if is_dl: dl_server_log.close()
    logging.debug('Log files closed')
#} End method run_ue_test