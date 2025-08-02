import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import CustomModal from '../components/CustomModal';
import { useToast } from '../components/ToastNotification';
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
    const [searchResults, setSearchResults] = useState(null);
    const [searchLoading, setSearchLoading] = useState(false);
    const [showAddWordForm, setShowAddWordForm] = useState(false);
    const [newWordData, setNewWordData] = useState({
        serbian_word: '',
        english_translation: '',
        category_id: 1,
        context: '',
        notes: ''
    });

    // Custom modal state
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [confirmModalData, setConfirmModalData] = useState({
        title: '',
        message: '',
        onConfirm: null
    });

    // Toast notifications
    const { showToast, ToastContainer } = useToast();

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

    const handleRemoveWord = (word) => {
        setConfirmModalData({
            title: 'Remove Word',
            message: `Are you sure you want to remove "${word.serbian_word}" from your vocabulary? This will add it to your excluded words list.`,
            onConfirm: async () => {
                try {
                    await apiService.excludeWordFromVocabulary(word.id);
                    // Refresh both vocabulary and excluded words
                    fetchWords();
                    fetchExcludedWords();
                    showToast(`"${word.serbian_word}" has been removed from your vocabulary`, 'success');
                } catch (err) {
                    showToast('Failed to remove word from vocabulary', 'error');
                    console.error('Error removing word:', err);
                }
                setShowConfirmModal(false);
            }
        });
        setShowConfirmModal(true);
    };

    const handleRestoreWord = (excludedWord) => {
        setConfirmModalData({
            title: 'Restore Word',
            message: `Are you sure you want to restore "${excludedWord.word.serbian_word}" to your vocabulary?`,
            onConfirm: async () => {
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
                    showToast(`"${excludedWord.word.serbian_word}" has been restored to your vocabulary`, 'success');
                } catch (err) {
                    showToast('Failed to restore word to vocabulary', 'error');
                    console.error('Error restoring word:', err);
                }
                setShowConfirmModal(false);
            }
        });
        setShowConfirmModal(true);
    };

    const handlePermanentlyDeleteExcluded = (excludedWord) => {
        setConfirmModalData({
            title: 'Delete Excluded Word',
            message: `Are you sure you want to permanently remove "${excludedWord.word.serbian_word}" from your excluded list? You will be able to add it back to vocabulary later.`,
            onConfirm: async () => {
                try {
                    await apiService.removeFromExcludedWords(excludedWord.id);
                    fetchExcludedWords();
                    showToast(`"${excludedWord.word.serbian_word}" has been permanently removed from excluded list`, 'success');
                } catch (err) {
                    showToast('Failed to remove word from excluded list', 'error');
                    console.error('Error removing from excluded list:', err);
                }
                setShowConfirmModal(false);
            }
        });
        setShowConfirmModal(true);
    };

    const handleSearch = async (query) => {
        if (!query || query.length < 2) {
            setSearchResults(null);
            return;
        }

        setSearchLoading(true);
        try {
            const response = await apiService.searchWords(query);
            setSearchResults(response.data);
        } catch (err) {
            console.error('Error searching words:', err);
            setSearchResults(null);
        } finally {
            setSearchLoading(false);
        }
    };

    const handleSearchInputChange = (e) => {
        const value = e.target.value;
        setSearchTerm(value);

        // Debounce search API calls
        setTimeout(() => {
            handleSearch(value);
        }, 300);
    };

    const handleAddSuggestedWord = async () => {
        if (!newWordData.serbian_word || !newWordData.english_translation) {
            setError('Both Serbian word and English translation are required');
            return;
        }

        try {
            const response = await apiService.addSuggestedWord(newWordData);
            if (response.data.success) {
                // Reset form and close modal
                setNewWordData({
                    serbian_word: '',
                    english_translation: '',
                    category_id: 1,
                    context: '',
                    notes: ''
                });
                setShowAddWordForm(false);
                setSearchResults(null);
                setSearchTerm('');

                // Refresh vocabulary
                fetchWords();

                // Show success message
                showToast(response.data.message, 'success');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to add word');
            console.error('Error adding suggested word:', err);
        }
    };

    const openAddWordForm = (suggestion) => {
        setNewWordData({
            serbian_word: suggestion.suggested_serbian,
            english_translation: suggestion.suggested_english,
            category_id: 1,
            context: '',
            notes: ''
        });
        setShowAddWordForm(true);
    };

    const filterWords = () => {
        let filtered = words;

        if (selectedCategory) {
            filtered = filtered.filter(word => word.category_id === selectedCategory);
        }

        if (searchTerm && !searchResults) {
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

    const renderSearchSection = () => (
        <section className="search-section card">
            <div className="search-container">
                <input
                    type="text"
                    className="input-field search-input"
                    placeholder="Search words in your vocabulary or add new ones..."
                    value={searchTerm}
                    onChange={handleSearchInputChange}
                />
                {searchLoading && (
                    <div className="search-loading-indicator">
                        🔍
                    </div>
                )}
            </div>

            {searchResults && (
                <div className="search-results">
                    <header className="search-results-header">
                        <h4>Search Results for "{searchResults.query}"</h4>
                    </header>

                    {searchResults.vocabulary_results.length > 0 && (
                        <div className="vocabulary-results">
                            <h5>In Your Vocabulary ({searchResults.vocabulary_results.length})</h5>
                            <div className="search-results-grid">
                                {searchResults.vocabulary_results.map(word => (
                                    <div key={`vocab-${word.id}`} className="search-result-item">
                                        <div className="word-details">
                                            <strong>{word.serbian_word}</strong> - {word.english_translation}
                                        </div>
                                        <span className="category-badge small">{word.category_name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {searchResults.all_results.filter(w => !w.is_in_vocabulary).length > 0 && (
                        <div className="available-results">
                            <h5>Available to Add ({searchResults.all_results.filter(w => !w.is_in_vocabulary).length})</h5>
                            <div className="search-results-grid">
                                {searchResults.all_results.filter(w => !w.is_in_vocabulary).map(word => (
                                    <div key={`available-${word.id}`} className="search-result-item">
                                        <div className="word-details">
                                            <strong>{word.serbian_word}</strong> - {word.english_translation}
                                        </div>
                                        <span className="category-badge small">{word.category_name}</span>
                                        <button
                                            className="add-word-btn small"
                                            onClick={() => {
                                                setNewWordData({
                                                    serbian_word: word.serbian_word,
                                                    english_translation: word.english_translation,
                                                    category_id: word.category_id,
                                                    context: word.context || '',
                                                    notes: word.notes || ''
                                                });
                                                setShowAddWordForm(true);
                                            }}
                                        >
                                            + Add
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {searchResults.suggestion && (
                        <div className={`word-suggestion ${searchResults.suggestion.llm_processed ? 'ai-enhanced' : 'basic'}`}>
                            <header className="suggestion-header">
                                <h5>
                                    <span className="suggestion-icon">
                                        {searchResults.suggestion.llm_processed ? '🧠' : '💡'}
                                    </span>
                                    {searchResults.suggestion.message}
                                </h5>
                            </header>

                            {searchResults.suggestion.llm_processed && (
                                <div className="suggestion-details">
                                    <div className="details-grid">
                                        {searchResults.suggestion.suggested_serbian && (
                                            <div className="detail-item">
                                                <strong>Serbian:</strong> {searchResults.suggestion.suggested_serbian}
                                            </div>
                                        )}
                                        {searchResults.suggestion.suggested_english && (
                                            <div className="detail-item">
                                                <strong>English:</strong> {searchResults.suggestion.suggested_english}
                                            </div>
                                        )}
                                        {searchResults.suggestion.word_type && (
                                            <div className="detail-item">
                                                <strong>Type:</strong> {searchResults.suggestion.word_type}
                                            </div>
                                        )}
                                        {searchResults.suggestion.confidence && (
                                            <div className="detail-item">
                                                <strong>Confidence:</strong>
                                                <span className={`confidence-level ${searchResults.suggestion.confidence}`}>
                                                    {searchResults.suggestion.confidence}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {searchResults.suggestion.needs_openai_key && (
                                <div className="openai-warning">
                                    <p>⚠️ Configure your OpenAI API key in Settings to get AI-powered translation and word normalization.</p>
                                </div>
                            )}

                            <div className="suggestion-actions">
                                <button
                                    className={`add-word-btn ${searchResults.suggestion.llm_processed ? 'ai-enhanced' : ''}`}
                                    onClick={() => openAddWordForm(searchResults.suggestion)}
                                >
                                    + Add "{searchResults.suggestion.search_term}" to Vocabulary
                                </button>

                                {searchResults.suggestion.llm_processed && (
                                    <span className="ai-badge">✨ AI Enhanced</span>
                                )}
                            </div>

                            {searchResults.suggestion.error && (
                                <div className="suggestion-error">
                                    Error: {searchResults.suggestion.error}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </section>
    );

    const renderCategoryFilter = () => (
        <section className="category-filter-section">
            <div className="category-filter">
                <button
                    className={`category-badge ${!selectedCategory ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(null)}
                >
                    All ({words.length})
                </button>
                {categories.map(cat => {
                    const count = words.filter(w => w.category_id === cat.id).length;
                    return (
                        <button
                            key={cat.id}
                            className={`category-badge ${selectedCategory === cat.id ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(cat.id)}
                        >
                            {cat.name} ({count})
                        </button>
                    );
                })}
            </div>
        </section>
    );

    const renderWordGrid = () => (
        <section className="words-section">
            {filteredWords.length === 0 ? (
                <div className="empty-state">
                    <p>No words in your vocabulary. Start by processing some Serbian text or reading news articles!</p>
                </div>
            ) : (
                <div className="word-grid">
                    {filteredWords.map(word => (
                        <article
                            key={word.id}
                            className="word-card"
                            style={{
                                backgroundImage: wordImages[word.id] ? `url(${wordImages[word.id]})` : 'none'
                            }}
                        >
                            <div className="word-image-section">
                                {loadingImages[word.id] ? (
                                    <div className="image-placeholder loading-state">
                                        <div className="image-spinner"></div>
                                    </div>
                                ) : !wordImages[word.id] ? (
                                    <div className="image-placeholder empty-state">
                                        <span>📷</span>
                                    </div>
                                ) : null}
                            </div>

                            <div className="word-content">
                                <header className="word-header">
                                    <h3 className="serbian-word">{word.serbian_word}</h3>
                                    <p className="english-translation">{word.english_translation}</p>
                                </header>

                                <div className="word-meta">
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
                                        <div className="mastery-progress">
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
                            </div>

                            <div className="word-actions">
                                <button
                                    className="remove-word-btn"
                                    onClick={() => handleRemoveWord(word)}
                                    title="Remove from vocabulary"
                                    aria-label={`Remove ${word.serbian_word} from vocabulary`}
                                >
                                    ×
                                </button>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </section>
    );

    const renderStatistics = () => (
        <section className="statistics-section card">
            <header>
                <h3>Vocabulary Statistics</h3>
            </header>
            <div className="stats-grid">
                <div className="stat-card">
                    <h3>Total Words</h3>
                    <div className="stat-value">{words.length}</div>
                </div>
                <div className="stat-card">
                    <h3>Mastered (80%+)</h3>
                    <div className="stat-value">
                        {words.filter(w => w.mastery_level >= 80).length}
                    </div>
                </div>
                <div className="stat-card">
                    <h3>In Progress</h3>
                    <div className="stat-value">
                        {words.filter(w => w.mastery_level > 0 && w.mastery_level < 80).length}
                    </div>
                </div>
                <div className="stat-card">
                    <h3>Not Started</h3>
                    <div className="stat-value">
                        {words.filter(w => !w.mastery_level || w.mastery_level === 0).length}
                    </div>
                </div>
                <div className="stat-card">
                    <h3>Excluded Words</h3>
                    <div className="stat-value">{excludedWords.length}</div>
                </div>
            </div>
        </section>
    );

    const renderExcludedWords = () => (
        <section className="excluded-words-section card">
            <header className="excluded-words-header">
                <h3>Excluded Words</h3>
                <button
                    className="toggle-excluded-btn btn"
                    onClick={() => setShowExcludedWords(!showExcludedWords)}
                    aria-expanded={showExcludedWords}
                >
                    {showExcludedWords ? 'Hide' : 'Show'} ({excludedWords.length})
                </button>
            </header>

            {showExcludedWords && (
                <div className="excluded-words-content">
                    <p className="excluded-words-description">
                        These words have been excluded from your vocabulary and will not appear in lessons or practice sessions.
                    </p>

                    {loadingExcluded ? (
                        <div className="loading-state">Loading excluded words...</div>
                    ) : excludedWords.length === 0 ? (
                        <div className="empty-state">
                            <p>No excluded words. Words you remove from vocabulary will appear here.</p>
                        </div>
                    ) : (
                        <div className="excluded-words-table">
                            <div className="table-header" role="row">
                                <div className="table-cell" role="columnheader">Serbian Word</div>
                                <div className="table-cell" role="columnheader">English Translation</div>
                                <div className="table-cell" role="columnheader">Category</div>
                                <div className="table-cell" role="columnheader">Reason</div>
                                <div className="table-cell" role="columnheader">Date Excluded</div>
                                <div className="table-cell" role="columnheader">Actions</div>
                            </div>
                            {excludedWords.map(excluded => (
                                <div key={excluded.id} className="table-row" role="row">
                                    <div className="table-cell" role="cell">
                                        <strong>{excluded.word.serbian_word}</strong>
                                    </div>
                                    <div className="table-cell" role="cell">
                                        {excluded.word.english_translation}
                                    </div>
                                    <div className="table-cell" role="cell">
                                        <span className="category-badge">
                                            {excluded.word.category_name || 'Unknown'}
                                        </span>
                                    </div>
                                    <div className="table-cell" role="cell">
                                        <span className={`reason-badge ${excluded.reason}`}>
                                            {excluded.reason === 'manual_removal' ? 'Manual' :
                                                excluded.reason === 'news_parser_skip' ? 'News Skip' :
                                                    excluded.reason || 'Unknown'}
                                        </span>
                                    </div>
                                    <div className="table-cell" role="cell">
                                        {new Date(excluded.created_at).toLocaleDateString()}
                                    </div>
                                    <div className="table-cell" role="cell">
                                        <div className="table-actions">
                                            <button
                                                className="restore-btn"
                                                onClick={() => handleRestoreWord(excluded)}
                                                title="Restore to vocabulary"
                                                aria-label={`Restore ${excluded.word.serbian_word} to vocabulary`}
                                            >
                                                ↩️ Restore
                                            </button>
                                            <button
                                                className="delete-btn"
                                                onClick={() => handlePermanentlyDeleteExcluded(excluded)}
                                                title="Remove from excluded list"
                                                aria-label={`Remove ${excluded.word.serbian_word} from excluded list`}
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
        </section>
    );

    const renderAddWordModal = () => (
        showAddWordForm && (
            <div className="modal-overlay" onClick={() => setShowAddWordForm(false)}>
                <div className="modal-content" onClick={e => e.stopPropagation()}>
                    <header className="modal-header">
                        <h3>Add Word to Vocabulary</h3>
                    </header>
                    <form className="add-word-form" onSubmit={(e) => { e.preventDefault(); handleAddSuggestedWord(); }}>
                        <div className="form-group">
                            <label htmlFor="serbian-word">Serbian Word *</label>
                            <input
                                id="serbian-word"
                                type="text"
                                className="input-field"
                                value={newWordData.serbian_word}
                                onChange={(e) => setNewWordData(prev => ({ ...prev, serbian_word: e.target.value }))}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="english-translation">English Translation *</label>
                            <input
                                id="english-translation"
                                type="text"
                                className="input-field"
                                value={newWordData.english_translation}
                                onChange={(e) => setNewWordData(prev => ({ ...prev, english_translation: e.target.value }))}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="category">Category</label>
                            <select
                                id="category"
                                className="input-field"
                                value={newWordData.category_id}
                                onChange={(e) => setNewWordData(prev => ({ ...prev, category_id: parseInt(e.target.value) }))}
                            >
                                {categories.map(cat => (
                                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="context">Context (optional)</label>
                            <textarea
                                id="context"
                                className="input-field"
                                value={newWordData.context}
                                onChange={(e) => setNewWordData(prev => ({ ...prev, context: e.target.value }))}
                                placeholder="Example sentence or context where you encountered this word"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="notes">Notes (optional)</label>
                            <textarea
                                id="notes"
                                className="input-field"
                                value={newWordData.notes}
                                onChange={(e) => setNewWordData(prev => ({ ...prev, notes: e.target.value }))}
                                placeholder="Personal notes about this word"
                            />
                        </div>

                        <div className="form-actions">
                            <button type="button" className="btn-secondary" onClick={() => setShowAddWordForm(false)}>
                                Cancel
                            </button>
                            <button type="submit" className="btn-primary">
                                Add Word & Queue Image
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        )
    );

    if (loading) {
        return (
            <div className="loading-container">
                <div className="loading">Loading vocabulary...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="error-container">
                <div className="error">{error}</div>
            </div>
        );
    }

    return (
        <div className="vocabulary-page">
            <div className="page-header">
                <h1>My Vocabulary</h1>
            </div>

            <div className="container page-content">
                {renderSearchSection()}
                {renderCategoryFilter()}
                {renderWordGrid()}
                {renderStatistics()}
                {renderExcludedWords()}
            </div>

            {renderAddWordModal()}

            <CustomModal
                isOpen={showConfirmModal}
                onClose={() => setShowConfirmModal(false)}
                onConfirm={confirmModalData.onConfirm}
                title={confirmModalData.title}
                message={confirmModalData.message}
                type="confirm"
            />

            <ToastContainer />
        </div>
    );
}

export default VocabularyPage;
