#!/usr/bin/python
# -*- coding: utf-8 -*-

# (C) Copyright 2019 StackHPC Ltd.
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
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
