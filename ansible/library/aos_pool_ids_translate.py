from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        data=dict(type='list', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    data_in = module.params['data']
    data_out = [ x.replace('/','-').replace('.','_') for x in data_in ]
    
    module.exit_json(changed=False,
                     result=data_out)

if __name__ == '__main__':
    main()