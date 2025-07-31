import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import TextProcessorPage from './pages/TextProcessorPage';
import VocabularyPage from './pages/VocabularyPage';
import PracticePage from './pages/PracticePage';
import NewsPage from './pages/NewsPage';
import LoginPage from './pages/LoginPage';
import SettingsPage from './pages/SettingsPage';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const token = localStorage.getItem('token');
        const savedUser = localStorage.getItem('user');

        if (token && savedUser) {
            setIsAuthenticated(true);
            setUser(JSON.parse(savedUser));
        }
        setLoading(false);
    }, []);

    const handleLogin = (token, userData) => {
        setIsAuthenticated(true);
        setUser(userData);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setUser(null);
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <Router>
            <div className="App">
                {isAuthenticated && (
                    <nav className="nav">
                        <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
                            Home
                        </NavLink>
                        <NavLink to="/process-text" className={({ isActive }) => isActive ? 'active' : ''}>
                            Process Text
                        </NavLink>
                        <NavLink to="/vocabulary" className={({ isActive }) => isActive ? 'active' : ''}>
                            My Vocabulary
                        </NavLink>
                        <NavLink to="/practice" className={({ isActive }) => isActive ? 'active' : ''}>
                            Practice
                        </NavLink>
                        <NavLink to="/news" className={({ isActive }) => isActive ? 'active' : ''}>
                            News
                        </NavLink>
                        <NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>
                            Settings
                        </NavLink>
                        <div className="nav-right">
                            <span className="user-info">Welcome, {user?.username}</span>
                            <button onClick={handleLogout} className="logout-button">
                                Logout
                            </button>
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
                        path="/practice"
                        element={
                            isAuthenticated ?
                                <PracticePage /> :
                                <Navigate to="/login" replace />
                        }
                    />
                    <Route
                        path="/news"
                        element={
                            isAuthenticated ?
                                <NewsPage /> :
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
