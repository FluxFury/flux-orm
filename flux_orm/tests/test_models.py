import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from flux_orm.database import new_session
from flux_orm.models.models import (
    Sport,
    Competition,
    Team,
    TeamMember,
    Coach,
    Match,
    MatchStatus,
    Substitution,
    CompetitionCategory,
    MatchAIStatement,
    CompetitionInCategory,
)
from flux_orm.models.enums import MatchStatusEnum


# -------------------- helpers -------------------- #
def with_(query, *opts):
    """Небольшой хелпер для лаконичного .options(selectinload(...))."""
    return query.options(*opts)

def eager(query, *opts, fresh=False):
    q = query.options(*opts)
    if fresh:
        q = q.execution_options(populate_existing=True)
    return q


async def clear_cache(session):
    """Сбросить identity-map, чтобы выбрать свежие данные."""
    await session.run_sync(lambda s: s.expire_all())

# -------------------- базовая инициализация -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_setup_sports():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sports = [
            Sport(name="Soccer", description="A popular sport"),
            Sport(name="Basketball", description="With a basket"),
            Sport(name="Test Sport"),
            Sport(name="Sport with Competitions"),
            Sport(name="New Sport"),
            Sport(name="Team Competition Sport"),
            Sport(name="Competition for Match Sport"),
            Sport(name="Category Sport"),
            Sport(name="AI Statement Sport"),
            Sport(name="Delete Test Sport"),
        ]
        session.add_all(sports)
        await session.commit()


# -------------------- ON DELETE CASCADE (M-M Category) -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_cascade_with_ondelete():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        comps = [Competition(sport=sport, name=f"C{i}") for i in range(3)]
        cats = [CompetitionCategory(name=f"Cat {i}") for i in range(3)]
        for c in comps:
            c.categories = cats
        session.add_all(comps)
        await session.commit()

        before = (
            await session.execute(select(CompetitionInCategory))
        ).scalars().all()

        await session.delete(cats[0])
        await session.commit()
        await clear_cache(session)

        after = (
            await session.execute(select(CompetitionInCategory))
        ).scalars().all()
        assert len(after) == len(before) - len(comps)


# -------------------- Competition-Match каскад -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        comp = Competition(name="Comp-del", sport=sport)
        session.add(comp)
        await session.commit()

        t1, t2 = Team(name="X"), Team(name="Y")
        session.add_all([t1, t2])
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.SCHEDULED)
        session.add(status)
        await session.commit()

        match = Match(
            match_name="M-del",
            competition=comp,
            sport=sport,
            match_status=status,
            external_id="m-del",
            match_teams=[t1, t2],
        )
        session.add(match)
        await session.commit()

        await session.delete(comp)
        await session.commit()
        await clear_cache(session)

        assert not (
            await session.execute(select(Match).filter_by(match_name="M-del"))
        ).scalars().all()

        teams = (
            await session.execute(select(Team).filter(Team.name.in_(["X", "Y"])))
        ).scalars().all()
        assert len(teams) == 2


# -------------------- Team ↔ Members -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_team_with_members():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(
            name="Team F",
            members=[TeamMember(name="Player One"), TeamMember(name="Player Two")],
        )
        session.add(team)
        await session.commit()

        members = (
            await session.execute(
                select(TeamMember).filter(
                    TeamMember.name.in_(["Player One", "Player Two"])
                )
            )
        ).scalars().all()
        assert len(members) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_team_and_check_members():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        member = TeamMember(name="Solo Player")
        team = Team(name="Team G", members=[member])
        session.add(team)
        await session.commit()

        await session.delete(team)
        await session.commit()

        assert (
            await session.execute(select(TeamMember).filter_by(name="Solo Player"))
        ).scalars().first() is None


