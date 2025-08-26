# Contributing to Article Assistant

First off, thank you for considering contributing to Article Assistant! It's people like you that make this project great.

## How Can I Contribute?

### 🐛 Reporting Bugs
- Use the [Bug Report template](https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot/issues/new?template=bug_report.md)
- Describe the exact steps to reproduce the bug
- Include logs from `docker-compose logs telegram-bot`

### 🚀 Suggesting Enhancements
- Use the [Feature Request template](https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot/issues/new?template=feature_request.md)
- Explain why this enhancement would be useful
- Suggest possible implementation approaches

### 💻 Code Contributions
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Setup

### With Docker (Recommended)
```bash
git clone https://github.com/your-username/Article-Assistant--RAG-Telegram-Bot.git
cd Article-Assistant--RAG-Telegram-Bot
cp .env.example .env
# Edit .env with your test keys
docker-compose up -d --build