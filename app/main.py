import os
import string
import random
from datetime import datetime
from typing import Optional, List
import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from starlette.status import HTTP_307_TEMPORARY_REDIRECT


app = FastAPI(title="URL Shortener API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
)


# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "urlshortener")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Global pool for database connections
pool = None

# Pydantic Models
class URLBase(BaseModel):
    url: HttpUrl
    
class URLCreate(URLBase):
    custom_path: Optional[str] = None
    
class URLResponse(BaseModel):
    short_url: str
    original_url: str
    created_at: datetime
    visits: int
    
    class Config:
        from_attributes = True
        
class URLStats(BaseModel):
    urls: List[URLResponse]
    total_urls: int
    total_visits: int


def generate_short_url(length: int = 6) -> str:
    """Generate a random short URL."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@app.on_event("startup")
async def startup():
    """Initialize database connection pool on startup."""
    global pool
    
    # Create connection pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        min_size=5,
        max_size=20
    )
    
    # Create tables if they don't exist
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS url_map (
            id SERIAL PRIMARY KEY,
            short_url VARCHAR(255) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            visits INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_short_url ON url_map(short_url);
        CREATE INDEX IF NOT EXISTS idx_original_url ON url_map(original_url);
        """)


@app.post("/shorten", response_model=URLResponse)
async def create_short_url(url_data: URLCreate):
    """Create a new short URL."""
    async with pool.acquire() as conn:
        # Check if custom path is provided
        if url_data.custom_path:
            short_url = url_data.custom_path
            # Check if custom path already exists
            existing_url = await conn.fetchrow(
                "SELECT * FROM url_map WHERE short_url = $1", short_url
            )
            if existing_url:
                raise HTTPException(status_code=400, detail="Custom short URL already in use")
        else:
            # Generate a unique short URL
            while True:
                short_url = generate_short_url()
                existing_url = await conn.fetchrow(
                    "SELECT * FROM url_map WHERE short_url = $1", short_url
                )
                if not existing_url:
                    break
        
        # Insert new URL mapping
        created_at = datetime.utcnow()
        db_url = await conn.fetchrow(
            """
            INSERT INTO url_map (short_url, original_url, created_at, visits, is_active) 
            VALUES ($1, $2, $3, $4, $5) 
            RETURNING id, short_url, original_url, created_at, visits
            """,
            short_url, str(url_data.url), created_at, 0, True
        )
        
        # Convert to dictionary for response
        return {
            "short_url": db_url["short_url"],
            "original_url": db_url["original_url"],
            "created_at": db_url["created_at"],
            "visits": db_url["visits"]
        }


@app.get("/{short_url}")
async def redirect_to_url(short_url: str):
    """Redirect to original URL."""
    async with pool.acquire() as conn:
        # Find the URL in database
        db_url = await conn.fetchrow(
            "SELECT * FROM url_map WHERE short_url = $1", short_url
        )
        
        if not db_url or not db_url["is_active"]:
            raise HTTPException(status_code=404, detail="URL not found")
        
        # Increment visit counter
        await conn.execute(
            "UPDATE url_map SET visits = visits + 1 WHERE short_url = $1",
            short_url
        )
        
        # Redirect to original URL
        return RedirectResponse(url=db_url["original_url"], status_code=HTTP_307_TEMPORARY_REDIRECT)


@app.get("/stats/", response_model=URLStats)
async def get_stats(
    skip: int = Query(0, ge=0), 
    limit: int = Query(10, ge=1, le=100)
):
    """Get statistics about URLs."""
    async with pool.acquire() as conn:
        # Get URLs with pagination
        urls = await conn.fetch(
            "SELECT * FROM url_map ORDER BY created_at DESC OFFSET $1 LIMIT $2",
            skip, limit
        )
        
        # Get total counts
        total_urls = await conn.fetchval("SELECT COUNT(*) FROM url_map")
        
        total_visits_result = await conn.fetchval("SELECT SUM(visits) FROM url_map")
        total_visits = total_visits_result if total_visits_result is not None else 0
        
        # Convert records to dictionaries
        url_list = [
            {
                "short_url": url["short_url"],
                "original_url": url["original_url"],
                "created_at": url["created_at"],
                "visits": url["visits"]
            } for url in urls
        ]
        
        return {
            "urls": url_list,
            "total_urls": total_urls,
            "total_visits": total_visits
        }


@app.delete("/{short_url}", response_model=URLResponse)
async def deactivate_url(short_url: str):
    """Deactivate a URL."""
    async with pool.acquire() as conn:
        # Find the URL in database
        db_url = await conn.fetchrow(
            "SELECT * FROM url_map WHERE short_url = $1", short_url
        )
        
        if not db_url:
            raise HTTPException(status_code=404, detail="URL not found")
        
        # Deactivate URL
        updated_url = await conn.fetchrow(
            "UPDATE url_map SET is_active = FALSE WHERE short_url = $1 RETURNING *",
            short_url
        )
        
        # Convert to dictionary for response
        return {
            "short_url": updated_url["short_url"],
            "original_url": updated_url["original_url"],
            "created_at": updated_url["created_at"],
            "visits": updated_url["visits"]
        }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)