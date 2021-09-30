from ansible.module_utils.basic import AnsibleModule


def main():
    module_args = dict(
        systems=dict(type='list', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    vns_from_systems = {}
    for system in module.params['systems']:
        system_label = system["label"]
        if "interfaces" not in system:
            continue
        for interface in system["interfaces"]:
            if_name = interface["if_name"]
            if "vns" not in interface:
                continue
            for vn in interface["vns"]:
                if vn not in vns_from_systems:
                    vns_from_systems[vn] = []
                vns_from_systems[vn].append({ "system": system_label, "if_name": if_name})
    
    module.exit_json(changed=False,
                     result=vns_from_systems)

if __name__ == '__main__':
    main()
