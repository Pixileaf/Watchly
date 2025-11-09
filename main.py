from fastapi import FastAPI, HTTPException
from loguru import logger
from app.services.tmdb_service import TMDBService
from app.services.recommendation_service import RecommendationService

# Configure loguru
import os

os.makedirs("logs", exist_ok=True)
logger.add("logs/watchly_{time}.log", rotation="10 MB", retention="7 days", level="INFO")
logger.add(lambda msg: print(msg, end=""), level="INFO", colorize=True)

app = FastAPI(
    title="Watchly", description="Stremio catalog addon for movie and series recommendations", version="1.0.0"
)

# Initialize services
tmdb_service = TMDBService()
recommendation_service = RecommendationService()


@app.get("/manifest.json")
async def manifest():
    """Stremio manifest endpoint."""
    return {
        "id": "com.watchly",
        "version": "1.0.0",
        "name": "Watchly",
        "description": "Movie and series recommendations based on your Stremio library",
        "resources": ["catalog"],
        "types": ["movie", "series"],
        "idPrefixes": ["tt"],
        "catalogs": [
            {"type": "movie", "id": "watchly.rec", "name": "Recommended", "extra": []},
            {"type": "series", "id": "watchly.rec", "name": "Recommended", "extra": []},
        ],
    }


@app.get("/catalog/{type}/{id}.json")
async def get_catalog(type: str, id: str):
    """`
    Stremio catalog endpoint for movies and series.
    Returns recommendations based on user's Stremio library.

    Args:
        content_type: 'movie' or 'series'
        id: Catalog ID (e.g., 'watchly-movies' or 'watchly-series')
    """
    logger.info(f"Fetching catalog for {type} with id {id}")

    if type not in ["movie", "series"]:
        logger.warning(f"Invalid type: {type}")
        raise HTTPException(status_code=400, detail="Invalid type. Use 'movie' or 'series'")

    if id not in ["watchly.rec"]:
        logger.warning(f"Invalid id: {id}")
        raise HTTPException(status_code=400, detail="Invalid id. Use 'watchly.rec'")

    try:
        # Get recommendations based on library
        recommendations = await recommendation_service.get_recommendations(
            content_type=type, seed_limit=2, per_seed_limit=5, max_results=50
        )
        logger.info(f"Found {len(recommendations)} recommendations for {type}")

        # Recommendations already contain full metadata in Stremio format
        # Extract meta from each recommendation
        metas = []
        for rec in recommendations:
            # rec is already the full addon meta response with 'meta' key
            if rec and rec.get("meta"):
                metas.append(rec["meta"])

        logger.info(f"Returning {len(metas)} items for {type}")
        return {"metas": metas}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching catalog for {type}/{id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
