import os
import logging
import tempfile
import subprocess
from typing import Optional, Tuple
import yt_dlp
import whisper
from pathlib import Path

logger = logging.getLogger(__name__)

class YouTubeProcessor:
    """Handles YouTube video downloading and transcription"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="youtube_")
        self.whisper_model = None
        self._load_whisper_model()
    
    def _load_whisper_model(self):
        """Load Whisper model for transcription"""
        try:
            logger.info("Loading Whisper model...")
            # Try to load the smallest model first for better compatibility
            self.whisper_model = whisper.load_model("tiny")
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            # Try alternative loading method
            try:
                logger.info("Trying alternative Whisper loading...")
                import torch
                if torch.cuda.is_available():
                    logger.info("CUDA available, using GPU")
                    self.whisper_model = whisper.load_model("tiny", device="cuda")
                else:
                    logger.info("Using CPU")
                    self.whisper_model = whisper.load_model("tiny", device="cpu")
                logger.info("Whisper model loaded successfully with alternative method")
            except Exception as e2:
                logger.error(f"Alternative loading also failed: {str(e2)}")
                self.whisper_model = None
    
    def download_video(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Download YouTube video and extract audio
        
        Returns:
            Tuple of (video_title, audio_file_path, video_info)
        """
        import time
        try:
            if not self._is_youtube_url(url):
                raise ValueError("Invalid YouTube URL")
            
            logger.info(f"Downloading video from: {url}")
            
            # Optional runtime configs from environment
            yt_proxy = os.getenv('YT_PROXY') or os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
            yt_geo = os.getenv('YT_GEO', 'US')
            yt_cookies_browser = os.getenv('YT_COOKIES_FROM_BROWSER')  # e.g., 'chrome' | 'edge' | 'firefox'
            yt_cookies_file = os.getenv('YT_COOKIES_FILE')  # path to Netscape cookies.txt

            # Configure yt-dlp options with robust network settings and anti-403 measures
            ydl_opts = {
                # Prefer m4a when available, then bestaudio, then best
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                # Let yt-dlp extract audio via FFmpeg postprocessor
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                        'preferredquality': '192'
                    }
                ],
                'prefer_ffmpeg': True,
                'keepvideo': False,
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 20,
                'retries': 5,
                'fragment_retries': 5,
                'extractor_retries': 3,
                'concurrent_fragment_downloads': 1,
                'geo_bypass': True,
                'geo_bypass_country': yt_geo,
                'proxy': yt_proxy,
                'retry_sleep_functions': {
                    'http': lambda _: 2,
                    'fragment': lambda _: 2
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web']
                    }
                },
                'nocheckcertificate': True,
            }

            # Attach cookies if provided
            if yt_cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (yt_cookies_browser,)
            elif yt_cookies_file and os.path.exists(yt_cookies_file):
                ydl_opts['cookiefile'] = yt_cookies_file
            
            last_error: Optional[str] = None
            for attempt in range(1, 4):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Extract video info
                        info = ydl.extract_info(url, download=False)
                        video_title = info.get('title', 'Unknown Title')
                        duration = info.get('duration', 0)
                        
                        # Check video duration (max 2 hours)
                        if duration > 7200:  # 2 hours in seconds
                            raise ValueError(f"Video too long ({duration//60} minutes). Maximum allowed: 2 hours")
                        
                        logger.info(f"Video: {video_title} ({duration//60} minutes)")
                        
                        # Download the video
                        ydl.download([url])
                        
                        # Find the downloaded audio file
                        audio_files = list(Path(self.temp_dir).glob("*.wav"))
                        if not audio_files:
                            # If no wav file, look for other audio formats
                            audio_files = list(Path(self.temp_dir).glob("*.mp3")) + \
                                        list(Path(self.temp_dir).glob("*.m4a")) + \
                                        list(Path(self.temp_dir).glob("*.webm"))
                        
                        if not audio_files:
                            raise ValueError("No audio file found after download")
                        
                        audio_file_path = str(audio_files[0])
                        logger.info(f"Audio file downloaded: {audio_file_path}")
                        
                        return video_title, audio_file_path, f"Duration: {duration//60} minutes"
                except Exception as e:
                    last_error = str(e)
                    # If format-related error, fall back to a very generic format next attempt
                    if 'Requested format is not available' in last_error or 'format is not available' in last_error:
                        logger.warning("Format not available, falling back to generic bestaudio")
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts.pop('postprocessors', None)
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'wav',
                            'preferredquality': '192'
                        }]
                    # If 403 forbidden, try alternate player client and enforce geo/proxy/cookies if present
                    if 'HTTP Error 403' in last_error or 'Forbidden' in last_error or 'returned 403' in last_error:
                        logger.warning("HTTP 403 detected, switching player client and enforcing geo/cookies")
                        ydl_opts['extractor_args'] = {
                            'youtube': {
                                'player_client': ['android', 'web'],
                            }
                        }
                        if yt_proxy:
                            ydl_opts['proxy'] = yt_proxy
                        ydl_opts['geo_bypass'] = True
                        ydl_opts['geo_bypass_country'] = yt_geo
                        if yt_cookies_browser:
                            ydl_opts['cookiesfrombrowser'] = (yt_cookies_browser,)
                        elif yt_cookies_file and os.path.exists(yt_cookies_file):
                            ydl_opts['cookiefile'] = yt_cookies_file
                    logger.warning(f"Download attempt {attempt} failed: {last_error}")
                    # short backoff before retry
                    time.sleep(2 * attempt)
                    continue
            
            raise RuntimeError(last_error or "Unknown download error")
                
        except Exception as e:
            logger.error(f"Video download failed: {str(e)}")
            return None, None, str(e)
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if not self.whisper_model:
                raise ValueError("Whisper model not loaded")
            
            if not os.path.exists(audio_file_path):
                raise ValueError(f"Audio file not found: {audio_file_path}")
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"Audio file size: {file_size} bytes")
            
            if file_size == 0:
                raise ValueError("Audio file is empty")
            
            logger.info(f"Transcribing audio: {audio_file_path}")
            
            # Convert audio to WAV if needed
            wav_path = self._ensure_wav_format(audio_file_path)
            
            # Transcribe the audio with verbose logging
            logger.info("Starting transcription...")
            result = self.whisper_model.transcribe(
                wav_path,
                verbose=True,
                language=None,  # Auto-detect language
                fp16=False  # Disable fp16 for better compatibility
            )
            
            transcript = result["text"].strip()
            
            if not transcript:
                logger.warning("Empty transcript generated")
                # Try with different settings
                logger.info("Retrying with different settings...")
                result = self.whisper_model.transcribe(
                    wav_path,
                    verbose=True,
                    language="en",  # Force English
                    fp16=False
                )
                transcript = result["text"].strip()
            
            if not transcript:
                raise ValueError("No transcript generated after retry")
            
            logger.info(f"Transcription completed. Length: {len(transcript)} characters")
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Audio file path: {audio_file_path}")
            if os.path.exists(audio_file_path):
                logger.error(f"File exists, size: {os.path.getsize(audio_file_path)} bytes")
            return None
    
    def _ensure_wav_format(self, audio_file_path: str) -> str:
        """Convert audio file to WAV format if needed"""
        try:
            file_ext = Path(audio_file_path).suffix.lower()
            
            if file_ext == '.wav':
                logger.info("File is already in WAV format")
                return audio_file_path
            
            # Convert to WAV using ffmpeg
            wav_path = str(Path(audio_file_path).with_suffix('.wav'))
            
            logger.info(f"Converting {file_ext} to WAV format...")
            
            import subprocess
            cmd = [
                'ffmpeg',
                '-i', audio_file_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',      # Mono
                '-y',            # Overwrite output file
                wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                # Return original file if conversion fails
                return audio_file_path
            
            logger.info(f"Successfully converted to WAV: {wav_path}")
            return wav_path
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            # Return original file if conversion fails
            return audio_file_path
    
    def process_youtube_video(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Complete YouTube video processing pipeline
        
        Args:
            url: YouTube video URL
            
        Returns:
            Tuple of (video_title, transcript, video_info)
        """
        try:
            # Download video and extract audio
            video_title, audio_path, video_info = self.download_video(url)
            
            if not video_title or not audio_path:
                return None, None, video_info
            
            # Transcribe audio
            transcript = self.transcribe_audio(audio_path)
            
            if not transcript:
                return video_title, None, "Transcription failed"
            
            return video_title, transcript, video_info
            
        except Exception as e:
            logger.error(f"YouTube processing failed: {str(e)}")
            return None, None, str(e)
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com',
            'www.youtube.com',
            'm.youtube.com',
            'youtu.be',
            'www.youtu.be'
        ]
        
        return any(domain in url.lower() for domain in youtube_domains)
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