# -------------------- Coach rename -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_update_coach_and_check_teams():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        coach = Coach(name="Coach Update")
        teams = [Team(name="Team H", coaches=[coach]), Team(name="Team I", coaches=[coach])]
        session.add_all(teams)
        await session.commit()

        coach.name = "Coach Updated"
        await session.commit()

        updated_coach = (
            await session.execute(select(Coach).filter_by(name="Coach Updated"))
        ).scalars().first()
        assert updated_coach

        loaded_teams = (
            await session.execute(
                with_(select(Team).filter(Team.name.in_(["Team H", "Team I"])),
                      selectinload(Team.coaches))
            )
        ).scalars().all()
        assert all(updated_coach in t.coaches for t in loaded_teams)


# -------------------- Match create -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_add_match_with_teams():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(
                select(Sport).filter_by(name="Competition for Match Sport")
            )
        ).scalars().first()

        status = MatchStatus(name=MatchStatusEnum.SCHEDULED)
        session.add(status)
        await session.commit()

        competition = Competition(name="Competition for Match", sport=sport)
        session.add(competition)
        await session.commit()

        team1, team2 = Team(name="Team J"), Team(name="Team K")
        session.add_all([team1, team2])
        await session.commit()

        match = Match(
            match_name="Team J vs Team K",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="123432890",
            match_teams=[team1, team2],
        )
        session.add(match)
        await session.commit()

        loaded_match = (
            await session.execute(
                with_(select(Match).filter_by(match_name="Team J vs Team K"),
                      selectinload(Match.match_teams))
            )
        ).scalars().first()
        assert loaded_match and len(loaded_match.match_teams) == 2


# -------------------- Delete TeamMember -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team_member():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        m = TeamMember(name="Transient")
        t1, t2 = Team(name="L", members=[m]), Team(name="M", members=[m])
        session.add_all([t1, t2])
        await session.commit()

        await session.delete(m)
        await session.commit()
        await clear_cache(session)

        teams = (
            await session.execute(
                eager(select(Team).filter(Team.name.in_(["L", "M"])),
                      selectinload(Team.members), fresh=True)
            )
        ).scalars().all()
        assert all(not t.members for t in teams)


# -------------------- Delete whole Team -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(
            name="Team N",
            members=[TeamMember(name="Player Alpha"), TeamMember(name="Player Beta")],
        )
        session.add(team)
        await session.commit()

        await session.delete(team)
        await session.commit()

        assert not (
            await session.execute(
                select(TeamMember).filter(
                    TeamMember.name.in_(["Player Alpha", "Player Beta"])
                )
            )
        ).scalars().all()


# -------------------- Match + substitutions -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_create_match_with_status_and_substitutions():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        status = MatchStatus(name=MatchStatusEnum.SCHEDULED)
        session.add(status)
        await session.flush()

        competition = Competition(name="Competition with Substitutions", sport=sport)
        session.add(competition)
        await session.flush()

        team1, team2 = Team(name="Team O"), Team(name="Team P")
        session.add_all([team1, team2])
        await session.flush()

        match = Match(
            match_name="Team O vs Team P",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="121321890",
            match_teams=[team1, team2],
        )
        session.add(match)
        await session.flush()

        pin, pout = TeamMember(name="Substitute In"), TeamMember(name="Substitute Out")
        session.add_all([pin, pout])
        await session.flush()

        substitution = Substitution(
            match=match,
            prev_player_id=pout.player_id,
            new_player_id=pin.player_id,
            time=45,
            team=team1,
        )
        session.add(substitution)
        await session.flush()

        saved_sub = (
            await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        ).scalars().first()
        assert saved_sub and saved_sub.time == 45
        await session.commit()


