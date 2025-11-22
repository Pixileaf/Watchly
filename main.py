import os
import uvicorn
from app.core import app, settings

if __name__ == "__main__":
    PORT = os.getenv("PORT", settings.PORT)
    reload = settings.APP_ENV == "development"
    uvicorn.run("app.core.app:app", host="0.0.0.0", port=int(PORT), reload=reload)
