import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- Render Port Fix ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- Credentials ---
TOKEN = "8717535794:AAEKGvRZmktB06k-r9K9KTN49yC26ZMd39Q"
API_KEY = "AIzaSyCAb97dcGC6vrRbrkpuHGVZYD0hMP74E7w"

genai.configure(api_key=API_KEY)

# 'gemini-1.5-flash' ካልሰራ 'gemini-pro' አስተማማኝ ነው
model = genai.GenerativeModel('gemini-pro')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        # ስህተቱ ከሞዴሉ ስም ጋር የተያያዘ ከሆነ ሌላ ሞዴል መሞከር
        try:
            alt_model = genai.GenerativeModel('gemini-1.5-pro')
            response = alt
