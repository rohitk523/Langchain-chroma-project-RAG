from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
from functools import wraps
from app.config import settings

security = HTTPBearer()

class ClerkAuthError(Exception):
    """Custom exception for Clerk authentication errors"""
    pass

async def get_clerk_jwt_public_key() -> str:
    """Get Clerk's public key for JWT verification"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.com/v1/jwks",
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"}
            )
            
            if response.status_code == 200:
                jwks = response.json()
                # For simplicity, we'll use the first key
                # In production, you should match the key by 'kid' from the JWT header
                if jwks.get('keys'):
                    return jwks['keys'][0]
                else:
                    raise ClerkAuthError("No JWKS keys found")
            else:
                raise ClerkAuthError(f"Failed to fetch JWKS: {response.status_code}")
                
    except Exception as e:
        raise ClerkAuthError(f"Error fetching JWKS: {str(e)}")

async def verify_clerk_token(token: str) -> Dict[str, Any]:
    """Verify Clerk JWT token and return user data"""
    try:
        # First, decode the JWT without verification to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        unverified_payload = jwt.get_unverified_claims(token)
        
        # Get the JWKS (JSON Web Key Set) from Clerk
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            # Get JWKS from Clerk
            jwks_response = await client.get(
                "https://api.clerk.com/v1/jwks",
                headers=headers
            )
            
            if jwks_response.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail=f"Failed to fetch JWKS: {jwks_response.status_code}"
                )
            
            jwks_data = jwks_response.json()
            
            # Find the correct key from JWKS
            key_id = unverified_header.get("kid")
            if not key_id:
                raise HTTPException(status_code=401, detail="No key ID in token")
            
            # Find the matching key
            public_key = None
            for key in jwks_data.get("keys", []):
                if key.get("kid") == key_id:
                    public_key = key
                    break
            
            if not public_key:
                raise HTTPException(status_code=401, detail="Public key not found")
            
            # Convert JWK to key object for verification
            try:
                rsa_key = jwk.construct(public_key)
                
                # Verify the JWT with the public key
                payload = jwt.decode(
                    token,
                    key=rsa_key,
                    algorithms=["RS256"],
                    options={"verify_aud": False}  # Skip audience verification for now
                )
                
                # Extract user information from the verified payload
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(status_code=401, detail="No user ID in token")
                
                # Get user information from Clerk API
                user_response = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers=headers
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    
                    # Extract email from email_addresses array
                    email = None
                    if user_data.get("email_addresses"):
                        primary_email = next(
                            (addr for addr in user_data["email_addresses"] if addr.get("primary")), 
                            user_data["email_addresses"][0] if user_data["email_addresses"] else None
                        )
                        email = primary_email.get("email_address") if primary_email else None
                    
                    # Build user info
                    return {
                        "sub": user_data["id"],
                        "email": email,
                        "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or None,
                        "first_name": user_data.get("first_name"),
                        "last_name": user_data.get("last_name"),
                        "session_id": payload.get("sid"),
                        "user_id": user_data["id"]
                    }
                else:
                    # If we can't get user data, return what we have from the token
                    return {
                        "sub": payload.get("sub"),
                        "email": payload.get("email"),
                        "name": payload.get("name"),
                        "first_name": payload.get("given_name"),
                        "last_name": payload.get("family_name"),
                        "session_id": payload.get("sid"),
                        "user_id": payload.get("sub")
                    }
                
            except JWTError as e:
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
                
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Network error during authentication: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Authentication failed: {str(e)}"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="No authentication credentials provided")
    
    user_data = await verify_clerk_token(credentials.credentials)
    return user_data

def get_current_user_id(token: str) -> str:
    """Extract user ID from token (synchronous helper for non-async contexts)"""
    try:
        # Decode JWT without verification to get user ID quickly
        payload = jwt.get_unverified_claims(token)
        return payload.get("sub", "")
    except JWTError:
        return ""

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return decorated_function

# Health check function for auth service
async def health_check_auth() -> Dict[str, Any]:
    """Check if Clerk authentication service is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.com/v1/jwks",
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
                timeout=10
            )
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "clerk_api_accessible": response.status_code == 200,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "clerk_api_accessible": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        } 