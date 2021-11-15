#!python3

import yaml
import requests
import urllib3
import json
import sys
import time
from read_xlsx import AosXlsx


class AosVn:
    def __init__(self, aos_server, bp, rz, vn_id, virtualnetwork) -> None:
        self.aos_server = aos_server
        self.bp = bp
        self.rz = rz
        self.id = vn_id
        self.data = virtualnetwork
        print(f"==== AosVn.data: {self.data}")
        self.create()

    def get_system_interface_uuid(self, system_name, interface_name):
        system_query = {
            "blueprint-id": self.bp.id,
            # "query": f"node('system', name='system', label='{system_name}').out"
            "query": f"node('system', name='system', label='{system_name}').out('hosted_interfaces').node('interface',if_name='{interface_name}',name='interface')"
        }
        system_data = json.loads(self.aos_server.graph_query(self.bp.id, system_query).data)
        print(f"==== get_system_uuid(): system_data: {system_data}")
        system_uuid = system_data["items"][0]["system"]["id"]
        print(f"==== get_system_uuid(): system_uuid: {system_uuid}")
        interface_uuid = system_data["items"][0]["interface"]["id"]
        print(f"==== get_system_uuid(): interface_uuid: {interface_uuid}")
        return (system_uuid, interface_uuid)


    def create(self):
        bound_to = []
        interface_uuid_list = []
        for system_name, system in self.bp.data["systems"].items():
            system_uuid = ''
            for interface_name, interface in system["interfaces"].items():
                print(f"==== create(): interface: {interface}")
                print(f"==== create(): vns: {interface['vns']}")
                if not interface or not interface['vns']:
                    continue
                vns_acquired = interface["vns"].split(",")
                print(f"==== create(): vns: {vns_acquired}")
                if self.id in vns_acquired:
                    if not system_uuid:
                        (system_uuid, interface_uuid) = self.get_system_interface_uuid(system_name, interface_name)
                    bound_to.append({ "system_id": system_uuid, "access_switch_node_ids": [], "vlan_id": self.data["vlan_id"] })
                    interface_uuid_list.append(interface_uuid)
                    break
        print(f"==== create(): bound_to: {bound_to}")

        vn_spec = {
            "label": self.id,
            "description": self.data["description"],
            "vn_type": self.data["vn_type"],
            "vlan_id": self.data["vlan_id"],
            "bound_to": bound_to,
            "virtual_gateway_ipv4_enabled": self.data["virtual_gateway_ipv4_enabled"],
            "ipv4_enabled": self.data["ipv4_enabled"],
            "ipv4_subnet": self.data["ipv4_subnet"],
            "dhcp_service": self.data["dhcp_server"],
            "security_zone_id": self.rz.uuid
        }
        vn_batch_url = f"/api/blueprints/{self.bp.id}/virtual-networks"
        policy_import_url = f"/api/blueprints/{self.bp.id}/obj-policy-import"

        # update networks with system_id and create VN
        new_vn = self.aos_server.http_post(vn_batch_url, vn_spec, expected=201)
        self.uuid = json.loads(new_vn.data)["id"]

        # create connectivity template for the VN created
        policy_name = f"{self.rz.id}_{vn_spec['vn_type']}_{vn_spec['vlan_id']}_vlan_tagged"
        vn_ep_name = f"vn_endpoints_{policy_name}"
        vn_policy = {
            "policies": [
                {
                    "id": vn_ep_name,
                    "label": vn_ep_name,
                    "description": f"vlan {self.id} vxlan vlan tagged",
                    "policy_type_name": "batch",
                    "attributes": {
                        "subpolicies": [
                            f"pipeline_{policy_name}"
                        ]
                    },
                    "user_data": "{\"isSausage\": true}",
                    "visible": True,
                    "tags": [],
                },
                {
                    "id": f"pipeline_{policy_name}",
                    "label": "Virtual Network (Single) (pipeline)",
                    "description": "Add a single VLAN to interfaces, as tagged or untagged.",
                    "policy_type_name": "pipeline",
                    "attributes": {
                        "first_subpolicy": policy_name,
                        "second_subpolicy": f"noop_{policy_name}"
                    },
                    "visible": False,
                    "tags": []                    
                },
                {
                    "id": policy_name,
                    "label": "Virtual Network (Single)",
                    "description": "",
                    "policy_type_name": "AttachSingleVLAN",
                    "attributes": {
                        "vn_node_id": self.uuid,
                        "tag_type": "vlan_tagged"
                    },
                    "visible": False,
                    "tags": [],
                },
                {
                    "id": f"noop_{policy_name}",
                    "label": "noop",
                    "description": "",
                    "policy_type_name": "noop",
                    "attributes": {},
                    "visible": False,
                    "tags": [],
                }
            ]
        }
        ep_result = self.aos_server.http_put(policy_import_url, vn_policy, expected=204)
        print(f"== create(): ep_result.data: {ep_result.data}")
        # print(f"== create(): ep result is empty: {json.loads(ep_result.data)}")

        # associate the connectivity template to the interfaces
        policy_attach_url = f"/api/blueprints/{self.bp.id}/obj-policy-batch-apply?async=full"

        for if_uuid in interface_uuid_list:
            policy_attach_list = {
                "application_points": [
                    {
                        "id": if_uuid,
                        "policies": [{"policy": vn_ep_name,"used": True}]
                    } 
                ]
            }
            self.aos_server.http_patch(policy_attach_url, policy_attach_list, expected=202)



