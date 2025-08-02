import React, { useState, useEffect } from 'react';
import './XPWidget.css';
import { fetchWithAuth } from '../services/api';

const XPWidget = () => {
    const [xpData, setXpData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchXPData();
    }, []);

    const fetchXPData = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth('/xp');
            if (response.ok) {
                const data = await response.json();
                setXpData(data);
            } else {
                setError('Failed to fetch XP data');
            }
        } catch (err) {
            console.error('Error fetching XP data:', err);
            setError('Error loading XP data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="xp-widget loading">
                <div className="loading-spinner"></div>
                <span>Loading XP...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="xp-widget error">
                <span>⚠️ {error}</span>
            </div>
        );
    }

    if (!xpData) {
        return null;
    }

    const { user_xp, level_progress, today_xp, xp_streak } = xpData;
    const progressPercentage = level_progress?.level_progress_percentage || 0;

    return (
        <div className="xp-widget">
            <div className="xp-header">
                <div className="xp-title">
                    <span className="xp-icon">⭐</span>
                    <span>Level {user_xp?.current_level || 1}</span>
                </div>
                <div className="xp-total">
                    {user_xp?.total_xp?.toLocaleString() || 0} XP
                </div>
            </div>

            <div className="xp-progress-container">
                <div className="xp-progress-bar">
                    <div
                        className="xp-progress-fill"
                        style={{ width: `${progressPercentage}%` }}
                    ></div>
                </div>
                <div className="xp-progress-text">
                    {level_progress?.level_progress_xp || 0} / {level_progress?.level_total_xp || 100} XP
                </div>
            </div>

            <div className="xp-stats">
                <div className="xp-stat">
                    <span className="xp-stat-icon">🔥</span>
                    <div className="xp-stat-content">
                        <div className="xp-stat-value">{today_xp || 0}</div>
                        <div className="xp-stat-label">Today</div>
                    </div>
                </div>
                <div className="xp-stat">
                    <span className="xp-stat-icon">⚡</span>
                    <div className="xp-stat-content">
                        <div className="xp-stat-value">{xp_streak || 0}</div>
                        <div className="xp-stat-label">Day Streak</div>
                    </div>
                </div>
                <div className="xp-stat">
                    <span className="xp-stat-icon">🎯</span>
                    <div className="xp-stat-content">
                        <div className="xp-stat-value">{level_progress?.xp_to_next_level || 0}</div>
                        <div className="xp-stat-label">To Next</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default XPWidget;
