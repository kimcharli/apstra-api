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


    def _auth(self) -> None:
        auth_url = "/api/aaa/login"
        auth_spec = {
            "username": self.username,
            "password": self.password
        }
        resp = self.http_post( auth_url, auth_spec, headers=self.json_header, expected=201)
        self.token = json.loads(resp.data)["token"]
        print(f"== token: {self.token}")


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
            
    def routing_zone_get(self, bp_id, rz_name) -> str:
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http_get(routing_zone_url)
        rzs = json.loads(resp.data)["items"]
        for rz in rzs:
            if rzs[rz]["label"] == rz_name:
                return rzs[rz]["id"]

    def routing_zone_add(self, bp_id, data) -> None:
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones"
        routing_zone_spec =  {
            "sz_type": "evpn",
            "label": data["label"],
            "vrf_name": f"{data['label']}-vrf",
            "vlan_id": data["vlan_id"]
            }
        resp = self.http_post(routing_zone_url, routing_zone_spec, expected=201)
        
        routing_zone_id = self.routing_zone_get(bp_id, data["label"])
        dhcp_server_url = f"/api/blueprints/{bp_id}/security-zones/{routing_zone_id}/dhcp-servers"
        dhcp_server_spec = { "items": data["dhcp_servers"] }
        resp = self.http_put(dhcp_server_url, dhcp_server_spec, expected=204)

        # "Private-10_0_0_0-8"
        loopback_url = f"/api/blueprints/{bp_id}/resource_groups/ip/" + requests.utils.quote(f"sz:{routing_zone_id},leaf_loopback_ips")
        loopback_spec = {
            "pool_ids": [ prefix.replace("/", "-").replace(".", "_") for prefix in data["leaf_loopback_ips"] ]
        }
        resp = self.http_put(loopback_url, loopback_spec, expected=202)

    def routing_zone_delete(self, bp_id, routing_zone_name) -> None:
        routing_zone_id = self.routing_zone_get(bp_id, routing_zone_name)
        routing_zone_url = f"/api/blueprints/{bp_id}/security-zones/{routing_zone_id}"
        self.http_delete(routing_zone_url, expected=204)


    def context_template_add(self, bp_id, policies):
        policy_url = f"/api/blueprints/{bp_id}/obj-policy-import"
        policy_spec = {
            "policies": policies
        }
        resp = self.http_put(policy_url, policy_spec, expected=204)

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

    def virtual_networks_add(self, bp_id, networks, routing_zone_label ):
        routing_zone_id = self.routing_zone_get(bp_id, routing_zone_label)
        vn_batch_url = f"/api/blueprints/{bp_id}/virtual-networks"
        for vn in networks:
            vn["security_zone_id"] = routing_zone_id
            self.http_post(vn_batch_url, vn, expected=201)


    def virtual_networks_delete(self, bp_id, vn_name ) -> None:
        vn_id = self.virtual_networks_find(bp_id, vn_name)
        vn_url = f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}?async=full"
        self.http_delete(vn_url, expected=202)


# post https://18.224.213.67:20759/api/blueprints/evpn-vqfx_offbox-virtual/virtual-networks-batch?async=full
# 202 accepted
# test1234 = { "virtual_networks":[{"virtual_gateway_ipv4_enabled":true,"vn_id":null,"vn_type":"vxlan","svi_ips":[{"system_id":"a4295414-0810-43dd-913e-32075b581a62","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null},{"system_id":"f05f2abb-fd9f-4c09-91a7-76ce06bcb5e4","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null},{"system_id":"08a0bd88-6184-48da-9d8c-4261ff259b86","ipv4_mode":"enabled","ipv4_addr":null,"ipv6_mode":"disabled","ipv6_addr":null}],"virtual_gateway_ipv4":null,"ipv6_subnet":null,"bound_to":[{"system_id":"dc31602f-fc0a-4388-a1eb-7a1dc19eca6e","access_switch_node_ids":[],"vlan_id":801},{"system_id":"08a0bd88-6184-48da-9d8c-4261ff259b86","access_switch_node_ids":[],"vlan_id":801}],"vni_ids":[],"virtual_gateway_ipv6":null,"ipv4_subnet":"8.0.1.0/24","rt_policy":{"import_RTs":null,"export_RTs":null},"label":"c-801","ipv4_enabled":true,"virtual_gateway_ipv6_enabled":false,"ipv6_enabled":false,"security_zone_id":"ccd2d9a6-1fc0-46b4-a1c4-9000faf25a59","dhcp_service":"dhcpServiceDisabled","create_policy_tagged":true}]}


def main():
    with open(r'inventory.yaml') as file:
        AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
        # print(AOS_ENV)

    bp_id = AOS_ENV["blueprints"][0]["id"]

    aos_server = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])

    # aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])


    # aos_server.context_template_add(bp_id, AOS_ENV["blueprints"][0]["policies"])

    aos_server.routing_zone_add(bp_id, AOS_ENV["blueprints"][0]["routing_zones"][0])
    aos_server.virtual_networks_add(bp_id, AOS_ENV["blueprints"][0]["routing_zones"][0]["virtual_networks"], AOS_ENV["blueprints"][0]["routing_zones"][0]["label"])


    # aos_server.context_template_delete(bp_id, "test1234")

    # aos_server.virtual_networks_delete(bp_id, "c-801")
    # aos_server.routing_zone_delete(bp_id, "crimson")

if __name__ == "__main__":
    main()







