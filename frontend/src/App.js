import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, NavLink } from 'react-router-dom';
import HomePage from './pages/HomePage';
import TextProcessorPage from './pages/TextProcessorPage';
import VocabularyPage from './pages/VocabularyPage';
import PracticePage from './pages/PracticePage';
import NewsPage from './pages/NewsPage';

function App() {
    return (
        <Router>
            <div className="App">
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
                </nav>

                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/process-text" element={<TextProcessorPage />} />
                    <Route path="/vocabulary" element={<VocabularyPage />} />
                    <Route path="/practice" element={<PracticePage />} />
                    <Route path="/news" element={<NewsPage />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
