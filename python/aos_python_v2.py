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

    def get_system_uuid(self, system_name):
        system_query = {
            "blueprint-id": self.bp.id,
            "query": f"node('system', name='n1', label='{system_name}')"
        }
        system_data = json.loads(self.aos_server.graph_query(self.bp.id, system_query).data)
        # print(f"==== rz_data: {rz_data}")
        system_uuid = system_data["items"][0]["n1"]["id"]
        print(f"==== system_uuid: {system_uuid}")
        return system_uuid


    def create(self):
        bound_to = []
        for system_name, system in self.bp.data["systems"].items():
            system_uuid = ''
            for interface_name, interface in system["interfaces"].items():
                print(f"==== create: interface: {interface}")
                print(f"==== create: vns: {interface['vns']}")
                if not interface or not interface['vns']:
                    continue
                vns_acquired = interface["vns"].split(",")
                print(f"==== create: vns: {vns_acquired}")
                if self.id in vns_acquired:
                    if not system_uuid:
                        system_uuid = self.get_system_uuid(system_name)
                    bound_to.append({ "system_id": system_uuid, "access_switch_node_ids": [], "vlan_id": self.data["vlan_id"] })
                    break
        print(f"==== bound_to: {bound_to}")

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
        vn_node_id = json.loads(new_vn.data)["id"]

        # # create connectivity template for the VN created
        # policy_name = f"{routing_zone_label}_{vn['vn_type']}_{vn['vlan_id']}_vlan_tagged"
        # vn_ep_name = f"vn_endpoints_{policy_name}"
        # vn_policy = {
        #     "policies": [
        #         {
        #             "id": vn_ep_name,
        #             "label": vn_ep_name,
        #             "description": f"vlan {vn['label']} vxlan vlan tagged",
        #             "policy_type_name": "batch",
        #             "attributes": {
        #                 "subpolicies": [
        #                     f"pipeline_{policy_name}"
        #                 ]
        #             },
        #             "user_data": "{\"isSausage\": true}",
        #             "visible": True,
        #             "tags": [],
        #         },
        #         {
        #             "id": f"pipeline_{policy_name}",
        #             "label": "Virtual Network (Single) (pipeline)",
        #             "description": "Add a single VLAN to interfaces, as tagged or untagged.",
        #             "policy_type_name": "pipeline",
        #             "attributes": {
        #                 "first_subpolicy": policy_name,
        #                 "second_subpolicy": f"noop_{policy_name}"
        #             },
        #             "visible": False,
        #             "tags": []                    
        #         },
        #         {
        #             "id": policy_name,
        #             "label": "Virtual Network (Single)",
        #             "description": "",
        #             "policy_type_name": "AttachSingleVLAN",
        #             "attributes": {
        #                 "vn_node_id": vn_node_id,
        #                 "tag_type": "vlan_tagged"
        #             },
        #             "visible": False,
        #             "tags": [],
        #         },
        #         {
        #             "id": f"noop_{policy_name}",
        #             "label": "noop",
        #             "description": "",
        #             "policy_type_name": "noop",
        #             "attributes": {},
        #             "visible": False,
        #             "tags": [],
        #         }
        #     ]
        # }
        # ep_result = self.http_put(policy_import_url, vn_policy, expected=204)
        # # print(f"== ep result is empty: {json.loads(ep_result.data)}")

        # # associate the connectivity template to the interfaces
        # if vn['label'] not in vns_from_systems or interface not in vns_from_systems[vn['label']]:
        #     continue
        # for interface in vns_from_systems[vn['label']]:
        #     # get interface id from graph db
        #     interface_query = {
        #         "blueprint-id": bp_id,
        #         "query": f"node('system', label='{system_label}').out('hosted_interfaces').node('interface',if_name='{if_name}',name='interface')"
        #     }
        #     interface_data = json.loads(self.graph_query(bp_id, interface_query).data)
        #     if_id = interface_data['items'][0]['interface']['id']
        #     print( f"== if_id: {if_id}")

        #     policy_attach_list = {
        #         "application_points": [
        #             {
        #                 "id": if_id,
        #                 "policies": [{"policy": vn_ep_name,"used": True}]
        #             } 
        #         ]
        #     }
        #     self.http_patch(policy_attach_url, policy_attach_list, expected=202)





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

        rz_query = {
            "blueprint-id": self.bp.id,
            "query": f"node('security_zone', name='n1', label='{self.id}')"
        }
        rz_data = json.loads(self.aos_server.graph_query(self.bp.id, rz_query).data)
        print(f"==== rz_data: {rz_data}")
        self.uuid = rz_data["items"][0]["n1"]["id"]
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
    def __init__(self, aos_server, bp_id, blueprint) -> None:
        self.aos_server = aos_server
        print(f"==== AosBP.__init__(): blueprint={bp_id}")
        self.id = bp_id
        self.data = blueprint
        print(f"==== AosBP.__init__: data: {self.data}")
        self.create_routingzones()

    def create_routingzones(self) -> None:
        for rz_id in self.data["routing_zones"]:
            rz = AosRz(self.aos_server, self, rz_id, self.data["routing_zones"][rz_id] )



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
    


    def create_blueprints(self) -> None:
        print(f"==== self.inventory[bp]: {self.inventory['blueprints']}")
        for bp_id in self.inventory["blueprints"]:
            AosBp(self, bp_id, self.inventory["blueprints"][bp_id] )



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
            

    def routing_zone_delete(self, bp_id, routing_zone_name) -> None:
        routing_zone_id = self.routing_zone_get(bp_id, routing_zone_name)
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones/{routing_zone_id}"
        self.http_delete(routing_zone_url, expected=204)


    def context_template_delete(self, bp_id, ct_id) -> None:
        resp = self.http_delete(f"/api/blueprints/{bp_id}/endpoint-policies/{ct_id}?delete_recursive=true", expected=204)

    def virtual_networks_find(self, bp_id, vn_name) -> str:
        vn_find_url = f"/api/blueprints/{bp_id}/virtual-networks"
        resp = self.http_get(vn_find_url, expected=200)
        if resp.status == 200:
            vns = json.loads(resp.data)["virtual_networks"]
            for vn in vns:
                if vns[vn]["label"] == vn_name:
                    return vns[vn]["id"]
        else:
            print(resp.data)
            return "Error"

    # not ready
    def virtual_networks_batch(self, bp_id, networks):
        vn_batch_url = f"/api/blueprints/{bp_id}/virtual-networks-batch?async=full"
        vn_batch_spec = {
            "virtual-networks": networks
        }
        resp = self.http_post(vn_batch_url, vn_batch_spec, expected=202)
        if resp.status != 202: #accepted
            print(f"vn_batch_spec: {resp.data}")


    def virtual_networks_add(self, bp_id, networks, routing_zone_label, systems):
        policy_attach_url = f"/api/blueprints/{bp_id}/obj-policy-batch-apply?async=full"

        # build dict from systems to be used for policy
        vns_from_systems = {}    # { VN: [{system: label, if_name: name}] }
        for system in systems:
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
        print(f"== vn_from_systems: {vns_from_systems}")

        # build dict system_id from nodes 
        nodes_url = f"/api/blueprints/{bp_id}/nodes"
        nodes = json.loads(self.http_get(nodes_url, expected=200).data)['nodes']
        system_ids = {} # system_label: system_id
        for k, v in nodes.items():
            if v["type"] == "system":
                system_ids[v["label"]] = v["id"]

        routing_zone_id = self.routing_zone_get(bp_id, routing_zone_label)
        vn_batch_url = f"/api/blueprints/{bp_id}/virtual-networks"
        policy_import_url = f"/api/blueprints/{bp_id}/obj-policy-import"
        for vn in networks:
            # update networks with system_id and create VN
            vn["security_zone_id"] = routing_zone_id
            for i in range(len(vn["bound_to"])):
                vn["bound_to"][i]["system_id"] = system_ids[vn["bound_to"][i]["system_label"]]
                # print(system)
            new_vn = self.http_post(vn_batch_url, vn, expected=201)
            vn_node_id = json.loads(new_vn.data)["id"]

            # create connectivity template for the VN created
            policy_name = f"{routing_zone_label}_{vn['vn_type']}_{vn['vlan_id']}_vlan_tagged"
            vn_ep_name = f"vn_endpoints_{policy_name}"
            vn_policy = {
                "policies": [
                    {
                        "id": vn_ep_name,
                        "label": vn_ep_name,
                        "description": f"vlan {vn['label']} vxlan vlan tagged",
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
                            "vn_node_id": vn_node_id,
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
            ep_result = self.http_put(policy_import_url, vn_policy, expected=204)
            # print(f"== ep result is empty: {json.loads(ep_result.data)}")

            # associate the connectivity template to the interfaces
            if vn['label'] not in vns_from_systems or interface not in vns_from_systems[vn['label']]:
                continue
            for interface in vns_from_systems[vn['label']]:
                # get interface id from graph db
                interface_query = {
                    "blueprint-id": bp_id,
                    "query": f"node('system', label='{system_label}').out('hosted_interfaces').node('interface',if_name='{if_name}',name='interface')"
                }
                interface_data = json.loads(self.graph_query(bp_id, interface_query).data)
                if_id = interface_data['items'][0]['interface']['id']
                print( f"== if_id: {if_id}")

                policy_attach_list = {
                    "application_points": [
                       {
                           "id": if_id,
                           "policies": [{"policy": vn_ep_name,"used": True}]
                       } 
                    ]
                }
                self.http_patch(policy_attach_url, policy_attach_list, expected=202)

    def virtual_networks_delete(self, bp_id, vn_name ) -> urllib3.response.HTTPResponse:
        vn_id = self.virtual_networks_find(bp_id, vn_name)
        vn_url = f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}?async=full"
        return self.http_delete(vn_url, expected=202)


    def commit(self, bp_id, description='') -> urllib3.response.HTTPResponse:
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
    wb = AosXlsx("fabric-1.xlsx", "temp/temp.yaml")
    wb.run_all()
    print(f"====== inventory: {wb.inventory}")
    aos_server = AosServer(wb.inventory)
    

    print( "creating")
    # aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])
    aos_server.create_blueprints()
    # aos_server.routing_zone_add(bp_id, AOS_ENV["blueprints"][0]["routing_zones"][0])
    # aos_server.virtual_networks_add(bp_id, AOS_ENV["blueprints"][0]["routing_zones"][0]["virtual_networks"], AOS_ENV["blueprints"][0]["routing_zones"][0]["label"], AOS_ENV["blueprints"][0]["systems"])
    # # TODO: implement async
    # # time.sleep(10)
    # aos_server.commit(bp_id)

if __name__ == "__main__":
    main()







