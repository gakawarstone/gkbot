import os

# Set dummy environment variables for tests if they are not set or are empty
# but ONLY if INTEGRATION_TEST is not enabled.
if os.environ.get("INTEGRATION_TEST") != "1":
    def set_env_default(key, value):
        if not os.environ.get(key):
            os.environ[key] = value

    set_env_default("BOT_TOKEN", "12345678:ABCDEF-GHIJKLMNOPQRSTUV")
    set_env_default("ADMIN_IDS", "1234")
    set_env_default("SQLDIALECT", "sqlite")
    set_env_default("DB_USER", "dummy")
    set_env_default("DB_PASSWORD", "dummy")
    set_env_default("DB_HOST", "dummy")
    set_env_default("DB_PORT", "dummy")
    set_env_default("DB_NAME", ":memory:")
