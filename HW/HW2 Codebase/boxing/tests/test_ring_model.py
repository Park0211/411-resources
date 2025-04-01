import pytest
from unittest.mock import patch, Mock
import math

from boxing.models.ring_model import RingModel
from boxing.models.boxers_model import Boxer


# Test data for use in test cases
BOXER_1 = Boxer(id=1, name="Mike Tyson", weight=220, height=71, reach=71.0, age=35)
BOXER_2 = Boxer(id=2, name="Floyd Mayweather", weight=147, height=68, reach=72.0, age=30)
YOUNG_BOXER = Boxer(id=3, name="Young Fighter", weight=160, height=70, reach=70.0, age=22)
OLD_BOXER = Boxer(id=4, name="Veteran Fighter", weight=180, height=72, reach=74.0, age=38)


@pytest.fixture
def empty_ring():
    """Fixture for an empty ring."""
    return RingModel()


@pytest.fixture
def ring_with_one_boxer():
    """Fixture for a ring with one boxer."""
    ring = RingModel()
    ring.enter_ring(BOXER_1)
    return ring


@pytest.fixture
def ring_with_two_boxers():
    """Fixture for a ring with two boxers."""
    ring = RingModel()
    ring.enter_ring(BOXER_1)
    ring.enter_ring(BOXER_2)
    return ring


class TestRingModelInitialization:
    """Unit tests for RingModel initialization."""

    def test_init_creates_empty_ring(self):
        """Test that initialization creates an empty ring."""
        ring = RingModel()
        assert ring.ring == []
        assert len(ring.ring) == 0


class TestRingOperations:
    """Unit tests for basic ring operations like enter_ring, clear_ring, and get_boxers."""

    def test_enter_ring_adds_boxer(self, empty_ring):
        """Test that enter_ring adds a boxer to the ring."""
        empty_ring.enter_ring(BOXER_1)
        assert len(empty_ring.ring) == 1
        assert empty_ring.ring[0] == BOXER_1
    
    def test_enter_ring_adds_second_boxer(self, ring_with_one_boxer):
        """Test that enter_ring can add a second boxer."""
        ring_with_one_boxer.enter_ring(BOXER_2)
        assert len(ring_with_one_boxer.ring) == 2
        assert ring_with_one_boxer.ring[0] == BOXER_1
        assert ring_with_one_boxer.ring[1] == BOXER_2
    
    def test_enter_ring_rejects_third_boxer(self, ring_with_two_boxers):
        """Test that enter_ring rejects a third boxer."""
        with pytest.raises(ValueError, match="Ring is full"):
            ring_with_two_boxers.enter_ring(YOUNG_BOXER)
    
    def test_enter_ring_validates_boxer_type(self, empty_ring):
        """Test that enter_ring validates that the argument is a Boxer."""
        with pytest.raises(TypeError, match="Invalid type: Expected 'Boxer'"):
            empty_ring.enter_ring("Not a boxer")
    
    def test_clear_ring_empties_ring(self, ring_with_two_boxers):
        """Test that clear_ring removes all boxers."""
        ring_with_two_boxers.clear_ring()
        assert len(ring_with_two_boxers.ring) == 0
    
    def test_clear_empty_ring_does_nothing(self, empty_ring):
        """Test that clear_ring on an empty ring doesn't cause errors."""
        empty_ring.clear_ring()  # Should not raise any exception
        assert len(empty_ring.ring) == 0
    
    def test_get_boxers_returns_all_boxers(self, ring_with_two_boxers):
        """Test that get_boxers returns all boxers in the ring."""
        boxers = ring_with_two_boxers.get_boxers()
        assert len(boxers) == 2
        assert BOXER_1 in boxers
        assert BOXER_2 in boxers
    
    def test_get_boxers_from_empty_ring_returns_empty_list(self, empty_ring):
        """Test that get_boxers returns an empty list for an empty ring."""
        boxers = empty_ring.get_boxers()
        assert boxers == []


class TestFightingSkill:
    """Unit tests for the get_fighting_skill method."""

    def test_get_fighting_skill_calculates_correctly(self, empty_ring):
        """Test that get_fighting_skill calculates the skill correctly."""
        # For "Mike Tyson": (220 * 10) + (71.0 / 10) + 0 = 2200 + 7.1 + 0 = 2207.1
        skill = empty_ring.get_fighting_skill(BOXER_1)
        expected_skill = (220 * len("Mike Tyson")) + (71.0 / 10) + 0
        assert skill == expected_skill
    
    def test_get_fighting_skill_applies_age_modifier_for_young(self, empty_ring):
        """Test that get_fighting_skill applies age modifier for young boxers."""
        # Young boxer (age < 25) gets -1 modifier
        skill = empty_ring.get_fighting_skill(YOUNG_BOXER)
        expected_skill = (160 * len("Young Fighter")) + (70.0 / 10) + (-1)
        assert skill == expected_skill
    
    def test_get_fighting_skill_applies_age_modifier_for_old(self, empty_ring):
        """Test that get_fighting_skill applies age modifier for old boxers."""
        # Old boxer (age > 35) gets -2 modifier
        skill = empty_ring.get_fighting_skill(OLD_BOXER)
        expected_skill = (180 * len("Veteran Fighter")) + (74.0 / 10) + (-2)
        assert skill == expected_skill


