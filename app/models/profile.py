from pydantic import BaseModel, Field


class SparseVector(BaseModel):
    """
    Represents a sparse vector where keys are feature IDs and values are weights.
    Example: {28: 0.8, 12: 0.5} for Action and Adventure genres.
    """

    values: dict[int, float] = Field(default_factory=dict)

    def normalize(self):
        """Normalize values to 0-1 range based on the maximum value."""
        if not self.values:
            return

        max_val = max(self.values.values())
        if max_val > 0:
            for k in self.values:
                self.values[k] = round(self.values[k] / max_val, 4)

    def get_top_features(self, limit: int = 5) -> list[tuple[int, float]]:
        """Return top N features by weight."""
        sorted_items = sorted(self.values.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:limit]


class UserTasteProfile(BaseModel):
    """
    The complete user taste profile consisting of multiple sparse vectors.
    """

    genres: SparseVector = Field(default_factory=SparseVector)
    keywords: SparseVector = Field(default_factory=SparseVector)
    cast: SparseVector = Field(default_factory=SparseVector)
    crew: SparseVector = Field(default_factory=SparseVector)
    years: SparseVector = Field(default_factory=SparseVector)

    def normalize_all(self):
        """Normalize all component vectors."""
        self.genres.normalize()
        self.keywords.normalize()
        self.cast.normalize()
        self.crew.normalize()
        self.years.normalize()

    def get_top_genres(self, limit: int = 3) -> list[tuple[int, float]]:
        return self.genres.get_top_features(limit)

    def get_top_keywords(self, limit: int = 5) -> list[tuple[int, float]]:
        return self.keywords.get_top_features(limit)

    def get_top_crew(self, limit: int = 2) -> list[tuple[int, float]]:
        return self.crew.get_top_features(limit)
