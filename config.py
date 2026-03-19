from sentinelhub import SHConfig #pip install sentinelhub
import os

# sentinelhub
config = SHConfig()
config.sh_client_id = os.getenv("SH_CLIENT_ID")
config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")

#tg
token = os.getenv("BOT_TOKEN")