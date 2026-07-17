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
        return False, "template-bot.py bulunamadı"

    bot_dir = BOTS_DIR / name
    if bot_dir.exists():
        return False, f"'{name}' adında bir bot zaten var"

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
        "source": "template"
    }
    save_config(config)

    log(name, "Bot oluşturuldu")
    return True, "Bot başarıyla oluşturuldu"


def install_deps(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"
    bot_dir = Path(config["bots"][bot_name]["directory"])
    req_file = bot_dir / "requirements.txt"
    if not req_file.exists():
        return False, "requirements.txt bulunamadı"
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        try:
            result = subprocess.run(cmd, cwd=str(bot_dir), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            result = subprocess.run(cmd + ["--break-system-packages"], cwd=str(bot_dir), check=True, capture_output=True, text=True)
        log(bot_name, "Bağımlılıklar kuruldu")
        return True, "Bağımlılıklar başarıyla kuruldu"
    except subprocess.CalledProcessError as e:
        return False, f"Kurulum hatası: {e.stderr}"


def start_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"

    bot_info = config["bots"][bot_name]
    if bot_info["status"] == "running":
        return False, "Bot zaten çalışıyor"

    bot_dir = Path(bot_info["directory"])
    bot_script = bot_dir / "bot.py"
    if not bot_script.exists():
        return False, "bot.py bulunamadı"

    if not bot_info.get("token"):
        return False, "Bot tokeni bulunamadı"

    env = os.environ.copy()
    env["DISCORD_TOKEN"] = bot_info["token"]

    env_file = bot_dir / ".env"
    if not env_file.exists():
        env_file.write_text(f"DISCORD_TOKEN={bot_info['token']}\n")

    log_path = get_log_path(bot_name)
    try:
        with open(log_path, "a") as log_file:
            log_file.write(f"\n--- Bot başlatılıyor: {datetime.now().isoformat()} ---\n")
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
            error_info = log_lines[-1] if log_lines else "Bilinmeyen hata"
            log(bot_name, f"Bot başlatılamadı (process öldü)")
            return False, f"Bot başlatılamadı. Son log: {error_info}"

        bot_info["pid"] = process.pid
        bot_info["status"] = "running"
        save_config(config)

        log(bot_name, f"Bot başlatıldı (PID: {process.pid})")
        return True, f"Bot başlatıldı (PID: {process.pid})"
    except Exception as e:
        return False, f"Başlatma hatası: {str(e)}"


def stop_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"

    bot_info = config["bots"][bot_name]
    if bot_info["status"] != "running" or not bot_info["pid"]:
        return False, "Bot zaten çalışmıyor"

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
    log(bot_name, "Bot durduruldu")
    return True, "Bot durduruldu"


def restart_bot(bot_name):
    stop_bot(bot_name)
    time.sleep(1)
    return start_bot(bot_name)


def delete_bot(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"

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

    log(bot_name, "Bot silindi")
    return True, "Bot silindi"


def git_push(bot_name, commit_message=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    if not (bot_dir / ".git").exists():
        subprocess.run(["git", "init"], cwd=str(bot_dir), capture_output=True)

    try:
        subprocess.run(["git", "add", "."], cwd=str(bot_dir), check=True, capture_output=True)
        msg = commit_message or f"Bot güncelleme: {datetime.now().isoformat()}"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(bot_dir), check=False, capture_output=True)
        result = subprocess.run(["git", "push"], cwd=str(bot_dir), capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Push hatası: {result.stderr}"
        log(bot_name, "Git push yapıldı")
        return True, "Git push başarılı"
    except subprocess.CalledProcessError as e:
        return False, f"Git hatası: {e.stderr.decode() if e.stderr else str(e)}"


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
        return False, "Bot bulunamadı"

    bot_file = Path(config["bots"][bot_name]["directory"]) / "bot.py"
    if not bot_file.exists():
        return False, "bot.py bulunamadı"

    if content is not None:
        bot_file.write_text(content, encoding="utf-8")
        log(bot_name, "Bot dosyası düzenlendi")
        return True, "Bot dosyası güncellendi"

    return True, bot_file.read_text(encoding="utf-8")


def replace_bot_file(bot_name, bot_code, requirements_content=None, token=None):
    config = load_config()
    if bot_name not in config["bots"]:
        return False, "Bot bulunamadı"

    bot_dir = Path(config["bots"][bot_name]["directory"])
    (bot_dir / "bot.py").write_text(bot_code, encoding="utf-8")

    if token:
        config["bots"][bot_name]["token"] = token
        (bot_dir / ".env").write_text(f"DISCORD_TOKEN={token}\n")

    if requirements_content is not None:
        (bot_dir / "requirements.txt").write_text(requirements_content, encoding="utf-8")

    save_config(config)
    log(bot_name, "Bot dosyası değiştirildi")
    return True, "Bot dosyası başarıyla güncellendi"


def get_bot_logs(bot_name, lines=50):
    log_path = get_log_path(bot_name)
    if not log_path.exists():
        return []
    content = log_path.read_text(encoding="utf-8", errors="replace")
    all_lines = content.splitlines()
    return all_lines[-lines:]


def monitor_loop(interval=5):
    while True:
        time.sleep(interval)
        try:
            config = load_config()
            changed = False
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
                        log(name, "Bot beklenmedik şekilde durdu")
                        if info.get("auto_restart"):
                            log(name, "Otomatik yeniden başlatılıyor...")
                            save_config(config)
                            start_bot(name)
            if changed:
                save_config(config)
        except Exception:
            pass


def import_bot(name, bot_code, token=None, requirements_content=None):
    if not bot_code:
        return False, "Bot kodu gerekli"

    bot_dir = BOTS_DIR / name
    if bot_dir.exists():
        return False, f"'{name}' adında bir bot zaten var"

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
        "source": "imported"
    }
    save_config(config)

    log(name, "Bot dosyadan içe aktarıldı")
    return True, "Bot başarıyla içe aktarıldı"


def get_bot_invite_url(bot_name):
    config = load_config()
    if bot_name not in config["bots"]:
        return None, "Bot bulunamadı"

    token = config["bots"][bot_name].get("token", "")
    if not token:
        return None, "Bot tokeni bulunamadı"

    parts = token.split(".")
    if len(parts) < 2:
        return None, "Geçersiz token formatı"

    client_id = parts[0]
    url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot"
    return url, "OK"


def start_monitor():
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    return thread
