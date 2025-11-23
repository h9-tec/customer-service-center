import os
from typing import Optional

from rest_framework.permissions import BasePermission


def _get_api_key_from_request(request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("api-key "):
        return auth_header.split(" ", 1)[1]
    return request.headers.get("X-API-Key") or request.query_params.get("api_key")


class APIKeyPermission(BasePermission):
    """Simple API key permission for server-to-server endpoints."""

    def has_permission(self, request, view) -> bool:
        required_key = os.environ.get("API_KEY")
        if not required_key:
            return False
        provided = _get_api_key_from_request(request)
        return provided == required_key
