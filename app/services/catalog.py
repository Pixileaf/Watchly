import asyncio
from collections import Counter

from loguru import logger

from app.core.settings import UserSettings
from app.services.scoring import ScoringService
from app.services.stremio_service import StremioService
from app.services.tmdb_service import TMDBService

from .tmdb.genre import MOVIE_GENRE_TO_ID_MAP, SERIES_GENRE_TO_ID_MAP


class DynamicCatalogService:
    """
    Generates dynamic catalog rows based on user library and preferences.
    """

    def __init__(self, stremio_service: StremioService):
        self.stremio_service = stremio_service
        self.tmdb_service = TMDBService()
        self.scoring_service = ScoringService()

    @staticmethod
    def normalize_type(type_):
        return "series" if type_ == "tv" else type_

    def build_catalog_entry(self, item, label, config_id):
        item_id = item.get("_id", "")
        # Use watchly.{config_id}.{item_id} format for better organization
        if item_id.startswith("tt") and config_id in ["watchly.loved", "watchly.watched"]:
            catalog_id = f"{config_id}.{item_id}"
        else:
            catalog_id = item_id

        name = item.get("name")
        # Truncate long names for cleaner UI
        if len(name) > 25:
            name = name[:25] + "..."

        return {
            "type": self.normalize_type(item.get("type")),
            "id": catalog_id,
            "name": f"{label} {name}",
            "extra": [],
        }

    async def get_dynamic_catalogs(
        self, library_items: list[dict], user_settings: UserSettings | None = None
    ) -> list[dict]:
        """
        Generate all dynamic catalog rows:
        1. Because you watched X
        2. Because you loved X
        3. Genre rows
        """
        catalogs = []

        # 1. Interaction-based rows (Because you watched/loved)
        # We pick the TOP 2 most relevant items to show "Because you watched" rows for
        # This prevents spamming the user with 50 rows

        # Score all items to find the best "Source" items
        all_items = library_items.get("loved", []) + library_items.get("watched", [])

        # Deduplicate
        unique_items = {item["_id"]: item for item in all_items}
        processed_items = []
        for item_data in unique_items.values():
            # Use process_item to get a full ScoredItem object
            scored_item_obj = self.scoring_service.process_item(item_data)

            # We need a dict structure for the rest of the legacy code for now,
            # or we can attach the score to the dict.
            # Let's attach the score to the original dict for minimal disruption to this method's flow
            item_data["_interest_score"] = scored_item_obj.score
            processed_items.append(item_data)

        # Sort by score
        processed_items.sort(key=lambda x: x["_interest_score"], reverse=True)

        # Pick top items for "Because you..." rows
        # We only want to show maybe 1 or 2 of these specific rows per refresh to keep it fresh
        # For now, let's pick the top 1 Movie and top 1 Series
        top_movie = next((i for i in processed_items if i["type"] == "movie"), None)
        top_series = next((i for i in processed_items if i["type"] == "series"), None)

        candidates = []
        if top_movie:
            candidates.append(top_movie)
        if top_series:
            candidates.append(top_series)

        for item in candidates:
            # Decide label based on status
            is_loved = item.get("_is_loved", False)
            label = "Because you Loved" if is_loved else "Because you Watched"
            row_id = "watchly.loved" if is_loved else "watchly.watched"

            catalogs.append(self.build_catalog_entry(item, label, row_id))

        # 2. Genre-based rows
        genre_catalogs = await self.get_genre_based_catalogs(library_items, user_settings)
        catalogs += genre_catalogs

        return catalogs

    async def get_watched_loved_catalogs(self, library_items: list[dict], user_settings: UserSettings | None = None):
        """Legacy compatibility wrapper - redirects to get_dynamic_catalogs"""
        # Only called by the old update flow, we can redirect or keep minimal logic
        # For the new architecture, we want to merge this logic.
        return await self.get_dynamic_catalogs(library_items, user_settings)

    async def _get_item_genres(self, item_id: str, item_type: str) -> list[str]:
        """Fetch genres for a specific item from TMDB."""
        try:
            # Convert IMDB ID to TMDB ID
            tmdb_id = None
            media_type = "movie" if item_type == "movie" else "tv"

            if item_id.startswith("tt"):
                tmdb_id, _ = await self.tmdb_service.find_by_imdb_id(item_id)
            elif item_id.startswith("tmdb:"):
                tmdb_id = int(item_id.split(":")[1])

            if not tmdb_id:
                return []

            # Fetch details
            if media_type == "movie":
                details = await self.tmdb_service.get_movie_details(tmdb_id)
            else:
                details = await self.tmdb_service.get_tv_details(tmdb_id)

            return [g.get("name") for g in details.get("genres", [])]
        except Exception as e:
            logger.warning(f"Failed to fetch genres for {item_id}: {e}")
            return []

    async def get_genre_based_catalogs(self, library_items: list[dict], user_settings: UserSettings | None = None):
        genre_label = "You might also Like"
        genre_enabled = True

        if user_settings:
            genre_config = next((c for c in user_settings.catalogs if c.id == "watchly.genre"), None)
            if genre_config:
                genre_enabled = genre_config.enabled
                if genre_config.name:
                    genre_label = genre_config.name

        if not genre_enabled:
            return []

        # get separate movies and series lists from loved items
        loved_movies = [item for item in library_items.get("loved", []) if item.get("type") == "movie"]
        loved_series = [item for item in library_items.get("loved", []) if item.get("type") == "series"]

        # only take last 5 results from loved movies and series
        loved_movies = loved_movies[:5]
        loved_series = loved_series[:5]

        # fetch genres concurrently
        movie_tasks = [self._get_item_genres(item.get("_id").strip(), "movie") for item in loved_movies]
        series_tasks = [self._get_item_genres(item.get("_id").strip(), "series") for item in loved_series]

        movie_genres_list = await asyncio.gather(*movie_tasks)
        series_genres_list = await asyncio.gather(*series_tasks)

        # now flatten list and count the occurance of each genre for both movies and series separately
        movie_genre_counts = Counter(
            [genre for sublist in movie_genres_list for genre in sublist if genre in MOVIE_GENRE_TO_ID_MAP]
        )
        series_genre_counts = Counter(
            [genre for sublist in series_genres_list for genre in sublist if genre in SERIES_GENRE_TO_ID_MAP]
        )
        sorted_movie_genres = sorted(movie_genre_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_series_genres = sorted(series_genre_counts.items(), key=lambda x: x[1], reverse=True)

        # now get the top 2 genres for movies and series
        top_2_movie_genre_names = [genre for genre, _ in sorted_movie_genres[:2]]
        top_2_series_genre_names = [genre for genre, _ in sorted_series_genres[:2]]

        # convert id to name
        top_2_movie_genres = [str(MOVIE_GENRE_TO_ID_MAP[genre_name]) for genre_name in top_2_movie_genre_names]
        top_2_series_genres = [str(SERIES_GENRE_TO_ID_MAP[genre_name]) for genre_name in top_2_series_genre_names]
        catalogs = []

        if top_2_movie_genres:
            catalogs.append(
                {
                    "type": "movie",
                    "id": f"watchly.genre.{'_'.join(top_2_movie_genres)}",
                    "name": genre_label,
                    "extra": [],
                }
            )

        if top_2_series_genres:
            catalogs.append(
                {
                    "type": "series",
                    "id": f"watchly.genre.{'_'.join(top_2_series_genres)}",
                    "name": genre_label,
                    "extra": [],
                }
            )

        return catalogs
