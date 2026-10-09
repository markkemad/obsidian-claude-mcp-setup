#!/usr/bin/env python3
"""
Interactive setup: connect Claude Code to an Obsidian vault over MCP.

Uses the "Local REST API with MCP" Obsidian plugin
(https://github.com/coddingtonbear/obsidian-local-rest-api), which since
mid-2026 ships its own streamable-HTTP MCP server directly -- no separate
bridge process needed. This script:

  1. Finds your Obsidian vaults (or lets you type a path)
  2. Downloads the plugin's release files into the vault
  3. Enables it in the vault's plugin list
  4. Opens Obsidian on that vault so you can approve community plugins
     (a manual safety gate inside Obsidian -- no script can skip this)
  5. Reads the API key the plugin generates on first run
  6. Registers the MCP connector with Claude Code (`claude mcp add`)

Requires: Python 3.8+, and the `claude` CLI on PATH for the last step
(if it's missing you'll get the exact command to run yourself).
"""
import json
import os
import platform
import secrets
import shutil
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

try:
    # On machines behind a TLS-inspecting corporate proxy/antivirus, Python's
    # bundled CA list rejects the re-signed cert even though Windows/macOS
    # trusts it. `truststore` makes the ssl module defer to the OS trust
    # store instead, which fixes that without touching security settings.
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

REPO = "coddingtonbear/obsidian-local-rest-api"
GITHUB_API = f"https://api.github.com/repos/{REPO}/releases/latest"
PLUGIN_ASSET_NAMES = ("main.js", "manifest.json", "styles.css")
UA = {"User-Agent": "obsidian-mcp-setup-script"}


def obsidian_config_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ["APPDATA"]) / "obsidian"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support" / "obsidian"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "obsidian"
    return base / "obsidian.json"


def discover_vaults():
    cfg = obsidian_config_path()
    if not cfg.exists():
        return []
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception:
        return []
    vaults = []
    for info in data.get("vaults", {}).values():
        path = info.get("path")
        if path:
            vaults.append(Path(path))
    return vaults


def register_vault(vault_path: Path):
    """Add vault_path to Obsidian's own vault registry (obsidian.json) if
    it isn't already there. Obsidian's `obsidian://open?path=` handler only
    resolves paths it already knows about -- it won't bootstrap a brand-new
    vault from a raw folder path -- so this is required for both newly
    created vaults and any typed-in custom path. Merges additively; never
    touches other vaults' existing entries."""
    cfg_path = obsidian_config_path()
    data = {"vaults": {}}
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            data = {"vaults": {}}
    vaults = data.setdefault("vaults", {})

    target = str(vault_path)
    for existing in vaults.values():
        if existing.get("path", "").lower() == target.lower():
            return  # already registered

    new_id = secrets.token_hex(8)
    vaults[new_id] = {"path": target, "ts": int(time.time() * 1000)}
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(data), encoding="utf-8")


def prompt_choice(prompt, options):
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("  -> enter a number from the list.")


