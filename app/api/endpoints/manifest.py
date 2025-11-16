from fastapi.routing import APIRouter
from fastapi import Response
from app.config import settings

router = APIRouter()


@router.get("/manifest.json")
async def manifest(response: Response):
    """Stremio manifest endpoint."""
    # Cache manifest for 1 day (86400 seconds)
    # response.headers["Cache-Control"] = "public, max-age=86400"
    return {
        "id": settings.ADDON_ID,
        "version": "0.1.0",
        "name": "Watchly",
        "description": "Movie and series recommendations based on your Stremio library",
        "resources": [
            {"name": "catalog", "types": ["movie", "series"], "idPrefixes": ["tt"]},
            {"name": "stream", "types": ["movie", "series"], "idPrefixes": ["tt"]},
        ],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"],
        "catalogs": [
            {"type": "movie", "id": "watchly.rec", "name": "Recommended", "extra": []},
            {"type": "series", "id": "watchly.rec", "name": "Recommended", "extra": []},
        ],
    }
