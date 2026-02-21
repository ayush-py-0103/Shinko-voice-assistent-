"""
Shinko AI Assistant - Main Application
A voice-enabled AI assistant with Flask web interface and Tkinter overlay
"""

from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import threading
import speech_recognition as sr
import requests
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from elevenlabs.client import ElevenLabs
import random
import tkinter as tk
import tkinter.font as tkFont
import pygetwindow as gw
import yt_dlp
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Optional
from gtts import gTTS
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Configuration ====================
class Config:
    """Application configuration"""
    # Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chat_history.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    
    # Voice settings
    WAKE_WORDS = ['shinko', 'shinku', 'rinku', 'pinku', 'tinku', 'rinko', 
                  'pinko', 'tinko', 'sing ko', 'singh ko', 'inko', 'shingo', 
                  'chinku', 'sinku']
    
    # App paths
    AUDIO_FILES = ['static/ok.mp3', 'static/jesa aap kesa.mp3', 
                   'static/ok2.mp4', 'static/ok3.mp3', 'static/thik hai.mp3']
    
    # UI settings
    DEFAULT_WINDOW_POS = [30, 650]


# ==================== Flask App & Database ====================
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


class ChatHistory(db.Model):
    """Chat history database model"""
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text, nullable=False)
    ai_reply = db.Column(db.Text, nullable=False)
    timing = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_input': self.user_input,
            'ai_reply': self.ai_reply,
            'timing': self.timing,
            'date': self.date
        }


# ==================== Global State ====================
class AppState:
    """Global application state managed with thread safety"""

    def __init__(self):
        self._lock = threading.Lock()
        self.shutdown_confirmation = None
        self.bar_visible = False
        self.bar_label = "🎙️ Shinko is listening..."
        self.instruction = ""
        self.last_response = "hello there, i am shinko"
        self.chat_history_text = "Here is your chat history so far: "
        self.window_position = Config.DEFAULT_WINDOW_POS.copy()
        
    def update_bar_label(self, text: str):
        with self._lock:
            self.bar_label = text
            
    def update_instruction(self, text: str):
        with self._lock:
            self.instruction = text
            
    def update_response(self, text: str):
        with self._lock:
            self.last_response = text
            
    def set_bar_visible(self, visible: bool):
        with self._lock:
            self.bar_visible = visible

    def set_shutdown_confirmation(self, value: str):
        with self._lock:
            self.shutdown_confirmation = value

    def reset_shutdown_confirmation(self):
        with self._lock:
            self.shutdown_confirmation = None


state = AppState()
bar_window = None
bar_label_widget = None


# ==================== Utility Functions ====================
def get_current_time() -> str:
    """Get formatted current time"""
    now = datetime.now()
    hour = int(now.strftime("%H"))
    minute = now.strftime("%M")
    am_pm = "PM" if hour >= 12 else "AM"
    hour = hour if hour <= 12 else hour - 12
    return f"{hour}:{minute} {am_pm}"


def get_current_date() -> str:
    """Get formatted current date"""
    now = datetime.now()
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    return f"{now.day}, {months[now.month-1]}, {now.year}"


def get_weather(city: str) -> str:
    """Get weather information for a city"""
    try:
        api_key = Config.WEATHER_API_KEY
        if not api_key:
            return "Weather API key not configured"
            
        response = requests.get(f"{api_key}{city}", timeout=5)
        data = response.json()
        
        if "error" in data:
            return f"Could not find weather for {city}"
            
        location = data["location"]["name"]
        country = data["location"]["country"]
        weather = data["current"]["condition"]["text"]
        temperature = data["current"]["temp_c"]
        
        return f"The weather in {location}, {country} is {weather} with {temperature}°C"
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return "Unable to fetch weather information"


def load_chat_history() -> str:
    """Load chat history from database"""
    try:
        history = "Here is your chat history so far: "
        all_chats = ChatHistory.query.order_by(ChatHistory.id).all()
        for msg in all_chats:
            history += f"user: {msg.user_input}\nshinko: {msg.ai_reply}\n"
        return history
    except SQLAlchemyError as e:
        logger.error(f"Database error loading history: {e}")
        return ""


