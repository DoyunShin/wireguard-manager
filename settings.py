from pathlib import Path
import json

configPath = Path("data/config.json")

DEBUG = False

SERVER_DOMAIN = "vpn.example.com"
SECRET_KEY = "00000000000000000000000000000000"
LOGIN_TIME = 3600
FLOW_TIME = 300

GOOGLE_CALLBACK_URL = "/api/auth/callback"
GOOGLE_CLIENT_SECRET = {}

ALLOWED_EMAILS = []
ALLOWED_DOMAINS = []

WG_ALLOWED_IPS = []
WG_PERSISTENT_KEEPALIVE = 0
WG_SERVER_PORT = 51820
WG_ADDRESSES = "192.168.0.0/24"
WG_DNS = ""



def load_config():
    global configPath

    if not configPath.exists():
        raise FileNotFoundError("Config file not found.\n> data/config.json")

    data = json.loads(configPath.read_text())
    for key, value in data.items():
        globals()[key] = value
