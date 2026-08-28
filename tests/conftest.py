import os


os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["DEBUG"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = ""

os.environ.setdefault("SMTP_HOST", "")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "")
os.environ.setdefault("SMTP_PASSWORD", "")
os.environ.setdefault("SMTP_FROM_EMAIL", "")
os.environ.setdefault("SMTP_FROM_NAME", "ByteBeacon")
os.environ.setdefault("SMTP_USE_TLS", "true")
os.environ.setdefault("SMTP_USE_SSL", "false")
