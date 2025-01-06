# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import pyodbc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

from auth_service import AuthUtils
from user_service import UserService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app_ = FastAPI(
        title="Trail Service API",
        description="API for managing hiking trails and user associations",
        version="1.0.0"
    )

    # Configure CORS
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app_


# Create the application instance
app = create_app()


# Models
class TrailBase(BaseModel):
    TrailName: str
    Description: Optional[str] = None


class TrailCreate(TrailBase):
    pass


class Trail(TrailBase):
    TrailID: int
    DateCreated: datetime
    CreatedBy: int

    class Config:
        orm_mode = True


# Database connection
def get_db():
    conn = None
    try:
        conn = pyodbc.connect(settings.DATABASE_URL)
        yield conn
    finally:
        if conn:
            conn.close()


# Auth middleware
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Authentication endpoints
@app.post("/token")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: pyodbc.Connection = Depends(get_db)
):
    """
    Login endpoint that:
    1. Verifies credentials with Plymouth service
    2. Gets or creates user in local database
    3. Returns JWT token with user information
    """
    # Verify credentials with Plymouth service
    is_verified = await AuthUtils.verify_plymouth_credentials(
        email=form_data.username,
        password=form_data.password
    )

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get or create user in local database
    try:
        user = await UserService.get_or_create_user(db, form_data.username)

        # Create access token with user information
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthUtils.create_access_token(
            data={
                "sub": form_data.username,
                "user_id": user["user_id"],
                "name": user["name"]
            },
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["user_id"],
                "name": user["name"],
                "email": user["email"]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during user management: {str(e)}"
        )


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: pyodbc.Connection = Depends(get_db)
):
    """Get current user from token and ensure they exist in database"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = AuthUtils.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

        user = await UserService.get_user_by_email(db, email)
        if user is None:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception


# Example protected route using the enhanced user information
@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# Protected route example
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """Example of a protected route"""
    return {
        "message": "You are authenticated",
        "user_email": current_user["email"]
    }


# API Routes
@app.get("/api/trails", response_model=List[Trail])
async def get_trails(db: pyodbc.Connection = Depends(get_db)):
    """Get all trails (public view)"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM CW1.Trail")
    trails = cursor.fetchall()
    return [dict(zip([column[0] for column in cursor.description], trail)) for trail in trails]


@app.get("/api/trails/{trail_id}", response_model=Trail)
async def get_trail(trail_id: int, db: pyodbc.Connection = Depends(get_db)):
    """Get a specific trail by ID"""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM CW1.Trail WHERE TrailID = ?", trail_id)
    trail = cursor.fetchone()

    if trail is None:
        raise HTTPException(status_code=404, detail="Trail not found")

    return dict(zip([column[0] for column in cursor.description], trail))


@app.post("/api/trails", response_model=Trail)
async def create_trail(
        trail: TrailCreate,
        current_user=Depends(get_current_user),
        db: pyodbc.Connection = Depends(get_db)
):
    """Create a new trail (authenticated)"""
    cursor = db.cursor()

    # Execute the stored procedure
    cursor.execute("""
        EXEC CW1.AddNewTrail 
        @TrailName = ?, 
        @Description = ?, 
        @DateCreated = ?, 
        @CreatedBy = ?
    """, trail.TrailName, trail.Description, datetime.now(), current_user["user_id"])

    db.commit()

    # Get the newly created trail
    cursor.execute("SELECT TOP 1 * FROM CW1.Trail ORDER BY TrailID DESC")
    new_trail = cursor.fetchone()
    return dict(zip([column[0] for column in cursor.description], new_trail))


@app.put("/api/trails/{trail_id}", response_model=Trail)
async def update_trail(
        trail_id: int,
        trail: TrailCreate,
        current_user=Depends(get_current_user),
        db: pyodbc.Connection = Depends(get_db)
):
    """Update a trail (authenticated)"""
    cursor = db.cursor()

    # Check if trail exists and user has permission
    cursor.execute("SELECT CreatedBy FROM CW1.Trail WHERE TrailID = ?", trail_id)
    existing_trail = cursor.fetchone()

    if not existing_trail:
        raise HTTPException(status_code=404, detail="Trail not found")
    if existing_trail.CreatedBy != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this trail")

    # Execute the stored procedure
    cursor.execute("""
        EXEC CW1.UpdateTrail 
        @TrailID = ?, 
        @TrailName = ?, 
        @Description = ?
    """, trail_id, trail.TrailName, trail.Description)

    db.commit()

    # Get the updated trail
    cursor.execute("SELECT * FROM CW1.Trail WHERE TrailID = ?", trail_id)
    updated_trail = cursor.fetchone()
    return dict(zip([column[0] for column in cursor.description], updated_trail))


@app.delete("/api/trails/{trail_id}")
async def delete_trail(
        trail_id: int,
        current_user=Depends(get_current_user),
        db: pyodbc.Connection = Depends(get_db)
):
    """Delete a trail (authenticated)"""
    cursor = db.cursor()

    # Check if trail exists and user has permission
    cursor.execute("SELECT CreatedBy FROM CW1.Trail WHERE TrailID = ?", trail_id)
    existing_trail = cursor.fetchone()

    if not existing_trail:
        raise HTTPException(status_code=404, detail="Trail not found")
    if existing_trail.CreatedBy != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this trail")

    # Execute the stored procedure
    cursor.execute("EXEC CW1.DeleteTrail @TrailID = ?", trail_id)
    db.commit()

    return {"message": "Trail deleted successfully"}


# Additional routes for user-trail associations
@app.get("/api/users/{user_id}/trails", response_model=List[Trail])
async def get_user_trails(
        user_id: int,
        current_user=Depends(get_current_user),
        db: pyodbc.Connection = Depends(get_db)
):
    """Get all trails for a specific user"""
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these trails")

    cursor = db.cursor()
    cursor.execute("""
        SELECT t.* 
        FROM CW1.Trail t
        JOIN CW1.UserTrail ut ON t.TrailID = ut.TrailID
        WHERE ut.UserID = ?
    """, user_id)

    trails = cursor.fetchall()
    return [dict(zip([column[0] for column in cursor.description], trail)) for trail in trails]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=3000)
