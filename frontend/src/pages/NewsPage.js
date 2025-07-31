import React, { useState, useEffect } from 'react';
import { fetchNews, processText } from '../services/api';
import './NewsPage.css';

function NewsPage() {
    const [articles, setArticles] = useState([]);
    const [selectedArticle, setSelectedArticle] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingWords, setProcessingWords] = useState(false);
    const [processedWords, setProcessedWords] = useState([]);
    const [selectedWords, setSelectedWords] = useState([]);
    const [showWordSelection, setShowWordSelection] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [selectedSource, setSelectedSource] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [sources, setSources] = useState({});
    const [categories, setCategories] = useState({});
    const [availableCategories, setAvailableCategories] = useState([]);

    useEffect(() => {
        loadSourcesAndCategories();
    }, []);

    useEffect(() => {
        loadNews();
    }, [selectedSource, selectedCategory]);

    const loadSourcesAndCategories = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/news/sources');
            const data = await response.json();
            setSources(data.sources);
            setCategories(data.categories);
            setAvailableCategories(['all']); // Default to showing all categories
        } catch (err) {
            console.error('Error loading sources and categories:', err);
        }
    };

    const loadNews = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (selectedSource) params.append('source', selectedSource);
            if (selectedCategory && selectedCategory !== 'all') params.append('category', selectedCategory);

            const data = await fetchNews(params.toString());
            setArticles(data.articles || []);
        } catch (err) {
            setError('Failed to load news articles');
            console.error('Error loading news:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSourceChange = (e) => {
        const newSource = e.target.value;
        setSelectedSource(newSource);

        // Update available categories based on selected source
        if (newSource && sources[newSource] && sources[newSource].categories) {
            setAvailableCategories(sources[newSource].categories);
            // Reset category if it's not available for the new source
            if (!sources[newSource].categories.includes(selectedCategory)) {
                setSelectedCategory('all');
            }
        } else {
            // Show all unique categories when "All Sources" is selected
            const allCategories = new Set(['all']);
            Object.values(sources).forEach(source => {
                if (source.categories) {
                    source.categories.forEach(cat => allCategories.add(cat));
                }
            });
            setAvailableCategories(Array.from(allCategories));
        }
    };

    const handleArticleClick = (article) => {
        setSelectedArticle(article);
        setShowWordSelection(false);
        setProcessedWords([]);
        setSelectedWords([]);
        setSuccessMessage('');
    };

    const handleExtractWords = async () => {
        if (!selectedArticle) return;

        try {
            setProcessingWords(true);
            setError('');

            // Combine title and content for processing
            const fullText = `${selectedArticle.title} ${selectedArticle.content}`;
            const result = await processText(fullText);

            if (result.words && result.words.length > 0) {
                setProcessedWords(result.words);
                setSelectedWords(result.words.map(w => w.id));
                setShowWordSelection(true);
            } else {
                setError('No new words found in this article');
            }
        } catch (err) {
            setError('Failed to process article text');
            console.error('Error processing text:', err);
        } finally {
            setProcessingWords(false);
        }
    };

    const handleWordToggle = (wordId) => {
        setSelectedWords(prev =>
            prev.includes(wordId)
                ? prev.filter(id => id !== wordId)
                : [...prev, wordId]
        );
    };

    const handleSelectAll = () => {
        setSelectedWords(processedWords.map(w => w.id));
    };

    const handleDeselectAll = () => {
        setSelectedWords([]);
    };

    const handleSaveWords = async () => {
        const wordsToSave = processedWords.filter(w => selectedWords.includes(w.id));

        if (wordsToSave.length === 0) {
            setError('Please select at least one word to save');
            return;
        }

        try {
            // Save words using the existing vocabulary API
            for (const word of wordsToSave) {
                await fetch('http://localhost:5000/api/vocabulary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        serbian: word.serbian,
                        english: word.english,
                        category: word.category
                    })
                });
            }

            setSuccessMessage(`Successfully added ${wordsToSave.length} words to your vocabulary!`);
            setShowWordSelection(false);
            setProcessedWords([]);
            setSelectedWords([]);
        } catch (err) {
            setError('Failed to save words');
            console.error('Error saving words:', err);
        }
    };

    const highlightWords = (text) => {
        if (!showWordSelection || processedWords.length === 0) {
            return text;
        }

        let highlightedText = text;
        processedWords.forEach(word => {
            const regex = new RegExp(`\\b${word.original || word.serbian}\\b`, 'gi');
            highlightedText = highlightedText.replace(regex, match =>
                `<span class="highlighted-word" title="${word.serbian}: ${word.english}">${match}</span>`
            );
        });

        return <div dangerouslySetInnerHTML={{ __html: highlightedText }} />;
    };

    if (loading) {
        return <div className="news-page"><div className="loading">Loading news...</div></div>;
    }

    return (
        <div className="news-page">
            <h1>Serbian News</h1>
            <p className="subtitle">Read Serbian news and learn new vocabulary in context</p>

            <div className="news-filters">
                <div className="filter-group">
                    <label htmlFor="source-select">Source:</label>
                    <select
                        id="source-select"
                        value={selectedSource}
                        onChange={handleSourceChange}
                        className="filter-select"
                    >
                        <option value="">All Sources</option>
                        {Object.entries(sources).filter(([key]) => key !== 'all').map(([key, source]) => (
                            <option key={key} value={source.value}>
                                {source.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label htmlFor="category-select">Category:</label>
                    <select
                        id="category-select"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="filter-select"
                    >
                        {availableCategories.map(cat => (
                            <option key={cat} value={cat}>
                                {categories[cat] || cat}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {error && <div className="error">{error}</div>}
            {successMessage && <div className="success">{successMessage}</div>}

            <div className="news-container">
                <div className="articles-list">
                    <h2>Latest Articles</h2>
                    {articles.length === 0 ? (
                        <p>No articles available</p>
                    ) : (
                        articles.map((article, index) => (
                            <div
                                key={index}
                                className={`article-card ${selectedArticle === article ? 'selected' : ''}`}
                                onClick={() => handleArticleClick(article)}
                            >
                                <h3>{article.title}</h3>
                                <p className="article-source">{article.source} • {article.date}</p>
                                <p className="article-preview">
                                    {article.content.substring(0, 150)}...
                                </p>
                            </div>
                        ))
                    )}
                </div>

                <div className="article-reader">
                    {selectedArticle ? (
                        <>
                            <div className="article-header">
                                <h2>{selectedArticle.title}</h2>
                                <p className="article-meta">
                                    {selectedArticle.source} • {selectedArticle.date}
                                    {selectedArticle.link && (
                                        <>
                                            {' • '}
                                            <a
                                                href={selectedArticle.link}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="article-link"
                                            >
                                                Read full article
                                            </a>
                                        </>
                                    )}
                                </p>
                                {!showWordSelection && (
                                    <button
                                        className="extract-button"
                                        onClick={handleExtractWords}
                                        disabled={processingWords}
                                    >
                                        {processingWords ? 'Processing...' : 'Extract Vocabulary'}
                                    </button>
                                )}
                            </div>

                            <div className="article-content">
                                {showWordSelection ? (
                                    highlightWords(selectedArticle.content)
                                ) : (
                                    <>
                                        <p>{selectedArticle.content}</p>
                                        {selectedArticle.fullContentFetched && (
                                            <p className="article-note article-note-success">
                                                <em>Full article content loaded from N1 Info.</em>
                                            </p>
                                        )}
                                        {selectedArticle.link && selectedArticle.content.length < 500 && !selectedArticle.fullContentFetched && (
                                            <p className="article-note">
                                                <em>Note: This is a preview. Full content could not be loaded automatically.</em>
                                            </p>
                                        )}
                                    </>
                                )}
                            </div>

                            {showWordSelection && processedWords.length > 0 && (
                                <div className="word-selection">
                                    <h3>Found {processedWords.length} New Words</h3>
                                    <div className="selection-buttons">
                                        <button onClick={handleSelectAll}>Select All</button>
                                        <button onClick={handleDeselectAll}>Deselect All</button>
                                        <button
                                            className="save-button"
                                            onClick={handleSaveWords}
                                            disabled={selectedWords.length === 0}
                                        >
                                            Save {selectedWords.length} Words
                                        </button>
                                    </div>

                                    <div className="words-grid">
                                        {processedWords.map(word => (
                                            <label key={word.id} className="word-checkbox">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedWords.includes(word.id)}
                                                    onChange={() => handleWordToggle(word.id)}
                                                />
                                                <span className="word-info">
                                                    <strong>{word.serbian}</strong>
                                                    {word.original && word.original !== word.serbian &&
                                                        <span className="original-form"> ({word.original})</span>
                                                    }
                                                    <span className="translation"> - {word.english}</span>
                                                    <span className="category"> [{word.category}]</span>
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="no-article-selected">
                            <p>Select an article to start reading</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default NewsPage;
