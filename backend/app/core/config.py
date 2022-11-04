from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "hambook"
VERSION = "1.0.0"
API_PREFIX = "/api"
SRV_URI = config("SRV_URI", cast=str, default="http://dev.hambook.net")

SECRET_KEY = config("SECRET_KEY", cast=Secret)
ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    cast=int,
    default=7 * 24 * 60  # one week
)
TEMPORARY_TOKEN_EXPIRE_MINUTES = config(
    "TEMPORARY_TOKEN_EXPIRE_MINUTES",
    cast=int,
    default=1 * 60  # one hour
)

JWT_ALGORITHM = config("JWT_ALGORITHM", cast=str, default="HS256")
JWT_AUDIENCE = config("JWT_AUDIENCE", cast=str, default="hambook.net:auth")
JWT_TOKEN_PREFIX = config("JWT_TOKEN_PREFIX", cast=str, default="Bearer")

POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_PORT = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB = config("POSTGRES_DB", cast=str)

EMAIL_USER = config("EMAIL_USER", cast=str)
EMAIL_PASSWORD = config("EMAIL_PASSWORD", cast=str)
EMAIL_FROM = config("EMAIL_FROM", cast=str)
EMAIL_PORT = config("EMAIL_PORT", cast=str)
EMAIL_HOST = config("EMAIL_HOST", cast=str)



DATABASE_URL = config(
  "DATABASE_URL",
  cast=DatabaseURL,
  default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

