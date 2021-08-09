#!python3

import yaml
import requests
import urllib3
import json

class AosServer:
    def __init__(self, host: str, port: int, username: str, password: str, session: requests.Session = None):
        self.session = session
        urllib3.disable_warnings()
        self.http = urllib3.HTTPSConnectionPool(host, port=port, cert_reqs='CERT_NONE', assert_hostname=False)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.json_header = {"Content-Type": "application/json"}
        self._auth()
        self.json_token_header = {"Content-Type": "application/json", "AuthToken": self.token}


    def _auth(self):
        AUTH_PATH = "/api/aaa/login"
        AUTH_DATA = json.dumps({"username": self.username, "password": self.password})
        AUTH_HEADERS = urllib3.response.HTTPHeaderDict(self.json_header)
        resp = self.http.request('POST', AUTH_PATH, body=AUTH_DATA, headers=AUTH_HEADERS)
        self.token = json.loads(resp.data)["token"]
        print(f"token = {self.token}")


    def create_IP_Pool(self, pools):
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
            POOL_HEADERS = urllib3.response.HTTPHeaderDict(self.json_token_header)
            resp = self.http.request('POST', POOL_PATH, body=POOL_DATA, headers=POOL_HEADERS)
            print( f"ip-pool status should be 202: {resp.status}")
            





with open(r'inventory.yaml') as file:
    AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
    # print(AOS_ENV)

AOS_SERVER = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])

AOS_SERVER.create_IP_Pool(AOS_ENV["resources"]["ip_pools"])






