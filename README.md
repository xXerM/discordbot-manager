# Discord Bot Manager

A modern CLI + Web tool for managing Python-based Discord bots.

## Features

- **Bot Creation** — Creates new bots from the `templatebot.py` template
- **Start / Stop / Restart** — Manage bot processes
- **Code Editing** — Edit bot files via CLI or web interface
- **Token Management** — Update tokens in `.env` files
- **Dependency Management** — Auto-installs packages from `requirements.txt`
- **Git Integration** — `git init`, `commit`, and `push` bot directories
- **Live Monitoring** — Track RAM, CPU, storage, and uptime
- **Auto-Restart** — Automatically restarts bots on unexpected crashes
- **Logging** — Separate log files for each bot
- **Web Dashboard** — Modern, mobile-friendly dark theme UI powered by Flask
- **CLI Interface** — Interactive menu or direct argument commands

## Installation

```bash
git clone https://github.com/user/bot-manager-python.git
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

### Terminal (Command Line)

```bash
# Create a bot
python3 manager.py create mybot YOUR_DISCORD_TOKEN

# Start a bot
python3 manager.py start mybot

# Stop a bot
python3 manager.py stop mybot

# Restart a bot
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

# Git push
python3 manager.py git-push mybot -m "update"

# Install dependencies
python3 manager.py install mybot
```

## File Structure

```
bot-manager-python/
├── manager.py            # CLI interface (interactive + argument-based)
├── manager_core.py       # Core management logic
├── web_app.py            # Flask web application
├── templatebot.py        # Bot template
├── requirements.txt      # Dependencies
├── bot_config.json       # Bot configuration (auto-generated)
├── bots/                 # Created bot directories
├── logs/                 # Bot log files
├── templates/
│   └── index.html        # Web interface HTML
└── static/               # Static files
```

## templatebot.py

The template is built with `discord.py` and includes the following commands:

| Command | Description |
|---------|-------------|
| `^test` | Bot latency and status |
| `^ping` | Ping test |
| `^komutlar` | Command list |
| `^uptime` | API and message latency |

When creating a bot, this template is copied and the token is written to the `.env` file. To change the prefix, add `BOT_PREFIX=!` to the `.env` file. You can customize the template by editing `templatebot.py`.
