from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from models.database import Model
from models import mapped_column, ForeignKey, UUID, Mapped


class Team(Model):
    __tablename__ = "team"
    team_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    stats = mapped_column(JSONB)
    regalia = mapped_column(JSONB)


class TeamMember(Model):
    __tablename__ = "team_member"
    player_id: Mapped[UUID] = mapped_column(primary_key=True)
    nickname: Mapped[str]
    age: Mapped[int | None]
    country: Mapped[str | None]
    stats = mapped_column(JSONB)
    description: Mapped[str | None]
    image_url: Mapped[str | None]


class TeamInMatch(Model):
    __tablename__ = "team_in_match"
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)
    match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
    place: Mapped[int | None]
    stats = mapped_column(JSONB, nullable=True)


class PlayerInTeam(Model):
    __tablename__ = "player_in_team"
    player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)


class PlayerInMatchStats(Model):
    __tablename__ = "player_in_match_stats"
    player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
    stats = mapped_column(JSONB)


class Substitution(Model):
    __tablename__ = "substitution"
    match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
    prev_player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    new_player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    time: Mapped[int | None]
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'))


class MatchAIStatement(Model):
    __tablename__ = "match_ai_statement"
    statement_id: Mapped[UUID] = mapped_column(primary_key=True)
    statement: Mapped[str]
    match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'))


class CoachInTeam(Model):
    __tablename__ = "coach_in_team"
    coach_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)