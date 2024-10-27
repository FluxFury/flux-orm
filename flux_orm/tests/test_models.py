import pytest
from sqlalchemy import select

from flux_orm.database import new_session
from flux_orm.cs.models import (
    Sport, Competition, Team, TeamMember, Coach,
    Match, MatchStatus, Substitution, CompetitionCategory, MatchAIStatement, CompetitionInCategory
)


@pytest.mark.asyncio(loop_scope="session")
async def test_setup_sports():
    async with new_session() as session:
        # Создаем и сохраняем все спорты, которые будут использоваться в тестах
        sports = [
            Sport(name="Soccer", description="A popular sport", image_url="soccer.png"),
            Sport(name="Basketball", description="A sport with a ball and a basket", image_url="basketball.png"),
            Sport(name="Test Sport", description="A test sport", image_url=None),
            Sport(name="Sport with Competitions", description="Sport for competitions", image_url=None),
            Sport(name="New Sport", description="Another new sport", image_url=None),
            Sport(name="Team Competition Sport", description="Sport for team competition", image_url=None),
            Sport(name="Competition for Match Sport", description="Sport for competition matches", image_url=None),
            Sport(name="Category Sport", description="Sport for category tests", image_url=None),
            Sport(name="AI Statement Sport", description="Sport for AI statement tests", image_url=None),
            Sport(name="Delete Test Sport", description="Sport for delete tests", image_url=None),
        ]
        session.add_all(sports)
        await session.commit()

@pytest.mark.asyncio(loop_scope="session")
async def test_delete_cascade_with_ondelete():
    async with new_session() as session:

        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        competitions = [Competition(sport=sport, name="Competition 1"),
                        Competition(sport=sport, name="Competition 2"),
                        Competition(sport=sport, name="Competition 3")]
        categories = [CompetitionCategory(name="Category 1"),
                      CompetitionCategory(name="Category 2"),
                      CompetitionCategory(name="Category 3")]

        for competition in competitions:
            competition.categories = categories
        session.add_all(competitions)
        await session.commit()
        query = select(CompetitionInCategory)
        result = await session.execute(query)
        competition_in_categories_1 = result.scalars().all()
        print(competition_in_categories_1)

        for competition_in_category in competition_in_categories_1:
            print((competition_in_category.competition_id, competition_in_category.category_id))

        query2 = select(CompetitionCategory)
        result2 = await session.execute(query2)
        W = result2.scalars().first()

        await session.delete(W)

        await session.commit()
        zapros = select(CompetitionCategory)
        result = await session.execute(zapros)
        print(len(result.scalars().unique().all()))

        query = select(CompetitionInCategory)
        result = await session.execute(query)
        competition_in_categories_2 = result.scalars().unique().all()

        for competition_in_category in competition_in_categories_2:
            print((competition_in_category.competition_id, competition_in_category.category_id))

        print(competition_in_categories_2)
        assert len(competition_in_categories_2) == len(competition_in_categories_1) - 3

