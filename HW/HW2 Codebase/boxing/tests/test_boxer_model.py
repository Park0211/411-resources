import pytest
from unittest.mock import Mock, patch
import sqlite3
from contextlib import contextmanager

from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    get_weight_class,
    update_boxer_stats
)


#########################################################
#
#   Test Data and Fixtures
#
#########################################################

# Test dummy data
DUMMY_BOXER_1 = Boxer(id=1, name="Mike Tyson", weight=220, height=71, reach=71.0, age=35)
DUMMY_BOXER_2 = Boxer(id=2, name="Floyd Mayweather", weight=147, height=68, reach=72.0, age=30)
DUMMY_BOXER_3 = Boxer(id=3, name="Manny Pacquiao", weight=147, height=66, reach=67.0, age=28)


@pytest.fixture
def mock_cursor(mocker):
    """Mock cursor fixture for testing database operations."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


class TestBoxerModel:
    """Unit tests for the Boxer model class."""

    def test_boxer_initialization(self):
        """Test initialization of a Boxer object."""
        boxer = Boxer(1, "Mike Tyson", 220, 71, 71.0, 35)
        assert boxer.id == 1
        assert boxer.name == "Mike Tyson"
        assert boxer.weight == 220
        assert boxer.height == 71
        assert boxer.reach == 71.0
        assert boxer.age == 35
        assert boxer.weight_class == "HEAVYWEIGHT"

    def test_boxer_weight_class_assignment(self):
        """Test that weight class is correctly assigned based on weight."""
        # Heavyweight
        heavyweight = Boxer(1, "Mike Tyson", 220, 71, 71.0, 35)
        assert heavyweight.weight_class == "HEAVYWEIGHT"

        # Middleweight
        middleweight = Boxer(2, "Canelo Alvarez", 175, 70, 70.5, 32)
        assert middleweight.weight_class == "MIDDLEWEIGHT"

        # Lightweight
        lightweight = Boxer(3, "Gervonta Davis", 135, 66, 67.5, 28)
        assert lightweight.weight_class == "LIGHTWEIGHT"

        # Featherweight
        featherweight = Boxer(4, "Emanuel Navarrete", 126, 65, 66.0, 27)
        assert featherweight.weight_class == "FEATHERWEIGHT"

    def test_invalid_weight(self):
        """Test that an error is raised when weight is too low."""
        with pytest.raises(ValueError, match="Weight must be at least 125"):
            get_weight_class(124)


class TestBoxerCreation:
    """Tests for creating and deleting boxers in the database."""

    def test_create_boxer(self, mock_cursor):
        """Test creating a new boxer in the database."""
        # Setup the mock to return no existing boxer and then the new boxer's ID
        mock_cursor.fetchone.return_value = None

        create_boxer("Mike Tyson", 220, 71, 71.0, 35)

        # Check that the right queries were executed
        # First, check if boxer already exists by name
        assert mock_cursor.execute.call_args_list[0][0][0] == "SELECT 1 FROM boxers WHERE name = ?"
        assert mock_cursor.execute.call_args_list[0][0][1] == ("Mike Tyson",)

        # Then, check the insert query
        insert_query = mock_cursor.execute.call_args_list[1][0][0].strip()
        assert "INSERT INTO boxers" in insert_query
        assert "VALUES" in insert_query
        assert mock_cursor.execute.call_args_list[1][0][1] == ("Mike Tyson", 220, 71, 71.0, 35)

    def test_create_boxer_duplicate(self, mock_cursor):
        """Test creating a boxer with a duplicate name (should raise an error)."""
        # Setup the mock to return an existing boxer
        mock_cursor.fetchone.return_value = (1,)

        with pytest.raises(ValueError, match="Boxer with name 'Mike Tyson' already exists"):
            create_boxer("Mike Tyson", 220, 71, 71.0, 35)

    @patch("boxing.models.boxers_model.get_db_connection")
    def test_create_boxer_integrity_error(self, mock_get_db_connection):
        """Test handling of integrity error when creating a boxer."""
        # Setup the mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        # Make fetchone return None (no existing boxer)
        mock_cursor.fetchone.return_value = None

        # But then raise IntegrityError on insert
        mock_cursor.execute.side_effect = [None, sqlite3.IntegrityError("UNIQUE constraint failed")]

        with pytest.raises(ValueError, match="Boxer with name 'Mike Tyson' already exists"):
            create_boxer("Mike Tyson", 220, 71, 71.0, 35)

    def test_create_boxer_invalid_parameters(self):
        """Test error when trying to create a boxer with invalid parameters."""
        # Invalid weight
        with pytest.raises(ValueError, match="Invalid weight: 100"):
            create_boxer("Mike Tyson", 100, 71, 71.0, 35)

        # Invalid height
        with pytest.raises(ValueError, match="Invalid height: 0"):
            create_boxer("Mike Tyson", 220, 0, 71.0, 35)

        # Invalid reach
        with pytest.raises(ValueError, match="Invalid reach: 0"):
            create_boxer("Mike Tyson", 220, 71, 0, 35)

        # Invalid age (too young)
        with pytest.raises(ValueError, match="Invalid age: 17"):
            create_boxer("Mike Tyson", 220, 71, 71.0, 17)

        # Invalid age (too old)
        with pytest.raises(ValueError, match="Invalid age: 41"):
            create_boxer("Mike Tyson", 220, 71, 71.0, 41)

    def test_delete_boxer(self, mock_cursor):
        """Test deleting a boxer from the database."""
        # Setup the mock to return an existing boxer
        mock_cursor.fetchone.return_value = (1,)

        delete_boxer(1)

        # Check that the right queries were executed
        # First, check if boxer exists by ID
        assert mock_cursor.execute.call_args_list[0][0][0] == "SELECT id FROM boxers WHERE id = ?"
        assert mock_cursor.execute.call_args_list[0][0][1] == (1,)

        # Then, check the delete query
        delete_query = mock_cursor.execute.call_args_list[1][0][0].strip()
        assert "DELETE FROM boxers WHERE id = ?" in delete_query
        assert mock_cursor.execute.call_args_list[1][0][1] == (1,)

    def test_delete_boxer_not_found(self, mock_cursor):
        """Test error when trying to delete a non-existent boxer."""
        # Setup the mock to return no existing boxer
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
            delete_boxer(999)


class TestBoxerRetrieval:
    """Tests for retrieving boxers from the database."""

    def test_get_boxer_by_id(self, mock_cursor):
        """Test getting a boxer by ID."""
        # Setup the mock to return a boxer
        mock_cursor.fetchone.return_value = (1, "Mike Tyson", 220, 71, 71.0, 35)

        boxer = get_boxer_by_id(1)

        # Check that the right query was executed
        assert mock_cursor.execute.call_args[0][0].strip().startswith("SELECT id, name, weight, height, reach, age")
        assert mock_cursor.execute.call_args[0][1] == (1,)

        # Check that the boxer was returned correctly
        assert boxer.id == 1
        assert boxer.name == "Mike Tyson"
        assert boxer.weight == 220
        assert boxer.height == 71
        assert boxer.reach == 71.0
        assert boxer.age == 35
        assert boxer.weight_class == "HEAVYWEIGHT"

    def test_get_boxer_by_id_not_found(self, mock_cursor):
        """Test error when getting a non-existent boxer by ID."""
        # Setup the mock to return no boxer
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
            get_boxer_by_id(999)

    def test_get_boxer_by_name(self, mock_cursor):
        """Test getting a boxer by name."""
        # Setup the mock to return a boxer
        mock_cursor.fetchone.return_value = (1, "Mike Tyson", 220, 71, 71.0, 35)

        boxer = get_boxer_by_name("Mike Tyson")

        # Check that the right query was executed
        assert mock_cursor.execute.call_args[0][0].strip().startswith("SELECT id, name, weight, height, reach, age")
        assert mock_cursor.execute.call_args[0][1] == ("Mike Tyson",)

        # Check that the boxer was returned correctly
        assert boxer.id == 1
        assert boxer.name == "Mike Tyson"
        assert boxer.weight == 220
        assert boxer.height == 71
        assert boxer.reach == 71.0
        assert boxer.age == 35
        assert boxer.weight_class == "HEAVYWEIGHT"

    def test_get_boxer_by_name_not_found(self, mock_cursor):
        """Test error when getting a non-existent boxer by name."""
        # Setup the mock to return no boxer
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Boxer 'Unknown Boxer' not found"):
            get_boxer_by_name("Unknown Boxer")

    def test_get_leaderboard(self, mock_cursor):
        """Test retrieving the leaderboard."""
        # Setup the mock to return some boxers
        mock_cursor.fetchall.return_value = [
            (1, "Mike Tyson", 220, 71, 71.0, 35, 50, 44, 0.88),
            (2, "Floyd Mayweather", 147, 68, 72.0, 30, 50, 50, 1.0),
            (3, "Manny Pacquiao", 147, 66, 67.0, 28, 70, 62, 0.89)
        ]

        leaderboard = get_leaderboard()

        # Check that the right query was executed
        assert mock_cursor.execute.call_args[0][0].strip().startswith("SELECT id, name, weight, height, reach, age, fights, wins")
        
        # Check the leaderboard contents
        assert len(leaderboard) == 3
        assert leaderboard[0]['name'] == "Mike Tyson"
        assert leaderboard[1]['name'] == "Floyd Mayweather"
        assert leaderboard[2]['name'] == "Manny Pacquiao"
        
        # Check that the win percentage is calculated correctly
        assert leaderboard[0]['win_pct'] == 88.0
        assert leaderboard[1]['win_pct'] == 100.0
        assert leaderboard[2]['win_pct'] == 88.9

    def test_get_leaderboard_sorted_by_win_pct(self, mock_cursor):
        """Test retrieving the leaderboard sorted by win percentage."""
        # Setup the mock to return some boxers
        mock_cursor.fetchall.return_value = [
            (2, "Floyd Mayweather", 147, 68, 72.0, 30, 50, 50, 1.0),
            (3, "Manny Pacquiao", 147, 66, 67.0, 28, 70, 62, 0.89),
            (1, "Mike Tyson", 220, 71, 71.0, 35, 50, 44, 0.88)
        ]

        leaderboard = get_leaderboard(sort_by="win_pct")

        # Check that the right query was executed with the correct sort order
        query = mock_cursor.execute.call_args[0][0].strip()
        assert "ORDER BY win_pct DESC" in query

        # Check the leaderboard order
        assert leaderboard[0]['name'] == "Floyd Mayweather"
        assert leaderboard[1]['name'] == "Manny Pacquiao"
        assert leaderboard[2]['name'] == "Mike Tyson"

    def test_get_leaderboard_invalid_sort(self, mock_cursor):
        """Test error when using an invalid sort parameter."""
        with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
            get_leaderboard(sort_by="invalid_sort")

    def test_update_boxer_stats(self, mock_cursor):
        """Test updating a boxer's stats."""
        # Setup the mock to return an existing boxer
        mock_cursor.fetchone.return_value = (1,)

        # Test updating with a win
        update_boxer_stats(1, "win")

        # Check that the right query was executed
        win_query = mock_cursor.execute.call_args_list[1][0][0].strip()
        assert "UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?" in win_query
        assert mock_cursor.execute.call_args_list[1][0][1] == (1,)

        # Test updating with a loss
        update_boxer_stats(1, "loss")

        # Check that the right query was executed
        loss_query = mock_cursor.execute.call_args_list[3][0][0].strip()
        assert "UPDATE boxers SET fights = fights + 1 WHERE id = ?" in loss_query
        assert mock_cursor.execute.call_args_list[3][0][1] == (1,)

    def test_update_boxer_stats_invalid_result(self):
        """Test error when using an invalid result parameter."""
        with pytest.raises(ValueError, match="Invalid result: invalid_result"):
            update_boxer_stats(1, "invalid_result")

    def test_update_boxer_stats_boxer_not_found(self, mock_cursor):
        """Test error when updating stats for a non-existent boxer."""
        # Setup the mock to return no existing boxer
        mock_cursor.fetchone.return_value = None

        with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
            update_boxer_stats(999, "win")


