import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# Render Health Check
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# Credentials
TOKEN = "8717535794:AAE9jZUI9qE2NevbA1SvvI26wn9qjPYfFnw"
API_KEY = "AIzaSyAKkVfpGcWoMDcUP4mP9usQUw1HLnMAt8o"

genai.configure(api_key=API_KEY)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # ሞዴሉን እዚህ ጋር በቀጥታ እንጠራዋለን
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        # 404 ስህተት ከመጣ ሌላ ስም ይሞክራል
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(user_text)
            await update.message.reply_text(response.text)
        except Exception as e2:
            await update.message.reply_text(f"የሞዴል ስህተት፦ {str(e2)}")

if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)
