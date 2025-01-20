__all__ = ["load_config", "save_config", "remove_client", "add_client", "generate_wireguard_pair", "generate_wireguard_config", "get_wireguard_list"]

import settings

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import ipaddress
import random
import base64
import json

class WireguardPair:
    user: str
    private_key: str
    public_key: str
    preshared_key: str
    ip: str

    def to_dict(self):
        return {
            "private_key": self.private_key,
            "public_key": self.public_key,
            "addresses": self.addresses,
            "allowed_ips": self.allowed_ips,
            "server_dns": self.server_dns,
            "server_port": self.server_port,
            "persistent_keepalive": self.persistent_keepalive
        }
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

class ServerWGConfig:
    private_key: str
    public_key: str
    addresses: str
    allowed_ips: list[str]
    server_dns: str
    server_port: int
    persistent_keepalive: int

    


configPath = Path('data/wg.json')
server = ServerWGConfig()
clients: list[WireguardPair] = []

def load_config():
    """
    Load WireGuard configuration

    config json structure
    {
        "server": {
            "private_key": "base64",
            "public_key": "base64",
        },
        "clients": [
            {
                "user": "username",
                "private_key": "base64",
                "public_key": "base64",
                "preshared_key": "base64",
                "ip": "ip",
            },
            ...
        ]
    }
    
    """
    global configPath, server, clients

    if not configPath.exists():
        newkey = x25519.X25519PrivateKey.generate()
        data = {
            "server": {
                "private_key": base64.b64encode(newkey.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode(),
                "public_key": base64.b64encode(newkey.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode(),
            },
            "clients": []
        }
        configPath.write_text(json.dumps(data, indent=4))

    data = json.loads(configPath.read_text())
    server = ServerWGConfig()
    server.private_key = data["server"]["private_key"]
    server.public_key = data["server"]["public_key"]
    server.addresses = settings.WG_ADDRESSES
    server.allowed_ips = settings.WG_ALLOWED_IPS
    server.server_dns = settings.SERVER_DOMAIN
    server.server_port = settings.WG_SERVER_PORT
    server.persistent_keepalive = settings.WG_PERSISTENT_KEEPALIVE
    
    clients = []
    for client in data["clients"]:
        pair = WireguardPair()
        pair.user = client["user"]
        pair.private_key = client["private_key"]
        pair.public_key = client["public_key"]
        pair.preshared_key = client["preshared_key"]
        pair.ip = client["ip"]
        clients.append(pair)

def save_config():
    data = {
        "server": {
            "private_key": server.private_key,
            "public_key": server.public_key,
        },
        "clients": []
    }

    for client in clients:
        data["clients"].append(client.to_dict())

    configPath.write_text(json.dumps(data, indent=4))
    _save_wg_config()

def _save_wg_config():
    global server, clients

    wgconfPath = Path('/etc/wireguard/wg0.conf')

    data = f"""[Interface]
PrivateKey = {server.private_key}
Address = {_get_host_ip(settings.WG_ADDRESSES)}
ListenPort = {settings.WG_SERVER_PORT}
MTU = 1450
PostUp = 
PreDown = 
PostDown = 
Table = auto


"""
    for client in clients:
        data += f"""[Peer]
PublicKey = {client.public_key}
PresharedKey = {client.preshared_key}
AllowedIPs = {client.ip}/32
PersistentKeepalive = {server.persistent_keepalive}


"""
    
    wgconfPath.write_text(data)

def remove_client(user: str, ip: str) -> bool:
    global clients

    if not _is_ip_user_exists(user, ip):
        return False
    
    clients = [client for client in clients if not (client.user == user and client.ip == ip)]
    save_config()
    return True

def add_client(wgClient: WireguardPair) -> bool:
    global clients
    
    if _is_ip_exists(wgClient.ip):
        return False
    if _is_ip_user_exists(wgClient.user, wgClient.ip):
        return False
    
    clients.append(wgClient)
    save_config()
    return True


def _is_ip_user_exists(user: str, ip: str) -> bool:
    global clients
    return any(client.user == user and client.ip == ip for client in clients)

def _is_ip_exists(ip: str) -> bool:
    global clients
    return any(client.ip == ip for client in clients)

def _get_random_ip(cidr) -> str:
    while True:
        ip = str(ipaddress.IPv4Address(random.randint(int(ipaddress.IPv4Network(cidr).network_address) + 2, int(ipaddress.IPv4Network(cidr).broadcast_address) - 1)))
        if not _is_ip_exists(ip):
            return ip

def _get_host_ip(cidr) -> str:
    ipaddr = ipaddress.IPv4Network(cidr)
    return f"{ipaddr.network_address + 1}/{ipaddr.prefixlen}"

def generate_wireguard_pair(user: str, cidr: str) -> WireguardPair:
    key = x25519.X25519PrivateKey.generate()
    preshared_key = x25519.X25519PrivateKey.generate()
    return WireguardPair(
        user=user,
        private_key=base64.b64encode(key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode(),
        public_key=base64.b64encode(key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode(),
        preshared_key=base64.b64encode(preshared_key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode(),
        ip=_get_random_ip(cidr)
    )

def generate_wireguard_config(user: str, ip: str) -> str:
    global server

    if not _is_ip_user_exists(user, ip):
        return None
    
    wgClient = next(client for client in clients if client.user == user and client.ip == ip)

    return f"""[Interface]
PrivateKey = {wgClient.private_key}
Address = {wgClient.ip}/32
{f'DNS = {server.dns}' if server.dns else ''}

[Peer]
PublicKey = {server.public_key}
PresharedKey = {wgClient.preshared_key}
AllowedIPs = {server.addresses}, {" ,".join(server.allowed_ips)}
Endpoint = {server.server_dns}:{server.server_port}
PersistentKeepalive = {server.persistent_keepalive}
"""

def get_wireguard_list(user: str) -> list[dict]:
    global clients
    return [client.to_dict() for client in clients if client.user == user]