# -------------------- Delete Match & cascading substitutions -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        competition = Competition(name="Competition for Deletion Test", sport=sport)
        session.add(competition)
        await session.commit()

        team1, team2 = Team(name="Team Q"), Team(name="Team R")
        session.add_all([team1, team2])
        await session.commit()

        match = Match(
            match_name="Team Q vs Team R",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="1124214123390",
            match_teams=[team1, team2],
        )
        session.add(match)
        await session.commit()

        pin, pout = TeamMember(name="Sub In"), TeamMember(name="Sub Out")
        session.add_all([pin, pout])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=pout.player_id,
            new_player_id=pin.player_id,
            time=60,
            team=team2,
        )
        session.add(substitution)
        await session.commit()

        await session.delete(match)
        await session.commit()

        assert not (
            await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        ).scalars().all()

        still_exists = (
            await session.execute(select(MatchStatus).filter_by(name=MatchStatusEnum.LIVE))
        ).scalars().first()
        assert still_exists is not None


# -------------------- Competition ↔ Teams relation -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_relationship_team_competition():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Team Competition Sport"))
        ).scalars().first()

        comp = Competition(name="TeamComp", sport=sport)
        session.add(comp)
        await session.commit()

        t1, t2 = Team(name="S"), Team(name="T")
        session.add_all([t1, t2])
        await session.commit()

        # Получаем свежий объект с подзагруженным списком
        comp = (
            await session.execute(
                eager(select(Competition).filter_by(name="TeamComp"),
                      selectinload(Competition.teams), fresh=True)
            )
        ).scalars().first()
        comp.teams.extend([t1, t2])
        await session.commit()

        await clear_cache(session)
        comp = (
            await session.execute(
                eager(select(Competition).filter_by(name="TeamComp"),
                      selectinload(Competition.teams), fresh=True)
            )
        ).scalars().first()
        assert len(comp.teams) == 2


# -------------------- JSON-field stats update -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_update_team_stats():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(name="Team U", stats={"wins": 5, "losses": 2})
        session.add(team)
        await session.commit()

        team.stats["wins"] = 6
        await session.commit()

        refreshed = (
            await session.execute(select(Team).filter_by(name="Team U"))
        ).scalars().first()
        assert refreshed.stats["wins"] == 6


# -------------------- Delete Coach only -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_coach():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        coach = Coach(name="Del Coach")
        t1, t2 = Team(name="V", coaches=[coach]), Team(name="W", coaches=[coach])
        session.add_all([t1, t2])
        await session.commit()

        await session.delete(coach)
        await session.commit()
        await clear_cache(session)

        teams = (
            await session.execute(
                eager(select(Team).filter(Team.name.in_(["V", "W"])),
                      selectinload(Team.coaches), fresh=True)
            )
        ).scalars().all()
        assert all(not t.coaches for t in teams)


# -------------------- Competition with categories (save) -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_competition_with_categories():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        cat1, cat2 = CompetitionCategory(name="Category 1"), CompetitionCategory(name="Category 2")
        session.add_all([cat1, cat2])
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        competition = Competition(name="Competition with Categories", sport=sport, categories=[cat1, cat2])
        session.add(competition)
        await session.commit()

        comp = (
            await session.execute(
                with_(select(Competition).filter_by(name="Competition with Categories"),
                      selectinload(Competition.categories))
            )
        ).scalars().first()
        assert comp and len(comp.categories) == 2

@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_sport_with_competitions():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(
                eager(select(Sport).filter_by(name="New Sport"),
                      selectinload(Sport.competitions), fresh=True)
            )
        ).scalars().first()

        # Полностью очистить старые соревнования
        for old in list(sport.competitions):
            await session.delete(old)
        await session.commit()
        await clear_cache(session)

        # Добавляем два новых
        sport = (
            await session.execute(select(Sport).filter_by(name="New Sport").options(selectinload(Sport.competitions)))
        ).scalars().first()
        sport.competitions.extend([Competition(name="Competition C"),
                                   Competition(name="Competition D")])
        await session.commit()
        await clear_cache(session)

        # Проверяем: у спорта теперь есть ровно C и D
        refreshed = (
            await session.execute(
                eager(select(Sport).filter_by(name="New Sport"),
                      selectinload(Sport.competitions), fresh=True)
            )
        ).scalars().first()

        names = {c.name for c in refreshed.competitions}
        assert names.issuperset({"Competition C", "Competition D"})
        assert sum(n in {"Competition C", "Competition D"} for n in names) == 2

