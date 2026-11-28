"""Two scoped bearer credentials for the single-device installation"""
import secrets
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import Settings


bearer = HTTPBearer(auto_error=False)


def make_auth(settings: Settings):
    def role(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is not None:
            value = credentials.credentials.encode("utf-8")
            if secrets.compare_digest(value, settings.admin_token.encode("ascii")):
                return "admin"
            if secrets.compare_digest(value, settings.device_token.encode("ascii")):
                return "device"
        raise HTTPException(401, "Invalid or missing bearer credential",
                            headers={"WWW-Authenticate": "Bearer"})

    def admin(current_role: str = Depends(role)):
        if current_role != "admin":
            raise HTTPException(403, "Administrative credential required")

    def reader(current_role: str = Depends(role)):
        return current_role

    return admin, reader