def pick_folder_dialog(title="Select a folder"):
    """Native folder picker via tkinter. Returns None if unavailable (no
    display, tkinter missing, dialog cancelled) so callers can fall back
    to a typed path."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(title=title, initialdir=str(Path.home()))
        root.destroy()
    except Exception:
        return None
    return Path(chosen) if chosen else None


def create_new_vault() -> Path:
    print("\n== Create a new vault ==")
    print("Opening a folder picker so you can choose where to save it...")
    parent = pick_folder_dialog("Choose where to save the new vault")
    if parent is None:
        print("(Folder picker unavailable -- type a path instead.)")
        raw = input("Parent folder to create the vault in: ").strip().strip('"')
        parent = Path(raw).expanduser().resolve()
    if not parent.exists():
        sys.exit(f"Folder does not exist: {parent}")

    while True:
        name = input("Vault name: ").strip()
        while not name:
            name = input("Vault name (required): ").strip()

        vault_path = parent / name
        if name.lower() == parent.name.lower():
            print(f"Note: '{parent}' already ends in '{name}' -- this will "
                  f"create a nested folder:\n  {vault_path}")
        confirm = input(f"Create vault at:\n  {vault_path}\nProceed? [Y/n] ").strip().lower()
        if confirm in ("", "y", "yes"):
            break
        print("Let's try a different name.")

    if vault_path.exists() and any(vault_path.iterdir()):
        sys.exit(f"'{vault_path}' already exists and is not empty.")
    vault_path.mkdir(parents=True, exist_ok=True)
    (vault_path / ".obsidian").mkdir(exist_ok=True)
    print(f"Created new vault at {vault_path}")
    return vault_path


def select_vault() -> Path:
    vaults = discover_vaults()
    print("\n== Select an Obsidian vault ==")
    if not vaults:
        print("(No vaults found automatically in Obsidian's config.)")
    labels = [str(v) for v in vaults] + ["Create a new vault", "Enter a custom path"]
    idx = prompt_choice("Vault #: ", labels)
    if idx == len(vaults):
        path = create_new_vault()
    elif idx == len(vaults) + 1:
        raw = input("Full path to vault folder: ").strip().strip('"')
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            sys.exit(f"Path does not exist: {path}")
        (path / ".obsidian").mkdir(exist_ok=True)
    else:
        path = vaults[idx]

    # Obsidian's obsidian:// URI can only resolve paths already present in
    # its own vault registry -- make sure this one is in there (idempotent
    # for already-known vaults).
    register_vault(path)
    return path


TLS_HELP = (
    "TLS certificate verification failed. This is common behind a corporate\n"
    "TLS-inspecting proxy or antivirus, where Python's own CA list doesn't\n"
    "trust the re-signed certificate even though Windows/macOS does.\n"
    "Fix: pip install truststore\n"
    "then re-run this script."
)


def http_get_json(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            sys.exit(TLS_HELP)
        raise


def download(url, dest: Path):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            sys.exit(TLS_HELP)
        raise


def install_plugin(vault: Path):
    print("\n== Installing 'Local REST API with MCP' plugin ==")
    try:
        release = http_get_json(GITHUB_API)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        sys.exit(f"Could not reach GitHub to fetch the latest release: {e}")

    assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
    required_missing = [n for n in ("main.js", "manifest.json") if n not in assets]
    if required_missing:
        sys.exit(f"Latest release is missing expected files: {required_missing}")

    plugins_root = vault / ".obsidian" / "plugins"
    plugins_root.mkdir(parents=True, exist_ok=True)
    tmp_manifest = plugins_root / "_tmp_manifest.json"
    download(assets["manifest.json"], tmp_manifest)
    manifest = json.loads(tmp_manifest.read_text(encoding="utf-8"))
    plugin_id = manifest["id"]
    tmp_manifest.unlink()

    plugin_dir = plugins_root / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)
    for name in PLUGIN_ASSET_NAMES:
        if name in assets:
            download(assets[name], plugin_dir / name)

    print(f"Installed {release.get('tag_name', 'latest')} -> {plugin_dir}")
    return plugin_id, plugin_dir


def enable_plugin(vault: Path, plugin_id: str):
    cp_path = vault / ".obsidian" / "community-plugins.json"
    ids = []
    if cp_path.exists():
        try:
            ids = json.loads(cp_path.read_text(encoding="utf-8"))
        except Exception:
            ids = []
    if plugin_id not in ids:
        ids.append(plugin_id)
    cp_path.write_text(json.dumps(ids, indent=2), encoding="utf-8")


def launch_obsidian(vault: Path):
    uri = "obsidian://open?path=" + urllib.parse.quote(str(vault))
    print(f"\nOpening Obsidian on this vault:\n  {uri}")
    try:
        webbrowser.open(uri)
    except Exception:
        print("Could not auto-launch Obsidian -- open it manually and load this vault.")


def wait_for_api_key(plugin_dir: Path):
    data_path = plugin_dir / "data.json"
    print("\n== Waiting for the plugin to generate an API key ==")
    print("In Obsidian, if prompted, click to trust/enable community plugins,")
    print("then make sure 'Local REST API with MCP' is toggled ON under")
    print("Settings -> Community plugins.")
    while True:
        if data_path.exists():
            try:
                data = json.loads(data_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            key = data.get("apiKey")
            if key:
                return key, data
        input("Press Enter to check again (Ctrl+C to abort)... ")


def choose_endpoint(data: dict) -> str:
    https_port = data.get("port", 27124)
    http_enabled = bool(data.get("enableInsecureServer"))
    http_port = data.get("insecurePort", 27123)

    print("\n== Choose connection mode ==")
    print(f"  1. HTTPS (self-signed cert)  https://127.0.0.1:{https_port}/mcp/")
    if http_enabled:
        print(f"  2. HTTP (already enabled)    http://127.0.0.1:{http_port}/mcp/")
    else:
        print("  2. HTTP -- not enabled yet. Turn on 'Enable Non-encrypted")
        print("     HTTP Server' in the plugin's settings tab first, then pick this.")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "2":
        if not http_enabled:
            sys.exit("HTTP server isn't enabled in the plugin settings yet. "
                      "Enable it in Obsidian and re-run this script, or choose HTTPS.")
        return f"http://127.0.0.1:{http_port}/mcp/"

    print("\nNote: this is a self-signed certificate. If 'claude mcp add' or")
    print("Claude Code refuses the connection over TLS trust, re-run this")
    print("script and pick HTTP instead.")
    return f"https://127.0.0.1:{https_port}/mcp/"


def probe_mcp(url: str, api_key: str, timeout=5) -> bool:
    """True if the MCP endpoint answers an `initialize` request with HTTP 200.
    Certificate checks are skipped: this only ever talks to the plugin's
    self-signed loopback server."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "obsidian-mcp-setup", "version": "1"}},
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status == 200
    except Exception:
        return False


