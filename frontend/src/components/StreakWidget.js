import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';
import './StreakWidget.css';

const StreakWidget = ({ compact = false }) => {
    const [streaksData, setStreaksData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStreaksData();
    }, []);

    const fetchStreaksData = async () => {
        try {
            setLoading(true);
            const response = await apiService.getUserStreaks();
            setStreaksData(response.data);
            setError(null);
        } catch (err) {
            console.error('Error fetching streaks:', err);
            setError('Failed to load streaks');
        } finally {
            setLoading(false);
        }
    };

    const MiniProgressRing = ({ current, target, size = 50, strokeWidth = 4, color = '#4CAF50' }) => {
        const radius = (size - strokeWidth) / 2;
        const circumference = radius * 2 * Math.PI;
        const progress = Math.min(current / target, 1);
        const strokeDasharray = `${progress * circumference} ${circumference}`;

        return (
            <div className="mini-progress-ring">
                <svg width={size} height={size}>
                    <circle
                        className="mini-progress-ring-background"
                        stroke="#e0e0e0"
                        strokeWidth={strokeWidth}
                        fill="transparent"
                        r={radius}
                        cx={size / 2}
                        cy={size / 2}
                    />
                    <circle
                        className="mini-progress-ring-progress"
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
                <div className="mini-progress-text">{current}</div>
            </div>
        );
    };

    const StreakItem = ({ type, data, color, icon }) => {
        const getNextMilestone = (current) => {
            const milestones = [7, 14, 30, 60, 100, 365];
            return milestones.find(m => m > current) || current + 50;
        };

        const nextMilestone = getNextMilestone(data.current_streak);

        return (
            <div className={`streak-item ${!data.is_active ? 'inactive' : ''}`}>
                <div className="streak-item-header">
                    <span className="streak-item-icon">{icon}</span>
                    <span className="streak-item-type">{type}</span>
                    {data.is_active && <span className="active-indicator">●</span>}
                </div>
                <div className="streak-item-content">
                    <MiniProgressRing
                        current={data.current_streak}
                        target={nextMilestone}
                        color={color}
                        size={compact ? 40 : 50}
                        strokeWidth={compact ? 3 : 4}
                    />
                    <div className="streak-item-details">
                        <div className="current-streak">{data.current_streak}</div>
                        <div className="best-streak">Best: {data.longest_streak}</div>
                    </div>
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className={`streak-widget ${compact ? 'compact' : ''}`}>
                <div className="streak-widget-header">
                    <h3>🔥 Streaks</h3>
                </div>
                <div className="loading-streaks">
                    <div className="loading-spinner-small"></div>
                    <span>Loading...</span>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`streak-widget ${compact ? 'compact' : ''}`}>
                <div className="streak-widget-header">
                    <h3>🔥 Streaks</h3>
                </div>
                <div className="error-streaks">
                    <span>Failed to load streaks</span>
                    <button onClick={fetchStreaksData} className="retry-mini">↻</button>
                </div>
            </div>
        );
    }

    if (!streaksData) {
        return null;
    }

    const streakItems = [
        { type: 'Daily', data: streaksData.streaks.daily, color: '#FF6B35', icon: '🔥' },
        { type: 'Weekly', data: streaksData.streaks.weekly, color: '#4ECDC4', icon: '📅' },
        { type: 'Monthly', data: streaksData.streaks.monthly, color: '#45B7D1', icon: '🗓️' }
    ];

    return (
        <div className={`streak-widget ${compact ? 'compact' : ''}`}>
            <div className="streak-widget-header">
                <h3>🔥 Your Streaks</h3>
                <Link to="/streaks" className="view-all-link">View Details</Link>
            </div>

            <div className="streak-items">
                {streakItems.map((item, index) => (
                    <StreakItem
                        key={index}
                        type={item.type}
                        data={item.data}
                        color={item.color}
                        icon={item.icon}
                    />
                ))}
            </div>

            {streaksData.total_activities_today > 0 && (
                <div className="today-activity">
                    <span className="activity-badge">
                        {streaksData.total_activities_today} activities today ✓
                    </span>
                </div>
            )}

            <div className="streak-widget-footer">
                <Link to="/streaks" className="full-view-button">
                    View Full Streaks Page →
                </Link>
            </div>
        </div>
    );
};

export default StreakWidget;
