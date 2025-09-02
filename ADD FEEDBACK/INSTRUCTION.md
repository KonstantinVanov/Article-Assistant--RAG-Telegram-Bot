# 📊 Feedback System Implementation Guide

## 🌟 Overview
Enhance your RAG Telegram bot with a user feedback system that collects 👍/👎 ratings for AI responses. All feedback is stored in SQLite for comprehensive analysis and continuous improvement.

## If you find any error in the instructions or during installation, please be sure to report it. We will try to fix it as soon as possible.
<a href="https://t.me/Konstantin_vanov">@Konstantin_vanov</a>
## 📁 Files Modified

### 1. **Core Configuration** (`bot_config.py`)
``` bash
# Database initialization with feedback table
def init_db():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
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

# Multi-language feedback buttons
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

# New conversation state
(MAIN_MENU, ENTER_LINK, CHANGE_LANG, ASK_QUESTION, 
 PROMPT_MENU, ENTER_CUSTOM_PROMPT, SUMMARIZE_DOCK, FEEDBACK) = range(8)

```

### 2. **Feedback Handler** (`bot_handlers.py`)
``` bash
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Processes user feedback (like/dislike) and stores it in SQLite database
    with user ID, response text, feedback type, and automatic timestamp
    """
    # Implementation handles both languages and error cases
```
### 3. **Interface Utilities** (`bot_utils.py`)
``` bash
def get_feedback_keyboard(lang: str):
    """
    Returns interactive feedback keyboard with like/dislike buttons
    and cancel option in the user's preferred language
    """
    return ReplyKeyboardMarkup([
        [KeyboardButton(FEEDBACK_BUTTONS[lang]['like_btn']), 
         KeyboardButton(FEEDBACK_BUTTONS[lang]['dislike_btn'])],
        [KeyboardButton(LANGUAGES[lang]['cancel'])]
    ], resize_keyboard=True)
```

### 4. **State Management** (`bot_main.py`)
``` bash
# Integrated feedback state into conversation handler
FEEDBACK: [
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)
],
```

### 5. **Analytics Tool** (`feedback_analyzer.py`) - NEW
``` bash
# Comprehensive feedback analysis utilities:
# - get_feedback_stats(days=7): Daily statistics
# - get_feedback_ratio(): Like/dislike percentages
# - export_feedback_to_csv(): Data export functionality
```

## 📊 Features
Feature	Description	Status
Multi-language	English/Russian support	✅
Persistent Storage	SQLite database	✅
Response Preservation	Saves AI responses	✅
Analytics Ready	Built-in analysis tools	✅
Error Handling	Graceful failure recovery	✅
Time Tracking	Automatic timestamping	✅
🎯 Usage Flow
User Interaction:

Ask question → Get AI response → See feedback buttons

Feedback Collection:

👍 Like: Positive rating

👎 Dislike: Negative rating

📊 All data stored in SQLite

### 🔧 Troubleshooting
Common Issues:
``` bash 
"table already exists" error:

rm user_data.db

python bot_main.py
```
 


