#!python3

import yaml
import requests
import urllib3
import json


class AosRz:
    def __init__(self) -> None:
        pass

class AosBp:
    def __init__(self) -> None:
        pass


class AosServer:
    def __init__(self, host: str, port: int, username: str, password: str, session: requests.Session = None) -> None:
        self.session = session
        urllib3.disable_warnings()
        self.http = urllib3.HTTPSConnectionPool(host, port=port, cert_reqs='CERT_NONE', assert_hostname=False)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.json_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json"})
        self._auth()
        self.json_token_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json", "AuthToken": self.token})

    def http_get(self, path) -> urllib3.response.HTTPResponse:
        print(f"==== GET {path}")
        return self.http.request('GET', path, headers=self.json_token_header)

    def http_delete(self, path) -> urllib3.response.HTTPResponse:
        print(f"==== DELETE {path}")
        return self.http.request('DELETE', path, headers=self.json_token_header)

    def http_post(self, path, data, headers=None) -> urllib3.response.HTTPResponse:
        if not headers:
            headers = self.json_token_header
        print(f"==== POST {path}\n{data}")
        return self.http.request('POST', path, body=json.dumps(data), headers=headers)

    def http_put(self, path, data, headers=None) -> urllib3.response.HTTPResponse:
        print(f"==== PUT {path}\n{data}")
        if not headers:
            headers = self.json_token_header
        return self.http.request('PUT', path, body=json.dumps(data), headers=headers)


    def _auth(self) -> None:
        auth_url = "/api/aaa/login"
        auth_spec = {
            "username": self.username,
            "password": self.password
        }
        resp = self.http_post( auth_url, auth_spec, headers=self.json_header)
        self.token = json.loads(resp.data)["token"]
        print(f"token = {self.token}")


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
            resp = self.http_post(ip_pools_url, ip_pools_spec)
            print( f"ip-pool status should be 202: {resp.status}")
            
    def routing_zone_get(self, bp_id, rz_name) -> str:
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http_get(routing_zone_url)
        rzs = json.loads(resp.data)["items"]
        for rz in rzs:
            if rzs[rz]["label"] == rz_name:
                return rzs[rz]["id"]

    def create_routing_zone(self, bp_id, data) -> None:
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones"
        routing_zone_spec =  {
            "sz_type": "evpn",
            "label": data["label"],
            "vrf_name": f"{data['label']}-vrf",
            "vlan_id": data["vlan_id"]
            }
        resp = self.http_post(routing_zone_url, routing_zone_spec)
        print(f"resp of routing-zone should be 201: {resp.status}")
        
        rz_id = self.routing_zone_get(bp_id, data["label"])
        dhcp_server_url = f"/api/blueprints/{bp_id}/security-zones/{rz_id}/dhcp-servers"
        dhcp_server_spec = { "items": data["dhcp_server_spec"] }
        resp = self.http_put(dhcp_server_url, dhcp_server_spec)
        print(f"resp of routing-zone/dhcp-servers should be 204: {resp.status}")

        # "Private-10_0_0_0-8"
        loopback_url = f"/api/blueprints/{bp_id}/resource_groups/ip/" + requests.utils.quote(f"sz:{rz_id},leaf_loopback_ips")
        loopback_spec = {
            "pool_ids": [ prefix.replace("/", "-").replace(".", "_") for prefix in data["leaf_loopback_ips"] ]
        }
        resp = self.http_put(loopback_url, loopback_spec)
        print(f"loopback 202: {resp.status}")

    def context_template_add(self, bp_id, policies):
        policy_url = f"/api/blueprints/{bp_id}/obj-policy-import"
        policy_spec = {
            "policies": policies
        }
        resp = self.http_put(policy_url, policy_spec)
        print(f"policies 204: {resp.status}")

    def context_template_delete(self, bp_id, ct_id) -> None:
        resp = self.http_delete(f"/api/blueprints/{bp_id}/endpoint-policies/{ct_id}?delete_recursive=true")
        print(f"resp policies - get 204: {resp.status}")

    def virtual_networks_find(self, bp_id, vn_name) -> str:
        vn_find_url = f"/api/blueprints/{bp_id}/virtual-networks"
        resp = self.http_get(vn_find_url)
        if resp.status == 200:
            vns = json.loads(resp.data)["virtual_networks"]
            for vn in vns:
                if vns[vn]["label"] == vn_name:
                    return vns[vn]["id"]
        else:
            print(f"vn_get 200 ok: {resp.status}")
            print(resp.data)
            return "Error"

    # not ready
    def virtual_networks_batch(self, bp_id, networks):
        vn_batch_url = f"/api/blueprints/{bp_id}/virtual-networks-batch?async=full"
        vn_batch_spec = {
            "virtual-networks": networks
        }
        resp = self.http_post(vn_batch_url, vn_batch_spec)
        if resp.status != 202: #accepted
            print(f"vn_batch_spec status: {resp.status}\n{resp.data}")

    def virtual_networks_add(self, bp_id, networks):
        vn_batch_url = f"/api/blueprints/{bp_id}/virtual-networks"
        for vn in networks:
            resp = self.http_post(vn_batch_url, vn)
            print(f"== vn_add 201 created: {resp.status}")
            if resp.status != 201:
                print(resp.data)


    def virtual_networks_delete(self, bp_id, vn_name ) -> None:
        vn_id = self.virtual_networks_find(bp_id, vn_name)
        vn_url = f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}?async=full"
        resp = self.http_delete(vn_url)
        print(f"vn-delete 202 accepted: {resp.status}")


