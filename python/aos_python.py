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
        self.json_header = {"Content-Type": "application/json"}
        self._auth()
        self.json_token_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json", "AuthToken": self.token})


    def _auth(self) -> None:
        AUTH_PATH = "/api/aaa/login"
        AUTH_DATA = json.dumps({"username": self.username, "password": self.password})
        AUTH_HEADERS = urllib3.response.HTTPHeaderDict(self.json_header)
        resp = self.http.request('POST', AUTH_PATH, body=AUTH_DATA, headers=AUTH_HEADERS)
        self.token = json.loads(resp.data)["token"]
        print(f"token = {self.token}")


    def create_IP_Pool(self, pools) -> None:
        #     apstra-pool: ["4.0.0.0/24", "4.0.1.0/24"]
        for pool in pools:
            print( pool )
            ip_pools = {
                "subnets": [{"network": network} for network in pool["subnets"]], 
                "tags": pool["tags"],
                "display_name": pool["name"],
                "id": pool["name"],
            }
            POOL_PATH = "/api/resources/ip-pools"
            POOL_DATA = json.dumps(ip_pools)
            print( POOL_DATA )
            # POOL_HEADERS = urllib3.response.HTTPHeaderDict(self.json_token_header)
            resp = self.http.request('POST', POOL_PATH, body=POOL_DATA, headers=self.json_token_header)
            print( f"ip-pool status should be 202: {resp.status}")
            
    def routing_zone_get(self, bp_id, rz_name) -> str:
        RZ_PATH = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http.request('GET', RZ_PATH, headers=self.json_token_header)
        rzs = json.loads(resp.data)["items"]
        for rz in rzs:
            if rzs[rz].label == rz_name:
                return rz.id

    def create_routing_zone(self, bp_id, data) -> None:
        RZ_DATA =  {
            "sz_type": "evpn",
            "label": data["label"],
            "vrf_name": f"{data['label']}-vrf",
            "vlan_id": data["vlan_id"]
            }
        RZ_PATH = f"/api/blueprints/{bp_id}/security-zones"
        resp = self.http.request('POST', RZ_PATH, body=json.dumps(RZ_DATA), headers=self.json_token_header)
        print(f"resp of routing-zone: {resp.status}")
        
        rz_id = self.routing_zone_get(bp_id, data["label"])
        dhcp_servers = { "items": data["dhcp_servers"] }
        DS_PATH = f"/api/blueprints/{bp_id}/security-zones/{rz_id}/dhcp_servers"

        resp = self.http.request('PUT', DS_PATH, body=json.dumps(dhcp_servers), headers=self.json_token_header)
        print(f"resp of routing-zone/dhcp-servers: {resp.status}")







def main():
    with open(r'inventory.yaml') as file:
        AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
        # print(AOS_ENV)

    aos_server = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])

    aos_server.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])

    aos_server.create_routing_zone(AOS_ENV["blueprints"][0]["id"], AOS_ENV["blueprints"][0]["routing_zones"][0])


if __name__ == "__main__":
    main()






