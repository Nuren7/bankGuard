from pytdantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  DATABASE_URL: str
  GROQ_API_KEY: str
  HMAC_SECRET: str
  
  model_config = SettingsConfigDict(
    env_file=".env"
    env_file_encoder="utf-8"
    extra="ignore"
  )
  settings = Settings()