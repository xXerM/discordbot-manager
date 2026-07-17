import json
import threading
from flask import Flask, jsonify, request, render_template, send_from_directory
from manager_core import (
    create_bot, install_deps, start_bot, stop_bot, restart_bot,
    delete_bot, git_push, list_bots, get_bot_status, get_all_bots_status,
    edit_bot_file, get_bot_logs, start_monitor, load_config, save_config, log,
    import_bot, get_bot_invite_url,
    BASE_DIR, BOTS_DIR
)

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
start_monitor()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/bots", methods=["GET"])
def api_list_bots():
    bots = get_all_bots_status()
    return jsonify({"bots": bots})


@app.route("/api/bots/<name>", methods=["GET"])
def api_get_bot(name):
    data = get_bot_status(name)
    if data is None:
        return jsonify({"error": "Bot bulunamadı"}), 404
    return jsonify(data)


@app.route("/api/bots", methods=["POST"])
def api_create_bot():
    data = request.get_json()
    name = data.get("name", "").strip()
    token = data.get("token", "").strip()
    if not name or not token:
        return jsonify({"error": "İsim ve token gerekli"}), 400
    ok, msg = create_bot(name, token)
    if ok:
        install_deps(name)
        if data.get("auto_start"):
            start_bot(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/start", methods=["POST"])
def api_start_bot(name):
    ok, msg = start_bot(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/stop", methods=["POST"])
def api_stop_bot(name):
    ok, msg = stop_bot(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/restart", methods=["POST"])
def api_restart_bot(name):
    ok, msg = restart_bot(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>", methods=["DELETE"])
def api_delete_bot(name):
    ok, msg = delete_bot(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/git-push", methods=["POST"])
def api_git_push(name):
    data = request.get_json() or {}
    msg = data.get("message")
    ok, result = git_push(name, msg)
    return jsonify({"success": ok, "message": result}), (200 if ok else 400)


@app.route("/api/bots/<name>/edit", methods=["GET", "POST"])
def api_edit_bot(name):
    if request.method == "GET":
        ok, content = edit_bot_file(name)
        if not ok:
            return jsonify({"error": content}), 404
        return jsonify({"content": content})
    data = request.get_json()
    content = data.get("content", "")
    ok, msg = edit_bot_file(name, content)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/logs", methods=["GET"])
def api_get_logs(name):
    lines = request.args.get("lines", 50, type=int)
    logs = get_bot_logs(name, lines)
    return jsonify({"logs": logs})


@app.route("/api/bots/<name>/env", methods=["GET", "POST"])
def api_env(name):
    from pathlib import Path
    config = load_config()
    if name not in config["bots"]:
        return jsonify({"error": "Bot bulunamadı"}), 404
    env_file = Path(config["bots"][name]["directory"]) / ".env"
    if request.method == "GET":
        content = env_file.read_text() if env_file.exists() else ""
        return jsonify({"content": content})
    data = request.get_json()
    token = data.get("token", "")
    env_file.write_text(f"DISCORD_TOKEN={token}\n")
    config["bots"][name]["token"] = token
    save_config(config)
    return jsonify({"success": True, "message": "Token güncellendi"})


@app.route("/api/bots/import", methods=["POST"])
def api_import_bot():
    name = request.form.get("name", "").strip()
    token = request.form.get("token", "").strip()
    bot_file = request.files.get("bot_file")
    req_file = request.files.get("req_file")

    if not name:
        return jsonify({"error": "Bot adı gerekli"}), 400
    if not bot_file:
        return jsonify({"error": "Bot Python dosyası gerekli"}), 400

    bot_code = bot_file.read().decode("utf-8")
    req_content = None
    if req_file and req_file.filename:
        req_content = req_file.read().decode("utf-8")

    ok, msg = import_bot(name, bot_code, token, req_content)
    if ok:
        install_deps(name)
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/bots/<name>/invite", methods=["GET"])
def api_bot_invite(name):
    url, msg = get_bot_invite_url(name)
    if url is None:
        return jsonify({"error": msg}), 404
    return jsonify({"url": url})


@app.route("/api/bots/<name>/auto-restart", methods=["POST"])
def api_auto_restart(name):
    config = load_config()
    if name not in config["bots"]:
        return jsonify({"error": "Bot bulunamadı"}), 404
    data = request.get_json() or {}
    enabled = data.get("enabled", False)
    config["bots"][name]["auto_restart"] = enabled
    save_config(config)
    return jsonify({"success": True, "auto_restart": enabled})
