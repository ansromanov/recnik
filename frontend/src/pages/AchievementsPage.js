import React from 'react';
import AchievementsWidget from '../components/AchievementsWidget';
import XPWidget from '../components/XPWidget';
import './AchievementsPage.css';

const AchievementsPage = () => {
    return (
        <div className="achievements-page">
            <div className="page-header">
                <h1>🏆 Achievements & Progress</h1>
                <p>Track your learning journey and unlock rewards as you master Serbian vocabulary with Recnik!</p>
            </div>

            <div className="achievements-layout">
                <div className="achievements-sidebar">
                    <XPWidget />

                    <div className="quick-stats">
                        <h3>🎯 Quick Tips</h3>
                        <div className="tip-list">
                            <div className="tip-item">
                                <span className="tip-icon">📚</span>
                                <span>Add 100 words to unlock your first badge!</span>
                            </div>
                            <div className="tip-item">
                                <span className="tip-icon">💯</span>
                                <span>Complete practice sessions with 100% accuracy</span>
                            </div>
                            <div className="tip-item">
                                <span className="tip-icon">🔥</span>
                                <span>Maintain daily streaks for bonus XP</span>
                            </div>
                            <div className="tip-item">
                                <span className="tip-icon">👑</span>
                                <span>Master top 100 words to become a champion</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="achievements-main">
                    <AchievementsWidget />
                </div>
            </div>
        </div>
    );
};

export default AchievementsPage;
