# JARVIS Pro v3.0 - Installation Guide

## System Requirements

- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.12 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB free space
- **Audio**: Microphone and speakers

## Step-by-Step Installation

### 1. Download Python 3.12

**Windows**:
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

**macOS**:
```bash
brew install python@3.12
```

**Linux**:
```bash
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv
```

### 2. Clone Repository

```bash
git clone https://github.com/nawaz890-star/Jarvis-.git
cd Jarvis-
```

### 3. Create Virtual Environment

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Platform-Specific Setup

**Windows**: No additional setup needed

**macOS**:
```bash
brew install portaudio
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install portaudio19-dev
sudo apt-get install python3-tk
```

**Linux (Fedora/RHEL)**:
```bash
sudo dnf install portaudio-devel
sudo dnf install python3-tkinter
```

### 5. Get API Keys

#### Google Gemini API
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Create new API key
4. Copy the key

#### OpenAI GPT API
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new API key
3. Copy the key

#### SerpAPI (Optional - for web search)
1. Go to [SerpAPI](https://serpapi.com/)
2. Sign up for free account
3. Copy your API key

### 6. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your favorite text editor:

```env
# Required
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional
SEARCH_API_KEY=your_serpapi_key_here

# Customize
ASSISTANT_NAME=Jarvis
USER_NAME=YourName
```

### 7. Test Installation

```bash
python main.py --cli
```

Type a simple message like "Hello" and verify you get a response.

## Troubleshooting

### "ModuleNotFoundError: No module named..."

```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Microphone Not Found

```bash
# List available microphones
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_indexes())"

# Update MIC_DEVICE_INDEX in .env
```

### Audio Not Working

**Windows**:
- Check Volume settings
- Ensure speakers are connected

**macOS**:
```bash
# Update audio drivers
brew upgrade portaudio
```

**Linux**:
```bash
# Check audio setup
alsamixer

# Reinstall audio libraries
sudo apt-get install --reinstall alsa-utils
```

### GUI Not Starting

**Option 1**: Update tkinter
```bash
# macOS
brew install python-tk@3.12

# Linux
sudo apt-get install python3.12-tk
```

**Option 2**: Use CLI mode
```bash
python main.py --cli
```

### API Key Errors

1. Verify key is correct (no extra spaces)
2. Check key has proper permissions
3. Ensure API account has credits
4. Test key in browser if possible

## Updating

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## Uninstall

```bash
# Deactivate virtual environment
deactivate

# Remove directory
rm -rf Jarvis-  # Linux/macOS
rmdir /s Jarvis-  # Windows
```

## Next Steps

1. Read [README.md](README.md) for feature overview
2. Check [Configuration](README.md#configuration) for customization
3. Try different modes: `python main.py --help`
4. Join [discussions](https://github.com/nawaz890-star/Jarvis-/discussions)

## Support

If you encounter issues:

1. Check the [Troubleshooting](README.md#troubleshooting) section
2. Run with debug: `python main.py --debug`
3. Share logs in [Issues](https://github.com/nawaz890-star/Jarvis-/issues)

---

**Happy coding with JARVIS!** 🚀
