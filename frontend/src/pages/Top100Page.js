import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';
import './Top100Page.css';

function Top100Page() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [words, setWords] = useState([]);
    const [selectedWords, setSelectedWords] = useState(new Set());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            setLoading(true);
            const response = await apiService.getCategories();
            // Filter categories that have top 100 words
            const categoriesWithTop100 = response.data.filter(cat => cat.top_100_count > 0);
            setCategories(categoriesWithTop100);
            setLoading(false);
        } catch (error) {
            setError('Failed to fetch categories');
            setLoading(false);
        }
    };

    const fetchCategoryWords = async (categoryId) => {
        try {
            setLoading(true);
            setError('');
            const response = await apiService.getTop100WordsByCategory(categoryId);
            setWords(response.data.words);
            setSelectedCategory(response.data.category);
            setSelectedWords(new Set());
            setLoading(false);
        } catch (error) {
            setError('Failed to fetch words');
            setLoading(false);
        }
    };

    const toggleWordSelection = (wordId) => {
        const newSelection = new Set(selectedWords);
        if (newSelection.has(wordId)) {
            newSelection.delete(wordId);
        } else {
            newSelection.add(wordId);
        }
        setSelectedWords(newSelection);
    };

    const selectAll = () => {
        const notInVocabulary = words.filter(w => !w.is_in_vocabulary);
        setSelectedWords(new Set(notInVocabulary.map(w => w.id)));
    };

    const deselectAll = () => {
        setSelectedWords(new Set());
    };

    const addSelectedWords = async () => {
        if (selectedWords.size === 0) {
            setError('Please select at least one word');
            return;
        }

        try {
            setLoading(true);
            const response = await apiService.addTop100WordsToVocabulary(Array.from(selectedWords));

            setSuccessMessage(`Successfully added ${response.data.added} words to your vocabulary!`);
            setSelectedWords(new Set());

            // Refresh the words to update their status
            if (selectedCategory) {
                fetchCategoryWords(selectedCategory.id);
            }

            setTimeout(() => setSuccessMessage(''), 3000);
        } catch (error) {
            setError('Failed to add words to vocabulary');
            setLoading(false);
        }
    };

    const getProgressPercentage = (category) => {
        if (category.top_100_count === 0) return 0;
        return Math.round((category.user_added_count / category.top_100_count) * 100);
    };

    if (loading && categories.length === 0) {
        return <div className="loading">Loading categories...</div>;
    }

    return (
        <div className="top100-page">
            <h1>Top 100 Serbian Words</h1>
            <p className="subtitle">Learn the most common Serbian words organized by category</p>

            {error && <div className="error-message">{error}</div>}
            {successMessage && <div className="success-message">{successMessage}</div>}

            {!selectedCategory ? (
                <div className="categories-grid">
                    {categories.map(category => {
                        const progress = getProgressPercentage(category);
                        return (
                            <div
                                key={category.id}
                                className="category-card"
                                onClick={() => fetchCategoryWords(category.id)}
                            >
                                <h3>{category.name}</h3>
                                <p className="category-description">{category.description}</p>
                                <div className="category-stats">
                                    <span className="word-count">{category.top_100_count} words</span>
                                    <span className="progress-text">
                                        {category.user_added_count} / {category.top_100_count} added
                                    </span>
                                </div>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${progress}%` }}
                                    />
                                </div>
                                <div className="progress-percentage">{progress}% complete</div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="words-section">
                    <div className="section-header">
                        <button
                            className="back-button"
                            onClick={() => {
                                setSelectedCategory(null);
                                setWords([]);
                                setSelectedWords(new Set());
                            }}
                        >
                            ← Back to Categories
                        </button>
                        <h2>{selectedCategory.name}</h2>
                        <div className="selection-controls">
                            <button onClick={selectAll} className="select-btn">
                                Select All Not Added
                            </button>
                            <button onClick={deselectAll} className="select-btn">
                                Deselect All
                            </button>
                        </div>
                    </div>

                    {loading ? (
                        <div className="loading">Loading words...</div>
                    ) : (
                        <>
                            <div className="words-grid">
                                {words.map(word => (
                                    <div
                                        key={word.id}
                                        className={`word-card ${word.is_in_vocabulary ? 'in-vocabulary' : ''} ${selectedWords.has(word.id) ? 'selected' : ''}`}
                                        onClick={() => !word.is_in_vocabulary && toggleWordSelection(word.id)}
                                    >
                                        <div className="word-content">
                                            <h4>{word.serbian_word}</h4>
                                            <p>{word.english_translation}</p>
                                        </div>
                                        {word.is_in_vocabulary ? (
                                            <div className="word-status">
                                                <span className="checkmark">✓</span>
                                                <span className="status-text">In vocabulary</span>
                                                {word.mastery_level > 0 && (
                                                    <div className="mastery-indicator">
                                                        <div className="mastery-bar">
                                                            <div
                                                                className="mastery-fill"
                                                                style={{ width: `${word.mastery_level}%` }}
                                                            />
                                                        </div>
                                                        <span className="mastery-text">{word.mastery_level}%</span>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="word-checkbox">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedWords.has(word.id)}
                                                    onChange={(e) => e.stopPropagation()}
                                                    readOnly
                                                />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {selectedWords.size > 0 && (
                                <div className="action-bar">
                                    <span className="selection-count">
                                        {selectedWords.size} word{selectedWords.size !== 1 ? 's' : ''} selected
                                    </span>
                                    <button
                                        onClick={addSelectedWords}
                                        className="add-button"
                                        disabled={loading}
                                    >
                                        Add to My Vocabulary
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export default Top100Page;
