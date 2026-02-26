<!-- PROJECT_NAME -->

<p align="right">
  <a href="https://github.com/nashobabrook/ai-diary/blob/main/README_CN.md">中文</a>
</p>

<p align="center">
  <img src="docs/images/logo.png" alt="编年 Logo" width="200"/>
</p>

<h1 align="center">编年 (BianNian)</h1>

<p align="center">
  <em>一个人就是一本<br/></em>
</p>

<p align="center">
  <a href="https://github.com/nashobabrook/ai-diary/releases">
    <img src="https://img.shields.io/github/v/release/nashobabrook/ai-diary?style=flat&color=4F46E5" alt="Release">
  </a>
  <a href="https://github.com/nashobabrook/ai-diary/stargazers">
    <img src="https://img.shields.io/github/stars/nashobabrook/ai-diary?style=flat&color=4F46E5" alt="Stars">
  </a>
  <a href="https://github.com/nashobabrook/ai-diary/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/nashobabrook/ai-diary?style=flat" alt="License">
  </a>
</p>

> AI-Powered Personal Diary: Chat to record your daily life, automatically generate journal entries

---

## Features

- **🤖 AI Conversation Recording** - naturally record your daily life through friendly chat
- **📝 Auto Journal Generation** - AI transforms conversations into well-written diary entries
- **🔍 Intelligent Search** - Multi-dimensional relevance ranking to quickly find historical records
- **🎨 Personalized Writing Style** - AI learns and mimics your unique writing style
- **💾 Local Storage** - All data stored locally on your filesystem, privacy protected
- **📊 Mood Analysis** - Automatic mood tracking with 5-level emotion assessment
- **🏷️ Smart Tagging** - Auto-extract tags from conversations
- **📅 Calendar View** - Visualize historical diaries and mood trajectories
- **✏️ Diary Editing** - Edit and refine AI-generated content anytime

---

## Screenshots

| Chat | Calendar |
|------|----------|
| <img src="docs/images/chat.png" width="400"/> | <img src="docs/images/calendar.png" width="400"/> |

