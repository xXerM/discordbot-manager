#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
from manager_core import (
    create_bot, install_deps, start_bot, stop_bot, restart_bot,
    delete_bot, git_push, list_bots, get_bot_status, get_all_bots_status,
    edit_bot_file, get_bot_logs, start_monitor, load_config, save_config, log,
    import_bot, get_bot_invite_url
)

def print_header():
    print("=" * 60)
    print("  Discord Bot Manager v1.0")
    print("=" * 60)

def print_bot_table(bots_data):
    if not bots_data:
        print("  Henüz bot bulunmuyor.")
        return
    print(f"\n  {'Ad':<20} {'Durum':<12} {'PID':<8} {'RAM':<10} {'Uptime':<15} {'Storage'}")
    print("  " + "-" * 75)
    for name, data in bots_data.items():
        if data is None:
            continue
        status = data.get("status", "?")
        pid = str(data.get("pid", "-"))
        mem = f"{data.get('memory_mb', 0):.1f}MB" if data.get("memory_mb") else "-"
        uptime_sec = data.get("uptime_seconds", 0)
        uptime = str(datetime.fromtimestamp(uptime_sec) - datetime.fromtimestamp(0)).split('.')[0] if uptime_sec else "-" if uptime_sec else "-"
        storage = f"{data.get('storage_mb', 0):.1f}MB"
        status_icon = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
        print(f"  {status_icon} {name:<18} {status:<12} {pid:<8} {mem:<10} {uptime:<15} {storage}")

def cmd_interactive():
    start_monitor()
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print_header()
        bots = get_all_bots_status()
        print_bot_table(bots)

        print("\n  Komutlar:")
        print("  [1] Bot Oluştur    [2] Bot Başlat")
        print("  [3] Bot Durdur     [4] Bot Yeniden Başlat")
        print("  [5] Bot Sil        [6] Bot Düzenle")
        print("  [7] Git Push       [8] Bağımlılıkları Kur")
        print("  [9] Bot Logları    [10] Bot İçe Aktar")
        print("  [11] Web Arayüzü   [12] Sunucuya Ekle (Davet)")
        print("  [0] Çıkış")
        choice = input("\n  Seçiminiz: ").strip()

        if choice == "0":
            print("  Görüşmek üzere!")
            break
        elif choice == "1":
            cmd_create()
        elif choice == "2":
            cmd_action("başlat", start_bot)
        elif choice == "3":
            cmd_action("durdur", stop_bot)
        elif choice == "4":
            cmd_action("yeniden başlat", restart_bot)
        elif choice == "5":
            cmd_delete()
        elif choice == "6":
            cmd_edit()
        elif choice == "7":
            cmd_git_push()
        elif choice == "8":
            cmd_action("bağımlılıkları kur", install_deps)
        elif choice == "9":
            cmd_logs()
        elif choice == "10":
            cmd_import()
        elif choice == "11":
            start_web()
        elif choice == "12":
            cmd_invite()
        else:
            input("  Geçersiz seçim. Devam etmek için Enter'a basın...")

def cmd_create():
    name = input("  Bot adı: ").strip()
    if not name:
        print("  Bot adı boş olamaz!")
        input("  Devam etmek için Enter'a basın...")
        return
    token = input("  Discord Bot Token: ").strip()
    if not token:
        print("  Token boş olamaz!")
        input("  Devam etmek için Enter'a basın...")
        return
    ok, msg = create_bot(name, token)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if ok:
        print("  Bağımlılıklar kuruluyor...")
        ok2, msg2 = install_deps(name)
        print(f"  {'✅' if ok2 else '❌'} {msg2}")
        auto_start = input("  Bot hemen başlatılsın mı? (e/H): ").strip().lower()
        if auto_start == "e":
            ok3, msg3 = start_bot(name)
            print(f"  {'✅' if ok3 else '❌'} {msg3}")
    input("  Devam etmek için Enter'a basın...")

