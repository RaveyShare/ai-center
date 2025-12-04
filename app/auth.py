import os
import jwt
from fastapi import HTTPException, status
from typing import Optional

def verify_token(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT secret missing")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

