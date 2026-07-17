# Discord Bot Manager

A modern CLI + Web tool for managing Python-based Discord bots.

## Features

- **Bot Creation** — Creates new bots from the `templatebot.py` template
- **Import Existing Bots** — Upload your own `.py` bot files with drag-and-drop; auto-installs dependencies
- **Replace Bot Files** — Update any bot's source code by uploading a new file (keeps config & token)
- **Start / Stop / Restart** — Manage bot processes with crash detection
- **Code Editing** — Edit bot files via CLI or web interface
- **Token Management** — Update tokens in `.env` files
- **Dependency Management** — Auto-installs packages from `requirements.txt`
- **Git Push & Pull** — `git init`, `commit`, `push`, and `pull` bot repositories
- **Live Monitoring** — Track RAM, CPU, storage, and uptime with auto-restart on crash
- **Logging** — Separate log files for each bot
- **Invite Link Generator** — Generate Discord OAuth2 invite URLs from bot tokens
- **Web Dashboard** — Modern, mobile-friendly dark theme UI with EN/TR language switcher
- **CLI Interface** — Interactive menu or direct argument commands with EN/TR language support
- **Language Support** — Both web and CLI support English (default) and Turkish

## Installation

```bash
git clone https://github.com/xXerM/discordbot-manager.git
cd bot-manager-python
pip install -r requirements.txt
```

## Usage

### Web Interface

```bash
python3 manager.py web
# http://localhost:5000
```

Or directly with Flask:

```bash
python3 web_app.py
```

### Terminal (Interactive)

```bash
python3 manager.py
```

Language can be toggled between English and Turkish from the interactive menu.

### Terminal (Command Line)

```bash
# Create a bot
python3 manager.py create mybot YOUR_DISCORD_TOKEN

# Start / Stop / Restart
python3 manager.py start mybot
python3 manager.py stop mybot
python3 manager.py restart mybot

# Delete a bot
python3 manager.py delete mybot

# List all bots
python3 manager.py list

# Show bot status
python3 manager.py status mybot

# View bot logs
python3 manager.py logs mybot --lines 50

# Edit bot file
python3 manager.py edit mybot

# Git push and pull
python3 manager.py git-push mybot -m "update"
python3 manager.py git-pull mybot --remote origin --branch main

# Install dependencies
python3 manager.py install mybot

# Import an existing bot from file
python3 manager.py import mybot /path/to/bot.py --token TOKEN --requirements /path/to/requirements.txt

# Get Discord invite link for a bot
python3 manager.py invite mybot

# Set CLI language
python3 manager.py lang en   # English (default)
python3 manager.py lang tr   # Turkish
```

## File Structure

```
bot-manager-python/
├── manager.py            # CLI interface (interactive + argument-based, EN/TR)
├── manager_core.py       # Core management logic
├── web_app.py            # Flask web application
├── templatebot.py        # Bot template
├── requirements.txt      # Dependencies
├── bot_config.json       # Bot configuration (auto-generated)
├── bots/                 # Created bot directories
├── logs/                 # Bot log files
├── templates/
│   └── index.html        # Web interface HTML (EN/TR)
└── static/               # Static files
```

## Importing Your Own Bots

You can upload your own Python bot files instead of using the template.

### Via Web Interface
1. Click **Import Bot** in the top navbar
2. Enter a bot name
3. Drag & drop your `.py` file (or click to browse)
4. Optionally add a `requirements.txt` and Discord token
5. Click **Import** — dependencies are auto-installed

Imported bots appear with an `IMPORTED` badge and support all management features (start, stop, monitor, logs, edit, replace file, git push/pull, invite).

You can also **replace** any bot's source file later via the **Replace File** button on its card — this is useful for updating custom bots without losing configuration.

### Via CLI
```bash
python3 manager.py import mybot ./my_bot.py --token TOKEN --requirements ./requirements.txt
```

## Git Integration

Each bot can have its own git repository. The manager supports:

- **git init** — Auto-initialized on first push
- **git push** — Commit and push changes to a remote
- **git pull** — Pull latest updates from a remote (useful for syncing bots across multiple machines)

### Via Web
Each bot card has `↑ Git Push` and `↓ Git Pull` buttons.

### Via CLI
```bash
python3 manager.py git-push mybot -m "update message"
python3 manager.py git-pull mybot --remote origin --branch main
```

## Language Support

Both the web interface and CLI support English (default) and Turkish:

- **Web:** Click the `TR` / `EN` button in the top navbar
- **CLI interactive:** Option `[14] Toggle Language (TR)` / `Dili Değiştir (EN)`
- **CLI command:** `python3 manager.py lang en` or `python3 manager.py lang tr`

Language preference is saved to `bot_config.json` and persists across sessions.

## templatebot.py

The template is built with `discord.py` and includes the following commands:

| Command | Description |
|---------|-------------|
| `^test` | Bot latency and status |
| `^ping` | Ping test |
| `^komutlar` | Command list |
| `^uptime` | API and message latency |

When creating a bot, this template is copied and the token is written to the `.env` file. To change the prefix, add `BOT_PREFIX=!` to the `.env` file. You can customize the template by editing `templatebot.py`.
