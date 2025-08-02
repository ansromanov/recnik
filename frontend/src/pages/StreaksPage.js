import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './StreaksPage.css';

const StreaksPage = () => {
    const [streaksData, setStreaksData] = useState(null);
    const [leaderboard, setLeaderboard] = useState([]);
    const [selectedStreakType, setSelectedStreakType] = useState('daily');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStreaksData();
        fetchLeaderboard();
    }, []);

    useEffect(() => {
        fetchLeaderboard();
    }, [selectedStreakType]);

    const fetchStreaksData = async () => {
        try {
            setLoading(true);
            const response = await apiService.getUserStreaks();
            setStreaksData(response.data);
            setError(null);
        } catch (err) {
            console.error('Error fetching streaks:', err);
            setError('Failed to load streaks data');
        } finally {
            setLoading(false);
        }
    };

    const fetchLeaderboard = async () => {
        try {
            const response = await apiService.getStreakLeaderboard(selectedStreakType, 10);
            setLeaderboard(response.data.leaderboard || []);
        } catch (err) {
            console.error('Error fetching leaderboard:', err);
        }
    };

    const ProgressRing = ({
        current,
        target,
        size = 120,
        strokeWidth = 8,
        color = '#4CAF50',
        backgroundColor = '#e0e0e0'
    }) => {
        const radius = (size - strokeWidth) / 2;
        const circumference = radius * 2 * Math.PI;
        const progress = Math.min(current / target, 1);
        const strokeDasharray = `${progress * circumference} ${circumference}`;

        return (
            <div className="progress-ring-container">
                <svg
                    className="progress-ring"
                    width={size}
                    height={size}
                >
                    {/* Background circle */}
                    <circle
                        className="progress-ring-background"
                        stroke={backgroundColor}
                        strokeWidth={strokeWidth}
                        fill="transparent"
                        r={radius}
                        cx={size / 2}
                        cy={size / 2}
                    />
                    {/* Progress circle */}
                    <circle
                        className="progress-ring-progress"
                        stroke={color}
                        strokeWidth={strokeWidth}
                        fill="transparent"
                        r={radius}
                        cx={size / 2}
                        cy={size / 2}
                        strokeDasharray={strokeDasharray}
                        strokeDashoffset={0}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${size / 2} ${size / 2})`}
                    />
                </svg>
                <div className="progress-ring-text">
                    <div className="progress-ring-current">{current}</div>
                    <div className="progress-ring-target">/ {target}</div>
                </div>
            </div>
        );
    };

    const StreakCard = ({ type, data, color }) => {
        const getNextMilestone = (current) => {
            const milestones = [7, 14, 30, 60, 100, 365];
            return milestones.find(m => m > current) || current + 50;
        };

        const getStreakIcon = (type) => {
            switch (type) {
                case 'daily': return '🔥';
                case 'weekly': return '📅';
                case 'monthly': return '🗓️';
                default: return '⭐';
            }
        };

        const formatLastActivity = (dateString) => {
            if (!dateString) return 'Never';
            const date = new Date(dateString);
            const today = new Date();
            const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));

            if (diffDays === 0) return 'Today';
            if (diffDays === 1) return 'Yesterday';
            return `${diffDays} days ago`;
        };

        const nextMilestone = getNextMilestone(data.current_streak);

        return (
            <div className={`streak-card ${type}-streak ${!data.is_active ? 'inactive' : ''}`}>
                <div className="streak-card-header">
                    <div className="streak-icon">{getStreakIcon(type)}</div>
                    <div className="streak-type">{type.charAt(0).toUpperCase() + type.slice(1)} Streak</div>
                    <div className={`streak-status ${data.is_active ? 'active' : 'inactive'}`}>
                        {data.is_active ? 'Active' : 'Broken'}
                    </div>
                </div>

                <div className="streak-content">
                    <div className="progress-section">
                        <ProgressRing
                            current={data.current_streak}
                            target={nextMilestone}
                            color={color}
                            size={100}
                            strokeWidth={6}
                        />
                        <div className="streak-details">
                            <div className="streak-metric">
                                <span className="metric-label">Current</span>
                                <span className="metric-value">{data.current_streak}</span>
                            </div>
                            <div className="streak-metric">
                                <span className="metric-label">Best</span>
                                <span className="metric-value">{data.longest_streak}</span>
                            </div>
                        </div>
                    </div>

                    <div className="streak-info">
                        <div className="info-item">
                            <span className="info-label">Last Activity:</span>
                            <span className="info-value">{formatLastActivity(data.last_activity_date)}</span>
                        </div>
                        {data.is_active && data.days_until_break > 0 && (
                            <div className="info-item warning">
                                <span className="info-label">Expires in:</span>
                                <span className="info-value">{data.days_until_break} day{data.days_until_break !== 1 ? 's' : ''}</span>
                            </div>
                        )}
                        <div className="info-item">
                            <span className="info-label">Next milestone:</span>
                            <span className="info-value">{nextMilestone} days</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const ActivitySummary = ({ recentActivities, totalToday }) => {
        return (
            <div className="activity-summary">
                <h3>Activity Summary</h3>
                <div className="today-summary">
                    <div className="today-count">
                        <span className="count-number">{totalToday}</span>
                        <span className="count-label">Activities Today</span>
                    </div>
                </div>

                <div className="recent-activities">
                    <h4>Recent Activities</h4>
                    {recentActivities && recentActivities.length > 0 ? (
                        <div className="activities-list">
                            {recentActivities.slice(0, 5).map((activity, index) => (
                                <div key={index} className="activity-item">
                                    <div className="activity-date">
                                        {new Date(activity.activity_date).toLocaleDateString()}
                                    </div>
                                    <div className="activity-details">
                                        <span className="activity-type">{activity.activity_type.replace('_', ' ')}</span>
                                        <span className="activity-count">({activity.activity_count})</span>
                                        {activity.streak_qualifying && (
                                            <span className="qualifying-badge">✓</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="no-activities">
                            <p>No recent activities found.</p>
                            <p>Start practicing or adding vocabulary to build your streaks!</p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const Leaderboard = ({ leaderboard, streakType }) => {
        return (
            <div className="leaderboard">
                <div className="leaderboard-header">
                    <h3>Leaderboard</h3>
                    <select
                        value={streakType}
                        onChange={(e) => setSelectedStreakType(e.target.value)}
                        className="streak-type-selector"
                    >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                    </select>
                </div>

                <div className="leaderboard-list">
                    {leaderboard.length > 0 ? (
                        leaderboard.map((entry, index) => (
                            <div key={entry.user_id} className={`leaderboard-entry ${index < 3 ? 'top-three' : ''}`}>
                                <div className="rank">
                                    {index === 0 && '🥇'}
                                    {index === 1 && '🥈'}
                                    {index === 2 && '🥉'}
                                    {index > 2 && `#${entry.rank}`}
                                </div>
                                <div className="username">{entry.username}</div>
                                <div className="streak-value">
                                    <span className="current">{entry.current_streak}</span>
                                    <span className="best">({entry.longest_streak} best)</span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="no-leaderboard">
                            <p>No leaderboard data available yet.</p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="streaks-page">
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <p>Loading your streaks...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="streaks-page">
                <div className="error">
                    <h2>Error Loading Streaks</h2>
                    <p>{error}</p>
                    <button onClick={fetchStreaksData} className="retry-button">
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="streaks-page">
            <div className="page-header">
                <h1>Your Learning Streaks</h1>
                <p>Track your daily, weekly, and monthly learning progress</p>
            </div>

            {streaksData && (
                <>
                    <div className="streaks-grid">
                        <StreakCard
                            type="daily"
                            data={streaksData.streaks.daily}
                            color="#FF6B35"
                        />
                        <StreakCard
                            type="weekly"
                            data={streaksData.streaks.weekly}
                            color="#4ECDC4"
                        />
                        <StreakCard
                            type="monthly"
                            data={streaksData.streaks.monthly}
                            color="#45B7D1"
                        />
                    </div>

                    <div className="bottom-section">
                        <ActivitySummary
                            recentActivities={streaksData.recent_activities}
                            totalToday={streaksData.total_activities_today}
                        />

                        <Leaderboard
                            leaderboard={leaderboard}
                            streakType={selectedStreakType}
                        />
                    </div>
                </>
            )}
        </div>
    );
};

export default StreaksPage;
