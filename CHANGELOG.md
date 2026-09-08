# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-09-08

### Added
- Interactive vault selection (existing, create new, or custom path)
- Automatic plugin installation from GitHub releases
- Vault registration in Obsidian's config (fixes "Vault not found" errors)
- Interactive endpoint selection (HTTPS or HTTP)
- TLS certificate verification auto-healing via truststore
- Fallback to manual `claude mcp add` if CLI not on PATH
- Support for Windows, macOS, and Linux
- Comprehensive error messages and recovery paths
- Idempotent vault registration (re-running doesn't duplicate entries)
- Case-insensitive path matching on Windows

### Security
- Uses secure bearer token authentication
- Generates random vault IDs in Obsidian's config
- Self-signed HTTPS certificate support with warnings
- Local-only MCP server (127.0.0.1)

### Documentation
- Detailed README with troubleshooting section
- Quick start guide
- Contributing guidelines
- Security notes
- Privacy statement

## Future

Potential improvements being considered:
- Support for multiple vaults in a single session
- Automatic HTTP fallback if HTTPS fails
- Built-in vault health check
- One-click unregister command
- Web UI alternative to CLI prompts
