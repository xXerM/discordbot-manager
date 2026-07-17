#!/usr/bin/env python3
import os
import sys
import json
import argparse
from datetime import datetime
from manager_core import (
    create_bot, install_deps, start_bot, stop_bot, restart_bot,
    delete_bot, git_push, list_bots, get_bot_status, get_all_bots_status,
    edit_bot_file, get_bot_logs, start_monitor, load_config, save_config, log,
    import_bot, get_bot_invite_url
)

LANG = {
    "en": {
        "header": "Discord Bot Manager v1.0",
        "no_bots": "No bots yet.",
        "menu_title": "Commands:",
        "menu_create": "Create Bot",
        "menu_start": "Start Bot",
        "menu_stop": "Stop Bot",
        "menu_restart": "Restart Bot",
        "menu_delete": "Delete Bot",
        "menu_edit": "Edit Bot",
        "menu_git": "Git Push",
        "menu_install": "Install Dependencies",
        "menu_logs": "Bot Logs",
        "menu_import": "Import Bot",
        "menu_web": "Web Interface",
        "menu_invite": "Add to Server (Invite)",
        "menu_lang": "Toggle Language (TR)",
        "menu_exit": "Exit",
        "choice": "Your choice: ",
        "invalid": "Invalid choice. Press Enter to continue...",
        "exit_msg": "Goodbye!",
        "name": "Bot name: ",
        "name_empty": "Bot name cannot be empty!",
        "token": "Discord Bot Token: ",
        "token_empty": "Token cannot be empty!",
        "installing": "Installing dependencies...",
        "auto_start": "Auto start now? (y/N): ",
        "no_bots_for": "No bots for {action}.",
        "select_num": "Select bot number: ",
        "invalid_num": "Invalid number!",
        "invalid_input": "Invalid input!",
        "confirm_delete": "Delete '{name}'? (y/Y): ",
        "confirm_yn": " (y/N): ",
        "no_bots_avail": "No bots available.",
        "edit_code": "Current code (Ctrl+D to save, Ctrl+C to cancel):",
        "no_changes": "No changes made.",
        "cancelled": "Cancelled.",
        "commit_msg": "Commit message (optional): ",
        "logs_for": "--- {name} last 50 logs ---",
        "bot_path": "Bot Python file path: ",
        "invalid_path": "Enter a valid file path!",
        "token_opt": "Discord Bot Token (optional): ",
        "req_path": "Requirements file path (optional): ",
        "invite_for": "Get invite link for bot: ",
        "invite_link": "Invite link: {url}",
        "web_starting": "Starting web interface...",
        "web_access": "Visit http://localhost:5000",
        "web_stop": "Press Ctrl+C to stop.",
        "web_no_flask": "Flask not installed. Run 'pip install flask'.",
        "continue": "Press Enter to continue...",
        "table_header": "{'Name':<20} {'Status':<12} {'PID':<8} {'RAM':<10} {'Uptime':<15} {'Storage'}",
        "file_not_found": "File not found!",
        "req_not_found": "Requirements file not found!",
        "bot_not_found": "Bot not found!",
        "lang_toggle": "Toggle Language (TR)",
        "lang_prompt": "Press Enter to continue...",
        "restarting": "Automatically restarting...",
        "deps_ok": "Dependencies installed successfully.",
        "deps_fail": "Dependency installation failed.",
    },
    "tr": {
        "header": "Discord Bot Manager v1.0",
        "no_bots": "Hen\u00fcz bot bulunmuyor.",
        "menu_title": "Komutlar:",
        "menu_create": "Bot Olu\u015ftur",
        "menu_start": "Bot Ba\u015flat",
        "menu_stop": "Bot Durdur",
        "menu_restart": "Bot Yeniden Ba\u015flat",
        "menu_delete": "Bot Sil",
        "menu_edit": "Bot D\u00fczenle",
        "menu_git": "Git Push",
        "menu_install": "Ba\u011f\u0131ml\u0131l\u0131klar\u0131 Kur",
        "menu_logs": "Bot Loglar\u0131",
        "menu_import": "Bot \u0130\u00e7e Aktar",
        "menu_web": "Web Aray\u00fcz\u00fc",
        "menu_invite": "Sunucuya Ekle (Davet)",
        "menu_lang": "Dili De\u011fi\u015ftir (EN)",
        "menu_exit": "\u00c7\u0131k\u0131\u015f",
        "choice": "Se\u00e7iminiz: ",
        "invalid": "Ge\u00e7ersiz se\u00e7im. Devam etmek i\u00e7in Enter'a bas\u0131n...",
        "exit_msg": "G\u00f6r\u00fc\u015fmek \u00fczere!",
        "name": "Bot ad\u0131: ",
        "name_empty": "Bot ad\u0131 bo\u015f olamaz!",
        "token": "Discord Bot Token: ",
        "token_empty": "Token bo\u015f olamaz!",
        "installing": "Ba\u011f\u0131ml\u0131l\u0131klar kuruluyor...",
        "auto_start": "Bot hemen ba\u015flat\u0131ls\u0131n m\u0131? (e/H): ",
        "no_bots_for": "{action} i\u00e7in bot yok.",
        "select_num": "Bot numaras\u0131: ",
        "invalid_num": "Ge\u00e7ersiz numara!",
        "invalid_input": "Ge\u00e7ersiz giri\u015f!",
        "confirm_delete": "'{name}' silinsin mi? (e/E): ",
        "confirm_yn": " (e/H): ",
        "no_bots_avail": "Bot yok.",
        "edit_code": "Mevcut kod (Ctrl+D ile kaydet, Ctrl+C ile iptal):",
        "no_changes": "De\u011fi\u015fiklik yap\u0131lmad\u0131.",
        "cancelled": "\u0130ptal edildi.",
        "commit_msg": "Commit mesaj\u0131 (opsiyonel): ",
        "logs_for": "--- {name} son 50 log ---",
        "bot_path": "Bot Python dosyas\u0131 yolu: ",
        "invalid_path": "Ge\u00e7erli bir dosya yolu girin!",
        "token_opt": "Discord Bot Token (opsiyonel): ",
        "req_path": "Requirements dosyas\u0131 yolu (opsiyonel): ",
        "invite_for": "Davet linki al\u0131nacak bot: ",
        "invite_link": "Davet linki: {url}",
        "web_starting": "Web aray\u00fcz\u00fc ba\u015flat\u0131l\u0131yor...",
        "web_access": "http://localhost:5000 adresinden eri\u015febilirsiniz.",
        "web_stop": "Durdurmak i\u00e7in Ctrl+C'ye bas\u0131n.",
        "web_no_flask": "Flask kurulu de\u011fil. 'pip install flask' \u00e7al\u0131\u015ft\u0131r\u0131n.",
        "continue": "Devam etmek i\u00e7in Enter'a bas\u0131n...",
        "table_header": "{'Ad':<20} {'Durum':<12} {'PID':<8} {'RAM':<10} {'Uptime':<15} {'Storage'}",
        "file_not_found": "Dosya bulunamad\u0131!",
        "req_not_found": "Requirements dosyas\u0131 bulunamad\u0131!",
        "bot_not_found": "Bot bulunamad\u0131!",
        "lang_toggle": "Dili De\u011fi\u015ftir (EN)",
        "lang_prompt": "Devam etmek i\u00e7in Enter'a bas\u0131n...",
        "restarting": "Otomatik yeniden ba\u015flat\u0131l\u0131yor...",
        "deps_ok": "Ba\u011f\u0131ml\u0131l\u0131klar ba\u015far\u0131yla kuruldu.",
        "deps_fail": "Ba\u011f\u0131ml\u0131l\u0131k kurulumu ba\u015far\u0131s\u0131z.",
    }
}

