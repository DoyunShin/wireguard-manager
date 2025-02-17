import settings

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import ipaddress
import random
import base64
import json
import os

class WireguardPair:
    id: int
    name: str
    user: str
    private_key: str
    public_key: str
    preshared_key: str

    def __init__(self, id: int, name: str, user: str, private_key: str, public_key: str, preshared_key: str):
        self.id = id
        self.name = name
        self.user = user
        self.private_key = private_key
        self.public_key = public_key
        self.preshared_key = preshared_key

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user": self.user,
            "private_key": self.private_key,
            "public_key": self.public_key,
            "preshared_key": self.preshared_key,
            "ip": convert_id_to_ip(self.id)
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

rootDataPath = Path('/app/data')
configPath = rootDataPath / 'wg.json'
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
                "id": 0000, (int of ip address)
                "user": "username(email)",
                "name": "client name",
                "private_key": "base64",
                "public_key": "base64",
                "preshared_key": "base64",
                "ip": "ip address"
            },
            ...
        ]
    }
    
    """
    global rootPath, configPath, server, clients

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
        # pair = WireguardPair()
        # pair.user = client["user"]
        # pair.private_key = client["private_key"]
        # pair.public_key = client["public_key"]
        # pair.preshared_key = client["preshared_key"]
        clients.append(WireguardPair(
            id=client["id"],
            name=client["name"],
            user=client["user"],
            private_key=client["private_key"],
            public_key=client["public_key"],
            preshared_key=client["preshared_key"]
        ))

    if not Path(f'{rootDataPath}/postup.sh').exists():
        Path(f'{rootDataPath}/postup.sh').touch()
        Path(f'{rootDataPath}/postup.sh').chmod(0o755)
    if not Path(f'{rootDataPath}/predown.sh').exists():
        Path(f'{rootDataPath}/predown.sh').touch()
        Path(f'{rootDataPath}/predown.sh').chmod(0o755)
    if not Path(f'{rootDataPath}/postdown.sh').exists():
        Path(f'{rootDataPath}/postdown.sh').touch()
        Path(f'{rootDataPath}/postdown.sh').chmod(0o755)

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

def _save_wg_config():
    global server, clients

    wgconfPath = Path('/etc/wireguard/wg0.conf')
    
    data = f"""[Interface]
PrivateKey = {server.private_key}
Address = {_get_host_ip(settings.WG_ADDRESSES)}
ListenPort = 51820
MTU = 1450
PostUp = /app/data/postup.sh
PreDown = /app/data/predown.sh
PostDown = /app/data/postdown.sh
Table = auto


"""
    for client in clients:
        data += f"""[Peer]
PublicKey = {client.public_key}
PresharedKey = {client.preshared_key}
AllowedIPs = {convert_id_to_ip(client.id)}/32
PersistentKeepalive = {server.persistent_keepalive}


"""
    
    wgconfPath.write_text(data)

def remove_client(user: str, ipid: str) -> bool:
    global clients

    if not _is_id_user_exists(user, ipid):
        return False
    
    clients = [client for client in clients if not (client.user == user and client.id == ipid)]
    save_config()
    reload()
    return True

def add_client(wgClient: WireguardPair) -> bool:
    global clients
    
    if _is_id_exists(wgClient.id):
        return False
    if _is_id_user_exists(wgClient.user, wgClient.id):
        return False
    
    clients.append(wgClient)
    save_config()
    reload()
    return True

def user_config_count(user: str) -> int:
    global clients
    return len([client for client in clients if client.user == user])

def convert_id_to_ip(id: int) -> str:
    return str(ipaddress.IPv4Address(id))

def convert_ip_to_id(ip: str) -> int:
    return int(ipaddress.IPv4Address(ip))

# def _is_ip_user_exists(user: str, ip: str) -> bool:
#     global clients
#     return any(client.user == user and client.ip == ip for client in clients)

# def _is_ip_exists(ip: str) -> bool:
#     global clients
#     return any(client.ip == ip for client in clients)

def _is_id_user_exists(user: str, id: int) -> bool:
    global clients
    return any(client.user == user and client.id == id for client in clients)

def _is_id_exists(id: int) -> bool:
    global clients
    return any(client.id == id for client in clients)

def _get_random_id(cidr: str) -> int:
    while True:
        ipid = random.randint(int(ipaddress.IPv4Network(cidr).network_address) + 2, int(ipaddress.IPv4Network(cidr).broadcast_address) - 1)
        if not _is_id_exists(ipid):
            return ipid

def _get_host_ip(cidr) -> str:
    """
    Get wireguard server ip address
    """
    ipaddr = ipaddress.IPv4Network(cidr)
    return f"{ipaddr.network_address + 1}/{ipaddr.prefixlen}"

def generate_wireguard_pair(user: str, wgname: str = None) -> WireguardPair:
    key = x25519.X25519PrivateKey.generate()
    preshared_key = x25519.X25519PrivateKey.generate()
    ipid = _get_random_id(settings.WG_ADDRESSES)
    return WireguardPair(
        id=ipid,
        name=wgname,
        user=user,
        private_key=base64.b64encode(key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode(),
        public_key=base64.b64encode(key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode(),
        preshared_key=base64.b64encode(preshared_key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())).decode()
    )

def fix_wireguard_pair(user: str, ipid: str, wgname: str = None) -> bool:
    global clients

    if not _is_id_user_exists(user, ipid):
        return False
    
    wgClient = next(client for client in clients if client.user == user and client.id == ipid)
    wgClient.name = wgname
    
    save_config()
    reload()
    return True

def generate_wireguard_config(user: str, ipid: int) -> str:
    global server

    if not _is_id_user_exists(user, ipid):
        return None
    
    wgClient = next(client for client in clients if client.user == user and client.id == ipid)

    return f"""[Interface]
PrivateKey = {wgClient.private_key}
Address = {convert_id_to_ip(wgClient.id)}/32
{f'DNS = {settings.WG_DNS}\n' if settings.WG_DNS else ''}
[Peer]
PublicKey = {server.public_key}
PresharedKey = {wgClient.preshared_key}
AllowedIPs = {server.addresses}, {", ".join(server.allowed_ips)}
Endpoint = {server.server_dns}:{server.server_port}
PersistentKeepalive = {server.persistent_keepalive}
"""

def get_wireguard_name(user: str, ipid: int) -> str:
    global clients

    if not _is_id_user_exists(user, ipid):
        return None
    
    return next(client.name for client in clients if client.user == user and client.id == ipid)

def get_wireguard_list(user: str) -> list[dict]:
    """
    Get WireGuard list

    Returns:
        list[dict]: List of WireGuard clients
    """
    global clients
    return [client.to_dict() for client in clients if client.user == user]


def start():
    _save_wg_config()
    print("Starting WireGuard")
    os.system("sudo bash -c 'wg-quick up wg0'")

def stop():
    os.system("sudo bash -c 'wg-quick down wg0'")

def reload():
    _save_wg_config()
    # os.system("wg syncconf wg0 <(wg-quick strip wg0)")
    print("Reloading WireGuard configuration")
    os.system("sudo bash -c 'wg syncconf wg0 <(wg-quick strip wg0)'")

def list_users():
    global clients
    return list(set(client.user for client in clients))
