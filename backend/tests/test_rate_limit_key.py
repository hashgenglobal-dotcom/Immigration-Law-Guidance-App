from unittest.mock import MagicMock

from app.services.rate_limit_service import _client_key


def test_client_key_uses_header() -> None:
    request = MagicMock()
    request.headers = {"X-Client-Id": "device-abc"}
    request.client = MagicMock(host="127.0.0.1")
    key = _client_key(request, None)
    assert len(key) == 32