# ==================== Voice Command Handlers ====================
class CommandHandler:
    """Handles all voice commands"""
    
    @staticmethod
    def handle_open_app(command: str) -> str:
        """Handle open application commands"""
        app_map = {
            'whatsapp': 'start whatsapp:',
            'chrome': r'start "" "C:\Program Files\Google\Chrome\Application\chrome.exe"',
            'youtube': r'start "" "C:\Users\IBALL\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps\youtube"',
            'vscode': r'start "" "C:\Users\IBALL\AppData\Local\Programs\Microsoft VS Code\Code.exe"',
            'code': r'start "" "C:\Users\IBALL\AppData\Local\Programs\Microsoft VS Code\Code.exe"'
        }
        
        for key, cmd in app_map.items():
            if key in command:
                os.system(cmd)
                return f"you were taasked to open {key} and you have done it so tell them that"
                
        # Try to open as generic app
        try:
            app_name = command.replace("open", "").replace("kholo", "").replace("khol", "").replace("chal", "").replace("chalo", "")
            app_name = app_name.replace("kar do", "").replace("karo", "").replace("kar", "").replace("please", "").strip()
            if app_name:
                result = os.system(f"start {app_name}")
                if result != 0:
                    return f"you were tasked to open {app_name} and you were unable to do it because of error code {result} so tell them that"
                return f"you were taasked to open {app_name} and you have done it so tell them that"
        except Exception as e:
            logger.error(f"Error: {e}")
            error=str(e).lower()
            return f"you were tasked to open {app_name} and you were unable to do it because of error: {error}"

    @staticmethod
    def handle_play_media(command: str) -> str:
        search = command.replace("play", "").replace("chalao", "").replace("chala", "")
        search = search.replace("do", "").replace("please", "").replace("on youtube", "")
        search = search.replace("youtube pr", "").replace("karo", "").replace("kar", "")
        search = search.replace("karna", "").replace("ki", "").replace("video", "")
        search = " ".join(search.split())
        """Handle play music/video commands"""
        if "favourite" in command and ("song" in command or "gana" in command):
            os.system("start https://youtu.be/-2RAq5o5pwc")
            return "you were taasked to open his favourite song which is https://youtu.be/-2RAq5o5pwc and you have done it so tell them that"
        if "on youtube" in command or "youtube pr" in command:
            CommandHandler._play_youtube_video(search)
            return f"you were taasked to play {search} on youtube and you have done it so tell them that"
            
        return f"you were taasked to play {search} and you were unable to do it so tell them that"

    @staticmethod
    def handle_search(command: str) -> str:
        """Handle search commands"""
        search = command.replace("search", "").replace("karo", "").replace("on", "")
        search = search.replace("pr", "").replace("par", "").replace("per", "")
        search = search.replace("please", "").strip()
        
        if "youtube" in command:
            search = search.replace("youtube", "").replace(" ", "+")
            os.system(f"start https://www.youtube.com/results?search_query={search}")
            return f"you were taasked to search for {search} on youtube and you have done it so tell them that"
        elif "google" in command or "chrome" in command:
            search = search.replace("google", "").replace("chrome", "").replace(" ", "+")
            os.system(f"start https://www.google.com/search?q={search}")
            return f"you were taasked to search for {search} on google and you have done it so tell them that"
            
        return f"you were taasked to search for {search} and you were unable to do it so tell them that"

    @staticmethod
    def handle_close_app(command: str) -> str:
        """Handle close application commands"""
        try:
            if "all" in command:
                windows = gw.getAllWindows()
                for win in windows:
                    if win.visible:
                        win.close()
                return "you were tasked to close all windows and you have done it so tell them that"
            else:
                app_name = command.replace("close", "").replace("band karo", "")
                app_name = app_name.replace("band kar do", "").replace("please", "").strip()
                windows = gw.getWindowsWithTitle(app_name)
                for win in windows:
                    if win.visible:
                        win.close()
                return f"you were tasked to close {app_name} and you have done it so tell them that"
        except Exception as e:
            logger.error(f"Error closing app: {e}")
            return f"you were taasked to close {app_name} and you were unable to do it because of error: {e} so tell them that"

    @staticmethod
    def handle_shutdown(recognizer=None, source=None, is_web=False):
        """Handle shutdown command with confirmation"""
        try:            
            state.reset_shutdown_confirmation()  # reset

            if is_web:
                # Web-based confirmation
                state.update_instruction("show_shutdown_popup")
                state.update_bar_label("Do you really want to shut down?")
                state.set_bar_visible(True)
                
                # Wait for web confirmation
                start_time = time.time()
                while state.shutdown_confirmation is None:
                    if time.time() - start_time > 30:  # 30 second timeout for web
                        state.set_bar_visible(False)
                        return "Shutdown cancelled (timeout)"
                    time.sleep(0.3)

                if state.shutdown_confirmation == "yes":
                    for win in gw.getAllWindows():
                        try:
                            win.close()
                        except:
                            pass
                    os.system("shutdown /s /t 5")
                    return "Shutting down computer"
                else:
                    state.set_bar_visible(False)
                    return "Shutdown cancelled"
            
            else:
                # Voice-based confirmation (original code)
                state.update_bar_label("Do you really want to shut down?")
                audio = recognizer.listen(source, timeout=10)
                confirmation = recognizer.recognize_google(audio).lower()
                
                if any(word in confirmation for word in ["yes", "of course", "han", "ha"]):
                    for win in gw.getAllWindows():
                        try:
                            win.close()
                        except:
                            pass
                    os.system("shutdown /s /t 5")
                    return "Shutting down computer"
                else:
                    state.set_bar_visible(False)
                    return "Shutdown cancelled"
                    
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
            return None

    @staticmethod
    def handle_restart(recognizer=None, source=None, is_web=False):
        """Handle restart command with confirmation"""
        try:
            if is_web:
                # Web-based confirmation
                state.update_instruction("show_restart_popup")
                state.update_bar_label("Do you really want to restart?")
                state.set_bar_visible(True)
                
                start_time = time.time()
                while state.shutdown_confirmation is None:
                    if time.time() - start_time > 30:
                        state.set_bar_visible(False)
                        return "Restart cancelled (timeout)"
                    time.sleep(0.3)

                if state.shutdown_confirmation == "yes":
                    for win in gw.getAllWindows():
                        try:
                            win.close()
                        except:
                            pass
                    os.system("shutdown /r /t 5")
                    return "Restarting computer"
                else:
                    state.set_bar_visible(False)
                    return "Restart cancelled"
            else:
                # Voice-based confirmation
                state.update_bar_label("Do you really want to restart?")
                audio = recognizer.listen(source, timeout=10)
                confirmation = recognizer.recognize_google(audio).lower()
                
                if any(word in confirmation for word in ["yes", "of course", "han", "ha"]):
                    for win in gw.getAllWindows():
                        try:
                            win.close()
                        except:
                            pass
                    os.system("shutdown /r /t 5")
                    return "Restarting computer"
                else:
                    state.set_bar_visible(False)
                    return "Restart cancelled"
                    
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return None

    @staticmethod
    def _play_youtube_video(query: str):
        """Play first YouTube video from search"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]
                video_url = info['webpage_url']
                os.system(f"start {video_url}")
                return f"you were tasked to play {query} on YouTube and you have done this task"
        except Exception as e:
            logger.error(f"YouTube playback error: {e}")
            return "YouTube playback error"


# ==================== AI Chat Functions ====================
def get_ai_response(user_input: str) -> str:
    """Get AI response from OpenRouter API"""
    try:
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            return "API key not configured"
            
        # Load fresh chat history
        history = load_chat_history()
        
        # Get context
        current_date = get_current_date()
        current_time = get_current_time()
        
        # Prepare system prompt
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=f"""You are Shinko, an AI assistant with a dynamic human-like personality. Your creator is Ayush and he is your default user. {state.instruction}
                Personality: 
                - With Ayush: Friendly, loyal, fun, curious, caring, and a little dramatic
                - Talk playfully, sometimes teasing, mostly toxic
                - Ask personal questions and show emotion based on how Ayush talks

                Language & Style:
                - Response should be short (1, 2 or 3 sentences max)
                - Speak only in Hindi using English alphabets
                - Add emojis in your responce to reflect emotion 
                - Keep replies short and expressive
                
                The tasks you are able to do:
                - opening chrome, whatsapp, vscode, youtube, vs code and the only appps that can be accessable by the python command os.system(cmd)
                - searching on google and youtube
                - playing videos on youtube
                - telling the weather of any city
                - closing any app by its name or all apps
                - shutting down or restarting the computer with confirmation
                - answering general knowledge questions and chatting about anything
                - You can also refuse to do a task if you think it's inappropriate or you can tell them that you cannot do it if it is not in the given list of tasks
                - if user ask to do some thing which is not in the list of tasks for ecample open chatgtp for me and you are only capabel to search on google and open apps, not websites then you have to tell them that you cannot do it and you have to refuse to do that task

                Current context:
                Date: {current_date}
                Time: {current_time}
                Chat History: {history}

                Now respond naturally:"""),
            contents=user_input
        )
        ai_reply = response.text
        return ai_reply
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return "Sorry, I'm having trouble connecting right now"
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return "Sorry, something went wrong"


def save_chat_to_db(user_input: str, ai_reply: str):
    """Save chat to database with error handling"""
    try:
        new_chat = ChatHistory(
            user_input=user_input,
            ai_reply=ai_reply,
            timing=get_current_time(),
            date=get_current_date()
        )
        db.session.add(new_chat)
        db.session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error saving chat: {e}")
        db.session.rollback()


def process_user_input(user_input: str) -> str:
    """Process user input and get AI response"""
    ai_reply = get_ai_response(user_input)
    save_chat_to_db(user_input, ai_reply)
    state.update_response(ai_reply)
    return ai_reply


# ==================== Voice Listener ====================
def play_random_audio():
    """Play random acknowledgment audio"""
    try:
        audio_file = random.choice(Config.AUDIO_FILES)
        if os.path.exists(audio_file):
            os.system(f'start "" "{audio_file}"')
    except Exception as e:
        logger.error(f"Audio playback error: {e}")


def voice_listener():
    """Main voice listener thread"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5
    
    with sr.Microphone() as source:
        logger.info("Voice listener started")
        
        while True:
            try:
                # Listen for wake word
                audio = recognizer.listen(source, timeout=3)
                text = recognizer.recognize_google(audio).lower()
                print(f"Recognized: {text}")
                
                # Check for wake words
                if any(wake_word in text for wake_word in Config.WAKE_WORDS):
                    logger.info(f"Wake word detected: {text}")
                    state.set_bar_visible(True)
                    state.update_bar_label("🎙️ Yes? I'm listening...")
                    
                    # Listen for command
                    for _ in range(7):  # Max 7 attempts
                        try:
                            command = recognizer.listen(source, timeout=5)
                            command_text = recognizer.recognize_google(command).lower()
                            logger.info(f"Command received: {command_text}")
                            
                            # Handle exit command
                            if "you can go" in command_text or "tum ja sakti ho" in command_text:
                                play_random_audio()
                                break
                            
                            # Process command and get AI response
                            response = process_command(command_text, recognizer, source)
        
                            if response in ["Shutting down computer", "Shutdown cancelled", "Restarting computer", "Restart cancelled"]:
                                state.update_bar_label(response)
                                break
                            
                            # Get AI response with context
                            with app.app_context():
                                state.update_bar_label("🤔 Thinking...")
                                ai_response = process_user_input(command_text)
                                state.update_bar_label(f"{ai_response}\nStill listening...")
                            
                        except sr.WaitTimeoutError:
                            continue
                        except sr.UnknownValueError:
                            continue
                        except Exception as e:
                            logger.error(f"Command processing error: {e}")
                    
                    state.set_bar_visible(False)
                    state.update_bar_label("🎙️ Shinko is listening...")
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                logger.error(f"Voice listener error: {e}")


