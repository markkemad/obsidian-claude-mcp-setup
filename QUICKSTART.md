# Quick Start

## 30 Seconds

```bash
python setup.py
```

Follow the prompts. That's it.

## Step by Step

1. **Run the script**
   ```bash
   python setup.py
   ```

2. **Pick or create a vault**
   - Choose an existing vault from the list, or
   - Type "Create a new vault" to make a new one
   - If you create one, a folder picker will open

3. **Wait for Obsidian to open**
   Obsidian launches on your vault automatically.

4. **Enable the plugin**
   - Go to Settings → Community plugins
   - If Obsidian shows a "Restricted mode" notice, click to enable community plugins
   - Find "Local REST API with MCP" and toggle it ON
   - Close settings

5. **Back to the terminal**
   - The script is waiting for the plugin to activate
   - Press Enter to continue
   - It will check for the API key

6. **Choose connection mode**
   - Pick option 1 (HTTPS, default), which works for most people
   - Pick option 2 (HTTP) only if option 1 fails in the next step

7. **Name your vault**
   - Give it a name for Claude Code (or keep the default)

8. **Done!**
   The script registers everything with Claude Code and confirms the connection works.

## Next Steps

Open a **new** Claude Code session and try:
```
Search my vault for notes about X
Read "My Note.md"
List all notes with #tag
```

Claude will use your vault over MCP.

## Troubleshooting Quick Links

- **"Vault not found"** → Re-run the script with the same folder
- **"claude" not found** → Copy and run the printed `claude mcp add` command manually
- **HTTPS certificate error** → Re-run, pick HTTP mode, then enable "Enable Non-encrypted HTTP Server" in Obsidian plugin settings
- **TLS error** → Run `pip install truststore` then re-run the script

More details in [README.md](README.md).
