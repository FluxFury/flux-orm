from sqlalchemy.dialects.postgresql import JSONB

from models.database import Model
from datetime import datetime
from models import mapped_column, ForeignKey, UUID, Mapped

''' Ориентировочная последовательность взаимодействия с таблицами - снизу вверх'''


class Sport(Model):
    __tablename__ = "sport"
    sport_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]


class Competition(Model):
    __tablename__ = "competition"
    competition_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    sport_id: Mapped[UUID] = mapped_column(ForeignKey('sport.sport_id'))
    description: Mapped[str | None]
    image_url: Mapped[str | None]


class CompetitionCategory(Model):
    __tablename__ = "competition_category"
    category_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]


class CompetitionInCategory(Model):
    __tablename__ = "competition_in_category"
    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'), primary_key=True)
    category_id: Mapped[UUID] = mapped_column(ForeignKey('competition_category.category_id'), primary_key=True)


class TeamInCompetition(Model):
    __tablename__ = "team_in_competition"
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)
    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'), primary_key=True)
    place: Mapped[int]
    stats = mapped_column(JSONB)


class Match(Model):
    __tablename__ = "match"
    match_id: Mapped[UUID] = mapped_column(primary_key=True)
    match_name: Mapped[str]
    planned_start_datetime: Mapped[datetime]
    end_datetime: Mapped[datetime | None]
    is_online: Mapped[bool]

    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'))
    status_id: Mapped[UUID] = mapped_column(ForeignKey('match_status.status_id'))


class MatchStatus(Model):
    __tablename__ = "match_status"
    status_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