class AosRz:
    def __init__(self, aos_server, bp, rz_id, routingzone) -> None:
        self.aos_server = aos_server
        self.bp = bp
        self.id = rz_id
        self.data = routingzone
        print(f"==== AosRz.__init__: data: {self.data}")
        self.create()

    def create(self) -> None:        
        print("====== AosRz.create()")
        routing_zone_url = f"/api/blueprints/{self.bp.id}/security-zones"
        routing_zone_spec =  {
            "sz_type": "evpn",
            "label": self.id,
            "vrf_name": f"{self.id}-vrf",
            "vlan_id": self.data["vlan_id"]
            # "vni_id": 20220
            }
        resp = self.aos_server.http_post(routing_zone_url, routing_zone_spec, expected=201)
        print(f"==== create(): resp: {resp.data}")
        self.uuid = json.loads(resp.data)["id"]
        print(f"==== create(): uuid: {self.uuid}")

        # rz_query = {
        #     "blueprint-id": self.bp.id,
        #     "query": f"node('security_zone', name='n1', label='{self.id}')"
        # }
        # rz_data = json.loads(self.aos_server.graph_query(self.bp.id, rz_query).data)
        # print(f"==== create(): rz_data: {rz_data}")
        # self.uuid = rz_data["items"][0]["n1"]["id"]
        # print(f"==== self.uuid: {rz_uuid}")

        dhcp_server_url = f"/api/blueprints/{self.bp.id}/security-zones/{self.uuid}/dhcp-servers"
        dhcp_server_spec = { "items": self.data["dhcp_servers"] }
        resp = self.aos_server.http_put(dhcp_server_url, dhcp_server_spec, expected=204)

        # "Private-10_0_0_0-8"
        loopback_url = f"/api/blueprints/{self.bp.id}/resource_groups/ip/" + requests.utils.quote(f"sz:{self.uuid},leaf_loopback_ips")
        loopback_spec = {
            "pool_ids": [ prefix.replace("/", "-").replace(".", "_") for prefix in self.data["leaf_loopback_ips"] ]
        }
        resp = self.aos_server.http_put(loopback_url, loopback_spec, expected=202)

        for vn_id, vn in self.data["virtual_networks"].items():
            vn = AosVn(self.aos_server, self.bp, self, vn_id, vn )



