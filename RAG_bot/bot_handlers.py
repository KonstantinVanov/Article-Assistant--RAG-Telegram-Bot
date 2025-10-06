from telegram import Update
from telegram.ext import ContextTypes
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from bot_utils import (
    get_main_menu_keyboard, get_prompt_menu_keyboard, 
    get_lang_menu_keyboard, get_cancel_keyboard
)
from bot_config import (
    LANGUAGES, DEFAULT_PROMPT, MAIN_MENU, ENTER_CUSTOM_PROMPT,
    ENTER_LINK, ASK_QUESTION, CHANGE_LANG, PROMPT_MENU, ENTER_YOUTUBE_URL, logger
)
from Requests import answer
from indexer import reindex, reindex_video_transcript
from youtube_processor import YouTubeProcessor
import os

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lang'] = 'en'
    context.user_data['has_article'] = False
    context.user_data['current_prompt'] = DEFAULT_PROMPT['en']
    lang = context.user_data['lang']
    
    await update.message.reply_text(
        text=LANGUAGES[lang]['welcome'],
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(lang, has_article=False),
        disable_web_page_preview=True
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    valid_commands = [
        LANGUAGES[lang]['ask_btn'],
        LANGUAGES[lang]['article_btn'],
        LANGUAGES[lang]['youtube_btn'],
        LANGUAGES[lang]['lang_btn'],
        LANGUAGES[lang]['prompt_btn'],
        LANGUAGES[lang]['summarize_btn'],
        LANGUAGES[lang]['cancel']
    ]
    
    if text not in valid_commands:
        await update.message.reply_text(
            LANGUAGES[lang]['invalid_input'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['ask_btn']:
        if not has_article:
            await update.message.reply_text(
                LANGUAGES[lang]['no_article_error'],
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            return MAIN_MENU
        
        await update.message.reply_text(
            LANGUAGES[lang]['ask_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ASK_QUESTION
    
    if text == LANGUAGES[lang]['article_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_url'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_LINK
    
    if text == LANGUAGES[lang]['youtube_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_youtube_url'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_YOUTUBE_URL
    
    if text == LANGUAGES[lang]['lang_btn']:
        await update.message.reply_text(
            LANGUAGES[lang].get('select_lang', 'Select language:'),
            reply_markup=get_lang_menu_keyboard()
        )
        return CHANGE_LANG
    
    if text == LANGUAGES[lang]['prompt_btn']:
        await update.message.reply_text(
            LANGUAGES[lang]['prompt_menu'],
            reply_markup=get_prompt_menu_keyboard(lang)
        )
        return PROMPT_MENU
    
    if text == LANGUAGES[lang]['summarize_btn']:
        if not has_article:
            await update.message.reply_text(
                LANGUAGES[lang]['no_article_error'],
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            return MAIN_MENU
        return await handle_summarize(update, context)
    
    return MAIN_MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    if not has_article:
        await update.message.reply_text(
            LANGUAGES[lang]['no_article_error'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            LANGUAGES[lang].get('canceled', 'Canceled'),
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    await update.message.reply_text(LANGUAGES[lang]['processing'])
    
    try:
        current_prompt = context.user_data.get('current_prompt', DEFAULT_PROMPT[lang])
        full_query = f"{current_prompt}\n\nQuestion: {text}"
        
        response = answer(full_query)
        
        await update.message.reply_text(
            response,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            LANGUAGES[lang]['after_answer'],
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        
    except Exception as e:
        error_msg = f"❌ {LANGUAGES[lang].get('error', 'Error')}: {str(e)}"
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
    
    return MAIN_MENU

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    
    def get_text(key, default):
        return LANGUAGES[lang].get(key, LANGUAGES['en'].get(key, default))
    
    if update.message.text and update.message.text == get_text('cancel', 'Cancel'):
        await update.message.reply_text(
            get_text('cancel', 'Canceled'),
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    file_path = None
    source_type = None
    
    try:
        if update.message.text:
            text = update.message.text.strip()
            
            if text == get_text('cancel', 'Cancel'):
                await update.message.reply_text(
                    get_text('cancel', 'Canceled'),
                    reply_markup=get_main_menu_keyboard(lang, has_article)
                )
                return MAIN_MENU
            
            if not text.startswith(('http://', 'https://')):
                await update.message.reply_text(
                    get_text('invalid_url', 'Please enter a valid URL'),
                    reply_markup=get_cancel_keyboard(lang)
                )
                return ENTER_LINK
            
            source = text
            source_type = 'url'
        
        elif update.message.document:
            document = update.message.document
            file_name = document.file_name
            file_size = document.file_size
            
            MAX_FILE_SIZE = 10 * 1024 * 1024
            if file_size > MAX_FILE_SIZE:
                await update.message.reply_text(
                    get_text('file_too_large', 'File too large'),
                    reply_markup=get_cancel_keyboard(lang)
                )
                return ENTER_LINK
            
            ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
            if ext not in ['pdf', 'txt']:
                await update.message.reply_text(
                    get_text('unsupported_format', 'Unsupported format'),
                    reply_markup=get_cancel_keyboard(lang)
                )
                return ENTER_LINK
            
            await update.message.reply_text(
                get_text('file_uploaded', 'File uploaded')
            )
            
            file = await document.get_file()
            file_path = f"temp_{update.update_id}_{file_name}"
            await file.download_to_drive(file_path)
            
            source = file_path
            source_type = 'file'
        
        else:
            await update.message.reply_text(
                get_text('invalid_input', 'Invalid input'),
                reply_markup=get_cancel_keyboard(lang)
            )
            return ENTER_LINK
        
        await update.message.reply_text(
            get_text('indexing', 'Indexing'),
            reply_markup=get_cancel_keyboard(lang)
        )
        
        num_chunks = reindex(source)
        
        context.user_data['has_article'] = True
        context.user_data['last_source_type'] = source_type
        context.user_data['last_source'] = source if source_type == 'url' else file_name
        
        await update.message.reply_text(get_text('index_success', 'Indexed successfully'))
        
        chunks_message = get_text('chunks_info', 'Processed {} chunks').format(num_chunks)
        
        if source_type == 'file':
            file_processed = get_text('file_processed', 'File processed')
            chunks_message += f"\n📄 {file_processed}: {file_name}"
        else:
            url_processed = get_text('url_processed', 'URL processed')
            chunks_message += f"\n🌐 {url_processed}"
        
        await update.message.reply_text(
            chunks_message,
            reply_markup=get_main_menu_keyboard(lang, has_article=True),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Indexing error: {str(e)}")
        error_msg = get_text('error', 'Error occurred')
        await update.message.reply_text(
            f"{error_msg}: {str(e)}",
            reply_markup=get_main_menu_keyboard(lang, False)
        )
        
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing temp file {file_path}: {str(e)}")
    
    return MAIN_MENU

async def handle_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    
    if not context.user_data.get('has_article', False):
        await update.message.reply_text(LANGUAGES[lang]['no_article_error'])
        return MAIN_MENU
    
    await update.message.reply_text(LANGUAGES[lang]['summarizing'])
    
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.proxyapi.ru/openai/v1"
        )
        
        vector_store = FAISS.load_local(
            folder_path="./faiss_index",
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )

        docs = vector_store.similarity_search("Summarize key points", k=4)
        
        if not docs:
            await update.message.reply_text(LANGUAGES[lang]['no_content'])
            return MAIN_MENU
        
        summary_prompt = DEFAULT_PROMPT['summary_prompt'][lang].format(
            text="\n\n".join([doc.page_content[:500] for doc in docs])
        )
        
        response = answer(summary_prompt)
        
        await update.message.reply_text(
            f"{LANGUAGES[lang]['summary_title']}\n\n{response}",
            reply_markup=get_main_menu_keyboard(lang, has_article=True),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        await update.message.reply_text(
            f"❌ {LANGUAGES[lang]['error']}: {str(e)}",
            reply_markup=get_main_menu_keyboard(lang, True)
        )
    
    return MAIN_MENU

async def handle_prompt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            LANGUAGES[lang].get('canceled', 'Canceled'),
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['default_prompt']:
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        await update.message.reply_text(
            LANGUAGES[lang]['current_prompt'].format(DEFAULT_PROMPT[lang]),
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    if text == LANGUAGES[lang]['custom_prompt']:
        await update.message.reply_text(
            LANGUAGES[lang]['enter_custom_prompt'],
            reply_markup=get_cancel_keyboard(lang)
        )
        return ENTER_CUSTOM_PROMPT
    
    return PROMPT_MENU

async def handle_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    text = update.message.text
    
    if text == LANGUAGES[lang]['cancel']:
        await update.message.reply_text(
            LANGUAGES[lang].get('canceled', 'Canceled'),
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
        return MAIN_MENU
    
    context.user_data['current_prompt'] = text
    await update.message.reply_text(
        LANGUAGES[lang]['prompt_saved'],
        reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
    )
    return MAIN_MENU

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_map = {"English 🇬🇧": 'en', "Русский 🇷🇺": 'ru'}
    text = update.message.text
    
    if text in lang_map:
        lang = lang_map[text]
        context.user_data['lang'] = lang
        context.user_data['current_prompt'] = DEFAULT_PROMPT[lang]
        
        await update.message.reply_text(
            LANGUAGES[lang]['lang_changed'],
            reply_markup=get_main_menu_keyboard(lang, context.user_data.get('has_article', False))
        )
    else:
        current_lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            LANGUAGES[current_lang].get('select_lang', 'Please select language'),
            reply_markup=get_lang_menu_keyboard()
        )
    
    return MAIN_MENU

async def handle_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube video URL processing"""
    lang = context.user_data.get('lang', 'en')
    has_article = context.user_data.get('has_article', False)
    text = update.message.text
    
    def get_text(key, default):
        return LANGUAGES[lang].get(key, LANGUAGES['en'].get(key, default))
    
    if text == get_text('cancel', 'Cancel'):
        await update.message.reply_text(
            get_text('cancel', 'Canceled'),
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
        return MAIN_MENU
    
    try:
        # Validate YouTube URL
        if not text.startswith(('http://', 'https://')):
            await update.message.reply_text(
                get_text('invalid_youtube_url', 'Please enter a valid YouTube URL'),
                reply_markup=get_cancel_keyboard(lang)
            )
            return ENTER_YOUTUBE_URL
        
        # Check if it's a YouTube URL
        youtube_domains = ['youtube.com', 'youtu.be']
        if not any(domain in text.lower() for domain in youtube_domains):
            await update.message.reply_text(
                get_text('invalid_youtube_url', 'Please enter a valid YouTube URL'),
                reply_markup=get_cancel_keyboard(lang)
            )
            return ENTER_YOUTUBE_URL
        
        # Initialize YouTube processor
        processor = YouTubeProcessor()
        
        # Download video
        await update.message.reply_text(
            get_text('downloading_video', 'Downloading video...'),
            reply_markup=get_cancel_keyboard(lang)
        )
        
        video_title, transcript, video_info = processor.process_youtube_video(text)
        
        if not video_title or not transcript:
            # Provide more detailed error information
            if not video_title:
                error_msg = get_text('download_failed', 'Failed to download video')
            elif not transcript:
                error_msg = get_text('transcription_failed', 'Failed to transcribe video')
                # Add specific error details if available
                if video_info and "Transcription failed" in video_info:
                    error_msg += f"\n\nДетали ошибки: {video_info}"
            else:
                error_msg = video_info or get_text('youtube_processing_error', 'Error processing YouTube video')
            
            await update.message.reply_text(
                f"❌ {error_msg}",
                reply_markup=get_main_menu_keyboard(lang, has_article)
            )
            processor.cleanup()
            return MAIN_MENU
        
        # Transcribe video
        await update.message.reply_text(
            get_text('transcribing_video', 'Transcribing video content...'),
            reply_markup=get_cancel_keyboard(lang)
        )
        
        # Index the transcript
        await update.message.reply_text(
            get_text('indexing', 'Indexing video content...'),
            reply_markup=get_cancel_keyboard(lang)
        )
        
        num_chunks = reindex_video_transcript(video_title, transcript, video_info)
        
        # Update user data
        context.user_data['has_article'] = True
        context.user_data['last_source_type'] = 'youtube'
        context.user_data['last_source'] = video_title
        
        # Send success message
        success_message = get_text('video_processed', 'Video processed successfully!')
        success_message += f"\n\n{get_text('video_title', 'Video: {}').format(video_title)}"
        if video_info:
            success_message += f"\n{get_text('video_duration', 'Duration: {}').format(video_info)}"
        success_message += f"\n{get_text('transcript_length', 'Transcript length: {} characters').format(len(transcript))}"
        
        chunks_message = get_text('chunks_info', 'Processed {} chunks').format(num_chunks)
        chunks_message += "\n\nYou can now ask questions about this video content."
        
        await update.message.reply_text(success_message)
        await update.message.reply_text(
            chunks_message,
            reply_markup=get_main_menu_keyboard(lang, has_article=True),
            parse_mode="Markdown"
        )
        
        # Cleanup
        processor.cleanup()
        
    except Exception as e:
        logger.error(f"YouTube processing error: {str(e)}")
        error_msg = get_text('youtube_processing_error', 'Error processing YouTube video: {}').format(str(e))
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_menu_keyboard(lang, has_article)
        )
    
    return MAIN_MENU