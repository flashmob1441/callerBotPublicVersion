import os


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


BOT_TOKEN = _required("BOT_TOKEN")
API_ID = int(_required("API_ID"))
API_HASH = _required("API_HASH")
BLACKLIST = {int(i) for i in os.getenv("BLACKLIST", "").split(",") if i.strip()}
