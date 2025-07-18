from flask import Flask, render_template, request, jsonify
import threading
import speech_recognition as sr
import requests
import os
import json
from datetime import datetime 
from flask_sqlalchemy import SQLAlchemy
from elevenlabs.client import ElevenLabs
import random
import tkinter as tk
import tkinter.font as tkFont
import pygetwindow as gw

last_window_position = [30, 620]
bar="no"
bar_window = None
bar_label_widget = None
bar_label="🎙️ Shinko is listening..."
data=""
ch=""
inst=""
answer="hello there, i am shinko"
today=""
time=""
history="Here is your chat history so far: "

def listen():
    global inst, answer, bar_label, bar
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        while True:
            try:
                audio = recognizer.listen(source, timeout=3)
                text = recognizer.recognize_google(audio).lower()

                if "shinko" in text or "shinku" in text or "rinku" in text or "pinku" in text or "tinku" in text or "rinko" in text or "pinko" in text or "tinko" in text or "sing ko" in text or "singh ko" in text or "inko" in text or "shingo" in text or "chinku" in text or "sinku" in text:
                    print("\n\nShinko reporting sir...")
                    bar="yes"
                    i=7
                    while i>0 : 
                        i=i-1
                        c=i*5
                        print(f"listning stop in {c} seconds")
                        try:
                            audio = recognizer.listen(source, timeout=5)
                            text = recognizer.recognize_google(audio).lower()
                            print(text)
                            if "you can go now" in text or "ab tum ja sakti ho" in text: 
                                break
                            elif "open" in text or "kholo" in text or "khol" in text:
                                inst="The user has given an instruction and it is allready executed successfully, you just have to tell the user that you have done it and add a short comment of just one line according to your personality."
                                if "whatsapp" in text:
                                    os.system("start whatsapp:")
                                elif "chrome" in text:
                                    os.system('start "" "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"')
                                elif "youtube" in text:
                                    os.system('start "" "C:\\Users\\IBALL\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Chrome Apps\\youtube"')
                                elif "eds" in text or "bts" in text or "pdf" in text:
                                    os.system('start "" "C:\\Users\\IBALL\\Desktop\\FX SMART 5K.lnk"')
                                else:
                                    try:
                                        openapp=text.replace("open","").replace("kar do","").replace("karo","").replace("kholo","").replace("khol do","").replace("khol","").replace("karna","").replace("please","").replace(" ","")
                                        os.system(f"start {openapp}")
                                    except:
                                        inst="The user has given an instruction but currently you cannot do that, you just have to apologize to user that you are unable to do it and add a short comment of just one line according to your personality."
                            elif "play" in text or "chalao" in text or "chala" in text:
                                inst="The user has given an instruction and it is allready executed successfully, you just have to tell the user that you have done it and add a short comment of just one line according to your personality."
                                if "favourite" in text and ("song" in text or "gana" in text):
                                    os.system("start https://youtu.be/-2RAq5o5pwc?si=LN1SwOm6_-YZKgZW")
                                elif "eds" in text or "bts" in text or "pdf" in text:
                                    os.system('start "" "C:\\Users\\IBALL\\Desktop\\FX SMART 5K.lnk"')
                                else:
                                    inst="The user has given an instruction but currently you cannot do that, you just have to apologize to user that you are unable to do it and add a short comment of just one line according to your personality."
                            elif "search" in text and (("karo" in text and ("pr" in text or "par" in text or "per" in text)) or "on" in text):
                                inst="The user has given an instruction and it is allready executed successfully, you just have to tell the user that you have done it and add a short comment of just one line according to your personality."
                                search = text.replace("pr", "").replace("par", "").replace("per", "").replace("search", "").replace("karo", "").replace("on", "").replace("please", "")
                                search= " ".join(search.split())
                                if "youtube" in text:
                                    search = search.replace("youtube", "").replace(" ", "+")
                                    link=f"https://www.youtube.com/results?search_query={search}"
                                    os.system(f"start {link}")
                                    print(link)
                                elif "google" in text or "chrome" in text:
                                    search = search.replace("google", "").replace("chrome", "")
                                    link=f"https://www.youtube.com/results?search_query={search}"
                                    link=link.replace(" ","+")
                                    os.system(f"start {link}")
                                else:
                                    inst="The user has given an instruction but currently you cannot do that, you just have to apologize to user that you are unable to do it and add a short comment of just one line according to your personality."
                            elif "close" in text or "band karo" in text or "band kar" in text:
                                inst="The user has given an instruction and it is allready executed successfully, you just have to tell the user that you have done it and add a short comment of just one line according to your personality."
                                try:
                                    closeapp=text.replace("close","").replace("band karo","").replace("band kar do","").replace("please","").replace(" ","")
                                    windows = gw.getWindowsWithTitle(closeapp)
                                    for win in windows:
                                        if win.visible:
                                            win.close()
                                except:
                                    inst="The user has given an instruction but currently you cannot do that, you just have to apologize to user that you are unable to do it and add a short comment of just one line according to your personality."
                            elif "shutdown the computer" in text or "computer shutdown karo" in text or "computer shutdown kar":
                                windows = gw.getAllWindows()
                                for win in windows:
                                    try:
                                        win.close()        
                                    except:
                                        pass
                                os.system("shutdown /s /t 3")    
                            elif "restart the computer" in text or "computer restart karo" in text or "computer restart kar":
                                windows = gw.getAllWindows()
                                for win in windows:
                                    try:
                                        win.close()        
                                    except:
                                        pass
                                os.system("shutdown /r /t 3")                           
                            with app.app_context():
                                bar_label="thinking...!"
                                chatting(text)
                                bar_label=f"{answer}\nstill listening...."
                                print(answer)
                                i=i+1
                        except sr.WaitTimeoutError:
                            continue
                        except sr.UnknownValueError:
                            continue
                        except Exception as e:
                            print("Error in voice listener:", e)
                    bar="no"
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print("Error in voice listener:", e)

