from sentinelhub import SHConfig #pip install sentinelhub
import os

# sentinelhub
def sentinel_config():
    config = SHConfig()
    config.sh_client_id = os.getenv("SH_CLIENT_ID")
    config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")
    return config

#tg
def token():
    import os
    return os.getenv("BOT_TOKEN")

# github.com/xzbey | tg/xzbey