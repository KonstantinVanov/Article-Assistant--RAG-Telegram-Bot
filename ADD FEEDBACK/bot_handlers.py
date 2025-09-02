async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    has_article = context.user_data.get('has_article', False)
    

    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            "Отменено" if lang == 'ru' else "Canceled",
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    

    if text not in [FEEDBACK_BUTTONS[lang]['like_btn'], FEEDBACK_BUTTONS[lang]['dislike_btn']]:
        await update.message.reply_text(
            LANGUAGES[lang]['invalid_input'],
            reply_markup=get_feedback_keyboard(lang)
        )
        return FEEDBACK
    

    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        

        feedback_type = 'like' if text == FEEDBACK_BUTTONS[lang]['like_btn'] else 'dislike'
        response_text = context.user_data.get('last_response', '')
        

        if response_text and len(response_text) > 1000:
            response_text = response_text[:1000] + "..."
        
        cursor.execute(
            'INSERT INTO feedback (user_id, response_text, feedback_type) VALUES (?, ?, ?)',
            (user_id, response_text, feedback_type)
        )
        conn.commit()
        conn.close()
        
        logger.info(f"Feedback saved: user_id={user_id}, type={feedback_type}")
        
        await update.message.reply_text(
            FEEDBACK_BUTTONS[lang]['feedback_thanks'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        
    except Exception as e:
        logger.error(f"Feedback database error: {str(e)}")

        await update.message.reply_text(
            FEEDBACK_BUTTONS[lang]['feedback_error'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
    
    return MAIN_MENU