from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident
from app.models.notification import Notification