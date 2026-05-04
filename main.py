import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. ለ Render የፖርት ስህተት መፍትሄ (Health Check) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    # Render የሚሰጠውን ፖርት ይጠቀማል
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. መለያዎች (Credentials) ---
# አዲሱ ቶከን እዚህ ገብቷል
TOKEN = "8717535794:AAE9jZUI9qE2NevbA1SvvI26wn9qjPYfFnw"
API_KEY = "AIzaSyCAb97dcGC6vrRbrkpuHGVZYD0hMP74E7w"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. መልዕክቶችን መቀበያ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_text = update.message.text
    # ቦቱ እየጻፈ መሆኑን የሚያሳይ (Typing...)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception:
        try:
            # አማራጭ ሞዴል መሞከር
            alt_model = genai.GenerativeModel('gemini-pro')
            alt_response = alt_model.generate_content(user_text)
            await update.message.reply_text(alt_response.text)
        except Exception:
            await update.message.reply_text("ይቅርታ፣ ምላሽ መስጠት አልቻልኩም።")

# --- 4. ዋናው ማስጀመሪያ ---
if __name__ == '__main__':
    # ፖርት የሚከፍተውን ሰርቨር ማስነሳት
    Thread(target=run_server, daemon=True).start()
    
    # የቴሌግራም ቦት አፕሊኬሽን
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ በአዲሱ ቶከን ስራ ጀምሯል...")
    # የድሮ የተደራረቡ ግንኙነቶችን ለማጽዳት
    application.run_polling(drop_pending_updates=True)
