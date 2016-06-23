'''
The Load Test Script - VERSION 1.0 - MAY 2014

Change history:
Version 0.1 - Jan 2014 - Basic UDP testing implemented. No logging
Version 1.0 - May 2014 - Full re-write of TestInstance, included support for logging and TCP tests and Ctrl-C test cancellation

loadtest.TestConfig extends ConfigParser in order to parse the test config .ini and to hold the config in a dictionary.
Some basic functions have been added to make data access a bit easier.

TestConfig.py implements the TestConfig class and methods

@author: Oliver Thomas
'''

import os
from ConfigParser import ConfigParser


class TestConfig(ConfigParser): #{
    '''
    class TestConfig(ConfigParser):
    Sub-class of:                    ConfigParser
    
    Overview:
    The TestConfig class provides a slightly modified version of the ConfigParser class, with some modifications 
    to certain methods and the addition of the get_full_ue_configs method which is a quick and easy method to get 
    all the UE configs returned as a list of dicts. This makes it somewhat easier to do the processing required by 
    TestInstance than it would be on the raw ConfigParser class.

    Public methods:
    is_list(self, section, option):
    Returns a boolean which determines if a config item is a comma-delimited list or not. 
    Tests for the presence of ',' in the config item value
    
    get_list(self, section, option):
    Alternative to ConfigParser.get. Returns the item at section/option, but will return a list rather than a single value, 
    if the item is a comma-delimited list (uses is_list).
    
    get_section_map(self, section)
    Returns a dict of all the config items in a section, including list values if present.
    
    get_full_ue_configs(self):
    Returns a list of all the dicts representing all the configured UEs. Each dict includes all the config items for each UE, 
    including list values if present.
    
    get_globals(self):
    Returns all the config items in the 'Globals' section of the config. If Globals is not present then it also defines and
    returns some default values.
    
    '''

    def __init__(self, path): #{
        '''
        Constructor
        '''
        ConfigParser.__init__(self)
        '''
        ConfigParser.optionxform attribute is left as default
        This means all option names will be converted to lower case
        To change this and make option names case sensitive, un-comment the below line of code:
        '''
        # self.optionxform = str
        self.read(path)
    #} End method __init__

    def is_list(self, section, option): #{
        if str(self.get(section, option)).count(',') == 0:
        ## Then this is not a comma-delimited list...
            return 0
        else:
        ## Then this is a comma-delimited list...
            return 1
    #} End method is_list

    def get_list(self, section, option): #{
        value = self.get(section, option)
        if self.is_list(section, option):
        ## Then this is a comma-delimited list, return the list...
            value_list = str(value).split(',')
            return value_list
        else: ## Return the value...
            return value
    #} End method get_list

    def get_section_map(self, section): #{
        options_dict = {}
        options = self.options(section)
        for option in options:
            options_dict[option] = self.get_list(section, option)
        return options_dict
    #} End method get_section_map

    def get_full_ue_configs(self): #{
        ue_config = {}
        ue_configs = []
        for section in self.sections():
            if not section == 'Globals':
                ue_config = self.get_section_map(section)
                ue_configs.append(ue_config)
        return ue_configs
    #} End method get_full_ue_configs
    
    def get_globals(self): #{
        globals_dict = {}
        if self.has_section('Globals'):
            globals_dict['logdir'] = os.path.normpath(self.get('Globals', 'baselogdir'))
            globals_dict['logging'] = int(self.get('Globals', 'logging'))
            globals_dict['logprefix'] = self.get('Globals', 'logprefix')
        else: # Set all to defaults:
            globals_dict['logdir'] = os.path.normpath('C:\\loadTestLogs\\')
            globals_dict['logging'] = 1 # Yes please!
            globals_dict['logprefix'] = 'Undefined-' # No prefix defined
            
        return globals_dict
    #} End method get_globals
#} End class TestConfig