# -------------------- Delete CompetitionCategory -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition_category():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        cat = CompetitionCategory(name="Cat-Del")
        session.add(cat)
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Category Sport"))
        ).scalars().first()

        comp = Competition(name="Comp-Cat-Del", sport=sport, categories=[cat])
        session.add(comp)
        await session.commit()

        await session.delete(cat)
        await session.commit()
        await clear_cache(session)

        comp = (
            await session.execute(
                eager(select(Competition).filter_by(name="Comp-Cat-Del"),
                      selectinload(Competition.categories), fresh=True)
            )
        ).scalars().first()
        assert not comp.categories


# -------------------- Delete MatchStatus -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match_status():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        ).scalars().first()

        comp = Competition(name="Comp-Status", sport=sport)
        session.add(comp)
        await session.commit()

        match = Match(
            match_name="Match-Status",
            competition=comp,
            match_status=status,
            sport=sport,
            external_id="ms",
        )
        session.add(match)
        await session.commit()

        await session.delete(status)
        await session.commit()
        await clear_cache(session)

        match = (
            await session.execute(
                eager(select(Match).filter_by(match_name="Match-Status"),
                      selectinload(Match.match_status), fresh=True)
            )
        ).scalars().first()
        assert match.match_status is None


# -------------------- Delete Substitution only -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_substitution():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        competition = Competition(name="Competition for Substitution Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        team = Team(name="Team for Substitution")
        session.add(team)
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        match = Match(
            match_name="Match for Substitution Deletion",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="112241241413390",
            match_teams=[team],
        )
        session.add(match)
        await session.commit()

        pin, pout = TeamMember(name="Sub In Player"), TeamMember(name="Sub Out Player")
        session.add_all([pin, pout])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=pout.player_id,
            new_player_id=pin.player_id,
            time=30,
            team=team,
        )
        session.add(substitution)
        await session.commit()

        await session.delete(substitution)
        await session.commit()

        # убедимся, что замена удалена, матч и команда живы
        assert not (
            await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        ).scalars().all()

        assert (
            await session.execute(select(Match).filter_by(match_name=match.match_name))
        ).scalars().first()

        assert (
            await session.execute(select(Team).filter_by(name=team.name))
        ).scalars().first()


# -------------------- Delete AI-statement only -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_ai_statement():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="AI Statement Sport"))
        ).scalars().first()

        competition = Competition(name="Competition for AI Statement Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        match = Match(
            match_name="Match with AI Statement",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="1122542553252241413390",
        )
        session.add(match)
        await session.commit()

        ai_stmt = MatchAIStatement(matches=[match])
        session.add(ai_stmt)
        await session.commit()

        await session.delete(ai_stmt)
        await session.commit()

        remaining_match = (
            await session.execute(
                with_(select(Match).filter_by(match_name="Match with AI Statement"),
                      selectinload(Match.ai_statements))
            )
        ).scalars().first()
        assert remaining_match and not remaining_match.ai_statements


# -------------------- Update TeamMember -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_update_team_member():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        member = TeamMember(name="Updatable Player", age=25, country="Country A")
        session.add(member)
        await session.commit()

        member.age = 26
        member.country = "Country B"
        await session.commit()

        updated = (
            await session.execute(select(TeamMember).filter_by(name="Updatable Player"))
        ).scalars().first()
        assert updated.age == 26 and updated.country == "Country B"


