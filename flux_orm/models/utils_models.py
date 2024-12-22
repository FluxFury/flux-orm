from datetime import datetime
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped
from flux_orm.database import Model
from flux_orm.models.utils import utcnow_naive


class UsedUrl(Model):
    __tablename__ = "used_url"
    url: Mapped[str] = mapped_column(primary_key=True)
    used_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), default=utcnow_naive())