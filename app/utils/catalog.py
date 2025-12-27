from app.core.settings import UserSettings


def get_catalogs_from_config(
    user_settings: UserSettings, cat_id: str, default_name: str, default_movie: bool, default_series: bool
):
    catalogs = []
    config = next((c for c in user_settings.catalogs if c.id == cat_id), None)
    if not config or config.enabled:
        name = config.name if config and config.name else default_name
        enabled_movie = getattr(config, "enabled_movie", default_movie) if config else default_movie
        enabled_series = getattr(config, "enabled_series", default_series) if config else default_series

        if enabled_movie:
            catalogs.append({"type": "movie", "id": cat_id, "name": name, "extra": []})
        if enabled_series:
            catalogs.append({"type": "series", "id": cat_id, "name": name, "extra": []})
    return catalogs