# -------------------- Dynamic add/remove members -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_add_remove_team_member_from_team():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team, m1, m2 = Team(name="Dynamic Team"), TeamMember(name="Dynamic Player 1"), TeamMember(name="Dynamic Player 2")
        session.add_all([team, m1, m2])
        await session.commit()

        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Dynamic Team"),
                      selectinload(Team.members))
            )
        ).scalars().first()
        team.members.extend([m1, m2])
        await session.commit()

        # refresh с подзагрузкой, чтобы избежать MissingGreenlet
        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Dynamic Team"),
                      selectinload(Team.members))
            )
        ).scalars().first()
        assert len(team.members) == 2

        team.members.remove(m1)
        await session.commit()

        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Dynamic Team"),
                      selectinload(Team.members))
            )
        ).scalars().first()
        assert len(team.members) == 1 and m2 in team.members


# -------------------- Dynamic add/remove coaches -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_add_remove_coach_from_team():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team, c1, c2 = Team(name="Coachable Team"), Coach(name="Coach A"), Coach(name="Coach B")
        session.add_all([team, c1, c2])
        await session.commit()

        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Coachable Team"),
                      selectinload(Team.coaches))
            )
        ).scalars().first()
        team.coaches.extend([c1, c2])
        await session.commit()

        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Coachable Team"),
                      selectinload(Team.coaches))
            )
        ).scalars().first()
        assert len(team.coaches) == 2

        team.coaches.remove(c1)
        await session.commit()

        team = (
            await session.execute(
                with_(select(Team).filter_by(name="Coachable Team"),
                      selectinload(Team.coaches))
            )
        ).scalars().first()
        assert len(team.coaches) == 1 and c2 in team.coaches


# -------------------- Competition delete with matches -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition_with_matches():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        ).scalars().first()

        competition = Competition(name="Competition with Matches", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        match1 = Match(
            match_name="Match 1",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="m1",
        )
        match2 = Match(
            match_name="Match 2",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="m2",
        )
        session.add_all([match1, match2])
        await session.commit()

        await session.delete(competition)
        await session.commit()

        assert not (
            await session.execute(
                select(Match).filter(Match.match_name.in_(["Match 1", "Match 2"]))
            )
        ).scalars().all()


# -------------------- Delete Sport + categories -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_sport_with_categories():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        cat1, cat2 = CompetitionCategory(name="Sport Deletion Category 1"), CompetitionCategory(name="Sport Deletion Category 2")
        session.add_all([cat1, cat2])
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        ).scalars().first()

        comp_x = Competition(name="Competition X", sport=sport, categories=[cat1])
        comp_y = Competition(name="Competition Y", sport=sport, categories=[cat2])
        session.add_all([comp_x, comp_y])
        await session.commit()

        await session.delete(sport)
        await session.commit()

        assert not (
            await session.execute(
                select(Competition).filter(Competition.name.in_(["Competition X", "Competition Y"]))
            )
        ).scalars().all()

        assert not (
            await session.execute(
                select(CompetitionCategory).filter(
                    CompetitionCategory.name.in_(
                        ["Sport Deletion Category 1", "Sport Deletion Category 2"]
                    )
                )
            )
        ).scalars().all()


# -------------------- Update MatchStatus -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_update_match_status():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        competition = Competition(name="Competition for Status Update", sport=sport)
        session.add(competition)
        await session.commit()

        match = Match(
            match_name="Match for Status Update",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="1131232141413390",
        )
        session.add(match)
        await session.commit()

        status.name = MatchStatusEnum.SCHEDULED
        await session.commit()

        updated_match = (
            await session.execute(
                with_(select(Match).filter_by(match_name="Match for Status Update"),
                      selectinload(Match.match_status))
            )
        ).scalars().first()
        assert updated_match.match_status.name == MatchStatusEnum.SCHEDULED


# -------------------- Delete Team in Competition -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_delete_team_in_competition():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        comp = Competition(name="Comp-Team-Del", sport=sport)
        session.add(comp)
        await session.commit()

        team = Team(name="Team-Del")
        session.add(team)
        await session.commit()

        comp = (
            await session.execute(
                eager(select(Competition).filter_by(name="Comp-Team-Del"),
                      selectinload(Competition.teams), fresh=True)
            )
        ).scalars().first()
        comp.teams.append(team)
        await session.commit()

        await session.delete(team)
        await session.commit()
        await clear_cache(session)

        comp = (
            await session.execute(
                eager(select(Competition).filter_by(name="Comp-Team-Del"),
                      selectinload(Competition.teams), fresh=True)
            )
        ).scalars().first()
        assert not comp.teams


