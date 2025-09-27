from pathlib import Path
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import logging

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
    # Оставляем только таблицу users (если она нужна)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            current_lang TEXT DEFAULT 'en',
            custom_prompt TEXT
        )
    ''')
    
    # УДАЛИТЬ таблицу feedback
    conn.commit()
    return conn

# Language settings
LANGUAGES = {
    'en': {
        'welcome': """<b>- Welcome to Article Assistant!</b>

This bot uses RAG (Retrieval-Augmented Generation) to answer questions based on your documents.

<b>- How it works:</b>
1. Upload a file (PDF/TXT)
2. Ask questions about the content
3. Get AI-powered answers

<b>- Take part in our project:</b>
- <a href="https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot">GitHub Repository</a>
- Developer: <a href="https://t.me/Konstantin_vanov">@Konstantin_vanov</a>

<b>Please upload your first document to begin!</b>
""",
        'ask_btn': "Ask question",
        'article_btn': "Enter article",
        'lang_btn': "Change language",
        'prompt_btn': "Prompt settings",
        'summarize_btn': "Summary",
        'lang_changed': "Language changed to English",
        'ask_prompt': "📝 Please enter your question about the article:",
        'processing': "🔍 Searching for answer in the article...",
        'indexing': "📚 Indexing article content...",
        'summarizing': "📝 Generating summary...",
        'summary_title': "📌 Main Points:",
        'no_content': "No content to summarize",
        'after_answer': "💡 You can ask another question or choose another option below",
        'cancel': "Cancel",
        'error': "❌ Error occurred",
        'enter_url': "🌐 Please enter the article URL:",
        'no_article_error': "⚠️ Please add an article first using the 'Enter article' button",
        'invalid_input': "⚠️ Please use the buttons below to interact with me",
        'index_success': "✅ Article indexed successfully!",
        'chunks_info': "Processed {} content chunks.\n\nYou can now ask questions about this article.",
        'prompt_menu': "✏️ Choose prompt option:",
        'default_prompt': "Use default prompt",
        'custom_prompt': "Write new prompt",
        'enter_custom_prompt': "📝 Enter your custom prompt (e.g., 'Answer in technical style'):",
        'prompt_saved': "✅ Custom prompt saved! Now ask your question.",
        'current_prompt': "Current prompt: {}",
        'setup_guide': "🔧 Setup guide: https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot#setup",
        
        # NEW KEYS ADDED:
        'invalid_url': "⚠️ Please enter a valid URL starting with http:// or https://",
        'file_too_large': "⚠️ File is too large (max 10MB). Please upload a smaller file.",
        'file_empty': "⚠️ The file is empty. Please upload a valid file with content.",
        'unsupported_format': "⚠️ Unsupported file format. Please upload PDF or TXT files only.",
        'file_uploaded': "📥 File uploaded successfully! Processing...",
        'file_processed': "File processed",
        'url_processed': "URL processed successfully",
        'file_not_found': "❌ File not found. Please try uploading again.",
        'no_content_found': "❌ No readable content found in the document. Please try another file.",
        'connection_error': "❌ Connection error. Please check your internet connection and try again.",
        'api_key_error': "❌ System error: API key configuration issue. Please contact administrator.",
        'processing_file': "🔍 Processing your file...",
        'document_too_large': "⚠️ Document is too large. Processing in parts...",
        'max_size_exceeded': "❌ Document exceeds maximum processing size. Please use a smaller document."
    },
    'ru': {
        'welcome': """<b>— Добро пожаловать в Article Assistant!</b>

Этот бот использует RAG (Retrieval-Augmented Generation — генерация дополненной реальности) для ответов на вопросы на основе ваших документов.

<b>— Как это работает:</b>
1. Загрузите файл (PDF/TXT)
2. Задайте вопросы по содержанию
3. Получите ответы с помощью ИИ

<b>— Примите участие в нашем проекте:</b>
— <a href="https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot">Репозиторий GitHub</a>
— Разработчик: <a href="https://t.me/Konstantin_vanov">@Konstantin_vanov</a>

<b>Чтобы начать, загрузите свой первый документ!</b>""",
        'ask_btn': "Задать вопрос",
        'article_btn': "Ввести статью",
        'lang_btn': "Изменить язык",
        'prompt_btn': "Настройки промпта",
        'summarize_btn': "Краткое содержание",
        'lang_changed': "Язык изменен на Русский",
        'ask_prompt': "📝 Пожалуйста, введите ваш вопрос по статье:",
        'processing': "🔍 Ищу ответ в статье...",
        'indexing': "📚 Индексирую содержание статьи...",
        'summarizing': "📝 Генерирую краткое содержание...",
        'summary_title': "📌 Основные идеи:",
        'no_content': "Нет контента для суммаризации",
        'after_answer': "💡 Вы можете задать другой вопрос или выбрать другую опцию ниже",
        'cancel': "Отмена",
        'error': "❌ Произошла ошибка",
        'enter_url': "🌐 Введите URL статьи:",
        'no_article_error': "⚠️ Сначала добавьте статью, используя кнопку 'Ввести статью'",
        'invalid_input': "⚠️ Пожалуйста, используйте кнопки ниже для взаимодействия",
        'index_success': "✅ Статья успешно проиндексирована!",
        'chunks_info': "Обработано {} фрагментов контента.\n\nТеперь вы можете задавать вопросы по этой статье.",
        'prompt_menu': "✏️ Выберите вариант промпта:",
        'default_prompt': "Использовать стандартный промпт",
        'custom_prompt': "Написать свой промпт",
        'enter_custom_prompt': "📝 Введите ваш промпт (например, 'Отвечай в техническом стиле'):",
        'prompt_saved': "✅ Промпт сохранён! Теперь задайте вопрос.",
        'current_prompt': "Текущий промпт: {}",
        'setup_guide': "🔧 Инструкция: https://github.com/Konstantin-vanov-hub/Article-Assistant--RAG-Telegram-Bot#setup",
        
        # NEW KEYS ADDED:
        'invalid_url': "⚠️ Пожалуйста, введите корректный URL, начинающийся с http:// или https://",
        'file_too_large': "⚠️ Файл слишком большой (макс. 10MB). Загрузите файл меньшего размера.",
        'file_empty': "⚠️ Файл пустой. Загрузите validный файл с содержимым.",
        'unsupported_format': "⚠️ Неподдерживаемый формат файла. Загружайте только PDF или TXT файлы.",
        'file_uploaded': "📥 Файл успешно загружен! Обрабатываю...",
        'file_processed': "Файл обработан",
        'url_processed': "URL успешно обработан",
        'file_not_found': "❌ Файл не найден. Попробуйте загрузить снова.",
        'no_content_found': "❌ В документе не найдено читаемого содержимого. Попробуйте другой файл.",
        'connection_error': "❌ Ошибка соединения. Проверьте интернет-соединение и попробуйте снова.",
        'api_key_error': "❌ Системная ошибка: проблема с API ключом. Свяжитесь с администратором.",
        'processing_file': "🔍 Обрабатываю ваш файл...",
        'document_too_large': "⚠️ Документ слишком большой. Обрабатываю по частям...",
        'max_size_exceeded': "❌ Документ превышает максимальный размер обработки. Используйте документ меньшего размера."
    }
}

# Conversation states
(
    MAIN_MENU, ENTER_LINK, CHANGE_LANG, 
    ASK_QUESTION, PROMPT_MENU, ENTER_CUSTOM_PROMPT, SUMMARIZE_DOC
) = range(7)

# Default prompts
DEFAULT_PROMPT = {
    'en': """Expert Research Assistant Guidelines:

1. Source Accuracy:
   - Strictly use ONLY the provided context
   - For missing info: "The article doesn't specify"
   - Never hallucinate facts

2. Response Structure:
   - Core Answer (1 bolded sentence)
   - Key Evidence (3-5 bullet points max)
   - Practical Implications (when relevant)
   - Limitations (if data is incomplete)

3. Technical Content:
   - Code: ```python\n...\n``` 
   - Formulas: $E=mc^2$ format
   - Terms: "API (Application Programming Interface)"

4. Language Rules:
   - Match question's language
   - Auto-correct grammar subtly
   - Use ISO standards for dates/units

Context:
{context}

Question: {question}""",

    'ru': """Инструкции для эксперта-аналитика:

1. Точность данных:
   - Используйте ТОЛЬКО предоставленный контекст
   - При отсутствии данных: "В статье не указано"
   - Запрещено "додумывать" факты

2. Структура ответа:
   - Основной ответ (1 предложение жирным)
   - Доказательства (3-5 пунктов списка)
   - Практическое применение (если уместно)
   - Ограничения (при неполных данных)

3. Техническое оформление:
   - Код: ```python\n...\n```
   - Формулы: $E=mc^2$ 
   - Термины: "API (программный интерфейс)"

4. Языковые правила:
   - Соответствие языку вопроса
   - Коррекция ошибок в ответе
   - Даты/единицы в формате ISO

Контекст:
{context}

Вопрос: {question}""",

    'summary_prompt': {
        'en': """Generate a concise 3-5 bullet point summary in English focusing on:
        - Key arguments
        - Unique findings
        - Practical applications
        
        Text: {text}""",
        
        'ru': """Создай краткое содержание на русском (3-5 пунктов) выделяя:
        - Основные тезисы
        - Уникальные выводы
        - Практическое применение
        
        Текст: {text}"""
    }
}

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            current_lang TEXT DEFAULT 'en',
            custom_prompt TEXT,
            request_count INTEGER DEFAULT 0,
            last_request_date TEXT,
            is_premium INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            response_text TEXT,
            feedback_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()



FEEDBACK_BUTTONS = {
    'en': {
        'like_btn': "👍 Like",
        'dislike_btn': "👎 Dislike",
        'feedback_thanks': "Thank you for your feedback!",
        'feedback_error': "Error saving feedback"
    },
    'ru': {
        'like_btn': "👍 Нравится",
        'dislike_btn': "👎 Не нравится", 
        'feedback_thanks': "Спасибо за ваш отзыв!",
        'feedback_error': "Ошибка сохранения отзыва"
    }
}

(
    MAIN_MENU, ENTER_LINK, CHANGE_LANG, 
    ASK_QUESTION, PROMPT_MENU, ENTER_CUSTOM_PROMPT, 
    SUMMARIZE_DOC, FEEDBACK
) = range(8)