#!/usr/bin/python

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
