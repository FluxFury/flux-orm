from sqlalchemy import UniqueConstraint, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from datetime import datetime

from uuid6 import uuid6


from flux_orm.database import Model
from flux_orm.models import mapped_column, ForeignKey, UUID, Mapped
from flux_orm.models.utils import utcnow_naive
from flux_orm.models.enums import PipelineStatus
""" Ориентировочная последовательность взаимодействия с таблицами - сверху вниз"""
"""THESE TABLES WERE CREATED ACCORDING TO SOLID+ PRINCIPLES"""


class Sport(Model):
    __tablename__ = "sport"
    sport_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    competitions: Mapped[list["Competition"]] = relationship(
        back_populates="sport",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
    )
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="sport",
        uselist=True,
        cascade="save-update, expunge, merge",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class Competition(Model):
    __tablename__ = "competition"
    competition_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    sport_id: Mapped[UUID] = mapped_column(ForeignKey("sport.sport_id"))
    name: Mapped[str] = mapped_column(unique=True)
    prize_pool: Mapped[str | None]
    location: Mapped[str | None]
    start_date: Mapped[datetime | None]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    sport: Mapped["Sport"] = relationship(
        back_populates="competitions",
        cascade="save-update, expunge, merge",
    )
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="competition",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
    )
    categories: Mapped[list["CompetitionCategory"] | None] = relationship(
        back_populates="competitions",
        uselist=True,
        secondary="competition_in_category",
        cascade="save-update, expunge, merge, delete",
    )
    teams: Mapped[list["Team"] | None] = relationship(
        back_populates="competitions",
        uselist=True,
        secondary="team_in_competition",
        cascade="save-update, expunge, merge",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class CompetitionInCategory(Model):
    __tablename__ = "competition_in_category"
    competition_id: Mapped[UUID] = mapped_column(
        ForeignKey("competition.competition_id"), primary_key=True
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("competition_category.category_id", ondelete="CASCADE"),
        primary_key=True,
    )


class CompetitionCategory(Model):
    __tablename__ = "competition_category"
    category_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    competitions: Mapped[list["Competition"] | None] = relationship(
        back_populates="categories",
        uselist=True,
        secondary="competition_in_category",
        cascade="save-update, expunge, merge",
        passive_deletes=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class TeamInCompetition(Model):
    __tablename__ = "team_in_competition"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.team_id"), primary_key=True)
    competition_id: Mapped[UUID] = mapped_column(
        ForeignKey("competition.competition_id"),
        primary_key=True,
    )

    place: Mapped[int | None]
    stats = mapped_column(JSONB)


class Team(Model):
    __tablename__ = "team"
    team_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str] = mapped_column(unique=True)
    pretty_name: Mapped[str | None]
    team_url: Mapped[str | None]
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="match_teams",
        uselist=True,
        secondary="team_in_match",
        cascade="save-update, expunge, merge",
    )
    competitions: Mapped[list["Competition"] | None] = relationship(
        back_populates="teams",
        uselist=True,
        secondary="team_in_competition",
        cascade="save-update, expunge, merge",
    )
    members: Mapped[list["TeamMember"] | None] = relationship(
        back_populates="teams",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        secondary="player_in_team",
    )
    coaches: Mapped[list["Coach"] | None] = relationship(
        back_populates="teams",
        uselist=True,
        secondary="coach_in_team",
        cascade="save-update, expunge, merge",
    )
    substitutions: Mapped[list["Substitution"] | None] = relationship(
        back_populates="team",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
    )
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    stats: Mapped[dict | None] = mapped_column(MutableDict.as_mutable(JSONB()))
    regalia: Mapped[dict | None] = mapped_column(MutableDict.as_mutable(JSONB()))

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class PlayerInTeam(Model):
    __tablename__ = "player_in_team"
    player_id: Mapped[UUID] = mapped_column(
        ForeignKey("team_member.player_id"), primary_key=True
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.team_id"), primary_key=True)


# class PlayerInMatchStats(Model):
#     __tablename__ = "player_in_match_stats"
#     player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
#     match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
#     stats = mapped_column(JSONB)


class TeamMember(Model):
    __tablename__ = "team_member"
    __table_args__ = (
        UniqueConstraint(
            "nickname",
            "name",
            "image_url",
            name="team_member_nickname_name_image_unique",
        ),
    )
    player_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    team_member_url: Mapped[str | None]
    teams: Mapped[list["Team"]] = relationship(
        back_populates="members",
        uselist=True,
        secondary="player_in_team",
        cascade="save-update, expunge, merge",
    )
    nickname: Mapped[str | None]
    name: Mapped[str | None]
    age: Mapped[int | None]
    country: Mapped[str | None]
    stats = mapped_column(JSONB)
    description: Mapped[str | None]
    image_url: Mapped[str | None]

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class TeamInMatch(Model):
    __tablename__ = "team_in_match"
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.team_id"), primary_key=True)
    match_id: Mapped[UUID] = mapped_column(
        ForeignKey("match.match_id"), primary_key=True
    )
    place: Mapped[int | None]
    stats = mapped_column(JSONB, nullable=True)


class MatchStatus(Model):
    __tablename__ = "match_status"
    status_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    match: Mapped["Match"] = relationship(
        back_populates="match_status",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    name: Mapped[str]
    status: Mapped[dict[str, str] | None] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    image_url: Mapped[str | None]

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class Match(Model):
    __tablename__ = "match"
    __table_args__ = (
        UniqueConstraint(
            "match_name",
            "planned_start_datetime",
            name="match_name_planned_start_datetime_unique",
        ),
    )
    match_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    sport_id: Mapped[UUID] = mapped_column(ForeignKey("sport.sport_id"))
    match_name: Mapped[str]
    pretty_match_name: Mapped[str | None]
    match_streams: Mapped[dict[str, tuple[str, str, str, str]] | None] = mapped_column(
        MutableDict.as_mutable(JSONB())
    )
    match_url: Mapped[str | None]
    tournament_url: Mapped[str | None]
    pipeline_status: Mapped[PipelineStatus | None]
    pipeline_update_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=False)
    )
    external_id: Mapped[str] = mapped_column(unique=True)
    sport: Mapped["Sport"] = relationship(
        back_populates="matches",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    match_status: Mapped["MatchStatus"] = relationship(
        back_populates="match",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    match_teams: Mapped[list["Team"] | None] = relationship(
        back_populates="matches",
        uselist=True,
        secondary="team_in_match",
        cascade="save-update, expunge, merge",
    )
    ai_statements: Mapped[list["MatchAIStatement"] | None] = relationship(
        back_populates="matches",
        uselist=True,
        secondary="ai_statement_in_match",
        cascade="save-update, expunge, merge",
    )
    substitutions: Mapped[list["Substitution"] | None] = relationship(
        back_populates="match",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
    )
    competition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("competition.competition_id")
    )
    competition: Mapped["Competition"] = relationship(
        back_populates="matches",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    formatted_news: Mapped[list["FormattedNews"] | None] = relationship(
        back_populates="relevant_matches",
        uselist=True,
        secondary="filtered_match_in_news",
        cascade="save-update, expunge, merge",
    )
    status_id: Mapped[UUID | None] = mapped_column(ForeignKey("match_status.status_id"))
    planned_start_datetime: Mapped[datetime | None]
    end_datetime: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class AIStatementInMatch(Model):
    __tablename__ = "ai_statement_in_match"
    statement_id: Mapped[UUID] = mapped_column(
        ForeignKey("match_ai_statement.statement_id"),
        primary_key=True,
    )
    match_id: Mapped[UUID] = mapped_column(
        ForeignKey("match.match_id"), primary_key=True
    )


class MatchAIStatement(Model):
    __tablename__ = "match_ai_statement"
    statement_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="ai_statements",
        uselist=True,
        secondary="ai_statement_in_match",
        cascade="save-update, expunge, merge",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class Coach(Model):
    __tablename__ = "coach"
    coach_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    teams: Mapped[list["Team"] | None] = relationship(
        back_populates="coaches",
        uselist=True,
        secondary="coach_in_team",
        cascade="save-update, expunge, merge",
    )
    stats = mapped_column(JSONB)
    regalia = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class CoachInTeam(Model):
    __tablename__ = "coach_in_team"
    coach_id: Mapped[UUID] = mapped_column(
        ForeignKey("coach.coach_id"), primary_key=True
    )
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.team_id"), primary_key=True)


class Substitution(Model):
    __tablename__ = "substitution"
    match_id: Mapped[UUID] = mapped_column(
        ForeignKey("match.match_id"), primary_key=True
    )
    match: Mapped["Match"] = relationship(
        back_populates="substitutions",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    team: Mapped["Team"] = relationship(
        back_populates="substitutions",
        uselist=False,
        cascade="save-update, expunge, merge",
    )
    prev_player_id: Mapped[UUID] = mapped_column(
        ForeignKey("team_member.player_id"), primary_key=True
    )
    new_player_id: Mapped[UUID] = mapped_column(
        ForeignKey("team_member.player_id"), primary_key=True
    )
    time: Mapped[int | None]
    team_id: Mapped[UUID] = mapped_column(ForeignKey("team.team_id"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class RawNews(Model):
    __tablename__ = "raw_news"
    raw_news_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    sport_id: Mapped[UUID] = mapped_column(ForeignKey("sport.sport_id"))
    header: Mapped[str | None]
    text: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSONB()))
    url: Mapped[str]
    news_creation_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=False)
    )
    pipeline_status: Mapped[PipelineStatus | None]
    pipeline_update_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=False)
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class FormattedNews(Model):
    __tablename__ = "formatted_news"
    formatted_news_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    sport_id: Mapped[UUID] = mapped_column(ForeignKey("sport.sport_id"))
    header: Mapped[str | None]
    text: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSONB()))
    url: Mapped[str]
    keywords: Mapped[list[str]] = mapped_column(MutableList.as_mutable(JSONB()))
    news_creation_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=False)
    )
    relevant_matches: Mapped[list["Match"] | None] = relationship(
        back_populates="formatted_news",
        uselist=True,
        secondary="filtered_match_in_news",
        cascade="save-update, expunge, merge",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )


class FilteredMatchInNews(Model):
    __tablename__ = "filtered_match_in_news"
    match_id: Mapped[UUID] = mapped_column(
        ForeignKey("match.match_id"), primary_key=True
    )
    news_id: Mapped[UUID] = mapped_column(
        ForeignKey("formatted_news.formatted_news_id"), primary_key=True
    )
    respective_relevance: Mapped[int | None]

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), default=utcnow_naive()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        default=utcnow_naive(),
        onupdate=utcnow_naive(),
    )
