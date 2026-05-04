import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# Render Health Check (ለፖርት ስህተት መፍትሄ)
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# መለያዎች (Credentials)
TOKEN = "8717535794:AAE9jZUI9qE2NevbA1SvvI26wn9qjPYfFnw"
API_KEY = "AIzaSyAKkVfpGcWoMDcUP4mP9usQUw1HLnMAt8o"

genai.configure(api_key=API_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # በአዲሱ እና በቆየው የሞዴል ስሞች ይሞክራል
    model_names = ['gemini-1.5-flash', 'models/gemini-1.0-pro']
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(user_text)
            if response.text:
                await update.message.reply_text(response.text)
                return
        except Exception:
            continue
    
    await update.message.reply_text("ይቅርታ፣ አሁን ምላሽ መስጠት አልቻልኩም። እባክህ Render ላይ Build Cache አጽዳ።")

if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    application = Application.builder
