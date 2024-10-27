from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from uuid6 import uuid6

from flux_orm.database import Model
from flux_orm.cs import mapped_column, ForeignKey, UUID, Mapped

''' Ориентировочная последовательность взаимодействия с таблицами - сверху вниз'''
'''THESE TABLES WERE CREATED ACCORDING TO SOLID+ PRINCIPLES'''


class Sport(Model):
    __tablename__ = "sport"
    sport_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    competitions: Mapped[list["Competition"]] = relationship(
        back_populates="sport",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        lazy="joined"
    )


class Competition(Model):
    __tablename__ = "competition"
    competition_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    sport_id: Mapped[UUID] = mapped_column(ForeignKey('sport.sport_id'))
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    sport: Mapped["Sport"] = relationship(
        back_populates="competitions",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="competition",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        lazy="joined",
    )
    categories: Mapped[list["CompetitionCategory"] | None] = relationship(
        back_populates="competitions",
        uselist=True,
        secondary="competition_in_category",
        cascade="save-update, expunge, merge, delete",
        lazy="joined",
    )
    teams: Mapped[list["Team"] | None] = relationship(
        back_populates="competitions",
        uselist=True,
        secondary="team_in_competition",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )


class CompetitionInCategory(Model):
    __tablename__ = "competition_in_category"
    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'), primary_key=True
                                                 )
    category_id: Mapped[UUID] = mapped_column(ForeignKey('competition_category.category_id', ondelete="CASCADE"),
                                              primary_key=True
                                              )


class CompetitionCategory(Model):
    __tablename__ = "competition_category"
    category_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    competitions: Mapped[list["Competition"] | None] = relationship(back_populates="categories",
                                                                    uselist=True,
                                                                    secondary="competition_in_category",
                                                                    cascade="save-update, expunge, merge",
                                                                    lazy="joined",
                                                                    passive_deletes=True)


class TeamInCompetition(Model):
    __tablename__ = "team_in_competition"
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'),
                                          primary_key=True)
    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'),
                                                 primary_key=True,
                                                )

    place: Mapped[int | None]
    stats = mapped_column(JSONB)


class Team(Model):
    __tablename__ = "team"
    team_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    matches: Mapped[list["Match"] | None] = relationship(
        back_populates="match_teams",
        uselist=True,
        secondary="team_in_match",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    competitions: Mapped[list["Competition"] | None] = relationship(
        back_populates="teams",
        uselist=True,
        secondary="team_in_competition",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    members: Mapped[list["TeamMember"] | None] = relationship(
        back_populates="team",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        secondary="player_in_team",
        lazy="joined",
        
    )
    coaches: Mapped[list["Coach"] | None] = relationship(
        back_populates="teams",
        uselist=True,
        secondary="coach_in_team",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    substitutions: Mapped[list["Substitution"] | None] = relationship(
        back_populates="team",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        lazy="joined")
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    stats = mapped_column(JSONB)
    regalia = mapped_column(JSONB)


class PlayerInTeam(Model):
    __tablename__ = "player_in_team"
    player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    team_id: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)


# class PlayerInMatchStats(Model):
#     __tablename__ = "player_in_match_stats"
#     player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
#     match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
#     stats = mapped_column(JSONB)


class TeamMember(Model):
    __tablename__ = "team_member"
    player_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    team: Mapped[list["Team"]] = relationship("Team",
                                              back_populates="members",
                                              uselist=True,
                                              secondary="player_in_team",
                                              cascade="save-update, expunge, merge",
                                              lazy="joined",
                                              )
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


class MatchStatus(Model):
    __tablename__ = "match_status"
    status_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    match: Mapped[list["Match"]] = relationship(back_populates="match_status",
                                          uselist=True,
                                          cascade="save-update, expunge, merge",
                                          lazy="joined")
    name: Mapped[str]
    status = mapped_column(JSONB, nullable=True)
    image_url: Mapped[str | None]


class Match(Model):
    __tablename__ = "match"
    match_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    match_name: Mapped[str]
    match_status: Mapped["MatchStatus"] = relationship(
        back_populates="match",
        uselist=False,
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    match_teams: Mapped[list["Team"] | None] = relationship(
        back_populates="matches",
        uselist=True,
        secondary="team_in_match",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    ai_statements: Mapped[list["MatchAIStatement"] | None] = relationship(
        back_populates="matches",
        uselist=True,
        secondary="ai_statement_in_match",
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    substitutions: Mapped[list["Substitution"] | None] = relationship(
        back_populates="match",
        uselist=True,
        cascade="save-update, expunge, merge, delete",
        lazy="joined"
    )
    competition_id: Mapped[UUID] = mapped_column(ForeignKey('competition.competition_id'))
    competition: Mapped["Competition"] = relationship(
        back_populates="matches",
        uselist=False,
        cascade="save-update, expunge, merge",
        lazy="joined"
    )
    status_id: Mapped[UUID] = mapped_column(ForeignKey('match_status.status_id'), unique=True)
    planned_start_datetime: Mapped[datetime | None]
    end_datetime: Mapped[datetime | None]


class AIStatementInMatch(Model):
    __tablename__ = "ai_statement_in_match"
    statement_fk: Mapped[UUID] = mapped_column(ForeignKey('match_ai_statement.statement_id'),
                                               primary_key=True,
                                               )
    match_fk: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)


class MatchAIStatement(Model):
    __tablename__ = "match_ai_statement"
    statement_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    matches: Mapped[list["Match"] | None] = relationship(back_populates="ai_statements",
                                                         uselist=True,
                                                         secondary="ai_statement_in_match",
                                                         cascade="save-update, expunge, merge, delete",
                                                         lazy="joined")


class Coach(Model):
    __tablename__ = "coach"
    coach_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6)
    name: Mapped[str]
    description: Mapped[str | None]
    image_url: Mapped[str | None]
    teams: Mapped[list["Team"] | None] = relationship(back_populates="coaches",
                                                      uselist=True,
                                                      secondary="coach_in_team",
                                                      cascade="save-update, expunge, merge",
                                                      lazy="joined")
    stats = mapped_column(JSONB)
    regalia = mapped_column(JSONB)


class CoachInTeam(Model):
    __tablename__ = "coach_in_team"
    coach_fk: Mapped[UUID] = mapped_column(ForeignKey('coach.coach_id'), primary_key=True)
    team_fk: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'), primary_key=True)


class Substitution(Model):
    __tablename__ = "substitution"
    match_id: Mapped[UUID] = mapped_column(ForeignKey('match.match_id'), primary_key=True)
    match: Mapped["Match"] = relationship(back_populates="substitutions",
                                          uselist=False,
                                          cascade="save-update, expunge, merge",
                                          lazy="joined")
    team: Mapped["Team"] = relationship(back_populates="substitutions",
                                        uselist=False,
                                        cascade="save-update, expunge, merge",
                                        lazy="joined")
    prev_player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    new_player_id: Mapped[UUID] = mapped_column(ForeignKey('team_member.player_id'), primary_key=True)
    time: Mapped[int | None]
    team_fk: Mapped[UUID] = mapped_column(ForeignKey('team.team_id'))