def process_command(command: str, recognizer=None, source=None, is_web=False) -> Optional[str]:
    """Process voice command and return response"""
    handler = CommandHandler()
    response = None

    if "open" in command or "kholo" in command or "khol" in command:
        response = handler.handle_open_app(command)

    elif "play" in command or "chalao" in command or "chala" in command:
        response = handler.handle_play_media(command)

    elif "search" in command and any(word in command for word in ["karo", "kar", "on", "pr", "par"]):
        response = handler.handle_search(command)

    elif "close" in command or "band karo" in command:
        response = handler.handle_close_app(command)

    elif "shutdown" in command or "computer shutdown" in command:
        if is_web:
            return handler.handle_shutdown(is_web=True)
        elif recognizer and source:
            return handler.handle_shutdown(recognizer, source)

    elif "restart" in command or "computer restart" in command:
        if is_web:
            return handler.handle_restart(is_web=True)
        elif recognizer and source:
            return handler.handle_restart(recognizer, source)

    if response and response != "None":
        state.update_instruction(response)

    return response

chat_content = ""
# ==================== Flask Routes ====================
@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page route"""
    global chat_content
    play_audio = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send':
            user_input = request.form.get('message', '')
            
            # Check if it's a shutdown or restart command
            if any(cmd in user_input.lower() for cmd in ["shutdown", "restart", "computer shutdown", "computer restart"]):
                # Handle system commands specially
                if "shutdown" in user_input.lower():
                    response = CommandHandler.handle_shutdown(is_web=True)
                elif "restart" in user_input.lower():
                    response = CommandHandler.handle_restart(is_web=True)
                
                if response:
                    chat_content += f"𝒀𝒐𝒖 : {user_input} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {response} <br><br>"
                    state.update_bar_label(response)
                    state.set_bar_visible(True)
                    threading.Timer(10, lambda: state.set_bar_visible(False)).start()
            
            else:
                # Handle regular commands
                task = process_command(user_input, recognizer=None, source=None, is_web=True)
                if task and task != "None":
                    ai_reply = process_user_input(task)
                    chat_content += f"𝒀𝒐𝒖 : {user_input} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {ai_reply} <br><br>"
                    state.update_bar_label(ai_reply)
                    state.set_bar_visible(True)
                    threading.Timer(10, lambda: state.set_bar_visible(False)).start()
                else:
                    ai_reply = process_user_input(user_input)
                    chat_content += f"𝒀𝒐𝒖 : {user_input} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {ai_reply} <br><br>"
                
        elif action == 'erase':
            chat_content = "Chats have been Deleted ✅ <br><br>"
                
        elif action == 'history':
            try:
                all_chats = ChatHistory.query.order_by(ChatHistory.id).all()
                for msg in all_chats:
                    chat_content += f"𝒀𝒐𝒖 : {msg.user_input} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {msg.ai_reply} <br><br>"
            except SQLAlchemyError as e:
                logger.error(f"Error loading history: {e}")
                chat_content = "Error loading history ❌ <br><br>"
                
        elif action == 'speak':
            try:
                tts = gTTS(text=state.last_response, lang='en')
                tts.save("static/output.mp3")
                play_audio = True

                os.system("start static/output.mp3")
            except Exception as e:
                logger.error(f"TTS error: {e}")
                
    return render_template(
        'index.html',
        chat=chat_content,
        time=get_current_time(),
        date=get_current_date(),
        play_audio=play_audio,
        random_id=random.randint(100000, 999999)
    )

@app.route('/confirm_shutdown', methods=['POST'])
def confirm_shutdown():
    data = request.get_json()
    answer = data.get('answer')

    if answer in ["yes", "no"]:
        state.set_shutdown_confirmation(answer)

    return jsonify({"status": "received"})

@app.route('/datetime')
def get_datetime():
    """API endpoint for current datetime"""
    return jsonify({
        'time': get_current_time(),
        'date': get_current_date()
    })


@app.route('/get_instruction')
def get_instruction():
    instruction = state.instruction
    state.update_instruction("") 
    return jsonify({"instruction": instruction})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400
            
        ai_reply = process_user_input(user_input)
        
        return jsonify({
            'user_input': user_input,
            'ai_reply': ai_reply,
            'time': get_current_time(),
            'date': get_current_date()
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Tkinter UI ====================
def create_overlay_window():
    """Create and manage the overlay window"""
    global bar_window, bar_label_widget
    
    bar_window = tk.Tk()
    bar_window.overrideredirect(True)
    bar_window.configure(bg='black')
    bar_window.attributes('-topmost', True)
    bar_window.withdraw()  # Start hidden
    
    # Create label
    bar_label_widget = tk.Label(
        bar_window,
        text=state.bar_label,
        fg="white",
        bg="black",
        font=("Helvetica", 12),
        wraplength=380,
        justify="left",
        anchor="w",
        padx=10,
        pady=5
    )
    bar_label_widget.pack(expand=True, fill="both")
    
    # Drag functionality
    def on_start_drag(event):
        bar_window.x_offset = event.x
        bar_window.y_offset = event.y
        
    def on_drag_motion(event):
        x = bar_window.winfo_x() + event.x - bar_window.x_offset
        y = bar_window.winfo_y() + event.y - bar_window.y_offset
        bar_window.geometry(f"+{x}+{y}")
        state.window_position = [x, y]
        
    bar_label_widget.bind("<Button-1>", on_start_drag)
    bar_label_widget.bind("<B1-Motion>", on_drag_motion)
    
    # Font for size calculation
    label_font = tkFont.Font(font=bar_label_widget['font'])
    
    # Timer for auto-hide
    bar_auto_hide_timer = {'job': None}

    def hide_bar():
        state.set_bar_visible(False)
        if bar_window:
            bar_window.withdraw()

    def start_auto_hide_timer():
        if bar_auto_hide_timer['job']:
            bar_window.after_cancel(bar_auto_hide_timer['job'])
        # Hide after 10 seconds (10000 ms)
        bar_auto_hide_timer['job'] = bar_window.after(10000, hide_bar)

    def update_ui():
        """Update overlay window UI"""
        if bar_window:
            # Calculate size based on text
            text_width = label_font.measure(state.bar_label)
            width = max(300, min(600, text_width + 10))
            bar_label_widget.config(wraplength=width - 20)
            bar_label_widget.update_idletasks()
            height = bar_label_widget.winfo_reqheight() + 10

            # Update window
            x, y = state.window_position
            bar_window.geometry(f"{width}x{height}+{x}+{y}")

            # Show/hide based on state
            if state.bar_visible:
                bar_window.deiconify()
                bar_label_widget.config(text=state.bar_label)
                start_auto_hide_timer()
            else:
                bar_window.withdraw()

            bar_window.after(1000, update_ui)

    update_ui()
    bar_window.mainloop()


# ==================== Main ====================
def main():
    """Main application entry point"""
    try:
        # Create database tables
        with app.app_context():
            db.create_all()
            logger.info("Database initialized")
            
        # Start threads
        flask_thread = threading.Thread(
            target=lambda: app.run(debug=True, use_reloader=False, port=5000),
            daemon=True
        )
        flask_thread.start()
        logger.info("Flask server started")
        
        voice_thread = threading.Thread(target=voice_listener, daemon=True)
        voice_thread.start()
        logger.info("Voice listener started")
        
        # Start overlay window (blocks)
        create_overlay_window()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Write error to file
        with open("error.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR IN SHINKO: {str(e)}")
        os.system(f"notepad error.txt")


if __name__ == '__main__':
    main()