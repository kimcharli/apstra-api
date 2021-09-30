from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        systems=dict(type='dict', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    system_ids = {} # system_label: system_id
    for system in module.params['systems']['items']:
        system_ids[system['system']['label']] = system['system']['id']

    module.exit_json(changed=False,
                     result=system_ids)

if __name__ == '__main__':
    main()

