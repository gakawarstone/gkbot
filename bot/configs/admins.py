from .env import ADMIN_IDS


ADMINS = [int(i) for i in ADMIN_IDS.split(",") if i.strip()]