@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition():
    async with new_session() as session:
        # Fetch existing sport
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Test Sport should exist"

        # Create a Competition with the existing sport_id
        competition = Competition(name="Test Competition", sport=sport)
        session.add(competition)
        await session.commit()

        # Create Teams and Match
        team1 = Team(name="Team X")
        team2 = Team(name="Team Y")
        session.add_all([team1, team2])
        await session.commit()

        status = MatchStatus(name="Scheduled")
        session.add(status)
        await session.commit()

        match = Match(match_name="Test Match", competition=competition, match_status=status)
        match.match_teams = [team1, team2]
        session.add(match)
        await session.commit()

        # Delete the Competition and check that Matches are also deleted
        await session.delete(competition)
        await session.commit()

        # Verify that the Matches are deleted
        result = await session.execute(select(Match).filter_by(match_name="Test Match"))
        matches = result.scalars().all()
        assert not matches, "Matches should be deleted when competition is deleted"

        # Verify that Teams are not deleted
        result = await session.execute(select(Team).filter(Team.name.in_(["Team X", "Team Y"])))
        teams = result.unique().scalars().all()
        print(teams)
        assert len(teams) == 2, "Teams should not be deleted when competition is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_team_with_members():
    async with new_session() as session:
        # Create Team with Members
        member1 = TeamMember(nickname="Player One")
        member2 = TeamMember(nickname="Player Two")
        team = Team(name="Team F", members=[member1, member2])

        session.add(team)
        await session.commit()

        # Verify that the Members are saved
        result = await session.execute(select(TeamMember).filter(TeamMember.nickname.in_(["Player One", "Player Two"])))
        members = result.unique().scalars().all()
        assert len(members) == 2, "Team members should be saved with the team"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_team_and_check_members():
    async with new_session() as session:
        # Create Team with Members
        member = TeamMember(nickname="Solo Player")
        team = Team(name="Team G", members=[member])
        session.add(team)
        await session.commit()

        # Delete the Team
        await session.delete(team)
        await session.commit()

        # Check if the TeamMember still exists
        result = await session.execute(select(TeamMember).filter_by(nickname="Solo Player"))
        remaining_member = result.scalars().first()
        assert remaining_member is None, "TeamMember should be deleted when team is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_coach_and_check_teams():
    async with new_session() as session:
        # Create Coach and Teams
        coach = Coach(name="Coach Update")
        team1 = Team(name="Team H", coaches=[coach])
        team2 = Team(name="Team I", coaches=[coach])
        session.add_all([team1, team2])
        await session.commit()

        # Update Coach's name
        coach.name = "Coach Updated"
        await session.commit()

        # Verify that the updated coach is reflected in Teams
        result = await session.execute(select(Coach).filter_by(name="Coach Updated"))
        updated_coach = result.scalars().first()
        assert updated_coach is not None, "Coach's name should be updated"

        # Verify that Teams still reference the updated coach
        result = await session.execute(select(Team).filter(Team.name.in_(["Team H", "Team I"])))
        teams = result.unique().scalars().all()
        for team in teams:
            assert updated_coach in team.coaches, f"{team.name} should have the updated coach"


