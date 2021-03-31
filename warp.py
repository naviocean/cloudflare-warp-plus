import urllib.request
import json
import datetime
import random
import string
import time
import os
import sys
import subprocess
import shutil
import gzip
import dataclasses
from pathlib import Path


@dataclasses.dataclass
class AccountData():
    id: str
    account_id: str
    license_key: str
    access_token: str
    public_key: str
    private_key: str


@dataclasses.dataclass
class ConfigurationData():
    local_address_ipv4: str
    local_address_ipv6: str
    endpoint_address_host: str
    endpoint_public_key: str
    warp_enabled: bool
    account_type: str
    warp_plus_enabled: bool


class WARP:
    __default_headers = {'Host': 'api.cloudflareclient.com',
                         'Connection': 'Keep-Alive',
                         'Accept-Encoding': 'gzip',
                         'User-Agent': 'okhttp/3.12.1'}
    __api = "https://api.cloudflareclient.com"

    def __init__(self):
        self.__data_path = Path(".")
        self.__identity_path = self.__data_path.joinpath("wgcf-identity.json")
        self.__config_path = self.__data_path.joinpath("wgcf-profile.conf")
        self.__api_version = f"v0a{self._digitString(3)}"

    def _getRegUrl(self, refresh: bool = False) -> str:
        if refresh:
            return f"{self.__api}/v0a{self._digitString(3)}/reg"
        return f"{self.__api}/{self.__api_version}/reg"

    def _getConfigUrl(self, account_id: str) -> str:
        return f"{self._getRegUrl()}/{account_id}"

    def _genString(self, stringLength: int()) -> str:
        letters = string.ascii_letters + string.digits
        return ''.join(random.choice(letters) for i in range(stringLength))

    def _digitString(self, stringLength: int) -> str:
        digit = string.digits
        return ''.join((random.choice(digit) for i in range(stringLength)))

    def _genPrivateKey(self) -> str:
        result: str = subprocess.run(
            ["wg", "genkey"], capture_output=True).stdout.decode('utf-8')
        return result.strip()

    def _genPublicKey(self, private_key: str) -> str:
        result: str = subprocess.run(["wg", "pubkey"], input=bytes(private_key, 'utf-8'),
                                     capture_output=True).stdout.decode('utf-8')
        return result.strip()

    def _printAccount(self, account: AccountData):
        print("[+] Account Info:\n")
        print(f"[-] ID (*):{account.id}\n")
        print(f"[-] Account ID:{account.account_id}\n")
        print(f"[-] License Key (*):{account.license_key}\n")
        print(f"[-] Access Token:{account.access_token}\n")
        print(f"[-] Public Key:{account.public_key}\n")
        print(f"[-] Private Key (*):{account.private_key}\n")
        print("* Must to save\n")

    def _saveIdentitiy(self, account_data: AccountData):
        with open(self.__identity_path, "w") as f:
            f.write(json.dumps(dataclasses.asdict(account_data), indent=4))

    def _loadIdentity(self) -> AccountData:
        with open(self.__identity_path, "r") as f:
            account_data = AccountData(**json.loads(f.read()))
            return account_data

    def _genKeyPair(self) -> (str, str):
        private_key = self._genPrivateKey()
        public_key = self._genPublicKey(private_key)
        return (public_key, private_key)

    def _getServerConf(self, account_data: AccountData) -> ConfigurationData:
        try:
            headers = self.__default_headers.copy()
            headers["Authorization"] = f"Bearer {account_data.access_token}"
            req = urllib.request.Request(
                self._getConfigUrl(account_data.id), None, headers)
            response = urllib.request.urlopen(req)
            status_code = response.getcode()
            assert status_code == 200, f"Request get Server config error code {status_code}"

            data = response.read()
            data = json.loads(gzip.decompress(data).decode('utf-8'))
            addresses = data["config"]["interface"]["addresses"]
            peer = data["config"]["peers"][0]
            endpoint = peer["endpoint"]
            endpoint_host = endpoint if "v4" not in endpoint else endpoint['host']
            account = data["account"] if "account" in data else ""
            account_type = account["account_type"] if account != "" else "free"
            warp_plus = account["warp_plus"] if account != "" else False

            return ConfigurationData(addresses["v4"], addresses["v6"], endpoint_host, peer["public_key"], data["warp_enabled"], account_type, warp_plus)
        except Exception as error:
            print("")
            print(error)

    def _enableWarp(self, account_data: AccountData):
        try:
            headers = self.__default_headers.copy()
            headers["Authorization"] = f"Bearer {account_data.access_token}"
            headers["Content-Type"] = "application/json; charset=UTF-8"
            body = {"warp_enabled": True}
            data = json.dumps(body).encode('utf-8')
            req = urllib.request.Request(
                self._getConfigUrl(account_data.id), data, headers, method='PATCH')
            response = urllib.request.urlopen(req)
            status_code = response.getcode()
            data = response.read()
            data = json.loads(gzip.decompress(data).decode('utf-8'))
            assert status_code == 200, f"Request enable WARP error code {status_code}"
            assert data["warp_enabled"] == True
        except Exception as error:
            print("")
            print(error)

    def _getWireguardConf(self, private_key: str, address_1: str, address_2: str, public_key: str, endpoint: str) -> str:
        return f"""
            [Interface]
            PrivateKey = {private_key}
            DNS = 1.1.1.1
            DNS = 1.0.0.1
            Address = {address_1}
            Address = {address_2}

            [Peer]
            PublicKey = {public_key}
            AllowedIPs = 0.0.0.0/0
            AllowedIPs = ::/0
            Endpoint = {endpoint}
            """[1:-1]

    def _register(self) -> AccountData:
        try:
            headers = self.__default_headers.copy()
            headers['Content-Type'] = 'application/json; charset=UTF-8'
            install_id = self._genString(22)
            public_key, private_key = self._genKeyPair()
            body = {"install_id": install_id,
                    "tos": datetime.datetime.now().isoformat()[:-3] + "+02:00",
                    "key": public_key,
                    "fcm_token": "{}:APA91b{}".format(install_id, self._genString(134)),
                    "type": "Android",
                    "locale": "en_US"}
            data = json.dumps(body).encode('utf-8')
            req = urllib.request.Request(self._getRegUrl(), data, headers)
            response = urllib.request.urlopen(req)
            status_code = response.getcode()
            assert status_code == 200, f"Request register error code {status_code}"

            data = response.read()
            data = json.loads(gzip.decompress(data).decode('utf-8'))
            account = AccountData(data["id"],
                                  data["account"]["id"],
                                  data["account"]["license"],
                                  data["token"],
                                  public_key,
                                  private_key
                                  )
            self._printAccount(account)
            self._saveIdentitiy(account)
            return account
        except Exception as error:
            print("")
            print(error)

    def createConfig(self) -> str:
        account_data: AccountData
        if not self.__identity_path.exists():
            print(f"Creating new identity...")
            account_data = self._register()
        else:
            print(f"Loading existing identity...")
            account_data = self._loadIdentity()

        print(f"Getting configuration...")
        conf_data = self._getServerConf(account_data)
        if not conf_data.warp_enabled:
            print(f"Enabling Warp...")
            self._enableWarp(account_data)
            conf_data.warp_enabled = True

        print(f"Account type: {conf_data.account_type}")
        print(f"Warp+ enabled: {conf_data.warp_plus_enabled}")

        print("Creating WireGuard configuration...")

        with open(self.__config_path, "w") as f:
            f.write(self._getWireguardConf(account_data.private_key, conf_data.local_address_ipv4,
                                           conf_data.local_address_ipv6, conf_data.endpoint_public_key,
                                           conf_data.endpoint_address_host))
        return account_data.id

    def buffData(self, account_id: str) -> int:
        try:
            install_id = self._genString(22)
            body = {"key": "{}=".format(self._genString(43)),
                    "install_id": install_id,
                    "fcm_token": "{}:APA91b{}".format(install_id, self._genString(134)),
                    "referrer": account_id,
                    "warp_enabled": False,
                    "tos": datetime.datetime.now().isoformat()[:-3] + "+02:00",
                    "type": "Android",
                    "locale": "es_ES"}
            data = json.dumps(body).encode('utf8')
            headers = {'Content-Type': 'application/json; charset=UTF-8',
                       'Host': 'api.cloudflareclient.com',
                       'Connection': 'Keep-Alive',
                       'Accept-Encoding': 'gzip',
                       'User-Agent': 'okhttp/3.12.1'
                       }
            req = urllib.request.Request(self._getRegUrl(True), data, headers)
            response = urllib.request.urlopen(req)
            status_code = response.getcode()
            return status_code
        except Exception as error:
            print("")
            print(error)
