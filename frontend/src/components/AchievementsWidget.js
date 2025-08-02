import React, { useState, useEffect } from 'react';
import './AchievementsWidget.css';
import { fetchWithAuth } from '../services/api';

const AchievementsWidget = ({ compact = false }) => {
    const [achievementsData, setAchievementsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('all');

    useEffect(() => {
        fetchAchievements();
    }, []);

    const fetchAchievements = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth('/achievements');
            if (response.ok) {
                const data = await response.json();
                setAchievementsData(data);
            } else {
                setError('Failed to fetch achievements');
            }
        } catch (err) {
            console.error('Error fetching achievements:', err);
            setError('Error loading achievements');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className={`achievements-widget ${compact ? 'compact' : ''} loading`}>
                <div className="loading-spinner"></div>
                <span>Loading achievements...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`achievements-widget ${compact ? 'compact' : ''} error`}>
                <span>⚠️ {error}</span>
            </div>
        );
    }

    if (!achievementsData) {
        return null;
    }

    const { achievements_by_category, stats, earned_achievements } = achievementsData;
    const categories = Object.keys(achievements_by_category || {});
    const recentEarned = earned_achievements?.slice(0, 3) || [];

    // If compact mode, show only recent achievements
    if (compact) {
        return (
            <div className="achievements-widget compact">
                <div className="achievements-header">
                    <h3>🏆 Recent Achievements</h3>
                    <div className="achievements-stats-compact">
                        {stats?.total_earned || 0}/{stats?.total_achievements || 0}
                    </div>
                </div>
                <div className="recent-achievements">
                    {recentEarned.length > 0 ? (
                        recentEarned.map((achievement) => (
                            <div key={achievement.id} className="achievement-badge compact">
                                <span className="achievement-icon">{achievement.achievement?.badge_icon || '🏆'}</span>
                                <div className="achievement-info">
                                    <div className="achievement-name">{achievement.achievement?.name}</div>
                                    <div className="achievement-xp">+{achievement.achievement?.xp_reward || 0} XP</div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="no-achievements">
                            <span>🎯</span>
                            <span>Start learning to earn achievements!</span>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Full achievements view
    const filteredAchievements = selectedCategory === 'all'
        ? achievements_by_category
        : { [selectedCategory]: achievements_by_category[selectedCategory] };

    return (
        <div className="achievements-widget">
            <div className="achievements-header">
                <h2>🏆 Achievements</h2>
                <div className="achievements-stats">
                    <div className="stat">
                        <span className="stat-value">{stats?.total_earned || 0}</span>
                        <span className="stat-label">Earned</span>
                    </div>
                    <div className="stat">
                        <span className="stat-value">{stats?.completion_percentage || 0}%</span>
                        <span className="stat-label">Complete</span>
                    </div>
                    <div className="stat">
                        <span className="stat-value">{stats?.total_xp_from_achievements || 0}</span>
                        <span className="stat-label">Bonus XP</span>
                    </div>
                </div>
            </div>

            <div className="category-filters">
                <button
                    className={`category-filter ${selectedCategory === 'all' ? 'active' : ''}`}
                    onClick={() => setSelectedCategory('all')}
                >
                    All
                </button>
                {categories.map((category) => (
                    <button
                        key={category}
                        className={`category-filter ${selectedCategory === category ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(category)}
                    >
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                        <span className="category-count">
                            {achievements_by_category[category]?.earned_count || 0}
                        </span>
                    </button>
                ))}
            </div>

            <div className="achievements-grid">
                {Object.entries(filteredAchievements).map(([category, categoryData]) => (
                    <div key={category} className="achievement-category">
                        <h3 className="category-title">
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                            <span className="category-progress">
                                {categoryData.earned_count}/{categoryData.total}
                            </span>
                        </h3>

                        {/* Earned achievements */}
                        {categoryData.earned.length > 0 && (
                            <div className="achievements-section earned">
                                <h4>✅ Earned</h4>
                                <div className="achievements-list">
                                    {categoryData.earned.map((achievement) => (
                                        <div key={achievement.id} className="achievement-badge earned">
                                            <div
                                                className="achievement-badge-inner"
                                                style={{ backgroundColor: achievement.achievement?.badge_color || '#3498db' }}
                                            >
                                                <span className="achievement-icon">
                                                    {achievement.achievement?.badge_icon || '🏆'}
                                                </span>
                                            </div>
                                            <div className="achievement-details">
                                                <div className="achievement-name">{achievement.achievement?.name}</div>
                                                <div className="achievement-description">
                                                    {achievement.achievement?.description}
                                                </div>
                                                <div className="achievement-xp">+{achievement.achievement?.xp_reward || 0} XP</div>
                                                <div className="achievement-date">
                                                    Earned {new Date(achievement.earned_at).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Available achievements */}
                        {categoryData.available.length > 0 && (
                            <div className="achievements-section available">
                                <h4>🎯 Available</h4>
                                <div className="achievements-list">
                                    {categoryData.available.map((achievement) => (
                                        <div key={achievement.id} className="achievement-badge available">
                                            <div
                                                className="achievement-badge-inner locked"
                                                style={{ borderColor: achievement.badge_color || '#3498db' }}
                                            >
                                                <span className="achievement-icon locked">
                                                    {achievement.badge_icon || '🏆'}
                                                </span>
                                            </div>
                                            <div className="achievement-details">
                                                <div className="achievement-name">{achievement.name}</div>
                                                <div className="achievement-description">
                                                    {achievement.description}
                                                </div>
                                                <div className="achievement-xp">+{achievement.xp_reward || 0} XP</div>
                                                {achievement.progress && (
                                                    <div className="achievement-progress">
                                                        <div className="progress-bar">
                                                            <div
                                                                className="progress-fill"
                                                                style={{ width: `${achievement.progress.percentage}%` }}
                                                            ></div>
                                                        </div>
                                                        <div className="progress-text">
                                                            {achievement.progress.description} ({achievement.progress.percentage}%)
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AchievementsWidget;
