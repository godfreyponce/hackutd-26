import socket

import pytest


@pytest.fixture
def unused_url():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    return f"ws://127.0.0.1:{port}"