# -------------------- Delete Player in Team -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_player_in_team():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(name="Team-Player-Del")
        member = TeamMember(name="Player-Del")
        session.add_all([team, member])
        await session.commit()

        # перезагружаем team с members, чтобы избежать ленивой загрузки
        team = (
            await session.execute(
                eager(select(Team).filter_by(name="Team-Player-Del"),
                      selectinload(Team.members), fresh=True)
            )
        ).scalars().first()
        team.members.append(member)
        await session.commit()

        await session.delete(member)
        await session.commit()
        await clear_cache(session)

        team = (
            await session.execute(
                eager(select(Team).filter_by(name="Team-Player-Del"),
                      selectinload(Team.members), fresh=True)
            )
        ).scalars().first()
        assert not team.members


# -------------------- Delete Coach in Team -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_coach_in_team():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(name="Team-Coach-Del")
        coach = Coach(name="Coach-Del")
        session.add_all([team, coach])
        await session.commit()

        team = (
            await session.execute(
                eager(select(Team).filter_by(name="Team-Coach-Del"),
                      selectinload(Team.coaches), fresh=True)
            )
        ).scalars().first()
        team.coaches.append(coach)
        await session.commit()

        await session.delete(coach)
        await session.commit()
        await clear_cache(session)

        team = (
            await session.execute(
                eager(select(Team).filter_by(name="Team-Coach-Del"),
                      selectinload(Team.coaches), fresh=True)
            )
        ).scalars().first()
        assert not team.coaches



# -------------------- Delete Match with AI-statements -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match_with_ai_statements():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        sport = (
            await session.execute(select(Sport).filter_by(name="AI Statement Sport"))
        ).scalars().first()

        comp = Competition(name="Comp-AI-Del", sport=sport)
        session.add(comp)
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        match = Match(
            match_name="Match-AI-Del",
            competition=comp,
            match_status=status,
            sport=sport,
            external_id="maid",
        )
        session.add(match)
        await session.commit()

        ai_stmt = MatchAIStatement(matches=[match])
        session.add(ai_stmt)
        await session.commit()

        await session.delete(match)
        await session.commit()
        await clear_cache(session)

        ai_stmts = (
            await session.execute(
                eager(select(MatchAIStatement), selectinload(MatchAIStatement.matches), fresh=True)
            )
        ).scalars().all()
        assert all(not s.matches for s in ai_stmts)


# -------------------- Delete Team with substitutions -------------------- #
@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team_with_substitutions():
    async with new_session(expire_on_commit=False, autoflush=False) as session:
        team = Team(name="Team with Substitutions")
        session.add(team)
        await session.commit()

        sport = (
            await session.execute(select(Sport).filter_by(name="Test Sport"))
        ).scalars().first()

        competition = Competition(name="Competition for Team Deletion with Substitutions", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name=MatchStatusEnum.LIVE)
        session.add(status)
        await session.commit()

        match = Match(
            match_name="Match with Substitutions",
            competition=competition,
            match_status=status,
            sport=sport,
            external_id="1762343390",
            match_teams=[team],
        )
        session.add(match)
        await session.commit()

        pin, pout = TeamMember(name="Sub Player In"), TeamMember(name="Sub Player Out")
        session.add_all([pin, pout])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=pout.player_id,
            new_player_id=pin.player_id,
            time=70,
            team=team,
        )
        session.add(substitution)
        await session.commit()

        await session.delete(team)
        await session.commit()

        subs_after = (
            await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        ).scalars().all()
        assert not subs_after

        remaining_match = (
            await session.execute(select(Match).filter_by(match_name=match.match_name))
        ).scalars().first()
        assert remaining_match
