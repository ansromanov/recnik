import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './VocabularyPage.css';

function VocabularyPage() {
    const [words, setWords] = useState([]);
    const [filteredWords, setFilteredWords] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [wordImages, setWordImages] = useState({});
    const [loadingImages, setLoadingImages] = useState({});
    const [excludedWords, setExcludedWords] = useState([]);
    const [showExcludedWords, setShowExcludedWords] = useState(false);
    const [loadingExcluded, setLoadingExcluded] = useState(false);

    useEffect(() => {
        fetchCategories();
        fetchWords();
        fetchExcludedWords();
    }, []);

    useEffect(() => {
        filterWords();
    }, [words, selectedCategory, searchTerm]);

    const fetchCategories = async () => {
        try {
            const response = await apiService.getCategories();
            setCategories(response.data);
        } catch (err) {
            console.error('Error fetching categories:', err);
        }
    };

    const fetchWords = async () => {
        try {
            setLoading(true);
            const response = await apiService.getWords();
            // Filter to only show words that are in the user's vocabulary
            const userWords = response.data.filter(word => word.is_in_vocabulary);
            setWords(userWords);
            setError(null);
        } catch (err) {
            setError('Failed to load vocabulary');
            console.error('Error fetching words:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchExcludedWords = async () => {
        try {
            setLoadingExcluded(true);
            const response = await apiService.getExcludedWords();
            setExcludedWords(response.data);
        } catch (err) {
            console.error('Error fetching excluded words:', err);
        } finally {
            setLoadingExcluded(false);
        }
    };

    const handleRemoveWord = async (word) => {
        if (window.confirm(`Are you sure you want to remove "${word.serbian_word}" from your vocabulary? This will add it to your excluded words list.`)) {
            try {
                await apiService.excludeWordFromVocabulary(word.id);
                // Refresh both vocabulary and excluded words
                fetchWords();
                fetchExcludedWords();
            } catch (err) {
                setError('Failed to remove word from vocabulary');
                console.error('Error removing word:', err);
            }
        }
    };

    const handleRestoreWord = async (excludedWord) => {
        if (window.confirm(`Are you sure you want to restore "${excludedWord.word.serbian_word}" to your vocabulary?`)) {
            try {
                await apiService.removeFromExcludedWords(excludedWord.id);
                // Add the word back to vocabulary
                await apiService.addWords([{
                    serbian_word: excludedWord.word.serbian_word,
                    english_translation: excludedWord.word.english_translation,
                    category_id: excludedWord.word.category_id,
                    context: excludedWord.word.context,
                    notes: excludedWord.word.notes
                }]);
                // Refresh both vocabulary and excluded words
                fetchWords();
                fetchExcludedWords();
            } catch (err) {
                setError('Failed to restore word to vocabulary');
                console.error('Error restoring word:', err);
            }
        }
    };

    const handlePermanentlyDeleteExcluded = async (excludedWord) => {
        if (window.confirm(`Are you sure you want to permanently remove "${excludedWord.word.serbian_word}" from your excluded list? You will be able to add it back to vocabulary later.`)) {
            try {
                await apiService.removeFromExcludedWords(excludedWord.id);
                fetchExcludedWords();
            } catch (err) {
                setError('Failed to remove word from excluded list');
                console.error('Error removing from excluded list:', err);
            }
        }
    };

    const filterWords = () => {
        let filtered = words;

        if (selectedCategory) {
            filtered = filtered.filter(word => word.category_id === selectedCategory);
        }

        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(word =>
                word.serbian_word.toLowerCase().includes(term) ||
                word.english_translation.toLowerCase().includes(term)
            );
        }

        setFilteredWords(filtered);
    };

    const getMasteryColor = (level) => {
        if (level >= 80) return '#4CAF50';
        if (level >= 60) return '#8BC34A';
        if (level >= 40) return '#FFC107';
        if (level >= 20) return '#FF9800';
        return '#F44336';
    };

    const loadWordImage = async (word) => {
        if (wordImages[word.id] || loadingImages[word.id]) {
            return; // Already loaded or loading
        }

        setLoadingImages(prev => ({ ...prev, [word.id]: true }));

        try {
            const response = await apiService.getWordImage(word.id);
            if (response.data.success && response.data.image) {
                setWordImages(prev => ({
                    ...prev,
                    [word.id]: `data:${response.data.image.content_type};base64,${response.data.image.image_data}`
                }));
            }
        } catch (error) {
            console.error(`Error loading image for word ${word.serbian_word}:`, error);
            // Try to search for a new image if the cached one failed
            try {
                const searchResponse = await apiService.searchImage(word.serbian_word, word.english_translation);
                if (searchResponse.data.success && searchResponse.data.image) {
                    setWordImages(prev => ({
                        ...prev,
                        [word.id]: `data:${searchResponse.data.image.content_type};base64,${searchResponse.data.image.image_data}`
                    }));
                }
            } catch (searchError) {
                console.error(`Error searching image for word ${word.serbian_word}:`, searchError);
            }
        } finally {
            setLoadingImages(prev => ({ ...prev, [word.id]: false }));
        }
    };

    // Load images for filtered words when they change
    useEffect(() => {
        filteredWords.forEach(word => {
            loadWordImage(word);
        });
    }, [filteredWords]);

    if (loading) return <div className="loading">Loading vocabulary...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="container">
            <h1>My Vocabulary</h1>

            <div className="card">
                <div style={{ marginBottom: '20px' }}>
                    <input
                        type="text"
                        className="input-field"
                        placeholder="Search words..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="category-filter">
                    <div
                        className={`category-badge ${!selectedCategory ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(null)}
                    >
                        All ({words.length})
                    </div>
                    {categories.map(cat => {
                        const count = words.filter(w => w.category_id === cat.id).length;
                        return (
                            <div
                                key={cat.id}
                                className={`category-badge ${selectedCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat.id)}
                            >
                                {cat.name} ({count})
                            </div>
                        );
                    })}
                </div>
            </div>

            {filteredWords.length === 0 ? (
                <div className="card">
                    <p>No words in your vocabulary. Start by processing some Serbian text or reading news articles!</p>
                </div>
            ) : (
                <div className="word-grid">
                    {filteredWords.map(word => (
                        <div
                            key={word.id}
                            className="word-card"
                            style={{
                                backgroundImage: wordImages[word.id] ? `url(${wordImages[word.id]})` : 'none'
                            }}
                        >
                            {/* Image status indicator */}
                            {loadingImages[word.id] ? (
                                <div className="image-placeholder loading-image">
                                    <div className="image-spinner"></div>
                                </div>
                            ) : !wordImages[word.id] ? (
                                <div className="image-placeholder">
                                    <span>📷</span>
                                </div>
                            ) : null}

                            <div className="word-header">
                                <h3 className="serbian-word">{word.serbian_word}</h3>
                                <p className="english-translation">{word.english_translation}</p>
                            </div>

                            <div className="word-category">
                                <span className="category-badge">
                                    {word.category_name}
                                </span>
                            </div>

                            {word.mastery_level !== null && (
                                <div className="mastery-section">
                                    <div className="mastery-header">
                                        <span className="mastery-label">Mastery</span>
                                        <span className="mastery-percentage">{word.mastery_level}%</span>
                                    </div>
                                    <div className="mastery-indicator">
                                        <div className="mastery-bar">
                                            <div
                                                className="mastery-fill"
                                                style={{
                                                    width: `${word.mastery_level}%`,
                                                    backgroundColor: getMasteryColor(word.mastery_level)
                                                }}
                                            />
                                        </div>
                                    </div>
                                    {word.times_practiced > 0 && (
                                        <p className="practice-count">
                                            Practiced {word.times_practiced} times
                                        </p>
                                    )}
                                </div>
                            )}

                            {word.context && (
                                <div className="word-context">
                                    <p className="context-label">Context:</p>
                                    <p className="context-text">{word.context}</p>
                                </div>
                            )}

                            {word.notes && (
                                <div className="word-notes">
                                    <p className="notes-label">Notes:</p>
                                    <p className="notes-text">{word.notes}</p>
                                </div>
                            )}

                            <div className="word-actions">
                                <button
                                    className="remove-word-btn"
                                    onClick={() => handleRemoveWord(word)}
                                    title="Remove from vocabulary"
                                >
                                    ❌ Remove
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="card" style={{ marginTop: '30px' }}>
                <h3>Vocabulary Statistics</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Total Words</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{words.length}</p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Mastered (80%+)</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => w.mastery_level >= 80).length}
                        </p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>In Progress</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => w.mastery_level > 0 && w.mastery_level < 80).length}
                        </p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Not Started</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => !w.mastery_level || w.mastery_level === 0).length}
                        </p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Excluded Words</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{excludedWords.length}</p>
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginTop: '30px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h3>Excluded Words</h3>
                    <button
                        className="category-badge"
                        onClick={() => setShowExcludedWords(!showExcludedWords)}
                        style={{ cursor: 'pointer' }}
                    >
                        {showExcludedWords ? 'Hide' : 'Show'} ({excludedWords.length})
                    </button>
                </div>

                {showExcludedWords && (
                    <div>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            These words have been excluded from your vocabulary and will not appear in lessons or practice sessions.
                        </p>

                        {loadingExcluded ? (
                            <div className="loading">Loading excluded words...</div>
                        ) : excludedWords.length === 0 ? (
                            <p>No excluded words. Words you remove from vocabulary will appear here.</p>
                        ) : (
                            <div className="excluded-words-table">
                                <div className="table-header">
                                    <div className="table-cell">Serbian Word</div>
                                    <div className="table-cell">English Translation</div>
                                    <div className="table-cell">Category</div>
                                    <div className="table-cell">Reason</div>
                                    <div className="table-cell">Date Excluded</div>
                                    <div className="table-cell">Actions</div>
                                </div>
                                {excludedWords.map(excluded => (
                                    <div key={excluded.id} className="table-row">
                                        <div className="table-cell">
                                            <strong>{excluded.word.serbian_word}</strong>
                                        </div>
                                        <div className="table-cell">
                                            {excluded.word.english_translation}
                                        </div>
                                        <div className="table-cell">
                                            <span className="category-badge">
                                                {excluded.word.category_name || 'Unknown'}
                                            </span>
                                        </div>
                                        <div className="table-cell">
                                            <span className={`reason-badge ${excluded.reason}`}>
                                                {excluded.reason === 'manual_removal' ? 'Manual' :
                                                    excluded.reason === 'news_parser_skip' ? 'News Skip' :
                                                        excluded.reason || 'Unknown'}
                                            </span>
                                        </div>
                                        <div className="table-cell">
                                            {new Date(excluded.created_at).toLocaleDateString()}
                                        </div>
                                        <div className="table-cell">
                                            <div className="table-actions">
                                                <button
                                                    className="restore-btn"
                                                    onClick={() => handleRestoreWord(excluded)}
                                                    title="Restore to vocabulary"
                                                >
                                                    ↩️ Restore
                                                </button>
                                                <button
                                                    className="delete-btn"
                                                    onClick={() => handlePermanentlyDeleteExcluded(excluded)}
                                                    title="Remove from excluded list"
                                                >
                                                    🗑️ Delete
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default VocabularyPage;
