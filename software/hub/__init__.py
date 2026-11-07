import os


def hub_url() -> str:
    return os.environ.get("HUB_URL", "ws://localhost:8765")