class TestFight:
    """Unit tests for the fight method."""

    def test_fight_raises_error_if_not_enough_boxers(self, empty_ring, ring_with_one_boxer):
        """Test that fight raises an error if there are not enough boxers."""
        with pytest.raises(ValueError, match="There must be two boxers to start a fight"):
            empty_ring.fight()
        
        with pytest.raises(ValueError, match="There must be two boxers to start a fight"):
            ring_with_one_boxer.fight()
    
    @patch('boxing.models.ring_model.get_random')
    @patch('boxing.models.ring_model.update_boxer_stats')
    def test_fight_boxer1_wins(self, mock_update_stats, mock_get_random, ring_with_two_boxers):
        """Test a fight where boxer 1 wins."""
        # Make sure the random number is such that boxer 1 wins
        # If normalized_delta is 0.7 and random_number is 0.5, boxer 1 should win
        mock_get_random.return_value = 0.5
        
        # Call the fight method
        winner = ring_with_two_boxers.fight()
        
        # Check the winner
        assert winner == "Mike Tyson"
        
        # Check that update_boxer_stats was called correctly
        assert mock_update_stats.call_count == 2
        mock_update_stats.assert_any_call(1, "win")  # Boxer 1 won
        mock_update_stats.assert_any_call(2, "loss")  # Boxer 2 lost
        
        # Check that the ring is cleared
        assert len(ring_with_two_boxers.ring) == 0
    
    @patch('boxing.models.ring_model.get_random')
    @patch('boxing.models.ring_model.update_boxer_stats')
    def test_fight_boxer2_wins(self, mock_update_stats, mock_get_random, ring_with_two_boxers):
        """Test a fight where boxer 2 wins."""
        # Make sure the random number is such that boxer 2 wins
        # If normalized_delta is 0.7 and random_number is 0.8, boxer 2 should win
        mock_get_random.return_value = 0.8
        
        # Call the fight method
        winner = ring_with_two_boxers.fight()
        
        # Check the winner
        assert winner == "Floyd Mayweather"
        
        # Check that update_boxer_stats was called correctly
        assert mock_update_stats.call_count == 2
        mock_update_stats.assert_any_call(2, "win")  # Boxer 2 won
        mock_update_stats.assert_any_call(1, "loss")  # Boxer 1 lost
        
        # Check that the ring is cleared
        assert len(ring_with_two_boxers.ring) == 0
    
    def test_normalized_delta_calculation(self):
        """Test that the normalized delta is calculated correctly."""
        # This test verifies the mathematical formula used in the fight method
        # delta = 100
        # normalized_delta = 1 / (1 + e^(-delta)) should be close to 1
        normalized_delta = 1 / (1 + math.e ** (-100))
        assert normalized_delta > 0.99999
        
        # delta = -100
        # normalized_delta = 1 / (1 + e^(-delta)) should be close to 0
        normalized_delta = 1 / (1 + math.e ** (100))
        assert normalized_delta < 0.00001
        
        # delta = 0
        # normalized_delta = 1 / (1 + e^(-delta)) should be 0.5
        normalized_delta = 1 / (1 + math.e ** (0))
        assert normalized_delta == 0.5


class TestRingModelIntegration:
    """Integration tests for the RingModel."""
    
    @patch('boxing.models.ring_model.update_boxer_stats')
    @patch('boxing.models.ring_model.get_random')
    def test_full_fight_workflow(self, mock_get_random, mock_update_stats):
        """Test the full workflow of creating a ring, adding boxers, and having them fight."""
        # Setup
        ring = RingModel()
        mock_get_random.return_value = 0.4  # Boxer 1 should win
        
        # Execute
        ring.enter_ring(BOXER_1)
        ring.enter_ring(BOXER_2)
        winner = ring.fight()
        
        # Verify
        assert winner == "Mike Tyson"
        assert mock_update_stats.call_count == 2
        mock_update_stats.assert_any_call(1, "win")
        mock_update_stats.assert_any_call(2, "loss")
        assert len(ring.ring) == 0


class TestRingModelSmoke:
    """Smoke tests for the RingModel."""
    
    @patch('boxing.models.ring_model.update_boxer_stats')
    @patch('boxing.models.ring_model.get_random')
    def test_smoke_test(self, mock_get_random, mock_update_stats):
        """Basic smoke test to verify the RingModel works as expected."""
        # Setup
        ring = RingModel()
        mock_get_random.return_value = 0.2
        mock_update_stats.return_value = None
        
        # 1. Create ring
        assert len(ring.ring) == 0
        
        # 2. Add boxers
        ring.enter_ring(BOXER_1)
        ring.enter_ring(BOXER_2)
        assert len(ring.ring) == 2
        
        # 3. Have them fight
        winner = ring.fight()
        assert winner in ["Mike Tyson", "Floyd Mayweather"]
        
        # 4. Verify ring is cleared after fight
        assert len(ring.ring) == 0 