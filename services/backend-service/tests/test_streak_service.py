"""
Tests for Streak Service functionality
"""

from datetime import date, timedelta
import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import StreakActivity, User, UserStreak
from services.streak_service import StreakService


class TestStreakService:
    """Test streak service core functionality"""

    @pytest.fixture
    def streak_service(self):
        """Create streak service instance"""
        return StreakService()

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(username="streakuser")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        return user

    def test_record_qualifying_activity(self, streak_service, test_user, db_session):
        """Test recording activities that qualify for streaks"""
        # Test practice session with enough questions
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=10,  # Above MIN_PRACTICE_QUESTIONS (5)
        )

        assert result["success"] is True
        assert result["qualified_for_streak"] is True
        assert "activity" in result
        assert "streak_updates" in result

        # Check activity was recorded
        activity = StreakActivity.query.filter_by(
            user_id=test_user.id, activity_date=date.today()
        ).first()
        assert activity is not None
        assert activity.streak_qualifying is True

    def test_record_non_qualifying_activity(self, streak_service, test_user, db_session):
        """Test recording activities that don't qualify for streaks"""
        # Test practice session with too few questions
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=3,  # Below MIN_PRACTICE_QUESTIONS (5)
        )

        assert result["success"] is True
        assert result["qualified_for_streak"] is False

        activity = StreakActivity.query.filter_by(
            user_id=test_user.id, activity_date=date.today()
        ).first()
        assert activity.streak_qualifying is False

    def test_daily_streak_initialization(self, streak_service, test_user, db_session):
        """Test first-time daily streak creation"""
        result = streak_service.record_activity(
            user_id=test_user.id, activity_type="practice_session", activity_count=10
        )

        assert result["success"] is True

        # Check daily streak was created
        daily_streak = UserStreak.query.filter_by(user_id=test_user.id, streak_type="daily").first()

        assert daily_streak is not None
        assert daily_streak.current_streak == 1
        assert daily_streak.longest_streak == 1
        assert daily_streak.last_activity_date == date.today()

    def test_daily_streak_continuation(self, streak_service, test_user, db_session):
        """Test continuing daily streak on consecutive days"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Record activity yesterday
        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=10,
            activity_date=yesterday,
        )

        # Record activity today
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=8,
            activity_date=today,
        )

        assert result["success"] is True

        daily_streak = UserStreak.query.filter_by(user_id=test_user.id, streak_type="daily").first()

        assert daily_streak.current_streak == 2
        assert daily_streak.longest_streak == 2

    def test_daily_streak_reset(self, streak_service, test_user, db_session):
        """Test daily streak reset when missing a day"""
        today = date.today()
        three_days_ago = today - timedelta(days=3)

        # Record activity 3 days ago
        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="vocabulary_added",
            activity_count=5,
            activity_date=three_days_ago,
        )

        # Record activity today (missed 2 days)
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=10,
            activity_date=today,
        )

        assert result["success"] is True

        daily_streak = UserStreak.query.filter_by(user_id=test_user.id, streak_type="daily").first()

        # Should reset to 1
        assert daily_streak.current_streak == 1
        assert daily_streak.longest_streak == 1  # Previous streak was only 1 day

    def test_vocabulary_addition_streak(self, streak_service, test_user, db_session):
        """Test streak with vocabulary addition activity"""
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="vocabulary_added",
            activity_count=5,  # Above MIN_VOCABULARY_WORDS (3)
        )

        assert result["success"] is True
        assert result["qualified_for_streak"] is True

    def test_multiple_activities_same_day(self, streak_service, test_user, db_session):
        """Test combining multiple activities on same day"""
        today = date.today()

        # First activity - not qualifying
        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=3,  # Below threshold
            activity_date=today,
        )

        # Second activity - should combine and now qualify
        result = streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=4,  # Combined: 3 + 4 = 7, above threshold
            activity_date=today,
        )

        assert result["success"] is True

        # Should be one activity record
        activities = StreakActivity.query.filter_by(user_id=test_user.id, activity_date=today).all()

        assert len(activities) == 1
        # The combined activity count should be 7
        assert activities[0].activity_count == 7
        assert activities[0].streak_qualifying is True

    def test_get_user_streaks(self, streak_service, test_user, db_session):
        """Test getting comprehensive streak information"""
        # Record some activities to create streaks
        today = date.today()
        yesterday = today - timedelta(days=1)

        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=10,
            activity_date=yesterday,
        )

        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=8,
            activity_date=today,
        )

        streaks_data = streak_service.get_user_streaks(test_user.id)

        assert "streaks" in streaks_data
        assert "recent_activities" in streaks_data
        assert "total_activities_today" in streaks_data

        # Check streak types are present
        streaks = streaks_data["streaks"]
        assert "daily" in streaks
        assert "weekly" in streaks
        assert "monthly" in streaks

        # Check daily streak data
        daily_streak = streaks["daily"]
        assert daily_streak["current_streak"] == 2
        assert daily_streak["longest_streak"] == 2
        assert daily_streak["is_active"] is True

    def test_streak_status_checking(self, streak_service, test_user, db_session):
        """Test checking if streaks are still active"""
        # Create a streak from yesterday
        yesterday = date.today() - timedelta(days=1)

        streak_service.record_activity(
            user_id=test_user.id,
            activity_type="practice_session",
            activity_count=10,
            activity_date=yesterday,
        )

        streak = UserStreak.query.filter_by(user_id=test_user.id, streak_type="daily").first()

        # Check status - should still be active (within 1 day grace)
        is_active, days_until_break = streak_service._check_streak_status(streak, date.today())

        assert is_active is True
        assert days_until_break >= 0

    def test_streak_leaderboard(self, streak_service, db_session):
        """Test streak leaderboard generation"""
        # Create users with different streak levels
        users = []
        streak_lengths = [5, 10, 3, 15, 7]

        for i, streak_len in enumerate(streak_lengths):
            user = User(username=f"streakuser{i}")
            user.set_password("password")
            db_session.add(user)
            db_session.flush()
            users.append(user)

            # Create streak record
            user_streak = UserStreak(
                user_id=user.id,
                streak_type="daily",
                current_streak=streak_len,
                longest_streak=streak_len,
                last_activity_date=date.today(),
            )
            db_session.add(user_streak)

        db_session.commit()

        # Get leaderboard
        leaderboard = streak_service.get_streak_leaderboard("daily", limit=5)

        assert len(leaderboard) == 5

        # Should be sorted by current_streak descending
        assert leaderboard[0]["current_streak"] == 15
        assert leaderboard[1]["current_streak"] == 10
        assert leaderboard[2]["current_streak"] == 7

        # Check rank assignment
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[1]["rank"] == 2
        assert leaderboard[2]["rank"] == 3

    def test_practice_session_integration(self, streak_service, test_user, db_session):
        """Test integration method for practice sessions"""
        result = streak_service.record_practice_session(
            user_id=test_user.id, total_questions=12, correct_answers=10
        )

        assert result["success"] is True
        assert result["qualified_for_streak"] is True

        # Check activity record
        activity = StreakActivity.query.filter_by(
            user_id=test_user.id, activity_date=date.today()
        ).first()

        # Since this is the first activity, it should be practice_session
        assert "practice_session" in activity.activity_type
        assert activity.activity_count == 12

    def test_vocabulary_addition_integration(self, streak_service, test_user, db_session):
        """Test integration method for vocabulary additions"""
        # Use a fresh user for this test to avoid activity type conflicts
        fresh_user = User(username="vocabuser")
        fresh_user.set_password("password")
        db_session.add(fresh_user)
        db_session.commit()

        result = streak_service.record_vocabulary_addition(user_id=fresh_user.id, words_added=8)

        assert result["success"] is True
        assert result["qualified_for_streak"] is True

        activity = StreakActivity.query.filter_by(
            user_id=fresh_user.id, activity_date=date.today()
        ).first()

        assert activity.activity_type == "vocabulary_added"
        assert activity.activity_count == 8


class TestStreakProgressCalculation:
    """Test streak progress and milestone calculations"""

    @pytest.fixture
    def streak_service(self):
        return StreakService()

    def test_progress_percentage_calculation(self, streak_service):
        """Test progress percentage towards milestones"""
        # Test progress towards first milestone (7 days)
        progress = streak_service._calculate_progress_percentage(3)
        expected = int((3 / 7) * 100)  # 42%
        assert progress == expected

        # Test progress towards second milestone (14 days)
        progress = streak_service._calculate_progress_percentage(10)
        # Progress from 7-day milestone towards 14-day: (10-7)/(14-7) = 3/7
        expected = int((3 / 7) * 100)  # 42%
        assert progress == expected

        # Test completion of all milestones
        progress = streak_service._calculate_progress_percentage(400)
        assert progress == 100

    def test_previous_period_date_calculation(self, streak_service):
        """Test calculation of previous period dates"""
        test_date = date(2024, 2, 15)

        # Daily - previous day
        prev_daily = streak_service._get_previous_period_date("daily", test_date)
        assert prev_daily == date(2024, 2, 14)

        # Weekly - previous week same day
        prev_weekly = streak_service._get_previous_period_date("weekly", test_date)
        assert prev_weekly == date(2024, 2, 8)

        # Monthly - previous month same day
        prev_monthly = streak_service._get_previous_period_date("monthly", test_date)
        assert prev_monthly == date(2024, 1, 15)

    def test_longest_streak_tracking(self, streak_service, db_session):
        """Test that longest streak is properly tracked"""
        user = User(username="longeststreakuser")
        user.set_password("password")
        db_session.add(user)
        db_session.flush()

        # Build up streak to 5 days
        base_date = date(2024, 1, 1)
        for i in range(5):
            streak_service.record_activity(
                user_id=user.id,
                activity_type="practice_session",
                activity_count=10,
                activity_date=base_date + timedelta(days=i),
            )

        # Check longest streak
        daily_streak = UserStreak.query.filter_by(user_id=user.id, streak_type="daily").first()
        assert daily_streak.longest_streak == 5

        # Break streak and start new one (only 3 days)
        new_base = base_date + timedelta(days=7)  # Skip 2 days
        for i in range(3):
            streak_service.record_activity(
                user_id=user.id,
                activity_type="practice_session",
                activity_count=8,
                activity_date=new_base + timedelta(days=i),
            )

        # Longest streak should still be 5, current should be 3
        daily_streak = UserStreak.query.filter_by(user_id=user.id, streak_type="daily").first()
        assert daily_streak.longest_streak == 5
        assert daily_streak.current_streak == 3
