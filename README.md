# Watchly
Stremio addon for movie and series recommendation

## FastAPI Stremio Catalog API

A FastAPI-based Stremio catalog addon that provides movie and series recommendations from TMDB based on your Stremio library. Uses IMDB IDs as primary identifiers and generates personalized recommendations.

## Project Structure

```
Watchly/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                 # Pydantic settings
│   ├── models.py                 # Pydantic models for Stremio
│   └── services/
│       ├── __init__.py
│       ├── tmdb_service.py       # TMDB API service
│       ├── stremio_service.py    # Stremio library service
│       └── recommendation_service.py  # Recommendation engine
├── requirements.txt
├── vercel.json                   # Vercel configuration
└── README.md
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get TMDB API Key:**
   - Sign up at [TMDB](https://www.themoviedb.org/)
   - Get your API key from [API Settings](https://www.themoviedb.org/settings/api)

3. **Get Stremio Credentials:**
   - Your Stremio username and password (used to fetch your library)

4. **Set environment variables:**
   ```bash
   export TMDB_API_KEY=your_api_key_here
   export STREMIO_USERNAME=your_stremio_username
   export STREMIO_PASSWORD=your_stremio_password
   ```
   
   Or create a `.env` file:
   ```
   TMDB_API_KEY=your_api_key_here
   STREMIO_USERNAME=your_stremio_username
   STREMIO_PASSWORD=your_stremio_password
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## Stremio Catalog API Endpoints

### Manifest
- **GET** `/manifest.json` - Stremio addon manifest

### Catalog
- **GET** `/catalog/{type}/{id}.json` - Get recommendations based on your library
  - `type`: `movie` or `series`
  - `id`: Catalog ID (`watchly-movies` or `watchly-series`)
  - Example: `GET /catalog/movie/watchly-movies.json` (Movie recommendations)
  - Example: `GET /catalog/series/watchly-series.json` (Series recommendations)
  
  **Note:** Recommendations are generated based on items in your Stremio library. The service uses your most recent library items as seeds to find similar content.

## Additional API Endpoints

### Health Check
- **GET** `/health` - Check API health status

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Vercel Deployment

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Set environment variables in Vercel:**
   ```bash
   vercel env add TMDB_API_KEY
   vercel env add STREMIO_USERNAME
   vercel env add STREMIO_PASSWORD
   ```
   Or set them in the Vercel dashboard under Project Settings > Environment Variables

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Production deployment:**
   ```bash
   vercel --prod
   ```

The `vercel.json` file is already configured to use the Python runtime and route all requests to `app/main.py`.

## Example Usage

### Stremio Catalog
```bash
# Get movie recommendations based on your library
curl http://localhost:8000/catalog/movie/watchly-movies.json

# Get series recommendations based on your library
curl http://localhost:8000/catalog/series/watchly-series.json
```

## How It Works

1. **Library Fetching**: The service fetches your Stremio library items (movies and series)
2. **Seed Selection**: Uses your most recent library items (up to 20) as seeds
3. **Recommendation Generation**: For each seed, fetches recommendations and similar content from TMDB
4. **Deduplication**: Removes items already in your library and deduplicates results
5. **Scoring**: Combines recommendations from multiple seeds with scoring
6. **IMDB ID Mapping**: All results use IMDB IDs as primary identifiers (Stremio standard)

## Features

- ✅ Pydantic Settings for environment variable management
- ✅ Stremio library integration
- ✅ Library-based recommendation engine
- ✅ IMDB IDs as primary identifiers
- ✅ Both movies and TV series support
- ✅ Automatic deduplication and filtering
- ✅ Vercel deployment ready
- ✅ Clean project structure with app folder

## Configuration

The recommendation engine can be configured via the `get_recommendations` method:
- `seed_limit`: Number of library items to use as seeds (default: 20)
- `per_seed_limit`: Recommendations per seed (default: 4)
- `max_results`: Maximum total results (default: 50)
