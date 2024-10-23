from datetime import datetime, UTC
from sqlalchemy.orm import mapped_column, Mapped
from flux_orm.database import Model


class UsedUrl(Model):
    __tablename__ = "used_url"
    url: Mapped[str] = mapped_column(primary_key=True)
    used_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))