class AosBp:
    def __init__(self, aos_server, bp_id: str, blueprint: dict, phase: str) -> None:
        print_prefix = "==== AosBp.__init():"
        self.aos_server = aos_server
        print(f"{print_prefix} blueprint={bp_id}")
        self.id = bp_id
        self.data = blueprint
        self.phase = phase
        print(f"{print_prefix} data: {self.data}")

        if self.phase == "day1":
            bp_url = f"/api/blueprints?async=full"
            bp_spec = {
                "design": self.data["design"],
                "init_type": self.data["init_type"],
                "label": self.id,
                "template_id": self.data["template_id"]
            }            
            resp = self.aos_server.http_post(bp_url, bp_spec, expected=202)
            print(f"{print_prefix} resp: {resp.data}")
            self.uuid = json.loads(resp.data)["id"]
            task_id = json.loads(resp.data)["task_id"]
            print(f"{print_prefix} uuid: {self.uuid}, task_id: {task_id}")

            for i in range(5):
                task_url = f"/api/blueprints/{self.uuid}/tasks/{task_id}"
                resp = self.aos_server.http_get(task_url)
                task_status = json.loads(resp.data)['status']
                print(f"{print_prefix} task status: {task_status}")
                if task_status == "succeeded":
                    break
                time.sleep(5)


            asns_spines_url = f"/api/blueprints/{self.uuid}/resource_groups/asn/spine_asns"
            asns_spines_spec = {
                "pool_ids": self.data["asns_spines"].split(',')
            }
            resp = self.aos_server.http_put(asns_spines_url, asns_spines_spec, expected=202)
            # empty payload

            asns_leaf_url = f"/api/blueprints/{self.uuid}/resource_groups/asn/leaf_asns"
            asns_leaf_spec = {
                "pool_ids": self.data["asns_leafs"].split(',')
            }
            resp = self.aos_server.http_put(asns_leaf_url, asns_leaf_spec, expected=202)
            # empty payload

            lo0_spines_url = f"/api/blueprints/{self.uuid}/resource_groups/ip/spine_loopback_ips"
            lo0_spines_spec = {
                "pool_ids": self.data["spine_loopback_ips"].split(',')
            }
            resp = self.aos_server.http_put(lo0_spines_url, lo0_spines_spec, expected=202)
            # empty payload

            lo0_leafs_url = f"/api/blueprints/{self.uuid}/resource_groups/ip/leaf_loopback_ips"
            lo0_leafs_spec = {
                "pool_ids": self.data["leaf_loopback_ips"].split(',')
            }
            resp = self.aos_server.http_put(lo0_leafs_url, lo0_leafs_spec, expected=202)
            # empty payload

            spine_leaf_link_ips_url = f"/api/blueprints/{self.uuid}/resource_groups/ip/spine_leaf_link_ips"
            spine_leaf_link_ips_spec = {
                "pool_ids": self.data["spine_leaf_link_ips"].split(',')
            }
            resp = self.aos_server.http_put(spine_leaf_link_ips_url, spine_leaf_link_ips_spec, expected=202)
            # empty payload







        if self.phase == "day2":
            self.create_routingzones()
            resp = self.commit("commit by script")

    def create_routingzones(self) -> None:
        for rz_id in self.data["routing_zones"]:
            rz = AosRz(self.aos_server, self, rz_id, self.data["routing_zones"][rz_id] )


    def commit(self, description='commit by script') -> urllib3.response.HTTPResponse:
        # get revision id
        revision_url = f"/api/blueprints/{self.id}/revisions"
        revision_data = json.loads(self.aos_server.http_get(revision_url,expected=200).data)
        revision_id = int(revision_data["items"][-1]["revision_id"]) + 10

        # check the tasks - need more check than this
        task_url = f"/api/blueprints/{self.id}/tasks?mode=full&filter=status%20in%20%5B%27in_progress%27%2C%20%27init%27%5D"
        while True:
            resp = self.aos_server.http_get(task_url,expected=200)
            running_task_count = len(json.loads(resp.data)["items"])
            print(f"==== tasks running: {resp.data}")
            if running_task_count:
                print(f"==== tasks running: {running_task_count}")
                time.sleep(5)
            else:
                break

        # TODO: fix. currently needs GUI to commit
        commit_url = f"/api/blueprints/{self.id}/deploy?async=full"
        commit_data = {
            "version": revision_id,
            "description": description
        }
        resp = self.aos_server.http_put(commit_url, commit_data, expected=202)
        print(f"==== AosBP.commit(): resp: {resp.data}")
        return resp