@pytest.mark.asyncio(loop_scope="session")
async def test_add_match_with_teams():
    async with new_session() as session:
        # Fetch existing sport for the competition
        result = await session.execute(select(Sport).filter_by(name="Competition for Match Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Competition for Match Sport should exist"

        # Create and commit MatchStatus
        status = MatchStatus(name="Scheduled")
        session.add(status)
        await session.commit()

        # Create and commit Competition with existing sport_id
        competition = Competition(name="Competition for Match", sport=sport)
        session.add(competition)
        await session.commit()

        # Create Teams and commit
        team1 = Team(name="Team J")
        team2 = Team(name="Team K")
        session.add_all([team1, team2])
        await session.commit()

        # Create Match with existing competition_id and status_id
        match = Match(
            match_name="Team J vs Team K",
            competition=competition,
            match_status=status
        )
        match.match_teams = [team1, team2]
        session.add(match)
        await session.commit()

        # Verify that Match is saved with Teams
        result = await session.execute(select(Match).filter_by(match_name="Team J vs Team K"))
        saved_match = result.scalars().first()
        assert saved_match is not None, "Match should be saved"
        assert len(saved_match.match_teams) == 2, "Match should have two teams"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team_member():
    async with new_session() as session:
        # Create TeamMember and associate with Teams
        member = TeamMember(nickname="Transient Player")
        team1 = Team(name="Team L", members=[member])
        team2 = Team(name="Team M", members=[member])
        session.add_all([team1, team2])
        await session.commit()

        # Delete the TeamMember
        await session.delete(member)
        await session.commit()

        # Verify that TeamMember is deleted
        result = await session.execute(select(TeamMember).filter_by(nickname="Transient Player"))
        deleted_member = result.scalars().first()
        assert deleted_member is None, "TeamMember should be deleted"

        # Verify that Teams still exist
        result = await session.execute(select(Team).filter(Team.name.in_(["Team L", "Team M"])))
        teams = result.unique().scalars().all()
        assert len(teams) == 2, "Teams should not be deleted when member is deleted"

        # Verify that Teams no longer have the member in their members list
        for team in teams:
            assert member not in team.members, "Teams should not have the deleted member"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team():
    async with new_session() as session:
        # Create Team with Members
        member1 = TeamMember(nickname="Player Alpha")
        member2 = TeamMember(nickname="Player Beta")
        team = Team(name="Team N", members=[member1, member2])
        session.add(team)
        await session.commit()

        # Delete the Team
        await session.delete(team)
        await session.commit()

        # Verify that Team is deleted
        result = await session.execute(select(Team).filter_by(name="Team N"))
        deleted_team = result.scalars().first()
        assert deleted_team is None, "Team should be deleted"

        # Verify that TeamMembers still exist
        result = await session.execute(
            select(TeamMember).filter(TeamMember.nickname.in_(["Player Alpha", "Player Beta"])))
        members = result.scalars().all()
        assert len(members) == 0, "TeamMembers should be deleted when team is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_match_with_status_and_substitutions():
    async with new_session() as session:
        # Fetch existing sport for the competition
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Test Sport should exist"

        # Create and commit MatchStatus
        status = MatchStatus(name="Scheduled")
        session.add(status)
        await session.flush()

        # Create Competition with existing sport_id
        competition = Competition(name="Competition with Substitutions", sport=sport)
        session.add(competition)
        await session.flush()

        # Create Teams
        team1 = Team(name="Team O")
        team2 = Team(name="Team P")
        session.add_all([team1, team2])
        await session.flush()

        # Create Match
        match = Match(
            match_name="Team O vs Team P",
            competition=competition,
            match_status=status
        )
        match.match_teams = [team1, team2]
        session.add(match)
        await session.flush()

        # Create Substitution
        player_in = TeamMember(nickname="Substitute In")
        player_out = TeamMember(nickname="Substitute Out")
        session.add_all([player_in, player_out])
        await session.flush()

        substitution = Substitution(
            match=match,
            prev_player_id=player_out.player_id,
            new_player_id=player_in.player_id,
            time=45,
            team=team1
        )
        session.add(substitution)
        await session.flush()

        # Verify that Substitution is saved
        result = await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        saved_substitution = result.scalars().first()
        assert saved_substitution is not None, "Substitution should be saved"
        assert saved_substitution.time == 45, "Substitution time should be 45"

        await session.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match():
    async with new_session() as session:
        # Fetch existing sport for the competition
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Test Sport should exist"

        # Create and commit MatchStatus
        status = MatchStatus(name="In Progress")
        session.add(status)
        await session.commit()
        # Create Competition with existing sport_id
        competition = Competition(name="Competition for Deletion Test", sport=sport)
        session.add(competition)
        await session.commit()

        team1 = Team(name="Team Q")
        team2 = Team(name="Team R")
        session.add_all([team1, team2])
        await session.commit()

        match = Match(
            match_name="Team Q vs Team R",
            competition=competition,
            match_status=status
        )
        match.match_teams = [team1, team2]
        session.add(match)
        await session.commit()

        # Create Substitution
        player_in = TeamMember(nickname="Sub In")
        player_out = TeamMember(nickname="Sub Out")
        session.add_all([player_in, player_out])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=player_out.player_id,
            new_player_id=player_in.player_id,
            time=60,
            team=team2
        )
        session.add(substitution)
        await session.commit()

        # Delete Match
        await session.delete(match)
        await session.commit()

        # Verify that Match is deleted
        result = await session.execute(select(Match).filter_by(match_name="Team Q vs Team R"))
        deleted_match = result.scalars().first()
        assert deleted_match is None, "Match should be deleted"

        # Verify that Substitution is also deleted
        result = await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        substitutions = result.scalars().all()
        assert not substitutions, "Substitutions should be deleted when match is deleted"

        # Verify that MatchStatus still exists
        result = await session.execute(select(MatchStatus).filter_by(name="In Progress"))
        status_exists = result.scalars().first()
        assert status_exists is not None, "MatchStatus should not be deleted when match is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_relationship_team_competition():
    async with new_session() as session:
        # Fetch existing sport
        result = await session.execute(select(Sport).filter_by(name="Team Competition Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Team Competition Sport should exist"

        # Create Competition with existing sport_id
        competition = Competition(name="Team Competition Test", sport=sport, teams=[])
        session.add(competition)
        await session.commit()

        # Create Teams
        team1 = Team(name="Team S")
        team2 = Team(name="Team T")
        session.add_all([team1, team2])
        await session.commit()

        # Associate Teams with Competition
        competition.teams.extend([team1, team2])
        await session.commit()

        # Verify that Teams are associated with Competition
        result = await session.execute(select(Competition).filter_by(name="Team Competition Test"))
        comp = result.scalars().first()
        assert len(comp.teams) == 2, "Competition should have two teams"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_team_stats():
    async with new_session() as session:
        # Create Team
        team = Team(name="Team U", stats={"wins": 5, "losses": 2})
        session.add(team)
        await session.commit()

        # Update Team stats
        team.stats["wins"] = 6
        await session.commit()

        # Verify that stats are updated
        result = await session.execute(select(Team).filter_by(name="Team U"))
        updated_team = result.scalars().first()
        assert updated_team.stats["wins"] == 6, "Team's wins should be updated to 6"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_coach():
    async with new_session() as session:
        # Create Coach and Teams
        coach = Coach(name="Coach Delete Test")
        team1 = Team(name="Team V", coaches=[coach])
        team2 = Team(name="Team W", coaches=[coach])
        session.add_all([team1, team2])
        await session.commit()

        # Delete Coach
        await session.delete(coach)
        await session.commit()

        # Verify that Coach is deleted
        result = await session.execute(select(Coach).filter_by(name="Coach Delete Test"))
        deleted_coach = result.scalars().first()
        assert deleted_coach is None, "Coach should be deleted"

        # Verify that Teams still exist
        result = await session.execute(select(Team).filter(Team.name.in_(["Team V", "Team W"])))
        teams = result.unique().scalars().all()
        assert len(teams) == 2, "Teams should not be deleted when coach is deleted"

        # Verify that Teams no longer have the coach in their coaches list
        for team in teams:
            assert coach not in team.coaches, "Teams should not have the deleted coach"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_competition_with_categories():
    async with new_session() as session:
        # Create Competition Categories
        category1 = CompetitionCategory(name="Category 1")
        category2 = CompetitionCategory(name="Category 2")
        session.add_all([category1, category2])
        await session.commit()

        # Fetch existing sport
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Test Sport should exist"

        # Create Competition with existing sport_id and associate with Categories
        competition = Competition(
            name="Competition with Categories",
            sport=sport,
            categories=[category1, category2]
        )
        session.add(competition)
        await session.commit()

        # Verify that Competition is associated with Categories
        result = await session.execute(select(Competition).filter_by(name="Competition with Categories"))
        comp = result.scalars().first()
        assert len(comp.categories) == 2, "Competition should have two categories"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_sport_with_competitions():
    async with new_session() as session:
        # Fetch existing sport
        result = await session.execute(select(Sport).filter_by(name="Sport with Competitions"))
        sport = result.scalars().first()
        assert sport is not None, "Sport with Competitions should exist"

        # Create Competitions with existing sport_id
        competition1 = Competition(name="Competition A", sport=sport)
        competition2 = Competition(name="Competition B", sport=sport)
        session.add_all([competition1, competition2])
        await session.commit()

        # Delete Sport
        await session.delete(sport)
        await session.commit()

        # Verify that Sport is deleted
        result = await session.execute(select(Sport).filter_by(name="Sport with Competitions"))
        deleted_sport = result.scalars().first()
        assert deleted_sport is None, "Sport should be deleted"

        # Verify that Competitions are not deleted
        result = await session.execute(
            select(Competition).filter(Competition.name.in_(["Competition A", "Competition B"])))
        competitions = result.scalars().all()
        assert len(competitions) == 0, "Competitions should be deleted when sport is deleted"

        # Verify that Competitions no longer have the sport associated
        for competition in competitions:
            assert competition.sport_id != sport.sport_id, "Competitions should not reference the deleted sport"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_save_sport_with_competitions():
    async with new_session() as session:
        # Fetch existing sport
        result = await session.execute(select(Sport).filter_by(name="New Sport"))
        sport = result.scalars().first()
        assert sport is not None, "New Sport should exist"

        # Clear any existing competitions associated with the sport
        sport.competitions = []
        await session.commit()

        # Create Competitions with existing sport_id
        competition1 = Competition(name="Competition C", sport=sport)
        competition2 = Competition(name="Competition D", sport=sport)
        session.add_all([competition1, competition2])
        await session.commit()

        # Verify that Competitions are saved with the Sport
        result = await session.execute(select(Sport).filter_by(name="New Sport"))
        saved_sport = result.scalars().first()
        assert len(saved_sport.competitions) == 2, "Sport should have two competitions"






# Новые тесты

@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition_category():
    async with new_session() as session:
        # Создаем категории соревнований
        category = CompetitionCategory(name="Delete Category Test")
        session.add(category)
        await session.commit()

        # Получаем существующий спорт
        result = await session.execute(select(Sport).filter_by(name="Category Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Category Sport should exist"

        # Создаем соревнование и связываем с категорией
        competition = Competition(name="Competition for Category Deletion", sport=sport, categories=[category])
        session.add(competition)
        await session.commit()

        # Удаляем категорию
        await session.delete(category)
        await session.commit()

        # Проверяем, что соревнование все еще существует
        result = await session.execute(select(Competition).filter_by(name="Competition for Category Deletion"))
        remaining_competition = result.scalars().first()
        assert remaining_competition is not None, "Competition should not be deleted when category is deleted"

        # Проверяем, что соревнование больше не связано с категорией
        assert len(remaining_competition.categories) == 0, "Competition should no longer have the deleted category"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match_status():
    async with new_session() as session:
        # Создаем статус матча
        status = MatchStatus(name="Delete Status Test")
        session.add(status)
        await session.commit()

        # Получаем существующий спорт
        result = await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Delete Test Sport should exist"

        # Создаем соревнование
        competition = Competition(name="Competition for Status Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        # Создаем матч с этим статусом
        match = Match(match_name="Match with Deletable Status", competition=competition, match_status=status)
        session.add(match)
        await session.commit()

        # Удаляем статус матча
        await session.delete(status)
        await session.commit()

        # Проверяем, что матч все еще существует
        result = await session.execute(select(Match).filter_by(match_name="Match with Deletable Status"))
        remaining_match = result.scalars().first()
        assert remaining_match is not None, "Match should not be deleted when status is deleted"

        # Проверяем, что матч больше не имеет статуса
        assert remaining_match.match_status is None, "Match should no longer have the deleted status"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_substitution():
    async with new_session() as session:
        # Создаем матч, команды и замену
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Test Sport should exist"

        competition = Competition(name="Competition for Substitution Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        team = Team(name="Team for Substitution")
        session.add(team)
        await session.commit()

        status = MatchStatus(name="Substitution Test Status")
        session.add(status)
        await session.commit()

        match = Match(match_name="Match for Substitution Deletion", competition=competition, match_status=status)
        match.match_teams = [team]
        session.add(match)
        await session.commit()

        player_in = TeamMember(nickname="Sub In Player")
        player_out = TeamMember(nickname="Sub Out Player")
        session.add_all([player_in, player_out])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=player_out.player_id,
            new_player_id=player_in.player_id,
            time=30,
            team=team
        )
        session.add(substitution)
        await session.commit()

        # Удаляем замену
        await session.delete(substitution)
        await session.commit()

        # Проверяем, что замена удалена
        result = await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        substitutions = result.scalars().all()
        assert not substitutions, "Substitution should be deleted"

        # Проверяем, что матч и команда все еще существуют
        result = await session.execute(select(Match).filter_by(match_name="Match for Substitution Deletion"))
        remaining_match = result.scalars().first()
        assert remaining_match is not None, "Match should still exist after substitution is deleted"

        result = await session.execute(select(Team).filter_by(name="Team for Substitution"))
        remaining_team = result.scalars().first()
        assert remaining_team is not None, "Team should still exist after substitution is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_ai_statement():
    async with new_session() as session:
        # Создаем матч и AI заявление
        result = await session.execute(select(Sport).filter_by(name="AI Statement Sport"))
        sport = result.scalars().first()
        assert sport is not None, "AI Statement Sport should exist"

        competition = Competition(name="Competition for AI Statement Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name="AI Statement Test Status")
        session.add(status)
        await session.commit()

        match = Match(match_name="Match with AI Statement", competition=competition, match_status=status)
        session.add(match)
        await session.commit()

        ai_statement = MatchAIStatement()
        ai_statement.matches = [match]
        session.add(ai_statement)
        await session.commit()

        # Удаляем AI заявление
        await session.delete(ai_statement)
        await session.commit()

        # Проверяем, что матч все еще существует
        result = await session.execute(select(Match).filter_by(match_name="Match with AI Statement"))
        remaining_match = result.scalars().first()
        assert remaining_match is not None, "Match should still exist after AI statement is deleted"

        # Проверяем, что матч больше не связан с AI заявлением
        assert len(remaining_match.ai_statements) == 0, "Match should no longer have the deleted AI statement"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_team_member():
    async with new_session() as session:
        # Создаем игрока
        member = TeamMember(nickname="Updatable Player", age=25, country="Country A")
        session.add(member)
        await session.commit()

        # Обновляем данные игрока
        member.age = 26
        member.country = "Country B"
        await session.commit()

        # Проверяем, что данные обновлены
        result = await session.execute(select(TeamMember).filter_by(nickname="Updatable Player"))
        updated_member = result.scalars().first()
        assert updated_member.age == 26, "Player's age should be updated to 26"
        assert updated_member.country == "Country B", "Player's country should be updated to Country B"


@pytest.mark.asyncio(loop_scope="session")
async def test_add_remove_team_member_from_team():
    async with new_session() as session:
        # Создаем команду и игроков
        team = Team(name="Dynamic Team")
        member1 = TeamMember(nickname="Dynamic Player 1")
        member2 = TeamMember(nickname="Dynamic Player 2")
        session.add_all([team, member1, member2])
        await session.commit()

        # Добавляем игроков в команду
        team.members.extend([member1, member2])
        await session.commit()

        # Проверяем, что игроки добавлены
        result = await session.execute(select(Team).filter_by(name="Dynamic Team"))
        team = result.scalars().first()
        assert len(team.members) == 2, "Team should have two members"

        # Удаляем одного игрока из команды
        team.members.remove(member1)
        await session.commit()

        # Проверяем, что игрок удален из команды
        assert len(team.members) == 1, "Team should have one member after removal"
        assert member2 in team.members, "Remaining member should be Dynamic Player 2"

        # Проверяем, что удаленный игрок все еще существует
        result = await session.execute(select(TeamMember).filter_by(nickname="Dynamic Player 1"))
        remaining_member = result.scalars().first()
        assert remaining_member is not None, "Removed member should still exist in the database"


@pytest.mark.asyncio(loop_scope="session")
async def test_add_remove_coach_from_team():
    async with new_session() as session:
        # Создаем команду и тренеров
        team = Team(name="Coachable Team")
        coach1 = Coach(name="Coach A")
        coach2 = Coach(name="Coach B")
        session.add_all([team, coach1, coach2])
        await session.commit()

        # Добавляем тренеров в команду
        team.coaches.extend([coach1, coach2])
        await session.commit()

        # Проверяем, что тренеры добавлены
        result = await session.execute(select(Team).filter_by(name="Coachable Team"))
        team = result.scalars().first()
        assert len(team.coaches) == 2, "Team should have two coaches"

        # Удаляем одного тренера из команды
        team.coaches.remove(coach1)
        await session.commit()

        # Проверяем, что тренер удален из команды
        assert len(team.coaches) == 1, "Team should have one coach after removal"
        assert coach2 in team.coaches, "Remaining coach should be Coach B"

        # Проверяем, что удаленный тренер все еще существует
        result = await session.execute(select(Coach).filter_by(name="Coach A"))
        remaining_coach = result.scalars().first()
        assert remaining_coach is not None, "Removed coach should still exist in the database"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_competition_with_matches():
    async with new_session() as session:
        # Получаем существующий спорт
        result = await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Delete Test Sport should exist"

        # Создаем соревнование и матчи
        competition = Competition(name="Competition with Matches", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name="Match Status for Deletion")
        session.add(status)
        await session.commit()

        match1 = Match(match_name="Match 1", competition=competition, match_status=status)
        match2 = Match(match_name="Match 2", competition=competition, match_status=status)
        session.add_all([match1, match2])
        await session.commit()

        # Удаляем соревнование
        await session.delete(competition)
        await session.commit()

        # Проверяем, что соревнование удалено
        result = await session.execute(select(Competition).filter_by(name="Competition with Matches"))
        deleted_competition = result.scalars().first()
        assert deleted_competition is None, "Competition should be deleted"

        # Проверяем, что матчи тоже удалены
        result = await session.execute(select(Match).filter(Match.match_name.in_(["Match 1", "Match 2"])))
        matches = result.scalars().all()
        assert not matches, "Matches should be deleted when competition is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_sport_with_categories():
    async with new_session() as session:
        # Создаем категории соревнований
        category1 = CompetitionCategory(name="Sport Deletion Category 1")
        category2 = CompetitionCategory(name="Sport Deletion Category 2")
        session.add_all([category1, category2])
        await session.commit()

        # Получаем существующий спорт
        result = await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        sport = result.scalars().first()
        assert sport is not None, "Delete Test Sport should exist"

        # Создаем соревнования и связываем с категориями
        competition1 = Competition(name="Competition X", sport=sport, categories=[category1])
        competition2 = Competition(name="Competition Y", sport=sport, categories=[category2])
        session.add_all([competition1, competition2])
        await session.commit()

        # Удаляем спорт
        await session.delete(sport)
        await session.commit()

        # Проверяем, что спорт удален
        result = await session.execute(select(Sport).filter_by(name="Delete Test Sport"))
        deleted_sport = result.scalars().first()
        assert deleted_sport is None, "Sport should be deleted"

        # Проверяем, что соревнования удалены
        result = await session.execute(select(Competition).filter(Competition.name.in_(["Competition X", "Competition Y"])))
        competitions = result.scalars().all()
        assert not competitions, "Competitions should be deleted when sport is deleted"

        # Проверяем, что категории все еще существуют
        result = await session.execute(select(CompetitionCategory).filter(CompetitionCategory.name.in_(["Sport Deletion Category 1", "Sport Deletion Category 2"])))
        categories = result.scalars().all()
        assert len(categories) == 2, "CompetitionCategories should not be deleted when sport is deleted"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_match_status():
    async with new_session() as session:
        # Создаем статус матча
        status = MatchStatus(name="Initial Status")
        session.add(status)
        await session.commit()

        # Создаем матч с этим статусом
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        competition = Competition(name="Competition for Status Update", sport=sport)
        session.add(competition)
        await session.commit()

        match = Match(match_name="Match for Status Update", competition=competition, match_status=status)
        session.add(match)
        await session.commit()

        # Обновляем статус матча
        status.name = "Updated Status"
        await session.commit()

        # Проверяем, что статус обновлен в матче
        result = await session.execute(select(Match).filter_by(match_name="Match for Status Update"))
        updated_match = result.scalars().first()
        assert updated_match.match_status.name == "Updated Status", "MatchStatus should be updated in the match"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_team_in_competition():
    async with new_session() as session:
        # Создаем команду и соревнование
        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        competition = Competition(name="Competition for Team Deletion", sport=sport)
        session.add(competition)
        await session.commit()

        team = Team(name="Team to Delete")
        session.add(team)
        await session.commit()

        # Связываем команду с соревнованием
        competition.teams.append(team)
        await session.commit()

        # Удаляем команду
        await session.delete(team)
        await session.commit()

        # Проверяем, что команда удалена
        result = await session.execute(select(Team).filter_by(name="Team to Delete"))
        deleted_team = result.scalars().first()
        assert deleted_team is None, "Team should be deleted"

        # Проверяем, что соревнование все еще существует
        result = await session.execute(select(Competition).filter_by(name="Competition for Team Deletion"))
        remaining_competition = result.scalars().first()
        assert remaining_competition is not None, "Competition should still exist after team is deleted"

        # Проверяем, что соревнование больше не содержит команду
        assert len(remaining_competition.teams) == 0, "Competition should not have the deleted team"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_player_in_team():
    async with new_session() as session:
        # Создаем команду и игрока
        team = Team(name="Team with Player Deletion")
        member = TeamMember(nickname="Player to Delete")
        session.add_all([team, member])
        await session.commit()

        # Связываем игрока с командой
        team.members.append(member)
        await session.commit()

        # Удаляем игрока
        await session.delete(member)
        await session.commit()

        # Проверяем, что игрок удален
        result = await session.execute(select(TeamMember).filter_by(nickname="Player to Delete"))
        deleted_member = result.scalars().first()
        assert deleted_member is None, "Player should be deleted"

        # Проверяем, что команда все еще существует
        result = await session.execute(select(Team).filter_by(name="Team with Player Deletion"))
        remaining_team = result.scalars().first()
        assert remaining_team is not None, "Team should still exist after player is deleted"

        # Проверяем, что команда больше не содержит игрока
        assert len(remaining_team.members) == 0, "Team should not have the deleted player"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_coach_in_team():
    async with new_session() as session:
        # Создаем команду и тренера
        team = Team(name="Team with Coach Deletion")
        coach = Coach(name="Coach to Delete")
        session.add_all([team, coach])
        await session.commit()

        # Связываем тренера с командой
        team.coaches.append(coach)
        await session.commit()

        # Удаляем тренера
        await session.delete(coach)
        await session.commit()

        # Проверяем, что тренер удален
        result = await session.execute(select(Coach).filter_by(name="Coach to Delete"))
        deleted_coach = result.scalars().first()
        assert deleted_coach is None, "Coach should be deleted"

        # Проверяем, что команда все еще существует
        result = await session.execute(select(Team).filter_by(name="Team with Coach Deletion"))
        remaining_team = result.scalars().first()
        assert remaining_team is not None, "Team should still exist after coach is deleted"

        # Проверяем, что команда больше не содержит тренера
        assert len(remaining_team.coaches) == 0, "Team should not have the deleted coach"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_match_with_ai_statements():
    async with new_session() as session:
        # Создаем матч и AI заявление
        result = await session.execute(select(Sport).filter_by(name="AI Statement Sport"))
        sport = result.scalars().first()
        competition = Competition(name="Competition for Match Deletion with AI", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name="Match Status for AI Deletion")
        session.add(status)
        await session.commit()

        match = Match(match_name="Match to Delete with AI", competition=competition, match_status=status)
        session.add(match)
        await session.commit()

        ai_statement = MatchAIStatement()
        ai_statement.matches = [match]
        session.add(ai_statement)
        await session.commit()

        # Удаляем матч
        await session.delete(match)
        await session.commit()

        # Проверяем, что матч удален
        result = await session.execute(select(Match).filter_by(match_name="Match to Delete with AI"))
        deleted_match = result.scalars().first()
        assert deleted_match is None, "Match should be deleted"

        # Проверяем, что AI заявление больше не связано с матчем
        result = await session.execute(select(MatchAIStatement))
        ai_statements = result.scalars().all()
        for ai_stmt in ai_statements:
            assert match not in ai_stmt.matches, "AI Statement should not reference the deleted match"


@pytest.mark.asyncio(loop_scope="session")
async def test_cascade_delete_team_with_substitutions():
    async with new_session() as session:
        # Создаем команду, матч и замену
        team = Team(name="Team with Substitutions")
        session.add(team)
        await session.commit()

        result = await session.execute(select(Sport).filter_by(name="Test Sport"))
        sport = result.scalars().first()
        competition = Competition(name="Competition for Team Deletion with Substitutions", sport=sport)
        session.add(competition)
        await session.commit()

        status = MatchStatus(name="Status for Team Deletion with Substitutions")
        session.add(status)
        await session.commit()

        match = Match(match_name="Match with Substitutions", competition=competition, match_status=status)
        match.match_teams.append(team)
        session.add(match)
        await session.commit()

        player_in = TeamMember(nickname="Sub Player In")
        player_out = TeamMember(nickname="Sub Player Out")
        session.add_all([player_in, player_out])
        await session.commit()

        substitution = Substitution(
            match=match,
            prev_player_id=player_out.player_id,
            new_player_id=player_in.player_id,
            time=70,
            team=team
        )
        session.add(substitution)
        await session.commit()

        # Удаляем команду
        await session.delete(team)
        await session.commit()

        # Проверяем, что команда удалена
        result = await session.execute(select(Team).filter_by(name="Team with Substitutions"))
        deleted_team = result.scalars().first()
        assert deleted_team is None, "Team should be deleted"

        # Проверяем, что замены тоже удалены
        result = await session.execute(select(Substitution).filter_by(match_id=match.match_id))
        substitutions = result.scalars().all()
        assert not substitutions, "Substitutions should be deleted when team is deleted"

        # Проверяем, что матч все еще существует
        result = await session.execute(select(Match).filter_by(match_name="Match with Substitutions"))
        remaining_match = result.scalars().first()
        assert remaining_match is not None, "Match should still exist after team is deleted"

# Ваши модели остаются без изменений

