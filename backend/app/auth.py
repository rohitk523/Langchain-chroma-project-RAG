from fastapi import HTTPException
import httpx
import json
from typing import Dict, Any
from app.config import settings

async def verify_clerk_token(token: str) -> Dict[str, Any]:
    """Verify Clerk JWT token and return user data"""
    try:
        # Use Clerk's API to verify the token
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.clerk_secret_key}",
                "Content-Type": "application/json"
            }
            
            # Verify the session token
            response = await client.post(
                "https://api.clerk.com/v1/sessions/verify",
                headers=headers,
                json={"token": token}
            )
            
            if response.status_code == 200:
                session_data = response.json()
                
                # Get user information
                user_response = await client.get(
                    f"https://api.clerk.com/v1/users/{session_data['user_id']}",
                    headers=headers
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    return {
                        "sub": user_data["id"],
                        "email": user_data.get("email_addresses", [{}])[0].get("email_address"),
                        "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                        "session_id": session_data["id"]
                    }
                else:
                    raise HTTPException(status_code=401, detail="Invalid user")
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
                
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_current_user_id(token: str) -> str:
    """Extract user ID from verified token (synchronous helper)"""
    # This would typically be used in sync contexts
    # For async contexts, use verify_clerk_token
    pass 