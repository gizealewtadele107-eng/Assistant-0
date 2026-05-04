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
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- Credentials ---
TOKEN = "8717535794:AAEKGvRZmktB06k-r9K9KTN49yC26ZMd39Q"
API_KEY = "AIzaSyCAb97dcGC6vrRbrkpuHGVZYD0hMP74E7w"

genai.configure(api_key=API_KEY)
# ሞዴሉን በትክክል መጥራት
model = genai.GenerativeModel('gemini-1.5-flash')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # ለ Gemini ጥያቄውን መላክ
        response = model.generate_content(user_text)
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("Gemini ባዶ ምላሽ ሰጥቷል።")
    except Exception as e:
        # ትክክለኛውን ስህተት ለተጠቃሚው ይነግረዋል
        error_msg = f"ስህተት ተከስቷል፦ {str(e)}"
        print(error_msg)
        await update.message.reply_text(error_msg)

if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ እየሰራ ነው...")
    application.run_polling(drop_pending_updates=True)