def wait_for_server(url: str, api_key: str, seconds=60) -> bool:
    print(f"\nWaiting up to {seconds}s for the MCP server at {url} ...")
    deadline = time.time() + seconds
    while time.time() < deadline:
        if probe_mcp(url, api_key):
            print("  -> server is up and the API key is accepted.")
            return True
        time.sleep(2)
    print("  -> no response. Obsidian must be running with the vault open and the")
    print("     plugin enabled, or the connector will show 'Failed to connect'.")
    return False


def register_with_claude(url: str, api_key: str, server_name: str):
    manual_cmd = (
        f'claude mcp add --transport http {server_name} {url} '
        f'--header "Authorization: Bearer {api_key}"'
    )
    # Resolve the full path: on Windows `claude` is usually a .cmd shim
    # (npm/nvm), which subprocess can't find by bare name.
    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("\n'claude' CLI not found on PATH. Install Claude Code, then run:")
        print(f"  {manual_cmd}")
        return

    scope_labels = [
        "user (available in every project you open)",
        "local (this project only, not shared)",
        "project (shared with the team via .mcp.json)",
    ]
    idx = prompt_choice("\nMCP scope #: ", scope_labels)
    scope = ["user", "local", "project"][idx]

    # Make re-runs idempotent: drop any earlier registration of this name
    # (e.g. a stale key or URL) so `add` doesn't fail with "already exists".
    subprocess.run([claude_bin, "mcp", "remove", "--scope", scope, server_name],
                   capture_output=True, text=True)

    cmd = [
        claude_bin, "mcp", "add", "--transport", "http", "--scope", scope,
        server_name, url, "--header", f"Authorization: Bearer {api_key}",
    ]
    print("\nRunning: claude mcp add --transport http --scope", scope,
          server_name, url, '--header "Authorization: Bearer ***"')
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
        print("\nRegistration failed. You can add it manually with:")
        print(f"  {manual_cmd}")
        return
    print(f"\nRegistered MCP server '{server_name}'. Verify with: claude mcp list")


def main():
    print("Claude Code <-> Obsidian MCP setup")
    vault = select_vault()
    plugin_id, plugin_dir = install_plugin(vault)
    enable_plugin(vault, plugin_id)
    launch_obsidian(vault)
    api_key, data = wait_for_api_key(plugin_dir)
    url = choose_endpoint(data)
    wait_for_server(url, api_key)
    default_name = "obsidian-" + vault.name.lower().replace(" ", "-")
    name = input(f"\nMCP server name [{default_name}]: ").strip() or default_name
    register_with_claude(url, api_key, name)
    print("\nDone. Try asking Claude Code to search or read a note from your vault to verify the connection.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nAborted.")
