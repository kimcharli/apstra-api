from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        spec=dict(type='dict', required=True),
        routing_zone_id=dict(type='str', Required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spec_in = module.params['spec']
    spec_in['security_zone_id'] = module.params['routing_zone_id']
    
    module.exit_json(changed=False,
                     result=spec_in)

if __name__ == '__main__':
    main()