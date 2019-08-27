# monasca-default-alarms

This role will setup a default alarm definition configuration for Monasca. It also provides Ansible modules for 
the creation of Monasca alarm definitions and notifications.
More details on alarm definitions can be found at the
[Monasca API documentation](https://github.com/openstack/monasca-api/blob/master/docs/monasca-api-spec.md#alarm-definitions-and-alarms)

## Requirements
Ansible >=2.8 is required to make use of features in this role such as doc fragments.
Unless provided with `monasca_api_url` it is assumed the service endpoint for Monasca is properly registered in keystone.

## Role Variables

These variables must be defined.

- `keystone_url`
- `keystone_project`

and either

- `keystone_user`
- `keystone_password`

or

- `keystone_token`
- `monasca_api_url`

By default the configured alarm definitions will be setup with an email notification to `root@localhost`.
Change the `notification_address` variable to send email elsewhere.
Alternatively, if `notification_type` is `WEBHOOK` or `SLACK` then `notification_address` specifies the URL:

    notification_address: "https://hooks.slack.com/services/XXXXXXXXX/YYYYYYYYY/ZZZZZZZZZZZZZZZZZZZZZZZ"
    notification_name: "Default Slack Notification"
    notification_type: "SLACK"

In addition, there are two optional variables to control the alarms created:

- `skip_tasks` (list)
- `custom_alarms` (dict)

See example playbook for `custom_alarms` fields. See `tasks/main.yml` for `skip_tasks` options.

The role is responsible for installing the python-monascaclient dependency inside a virtualenv.
The default location of the virtualenv is `/opt/python-monascaclient` - since this path usually
requires privilege escalation the role will use `become: yes` to create it.
Change the virtualenv directory using `monasca_client_virtualenv_dir: /foo`.
Disable privilege escalation using `virtualenv_become: no`.

## Example Playbook
Place the following in a playbook file, replacing the `keystone_` variables with those suitable for
your OpenStack deployment. Consider using ansible-vault or equivalent to store `keystone_password`.

    - name: Define default alarm notifications
      hosts: monitoring
      gather_facts: no
      vars:
        keystone_url: http://192.168.128.2:35357/v3/
        keystone_user: admin
        keystone_password: password
        keystone_project: monasca_control_plane
        skip_tasks: ["misc", "openstack", "monasca"]
        custom_alarms:
          - name: "Host CPU System Percent"
            description: "Alarms when System CPU % is higher than 80 (example custom alarm)"
            expression: "cpu.system_perc{hostname=host.domain.com} > 80"
            match_by: ['hostname']
      roles:
        - {role: stackhpc.monasca_default_alarms, tags: [alarms]}

## Monasca Modules Usage
There are two modules available in the library subdirectory, one for Monasca notifications and the other for
alarm definitions. For example:

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
        name: "Host Alive Alarm"
        description: "Trigger when a host alive check fails"
        expression: "host_alive_status > 0"
        keystone_url: "{{ keystone_url }}"
        keystone_user: "{{ keystone_user }}"
        keystone_password: "{{ keystone_password }}"
        keystone_project: "{{ keystone_project }}"
        monasca_api_url: "{{ default_notification.monasca_api_url }}"
        severity: "HIGH"
        alarm_actions:
          - "{{ default_notification.notification_method_id }}"
        ok_actions:
          - "{{ default_notification.notification_method_id }}"
        undetermined_actions:
          - "{{ default_notification.notification_method_id }}"

Refer to the documentation within the module for full detail.


## License
Apache

## Author Information
Originally created by Tim Kuhlman. Rewritten by Isaac Prior to support new Keystone authentication.

Monasca Team IRC: `#openstack-monasca` on `freenode.netmonasca@lists.launchpad.net.`
