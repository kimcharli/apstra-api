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
        return self.http.request('GET', path, headers=self.json_token_header)

    def http_post(self, path, data, headers=None) -> urllib3.response.HTTPResponse:
        if not headers:
            headers = self.json_token_header
        return self.http.request('POST', path, body=json.dumps(data), headers=headers)

    def http_put(self, path, data, headers=None) -> urllib3.response.HTTPResponse:
        if not headers:
            headers = self.json_token_header
        return self.http.request('PUT', path, body=json.dumps(data), headers=headers)


    def _auth(self) -> None:
        AUTH_PATH = "/api/aaa/login"
        resp = self.http_post( AUTH_PATH, {"username": self.username, "password": self.password}, headers=self.json_header)
        self.token = json.loads(resp.data)["token"]
        print(f"token = {self.token}")


    def create_IP_Pool(self, pools) -> None:
        for pool in pools:
            print( pool )
            ip_pools = {
                "subnets": [{"network": network} for network in pool["subnets"]], 
                "tags": pool["tags"],
                "display_name": pool["name"],
                "id": pool["name"],
            }
            POOL_PATH = "/api/resources/ip-pools"
            resp = self.http_post(POOL_PATH, ip_pools)
            print( f"ip-pool status should be 202: {resp.status}")
            
    def routing_zone_get(self, bp_id, rz_name) -> str:
        RZ_PATH = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http_get(RZ_PATH)
        rzs = json.loads(resp.data)["items"]
        for rz in rzs:
            if rzs[rz]["label"] == rz_name:
                return rzs[rz]["id"]

    def create_routing_zone(self, bp_id, data) -> None:
        RZ_DATA =  {
            "sz_type": "evpn",
            "label": data["label"],
            "vrf_name": f"{data['label']}-vrf",
            "vlan_id": data["vlan_id"]
            }
        RZ_PATH = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http_post(RZ_PATH, RZ_DATA)
        print(f"resp of routing-zone should be 201: {resp.status}")
        
        rz_id = self.routing_zone_get(bp_id, data["label"])
        dhcp_servers = { "items": data["dhcp_servers"] }
        DS_PATH = f"/api/blueprints/{bp_id}/security-zones/{rz_id}/dhcp-servers"
        resp = self.http_put(DS_PATH, dhcp_servers)
        print(f"resp of routing-zone/dhcp-servers should be 204: {resp.status}")

        # "Private-10_0_0_0-8"
        loop_data = {
            "pool_ids": [ prefix.replace("/", "-").replace(".", "_") for prefix in data["leaf_loopback_ips"] ]
        }
        LOOP_PATH = f"/api/blueprints/{bp_id}/resource_groups/ip/" + requests.utils.quote(f"sz:{rz_id},leaf_loopback_ips")
        print(LOOP_PATH)
        print(loop_data)
        resp = self.http_put(LOOP_PATH, loop_data)
        print(f"resp of routing-zone/leaf_loopbcka_ips got 202: {resp.status}")









def main():
    with open(r'inventory.yaml') as file:
        AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
        # print(AOS_ENV)

    aos_server = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])

    aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])

    aos_server.create_routing_zone(AOS_ENV["blueprints"][0]["id"], AOS_ENV["blueprints"][0]["routing_zones"][0])


if __name__ == "__main__":
    main()