class AosServer:
    def __init__(self, inventory) -> None:
        # host: str, port: int, username: str, password: str, session: requests.Session = None) -> None:
        # self.session = session
        # print(f"==== __init__(): {inventory}")
        self.inventory = inventory
        urllib3.disable_warnings()
        self.http = urllib3.HTTPSConnectionPool(inventory["aos_server"]["host"], port=inventory["aos_server"]["port"], cert_reqs='CERT_NONE', assert_hostname=False)

        self.json_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json"})
        self._auth()
        self.json_token_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json", "AuthToken": self.token})

    def http_get(self, path, expected=None) -> urllib3.response.HTTPResponse:
        print(f"==== GET {path}")
        resp = self.http.request('GET', path, headers=self.json_token_header)
        if expected:
            print(f"== status (expect {expected}): {resp.status}")
            if resp.status != expected:
                print(f"== body: {resp.data}")
        else:
            print(f"== status: {resp.status}")
        return resp

    def http_delete(self, path, expected=None) -> urllib3.response.HTTPResponse:
        print(f"==== DELETE {path}")
        resp = self.http.request('DELETE', path, headers=self.json_token_header)
        if expected:
            print(f"== status (expect {expected}): {resp.status}")
            if resp.status != expected:
                print(f"== body: {resp.data}")
        else:
            print(f"== status: {resp.status}")
        return resp
        

    def http_post(self, path, data, headers=None, expected=None) -> urllib3.response.HTTPResponse:
        if not headers:
            headers = self.json_token_header
        print(f"==== POST {path}\n{data}")
        resp = self.http.request('POST', path, body=json.dumps(data), headers=headers)
        if expected:
            print(f"== status (expect {expected}): {resp.status}")
            if resp.status != expected:
                print(f"== body: {resp.data}")
        else:
            print(f"== status: {resp.status}")
        return resp

    def http_put(self, path, data, headers=None, expected=None) -> urllib3.response.HTTPResponse:
        print(f"==== PUT {path}\n{data}")
        if not headers:
            headers = self.json_token_header
        resp = self.http.request('PUT', path, body=json.dumps(data), headers=headers)
        if expected:
            print(f"== status (expect {expected}): {resp.status}")
            if resp.status != expected:
                print(f"== body: {resp.data}")
        else:
            print(f"== status: {resp.status}")
        return resp

    def http_patch(self, path, data, headers=None, expected=None) -> urllib3.response.HTTPResponse:
        print(f"==== PATCH {path}\n{data}")
        if not headers:
            headers = self.json_token_header
        resp = self.http.request('PATCH', path, body=json.dumps(data), headers=headers)
        if expected:
            print(f"== status (expect {expected}): {resp.status}")
            if resp.status != expected:
                print(f"== body: {resp.data}")
        else:
            print(f"== status: {resp.status}")
        return resp

    def graph_query(self, bp_id, query) -> urllib3.response.HTTPResponse:
        # query_url = f"/api/blueprints/{bp_id}/qe?type=operation"
        query_url = f"/api/blueprints/{bp_id}/qe?type=staging"
        resp = self.http_post(query_url, query, expected=200)
        return resp


    def _auth(self) -> None:
        auth_url = "/api/aaa/login"
        auth_spec = {
            "username": self.inventory["aos_server"]["username"],
            "password": self.inventory["aos_server"]["password"]
        }
        resp = self.http_post( auth_url, auth_spec, headers=self.json_header, expected=201)
        self.token = json.loads(resp.data)["token"]
        print(f"== token: {self.token}")
    


    def create_blueprints(self, phase: str) -> None:
        print_prefix = "==== AosServer.create_blueprints:"
        print(f"{print_prefix} self.inventory[bp]: {self.inventory['blueprints']}")
        self.phase = phase       
        for bp_id in self.inventory["blueprints"]:
            AosBp(self, bp_id, self.inventory["blueprints"][bp_id], phase)



    def create_IP_Pool(self, pools) -> None:
        ip_pools_url = "/api/resources/ip-pools"
        for pool in pools:
            print( pool )
            ip_pools_spec = {
                "subnets": [{"network": network} for network in pool["subnets"]], 
                "tags": pool["tags"],
                "display_name": pool["name"],
                "id": pool["name"],
            }
            resp = self.http_post(ip_pools_url, ip_pools_spec, expected=202)
            

    # def routing_zone_delete(self, bp_id, routing_zone_name) -> None:
    #     routing_zone_id = self.routing_zone_get(bp_id, routing_zone_name)
    #     routing_zone_url = f"/api/blueprints/{bp_id}/security-zones/{routing_zone_id}"
    #     self.http_delete(routing_zone_url, expected=204)


    # def context_template_delete(self, bp_id, ct_id) -> None:
    #     resp = self.http_delete(f"/api/blueprints/{bp_id}/endpoint-policies/{ct_id}?delete_recursive=true", expected=204)



    def commit(self, bp_id, description='commit by script') -> urllib3.response.HTTPResponse:
        # get revision id
        revision_url = f"/api/blueprints/{bp_id}/revisions"
        revision_data = json.loads(self.http_get(revision_url,expected=200).data)
        revision_id = int(revision_data["items"][-1]["revision_id"]) + 10

        # TODO: fix. currently needs GUI to commit
        commit_url = f"/api/blueprints/{bp_id}/deploy?async=full"
        commit_data = {
            "version": revision_id,
            "description": description
        }
        resp = self.http_put(commit_url, commit_data, expected=202)
        return resp




def main():
    print_prefix = "======== main():"
    fabric_excel = "fabric-day1.xlsx"
    fabric_yaml = "temp/temp.yaml"
    if len(sys.argv) > 1:
        fabric_excel = sys.argv[1]
    print(f"{print_prefix} sys.argv: {sys.argv}")
    print(f"{print_prefix} fabric_excel: {fabric_excel}")
    print(f"{print_prefix} fabric_excel: {fabric_yaml}")
    wb = AosXlsx(fabric_excel, fabric_yaml)
    wb.run_all()
    print(f"{print_prefix} inventory: {wb.inventory}")
    aos_server = AosServer(wb.inventory)
    

    print( f"{print_prefix} blueprint creating")
    # aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])
    aos_server.create_blueprints("day1")
    # # TODO: implement async
    # # time.sleep(10)
    # aos_server.commit(bp_id)
    print( f"{print_prefix} blueprint done")

if __name__ == "__main__":
    main()








