import os

from app import create_app
from app.services.database import initialize_database


app = create_app(os.getenv("APP_ENV", "development"))


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
        print("Base de datos inicializada.")
