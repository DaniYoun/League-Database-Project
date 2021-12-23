from . import db
from sqlalchemy.sql import func

class Champions:
    championName = db.Column(db.String(10000), primary_key=True)
    releaseDate = db.Column(db.DateTime(timezone=True), default=func.now())