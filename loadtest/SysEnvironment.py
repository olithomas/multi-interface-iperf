'''
The Load Test Script - VERSION 1.0 - MAY 2014

Change history:
Version 0.1 - Jan 2014 - Basic UDP testing implemented. No logging
Version 1.0 - May 2014 - Full re-write of TestInstance, included support for logging and TCP tests and Ctrl-C test cancellation

loadtest.SysEnvironment implements some functions of the Windows Management Instrumentation API (WMI) in order to query 
information about the currently active interfaces. It also provides some methods for easy access to this information.

SysEnvironment.py implements the SysEnvironment class and methods only.

@author: Oliver Thomas
'''

import wmi
import re

class SysEnvironment(object): #{
    '''
    class SysEnvironment(object):
	Sub-class of:
	    object
	Private instance variables:
	    __sys_addr = Dictionary for holding a list of active interface names (as keys) and their IPv4 address
	    __sys_id = Dictionary for holding a list of active interface names (as keys) and their Interface ID
	    __c	= Instance of the WMI object
	Private instance methods:
		__init_interfaces() = object initialisation method to populate __sys_addr and __sys_id structures with active 
		interface info.

	Overview:
	The SysEnvironment class holds data structures containing the active interface IDs, names, and IPv4 addresses, for all 
	active interfaces on the Windows machine. It also provides some convenience methods for accessing that information.
	
	Public methods:
	get_interfaces_dict(self):
	Returns __sys_addr dictionary. Getters and Setters are not strictly necessary in Python, but it looks tidier in the 
	instantiating code this way.
	
	get_addr_of(self, searchStr)
	Returns the IPv4 address for the Network Interface name specified by searchStr. Returns 'Invalid Argument' if the key 
	doesn't exist.
	
    '''

    def __init__(self): #{
        '''
        Constructor
        '''
        self.__sys_addr = {}
        self.__sys_id = {}
        self.__c = wmi.WMI()
        
        '''
		Initialize __sys_addr dict with current system adapters and IPs:
		'''
        self.__init_interfaces()
    #} End method __init__ (constructor)
        
    def __str__(self): #{
        
        return_str = ''
        for item in self.__sys_addr.items():
            return_str = return_str + str(item)
        
        return return_str
    #} End method __str__
        
    def __init_interfaces(self): #{
        
        '''
		RegEx string to match valid IPv4 address:
		'''
        ipv4 = re.compile('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
        '''
		For all interfaces in the Network Adapter object, find the Adapter Configuration object 
		with InterfaceIndex equal to the Network Adapter InterfaceIndex:
		'''
        for interface in self.__c.Win32_NetworkAdapter():
            for interfaceConfig in self.__c.Win32_NetworkAdapterConfiguration(InterfaceIndex=interface.InterfaceIndex):
                if not interface.NetConnectionID is None and not interfaceConfig.IPAddress is None:
                    '''
					Then this is a valid adapter with at least one address
					'''
                    addr_list = interfaceConfig.IPAddress
                    for ip in addr_list:
                        if ipv4.match(ip):
                            '''
						    Then this is a valid IPv4 address. If more than one IPv4 address is found, this function will only add the last found
							'''
                            ipv4_addr = ip
                    self.__sys_addr[interface.NetConnectionID] = ipv4_addr
                    self.__sys_id[interface.NetConnectionID] = interface.InterfaceIndex
    #} End method __init_interfaces
    
    def get_interfaces_dict(self): #{
        '''
        Getter for the __sys_addr structure
        '''
        return self.__sys_addr
    #} End method get_interfaces_dict
    
    def get_addr_of(self, searchStr): #{
        '''
        Getter for specific items of the __sys_addr dict, referenced by searchStr.
        Some basic error handling added for unknown search strings
        '''
        if searchStr not in self.__sys_addr:
            return 'Invalid Argument'
        else:
            return self.__sys_addr[searchStr]
    #} End method get_addr_of

#} End class SysEnvironment