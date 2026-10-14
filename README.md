# 🦁 Animal Shorts Generator

Automated pipeline for generating engaging YouTube Shorts about fascinating animals using AI-powered content creation.

## Features

✨ **Fully Automated Pipeline**
- **AI-Powered Content Generation**: LLM-based script creation with topic discovery and deduplication
- **Multi-Modal Media Acquisition**: Prioritized fallback system (Veo Video → Pexels Stock → Generated Images)
- **Professional Audio**: Text-to-Speech narration with ambience and dynamic SFX
- **Optimized Video Assembly**: High-quality editing with captions and timing optimization
- **Direct YouTube Integration**: Automated upload with metadata and scheduling

🔄 **Intelligent Workflow**
- Prevents duplicate content with normalized topic deduplication
- Scheduled generation with configurable time slots
- Graceful fallback mechanisms at each pipeline stage
- Comprehensive error recovery and retry logic

🎬 **Production-Ready**
- Modular architecture for easy maintenance and extension
- Async/concurrent processing for performance
- Detailed logging and error handling
- Tested with diverse animal species

## Architecture

```
animal-shorts-generator/
├── generator.py              # Main pipeline orchestrator
├── single_run.py            # Single execution mode
├── modules/
│   ├── llm_utils.py         # LLM integration (topic, script generation)
│   ├── veo_client.py        # Google Vertex AI video generation
│   ├── image_generator.py   # Image generation with fallbacks
│   ├── audio_generator.py   # TTS + ambience + SFX
│   ├── video_editor.py      # Video assembly & editing
│   ├── youtube_uploader.py  # YouTube upload automation
│   ├── stock_client.py      # Pexels stock footage API
│   └── history_manager.py   # Content deduplication & history
└── assets/                  # Music, SFX templates
```

## Pipeline Stages

1. **Topic Discovery** → LLM suggests unique animal topic
2. **Script Generation** → Creates structured narrative with scenes
3. **Media Acquisition** → Veo → Pexels → Image Generation (automatic fallback)
4. **Audio Synthesis** → Narration + ambience + SFX composition
5. **Video Assembly** → Combines visuals, audio, captions, timing
6. **YouTube Upload** → Publishes with metadata and tags
7. **History Tracking** → Records metadata and prevents duplicates

## Installation

### Requirements
- Python 3.8+
- Google Cloud credentials (Vertex AI access)
- YouTube Data API credentials
- API keys: Pexels, LLM provider

### Setup

```bash
# Clone repository
git clone https://github.com/your-username/animal-shorts-generator.git
cd animal-shorts-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_API_KEY=your_api_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# API Keys
PEXELS_API_KEY=your_pexels_key
YOUTUBE_API_KEY=your_youtube_key

# Google Cloud (for Vertex AI)
GOOGLE_APPLICATION_CREDENTIALS=service_account.json
```

## Usage

### Automated Continuous Generation

```bash
python generator.py
```

Runs indefinitely with scheduled uploads at: 02:00, 10:00, 14:00, 17:00, 20:00, 23:00 UTC

### Single Video Generation

```bash
python single_run.py
```

Generates one video and exits (useful for testing)

### Custom Topic

```bash
python generator.py --once "Blue Ringed Octopus"
```

## Key Optimizations

- **Deduplication Engine**: Normalized alphanumeric comparison prevents topic repeats
- **Smart Fallbacks**: Multi-tier media acquisition ensures no failures
- **Async Processing**: Concurrent module execution for speed
- **Memory Efficiency**: Cleanup between runs, modular loading
- **Pre-sorted Scheduling**: Eliminates redundant computations

## Development

### Project Structure
- **Modular Design**: Each module is independent and testable
- **Error Handling**: Comprehensive try-catch with graceful degradation
- **Logging**: Detailed console output for monitoring
- **Type Safety**: Clear input/output contracts

### Testing

Test individual modules:
```bash
python test_description.py      # Script generation
python test_viral_features.py   # Audio features
python test_video_fix.py        # Video assembly
```

## Configuration

Edit `generator.py` to customize:
- `TARGET_HOURS`: Schedule time slots
- `FALLBACK_PROVIDERS`: Media acquisition priority
- `QUALITY_SETTINGS`: Video resolution, audio bitrate

## Known Limitations

- Vertex AI Veo requires quota availability
- YouTube uploads subject to API quota limits
- Generated images depend on external providers (Pollinations, Picsum)
- LLM creativity depends on model selection and prompting

## Future Roadmap

- [ ] Multi-language support
- [ ] Custom music library integration
- [ ] Analytics dashboard for view tracking
- [ ] Topic trending analysis
- [ ] Batch processing interface
- [ ] Custom voiceover support

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes with clear messages
4. Push and create a Pull Request

## License

MIT License - See LICENSE file for details

## Author

Created with 🎬 by [Your Name]

---

**Built with Code Generation & AI Automation** • Optimized for production use
