import React, { useState, useEffect } from 'react';
import { fetchContent, processText } from '../services/api';
import apiService from '../services/api';
import { Link } from 'react-router-dom';
import ttsService from '../services/ttsService';
import './ContentPage.css';

// Global function for handling dialogue line pronunciation with consistent voice assignment
window.handleDialogueLinePronunciation = async (text, buttonElement, speakerName = null, allSpeakers = []) => {
    if (!ttsService.isReady()) {
        console.warn('TTS service not ready. Status:', ttsService.getStatus());
        // Try to reinitialize TTS if it's not ready
        ttsService.loadResponsiveVoiceScript();
        return;
    }

    try {
        // Clean the text for pronunciation
        const cleanText = text.replace(/<[^>]*>/g, '').trim();

        // Get consistent voice assignment for this speaker in dialog context
        const voiceForSpeaker = ttsService.getVoiceForDialogSpeaker(speakerName, allSpeakers);

        // Temporarily set the voice for this speaker
        const originalVoice = ttsService.getCurrentVoice();
        ttsService.setVoice(voiceForSpeaker);

        await ttsService.playPronunciationWithFeedback(cleanText, buttonElement, {
            rate: 0.8,
            onstart: () => {
                console.log(`Started pronunciation for ${speakerName || 'speaker'} using voice: ${voiceForSpeaker}`);
            },
            onend: () => {
                console.log('Finished pronunciation');
                // Restore original voice
                ttsService.setVoice(originalVoice);
            },
            onerror: (error) => {
                console.error('Pronunciation error:', error);
                // Restore original voice on error
                ttsService.setVoice(originalVoice);
            }
        });
    } catch (error) {
        console.error('Error pronouncing text:', error);
    }
};

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

            // Combine title and content for processing, but preserve formatting
            let fullText;
            if (selectedArticle.content_type === 'dialogue') {
                // For dialogues, preserve the structure but clean up speaker names
                fullText = `${selectedArticle.title}\n\n${selectedArticle.content}`;
            } else {
                fullText = `${selectedArticle.title} ${selectedArticle.content}`;
            }

            const result = await processText(fullText);

            if (result.words && result.words.length > 0) {
                // Filter out any words that might have been missed due to exclusions
                const validWords = result.words.filter(word =>
                    word.serbian && word.english && word.serbian.trim() !== '' && word.english.trim() !== ''
                );

                if (validWords.length > 0) {
                    setProcessedWords(validWords);
                    setSelectedWords(validWords.map(w => w.id));
                    setShowWordSelection(true);
                } else {
                    setError('No new words found after filtering. All words may already be in your vocabulary or excluded.');
                }
            } else {
                setError('No new words found in this content. You may have already learned all the vocabulary from this text!');
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
            return formatContentDisplay(text, selectedArticle.content_type);
        }

        // Preserve the original formatting while highlighting words
        let highlightedText = text;

        // Sort words by length (longest first) to avoid partial matches
        const sortedWords = [...processedWords].sort((a, b) =>
            (b.original || b.serbian).length - (a.original || a.serbian).length
        );

        sortedWords.forEach(word => {
            const wordToMatch = word.original || word.serbian;
            // Use more precise regex to avoid breaking formatting
            const regex = new RegExp(`\\b${wordToMatch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
            highlightedText = highlightedText.replace(regex, match =>
                `<span class="highlighted-word" title="${word.serbian}: ${word.english}">${match}</span>`
            );
        });

        // Handle dialogue formatting with highlights
        if (selectedArticle.content_type === 'dialogue') {
            return (
                <div className="dialogue-content">
                    <div className="dialogue-controls">
                        <button
                            className="pronounce-dialogue-button"
                            onClick={(e) => {
                                const lines = highlightedText.split('\n').filter(line => line.trim());
                                const fullText = lines
                                    .filter(line => line.includes(':'))
                                    .map(line => {
                                        const cleanLine = line.replace(/<[^>]*>/g, ''); // Remove HTML tags
                                        return cleanLine.split(':').slice(1).join(':').trim();
                                    })
                                    .join('. ');
                                handlePronounceText(fullText, e.target);
                            }}
                            title="Pronounce entire dialogue"
                        >
                            🔊 Pronounce Dialogue
                        </button>
                    </div>
                    <div dangerouslySetInnerHTML={{ __html: formatDialogueWithHighlights(highlightedText) }} />
                </div>
            );
        }

        // For other content types, preserve paragraph structure
        const paragraphs = highlightedText.split('\n\n').filter(p => p.trim());
        return (
            <div className="formatted-content">
                <div className="content-controls">
                    <button
                        className="pronounce-content-button"
                        onClick={(e) => {
                            const cleanText = paragraphs.map(p => p.replace(/<[^>]*>/g, '')).join('. ');
                            handlePronounceText(cleanText, e.target);
                        }}
                        title="Pronounce entire content"
                    >
                        🔊 Pronounce Content
                    </button>
                </div>
                {paragraphs.map((paragraph, index) => (
                    <div key={index} className="content-paragraph">
                        <p dangerouslySetInnerHTML={{ __html: paragraph }} />
                        <button
                            className="pronounce-paragraph-button"
                            onClick={(e) => {
                                const cleanText = paragraph.replace(/<[^>]*>/g, '');
                                handlePronounceText(cleanText, e.target);
                            }}
                            title="Pronounce this paragraph"
                        >
                            🔊
                        </button>
                    </div>
                ))}
            </div>
        );
    };

    // Generate realistic Serbian names for dialogue speakers
    const generateSpeakerNames = () => {
        const maleNames = ['Marko', 'Stefan', 'Nikola', 'Miloš', 'Aleksandar', 'Filip', 'Luka', 'Petar', 'Nemanja', 'Jovan'];
        const femaleNames = ['Ana', 'Milica', 'Jovana', 'Marija', 'Tamara', 'Teodora', 'Nina', 'Ivana', 'Jelena', 'Sara'];

        const allNames = [...maleNames, ...femaleNames];
        const shuffled = allNames.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, 2); // Return 2 random names
    };

    // Format dialogue content with highlighting and proper speaker names
    const formatDialogueWithHighlights = (highlightedText) => {
        const speakerNames = generateSpeakerNames();
        const speakerMap = {};
        let speakerIndex = 0;

        const lines = highlightedText.split('\n').filter(line => line.trim());

        // First pass: collect all speakers for consistent voice assignment
        const allSpeakers = [];
        lines.forEach((line) => {
            if (line.includes(':')) {
                const [originalSpeaker] = line.split(':');
                const trimmedSpeaker = originalSpeaker.trim().replace(/<[^>]*>/g, '');

                let displaySpeaker = trimmedSpeaker;
                if (trimmedSpeaker === 'Osoba A' || trimmedSpeaker === 'Person A') {
                    if (!speakerMap['A']) {
                        speakerMap['A'] = speakerNames[0] || 'Marko';
                    }
                    displaySpeaker = speakerMap['A'];
                } else if (trimmedSpeaker === 'Osoba B' || trimmedSpeaker === 'Person B') {
                    if (!speakerMap['B']) {
                        speakerMap['B'] = speakerNames[1] || 'Ana';
                    }
                    displaySpeaker = speakerMap['B'];
                } else if (!speakerMap[trimmedSpeaker]) {
                    speakerMap[trimmedSpeaker] = speakerNames[speakerIndex % speakerNames.length] || `Speaker ${speakerIndex + 1}`;
                    speakerIndex++;
                    displaySpeaker = speakerMap[trimmedSpeaker];
                } else {
                    displaySpeaker = speakerMap[trimmedSpeaker];
                }

                if (!allSpeakers.includes(displaySpeaker)) {
                    allSpeakers.push(displaySpeaker);
                }
            }
        });

        // Second pass: format HTML with speaker list for consistent voice assignment
        let formattedHtml = '';
        lines.forEach((line, index) => {
            if (line.includes(':')) {
                const [originalSpeaker, ...textParts] = line.split(':');
                const text = textParts.join(':').trim();
                const trimmedSpeaker = originalSpeaker.trim().replace(/<[^>]*>/g, '');

                // Get the display speaker name using the same logic
                let displaySpeaker = trimmedSpeaker;
                if (trimmedSpeaker === 'Osoba A' || trimmedSpeaker === 'Person A') {
                    displaySpeaker = speakerMap['A'];
                } else if (trimmedSpeaker === 'Osoba B' || trimmedSpeaker === 'Person B') {
                    displaySpeaker = speakerMap['B'];
                } else {
                    displaySpeaker = speakerMap[trimmedSpeaker] || displaySpeaker;
                }

                const allSpeakersStr = JSON.stringify(allSpeakers).replace(/"/g, '&quot;');

                formattedHtml += `
                    <div class="dialogue-line">
                        <div class="dialogue-line-header">
                            <span class="dialogue-speaker">${displaySpeaker}:</span>
                            <button
                                class="pronounce-line-button"
                                onclick="window.handleDialogueLinePronunciation('${text.replace(/'/g, "\\'")}', this, '${displaySpeaker}', ${allSpeakersStr})"
                                title="Pronounce ${displaySpeaker}'s line"
                            >
                                🔊
                            </button>
                        </div>
                        <span class="dialogue-text">${text}</span>
                    </div>
                `;
            } else {
                formattedHtml += `<p class="dialogue-narrative">${line}</p>`;
            }
        });

        return formattedHtml;
    };

    // Enhanced pronunciation functionality
    const handlePronounceText = async (text, buttonElement) => {
        if (!ttsService.isReady()) {
            console.warn('TTS service not ready');
            return;
        }

        try {
            // Clean the text for pronunciation (remove speaker names if present)
            let cleanText = text;
            if (text.includes(':')) {
                const parts = text.split(':');
                if (parts.length > 1) {
                    cleanText = parts.slice(1).join(':').trim();
                }
            }

            await ttsService.playPronunciationWithFeedback(cleanText, buttonElement, {
                rate: 0.8,
                onstart: () => {
                    console.log('Started pronunciation');
                },
                onend: () => {
                    console.log('Finished pronunciation');
                },
                onerror: (error) => {
                    console.error('Pronunciation error:', error);
                }
            });
        } catch (error) {
            console.error('Error pronouncing text:', error);
        }
    };

    // Enhanced pronunciation functionality with speaker-specific voices
    const handlePronounceTextWithSpeaker = async (text, buttonElement, speakerName) => {
        if (!ttsService.isReady()) {
            console.warn('TTS service not ready');
            return;
        }

        try {
            // Clean the text for pronunciation (remove speaker names if present)
            let cleanText = text;
            if (text.includes(':')) {
                const parts = text.split(':');
                if (parts.length > 1) {
                    cleanText = parts.slice(1).join(':').trim();
                }
            }

            // Get appropriate voice for this speaker
            const voiceForSpeaker = ttsService.getVoiceForSpeaker(speakerName);

            // Temporarily set the voice for this speaker
            const originalVoice = ttsService.getCurrentVoice();
            ttsService.setVoice(voiceForSpeaker);

            await ttsService.playPronunciationWithFeedback(cleanText, buttonElement, {
                rate: 0.8,
                onstart: () => {
                    console.log(`Started pronunciation for ${speakerName} using voice: ${voiceForSpeaker}`);
                },
                onend: () => {
                    console.log('Finished pronunciation');
                    // Restore original voice
                    ttsService.setVoice(originalVoice);
                },
                onerror: (error) => {
                    console.error('Pronunciation error:', error);
                    // Restore original voice on error
                    ttsService.setVoice(originalVoice);
                }
            });
        } catch (error) {
            console.error('Error pronouncing text:', error);
        }
    };

    // Handle pronunciation of entire dialog with different voices
    const handlePronounceEntireDialog = async (content, buttonElement) => {
        if (!ttsService.isReady()) {
            console.warn('TTS service not ready');
            return;
        }

        try {
            const originalText = buttonElement.textContent;
            const originalDisabled = buttonElement.disabled;

            // Update button state
            buttonElement.textContent = '🔊 Playing Dialog...';
            buttonElement.disabled = true;

            // Parse dialog content to extract speakers and lines
            const speakerNames = generateSpeakerNames();
            const speakerMap = {};
            let speakerIndex = 0;

            const lines = content.split('\n').filter(line => line.trim());
            const dialogLines = [];
            const allSpeakers = [];

            // First pass: collect all speakers and dialog lines
            lines.forEach((line) => {
                if (line.includes(':')) {
                    const [originalSpeaker, ...textParts] = line.split(':');
                    const text = textParts.join(':').trim();
                    const cleanText = text.replace(/<[^>]*>/g, '').trim(); // Remove HTML tags
                    const trimmedSpeaker = originalSpeaker.trim().replace(/<[^>]*>/g, '');

                    // Map speaker names consistently
                    let displaySpeaker = trimmedSpeaker;
                    if (trimmedSpeaker === 'Osoba A' || trimmedSpeaker === 'Person A') {
                        if (!speakerMap['A']) {
                            speakerMap['A'] = speakerNames[0] || 'Marko';
                        }
                        displaySpeaker = speakerMap['A'];
                    } else if (trimmedSpeaker === 'Osoba B' || trimmedSpeaker === 'Person B') {
                        if (!speakerMap['B']) {
                            speakerMap['B'] = speakerNames[1] || 'Ana';
                        }
                        displaySpeaker = speakerMap['B'];
                    } else if (!speakerMap[trimmedSpeaker]) {
                        speakerMap[trimmedSpeaker] = speakerNames[speakerIndex % speakerNames.length] || `Speaker ${speakerIndex + 1}`;
                        speakerIndex++;
                        displaySpeaker = speakerMap[trimmedSpeaker];
                    } else {
                        displaySpeaker = speakerMap[trimmedSpeaker];
                    }

                    if (!allSpeakers.includes(displaySpeaker)) {
                        allSpeakers.push(displaySpeaker);
                    }

                    dialogLines.push({
                        speaker: displaySpeaker,
                        text: cleanText
                    });
                }
            });

            // Play the dialog with different voices
            await ttsService.playDialogWithVoices(dialogLines, allSpeakers, {
                rate: 0.8,
                onlinestart: (lineIndex, speaker, voice) => {
                    buttonElement.textContent = `🔊 Playing ${speaker}... (${lineIndex + 1}/${dialogLines.length})`;
                },
                onend: () => {
                    // Restore button state
                    buttonElement.textContent = originalText;
                    buttonElement.disabled = originalDisabled;
                    console.log('Finished playing entire dialog');
                },
                onerror: (error) => {
                    // Restore button state on error
                    buttonElement.textContent = originalText;
                    buttonElement.disabled = originalDisabled;
                    console.error('Error playing dialog:', error);
                }
            });

        } catch (error) {
            console.error('Error pronouncing entire dialog:', error);
            // Restore button state on error
            if (buttonElement) {
                buttonElement.textContent = '🔊 Pronounce Dialogue';
                buttonElement.disabled = false;
            }
        }
    };

    // Enhanced dialogue formatting with proper names and pronunciation
    const formatContentDisplay = (content, contentType) => {
        if (contentType === 'dialogue') {
            // Generate speaker names once for consistency
            const speakerNames = generateSpeakerNames();
            const speakerMap = {};
            let speakerIndex = 0;

            const lines = content.split('\n').filter(line => line.trim());

            // First pass: collect all speakers for consistent voice assignment
            const allSpeakers = [];
            lines.forEach((line) => {
                if (line.includes(':')) {
                    const [originalSpeaker] = line.split(':');
                    const trimmedSpeaker = originalSpeaker.trim();

                    let displaySpeaker = trimmedSpeaker;
                    if (trimmedSpeaker === 'Osoba A' || trimmedSpeaker === 'Person A') {
                        if (!speakerMap['A']) {
                            speakerMap['A'] = speakerNames[0] || 'Marko';
                        }
                        displaySpeaker = speakerMap['A'];
                    } else if (trimmedSpeaker === 'Osoba B' || trimmedSpeaker === 'Person B') {
                        if (!speakerMap['B']) {
                            speakerMap['B'] = speakerNames[1] || 'Ana';
                        }
                        displaySpeaker = speakerMap['B'];
                    } else if (!speakerMap[trimmedSpeaker]) {
                        speakerMap[trimmedSpeaker] = speakerNames[speakerIndex % speakerNames.length] || `Speaker ${speakerIndex + 1}`;
                        speakerIndex++;
                        displaySpeaker = speakerMap[trimmedSpeaker];
                    } else {
                        displaySpeaker = speakerMap[trimmedSpeaker];
                    }

                    if (!allSpeakers.includes(displaySpeaker)) {
                        allSpeakers.push(displaySpeaker);
                    }
                }
            });

            return (
                <div className="dialogue-content">
                    {/* Add pronunciation button for entire dialogue */}
                    <div className="dialogue-controls">
                        <button
                            className="pronounce-dialogue-button"
                            onClick={(e) => {
                                handlePronounceEntireDialog(content, e.target);
                            }}
                            title="Pronounce entire dialogue with different voices"
                        >
                            🔊 Pronounce Dialogue
                        </button>
                    </div>

                    {lines.map((line, index) => {
                        if (line.includes(':')) {
                            const [originalSpeaker, ...textParts] = line.split(':');
                            const text = textParts.join(':').trim();
                            const trimmedSpeaker = originalSpeaker.trim();

                            // Get the display speaker name using the same logic as first pass
                            let displaySpeaker = trimmedSpeaker;
                            if (trimmedSpeaker === 'Osoba A' || trimmedSpeaker === 'Person A') {
                                displaySpeaker = speakerMap['A'];
                            } else if (trimmedSpeaker === 'Osoba B' || trimmedSpeaker === 'Person B') {
                                displaySpeaker = speakerMap['B'];
                            } else {
                                displaySpeaker = speakerMap[trimmedSpeaker] || displaySpeaker;
                            }

                            return (
                                <div key={index} className="dialogue-line">
                                    <div className="dialogue-line-header">
                                        <span className="dialogue-speaker">{displaySpeaker}:</span>
                                        <button
                                            className="pronounce-line-button"
                                            onClick={(e) => {
                                                // Get consistent voice for this speaker using dialog speakers list
                                                const voiceForSpeaker = ttsService.getVoiceForDialogSpeaker(displaySpeaker, allSpeakers);
                                                const originalVoice = ttsService.getCurrentVoice();
                                                ttsService.setVoice(voiceForSpeaker);

                                                ttsService.playPronunciationWithFeedback(text, e.target, {
                                                    rate: 0.8,
                                                    onstart: () => {
                                                        console.log(`Started pronunciation for ${displaySpeaker} using voice: ${voiceForSpeaker}`);
                                                    },
                                                    onend: () => {
                                                        console.log('Finished pronunciation');
                                                        ttsService.setVoice(originalVoice);
                                                    },
                                                    onerror: (error) => {
                                                        console.error('Pronunciation error:', error);
                                                        ttsService.setVoice(originalVoice);
                                                    }
                                                }).catch(error => {
                                                    console.error('Error pronouncing text:', error);
                                                    ttsService.setVoice(originalVoice);
                                                });
                                            }}
                                            title={`Pronounce ${displaySpeaker}'s line`}
                                        >
                                            🔊
                                        </button>
                                    </div>
                                    <span className="dialogue-text">{text}</span>
                                </div>
                            );
                        }
                        return <p key={index} className="dialogue-narrative">{line}</p>;
                    })}
                </div>
            );
        }

        // For other content types, split into paragraphs with pronunciation option
        const paragraphs = content.split('\n\n').filter(p => p.trim());
        return (
            <div className="formatted-content">
                {contentType !== 'article' && (
                    <div className="content-controls">
                        <button
                            className="pronounce-content-button"
                            onClick={(e) => {
                                const fullText = paragraphs.join('. ');
                                handlePronounceText(fullText, e.target);
                            }}
                            title="Pronounce entire content"
                        >
                            🔊 Pronounce Content
                        </button>
                    </div>
                )}
                {paragraphs.map((paragraph, index) => (
                    <div key={index} className="content-paragraph">
                        <p>{paragraph}</p>
                        <button
                            className="pronounce-paragraph-button"
                            onClick={(e) => handlePronounceText(paragraph, e.target)}
                            title="Pronounce this paragraph"
                        >
                            🔊
                        </button>
                    </div>
                ))}
            </div>
        );
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
