# Article Assistant (RAG Telegram Bot)

[![Python Version](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple.svg)](https://openai.com/)
![RAG](https://img.shields.io/badge/tech-RAG-orange)
![PDF Support](https://img.shields.io/badge/feature-PDF%20Support-red)

**Contact**: [@Konstantin_vanov](https://t.me/Konstantin_vanov)

A Telegram bot for Q&A about articles using Retrieval-Augmented Generation. Indexes web content and PDF files, then provides accurate answers with sources.

![Answer Examples](images/Answer%20example_1.jpg) ![Answer Examples](images/Answer%20example_2.jpg)

## 📖 Table of Contents
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Docker Deployment](#-docker-deployment-recommended)
- [Traditional Installation](#-traditional-installation-without-docker)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)



## 🌟 Features
- **Web Article Processing** - Index content from URLs ✅
- **Multilingual Support** - English/Russian interfaces ✅
- **Q&A System** - Ask questions about indexed content ✅
- **Text Summarization** - Generate key points summaries ✅
- **PDF File Support** - Upload and process PDF documents ✅
- **TXT File Support** - Process text files directly ✅
- **No Request Limits** - Unlimited questions and processing ✅
- **Custom Prompts** - Adjust AI behavior and responses ✅

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ or Docker
- [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot)
- [OpenAI API Key](https://platform.openai.com/api-keys)

### RAG System Workflow

![alt text](images/scheme.png)

## 🐳 Docker Deployment (Recommended)

The easiest way to deploy with all dependencies included:

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot.git
cd Article-Assistant--RAG-Telegram-Bot

# Configure environment variables
cp .env.example .env
# Edit .env with your Telegram Bot Token and OpenAI API Key
nano .env

# Build and start the containers
docker-compose up -d --build

# View logs to verify everything is working
docker-compose logs -f telegram-bot
```

### Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d --build` | Build and start in background |
| `docker-compose down` | Stop and remove containers |
| `docker-compose logs -f telegram-bot` | Follow bot logs |
| `docker-compose restart telegram-bot` | Restart only the bot |
## 🔧 Traditional Installation (Without Docker)

### Clone and Setup
```bash
git clone https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot
cd Article-Assistant--RAG-Telegram-Bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
```

### Environment Variables
Create a `.env` file with:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Launch
```bash
python RAG_bot/bot_main.py
```

## 📱 Usage Examples

1. **Upload a PDF**: Send a PDF file to the bot
2. **Ask questions**: Type your question after indexing
3. **Get summaries**: Use the "Summary" button for key points
4. **Change language**: Use the language button to switch between English/Russian

## 🔧 Troubleshooting

### Common Issues

- **Bot not responding**: Check if all environment variables are set correctly
- **Indexing fails**: Ensure OpenAI API key is valid and has sufficient credits
- **File upload issues**: Check file size limits (max 10MB for files)
- **Vector store errors**: Delete `faiss_index` folder and re-index your content

### Getting Help

- Check the logs: `docker-compose logs -f telegram-bot`
- Verify environment variables are loaded
- Ensure OpenAI API key has sufficient credits

## 🤝 Contributing

We love contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to learn how you can help improve this project.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📜 License

MIT License © 2025 Konstantin. See [LICENSE](LICENSE) file for details.

## 📬 Support

For assistance, please:


- Search [existing issues](https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot/issues)
- Open a [new issue](https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot/issues/new) with detailed information
- Contact [@Konstantin_vanov](https://t.me/Konstantin_vanov) on Telegram