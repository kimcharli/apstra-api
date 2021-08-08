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
        # AUTH_URL = f"https://{self.host}:{self.port}/api/aaa/login"
        AUTH_DATA = json.dumps({"username": self.username, "password": self.password})
        AUTH_HEADERS = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json"})
        resp = self.http.request('POST', '/api/aaa/login', body=AUTH_DATA, headers=AUTH_HEADERS)
        self.token = json.loads(resp.data)["token"]
        print(f"token = {self.token}")







with open(r'inventory.yaml') as file:
    AOS_ENV = yaml.load(file, Loader=yaml.FullLoader)
    # print(AOS_ENV)

AOS_SERVER = AosServer(AOS_ENV["aos_server"]["host"], AOS_ENV["aos_server"]["port"], AOS_ENV["aos_server"]["username"], AOS_ENV["aos_server"]["password"])