_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "bot_config.json")

def _get_cli_lang():
    try:
        with open(_CONFIG_FILE) as f:
            cfg = json.load(f)
        return cfg.get("_cli_lang", "en")
    except (FileNotFoundError, json.JSONDecodeError):
        return "en"

def _set_cli_lang(lang):
    try:
        with open(_CONFIG_FILE) as f:
            cfg = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cfg = {"bots": {}}
    cfg["_cli_lang"] = lang
    with open(_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def t(key, **kwargs):
    lang = _get_cli_lang()
    val = LANG.get(lang, LANG["en"]).get(key, LANG["en"].get(key, key))
    for k, v in kwargs.items():
        val = val.replace(f"{{{k}}}", str(v))
    return val


def print_header():
    print("=" * 60)
    print(f"  {t('header')}")
    print("=" * 60)


def print_bot_table(bots_data):
    if not bots_data:
        print(f"  {t('no_bots')}")
        return
    h = f"\n  {'Name':<20} {'Status':<12} {'PID':<8} {'RAM':<10} {'Uptime':<15} {'Storage'}"
    print(h)
    print("  " + "-" * 75)
    for name, data in bots_data.items():
        if data is None:
            continue
        status = data.get("status", "?")
        pid = str(data.get("pid", "-"))
        mem = f"{data.get('memory_mb', 0):.1f}MB" if data.get("memory_mb") else "-"
        uptime_sec = data.get("uptime_seconds", 0)
        uptime = str(datetime.fromtimestamp(uptime_sec) - datetime.fromtimestamp(0)).split('.')[0] if uptime_sec else "-"
        storage = f"{data.get('storage_mb', 0):.1f}MB"
        status_icon = "\U0001f7e2" if status == "running" else "\U0001f534" if status == "stopped" else "\U0001f7e1"
        print(f"  {status_icon} {name:<18} {status:<12} {pid:<8} {mem:<10} {uptime:<15} {storage}")


def _wait():
    input(f"  {t('continue')}")


def cmd_interactive():
    start_monitor()
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print_header()
        bots = get_all_bots_status()
        print_bot_table(bots)

        print(f"\n  {t('menu_title')}")
        print(f"  [1] {t('menu_create')}    [2] {t('menu_start')}")
        print(f"  [3] {t('menu_stop')}     [4] {t('menu_restart')}")
        print(f"  [5] {t('menu_delete')}        [6] {t('menu_edit')}")
        print(f"  [7] {t('menu_git')}       [8] {t('menu_install')}")
        print(f"  [9] {t('menu_logs')}    [10] {t('menu_import')}")
        print(f"  [11] {t('menu_web')}   [12] {t('menu_invite')}")
        print(f"  [13] {t('menu_lang')}")
        print(f"  [0] {t('menu_exit')}")
        choice = input(f"\n  {t('choice')}").strip()

        if choice == "0":
            print(f"  {t('exit_msg')}")
            break
        elif choice == "1":
            cmd_create()
        elif choice == "2":
            cmd_action(t("menu_start").lower(), start_bot)
        elif choice == "3":
            cmd_action(t("menu_stop").lower(), stop_bot)
        elif choice == "4":
            cmd_action(t("menu_restart").lower(), restart_bot)
        elif choice == "5":
            cmd_delete()
        elif choice == "6":
            cmd_edit()
        elif choice == "7":
            cmd_git_push()
        elif choice == "8":
            cmd_action(t("menu_install").lower(), install_deps)
        elif choice == "9":
            cmd_logs()
        elif choice == "10":
            cmd_import()
        elif choice == "11":
            start_web()
        elif choice == "12":
            cmd_invite()
        elif choice == "13":
            cur = _get_cli_lang()
            new = "tr" if cur == "en" else "en"
            _set_cli_lang(new)
            print(f"  Language set to {'English' if new == 'en' else 'T\u00fcrk\u00e7e'}.")
            _wait()
        else:
            input(f"  {t('invalid')}")


def cmd_create():
    name = input(f"  {t('name')}").strip()
    if not name:
        print(f"  {t('name_empty')}")
        _wait()
        return
    token_val = input(f"  {t('token')}").strip()
    if not token_val:
        print(f"  {t('token_empty')}")
        _wait()
        return
    ok, msg = create_bot(name, token_val)
    print(f"  {'\u2705' if ok else '\u274c'} {msg}")
    if ok:
        print(f"  {t('installing')}")
        ok2, msg2 = install_deps(name)
        print(f"  {'\u2705' if ok2 else '\u274c'} {msg2}")
        auto = input(f"  {t('auto_start')}").strip().lower()
        if auto in ("y", "e"):
            ok3, msg3 = start_bot(name)
            print(f"  {'\u2705' if ok3 else '\u274c'} {msg3}")
    _wait()


def cmd_delete():
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_avail')}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            confirm = input(f"  {t('confirm_delete', name=bots[idx])}").strip().lower()
            if confirm in ("y", "e"):
                ok, msg = delete_bot(bots[idx])
                print(f"  {'\u2705' if ok else '\u274c'} {msg}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def cmd_edit():
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_avail')}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            name = bots[idx]
            ok, content = edit_bot_file(name)
            if not ok:
                print(f"  \u274c {content}")
                _wait()
                return
            print(f"  {t('edit_code')}")
            print("-" * 40)
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                new_content = "\n".join(lines)
                if new_content.strip():
                    ok2, msg2 = edit_bot_file(name, new_content)
                    print(f"\n  {'\u2705' if ok2 else '\u274c'} {msg2}")
                else:
                    print(f"\n  {t('no_changes')}")
            except KeyboardInterrupt:
                print(f"\n  {t('cancelled')}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def cmd_git_push():
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_avail')}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            msg = input(f"  {t('commit_msg')}").strip() or None
            ok, result = git_push(bots[idx], msg)
            print(f"  {'\u2705' if ok else '\u274c'} {result}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def cmd_logs():
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_avail')}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            name = bots[idx]
            lines = get_bot_logs(name, 50)
            print(f"\n  {t('logs_for', name=name)}")
            for line in lines:
                print(f"  {line}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def cmd_action(action_name, func):
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_for', action=action_name)}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        status = get_bot_status(name)
        icon = "\U0001f7e2" if status and status["status"] == "running" else "\U0001f534"
        print(f"  [{i}] {icon} {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            ok, msg = func(bots[idx])
            print(f"  {'\u2705' if ok else '\u274c'} {msg}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def cmd_import():
    name = input(f"  {t('name')}").strip()
    if not name:
        print(f"  {t('name_empty')}")
        _wait()
        return
    bot_path = input(f"  {t('bot_path')}").strip()
    if not bot_path or not os.path.isfile(bot_path):
        print(f"  {t('invalid_path')}")
        _wait()
        return
    token_val = input(f"  {t('token_opt')}").strip()
    req_path = input(f"  {t('req_path')}").strip()
    req_content = None
    if req_path and os.path.isfile(req_path):
        with open(req_path, encoding="utf-8") as f:
            req_content = f.read()
    with open(bot_path, encoding="utf-8") as f:
        bot_code = f.read()
    ok, msg = import_bot(name, bot_code, token_val, req_content)
    print(f"  {'\u2705' if ok else '\u274c'} {msg}")
    if ok:
        print(f"  {t('installing')}")
        ok2, msg2 = install_deps(name)
        print(f"  {'\u2705' if ok2 else '\u274c'} {msg2}")
    _wait()


def cmd_invite():
    bots = list_bots()
    if not bots:
        print(f"  {t('no_bots_avail')}")
        _wait()
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input(f"  {t('select_num')}")) - 1
        if 0 <= idx < len(bots):
            url, msg = get_bot_invite_url(bots[idx])
            if url:
                print(f"  \u2705 {t('invite_link', url=url)}")
            else:
                print(f"  \u274c {msg}")
        else:
            print(f"  {t('invalid_num')}")
    except ValueError:
        print(f"  {t('invalid_input')}")
    _wait()


def start_web():
    print(f"  {t('web_starting')}")
    print(f"  {t('web_access')}")
    print(f"  {t('web_stop')}")
    try:
        from web_app import app
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except ImportError:
        print(f"  {t('web_no_flask')}")
        _wait()


def main():
    start_monitor()

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Discord Bot Manager")
        subparsers = parser.add_subparsers(dest="command")

        p_create = subparsers.add_parser("create", help="Create a new bot")
        p_create.add_argument("name", help="Bot name")
        p_create.add_argument("token", help="Discord bot token")

        p_start = subparsers.add_parser("start", help="Start a bot")
        p_start.add_argument("name", help="Bot name")

        p_stop = subparsers.add_parser("stop", help="Stop a bot")
        p_stop.add_argument("name", help="Bot name")

        p_restart = subparsers.add_parser("restart", help="Restart a bot")
        p_restart.add_argument("name", help="Bot name")

        p_delete = subparsers.add_parser("delete", help="Delete a bot")
        p_delete.add_argument("name", help="Bot name")

        p_list = subparsers.add_parser("list", help="List all bots")

        p_status = subparsers.add_parser("status", help="Show bot status")
        p_status.add_argument("name", nargs="?", default=None, help="Bot name (optional)")

        p_logs = subparsers.add_parser("logs", help="View bot logs")
        p_logs.add_argument("name", help="Bot name")
        p_logs.add_argument("--lines", type=int, default=50, help="Number of lines")

        p_edit = subparsers.add_parser("edit", help="Edit bot file")
        p_edit.add_argument("name", help="Bot name")
        p_edit.add_argument("--content", help="New content")

        p_git = subparsers.add_parser("git-push", help="Git push bot")
        p_git.add_argument("name", help="Bot name")
        p_git.add_argument("-m", "--message", help="Commit message")

        p_install = subparsers.add_parser("install", help="Install dependencies")
        p_install.add_argument("name", help="Bot name")

        p_import = subparsers.add_parser("import", help="Import bot from file")
        p_import.add_argument("name", help="Bot name")
        p_import.add_argument("file", help="Python file path")
        p_import.add_argument("--token", help="Discord bot token")
        p_import.add_argument("--requirements", help="Requirements file path")

        p_invite = subparsers.add_parser("invite", help="Get bot invite link")
        p_invite.add_argument("name", help="Bot name")

        p_lang = subparsers.add_parser("lang", help="Set CLI language (en/tr)")
        p_lang.add_argument("lang", choices=["en", "tr"], help="Language code")

        p_web = subparsers.add_parser("web", help="Start web interface")

        args = parser.parse_args()

        if args.command == "create":
            ok, msg = create_bot(args.name, args.token)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
            if ok:
                install_deps(args.name)
        elif args.command == "start":
            ok, msg = start_bot(args.name)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "stop":
            ok, msg = stop_bot(args.name)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "restart":
            ok, msg = restart_bot(args.name)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "delete":
            ok, msg = delete_bot(args.name)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "list":
            bots = get_all_bots_status()
            print_bot_table(bots)
        elif args.command == "status":
            if args.name:
                data = get_bot_status(args.name)
                if data:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(t("bot_not_found"))
            else:
                bots = get_all_bots_status()
                print_bot_table(bots)
        elif args.command == "logs":
            lines = get_bot_logs(args.name, args.lines)
            for line in lines:
                print(line)
        elif args.command == "edit":
            if args.content:
                ok, msg = edit_bot_file(args.name, args.content)
                print(f"{'\u2705' if ok else '\u274c'} {msg}")
            else:
                ok, content = edit_bot_file(args.name)
                if ok:
                    print(content)
                else:
                    print(f"\u274c {content}")
        elif args.command == "git-push":
            ok, msg = git_push(args.name, args.message)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "install":
            ok, msg = install_deps(args.name)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
        elif args.command == "import":
            if not os.path.isfile(args.file):
                print(t("file_not_found"))
                return
            with open(args.file, encoding="utf-8") as f:
                bot_code = f.read()
            req_content = None
            if args.requirements:
                if os.path.isfile(args.requirements):
                    with open(args.requirements, encoding="utf-8") as f:
                        req_content = f.read()
                else:
                    print(t("req_not_found"))
                    return
            ok, msg = import_bot(args.name, bot_code, args.token, req_content)
            print(f"{'\u2705' if ok else '\u274c'} {msg}")
            if ok:
                install_deps(args.name)
        elif args.command == "invite":
            url, msg = get_bot_invite_url(args.name)
            if url:
                print(t("invite_link", url=url))
            else:
                print(f"\u274c {msg}")
        elif args.command == "lang":
            _set_cli_lang(args.lang)
            print(f"Language set to {'English' if args.lang == 'en' else 'T\u00fcrk\u00e7e'}.")
        elif args.command == "web":
            start_web()
        else:
            parser.print_help()
    else:
        cmd_interactive()


if __name__ == "__main__":
    main()
