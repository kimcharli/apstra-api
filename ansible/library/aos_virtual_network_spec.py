# from typing_extensions import Required
from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        spec=dict(type='dict', required=True),
        routing_zone_id=dict(type='str', required=True),
        systems=dict(type='dict', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    updated_spec = module.params['spec']
    updated_spec['security_zone_id'] = module.params['routing_zone_id']

    for i in range(len(updated_spec["bound_to"])):
        updated_spec["bound_to"][i]["system_id"] = module.params['systems'][updated_spec["bound_to"][i]["system_label"]]
    
    module.exit_json(changed=False,
                     result=updated_spec)

if __name__ == '__main__':
    main()