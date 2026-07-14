# JARVIS Pro v3.0

**Production-Ready AI Assistant with GUI, Voice, Memory & Automation**

## Features

### 🤖 AI Intelligence
- **Dual AI Providers**: Gemini (primary) + OpenAI (fallback)
- **Automatic Fallback**: Seamless switching between providers
- **Conversation Memory**: Persistent SQLite database
- **Context Awareness**: Full conversation history support

### 🎙️ Voice Processing
- **Wake Word Detection**: "Jarvis" trigger recognition
- **Continuous Listening**: Background voice input
- **Text-to-Speech**: Edge TTS with background threading
- **Noise Reduction**: Automatic ambient noise adjustment
- **Microphone Auto-Detection**: Smart device selection

### 🖥️ Modern GUI
- **Dark Theme**: Futuristic dark UI with blue accents
- **Real-time Chat**: Live conversation display
- **Status Indicators**: AI provider, microphone, internet status
- **Responsive Design**: 1200x700 default, fully resizable
- **Voice Integration**: One-click voice input

### 🔍 Web Search
- **Automatic Detection**: Identifies search queries
- **SerpAPI Integration**: Fast, accurate results
- **GUI Display**: Results shown inline
- **AI Context**: Search results passed to AI for better answers

### 💾 Memory System
- **SQLite Database**: Reliable persistence
- **Conversation History**: Full message logging
- **User Profile**: Preferences and notes
- **Auto-Cleanup**: Old data removed after 90 days

### 🤖 Automation
- **App Control**: Open applications and websites
- **File Management**: List, create, delete files
- **System Monitoring**: CPU, RAM, disk usage
- **Screenshot Capture**: Vision-based automation
- **Clipboard Manager**: Copy/paste operations
- **Mouse/Keyboard**: Simulate user input

### 📝 Coding Assistant
- **Code Generation**: Write functions, scripts, apps
- **File Editing**: Create and modify code files
- **Debugging**: Analyze and fix code
- **Project Generation**: Website, desktop app, API scaffolding

### 🔒 Security
- **Command Denylist**: Blocked dangerous commands (rm, shutdown, etc.)
- **Safe Execution**: Sandboxed automation tasks
- **API Key Protection**: Environment variable based
- **Error Handling**: Graceful failure modes

## Installation

### Prerequisites
- Python 3.12+
- pip package manager
- PortAudio (for audio processing)

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/nawaz890-star/Jarvis-.git
   cd Jarvis-
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
   
   Required:
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - `OPENAI_API_KEY`: Get from [OpenAI Dashboard](https://platform.openai.com/api-keys)
   
   Optional:
   - `SEARCH_API_KEY`: Get from [SerpAPI](https://serpapi.com/) for web search

## Usage

### GUI Mode (Default)
```bash
python main.py
```

### CLI Mode
```bash
python main.py --cli
```

### Voice-Only Mode
```bash
python main.py --voice
```

### Debug Mode
```bash
python main.py --debug
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `voice` | Enter voice input mode |
| `memory` | View recent conversation history |
| `clear` | Clear all conversation history |
| `exit` | Quit JARVIS |

## Configuration

Edit `.env` file to customize:

```env
# Assistant
ASSISTANT_NAME=Jarvis
USER_NAME=User

# Voice
VOICE_NAME=en-US-GuyNeural
WAKE_WORD=jarvis
ENABLE_WAKE_WORD=true
MIC_DEVICE_INDEX=0

# Memory
MEMORY_MAX_ITEMS=500
MEMORY_TTL_DAYS=90

# Features
AUTO_WEB_SEARCH_ENABLE=true
DEBUG_MODE=false
```

## Architecture

### Core Modules

```
core/
├── ai_engine.py          # Gemini/OpenAI integration
├── memory.py             # SQLite conversation storage
├── search_engine.py      # Web search via SerpAPI
├── voice_manager.py      # Speech recognition & TTS
└── automation.py         # System automation tasks

gui/
└── main_window.py        # Dark-themed tkinter GUI

tests/
├── test_ai_engine.py
├── test_memory.py
└── ...

main.py                  # Entry point
config.py               # Configuration management
```

### Data Flow

```
User Input (Text/Voice)
    ↓
[GUI / Voice Manager]
    ↓
[Memory - Load History]
    ↓
[Search Engine - Check Intent]
    ↓
[AI Engine - Generate Response]
    ↓
[Memory - Save Conversation]
    ↓
Output (Display + Speak)
```

## Performance

- **GUI Responsiveness**: All I/O operations in background threads
- **Voice Processing**: Async TTS generation
- **AI Requests**: Timeout protection (60s)
- **Database**: Indexed queries, auto-cleanup
- **Memory**: Capped at 500 conversations

## Troubleshooting

### GUI Not Starting
```bash
pip install customtkinter pillow
# Or use CLI mode: python main.py --cli
```

### Microphone Not Detected
```bash
python main.py --debug
# Check logs for MIC_DEVICE_INDEX suggestions
```

### API Errors
- Verify API keys in `.env`
- Check internet connection
- Ensure API quota not exceeded

### Audio Issues
- Install PortAudio: `brew install portaudio` (macOS) or `apt-get install portaudio19-dev` (Linux)
- Test microphone: `python -c "import speech_recognition; sr.Microphone.list_microphone_indexes()"`

## Development

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
black . --line-length 100
flake8 . --max-line-length 100
mypy . --ignore-missing-imports
```

## Roadmap

- [ ] Plugin system
- [ ] Multi-language support
- [ ] RAG (Retrieval-Augmented Generation)
- [ ] Custom model fine-tuning
- [ ] Desktop app packaging
- [ ] Mobile companion app

## License

MIT License - See LICENSE file

## Support

- 📖 [Documentation](https://github.com/nawaz890-star/Jarvis-/wiki)
- 🐛 [Report Issues](https://github.com/nawaz890-star/Jarvis-/issues)
- 💬 [Discussions](https://github.com/nawaz890-star/Jarvis-/discussions)

## Credits

Built with:
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI
- [Google Generative AI](https://ai.google.dev/) - Gemini
- [OpenAI](https://openai.com) - GPT
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Voice input
- [Edge TTS](https://github.com/rany2/edge-tts) - Voice output

---

**JARVIS Pro v3.0** - Made with ❤️ for productive AI assistance
