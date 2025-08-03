# Text-to-Speech Integration Proposal

## Serbian Vocabulary App

### 📋 **Project Overview**

**Feature**: Text-to-Speech (TTS) integration for Serbian vocabulary pronunciation  
**Timeline**: Week 1 implementation  
**Goal**: Enable audio pronunciation playback for vocabulary words with minimal cost and easy integration

---

## 🎯 **Requirements Analysis**

### **Core Requirements**

- ✅ Serbian language support
- ✅ High-quality pronunciation
- ✅ Low latency for real-time playback
- ✅ Cost-effective (preferably free tier)
- ✅ Easy API integration
- ✅ Audio file caching capability
- ✅ Multiple voice options (male/female)

### **Technical Requirements**

- RESTful API or SDK integration
- Audio format: MP3 or WAV
- Response time: < 2 seconds
- Caching strategy for performance
- Error handling and fallback options

---

## 🔍 **Market Research: TTS Solutions**

### **1. Google Cloud Text-to-Speech** ⭐⭐⭐⭐

**Cost**: $4.00 per 1 million characters (free tier: 1M chars/month)  
**Serbian Support**: ✅ Full support  
**Integration**: REST API, multiple SDKs  
**Pros**:

- Excellent Serbian pronunciation quality
- Multiple voice options (male/female)
- Well-documented API
- Reliable and scalable
- Free tier available

**Cons**:

- Requires Google Cloud account setup
- Pay-as-you-go after free tier
- API key management needed

**Integration Difficulty**: Easy  
**Recommended**: **YES** - Best quality and free tier

---

### **2. Microsoft Azure Speech Service** ⭐⭐⭐⭐

**Cost**: $16.00 per 1 million characters (free tier: 500K chars/month)  
**Serbian Support**: ✅ Full support  
**Integration**: REST API, Speech SDK  
**Pros**:

- High-quality Serbian voices
- Neural TTS technology
- Good documentation
- Free tier available

**Cons**:

- Higher cost than Google
- Smaller free tier
- Requires Azure account

**Integration Difficulty**: Easy  
**Recommended**: **YES** - Good alternative to Google

---

### **3. Amazon Polly** ⭐⭐⭐

**Cost**: $4.00 per 1 million characters (free tier: 5M chars/month)  
**Serbian Support**: ❌ Limited support  
**Integration**: AWS SDK, REST API  
**Pros**:

- Large free tier (5M chars)
- Good documentation
- AWS ecosystem integration

**Cons**:

- Limited Serbian voice options
- May not have optimal Serbian pronunciation
- AWS account required

**Integration Difficulty**: Medium  
**Recommended**: **NO** - Limited Serbian support

---

### **4. ElevenLabs** ⭐⭐⭐⭐

**Cost**: $5.00 per 1 million characters (free tier: 10K chars/month)  
**Serbian Support**: ✅ Custom voice cloning possible  
**Integration**: REST API  
**Pros**:

- Very high-quality voices
- Voice cloning capabilities
- Large free tier for testing
- Natural-sounding speech

**Cons**:

- Limited Serbian voices out-of-box
- Requires voice cloning for optimal Serbian
- Higher cost for production

**Integration Difficulty**: Easy  
**Recommended**: **MAYBE** - For premium quality, but requires setup

---

### **5. Web Speech API (Browser Native)** ⭐⭐

**Cost**: Free  
**Serbian Support**: ❌ Limited browser support  
**Integration**: JavaScript API  
**Pros**:

- Completely free
- No API keys needed
- Built into browsers

**Cons**:

- Limited Serbian language support
- Inconsistent across browsers
- Poor pronunciation quality
- No server-side control

**Integration Difficulty**: Easy  
**Recommended**: **NO** - Poor Serbian support

---

### **6. ResponsiveVoice.js** ⭐⭐

**Cost**: Free (with attribution)  
**Serbian Support**: ❌ No Serbian support  
**Integration**: JavaScript library  
**Pros**:

- Free to use
- Easy JavaScript integration
- No API keys required

**Cons**:

- No Serbian language support
- Limited voice quality
- Requires attribution

**Integration Difficulty**: Very Easy  
**Recommended**: **NO** - No Serbian support

---

## 🏆 **Recommended Solution: Google Cloud TTS**

### **Why Google Cloud TTS?**

1. **✅ Best Serbian Support**: Native Serbian voices with excellent pronunciation
2. **✅ Cost-Effective**: $4.00 per 1M characters with 1M free monthly
3. **✅ Easy Integration**: Well-documented REST API and SDKs
4. **✅ Reliable**: Google's infrastructure ensures high availability
5. **✅ Scalable**: Can handle production load easily

### **Cost Analysis**

- **Free Tier**: 1,000,000 characters/month
- **Typical Usage**: ~50,000 characters/month for vocabulary app
- **Cost**: $0/month (well within free tier)
- **Production Scaling**: ~$0.20/month for 50K additional characters

---

## 🛠️ **Implementation Plan**

### **Phase 1: Google Cloud TTS Setup (Day 1-2)**

#### **Step 1: Google Cloud Account Setup**

- Create Google Cloud project
- Enable Text-to-Speech API
- Generate API key
- Set up billing (free tier)

