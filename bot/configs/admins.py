from .env import ADMIN_IDS as _ADMIN_IDS


ADMINS = [int(i) for i in _ADMIN_IDS.split(",") if i.strip()] if _ADMIN_IDS else [1234]
