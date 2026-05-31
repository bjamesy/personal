from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    environment: str = "development"
    scrape_interval_hours: int = 6  # run 4× per day by default
    google_places_api_key: str = ""
    public_base_url: str = ""


    model_config = {"env_file": ".env"}


settings = Settings()
