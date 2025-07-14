from .env import _ADMIN_IDS


ADMINS = [int(i) for i in _ADMIN_IDS.split(",") if i.strip()]
