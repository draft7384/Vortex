"""
Entry point: arranca uvicorn.
Uso:  python main.py
o:    uvicorn main:app --reload
"""
import uvicorn

# Importa la instancia `app` desde app.py para que uvicorn la encuentre
from app import app  # noqa: F401


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