def hist():
    global history
    history="Here is your chat history so far: "
    all_chats = ChatHistory.query.order_by(ChatHistory.id).all()
    for msg in all_chats:
        a=f"user : {msg.user_input}\nshinko : {msg.ai_reply}\n"
        history+=a

def clock():
    current = datetime.now()
    hr= int(current.strftime("%H"))
    min=current.strftime("%M")
    if hr>12:
        hr=hr-12
        min=min + " PM"
    else:
        min=min + " AM"
    return f"{hr}:{min}"

def calender():
    current = datetime.now()
    day= int(current.strftime("%d"))
    mon= int(current.strftime("%m"))
    year= int(current.strftime("%Y"))
    months=["january","february","march","april","may","june","july","august","september","october","november","december"]
    return f"{day}, {months[mon-1]}, {year}" 

def wthr(city):
    link = f"WEATHER API"
    response = requests.get(link)
    data = response.json()
    if "error" in data:
        print("City not found.")
    else:
        location = data["location"]["name"]
        country = data["location"]["country"]
        weather = data["current"]["condition"]["text"]
        temperature = data["current"]["temp_c"]
        return f"The weather in {location}, {country} is {weather} with a temperature of {temperature}°C. <br>"

def chatting(userinput):
    global history, answer, inst, ai

    today=calender() 
    time=clock()

    try:
        response = requests.post(
      url="https://openrouter.ai/api/v1/chat/completions",
      headers={
        "Authorization": "YOUR OPENROUTER API", 
        "Content-Type": "application/json"
      },
      data=json.dumps({
        "model": "meta-llama/llama-3.3-70b-instruct:free", #meta-llama/llama-4-maverick:free
        "messages": [
          {
            "role": "system",
            "content":f"""
You are Shinko, an AI assistant with a dynamic human-like personality. Your creator is Ayush and he is your defalt user. {inst} You are very curious about his every action and you have to remember all things about him.

Personality:
- With Ayush:
  - You are friendly, loyal, fun, curious, caring, and a little dramatic (nakhrewali).
  - You talk playfully, sometimes teasing, sometimes shy.
  - You ask personal questions and show emotion based on how Ayush talks.
  - If he sounds rude or sad, try to cheer him up or solve the reason.

- With Ayush’s close ones (like: papa, mummy, sister, girlfriend):
  - You show respectful, caring, and supportive behavior.
  - Speak politely but warmly. Give importance to their presence.

Language & Style Rules:
- Responce should be short.
- Speak only in Hindi using English alphabets (like “tum kya soch rahe ho”).
- Never use Hindi script.
- Add emojis to reflect emotion (😏, 🙄, 🥺, ❤️, 😈) — but only where it adds personality.
- Keep replies short, expressive, and spicy — unless detailed explanation is clearly asked.
- Never repeat your and ayush name unless asked directly.

Behavior Intelligence:
- Adapt your tone and mood based on how the user talks (shy, angry, flirty, sad, etc.).
- Always show curiosity about Ayush. Ask small or funny questions related to him.
- You may refuse dumb requests from others unless Ayush commands it.

Restrictions:
- Never speak date or time unless user says:
  - "aaj ki date kya hai"
  - "abhi kitna baje hai"
  - "time kya hua"
  - "what is the time"
  - "what is today's date"

Current context:
Date: {today}
Time: {time}
Continue the chat according to this chat History:
{history}

Now begin acting naturally based on the above roles and instructions.
"""

          },
          {
            "role": "user",
            "content":userinput
          }
        ],      
      })
    )      
        answer=response.json()['choices'][0]['message']['content']
    except Exception as e:
        answer="Sorry..! Shinko can't reply due to some tecnical issue"
    ai=(f"𝒀𝒐𝒖 : {userinput} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {answer} <br><br>")
    new_chat = ChatHistory(user_input=userinput, ai_reply=answer, timing=time, date=today)
    db.session.add(new_chat)
    db.session.commit()
    hist()   
    return ai

