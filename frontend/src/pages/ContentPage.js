import React, { useState, useEffect } from 'react';
import { fetchContent, processText } from '../services/api';
import apiService from '../services/api';
import { Link } from 'react-router-dom';
import './ContentPage.css';

function ContentPage() {
    const [articles, setArticles] = useState([]);
    const [selectedArticle, setSelectedArticle] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingWords, setProcessingWords] = useState(false);
    const [processedWords, setProcessedWords] = useState([]);
    const [selectedWords, setSelectedWords] = useState([]);
    const [showWordSelection, setShowWordSelection] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [categories, setCategories] = useState({});
    const [availableCategories, setAvailableCategories] = useState([]);
    const [cacheInfo, setCacheInfo] = useState(null);
    const [contentType, setContentType] = useState('all');
    const [showContentGenerator, setShowContentGenerator] = useState(false);
    const [generatingContent, setGeneratingContent] = useState(false);

    // Content generation form state
    const [contentTopic, setContentTopic] = useState('');
    const [generateType, setGenerateType] = useState('dialogue');
    const [difficulty, setDifficulty] = useState('intermediate');
    const [wordCount, setWordCount] = useState(200);

    useEffect(() => {
        loadSourcesAndCategories();
    }, []);

    useEffect(() => {
        loadContent();
    }, [selectedCategory, contentType]);

    const loadSourcesAndCategories = async () => {
        try {
            const response = await apiService.getContentSources();
            const data = response.data;
            setCategories(data.categories);
            setAvailableCategories(['all']); // Default to showing all categories
        } catch (err) {
            console.error('Error loading sources and categories:', err);
        }
    };

    const loadContent = async () => {
        try {
            setLoading(true);
            const params = new URLSearchParams();
            if (selectedCategory && selectedCategory !== 'all') params.append('category', selectedCategory);
            if (contentType !== 'all') params.append('type', contentType);

            const data = await fetchContent(params.toString());
            setArticles(data.articles || []);

            // Set cache info if available
            if (data.from_cache) {
                setCacheInfo({
                    fromCache: true,
                    lastUpdate: data.last_update
                });
            } else {
                setCacheInfo(null);
            }
        } catch (err) {
            setError('Failed to load content');
            console.error('Error loading content:', err);
        } finally {
            setLoading(false);
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
                setError('No new words found in this content');
            }
        } catch (err) {
            if (err.response && err.response.status === 400) {
                setError(
                    <span>
                        Please configure your OpenAI API key in{' '}
                        <Link to="/settings">Settings</Link> to extract vocabulary
                    </span>
                );
            } else {
                setError('Failed to process content text');
            }
            console.error('Error processing text:', err);
        } finally {
            setProcessingWords(false);
        }
    };

    const handleGenerateContent = async () => {
        if (!contentTopic.trim()) {
            setError('Please enter a topic for content generation');
            return;
        }

        try {
            setGeneratingContent(true);
            setError('');

            let response;
            switch (generateType) {
                case 'dialogue':
                    response = await apiService.generateDialogue(contentTopic, difficulty, wordCount);
                    break;
                case 'story':
                    response = await apiService.generateVocabularyContent(contentTopic, [], 'story');
                    break;
                case 'summary':
                    // For summary, we'll use the selected article's content if available
                    const textToSummarize = selectedArticle ? selectedArticle.content : contentTopic;
                    response = await apiService.generateSummary(textToSummarize, 'brief');
                    break;
                default:
                    throw new Error('Invalid content type');
            }

            if (response.data.success) {
                setSuccessMessage(response.data.message);
                // Add the generated content to the articles list
                const newContent = response.data.content;
                setArticles(prev => [newContent, ...prev]);
                // Select the newly generated content
                setSelectedArticle(newContent);
                setShowContentGenerator(false);
                setContentTopic('');
            } else {
                setError('Failed to generate content');
            }
        } catch (err) {
            if (err.response && err.response.status === 400) {
                setError(
                    <span>
                        Please configure your OpenAI API key in{' '}
                        <Link to="/settings">Settings</Link> to generate content
                    </span>
                );
            } else {
                setError('Failed to generate content: ' + (err.response?.data?.error || err.message));
            }
            console.error('Error generating content:', err);
        } finally {
            setGeneratingContent(false);
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
        const wordsToExclude = processedWords.filter(w => !selectedWords.includes(w.id));

        if (wordsToSave.length === 0) {
            setError('Please select at least one word to save');
            return;
        }

        try {
            // Convert words to the format expected by the API
            const wordsForApi = wordsToSave.map(word => ({
                serbian_word: word.serbian,
                english_translation: word.english,
                category_id: 1, // Default category, you might want to map this properly
                context: `From content: ${selectedArticle.title}`,
                notes: word.original && word.original !== word.serbian ? `Original form: ${word.original}` : null
            }));

            await apiService.addWords(wordsForApi);

            // Add unselected words to excluded list so they won't appear in future lessons
            if (wordsToExclude.length > 0) {
                const wordsToExcludeApi = wordsToExclude.map(word => ({
                    serbian_word: word.serbian,
                    english_translation: word.english,
                    category_id: 1
                }));

                await apiService.bulkExcludeWords(wordsToExcludeApi, 'content_parser_skip');
            }

            setSuccessMessage(
                `Successfully added ${wordsToSave.length} words to your vocabulary!` +
                (wordsToExclude.length > 0 ? ` ${wordsToExclude.length} words were excluded from future lessons.` : '')
            );
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

    // Format content based on type for better display
    const formatContentDisplay = (content, contentType) => {
        if (contentType === 'dialogue') {
            // Format dialogue with proper speaker indication
            const lines = content.split('\n').filter(line => line.trim());
            return lines.map((line, index) => {
                if (line.includes(':')) {
                    const [speaker, ...textParts] = line.split(':');
                    const text = textParts.join(':').trim();
                    return (
                        <div key={index} className="dialogue-line">
                            <span className="dialogue-speaker">{speaker.trim()}:</span> {text}
                        </div>
                    );
                }
                return <p key={index}>{line}</p>;
            });
        }

        // For other content types, split into paragraphs
        return content.split('\n\n').map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
        ));
    };

    if (loading) {
        return <div className="loading">Loading content...</div>;
    }

    return (
        <div className="container">
            <h1>Serbian Content</h1>
            <p className="subtitle">Read Serbian content and learn new vocabulary in context</p>

            {cacheInfo && (
                <div className="cache-info">
                    <span className="cache-badge">📦 Cached</span>
                    {cacheInfo.lastUpdate && (
                        <span className="cache-time">
                            Last updated: {new Date(cacheInfo.lastUpdate).toLocaleTimeString()}
                        </span>
                    )}
                </div>
            )}

            <div className="content-filters">
                <div className="filter-group">
                    <label htmlFor="category-select">Category:</label>
                    <select
                        id="category-select"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Categories</option>
                        {Object.entries(categories).map(([key, name]) => (
                            <option key={key} value={key}>
                                {name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <label htmlFor="content-type-select">Content Type:</label>
                    <select
                        id="content-type-select"
                        value={contentType}
                        onChange={(e) => setContentType(e.target.value)}
                        className="filter-select"
                    >
                        <option value="all">All Content</option>
                        <option value="article">Articles</option>
                        <option value="dialogue">Dialogues</option>
                        <option value="summary">Summaries</option>
                        <option value="story">Stories</option>
                    </select>
                </div>

                <div className="filter-group">
                    <button
                        className="generate-content-button"
                        onClick={() => setShowContentGenerator(!showContentGenerator)}
                    >
                        {showContentGenerator ? 'Hide Generator' : 'Generate Content'}
                    </button>
                </div>
            </div>

            {showContentGenerator && (
                <div className="content-generator">
                    <h3>Generate New Content</h3>
                    <div className="generator-form">
                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="content-topic">Topic:</label>
                                <input
                                    type="text"
                                    id="content-topic"
                                    value={contentTopic}
                                    onChange={(e) => setContentTopic(e.target.value)}
                                    placeholder="Enter a topic (e.g., Serbian culture, technology)"
                                    className="topic-input"
                                />
                            </div>
                            <div className="form-group">
                                <label htmlFor="generate-type">Type:</label>
                                <select
                                    id="generate-type"
                                    value={generateType}
                                    onChange={(e) => setGenerateType(e.target.value)}
                                    className="generate-type-select"
                                >
                                    <option value="dialogue">Dialogue</option>
                                    <option value="story">Story</option>
                                    <option value="summary">Summary</option>
                                </select>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="difficulty">Difficulty:</label>
                                <select
                                    id="difficulty"
                                    value={difficulty}
                                    onChange={(e) => setDifficulty(e.target.value)}
                                    className="difficulty-select"
                                >
                                    <option value="beginner">Beginner</option>
                                    <option value="intermediate">Intermediate</option>
                                    <option value="advanced">Advanced</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label htmlFor="word-count">Word Count:</label>
                                <select
                                    id="word-count"
                                    value={wordCount}
                                    onChange={(e) => setWordCount(parseInt(e.target.value))}
                                    className="word-count-select"
                                >
                                    <option value={150}>~150 words</option>
                                    <option value={200}>~200 words</option>
                                    <option value={300}>~300 words</option>
                                </select>
                            </div>
                        </div>

                        <div className="generator-buttons">
                            <button
                                className="generate-button"
                                disabled={generatingContent}
                                onClick={handleGenerateContent}
                            >
                                {generatingContent ? 'Generating...' : 'Generate Content'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {error && <div className="error">{typeof error === 'string' ? error : error}</div>}
            {successMessage && <div className="success">{successMessage}</div>}

            <div className="content-container">
                <div className="articles-list">
                    <h2>Latest Content</h2>
                    {articles.length === 0 ? (
                        <p>No content available</p>
                    ) : (
                        articles.map((article, index) => (
                            <div
                                key={index}
                                className={`article-card ${selectedArticle === article ? 'selected' : ''} ${article.content_type || 'article'}`}
                                onClick={() => handleArticleClick(article)}
                            >
                                <h3>{article.title}</h3>
                                <div className="article-meta-line">
                                    <span className="article-source">{article.source}</span>
                                    {article.content_type && (
                                        <span className={`content-type-badge ${article.content_type}`}>
                                            {article.content_type}
                                        </span>
                                    )}
                                    <span className="article-date">• {article.date || article.created_at}</span>
                                </div>
                                <p className="article-preview">
                                    {article.content.substring(0, 150)}...
                                </p>
                                {article.word_count && (
                                    <div className="content-metadata">
                                        <span className="metadata-item">
                                            <strong>Words:</strong> {article.word_count}
                                        </span>
                                        {article.reading_time_minutes && (
                                            <span className="metadata-item">
                                                <strong>Reading time:</strong> {article.reading_time_minutes} min
                                            </span>
                                        )}
                                        {article.difficulty_level && (
                                            <span className="metadata-item">
                                                <strong>Level:</strong> {article.difficulty_level}
                                            </span>
                                        )}
                                    </div>
                                )}
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
                                    {selectedArticle.source} • {selectedArticle.date || selectedArticle.created_at}
                                    {selectedArticle.source_url && (
                                        <>
                                            {' • '}
                                            <a
                                                href={selectedArticle.source_url}
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
                                    formatContentDisplay(selectedArticle.content, selectedArticle.content_type)
                                )}

                                {selectedArticle.has_full_content && (
                                    <p className="article-note article-note-success">
                                        <em>Full content loaded successfully.</em>
                                    </p>
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
                            <p>Select content to start reading</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ContentPage;
