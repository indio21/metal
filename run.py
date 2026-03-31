import os

from app import create_app


app = create_app(os.getenv("APP_ENV", "development"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