class TestBoxerModelSmoke:
    """Smoke tests for Boxer model functionality."""

    @patch('boxing.models.boxers_model.get_db_connection')
    def test_basic_boxer_operations(self, mock_get_db_connection):
        """Test basic boxer operations: create, get, update stats."""
        # Setup the mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn

        # Setup mock responses for a series of operations
        # 1. Check if boxer exists when creating (it doesn't)
        # 2. Get boxer by ID
        # 3. Check if boxer exists when updating stats
        # 4. Get leaderboard
        mock_cursor.fetchone.side_effect = [
            None,  # No boxer exists with this name
            (1, "Mike Tyson", 220, 71, 71.0, 35),  # get_boxer_by_id result
            (1,),  # Boxer exists when updating stats
        ]
        
        mock_cursor.fetchall.return_value = [
            (1, "Mike Tyson", 220, 71, 71.0, 35, 1, 1, 1.0),
        ]

        # 1. Create a boxer
        create_boxer("Mike Tyson", 220, 71, 71.0, 35)
        
        # Reset mock for clean slate in the next test
        mock_cursor.reset_mock()
        mock_cursor.fetchone.side_effect = [
            (1, "Mike Tyson", 220, 71, 71.0, 35),  # get_boxer_by_id result
        ]
        
        # 2. Get the boxer
        boxer = get_boxer_by_id(1)
        assert boxer.name == "Mike Tyson"
        assert boxer.weight_class == "HEAVYWEIGHT"
        
        # Reset mock for clean slate in the next test
        mock_cursor.reset_mock()
        mock_cursor.fetchone.side_effect = [
            (1,),  # Boxer exists when updating stats
        ]
        
        # 3. Update the boxer's stats
        update_boxer_stats(1, "win")
        
        # Reset mock for clean slate in the next test
        mock_cursor.reset_mock()
        mock_cursor.fetchall.return_value = [
            (1, "Mike Tyson", 220, 71, 71.0, 35, 1, 1, 1.0),
        ]
        
        # 4. Get the leaderboard
        leaderboard = get_leaderboard()
        assert len(leaderboard) == 1
        assert leaderboard[0]['name'] == "Mike Tyson"
        assert leaderboard[0]['win_pct'] == 100.0 