# Article Assistant (RAG Telegram Bot)

[![Python Version](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple.svg)](https://openai.com/)
![RAG](https://img.shields.io/badge/tech-RAG-orange)
![PDF Support](https://img.shields.io/badge/feature-PDF%20Support-red)

**Live Bot**: [@RAG_Engineering_bot](https://t.me/RAG_Engineering_bot)

**My contact**: [@Konstantin_vanov](https://t.me/Konstantin_vanov)

Telegram bot for Q&A about articles using Retrieval-Augmented Generation. Indexes web content and PDF files, then provides accurate answers with sources.

![Answer](images/answer1.jpg)

## 🚀 Quick Demo

Try the live demo bot: [@RAG_Engineering_bot](https://t.me/RAG_Engineering_bot)

**Demo Limitations:**
- 3 requests per day
- URL processing only
- No file uploads

**For full features:** Deploy your own instance!

## 🌟 Features
### Available in Demo Version:
- **Web Article Processing** - Index content from URLs
- **Multilingual Support** - English/Russian content
- **Basic Q&A** - Ask questions about indexed content
- **Text Summarization** - Generate key points summaries

### Exclusive to Self-Hosted Version:
- **PDF File Support** - Upload and process PDF documents ✅
- **TXT File Support** - Process text files directly ✅
- **No Request Limits** - Unlimited questions and processing ✅
- **Custom Configuration** - Adjust chunk sizes and parameters ✅

## ⚠️ Demo Version Limitations
- **Maximum 3 requests per day** - Strict rate limiting
- **No PDF/TXT file support** - URL processing only
- **Basic functionality only** - Limited features
- **After daily limit** - Requires self-hosting to continue

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

## Quick Start with Docker

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
Command	Description
``` bash
#Build and start in background
docker-compose up -d --build
#remove containers
docker-compose down	Stop and
#Follow bot logs
docker-compose logs -f telegram-bot
#Restart only the bot
docker-compose restart telegram-bot	
```
### Traditional Installation (Without Docker)
### Clone and setup
``` bash
git clone https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot
cd Article-Assistant--RAG-Telegram-Bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```
### Configuration
``` bash
cp .env.example .env
```
### Add your credentials to .env file

### Launch
python RAG_bot/bot_main.py

### 🤝 Contributing
We love contributions! Please read our Contributing Guide to learn how you can help improve this project.

How to Contribute:
Fork the repository

Create a feature branch (git checkout -b feature/improvement)

Commit your changes (git commit -am 'Add new feature')

Push to the branch (git push origin feature/improvement)

Open a Pull Request

### 📜 License
MIT License © 2025 Konstantin. See LICENSE file for details.

### 📬 Support
For assistance, please:

Check the troubleshooting section

Search existing issues

Open a new issue with detailed information

Contact @Konstantin_vanov on Telegram