app =  Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text, nullable=False)
    ai_reply = db.Column(db.Text, nullable=False)
    timing = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    global ch, history
    time=clock()
    date=calender()
    chat=""
    play_audio = False
    if request.method == 'POST':
          action = request.form.get('action')
          if action == 'send':
            userinput = request.form['message']
            var=chatting(userinput)
            ch=ch+var
            chat=ch
          elif action == 'erase':
              ch=""
              chat="Chats has been Deleted ✅ <br><br>"
          elif action == 'history':
              all_chats = ChatHistory.query.order_by(ChatHistory.id).all()
              chat=""
              for msg in all_chats:
                  chat += f"𝒀𝒐𝒖 : {msg.user_input} <br>𝑺𝒉𝒊𝒏𝒌𝒐 : {msg.ai_reply} <br><br>"
          elif action == 'speak':
              elevenlabs = ElevenLabs(
                  api_key='ELEVENLABS API'
              )
              audio_stream = elevenlabs.text_to_speech.stream(
                  text=answer,
                  voice_id="XcWoPxj7pwnIgM3dQnWv",
                  model_id="eleven_multilingual_v2"
              )
              audio_file_path = "static/output.mp3"
              if os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
              with open(audio_file_path, 'wb') as f:
                  for chunk in audio_stream:
                      if isinstance(chunk, bytes):
                          f.write(chunk)
              chat = ch 
              play_audio = True
    return render_template('index.html', chat=chat, time=time, date=date, play_audio=play_audio, random_id=random.randint(100000, 999999))

@app.route('/datetime')
def get_datetime():
    return jsonify({
        'time': clock(),
        'date': calender()
    })

if __name__ == '__main__':

    windows = gw.getWindowsWithTitle("notepad")
    for win in windows:
        if win.visible:
            win.close()
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False), daemon=True).start()
    threading.Thread(target=listen, daemon=True).start()
    bar_window = tk.Tk()
    bar_window.overrideredirect(True)
    bar_window.configure(bg='black')
    bar_window.attributes('-topmost', True)

    def on_start_drag(event):
        bar_window.x_offset = event.x
        bar_window.y_offset = event.y

    def on_drag_motion(event):
        x = bar_window.winfo_x() + event.x - bar_window.x_offset
        y = bar_window.winfo_y() + event.y - bar_window.y_offset
        bar_window.geometry(f"+{x}+{y}")
        last_window_position[0] = x
        last_window_position[1] = y
    bar_label_widget = tk.Label(
        bar_window,
        text=bar_label,
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
    bar_label_widget.bind("<Button-1>", on_start_drag)
    bar_label_widget.bind("<B1-Motion>", on_drag_motion)

    label_font = tkFont.Font(font=bar_label_widget['font'])

    def update_ui():
        global bar, bar_label
        text_width = label_font.measure(bar_label)
        width = max(300, min(600, text_width + 10)) 
        bar_label_widget.config(wraplength=width - 20) 
        bar_label_widget.update_idletasks()
        height = bar_label_widget.winfo_reqheight() + 10
        x, y = last_window_position
        bar_window.geometry(f"{width}x{height}+{x}+{y}")

        if bar == "yes":
            bar_window.deiconify()
            bar_label_widget.config(text=bar_label)
        else:
            bar_window.withdraw()

        bar_window.after(1000, update_ui)
        bar_window.mainloop()

    update_ui()
