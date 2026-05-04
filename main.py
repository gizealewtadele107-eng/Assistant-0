import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. Render Health Check ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. Credentials ---
TOKEN = "8717535794:AAEUJs0OjOxosz91lgkyWEaJEI0wL48NG7U"
API_KEY = "AIzaSyAKkVfpGcWoMDcUP4mP9usQUw1HLnMAt8o"

genai.configure(api_key=API_KEY)

# --- 3. Welcome Message ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! 👋 እንኳን ደህና መጡ። የፈለጉትን ይጠይቁኝ።")

# --- 4. AI Response Handler (Smart Selection) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 404 ስህተትን ለመከላከል በቅደም ተከተል ይሞክራል
    model_names = ['gemini-1.5-flash', 'gemini-pro', 'models/gemini-1.0-pro']
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(user_text)
            await update.message.reply_text(response.text)
            return # መልስ ካገኘ እዚህ ይቆማል
        except Exception:
            continue # ስህተት ከመጣ ወደ ቀጣዩ ሞዴል ስም ያልፋል
            
    await update.message.reply_text("ይቅርታ፣ አሁን ምላሽ መስጠት አልቻልኩም። እባክህ Render ላይ 'Clear Build Cache' አድርግ።")

if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(drop_pending_updates=True)
