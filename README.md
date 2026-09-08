# Obsidian MCP Setup

Connect Claude Code to your Obsidian vault over the Model Context Protocol (MCP). This script automates the entire setup process: installing the plugin, registering the vault, and configuring Claude Code to access your notes.

## What This Does

This script:
- Discovers your existing Obsidian vaults (or lets you create a new one)
- Downloads and installs the "Local REST API with MCP" plugin into your vault
- Enables the plugin in Obsidian
- Generates a secure API key
- Registers the connection with Claude Code
- Handles TLS certificate verification issues automatically

Once set up, Claude Code can search, read, and write notes in your vault, enabling vault-aware RAG, project memory, and knowledge management workflows.

## Requirements

- Python 3.8 or later
- Obsidian desktop app
- Claude Code CLI (installed and on your PATH)
- Windows, macOS, or Linux

## Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/markkemad/obsidian-claude-mcp-setup.git
   cd obsidian-claude-mcp-setup
   ```

2. **Ensure Python is installed**
   ```bash
   python --version
   ```
   If Python isn't installed, download it from [python.org](https://www.python.org) or use your system's package manager.

3. **(Optional) Install the truststore package for corporate networks**
   If you're behind a corporate proxy or firewall, install this to fix TLS certificate issues:
   ```bash
   pip install truststore
   ```

## Usage

Run the script:
```bash
python setup.py
```

The script will guide you through these steps:

1. **Select a vault.** Pick from your existing Obsidian vaults, create a new one, or enter a custom path.
2. **Enable the plugin.** The script installs it automatically, then Obsidian opens so you can approve it (a one-click safety step inside Obsidian that no script can bypass).
3. **Verify the plugin.** Press Enter when the REST API plugin shows "ON" in Community plugins.
4. **Choose a connection mode.** HTTPS (default, self-signed cert) or HTTP (unencrypted, local-only).
5. **Name the MCP server.** Give your vault a name for Claude Code.
6. **Register with Claude Code.** The script runs `claude mcp add` to set it up.

## Troubleshooting

### "Vault not found" when Obsidian launches
The script registers your vault in Obsidian's own config, so this should not happen. If it does, re-run the script and pick the same vault folder.

### "claude" CLI not found
If the script can't find the `claude` command, manually run the printed command in your terminal. Make sure Claude Code is installed and the CLI is on your PATH.

### HTTPS certificate errors in Claude Code
Claude Code rejects self-signed certificates by default. Run the script again, select your vault, choose HTTP mode, and enable the "Enable Non-encrypted HTTP Server" toggle in Obsidian's plugin settings.

### TLS certificate verification failed
If you get an SSL error on startup, install the truststore package:
```bash
pip install truststore
```
Then re-run the script.

### "Obsidian" process not found or server not reachable
Make sure Obsidian is actually running with your vault open. The REST API server only exists inside the Obsidian process. If you closed Obsidian, restart it on that vault.

## How to Use After Setup

Open a new Claude Code session and ask it to work with your vault:

```
Search my vault for notes about project X
Read the file "My Note.md"
List all notes with the tag #work
```

Claude Code will use the registered MCP server to access your vault in real time.

## How It Works

This script automates the standard MCP connection flow:

1. **Plugin installation.** Downloads the Obsidian "Local REST API with MCP" plugin (v5.1.0+) and installs it into your vault's `.obsidian/plugins/` folder.
2. **Vault registration.** Adds your vault to Obsidian's own registry (`obsidian.json`) so Obsidian can find it.
3. **API key generation.** The plugin auto-generates a 256-bit API key on first load.
4. **MCP registration.** Registers an HTTP connection in Claude Code's `.claude.json` config with the plugin's endpoint and API key.
5. **Health check.** Claude Code immediately tests the connection to verify everything works.

The connection is local-only (localhost) and uses a bearer token for authentication. If you're using HTTP mode, traffic is unencrypted but confined to your machine.

## Security Notes

- The API key is stored in Obsidian's plugin config and Claude Code's MCP registry, both on your local machine
- The MCP server only listens on `127.0.0.1` (localhost), not the network
- If using HTTP mode, traffic is unencrypted but local-only
- If using HTTPS mode, the certificate is self-signed and generated locally

Never share your API key or run this script with untrusted users on your machine.

## Privacy

This script:
- Runs entirely locally on your machine
- Does not phone home or send data anywhere
- Does not modify Obsidian's app code or settings outside of installing the plugin
- Only needs network access to download the plugin from GitHub on first run

## License

MIT License. See LICENSE file for details.

## Support

For issues with the script itself, open an issue on GitHub.

For issues with the plugin, see [coddingtonbear/obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api).

For Claude Code questions, see the [Claude Code documentation](https://code.claude.com/docs).

## What's Next?

After setup, you can:
- Use Claude Code to search and organize your vault
- Build workflows that read from your vault and write summaries back
- Connect multiple vaults to different Claude sessions
- Use your vault as persistent project memory across sessions

Happy note-taking!
