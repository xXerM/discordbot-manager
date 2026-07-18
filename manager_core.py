import os
import sys
import json
import shutil
import subprocess
import time
import psutil
import threading
import signal
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
BOTS_DIR = BASE_DIR / "bots"
TEMPLATE_FILE = BASE_DIR / "templatebot.py"
CONFIG_FILE = BASE_DIR / "bot_config.json"
LOGS_DIR = BASE_DIR / "logs"

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

_config_lock = threading.Lock()


def load_config():
    with _config_lock:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
        return {"bots": {}}


def save_config(config):
    with _config_lock:
        CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def get_log_path(bot_name):
    return LOGS_DIR / f"{bot_name}.log"


def log(bot_name, message):
    path = get_log_path(bot_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(f"[{bot_name}] {message}")


def create_bot(name, token):
    if not TEMPLATE_FILE.exists():
        return False, "template-bot.py not found"

    bot_dir = BOTS_DIR / name
    if bot_dir.exists():
        return False, f"'{name}' already exists"

    bot_dir.mkdir(parents=True, exist_ok=True)
    dest = bot_dir / "bot.py"
    shutil.copy2(TEMPLATE_FILE, dest)

    env_file = bot_dir / ".env"
    env_file.write_text(f'DISCORD_TOKEN={token}\n')

    requirements = bot_dir / "requirements.txt"
    requirements.write_text("discord.py\naiohttp\npython-dotenv\n")

    config = load_config()
    config["bots"][name] = {
        "token": token,
        "created_at": datetime.now().isoformat(),
        "status": "stopped",
        "pid": None,
        "directory": str(bot_dir),
        "auto_restart": False,
        "auto_git_pull": False,
        "source": "template"
    }
    save_config(config)

    log(name, "Bot created")
    return True, "Bot created successfully"


def install_deps(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"
    bot_dir = Path(config["bots"][bot_name]["directory"])
    req_file = bot_dir / "requirements.txt"
    if not req_file.exists():
        return False, "requirements.txt not found"
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        try:
            result = subprocess.run(cmd, cwd=str(bot_dir), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            result = subprocess.run(cmd + ["--break-system-packages"], cwd=str(bot_dir), check=True, capture_output=True, text=True)
        log(bot_name, "Dependencies installed")
        return True, "Dependencies installed successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Installation error: {e.stderr}"


def start_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_info = config["bots"][bot_name]
    if bot_info["status"] == "running":
        return False, "Bot is already running"

    bot_dir = Path(bot_info["directory"])
    bot_script = bot_dir / "bot.py"
    if not bot_script.exists():
        return False, "bot.py not found"

    if not bot_info.get("token"):
        return False, "Bot token not found"

    env = os.environ.copy()
    env["DISCORD_TOKEN"] = bot_info["token"]

    env_file = bot_dir / ".env"
    if not env_file.exists():
        env_file.write_text(f"DISCORD_TOKEN={bot_info['token']}\n")

    log_path = get_log_path(bot_name)
    try:
        with open(log_path, "a") as log_file:
            log_file.write(f"\n--- Bot starting: {datetime.now().isoformat()} ---\n")
            log_file.flush()
            process = subprocess.Popen(
                [sys.executable, str(bot_script)],
                cwd=str(bot_dir),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL
            )

        time.sleep(3)

        alive = False
        try:
            proc = psutil.Process(process.pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                alive = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        if not alive:
            bot_info["status"] = "stopped"
            bot_info["pid"] = None
            save_config(config)
            log_lines = get_bot_logs(bot_name, 5)
            error_info = log_lines[-1] if log_lines else "Unknown error"
            log(bot_name, f"Bot failed to start (process died)")
            return False, f"Bot failed to start. Last log: {error_info}"

        bot_info["pid"] = process.pid
        bot_info["status"] = "running"
        save_config(config)

        log(bot_name, f"Bot started (PID: {process.pid})")
        return True, f"Bot started (PID: {process.pid})"
    except Exception as e:
        return False, f"Start error: {str(e)}"


def stop_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_info = config["bots"][bot_name]
    if bot_info["status"] != "running" or not bot_info["pid"]:
        return False, "Bot is not running"

    pid = bot_info["pid"]
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=10)
    except psutil.NoSuchProcess:
        pass
    except psutil.TimeoutExpired:
        try:
            proc = psutil.Process(pid)
            proc.kill()
        except psutil.NoSuchProcess:
            pass

    bot_info["status"] = "stopped"
    bot_info["pid"] = None
    save_config(config)
    log(bot_name, "Bot stopped")
    return True, "Bot stopped"


def restart_bot(bot_name):
    stop_bot(bot_name)
    time.sleep(1)
    return start_bot(bot_name)


def delete_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    if config["bots"][bot_name]["status"] == "running":
        stop_bot(bot_name)

    bot_dir = Path(config["bots"][bot_name]["directory"])
    if bot_dir.exists():
        shutil.rmtree(bot_dir)

    del config["bots"][bot_name]
    save_config(config)

    log_path = get_log_path(bot_name)
    if log_path.exists():
        log_path.unlink()

    log(bot_name, "Bot deleted")
    return True, "Bot deleted"


def git_push(bot_name, commit_message=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    if not (bot_dir / ".git").exists():
        subprocess.run(["git", "init"], cwd=str(bot_dir), capture_output=True)

    try:
        subprocess.run(["git", "add", "."], cwd=str(bot_dir), check=True, capture_output=True)
        msg = commit_message or f"Bot update: {datetime.now().isoformat()}"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(bot_dir), check=False, capture_output=True)
        result = subprocess.run(["git", "push"], cwd=str(bot_dir), capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Push error: {result.stderr}"
        log(bot_name, "Git push completed")
        return True, "Git push successful"
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e.stderr.decode() if e.stderr else str(e)}"


def git_pull(bot_name, remote="origin", branch=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    if not (bot_dir / ".git").exists():
        return False, "No git repository found for this bot"

    try:
        if branch:
            result = subprocess.run(["git", "pull", remote, branch], cwd=str(bot_dir), capture_output=True, text=True)
        else:
            result = subprocess.run(["git", "pull", remote], cwd=str(bot_dir), capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Pull error: {result.stderr}"
        log(bot_name, "Git pull completed")
        if "Already up to date" in result.stdout:
            return True, "Bot is already up to date"
        return True, "Bot updated successfully"
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e.stderr.decode() if e.stderr else str(e)}"


def get_bot_status(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return None

    info = config["bots"][bot_name]
    status = {"name": bot_name, **info}

    if info["status"] == "running" and info["pid"]:
        alive = False
        try:
            proc = psutil.Process(info["pid"])
            proc.cpu_percent(interval=0.05)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                status["cpu_percent"] = proc.cpu_percent(interval=0.05)
                status["memory_mb"] = proc.memory_info().rss / 1024 / 1024
                status["memory_percent"] = proc.memory_percent()
                status["create_time"] = datetime.fromtimestamp(proc.create_time()).isoformat()
                status["uptime_seconds"] = time.time() - proc.create_time()
                status["process_exists"] = True
                alive = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        if not alive:
            status["status"] = "stopped"
            status["pid"] = None
            status["process_exists"] = False
            config["bots"][bot_name]["status"] = "stopped"
            config["bots"][bot_name]["pid"] = None
            save_config(config)

    bot_dir = Path(info["directory"])
    if bot_dir.exists():
        total_size = 0
        for f in bot_dir.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
        status["storage_mb"] = total_size / 1024 / 1024
    else:
        status["storage_mb"] = 0

    log_path = get_log_path(bot_name)
    if log_path.exists():
        status["log_size_mb"] = log_path.stat().st_size / 1024 / 1024
    else:
        status["log_size_mb"] = 0

    return status


def list_bots():
    config = load_config()
    return list(config["bots"].keys())


def get_all_bots_status():
    bots = list_bots()
    result = {}
    for name in bots:
        result[name] = get_bot_status(name)
    return result


def edit_bot_file(bot_name, content=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_file = Path(config["bots"][bot_name]["directory"]) / "bot.py"
    if not bot_file.exists():
        return False, "bot.py not found"

    if content is not None:
        bot_file.write_text(content, encoding="utf-8")
        log(bot_name, "Bot file edited")
        return True, "Bot file updated"

    return True, bot_file.read_text(encoding="utf-8")


def replace_bot_file(bot_name, bot_code, requirements_content=None, token=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    (bot_dir / "bot.py").write_text(bot_code, encoding="utf-8")

    if token:
        config["bots"][bot_name]["token"] = token
        (bot_dir / ".env").write_text(f"DISCORD_TOKEN={token}\n")

    if requirements_content is not None:
        (bot_dir / "requirements.txt").write_text(requirements_content, encoding="utf-8")

    save_config(config)
    log(bot_name, "Bot file replaced")
    return True, "Bot file updated successfully"


def get_bot_logs(bot_name, lines=50):
    log_path = get_log_path(bot_name)
    if not log_path.exists():
        return []
    content = log_path.read_text(encoding="utf-8", errors="replace")
    all_lines = content.splitlines()
    return all_lines[-lines:]


def monitor_loop(interval=5):
    _last_git_check = 0
    while True:
        time.sleep(interval)
        try:
            config = load_config()
            changed = False
            now = time.time()
            for name, info in list(config["bots"].items()):
                if info["status"] == "running" and info["pid"]:
                    alive = False
                    try:
                        proc = psutil.Process(info["pid"])
                        proc.cpu_percent()
                        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                            alive = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass

                    if not alive:
                        info["status"] = "stopped"
                        info["pid"] = None
                        changed = True
                        log(name, "Bot stopped unexpectedly")
                        if info.get("auto_restart"):
                            log(name, "Auto-restarting...")
                            save_config(config)
                            start_bot(name)

            if now - _last_git_check > 60:
                _last_git_check = now
                for name, info in list(config["bots"].items()):
                    if info.get("auto_git_pull"):
                        behind, _ = check_git_updates(name) or (0, "")
                        if behind and behind > 0:
                            log(name, f"Git update found ({behind} commit(s)), updating...")
                            auto_pull_restart(name)
            if changed:
                save_config(config)
        except Exception:
            pass


def import_bot(name, bot_code, token=None, requirements_content=None):
    if not bot_code:
        return False, "Bot code is required"

    bot_dir = BOTS_DIR / name
    if bot_dir.exists():
        return False, f"'{name}' already exists"

    bot_dir.mkdir(parents=True, exist_ok=True)
    (bot_dir / "bot.py").write_text(bot_code, encoding="utf-8")

    if token:
        (bot_dir / ".env").write_text(f"DISCORD_TOKEN={token}\n")

    if requirements_content:
        (bot_dir / "requirements.txt").write_text(requirements_content, encoding="utf-8")
    else:
        (bot_dir / "requirements.txt").write_text("discord.py\naiohttp\npython-dotenv\n")

    config = load_config()
    config["bots"][name] = {
        "token": token or "",
        "created_at": datetime.now().isoformat(),
        "status": "stopped",
        "pid": None,
        "directory": str(bot_dir),
        "auto_restart": False,
        "auto_git_pull": False,
        "source": "imported"
    }
    save_config(config)

    log(name, "Bot imported from file")
    return True, "Bot imported successfully"


def clone_bot(name, repo_url, token=None):
    bot_dir = BOTS_DIR / name
    if bot_dir.exists():
        return False, f"'{name}' already exists"

    try:
        subprocess.run(["git", "clone", repo_url, str(bot_dir)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return False, f"Git clone error: {e.stderr}"

    bot_file = bot_dir / "bot.py"
    if not bot_file.exists():
        py_files = list(bot_dir.glob("*.py"))
        if len(py_files) == 0:
            py_files = [p for p in bot_dir.rglob("*.py") if not any(
                part.startswith(".") or part in ("__pycache__", "venv", ".venv", "env", "node_modules", "site-packages")
                for part in p.relative_to(bot_dir).parts[:-1]
            )]
        if len(py_files) == 0:
            shutil.rmtree(bot_dir)
            return False, "No .py files found in repository"
        if len(py_files) > 1:
            found = ", ".join(str(f.relative_to(bot_dir)) for f in py_files[:10])
            if len(py_files) > 10:
                found += f" and {len(py_files) - 10} more"
            return False, f"Multiple .py files found in repository ({found}). The main bot file should be named bot.py (directory was NOT deleted)."
        src = py_files[0]
        if src.parent == bot_dir:
            src.rename(bot_file)
        else:
            shutil.copy2(str(src), str(bot_file))
        log(name, f"{src.relative_to(bot_dir)} -> using as bot.py")

    if token:
        (bot_dir / ".env").write_text(f"DISCORD_TOKEN={token}\n")

    req_file = bot_dir / "requirements.txt"
    if not req_file.exists():
        (bot_dir / "requirements.txt").write_text("discord.py\naiohttp\npython-dotenv\n")

    config = load_config()
    config["bots"][name] = {
        "token": token or "",
        "created_at": datetime.now().isoformat(),
        "status": "stopped",
        "pid": None,
        "directory": str(bot_dir),
        "auto_restart": False,
        "auto_git_pull": False,
        "source": "cloned"
    }
    save_config(config)

    log(name, "Bot cloned from GitHub")
    return True, "Bot cloned successfully"


def set_auto_git_pull(bot_name, enabled):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"
    config["bots"][bot_name]["auto_git_pull"] = enabled
    save_config(config)
    status = "enabled" if enabled else "disabled"
    log(bot_name, f"Auto git pull {status}")
    return True, f"Auto git pull {status}"


def check_git_updates(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return None, "Bot not found"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    if not (bot_dir / ".git").exists():
        return None, "Git repository not found"

    try:
        subprocess.run(["git", "fetch"], cwd=str(bot_dir), capture_output=True, text=True)
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/HEAD"],
            cwd=str(bot_dir), capture_output=True, text=True
        )
        behind = int(result.stdout.strip() or 0)
        if behind > 0:
            return behind, f"{behind} new commit(s) available"
        return 0, "Up to date"
    except Exception as e:
        return None, str(e)


def auto_pull_restart(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot not found"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    was_running = (config["bots"][bot_name]["status"] == "running")

    if was_running:
        stop_bot(bot_name)

    try:
        result = subprocess.run(["git", "pull"], cwd=str(bot_dir), capture_output=True, text=True)
        if result.returncode != 0:
            log(bot_name, f"Git pull error: {result.stderr}")
            return False, f"Git pull error: {result.stderr}"
        log(bot_name, "Auto git pull completed")
    except Exception as e:
        return False, str(e)

    if (bot_dir / "requirements.txt").exists():
        install_deps(bot_name)

    if was_running:
        start_bot(bot_name)

    return True, "Bot updated and restarted"


def get_bot_invite_url(bot_name):
    import base64

    config = load_config()
    if bot_name not in config["bots"]:
        return None, "Bot not found"

    token = config["bots"][bot_name].get("token", "")
    if not token:
        return None, "Bot token not found"

    parts = token.split(".")
    if len(parts) < 2:
        return None, "Invalid token format"

    raw_id = parts[0]
    try:
        padded = raw_id + "=" * (4 - len(raw_id) % 4) if len(raw_id) % 4 else raw_id
        decoded = base64.b64decode(padded).decode("utf-8")
        client_id = decoded
    except Exception:
        client_id = raw_id

    url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot"
    return url, "OK"


def start_monitor():
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    return thread
