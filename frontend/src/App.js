import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import apiService from './services/api';
import HomePage from './pages/HomePage';
import TextProcessorPage from './pages/TextProcessorPage';
import VocabularyPage from './pages/VocabularyPage';
import PracticePage from './pages/PracticePage';
import ContentPage from './pages/ContentPage';
import LoginPage from './pages/LoginPage';
import SettingsPage from './pages/SettingsPage';
import Top100Page from './pages/Top100Page';
import StreaksPage from './pages/StreaksPage';
import AchievementsPage from './pages/AchievementsPage';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [avatar, setAvatar] = useState(null);
    const [loading, setLoading] = useState(true);
    const [dropdownOpen, setDropdownOpen] = useState(false);

    useEffect(() => {
        // Check if user is already logged in
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (token && savedUser) {
            setIsAuthenticated(true);
            setUser(JSON.parse(savedUser));
            fetchCurrentAvatar();
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        // Close dropdown when clicking outside
        const handleClickOutside = (event) => {
            if (dropdownOpen && !event.target.closest('.user-dropdown')) {
                setDropdownOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [dropdownOpen]);

    const fetchCurrentAvatar = async () => {
        try {
            const response = await apiService.getCurrentAvatar();
            setAvatar(response.data.avatar);
        } catch (err) {
            console.error('Error fetching current avatar:', err);
            // If no avatar exists, generate a default one
            try {
                const generateResponse = await apiService.generateAvatar();
                setAvatar(generateResponse.data.avatar);
            } catch (generateErr) {
                console.error('Error generating default avatar:', generateErr);
            }
        }
    };

    const handleLogin = (token, userData) => {
        setIsAuthenticated(true);
        setUser(userData);
        fetchCurrentAvatar();
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setUser(null);
        setAvatar(null);
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <Router>
            <div className="App">
                {isAuthenticated && (
                    <nav className="nav">
                        <div className="nav-left">
                            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                                Home
                            </NavLink>
                            <NavLink to="/process-text" className={({ isActive }) => isActive ? 'active' : ''}>
                                Process Text
                            </NavLink>
                            <NavLink to="/vocabulary" className={({ isActive }) => isActive ? 'active' : ''}>
                                My Vocabulary
                            </NavLink>
                            <NavLink to="/top100" className={({ isActive }) => isActive ? 'active' : ''}>
                                Top 100
                            </NavLink>
                            <NavLink to="/practice" className={({ isActive }) => isActive ? 'active' : ''}>
                                Practice
                            </NavLink>
                            <NavLink to="/content" className={({ isActive }) => isActive ? 'active' : ''}>
                                Content
                            </NavLink>
                        </div>
                        <div className="nav-right">
                            <div className="user-dropdown">
                                <button
                                    className="user-dropdown-toggle"
                                    onClick={() => setDropdownOpen(!dropdownOpen)}
                                >
                                    {avatar && (
                                        <img
                                            src={avatar.avatar_url}
                                            alt="User Avatar"
                                            className="nav-user-avatar"
                                            onError={(e) => {
                                                console.error('Avatar failed to load:', avatar.avatar_url);
                                                e.target.style.display = 'none';
                                            }}
                                        />
                                    )}
                                    Welcome, {user?.username} ▼
                                </button>
                                {dropdownOpen && (
                                    <div className="user-dropdown-menu">
                                        <div className="dropdown-section">
                                            <div className="dropdown-section-title">Profile</div>
                                            <NavLink
                                                to="/achievements"
                                                className="dropdown-item"
                                                onClick={() => setDropdownOpen(false)}
                                            >
                                                Achievements
                                            </NavLink>
                                            <NavLink
                                                to="/streaks"
                                                className="dropdown-item"
                                                onClick={() => setDropdownOpen(false)}
                                            >
                                                Streaks
                                            </NavLink>
                                        </div>
                                        <div className="dropdown-section">
                                            <NavLink
                                                to="/settings"
                                                className="dropdown-item"
                                                onClick={() => setDropdownOpen(false)}
                                            >
                                                Settings
                                            </NavLink>
                                            <button
                                                onClick={() => {
                                                    handleLogout();
                                                    setDropdownOpen(false);
                                                }}
                                                className="dropdown-item logout-item"
                                            >
                                                Logout
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </nav>
                )}

                <Routes>
                    {/* Public route */}
                    <Route
                        path="/login"
                        element={
                            isAuthenticated ?
                                <Navigate to="/" replace /> :
                                <LoginPage onLogin={handleLogin} />
                        }
                    />

                    {/* Protected routes */}
                    <Route
                        path="/"
                        element={
                            isAuthenticated ?
                                <HomePage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/process-text"
                        element={
                            isAuthenticated ?
                                <TextProcessorPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/vocabulary"
                        element={
                            isAuthenticated ?
                                <VocabularyPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/top100"
                        element={
                            isAuthenticated ?
                                <Top100Page /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/practice"
                        element={
                            isAuthenticated ?
                                <PracticePage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/content"
                        element={
                            isAuthenticated ?
                                <ContentPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/news"
                        element={
                            isAuthenticated ?
                                <Navigate to="/content" replace /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/achievements"
                        element={
                            isAuthenticated ?
                                <AchievementsPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/streaks"
                        element={
                            isAuthenticated ?
                                <StreaksPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/settings"
                        element={
                            isAuthenticated ?
                                <SettingsPage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
