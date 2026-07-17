# Discord Bot Manager

A modern CLI + Web tool for managing Python-based Discord bots.

## Features

- **Bot Creation** — Creates new bots from the `templatebot.py` template
- **Import Existing Bots** — Upload your own `.py` bot files with drag-and-drop; auto-installs dependencies
- **Replace Bot Files** — Update any bot's source code by uploading a new file (keeps config & token)
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

# Import an existing bot from file
python3 manager.py import mybot /path/to/bot.py --token TOKEN --requirements /path/to/requirements.txt

# Get Discord invite link for a bot
python3 manager.py invite mybot
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

## Importing Your Own Bots

You can upload your own Python bot files instead of using the template.

### Via Web Interface
1. Click **Import Bot** in the top navbar
2. Enter a bot name
3. Drag & drop your `.py` file (or click to browse)
4. Optionally add a `requirements.txt` and Discord token
5. Click **Import** — dependencies are auto-installed

Imported bots appear with an `IMPORTED` badge and support all management features (start, stop, monitor, logs, edit, replace, git push).

You can also **replace** any bot's source file later via the **Replace File** button on its card — this is useful for updating custom bots without losing configuration.

### Via CLI
```bash
python3 manager.py import mybot ./my_bot.py --token TOKEN --requirements ./requirements.txt
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
