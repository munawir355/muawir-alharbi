# auth_utils.py
import jwt
from datetime import datetime, timedelta
import requests
from fastapi import HTTPException, status
from typing import Optional
from config import get_settings

# Initialize settings
settings = get_settings()


class AuthUtils:
    AUTH_API_URL = settings.PLYMOUTH_AUTH_URL

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT token for authenticated user"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def verify_plymouth_credentials(email: str, password: str) -> bool:
        """Verify credentials against Plymouth's authentication service"""
        try:
            # Make the request
            response = requests.post(
                f"{AuthUtils.AUTH_API_URL}",
                json={
                    "email": email,
                    "password": password
                }
            )

            # Check if response is successful and contains verification
            if response.status_code == 200:
                result = response.json()
                return result == ["Verified", "True"]

            return False

        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to authentication service"
            )


    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )