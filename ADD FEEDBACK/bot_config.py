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
    SUMMARIZE_DOCK, FEEDBACK
) = range(8)