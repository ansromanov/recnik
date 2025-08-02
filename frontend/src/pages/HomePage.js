import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import StreakWidget from '../components/StreakWidget';
import XPWidget from '../components/XPWidget';
import AchievementsWidget from '../components/AchievementsWidget';

function HomePage() {
    const [stats, setStats] = useState({
        total_words: 0,
        user_vocabulary_count: 0,
        learned_words: 0,
        mastered_words: 0,
        recent_sessions: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const response = await apiService.getStats();
            setStats(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load statistics');
            console.error('Error fetching stats:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) return <div className="loading">Loading statistics...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="container">
            <h1>Serbian Vocabulary Learning</h1>

            <div className="stats-grid">
                <div className="stat-card">
                    <h3>My Vocabulary</h3>
                    <div className="stat-value">{stats.user_vocabulary_count || 0}</div>
                </div>
                <div className="stat-card">
                    <h3>Learned Words</h3>
                    <div className="stat-value">{stats.learned_words}</div>
                </div>
                <div className="stat-card">
                    <h3>Mastered Words</h3>
                    <div className="stat-value">{stats.mastered_words}</div>
                </div>
                <div className="stat-card">
                    <h3>Progress</h3>
                    <div className="stat-value">
                        {stats.user_vocabulary_count > 0
                            ? Math.round((stats.mastered_words / stats.user_vocabulary_count) * 100)
                            : 0}%
                    </div>
                </div>
            </div>

            <div className="gamification-widgets">
                <XPWidget />
                <StreakWidget />
                <AchievementsWidget compact={true} />
            </div>

            <div className="card">
                <h2>Recent Practice Sessions</h2>
                {stats.recent_sessions.length === 0 ? (
                    <p>No practice sessions yet. Start practicing to see your progress!</p>
                ) : (
                    <table style={{ width: '100%', marginTop: '20px' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid #ddd' }}>
                                <th style={{ padding: '10px', textAlign: 'left' }}>Date</th>
                                <th style={{ padding: '10px', textAlign: 'left' }}>Questions</th>
                                <th style={{ padding: '10px', textAlign: 'left' }}>Correct</th>
                                <th style={{ padding: '10px', textAlign: 'left' }}>Accuracy</th>
                                <th style={{ padding: '10px', textAlign: 'left' }}>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stats.recent_sessions.map((session) => (
                                <tr key={session.id} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '10px' }}>{formatDate(session.session_date)}</td>
                                    <td style={{ padding: '10px' }}>{session.total_questions}</td>
                                    <td style={{ padding: '10px' }}>{session.correct_answers}</td>
                                    <td style={{ padding: '10px' }}>
                                        {session.total_questions > 0
                                            ? Math.round((session.correct_answers / session.total_questions) * 100)
                                            : 0}%
                                    </td>
                                    <td style={{ padding: '10px' }}>
                                        {session.duration_seconds
                                            ? `${Math.floor(session.duration_seconds / 60)}:${(session.duration_seconds % 60).toString().padStart(2, '0')}`
                                            : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <div className="card">
                <h2>Getting Started</h2>
                <ol style={{ marginLeft: '20px', lineHeight: '1.8' }}>
                    <li>
                        <strong>Add New Words:</strong> Go to "Process Text" to paste Serbian text and automatically extract new vocabulary with translations.
                    </li>
                    <li>
                        <strong>Review Vocabulary:</strong> Visit "My Vocabulary" to see all your saved words organized by categories.
                    </li>
                    <li>
                        <strong>Practice:</strong> Use the "Practice" section to test your knowledge and improve retention.
                    </li>
                </ol>
            </div>
        </div>
    );
}

export default HomePage;
