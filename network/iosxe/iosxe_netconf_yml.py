#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = """
---
module: iosxe_netconf_yml
version_added: "2.2"
author: "Krishna Kothapalli(@privateip)"
short_description: Run NETCONF based configuration on IOSXE devices.
description:
  - Sends NETCONF based configuration to an iosxe node and returns the results
    read from the device. The M(iosxe_netconf_yml) module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
options:
  commands:
    description:
      - List of commands to send to the remote iosxe device over the
        configured provider. The resulting output from the command
        is returned. If the I(waitfor) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retires as expired.
    required: true

"""

EXAMPLES = """

  - name: Configure interfaces
    iosxe_netconf_yml:
      provider: "{{ provider }}"
      commands:
       interface:
         TenGigabitEthernet:
           name: "1/0/1"
           description: My description
    register: myoutput

"""

RETURN = """
stdout:
  description: the set of responses from the commands
  returned: always
  type: list
  sample: ['...', '...']

stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
  description: the conditionals that failed
  retured: failed
  type: list
  sample: ['...', '...']
"""

import yaml

import xml.dom.minidom

try:
    import ncclient.manager

    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


def convert_obj_to_xml(obj, indent):
    out = ""
    if isinstance(obj, dict):
        for key in obj.keys():
            value = obj[key]
            out += "<" + key + ">"
            out += convert_obj_to_xml(value, indent + 1)
            out += "</" + key + ">"

    elif isinstance(obj, basestring):
        out += obj
    else:
        out += str(obj)
    return out

def main():
    spec = dict(
        commands=dict(type='dict'),
        provider=dict()
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)


    commands = module.params['commands']
    username = module.params['username']
    password = module.params['password']
    host = module.params['host']
    port = module.params['port']

    dataMap = yaml.safe_load(str(commands))
    xml_output = convert_obj_to_xml(dataMap, 0)

    xml_output = """<?xml version="1.0" encoding="UTF-8"?>
            <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
              <native xmlns="http://cisco.com/ns/yang/ned/ios">
""" + xml_output + """
              </native>
            </config>
            """
    debug_log_file_name = "/tmp/iosxe.txt"
    debug_log_file_fd = open(debug_log_file_name, 'w')
    debug_log_file_fd.truncate()
    debug_log_file_fd.write(xml_output)

    if not HAS_NCCLIENT:
        module.fail_json(msg='could not import the python library '
                             'ncclient required by this module')

    try:
        xml.dom.minidom.parseString(xml_output)
    except:
        e = get_exception()

        module.fail_json(
            msg='error parsing XML: ' +
                str(e) + xml_output
        )
        return
    try:

        nchandle = ncclient.manager.connect_ssh(host, username=username, password=password, port=port,
                                                hostkey_verify=False)
        nchandle.edit_config(target='running', config=xml_output)
    except:
        e = get_exception()
        module.fail_json(
            msg='error netconf ' +
                str(e) + " XML request:" + xml_output
        )
        return


    result = dict(changed=True)

    result['stdout_lines'] = xml_output
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.iosxe import *

if __name__ == '__main__':
    main()
