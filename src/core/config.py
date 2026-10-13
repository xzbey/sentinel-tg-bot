from sentinelhub import SHConfig
from os import getenv
from functools import lru_cache

@lru_cache
def sentinel_config():
    config = SHConfig()
    config.sh_client_id = getenv("SH_CLIENT_ID")
    config.sh_client_secret = getenv("SH_CLIENT_SECRET")
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    config.sh_timeout = 60
    return config

#tg
@lru_cache
def token():
    return getenv("BOT_TOKEN")
