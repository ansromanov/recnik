import React, { useState } from 'react';
import apiService from '../services/api';

function TextProcessorPage() {
    const [text, setText] = useState('');
    const [processing, setProcessing] = useState(false);
    const [results, setResults] = useState(null);
    const [selectedWords, setSelectedWords] = useState([]);
    const [categories, setCategories] = useState([]);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    React.useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            const response = await apiService.getCategories();
            setCategories(response.data);
        } catch (err) {
            console.error('Error fetching categories:', err);
        }
    };

    const handleProcessText = async () => {
        if (!text.trim()) {
            setError('Please enter some Serbian text to process');
            return;
        }

        setProcessing(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await apiService.processText(text);
            setResults(response.data);
            setSelectedWords(response.data.translations.map((t, index) => ({
                ...t,
                id: index,
                category_id: t.category_id || 1,
                selected: true
            })));
        } catch (err) {
            setError('Failed to process text. Please try again.');
            console.error('Error processing text:', err);
        } finally {
            setProcessing(false);
        }
    };

    const toggleWordSelection = (wordId) => {
        setSelectedWords(words =>
            words.map(word =>
                word.id === wordId ? { ...word, selected: !word.selected } : word
            )
        );
    };

    const updateWordCategory = (wordId, categoryId) => {
        setSelectedWords(words =>
            words.map(word =>
                word.id === wordId ? { ...word, category_id: parseInt(categoryId) } : word
            )
        );
    };

    const handleSelectAll = () => {
        setSelectedWords(words =>
            words.map(word => ({ ...word, selected: true }))
        );
    };

    const handleDeselectAll = () => {
        setSelectedWords(words =>
            words.map(word => ({ ...word, selected: false }))
        );
    };

    const handleSaveWords = async () => {
        const wordsToSave = selectedWords
            .filter(word => word.selected)
            .map(({ serbian_word, english_translation, category_id }) => ({
                serbian_word,
                english_translation,
                category_id
            }));

        if (wordsToSave.length === 0) {
            setError('Please select at least one word to save');
            return;
        }

        try {
            const response = await apiService.addWords(wordsToSave);
            setSuccess(`Successfully saved ${response.data.inserted} words!`);
            setResults(null);
            setSelectedWords([]);
            setText('');
        } catch (err) {
            setError('Failed to save words. Please try again.');
            console.error('Error saving words:', err);
        }
    };

    return (
        <div className="container">
            <h1>Process Serbian Text</h1>

            <div className="card">
                <p>Paste Serbian text below to extract new vocabulary words with automatic translations.</p>

                <textarea
                    className="text-input-area"
                    placeholder="Paste your Serbian text here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />

                <button
                    className="btn"
                    onClick={handleProcessText}
                    disabled={processing}
                >
                    {processing ? 'Processing...' : 'Process Text'}
                </button>
            </div>

            {error && <div className="error">{error}</div>}
            {success && <div className="success">{success}</div>}

            {results && (
                <div className="card">
                    <h2>Processing Results</h2>
                    <div style={{ marginBottom: '20px' }}>
                        <p><strong>Total words found:</strong> {results.total_words}</p>
                        <p><strong>Already in vocabulary:</strong> {results.existing_words}</p>
                        <p><strong>New words:</strong> {results.new_words}</p>
                    </div>

                    {selectedWords.length > 0 && (
                        <>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                <h3>Select words to add to your vocabulary:</h3>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleSelectAll}
                                        style={{ padding: '5px 15px', fontSize: '14px' }}
                                    >
                                        Select All
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleDeselectAll}
                                        style={{ padding: '5px 15px', fontSize: '14px' }}
                                    >
                                        Deselect All
                                    </button>
                                </div>
                            </div>
                            <div className="translation-results">
                                {selectedWords.map((word) => (
                                    <div key={word.id} className="translation-item">
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                                            <input
                                                type="checkbox"
                                                checked={word.selected}
                                                onChange={() => toggleWordSelection(word.id)}
                                            />
                                            <span>
                                                <strong>{word.serbian_word}</strong> - {word.english_translation}
                                                {word.original_form && word.original_form !== word.serbian_word && (
                                                    <span style={{ fontSize: '12px', color: '#666', marginLeft: '10px' }}>
                                                        (from: {word.original_form})
                                                    </span>
                                                )}
                                            </span>
                                        </div>
                                        <select
                                            value={word.category_id}
                                            onChange={(e) => updateWordCategory(word.id, e.target.value)}
                                            style={{ padding: '5px' }}
                                        >
                                            {categories.map(cat => (
                                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                ))}
                            </div>

                            <div className="button-group">
                                <button
                                    className="btn"
                                    onClick={handleSaveWords}
                                >
                                    Save Selected Words
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={() => {
                                        setResults(null);
                                        setSelectedWords([]);
                                    }}
                                >
                                    Cancel
                                </button>
                            </div>
                        </>
                    )}
                </div>
            )}

            <div className="card">
                <h3>Tips:</h3>
                <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
                    <li>The system will automatically detect unique words from your text</li>
                    <li>Verbs are converted to infinitive form (e.g., "радим" → "радити")</li>
                    <li>Words are lowercase except proper nouns (names, places)</li>
                    <li>Words already in your vocabulary will be skipped</li>
                    <li>OpenAI API will translate up to 50 new words at a time</li>
                    <li>Categories are automatically assigned by AI based on word type</li>
                    <li>You can manually change categories and select/deselect words before saving</li>
                    <li>Use "Select All" or "Deselect All" buttons for quick selection</li>
                </ul>
            </div>
        </div>
    );
}

export default TextProcessorPage;
