"""
Streak Service for handling daily/weekly/monthly streak tracking and calculations.
Provides functionality for updating streaks based on user activities.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker
from models import db, UserStreak, StreakActivity, User
import logging

logger = logging.getLogger(__name__)


class StreakService:
    """Service for managing user streaks and activities"""

    STREAK_TYPES = ["daily", "weekly", "monthly"]
    QUALIFYING_ACTIVITIES = ["practice_session", "vocabulary_added"]

    # Minimum requirements for streak qualification
    MIN_PRACTICE_QUESTIONS = 5  # Minimum questions in a practice session
    MIN_VOCABULARY_WORDS = 3  # Minimum words added

    def __init__(self):
        """Initialize streak service"""
        pass

    def record_activity(
        self,
        user_id: int,
        activity_type: str,
        activity_count: int = 1,
        activity_date: Optional[date] = None,
    ) -> Dict:
        """
        Record a user activity and update streaks accordingly

        Args:
            user_id: User ID
            activity_type: Type of activity ('practice_session', 'vocabulary_added', 'login')
            activity_count: Number of activities (e.g., questions answered, words added)
            activity_date: Date of activity (defaults to today)

        Returns:
            Dict with streak updates and activity info
        """
        try:
            if activity_date is None:
                activity_date = date.today()

            # Check if this activity qualifies for streak
            streak_qualifying = self._is_qualifying_activity(
                activity_type, activity_count
            )

            # Get or create today's activity record
            existing_activity = StreakActivity.query.filter_by(
                user_id=user_id, activity_date=activity_date
            ).first()

            if existing_activity:
                # Update existing activity
                existing_activity.activity_count += activity_count

                # Handle activity type properly - don't concatenate if it's the same type
                existing_types = existing_activity.activity_type.split(",")
                if activity_type not in existing_types:
                    existing_activity.activity_type += f",{activity_type}"

                # Re-check if it now qualifies for streak using the primary activity type
                primary_activity_type = existing_types[
                    0
                ]  # Use first (primary) activity type
                existing_activity.streak_qualifying = self._is_qualifying_activity(
                    primary_activity_type, existing_activity.activity_count
                )

                activity_record = existing_activity
            else:
                # Create new activity record
                activity_record = StreakActivity(
                    user_id=user_id,
                    activity_date=activity_date,
                    activity_type=activity_type,
                    activity_count=activity_count,
                    streak_qualifying=streak_qualifying,
                )
                db.session.add(activity_record)

            db.session.flush()

            # Update streaks if activity qualifies
            streak_updates = {}
            if activity_record.streak_qualifying:
                streak_updates = self._update_all_streaks(user_id, activity_date)

            db.session.commit()

            return {
                "success": True,
                "activity": activity_record.to_dict(),
                "streak_updates": streak_updates,
                "qualified_for_streak": activity_record.streak_qualifying,
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error recording activity for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    def _is_qualifying_activity(self, activity_type: str, activity_count: int) -> bool:
        """Check if an activity qualifies for streak maintenance"""
        if (
            "practice_session" in activity_type
            and activity_count >= self.MIN_PRACTICE_QUESTIONS
        ):
            return True
        if (
            "vocabulary_added" in activity_type
            and activity_count >= self.MIN_VOCABULARY_WORDS
        ):
            return True
        return False

    def _update_all_streaks(self, user_id: int, activity_date: date) -> Dict:
        """Update all streak types for a user"""
        updates = {}

        for streak_type in self.STREAK_TYPES:
            update = self._update_streak(user_id, streak_type, activity_date)
            if update:
                updates[streak_type] = update

        return updates

    def _update_streak(
        self, user_id: int, streak_type: str, activity_date: date
    ) -> Optional[Dict]:
        """Update a specific streak type for a user"""
        try:
            # Get or create streak record
            streak = UserStreak.query.filter_by(
                user_id=user_id, streak_type=streak_type
            ).first()

            if not streak:
                streak = UserStreak(
                    user_id=user_id,
                    streak_type=streak_type,
                    current_streak=0,
                    longest_streak=0,
                )
                db.session.add(streak)

            # Calculate expected previous activity date
            expected_prev_date = self._get_previous_period_date(
                streak_type, activity_date
            )

            # Check if streak should continue or reset
            if streak.last_activity_date is None:
                # First activity ever
                streak.current_streak = 1
            elif streak.last_activity_date == activity_date:
                # Same day/period - no change needed
                return None
            elif streak.last_activity_date == expected_prev_date:
                # Consecutive period - increment streak
                streak.current_streak += 1
            elif streak.last_activity_date < expected_prev_date:
                # Missed period(s) - reset streak
                streak.current_streak = 1
            else:
                # Future date activity (shouldn't happen normally)
                logger.warning(
                    f"Future date activity detected: {activity_date} vs {streak.last_activity_date}"
                )
                return None

            # Update last activity date
            streak.last_activity_date = activity_date

            # Update longest streak if current is longer
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

            return {
                "streak_type": streak_type,
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "is_new_record": streak.current_streak == streak.longest_streak,
            }

        except Exception as e:
            logger.error(f"Error updating {streak_type} streak for user {user_id}: {e}")
            return None

    def _get_previous_period_date(self, streak_type: str, current_date: date) -> date:
        """Get the expected previous period date for streak calculation"""
        if streak_type == "daily":
            return current_date - timedelta(days=1)
        elif streak_type == "weekly":
            # Previous week (same day of week)
            return current_date - timedelta(weeks=1)
        elif streak_type == "monthly":
            # Previous month (same day)
            if current_date.month == 1:
                return current_date.replace(year=current_date.year - 1, month=12)
            else:
                try:
                    return current_date.replace(month=current_date.month - 1)
                except ValueError:
                    # Handle case where previous month has fewer days (e.g., Mar 31 -> Feb 28)
                    return current_date.replace(month=current_date.month - 1, day=28)
        else:
            raise ValueError(f"Invalid streak type: {streak_type}")

    def get_user_streaks(self, user_id: int) -> Dict:
        """Get all streaks for a user with progress information"""
        try:
            streaks = UserStreak.query.filter_by(user_id=user_id).all()

            # Create a dict with all streak types, defaulting to 0
            streak_data = {}
            for streak_type in self.STREAK_TYPES:
                streak_data[streak_type] = {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_activity_date": None,
                    "is_active": False,
                    "days_until_break": 0,
                    "progress_percentage": 0,
                }

            # Fill in actual data
            today = date.today()
            for streak in streaks:
                streak_info = streak.to_dict()
                streak_type = streak.streak_type

                # Check if streak is still active
                is_active, days_until_break = self._check_streak_status(streak, today)

                # Calculate progress percentage (towards next milestone)
                progress_percentage = self._calculate_progress_percentage(
                    streak.current_streak
                )

                streak_data[streak_type] = {
                    **streak_info,
                    "is_active": is_active,
                    "days_until_break": days_until_break,
                    "progress_percentage": progress_percentage,
                }

            # Get recent activity summary
            recent_activities = self._get_recent_activities(user_id, days=7)

            return {
                "streaks": streak_data,
                "recent_activities": recent_activities,
                "total_activities_today": self._get_today_activity_count(user_id),
                "streak_freeze_available": False,  # Feature for future implementation
            }

        except Exception as e:
            logger.error(f"Error getting streaks for user {user_id}: {e}")
            return {"error": str(e)}

    def _check_streak_status(
        self, streak: UserStreak, current_date: date
    ) -> Tuple[bool, int]:
        """Check if a streak is still active and days until it breaks"""
        if not streak.last_activity_date:
            return False, 0

        if streak.streak_type == "daily":
            days_since = (current_date - streak.last_activity_date).days
            if days_since <= 1:
                return True, 1 - days_since
            else:
                return False, 0
        elif streak.streak_type == "weekly":
            weeks_since = (current_date - streak.last_activity_date).days // 7
            if weeks_since <= 1:
                days_in_week = (current_date - streak.last_activity_date).days
                return True, 7 - days_in_week
            else:
                return False, 0
        elif streak.streak_type == "monthly":
            # Simplified monthly check
            months_diff = (current_date.year - streak.last_activity_date.year) * 12 + (
                current_date.month - streak.last_activity_date.month
            )
            if months_diff <= 1:
                return True, 30  # Simplified
            else:
                return False, 0

        return False, 0

    def _calculate_progress_percentage(self, current_streak: int) -> int:
        """Calculate progress percentage towards next milestone"""
        milestones = [7, 14, 30, 60, 100, 365]  # Common streak milestones

        for milestone in milestones:
            if current_streak < milestone:
                if milestone == 7:  # First milestone
                    return int((current_streak / milestone) * 100)
                else:
                    # Find previous milestone
                    prev_milestone = 0
                    for m in milestones:
                        if m < milestone:
                            prev_milestone = m
                        else:
                            break

                    progress_in_range = current_streak - prev_milestone
                    range_size = milestone - prev_milestone
                    return int((progress_in_range / range_size) * 100)

        # Beyond all milestones
        return 100

    def _get_recent_activities(self, user_id: int, days: int = 7) -> List[Dict]:
        """Get recent activities for a user"""
        cutoff_date = date.today() - timedelta(days=days)

        activities = (
            StreakActivity.query.filter(
                and_(
                    StreakActivity.user_id == user_id,
                    StreakActivity.activity_date >= cutoff_date,
                )
            )
            .order_by(StreakActivity.activity_date.desc())
            .all()
        )

        return [activity.to_dict() for activity in activities]

    def _get_today_activity_count(self, user_id: int) -> int:
        """Get total activity count for today"""
        today = date.today()
        activity = StreakActivity.query.filter_by(
            user_id=user_id, activity_date=today
        ).first()

        return activity.activity_count if activity else 0

    def get_streak_leaderboard(
        self, streak_type: str = "daily", limit: int = 10
    ) -> List[Dict]:
        """Get leaderboard for a specific streak type"""
        try:
            top_streaks = (
                db.session.query(
                    UserStreak.user_id,
                    UserStreak.current_streak,
                    UserStreak.longest_streak,
                    User.username,
                )
                .join(User)
                .filter(UserStreak.streak_type == streak_type)
                .order_by(UserStreak.current_streak.desc())
                .limit(limit)
                .all()
            )

            leaderboard = []
            for rank, (user_id, current_streak, longest_streak, username) in enumerate(
                top_streaks, 1
            ):
                leaderboard.append(
                    {
                        "rank": rank,
                        "user_id": user_id,
                        "username": username,
                        "current_streak": current_streak,
                        "longest_streak": longest_streak,
                    }
                )

            return leaderboard

        except Exception as e:
            logger.error(f"Error getting leaderboard for {streak_type}: {e}")
            return []

    def record_practice_session(
        self,
        user_id: int,
        total_questions: int,
        correct_answers: int,
        session_date: Optional[date] = None,
    ) -> Dict:
        """Record a practice session for streak tracking"""
        return self.record_activity(
            user_id=user_id,
            activity_type="practice_session",
            activity_count=total_questions,
            activity_date=session_date,
        )

    def record_vocabulary_addition(
        self, user_id: int, words_added: int, addition_date: Optional[date] = None
    ) -> Dict:
        """Record vocabulary addition for streak tracking"""
        return self.record_activity(
            user_id=user_id,
            activity_type="vocabulary_added",
            activity_count=words_added,
            activity_date=addition_date,
        )

    def check_and_reset_broken_streaks(self) -> Dict:
        """Check all streaks and reset broken ones (run as background task)"""
        try:
            today = date.today()
            reset_count = 0

            # Get all active streaks
            active_streaks = UserStreak.query.filter(
                UserStreak.current_streak > 0
            ).all()

            for streak in active_streaks:
                is_active, _ = self._check_streak_status(streak, today)

                if not is_active and streak.current_streak > 0:
                    streak.current_streak = 0
                    reset_count += 1

            db.session.commit()

            return {
                "success": True,
                "reset_count": reset_count,
                "checked_streaks": len(active_streaks),
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error checking broken streaks: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
streak_service = StreakService()