| LLM Config | Writing Style |
|------------|---------------|
| <img src="docs/images/llm.png" width="400"/> | <img src="docs/images/wite_style.png" width="400"/> |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- [OpenAI](https://platform.openai.com/) or [MiniMax](https://platform.minimaxi.com/) API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/nashobabrook/ai-diary.git
cd ai-diary

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd web
npm install
cd ..
```

### Run

#### Option 1: One-Click Start (Recommended)

```bash
# macOS / Linux
./start.sh

# Windows (Git Bash / WSL)
./start.sh
```

#### Option 2: Manual Start

```bash
# Terminal 1 - Start backend (port 8080)
python3 src/llm.py

# Terminal 2 - Start frontend
cd web
npm run dev
```

Visit http://localhost:5173 to get started.

---

## Configuration

### 1. LLM Provider Setup

First, configure your AI provider in the Settings page:

1. Click 「Settings」 in navigation
2. Enter your provider info:
   - **Provider**: Any name (e.g., "OpenAI", "Qwen", "Zhipu")
   - **Base URL**: API endpoint (see table below)
   - **API Key**: Your API key
   - **Model**: Model name (see table below)

### 2. Supported LLM Providers

| Provider | Base URL | Example Models | Function Call |
|----------|-----------|----------------|---------------|
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4`, `gpt-3.5-turbo` | ✅ |
| **Azure OpenAI** | `https://{your-resource}.openai.azure.com/` | `gpt-4`, `gpt-35-turbo` | ✅ |
| **MiniMax** | `https://api.minimaxi.com/v1` | `abab6.5s-chat`, `abab6.5g-chat` | ✅ (Anthropic format) |
| **Qwen (通义千问)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-max`, `qwen-plus` | ✅ |
| **Zhipu (智谱)** | `https://open.bigmodel.cn/api/paas/v4` | `glm-4`, `glm-3-turbo` | ✅ |
| **Ollama (Local)** | `http://localhost:11434/v1` | `llama3`, `qwen2`, `mistral` | ⚠️ Depends on model |
| **LM Studio (Local)** | `http://localhost:1234/v1` | Any loaded model | ⚠️ Depends on model |

> **Note**: Function Call requires the model to support it. Most cloud models (OpenAI, MiniMax, Qwen, Zhipu) support it. Local models (Ollama, LM Studio) depend on the specific model.

### 3. Writing Style (Optional)

Personalize your diary by setting your writing style:

1. Go to Settings page
2. Click 「Analyze Writing Style」 to let AI learn from your past entries
3. Or manually edit the `writing_style.md` file in your data directory

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| FastAPI | Web Framework |
| OpenAI SDK | LLM Interface |
| Pydantic | Data Validation |

### Frontend

| Technology | Purpose |
|------------|---------|
| React 18 | UI Framework |
| Vite | Build Tool |
| React Router | Routing |
| Day.js | Date Handling |

---

## Project Structure

```
ai-diary/
├── src/                    # Backend code
│   ├── llm.py             # FastAPI entry point
│   ├── agent.py           # Core Agent logic
│   ├── function_tools.py  # Function Call tools
│   ├── retrieval/         # Search module
│   ├── user_profile.py    # User profile management
│   └── writing_style.py   # Writing style manager
│
├── web/                   # Frontend code
│   ├── src/
│   │   ├── pages/        # Page components
│   │   │   ├── ChatPage.jsx
│   │   │   ├── CalendarPage.jsx
│   │   │   ├── StatsPage.jsx
│   │   │   └── ConfigPage.jsx
│   │   └── components/   # Reusable components
│   └── ...
│
├── bianNian/              # AI personality config
│   ├── diary-soul.md     # Character definition
│   └── dialogue.md       # Dialogue strategy
│
├── data/                  # Data storage (local, auto-created)
│   ├── diaries/           # Diary JSON files
│   ├── conversations/    # Conversation JSONL files
│   └── index/            # Search index
│
├── config/                # User configuration (auto-created)
├── start.sh               # One-click startup script
└── README.md              # This file
```

---

## Data Storage

All data is stored locally in the `data/` directory:

| Directory | Description |
|-----------|-------------|
| `data/default/diaries/` | Generated diary files |
| `data/default/conversations/` | Chat history |
| `data/default/index/` | Search index |
| `data/default/user.md` | User profile |
| `data/default/writing_style.md` | Custom writing style |

---

## API Documentation

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send chat message |
| `/diary/{date}` | GET | Get diary by date |
| `/diary/{date}` | PUT | Update diary content |
| `/diary/generate` | POST | Generate diary |
| `/calendar/{year}/{month}` | GET | Get calendar data |
| `/stats` | GET | Get mood statistics |
| `/config/{user_id}` | GET | Get user config |
| `/user/style/{user_id}` | GET/POST | Get/Set writing style |

---

## FAQ

### Q: Is my data secure?

A: Yes! All data is stored locally on your machine. No cloud upload - completely private.

### Q: Which LLM providers are supported?

A: Currently OpenAI and MiniMax are supported. The architecture supports any OpenAI-compatible API.

### Q: How does the writing style work?

A: You can let AI analyze your existing diary entries to learn your style, or manually write your style preferences in `writing_style.md`.

### Q: Can I edit the AI-generated diary?

A: Yes! Click the 「Edit」 button on any diary to modify content, mood, and tags.

### Q: How to backup?

A: Simply backup the entire `data/` directory.

### Q: Does it work on Windows?

A: Yes! Use [Git Bash](https://git-scm.com/download/win) or [WSL](https://docs.microsoft.com/en-us/windows/wsl/) to run the start script.

---

## License

MIT License - See [LICENSE](./LICENSE) for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/nashobabrook">nashobabrook</a>
</p>
