"""
XP Service for handling experience points, levels, and achievement system.
Provides functionality for XP calculation, level progression, and achievement unlocking.
"""

from datetime import date, datetime, timedelta
import logging
from typing import Optional

from sqlalchemy import and_, func

from models import (
    Achievement,
    PracticeSession,
    User,
    UserAchievement,
    UserStreak,
    UserVocabulary,
    UserXP,
    Word,
    XPActivity,
    db,
)

logger = logging.getLogger(__name__)


class XPService:
    """Service for managing user XP, levels, and achievements"""

    # XP values for different activities
    XP_VALUES = {
        "vocabulary_added": 10,  # Per word added
        "practice_correct": 5,  # Per correct answer
        "practice_session_complete": 25,  # Base XP for completing session
        "practice_perfect_session": 50,  # Bonus for 100% accuracy
        "daily_streak": 20,  # Per day of streak maintained
        "weekly_streak": 100,  # Bonus for weekly streaks
        "monthly_streak": 500,  # Bonus for monthly streaks
        "achievement_unlock": 0,  # Variable based on achievement
        "level_up": 100,  # Bonus XP for leveling up
        "mastery_milestone": 15,  # Per word reaching mastery thresholds
    }

    # Level progression formula parameters
    BASE_XP = 100  # XP required for level 2
    XP_MULTIPLIER = 1.5  # Exponential growth factor

    def __init__(self):
        """Initialize XP service"""
        pass

    def get_or_create_user_xp(self, user_id: int) -> UserXP:
        """Get or create UserXP record for a user"""
        user_xp = UserXP.query.filter_by(user_id=user_id).first()

        if not user_xp:
            user_xp = UserXP(user_id=user_id)
            db.session.add(user_xp)
            db.session.flush()

        return user_xp

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate total XP required to reach a specific level"""
        if level <= 1:
            return 0

        total_xp = 0
        for l in range(2, level + 1):
            level_xp = int(self.BASE_XP * (self.XP_MULTIPLIER ** (l - 2)))
            total_xp += level_xp

        return total_xp

    def calculate_level_from_xp(self, total_xp: int) -> tuple[int, int]:
        """Calculate current level and XP to next level from total XP"""
        if total_xp < self.BASE_XP:
            return 1, self.BASE_XP - total_xp

        current_level = 1
        cumulative_xp = 0

        while True:
            next_level_xp = int(
                self.BASE_XP * (self.XP_MULTIPLIER ** (current_level - 1))
            )
            if cumulative_xp + next_level_xp > total_xp:
                xp_to_next = (cumulative_xp + next_level_xp) - total_xp
                return current_level, xp_to_next

            cumulative_xp += next_level_xp
            current_level += 1

            # Safety check to prevent infinite loop
            if current_level > 100:
                return 100, 0

    def award_xp(
        self,
        user_id: int,
        activity_type: str,
        xp_amount: int = None,
        activity_details: dict = None,
        activity_date: Optional[date] = None,
    ) -> dict:
        """
        Award XP to a user for an activity

        Args:
            user_id: User ID
            activity_type: Type of activity
            xp_amount: Custom XP amount (if None, uses default for activity type)
            activity_details: Additional details about the activity
            activity_date: Date of activity (defaults to today)

        Returns:
            Dict with XP award results and any level ups
        """
        try:
            if activity_date is None:
                activity_date = date.today()

            # Calculate XP amount if not specified
            if xp_amount is None:
                xp_amount = self.XP_VALUES.get(activity_type, 0)

            if xp_amount <= 0:
                return {"success": False, "error": "Invalid XP amount"}

            # Get or create user XP record
            user_xp = self.get_or_create_user_xp(user_id)
            old_level = user_xp.current_level

            # Award XP
            user_xp.current_xp += xp_amount
            user_xp.total_xp += xp_amount

            # Calculate new level
            new_level, xp_to_next = self.calculate_level_from_xp(user_xp.total_xp)
            user_xp.current_level = new_level
            user_xp.xp_to_next_level = xp_to_next

            # Record XP activity
            xp_activity = XPActivity(
                user_id=user_id,
                activity_type=activity_type,
                xp_earned=xp_amount,
                activity_date=activity_date,
                activity_details=activity_details or {},
            )
            db.session.add(xp_activity)

            # Check for level up
            level_up_occurred = new_level > old_level
            level_up_bonus = 0

            if level_up_occurred:
                # Award bonus XP for leveling up
                level_up_bonus = self.XP_VALUES["level_up"] * (new_level - old_level)
                user_xp.total_xp += level_up_bonus

                # Record level up activity
                level_up_activity = XPActivity(
                    user_id=user_id,
                    activity_type="level_up",
                    xp_earned=level_up_bonus,
                    activity_date=activity_date,
                    activity_details={"old_level": old_level, "new_level": new_level},
                )
                db.session.add(level_up_activity)

            db.session.flush()

            # Check for achievement unlocks
            new_achievements = self.check_and_unlock_achievements(user_id)

            db.session.commit()

            return {
                "success": True,
                "xp_awarded": xp_amount,
                "level_up_bonus": level_up_bonus,
                "old_level": old_level,
                "new_level": new_level,
                "level_up_occurred": level_up_occurred,
                "total_xp": user_xp.total_xp,
                "current_xp": user_xp.current_xp,
                "xp_to_next_level": user_xp.xp_to_next_level,
                "new_achievements": new_achievements,
                "activity": xp_activity.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error awarding XP to user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    def check_and_unlock_achievements(self, user_id: int) -> list[dict]:
        """Check and unlock any achievements the user has earned"""
        try:
            # Get all active achievements
            achievements = Achievement.query.filter_by(is_active=True).all()

            # Get user's already unlocked achievements
            unlocked_achievement_ids = set(
                ua.achievement_id
                for ua in UserAchievement.query.filter_by(user_id=user_id).all()
            )

            new_achievements = []

            for achievement in achievements:
                if achievement.id in unlocked_achievement_ids:
                    continue

                # Check if user meets criteria
                if self._check_achievement_criteria(user_id, achievement):
                    # Unlock achievement
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id,
                        progress_data={"unlocked_at": datetime.utcnow().isoformat()},
                    )
                    db.session.add(user_achievement)

                    # Award achievement XP
                    if achievement.xp_reward > 0:
                        self.award_xp(
                            user_id=user_id,
                            activity_type="achievement_unlock",
                            xp_amount=achievement.xp_reward,
                            activity_details={
                                "achievement_key": achievement.achievement_key,
                                "achievement_name": achievement.name,
                            },
                        )

                    new_achievements.append(user_achievement.to_dict())

            return new_achievements

        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {e}")
            return []

    def _check_achievement_criteria(
        self, user_id: int, achievement: Achievement
    ) -> bool:
        """Check if user meets the criteria for a specific achievement"""
        try:
            criteria = achievement.unlock_criteria
            criteria_type = criteria.get("type")

            if criteria_type == "vocabulary_count":
                target = criteria.get("target", 0)
                current_count = UserVocabulary.query.filter_by(user_id=user_id).count()
                return current_count >= target

            elif criteria_type == "session_count":
                target = criteria.get("target", 0)
                current_count = PracticeSession.query.filter(
                    and_(
                        PracticeSession.user_id == user_id,
                        PracticeSession.total_questions > 0,
                    )
                ).count()
                return current_count >= target

            elif criteria_type == "perfect_session":
                required_accuracy = criteria.get("accuracy", 100)
                perfect_sessions = PracticeSession.query.filter(
                    and_(
                        PracticeSession.user_id == user_id,
                        PracticeSession.total_questions > 0,
                        PracticeSession.correct_answers
                        == PracticeSession.total_questions,
                    )
                ).count()
                return perfect_sessions > 0

            elif criteria_type == "streak_days":
                target = criteria.get("target", 0)
                daily_streak = UserStreak.query.filter(
                    and_(
                        UserStreak.user_id == user_id, UserStreak.streak_type == "daily"
                    )
                ).first()
                current_streak = daily_streak.current_streak if daily_streak else 0
                return current_streak >= target

            elif criteria_type == "level_reached":
                target = criteria.get("target", 0)
                user_xp = UserXP.query.filter_by(user_id=user_id).first()
                current_level = user_xp.current_level if user_xp else 1
                return current_level >= target

            elif criteria_type == "categories_mastered":
                target = criteria.get("target", 0)
                mastery_threshold = criteria.get("mastery_threshold", 80)

                # Get user's vocabulary grouped by category with high mastery
                mastered_categories = (
                    db.session.query(Word.category_id)
                    .join(UserVocabulary)
                    .filter(
                        and_(
                            UserVocabulary.user_id == user_id,
                            UserVocabulary.mastery_level >= mastery_threshold,
                        )
                    )
                    .distinct()
                    .count()
                )
                return mastered_categories >= target

            elif criteria_type == "top_100_mastery":
                mastery_threshold = criteria.get("mastery_threshold", 80)

                # Count top 100 words with high mastery
                mastered_top_100 = (
                    db.session.query(Word)
                    .join(UserVocabulary)
                    .filter(
                        and_(
                            Word.is_top_100 == True,
                            UserVocabulary.user_id == user_id,
                            UserVocabulary.mastery_level >= mastery_threshold,
                        )
                    )
                    .count()
                )

                # Get total top 100 words
                total_top_100 = Word.query.filter_by(is_top_100=True).count()

                return mastered_top_100 >= total_top_100

            elif criteria_type == "speed_practice":
                questions = criteria.get("questions", 20)
                max_time = criteria.get("max_time", 30)

                # Check if user has any sessions meeting speed criteria
                # This would require more detailed session tracking
                # For now, return False as this needs session timing data
                return False

            return False

        except Exception as e:
            logger.error(
                f"Error checking criteria for achievement {achievement.achievement_key}: {e}"
            )
            return False

    def get_user_xp_info(self, user_id: int) -> dict:
        """Get comprehensive XP information for a user"""
        try:
            user_xp = self.get_or_create_user_xp(user_id)

            # Calculate level progression info
            current_level_xp = self.calculate_xp_for_level(user_xp.current_level)
            next_level_xp = self.calculate_xp_for_level(user_xp.current_level + 1)
            level_progress_xp = user_xp.total_xp - current_level_xp
            level_total_xp = next_level_xp - current_level_xp
            level_progress_percentage = (
                int((level_progress_xp / level_total_xp) * 100)
                if level_total_xp > 0
                else 0
            )

            # Get recent XP activities
            recent_activities = (
                XPActivity.query.filter_by(user_id=user_id)
                .order_by(XPActivity.created_at.desc())
                .limit(10)
                .all()
            )

            # Get daily XP for the last 7 days
            cutoff_date = date.today() - timedelta(days=7)
            daily_xp = (
                db.session.query(
                    XPActivity.activity_date,
                    func.sum(XPActivity.xp_earned).label("total_xp"),
                )
                .filter(
                    and_(
                        XPActivity.user_id == user_id,
                        XPActivity.activity_date >= cutoff_date,
                    )
                )
                .group_by(XPActivity.activity_date)
                .order_by(XPActivity.activity_date.desc())
                .all()
            )

            # Calculate XP streak (consecutive days with XP earned)
            xp_streak = self._calculate_xp_streak(user_id)

            return {
                "user_xp": user_xp.to_dict(),
                "level_progress": {
                    "current_level": user_xp.current_level,
                    "level_progress_xp": level_progress_xp,
                    "level_total_xp": level_total_xp,
                    "level_progress_percentage": level_progress_percentage,
                    "xp_to_next_level": user_xp.xp_to_next_level,
                },
                "recent_activities": [
                    activity.to_dict() for activity in recent_activities
                ],
                "daily_xp": [
                    {"date": day.isoformat(), "xp": int(total_xp)}
                    for day, total_xp in daily_xp
                ],
                "xp_streak": xp_streak,
                "today_xp": self._get_today_xp(user_id),
            }

        except Exception as e:
            logger.error(f"Error getting XP info for user {user_id}: {e}")
            return {"error": str(e)}

    def _calculate_xp_streak(self, user_id: int) -> int:
        """Calculate consecutive days with XP earned"""
        try:
            today = date.today()
            streak = 0
            current_date = today

            while True:
                daily_xp = XPActivity.query.filter(
                    and_(
                        XPActivity.user_id == user_id,
                        XPActivity.activity_date == current_date,
                    )
                ).first()

                if daily_xp:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

                # Safety check
                if streak > 365:
                    break

            return streak

        except Exception as e:
            logger.error(f"Error calculating XP streak for user {user_id}: {e}")
            return 0

    def _get_today_xp(self, user_id: int) -> int:
        """Get total XP earned today"""
        try:
            today = date.today()
            result = (
                db.session.query(func.sum(XPActivity.xp_earned))
                .filter(
                    and_(
                        XPActivity.user_id == user_id, XPActivity.activity_date == today
                    )
                )
                .scalar()
            )
            return int(result) if result else 0

        except Exception as e:
            logger.error(f"Error getting today's XP for user {user_id}: {e}")
            return 0

    def get_user_achievements(self, user_id: int) -> dict:
        """Get user's achievements and progress"""
        try:
            # Get earned achievements
            earned_achievements = (
                UserAchievement.query.filter_by(user_id=user_id)
                .order_by(UserAchievement.earned_at.desc())
                .all()
            )

            # Get all available achievements by category
            all_achievements = (
                Achievement.query.filter_by(is_active=True)
                .order_by(Achievement.category, Achievement.xp_reward)
                .all()
            )

            # Get earned achievement IDs for quick lookup
            earned_ids = set(ua.achievement_id for ua in earned_achievements)

            # Group achievements by category
            achievements_by_category = {}
            for achievement in all_achievements:
                category = achievement.category
                if category not in achievements_by_category:
                    achievements_by_category[category] = {
                        "earned": [],
                        "available": [],
                        "total": 0,
                        "earned_count": 0,
                    }

                achievements_by_category[category]["total"] += 1

                if achievement.id in earned_ids:
                    # Find the user achievement for this one
                    user_achievement = next(
                        ua
                        for ua in earned_achievements
                        if ua.achievement_id == achievement.id
                    )
                    achievements_by_category[category]["earned"].append(
                        user_achievement.to_dict()
                    )
                    achievements_by_category[category]["earned_count"] += 1
                else:
                    # Check progress towards this achievement
                    progress = self._get_achievement_progress(user_id, achievement)
                    achievement_dict = achievement.to_dict()
                    achievement_dict["progress"] = progress
                    achievements_by_category[category]["available"].append(
                        achievement_dict
                    )

            # Calculate total stats
            total_achievements = len(all_achievements)
            total_earned = len(earned_achievements)
            total_xp_from_achievements = sum(
                ua.achievement.xp_reward for ua in earned_achievements
            )

            return {
                "achievements_by_category": achievements_by_category,
                "earned_achievements": [ua.to_dict() for ua in earned_achievements],
                "stats": {
                    "total_achievements": total_achievements,
                    "total_earned": total_earned,
                    "completion_percentage": (
                        int((total_earned / total_achievements) * 100)
                        if total_achievements > 0
                        else 0
                    ),
                    "total_xp_from_achievements": total_xp_from_achievements,
                },
            }

        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return {"error": str(e)}

    def _get_achievement_progress(self, user_id: int, achievement: Achievement) -> dict:
        """Get progress towards a specific achievement"""
        try:
            criteria = achievement.unlock_criteria
            criteria_type = criteria.get("type")

            progress = {
                "current": 0,
                "target": criteria.get("target", 0),
                "percentage": 0,
                "description": "",
            }

            if criteria_type == "vocabulary_count":
                progress["current"] = UserVocabulary.query.filter_by(
                    user_id=user_id
                ).count()
                progress[
                    "description"
                ] = f"{progress['current']}/{progress['target']} words in vocabulary"

            elif criteria_type == "session_count":
                progress["current"] = PracticeSession.query.filter(
                    and_(
                        PracticeSession.user_id == user_id,
                        PracticeSession.total_questions > 0,
                    )
                ).count()
                progress[
                    "description"
                ] = f"{progress['current']}/{progress['target']} practice sessions completed"

            elif criteria_type == "streak_days":
                daily_streak = UserStreak.query.filter(
                    and_(
                        UserStreak.user_id == user_id, UserStreak.streak_type == "daily"
                    )
                ).first()
                progress["current"] = daily_streak.current_streak if daily_streak else 0
                progress[
                    "description"
                ] = f"{progress['current']}/{progress['target']} day streak"

            elif criteria_type == "level_reached":
                user_xp = UserXP.query.filter_by(user_id=user_id).first()
                progress["current"] = user_xp.current_level if user_xp else 1
                progress[
                    "description"
                ] = f"Level {progress['current']}/{progress['target']}"

            # Calculate percentage
            if progress["target"] > 0:
                progress["percentage"] = min(
                    100, int((progress["current"] / progress["target"]) * 100)
                )

            return progress

        except Exception as e:
            logger.error(
                f"Error getting progress for achievement {achievement.achievement_key}: {e}"
            )
            return {
                "current": 0,
                "target": 0,
                "percentage": 0,
                "description": "Progress unavailable",
            }

    def get_xp_leaderboard(self, limit: int = 10) -> list[dict]:
        """Get XP leaderboard"""
        try:
            top_users = (
                db.session.query(
                    UserXP.user_id,
                    UserXP.total_xp,
                    UserXP.current_level,
                    User.username,
                )
                .join(User)
                .order_by(UserXP.total_xp.desc())
                .limit(limit)
                .all()
            )

            leaderboard = []
            for rank, (user_id, total_xp, current_level, username) in enumerate(
                top_users, 1
            ):
                leaderboard.append(
                    {
                        "rank": rank,
                        "user_id": user_id,
                        "username": username,
                        "total_xp": total_xp,
                        "current_level": current_level,
                    }
                )

            return leaderboard

        except Exception as e:
            logger.error(f"Error getting XP leaderboard: {e}")
            return []

    # Integration methods for existing systems
    def record_practice_session_xp(
        self,
        user_id: int,
        total_questions: int,
        correct_answers: int,
        session_duration: int = None,
    ) -> dict:
        """Record XP for a completed practice session"""
        try:
            # Base XP for completing session
            session_xp = self.XP_VALUES["practice_session_complete"]

            # XP for correct answers
            correct_xp = correct_answers * self.XP_VALUES["practice_correct"]

            # Bonus for perfect session
            perfect_bonus = 0
            if total_questions > 0 and correct_answers == total_questions:
                perfect_bonus = self.XP_VALUES["practice_perfect_session"]

            total_xp = session_xp + correct_xp + perfect_bonus

            activity_details = {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": (
                    (correct_answers / total_questions * 100)
                    if total_questions > 0
                    else 0
                ),
                "session_duration": session_duration,
                "perfect_session": perfect_bonus > 0,
            }

            return self.award_xp(
                user_id=user_id,
                activity_type="practice_session_complete",
                xp_amount=total_xp,
                activity_details=activity_details,
            )

        except Exception as e:
            logger.error(f"Error recording practice session XP for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    def record_vocabulary_addition_xp(self, user_id: int, words_added: int) -> dict:
        """Record XP for adding vocabulary words"""
        try:
            xp_amount = words_added * self.XP_VALUES["vocabulary_added"]

            activity_details = {
                "words_added": words_added,
                "xp_per_word": self.XP_VALUES["vocabulary_added"],
            }

            return self.award_xp(
                user_id=user_id,
                activity_type="vocabulary_added",
                xp_amount=xp_amount,
                activity_details=activity_details,
            )

        except Exception as e:
            logger.error(f"Error recording vocabulary XP for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    def record_streak_xp(
        self, user_id: int, streak_type: str, streak_days: int
    ) -> dict:
        """Record XP for maintaining streaks"""
        try:
            if streak_type == "daily":
                xp_amount = min(
                    streak_days * self.XP_VALUES["daily_streak"], 200
                )  # Cap daily XP
            elif streak_type == "weekly":
                xp_amount = self.XP_VALUES["weekly_streak"]
            elif streak_type == "monthly":
                xp_amount = self.XP_VALUES["monthly_streak"]
            else:
                return {"success": False, "error": "Invalid streak type"}

            activity_details = {
                "streak_type": streak_type,
                "streak_days": streak_days,
            }

            return self.award_xp(
                user_id=user_id,
                activity_type=f"{streak_type}_streak",
                xp_amount=xp_amount,
                activity_details=activity_details,
            )

        except Exception as e:
            logger.error(f"Error recording streak XP for user {user_id}: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
xp_service = XPService()
