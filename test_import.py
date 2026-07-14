# Créer un fichier test_import.py à la racine
from app.routes import weather as weather_routes
print("✅ Routes importées:", weather_routes.router.routes)