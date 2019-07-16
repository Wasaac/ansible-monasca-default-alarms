#!/usr/bin/python
# -*- coding: utf-8 -*-

# (C) Copyright 2019 StackHPC Ltd.
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: monasca
short_description: Base class for Monasca API authentication
description:
    - "A base class used to build Monasca Client based Ansible Modules"
    - "Authenticates to Keystone using either keystone token or username/password"
    - "Monasca project homepage - https://wiki.openstack.org/wiki/Monasca"
author:
    - Tim Kuhlman <tim@backgroundprocess.com>
    - Isaac Prior <isaac@stackhpc.com>
requirements: [ python-monascaclient , keystoneauth1 ]
options:
    api_version:
        default: '2_0'
        description:
            - The monasca api version.
    keystone_password:
        description:
            - Keystone password to use for authentication, required unless a I(keystone_token) is specified.
    keystone_url:
        required: true
        description:
            - Keystone url to authenticate against.
              Example http://192.168.10.5:5000/v3
    keystone_token:
        description:
            - Keystone token to use with the monasca api. If this is specified I(monasca_api_url) is required but
              I(keystone_user) and I(keystone_password) aren't.
    keystone_user:
        description:
            - Keystone user to log in as, required unless a I(keystone_token) is provided.
    keystone_project:
        required: true
        description:
            - Keystone project name to obtain a token for.
    monasca_api_url:
        description:
            - Service endpoint for the monasca api.
              Can be discovered if I(keystone_user) and I(keystone_password) are provided.
    user_domain_id:
        default: "default"
        description:
            - The domain id of the user.
    project_domain_id:
        default: "default"
        description:
            - The domain id of the project.
    monasca_endpoint_region:
        default: "RegionOne"
        description:
            - The monasca api region. Used to discover the endpoint if I(monasca_api_url) is not provided.
    monasca_endpoint_interface:
        default: ['admin', 'internal']
        description:
            - The monasca api interface. Used to discover the endpoint if I(monasca_api_url) is not provided.
'''

from ansible.module_utils.basic import missing_required_lib

try:
    from monascaclient import client as mon_client
    from keystoneauth1 import identity
    from keystoneauth1 import session
except ImportError:
    HAS_MONASCACLIENT = False
else:
    HAS_MONASCACLIENT = True


class MonascaAnsible(object):
    """ A base class used to build Monasca Client based Ansible Modules
        As input an ansible.module_utils.basic.AnsibleModule object is expected. It should have at least
        these params defined:
        - api_version
        - keystone_project
        - keystone_token or keystone_url, keystone_user and keystone_password
    """
    def __init__(self, module):
        self.module = module

        if not HAS_MONASCACLIENT:
            self.module.fail_json(msg=missing_required_lib('python-monascaclient or keystoneauth1'))

        self.api_version = self.module.params['api_version']

        # Create a keystone session from a password
        if self.module.params['keystone_token'] is None:
            sess = self._keystone_session()

            if self.module.params['monasca_api_url'] is None:
                self.api_url = self._endpoint_discover(sess)

            self.exit_data = {'monasca_api_url': self.api_url}

            self.monasca = mon_client.Client(api_version=self.api_version,
                                             endpoint=self.api_url,
                                             session=sess)

        else:  # user has supplied a keystone token
            self.token = self.module.params['keystone_token']
            if self.module.params['monasca_api_url'] is None:
                self.module.fail_json(msg='monasca_api_url param is required when using keystone_token')

            self.api_url = self.module.params['monasca_api_url']

            self.exit_data = {'monasca_api_url': self.api_url}

            self.monasca = mon_client.Client(api_version=self.api_version,
                                             endpoint=self.api_url,
                                             token=self.token,
                                             project_name=self.module.params['keystone_project'],
                                             auth_url=self.module.params['keystone_url'],
                                             project_domain_id=self.module.params['project_domain_id']
                                             )

    def _exit_json(self, **kwargs):
        """ Exit with supplied kwargs combined with the self.exit_data
        """
        kwargs.update(self.exit_data)
        self.module.exit_json(**kwargs)

    def _keystone_session(self):
        """ Return a Keystone session
        """
        auth = identity.Password(
            auth_url=self.module.params['keystone_url'],
            username=self.module.params['keystone_user'],
            password=self.module.params['keystone_password'],
            project_name=self.module.params['keystone_project'],
            user_domain_id=self.module.params['user_domain_id'],
            project_domain_id=self.module.params['project_domain_id']
        )
        return session.Session(auth=auth)

    def _endpoint_discover(self, sess):
        """ Return the Monasca API URL
        """
        min_version = self.module.params['api_version'].replace('_', '.')
        try:
            resp = sess.get('/',
                            endpoint_filter={'service_type': 'monitoring',
                                             'interface': self.module.params['monasca_endpoint_interface'],
                                             'region_name': self.module.params['monasca_endpoint_region'],
                                             'version': min_version})
        except Exception as e:
            self.module.fail_json(msg='Error discovering Monasca API URL from catalogue: {}'.format(e))
        else:
            if not resp.ok:
                self.module.fail_json(msg=str(resp.status_code) + resp.text)

        return resp.url


def argument_spec():
    return dict(
            api_version=dict(required=False, default='2_0', type='str'),
            keystone_user=dict(required=False, type='str'),
            keystone_password=dict(required=False, no_log=True, type='str'),
            keystone_token=dict(required=False, no_log=True, type='str'),
            keystone_url=dict(required=True, type='str'),
            keystone_project=dict(required=True, type='str'),
            monasca_api_url=dict(required=False, type='str'),
            user_domain_id=dict(required=False, default='default', type='str'),
            project_domain_id=dict(required=False, default='default', type='str'),
            monasca_endpoint_region=dict(required=False, default='RegionOne', type='str'),
            monasca_endpoint_interface=dict(required=False, default=['admin', 'internal'], type='list'),
        )


def mutually_exclusive():
    return [
        ['keystone_token', 'keystone_user'],
        ['keystone_token', 'keystone_password'],
        ['keystone_token', 'monasca_endpoint_interface'],
        ['keystone_token', 'monasca_endpoint_region']
    ]
