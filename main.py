import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. ለ Render ፖርት መክፈቻ (Health Check) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- 2. የግል መረጃዎች (Credentials) ---
# አዲሱ ቶከን እዚህ ገብቷል
TELEGRAM_TOKEN = "8717535794:AAEKGvRZmktB06k-r9K9KTN49yC26ZMd39Q"
GEMINI_API_KEY = "AIzaSyCAb97dcGC6vrRbrkpuHGVZYD0hMP74E7w"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. የቦቱ ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! በአዲሱ ቶከን ስራ ጀምሬአለሁ። የፈለጉትን ጥያቄ ይጠይቁኝ።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception:
        await update.message.reply_text("ይቅርታ፣ ምላሽ ለመስጠት ተቸግሬአለሁ።")

# --- 4. ቦቱን ማስጀመር ---
if __name__ == '__main__':
    # የ Render ፖርት ሰርቨርን ማስነሳት
    Thread(target=run_health_server, daemon=True).start()
    
    # የቴሌግራም ቦት አፕሊኬሽን
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ በአዲሱ ቶከን ስራ ጀምሯል...")
    
    # drop_pending_updates=True የ Conflict ስህተትን ይፈታል
    application.run_polling(drop_pending_updates=True)