#### **Step 2: Backend Integration**

```python
# Example integration code
import google.cloud.texttospeech as tts

def generate_serbian_audio(text, voice_name="sr-RS-Standard-A"):
    client = tts.TextToSpeechClient()
    
    synthesis_input = tts.SynthesisInput(text=text)
    voice = tts.VoiceSelectionParams(
        language_code="sr-RS",
        name=voice_name,
        ssml_gender=tts.SsmlVoiceGender.FEMALE
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)
    
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content
```

#### **Step 3: Audio Caching System**

- Implement Redis caching for audio files
- Cache strategy: 24-hour TTL for vocabulary words
- File naming: `{word_hash}_{voice}_{language}.mp3`

### **Phase 2: Frontend Integration (Day 3-4)**

#### **Step 1: Audio Player Component**

```javascript
// React component for audio playback
const AudioPlayer = ({ word, audioUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState(null);

  const playAudio = async () => {
    if (!audioUrl) {
      // Generate audio via API call
      const response = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: word, language: 'sr-RS' })
      });
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      setAudio(new Audio(audioUrl));
    }
    
    audio.play();
    setIsPlaying(true);
  };

  return (
    <button onClick={playAudio} disabled={isPlaying}>
      🔊 {isPlaying ? 'Playing...' : 'Play'}
    </button>
  );
};
```

#### **Step 2: Practice Mode Integration**

- Add audio button to vocabulary cards
- Implement audio feedback for correct/incorrect answers
- Add audio-only practice mode

### **Phase 3: Advanced Features (Day 5-7)**

#### **Step 1: Multiple Voice Options**

- Add male/female voice selection
- Implement voice preference settings
- Create voice preview functionality

#### **Step 2: Audio Practice Mode**

- Create listening comprehension exercises
- Add audio-only vocabulary recognition
- Implement audio-based answer validation

#### **Step 3: Performance Optimization**

- Implement audio preloading for common words
- Add loading states and error handling
- Optimize audio file sizes

---

## 📊 **Technical Architecture**

### **Backend Changes**

```
backend/
├── services/
│   └── tts_service.py          # Google TTS integration
├── api/
│   └── tts_endpoints.py        # TTS API endpoints
└── cache/
    └── audio_cache.py          # Audio file caching
```

### **Frontend Changes**

```
frontend/src/
├── components/
│   ├── AudioPlayer.js          # Audio playback component
│   └── AudioPracticeMode.js    # Audio-only practice
├── services/
│   └── audioService.js         # Audio API calls
└── pages/
    └── PracticePage.js         # Updated with audio features
```

### **Database Changes**

```sql
-- Audio cache tracking
CREATE TABLE audio_cache (
    id SERIAL PRIMARY KEY,
    word_hash VARCHAR(64) UNIQUE,
    audio_url VARCHAR(255),
    voice_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

---

## 💰 **Cost Estimation**

### **Monthly Costs**

- **Google Cloud TTS**: $0 (within free tier)
- **Audio Storage**: $0.50 (S3/Cloud Storage)
- **Bandwidth**: $0.20 (audio file delivery)
- **Total**: ~$0.70/month

### **Scaling Costs**

- **10,000 users**: ~$5/month
- **100,000 users**: ~$50/month
- **1,000,000 users**: ~$500/month

---

## 🎯 **Success Metrics**

### **Technical Metrics**

- Audio generation latency: < 2 seconds
- Cache hit rate: > 80%
- Audio quality score: > 4.5/5
- Error rate: < 1%

### **User Engagement Metrics**

- Audio feature adoption: > 60%
- Practice session duration: +20%
- Vocabulary retention: +15%
- User satisfaction: > 4.0/5

---

## 🚀 **Implementation Timeline**

### **Week 1 Breakdown**

- **Day 1-2**: Google Cloud setup and backend integration
- **Day 3-4**: Frontend audio player and practice integration
- **Day 5-7**: Advanced features and optimization

### **Deliverables**

- ✅ Serbian TTS integration with Google Cloud
- ✅ Audio playback in practice modes
- ✅ Audio caching system
- ✅ Multiple voice options
- ✅ Audio-only practice mode

---

## 🔧 **Alternative Solutions (If Google Cloud Fails)**

### **Backup Plan 1: Microsoft Azure**

- Similar quality and pricing
- Easy migration path
- Good Serbian support

### **Backup Plan 2: ElevenLabs**

- Premium quality voices
- Voice cloning for custom Serbian voice
- Higher cost but better quality

### **Backup Plan 3: Hybrid Approach**

- Use Google Cloud for production
- Use Web Speech API as fallback
- Implement graceful degradation

---

## 📝 **Next Steps**

1. **Approve Google Cloud TTS solution**
2. **Set up Google Cloud account and API keys**
3. **Begin backend integration**
4. **Implement frontend audio components**
5. **Test with Serbian vocabulary words**
6. **Deploy and monitor performance**

---

**Proposal Prepared**: February 8, 2025  
**Recommended Solution**: Google Cloud Text-to-Speech  
**Estimated Cost**: $0.70/month (within free tier)  
**Implementation Time**: 1 week  
**Risk Level**: Low