# post https://18.224.213.67:20759/api/blueprints/evpn-vqfx_offbox-virtual/virtual-networks-batch?async=full
# 202 accepted
# test1234 = { "virtual_networks":[{"virtual_gateway_ipv4_enabled":true,"vn_id":null,"vn_type":"vxlan","svi_ips":[{"system_id":"a4295414-0810-43dd-913e-32075b581a62","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null},{"system_id":"f05f2abb-fd9f-4c09-91a7-76ce06bcb5e4","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null},{"system_id":"08a0bd88-6184-48da-9d8c-4261ff259b86","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null}],"virtual_gateway_ipv4":null,"ipv6_subnet":null,"bound_to":[{"system_id":"dc31602f-fc0a-4388-a1eb-7a1dc19eca6e","access_switch_node_ids":[],"vlan_id":801},{"system_id":"08a0bd88-6184-48da-9d8c-4261ff259b86","access_switch_node_ids":[],"vlan_id":801}],"vni_ids":[],"virtual_gateway_ipv6":null,"ipv4_subnet":"8.0.1.0/24","rt_policy":{"import_RTs":null,"export_RTs":null},"label":"c-801","ipv4_enabled":true,"virtual_gateway_ipv6_enabled":false,"ipv6_enabled":false,"security_zone_id":"ccd2d9a6-1fc0-46b4-a1c4-9000faf25a59","dhcp_service":"dhcpServiceDisabled","create_policy_tagged":true}]}


def main():
    with open(r'inventory.yaml') as file:
        AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
        # print(AOS_ENV)

    aos_server = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])

    # aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])

    # aos_server.create_routing_zone(AOS_ENV["blueprints"][0]["id"], AOS_ENV["blueprints"][0]["routing_zones"][0])

    # aos_server.context_template_add(AOS_ENV["blueprints"][0]["id"], AOS_ENV["blueprints"][0]["policies"])

    aos_server.virtual_networks_add(AOS_ENV["blueprints"][0]["id"], AOS_ENV["blueprints"][0]["routing_zones"][0]["virtual_networks"])


    # aos_server.context_template_delete(AOS_ENV["blueprints"][0]["id"], "test1234")

    # aos_server.virtual_networks_delete(AOS_ENV["blueprints"][0]["id"], "c-801")



if __name__ == "__main__":
    main()







