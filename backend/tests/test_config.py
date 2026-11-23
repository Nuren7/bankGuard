from app.config import Settings
from app.database import normalize_database_url


def test_cors_origins_are_split_trimmed_and_empty_values_ignored():
    settings = Settings(
        DATABASE_URL="sqlite://",
        CORS_ORIGINS=" https://frontend.example.com/ , , http://localhost:3000 ",
    )

    assert settings.cors_origins == [
        "https://frontend.example.com",
        "http://localhost:3000",
    ]


def test_postgres_url_scheme_is_normalized():
    assert (
        normalize_database_url("postgres://user:pass@db.example/app")
        == "postgresql+psycopg2://user:pass@db.example/app"
    )
    assert (
        normalize_database_url("postgresql://user:pass@db.example/app")
        == "postgresql+psycopg2://user:pass@db.example/app"
    )
    assert (
        normalize_database_url("postgresql+psycopg2://user:pass@db.example/app")
        == "postgresql+psycopg2://user:pass@db.example/app"
    )
