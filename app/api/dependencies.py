from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[str] = Depends(security)
):
    from app.config import settings
    
    if settings.debug:
        return {"user_id": "debug_user"}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": "authenticated_user"}