def cmd_delete():
    bots = list_bots()
    if not bots:
        print("  Silinecek bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input("  Silinecek bot numarası: ")) - 1
        if 0 <= idx < len(bots):
            confirm = input(f"  '{bots[idx]}' silinsin mi? (e/E): ").strip().lower()
            if confirm == "e":
                ok, msg = delete_bot(bots[idx])
                print(f"  {'✅' if ok else '❌'} {msg}")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def cmd_edit():
    bots = list_bots()
    if not bots:
        print("  Düzenlenecek bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input("  Düzenlenecek bot numarası: ")) - 1
        if 0 <= idx < len(bots):
            name = bots[idx]
            ok, content = edit_bot_file(name)
            if not ok:
                print(f"  ❌ {content}")
                input("  Devam etmek için Enter'a basın...")
                return
            print("  Mevcut kod (Ctrl+D ile kaydet, Ctrl+C ile iptal):")
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
                    print(f"\n  {'✅' if ok2 else '❌'} {msg2}")
                else:
                    print("\n  Değişiklik yapılmadı.")
            except KeyboardInterrupt:
                print("\n  İptal edildi.")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def cmd_git_push():
    bots = list_bots()
    if not bots:
        print("  Bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input("  Push yapılacak bot numarası: ")) - 1
        if 0 <= idx < len(bots):
            msg = input("  Commit mesajı (opsiyonel): ").strip() or None
            ok, result = git_push(bots[idx], msg)
            print(f"  {'✅' if ok else '❌'} {result}")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def cmd_logs():
    bots = list_bots()
    if not bots:
        print("  Bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input("  Log görüntülenecek bot numarası: ")) - 1
        if 0 <= idx < len(bots):
            name = bots[idx]
            lines = get_bot_logs(name, 50)
            print(f"\n  --- {name} son 50 log ---")
            for line in lines:
                print(f"  {line}")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def cmd_action(action_name, func):
    bots = list_bots()
    if not bots:
        print(f"  {action_name} için bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        status = get_bot_status(name)
        icon = "🟢" if status and status["status"] == "running" else "🔴"
        print(f"  [{i}] {icon} {name}")
    try:
        idx = int(input(f"  {action_name} için bot numarası: ")) - 1
        if 0 <= idx < len(bots):
            ok, msg = func(bots[idx])
            print(f"  {'✅' if ok else '❌'} {msg}")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def cmd_import():
    name = input("  Bot adı: ").strip()
    if not name:
        print("  Bot adı boş olamaz!")
        input("  Devam etmek için Enter'a basın...")
        return
    bot_path = input("  Bot Python dosyası yolu: ").strip()
    if not bot_path or not os.path.isfile(bot_path):
        print("  Geçerli bir dosya yolu girin!")
        input("  Devam etmek için Enter'a basın...")
        return
    token = input("  Discord Bot Token (opsiyonel): ").strip()
    req_path = input("  Requirements dosyası yolu (opsiyonel): ").strip()
    req_content = None
    if req_path and os.path.isfile(req_path):
        with open(req_path, encoding="utf-8") as f:
            req_content = f.read()
    with open(bot_path, encoding="utf-8") as f:
        bot_code = f.read()
    ok, msg = import_bot(name, bot_code, token, req_content)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if ok:
        print("  Bağımlılıklar kuruluyor...")
        ok2, msg2 = install_deps(name)
        print(f"  {'✅' if ok2 else '❌'} {msg2}")
    input("  Devam etmek için Enter'a basın...")

def cmd_invite():
    bots = list_bots()
    if not bots:
        print("  Bot yok.")
        input("  Devam etmek için Enter'a basın...")
        return
    for i, name in enumerate(bots, 1):
        print(f"  [{i}] {name}")
    try:
        idx = int(input("  Davet linki alınacak bot: ")) - 1
        if 0 <= idx < len(bots):
            url, msg = get_bot_invite_url(bots[idx])
            if url:
                print(f"  ✅ Davet linki: {url}")
            else:
                print(f"  ❌ {msg}")
        else:
            print("  Geçersiz numara!")
    except ValueError:
        print("  Geçersiz giriş!")
    input("  Devam etmek için Enter'a basın...")

def start_web():
    print("  Web arayüzü başlatılıyor...")
    print("  http://localhost:5000 adresinden erişebilirsiniz.")
    print("  Durdurmak için Ctrl+C'ye basın.")
    try:
        from web_app import app
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except ImportError:
        print("  Flask kurulu değil. 'pip install flask' çalıştırın.")
        input("  Devam etmek için Enter'a basın...")

def main():
    start_monitor()

    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Discord Bot Manager")
        subparsers = parser.add_subparsers(dest="command")

        p_create = subparsers.add_parser("create", help="Yeni bot oluştur")
        p_create.add_argument("name", help="Bot adı")
        p_create.add_argument("token", help="Discord bot tokeni")

        p_start = subparsers.add_parser("start", help="Bot başlat")
        p_start.add_argument("name", help="Bot adı")

        p_stop = subparsers.add_parser("stop", help="Bot durdur")
        p_stop.add_argument("name", help="Bot adı")

        p_restart = subparsers.add_parser("restart", help="Bot yeniden başlat")
        p_restart.add_argument("name", help="Bot adı")

        p_delete = subparsers.add_parser("delete", help="Bot sil")
        p_delete.add_argument("name", help="Bot adı")

        p_list = subparsers.add_parser("list", help="Botları listele")

        p_status = subparsers.add_parser("status", help="Bot durumu")
        p_status.add_argument("name", nargs="?", default=None, help="Bot adı (opsiyonel)")

        p_logs = subparsers.add_parser("logs", help="Bot logları")
        p_logs.add_argument("name", help="Bot adı")
        p_logs.add_argument("--lines", type=int, default=50, help="Satır sayısı")

        p_edit = subparsers.add_parser("edit", help="Bot dosyasını düzenle")
        p_edit.add_argument("name", help="Bot adı")
        p_edit.add_argument("--content", help="Yeni içerik (dosyadan okumak için kullanmayın)")

        p_git = subparsers.add_parser("git-push", help="Git push")
        p_git.add_argument("name", help="Bot adı")
        p_git.add_argument("-m", "--message", help="Commit mesajı")

        p_install = subparsers.add_parser("install", help="Bağımlılıkları kur")
        p_install.add_argument("name", help="Bot adı")

        p_import = subparsers.add_parser("import", help="Bot dosyasını içe aktar")
        p_import.add_argument("name", help="Bot adı")
        p_import.add_argument("file", help="Python dosyası yolu")
        p_import.add_argument("--token", help="Discord bot tokeni")
        p_import.add_argument("--requirements", help="Requirements dosyası yolu")

        p_invite = subparsers.add_parser("invite", help="Bot davet linki")
        p_invite.add_argument("name", help="Bot adı")

        p_web = subparsers.add_parser("web", help="Web arayüzünü başlat")

        args = parser.parse_args()

        if args.command == "create":
            ok, msg = create_bot(args.name, args.token)
            print(f"{'✅' if ok else '❌'} {msg}")
            if ok:
                install_deps(args.name)
        elif args.command == "start":
            ok, msg = start_bot(args.name)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "stop":
            ok, msg = stop_bot(args.name)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "restart":
            ok, msg = restart_bot(args.name)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "delete":
            ok, msg = delete_bot(args.name)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "list":
            bots = get_all_bots_status()
            print_bot_table(bots)
        elif args.command == "status":
            if args.name:
                data = get_bot_status(args.name)
                if data:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print("Bot bulunamadı")
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
                print(f"{'✅' if ok else '❌'} {msg}")
            else:
                ok, content = edit_bot_file(args.name)
                if ok:
                    print(content)
                else:
                    print(f"❌ {content}")
        elif args.command == "git-push":
            ok, msg = git_push(args.name, args.message)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "install":
            ok, msg = install_deps(args.name)
            print(f"{'✅' if ok else '❌'} {msg}")
        elif args.command == "import":
            if not os.path.isfile(args.file):
                print("Dosya bulunamadı!")
                return
            with open(args.file, encoding="utf-8") as f:
                bot_code = f.read()
            req_content = None
            if args.requirements:
                if os.path.isfile(args.requirements):
                    with open(args.requirements, encoding="utf-8") as f:
                        req_content = f.read()
                else:
                    print("Requirements dosyası bulunamadı!")
                    return
            ok, msg = import_bot(args.name, bot_code, args.token, req_content)
            print(f"{'✅' if ok else '❌'} {msg}")
            if ok:
                install_deps(args.name)
        elif args.command == "invite":
            url, msg = get_bot_invite_url(args.name)
            if url:
                print(f"Davet linki: {url}")
            else:
                print(f"❌ {msg}")
        elif args.command == "web":
            start_web()
        else:
            parser.print_help()
    else:
        cmd_interactive()


if __name__ == "__main__":
    import json
    main()
