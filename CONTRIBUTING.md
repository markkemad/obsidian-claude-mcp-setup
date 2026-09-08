# Contributing

Thanks for your interest in improving this project!

## How to Contribute

### Report a Bug
Found an issue? Open a GitHub issue with:
- What you did
- What you expected to happen
- What actually happened
- Your OS and Python version
- Any error messages or logs

### Suggest an Enhancement
Have an idea? Open a GitHub issue describing:
- What problem it solves
- How users would benefit
- Any alternative approaches you've considered

### Submit a Pull Request
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Make your changes
4. Test on both Windows and Unix-like systems if possible
5. Commit with a clear message
6. Push to your fork
7. Open a pull request with a description of your changes

## Development

### Setup
```bash
git clone https://github.com/markkemad/obsidian-claude-mcp-setup.git
cd obsidian-claude-mcp-setup
pip install truststore  # Optional but recommended for testing
```

### Testing
Before submitting a PR, test the script:
- On a fresh Obsidian vault (create a new one via the setup script)
- On at least one of: Windows, macOS, Linux
- With both HTTPS and HTTP endpoints (if applicable)
- With an existing vault and a new vault

### Code Style
- Keep lines under 100 characters where reasonable
- Use descriptive variable names
- Add comments only for non-obvious logic
- Follow PEP 8 conventions

## Areas for Help

- Cross-platform testing (especially macOS and Linux)
- Better error messages for edge cases
- Documentation improvements
- Feature requests for vault workflows

## Questions?

Open an issue or discussion on the GitHub repository.

Thanks for contributing!
