#!/usr/bin/python
#coding: utf-8 -*-


# Example from:
# http://networkop.github.io/blog/2015/06/24/ansible-intro/
# http://networkop.github.io/blog/2015/07/03/parser-modules/

import yaml
import re
SCENARIO_FILE = "scenarios/all.txt"
GROUP_VAR_FILE = "group_vars/all.yml"

class ScenarioParser(object):

    def __init__(self):
        self.rc = 0
        self.storage = dict()
        self.file_content = dict()

    def open(self):
       try:
            with open(GROUP_VAR_FILE, 'r') as fileObj:
                self.file_content = yaml.load(fileObj)
       except:
           open(GROUP_VAR_FILE, 'w').close()

    def read(self):
        scenario_number = 0
        scenario_step   = 0
        scenario_name   = ''
        name_pattern = re.compile(r'^(\d+)\.?\s+(.*)')
        step_pattern = re.compile(r'.*[Ff][Rr][Oo][Mm]\s+([\d\w]+)\s+[Tt][Oo]\s+([\d\w]+)\s+[Vv][Ii][Aa]\s+([\d\w]+,*\s*[\d\w]+)*')
        with open(SCENARIO_FILE, 'r') as fileObj:
            for line in fileObj:
                if not line.startswith('#') and len(line) > 3:
                    name_match = name_pattern.match(line)
                    step_match = step_pattern.match(line)
                    if name_match:
                        scenario_number = name_match.group(1)
                        scenario_name   = name_match.group(2)
                        scenario_steps  = [scenario_name, {}]
                        if not scenario_number in self.storage:
                            self.storage[scenario_number] = scenario_steps
                        else:
                            scenario_steps = self.storage[scenario_number]
                    elif step_match:
                        from_device = step_match.group(1)
                        to_device = step_match.group(2)
                        via = step_match.group(3)
                        via_devices = [device_name.strip() for device_name in via.split(',')]
                        if not scenario_number == 0 or not scenario_name:
                            if not from_device in scenario_steps[1]:
                                scenario_steps[1][from_device] = dict()
                            scenario_steps[1][from_device][to_device] = via_devices
                    else:
                        self.rc = 1

    def write(self):
       self.file_content['scenarios'] = self.storage
       if self.rc == 0:
           with open(GROUP_VAR_FILE, 'w+') as fileObj:
               yaml.safe_dump(self.file_content, fileObj, explicit_start=True, indent=3, allow_unicode=True)

def main():
    module = AnsibleModule(argument_spec=dict())
    parser = ScenarioParser()
    parser.open()
    parser.read()
    parser.write()
    if not parser.rc == 0:
        module.fail_json(msg="Failed to parse. Incorrect input.")
    else:
        module.exit_json(changed=False)

from ansible.module_utils.basic import *
main()