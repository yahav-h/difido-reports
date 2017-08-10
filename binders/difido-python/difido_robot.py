'''
Created on Aug 10, 2017

@author: Itai Agmon
'''

from execution import Execution, Machine, Scenario, Test
from test_details import ReportElement, TestDetails
from execution_details import ExecutionDetails
from random import randint
import time
import socket
import local_utils, remote_utils
from datetime import datetime
from configuration import Conf

class AbstractReport(object):
    
    TIME_FORMAT = '%H:%M:%S:'
    
    DATE_FORMAT = '%Y/%m/%d'
    
    ROBOT_FORMAT = '%Y%m%d %H:%M:%S.%f'
    
    def __init__(self):
        self.init_model()
        self.start()
        conf = Conf("general")
        self.num_of_suites_to_ignore = conf.get_int("num.of.suites.to.ignore") 
    
    def init_model(self):
        self.execution = Execution()
        machine = Machine(socket.gethostname())

        self.execution.add_machine(machine)
        self.uid = str(randint(1000,9999) + time.time() / 1000).replace(".","")
        self.index = 0
        self.scenario_stack = []
    
    
    def start_suite(self, name, attr):
        if self.num_of_suites_to_ignore > 0:
            self.num_of_suites_to_ignore -= 1
            return 
        self.num_of_suites_to_ignore -= 1
        self.scenario = Scenario(name)
        if len(self.scenario_stack) is not 0:
            self.scenario_stack[-1].add_child(self.scenario)
        else:
            self.execution.get_last_machine().add_child(self.scenario)
            
        self.scenario_stack.append(self.scenario)
        self.write_execution()
        
    def start_keyword(self, name, attrs):
        if len(self.scenario_stack) is 0:
            return
        element = ReportElement()
        starttime = datetime.strptime(attrs['starttime'], AbstractReport.ROBOT_FORMAT)
        element.time = starttime.strftime(AbstractReport.TIME_FORMAT)
        element.title = attrs['kwname']
        if len(attrs['args']) is not 0:
            for att in attrs['args']:
                element.title += " " + str(att) 
        element.set_type("startLevel")
        self.testDetails.add_element(element)
        self.write_test_details()
        pass
    
    def end_keyword(self, name, attrs):
        if len(self.scenario_stack) is 0:
            return
        element = ReportElement()
        element.set_type("stopLevel")
        self.testDetails.add_element(element)
        self.write_test_details()
        pass

    
    def end_suite(self,name,attrs):
        self.num_of_suites_to_ignore += 1
        if self.num_of_suites_to_ignore > 0:
            return
        if len(self.scenario_stack) is not 0:
            self.scenario_stack.pop()
    
    def end_test(self,name, attrs):
        if len(self.scenario_stack) is 0:
            return
        
        if attrs["status"] != "PASS":
            self.test.set_status("failure")
        self.test.duration = attrs['elapsedtime']
        self.write_test_details()
        self.write_execution()
            
    def start_test(self, name, attrs):
        if len(self.scenario_stack) is 0:
            return
        
        self.test_start_time = datetime.strptime(attrs['starttime'], AbstractReport.ROBOT_FORMAT) 

        self.test = Test(self.index, name, self.uid + "_" +str(self.index))
        self.testDetails = TestDetails(self.uid + "_" +str(self.index))

        self.index += 1
        self.test.timstamp = self.test_start_time.strftime(AbstractReport.TIME_FORMAT)
        self.test.date = self.test_start_time.strftime(AbstractReport.DATE_FORMAT)
        self.test.description = attrs['doc']
        self.test.add_property("Long name", attrs['longname'])
        self.test.add_property("Robot id", attrs['id'])
        self.test.add_property("critical", str(attrs['critical']))
        tagIndex = 0
        for tag in attrs['tags']:
            self.test.add_property("tag" + str(tagIndex), tag)
            tagIndex += 1
        self.scenario.add_child(self.test)
        
        self.write_execution()
        self.write_test_details()
        
    
    def log_message(self,message):
        if len(self.scenario_stack) is 0:
            return
        
        element = ReportElement()
        timestamp = datetime.strptime(message['timestamp'], AbstractReport.ROBOT_FORMAT)
        element.time = timestamp.strftime(AbstractReport.TIME_FORMAT)
        element.title = message['message']
        if message["level"] == "FAIL":
            element.set_status("failure")
            self.test.set_status("failure")
        self.testDetails.add_element(element)
        self.write_test_details()

    def message(self, message):
        pass
    
    def start(self):
        pass
    
    def close(self):
        self.write_test_details()
        self.write_execution()

    def write_test_details(self):
        pass
    
    def write_execution(self):
        pass
            

class LocalReport(AbstractReport):
    
    ROBOT_LISTENER_API_VERSION = 2
    
    def start(self):
        local_utils.prepare_template()
        local_utils.prepare_current_log_folder()
        
    
    def write_test_details(self):
        local_utils.prepare_test_folder(self.testDetails.uid)
        local_utils.write_test_details_to_file(self.testDetails)

    
    def write_execution(self):
        local_utils.write_execution_to_file(self.execution)


    
class RemoteReport(AbstractReport):

    ROBOT_LISTENER_API_VERSION = 2
    
    def start(self):
        conf = Conf("remote")
        details = ExecutionDetails()
        details.description = conf.get_string("description")
        try: 
            self.execution_id = remote_utils.prepare_remote_execution(details)
            self.enabled = True
        except:
            self.enabled = False
            return
        
        machine = self.execution.get_last_machine()
        try: 
            self.machine_id = remote_utils.add_machine(self.execution_id, machine)
        except:
            self.enabled = False
            return
        self.retries = 10
        
        
        
    def write_execution(self):
        if not self.enabled:
            return
        try:
            remote_utils.update_machine(self.execution_id, self.machine_id, self.execution.get_last_machine())
        except Exception as e:
            print "Exception occurred when trying to update machine: " + str(e)
            self.check_if_disable()
    
    
    def write_test_details(self):
        if not self.enabled:
            return
        try:
            remote_utils.add_test_details(self.execution_id, self.testDetails)
        except Exception as e:
            print "Exception occurred when trying to add test details: " + str(e)
            self.check_if_disable()
    
    
    def close(self):
        super(RemoteReport, self).close()
        try:
            remote_utils.end_execution(self.execution_id)
        except:
            pass
            
    
    
    def check_if_disable(self):
        self.retries -= 1
        if self.retries <= 0:
            self.enabled = False
            print "Number of failed request exceeded the maximum allowed. Disabling remote Difido"
        pass
    
    
