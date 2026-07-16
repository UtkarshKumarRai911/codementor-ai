"""
Django settings for CodeMentor AI project.

Multi-Agent RAG Coding Assistant with Django, LangGraph, ChromaDB, and Gemini.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production"),
)
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    # Local apps
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "codementor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "codementor.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use dj-database-url if DATABASE_URL is set
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and not DATABASE_URL.startswith("sqlite"):
    import dj_database_url

    DATABASES["default"] = dj_database_url.parse(DATABASE_URL)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/minute",
        "user": "60/minute",
    },
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", "60"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
_cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
)
CORS_ALLOW_ALL_ORIGINS = _cors_origins.strip() == "*"
CORS_ALLOWED_ORIGINS = [] if CORS_ALLOW_ALL_ORIGINS else _cors_origins.split(",")
CORS_ALLOW_CREDENTIALS = True

# ChromaDB Configuration
CHROMA_SETTINGS = {
    "PERSIST_DIRECTORY": os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "chroma_data")),
    "COLLECTION_NAME": os.getenv("CHROMA_COLLECTION_NAME", "codementor_knowledge"),
    "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
}

# Gemini API Configuration
GEMINI_CONFIG = {
    "API_KEY": os.getenv("GEMINI_API_KEY", ""),
    "MODEL": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "MAX_OUTPUT_TOKENS": 4096,
    "TEMPERATURE": 0.3,
    "TOP_P": 0.9,
}

# LangGraph Configuration
LANGGRAPH_CONFIG = {
    "MAX_ITERATIONS": int(os.getenv("LANGGRAPH_MAX_ITERATIONS", "10")),
    "RECURSION_LIMIT": int(os.getenv("LANGGRAPH_RECURSION_LIMIT", "25")),
}

# Redis (optional caching)
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "agents": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "rag": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
