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
module: monasca_notification_method
short_description: Perform crud operations for Monasca notifications methods.
description:
    - "Performs crud operations (create/update/delete) on monasca notification methods."
    - "The Monasca project homepage: U(https://wiki.openstack.org/wiki/Monasca)."
    - "When relevant the notification_id is in the output and can be used with the register action."
author:
    - Tim Kuhlman <tim@backgroundprocess.com>
    - Isaac Prior <isaac@stackhpc.com>
requirements: [ python-monascaclient , keystoneauth1 ]
options:
    address:
        required: true
        description:
            - The notification method address corresponding to the type.
    name:
        required: true
        description:
            - The notification method name.
    state:
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the notification should exist.  When C(absent), removes the notification.
    type:
        required: true
        description:
            - The notification type. This must be one of the types supported by the Monasca API.
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


class MonascaNotification(MonascaAnsible):
    def run(self):
        name = self.module.params['name']
        type = self.module.params['type']
        address = self.module.params['address']

        notifications = {notif['name']: notif for notif in self.monasca.notifications.list()}
        if name in notifications.keys():
            notification = notifications[name]
        else:
            notification = None

        if self.module.params['state'] == 'absent':
            if notification is None:
                self._exit_json(changed=False)
            else:
                if self.module.check_mode:
                    self._exit_json(changed=True)

                self.monasca.notifications.delete(notification_id=notification['id'])
                self._exit_json(changed=True)

        else:  # Only other option is present
            if notification is None:
                if self.module.check_mode:
                    self._exit_json(changed=True)

                body = self.monasca.notifications.create(name=name, type=type, address=address)
                self._exit_json(changed=True, notification_method_id=body['id'])

            else:
                if notification['type'] == type and notification['address'] == address:
                    self._exit_json(changed=False, notification_method_id=notification['id'])
                else:
                    if self.module.check_mode:
                        self._exit_json(changed=True, notification_method_id=notification['id'])

                    self.monasca.notifications.update(notification_id=notification['id'],
                                                      name=name, type=type, address=address)
                    self._exit_json(changed=True, notification_method_id=notification['id'])


def main():
    arg_spec = argument_spec()
    arg_spec.update(
        dict(
            address=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            type=dict(required=True, type='str'),
        )
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        mutually_exclusive=mutually_exclusive(),
        supports_check_mode=True
    )

    notification = MonascaNotification(module)
    notification.run()


if __name__ == "__main__":
    main()
