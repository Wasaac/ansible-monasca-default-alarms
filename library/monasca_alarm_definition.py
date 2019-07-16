#!/usr/bin/python
# -*- coding: utf-8 -*-

# (C) Copyright 2019 StackHPC Ltd.
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: monasca_alarm_definition
short_description: Perform crud operations on Monasca alarm definitions
description:
    - "Performs crud operations (create/update/delete) on monasca alarm definitions"
    - "The Monasca project homepage: U(https://wiki.openstack.org/wiki/Monasca)."
    - "When relevant the alarm_definition_id is in the output and can be used with the register action"
author:
    - Tim Kuhlman <tim@backgroundprocess.com>
    - Isaac Prior <isaac@stackhpc.com>
requirements: [ python-monascaclient , keystoneauth1 ]
options:
    alarm_actions:
        description:
            -  Array of notification method IDs that are invoked for the transition to the ALARM state.
    description:
        description:
            - The description associated with the alarm definition.
    expression:
        description:
            - The alarm definition expression, required for create/update operations.
    match_by:
        default: "[hostname]"
        description:
            - Alarm definition match by, see the monasca api documentation for more detail.
    name:
        required: true
        description:
            - The alarm definition name.
    ok_actions:
        description:
            -  Array of notification method IDs that are invoked for the transition to the OK state.
    severity:
        default: "LOW"
        description:
            - The severity set for the alarm definition must be LOW, MEDIUM, HIGH or CRITICAL.
    state:
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the alarm definition should exist.  When C(absent), removes the alarm definition. The name
              is used to determine the alarm definition to remove.
    undetermined_actions:
        description:
            -  Array of notification method IDs that are invoked for the transition to the UNDETERMINED state.
extends_documentation_fragment: monasca
'''

EXAMPLES = '''
- name: Setup root email notification method
  monasca_notification_method:
    name: "Email Root"
    type: 'EMAIL'
    address: 'root@localhost'
    keystone_url: "{{ keystone_url }}"
    keystone_user: "{{ keystone_user }}"
    keystone_password: "{{ keystone_password }}"
    keystone_project: "{{ keystone_project }}"
  register: default_notification
- name: Create System Alarm Definitions
  monasca_alarm_definition:
    name: "{{ item.name }}"
    expression: "{{ item.expression }}"
    keystone_url: "{{ keystone_url }}"
    keystone_user: "{{ keystone_user }}"
    keystone_password: "{{ keystone_password }}"
    keystone_project: "{{ keystone_project }}"
    alarm_actions:
      - "{{ default_notification.notification_method_id | default(omit) }}"
    ok_actions:
      - "{{ default_notification.notification_method_id | default(omit) }}"
    undetermined_actions:
      - "{{ default_notification.notification_method_id | default(omit) }}"
  with_items:
    - { name: "High CPU usage", expression: "avg(cpu.idle_perc) < 10 times 3" }
    - { name: "Disk Inode Usage", expression: "disk.inode_used_perc > 90" }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.monasca import MonascaAnsible, argument_spec, mutually_exclusive


class MonascaDefinition(MonascaAnsible):
    def run(self):
        name = self.module.params['name']
        expression = self.module.params['expression']

        # Find existing definitions
        definitions = {definition['name']: definition for definition in self.monasca.alarm_definitions.list()}

        if self.module.params['state'] == 'absent':
            if name not in definitions.keys():
                self._exit_json(changed=False)

            if self.module.check_mode:
                self._exit_json(changed=True)
            resp = self.monasca.alarm_definitions.delete(alarm_id=definitions[name]['id'])
            if resp.status_code == 204:
                self._exit_json(changed=True)
            else:
                self.module.fail_json(msg=str(resp.status_code) + resp.text)

        else:  # Only other option is state=present
            def_kwargs = {"name": name, "description": self.module.params['description'], "expression": expression,
                          "match_by": self.module.params['match_by'], "severity": self.module.params['severity'],
                          "alarm_actions": self.module.params['alarm_actions'],
                          "ok_actions": self.module.params['ok_actions'],
                          "undetermined_actions": self.module.params['undetermined_actions']}

            if name in definitions.keys():
                if definitions[name]['expression'] == expression and \
                   definitions[name]['alarm_actions'] == self.module.params['alarm_actions'] and \
                   definitions[name]['ok_actions'] == self.module.params['ok_actions'] and \
                   definitions[name]['undetermined_actions'] == self.module.params['undetermined_actions']:
                    self._exit_json(changed=False, alarm_definition_id=definitions[name]['id'])
                def_kwargs['alarm_id'] = definitions[name]['id']

                if self.module.check_mode:
                    self._exit_json(changed=True, alarm_definition_id=definitions[name]['id'])
                body = self.monasca.alarm_definitions.patch(**def_kwargs)
            else:
                if self.module.check_mode:
                    self._exit_json(changed=True)
                body = self.monasca.alarm_definitions.create(**def_kwargs)

            if 'id' in body:
                self._exit_json(changed=True, alarm_definition_id=body['id'])
            else:
                self.module.fail_json(msg=body)


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            alarm_actions=dict(required=False, default=[], type='list'),
            description=dict(required=False, type='str'),
            expression=dict(required=False, type='str'),
            match_by=dict(default=['hostname'], type='list'),
            name=dict(required=True, type='str'),
            ok_actions=dict(required=False, default=[], type='list'),
            severity=dict(default='LOW', type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            undetermined_actions=dict(required=False, default=[], type='list'),
        )
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        mutually_exclusive=mutually_exclusive(),
        supports_check_mode=True
    )

    definition = MonascaDefinition(module)
    definition.run()


if __name__ == "__main__":
    main()
