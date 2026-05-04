import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. ለ Render ፖርት መክፈቻ (Health Check) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. መለያዎች (Credentials) ---
# አዲሱ የቴሌግራም ቶከንህ
TOKEN = "8717535794:AAE9jZUI9qE2NevbA1SvvI26wn9qjPYfFnw"
# አዲሱ የ Gemini API Key
API_KEY = "AIzaSyDkIuiYlB2gvimZB_TUQE8hCpN2-mhP3-k"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. መልዕክቶችን መቀበያ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_text = update.message.text
    # ቦቱ መልስ እያዘጋጀ መሆኑን የሚያሳይ (Typing...)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # ለ Gemini ጥያቄውን መላክ
        response = model.generate_content(user_text)
        if response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("ይቅርታ፣ Gemini ባዶ ምላሽ ሰጥቷል።")
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        
        try:
            # በሌላ ሞዴል መሞከር
            alt_model = genai.GenerativeModel('gemini-pro')
            alt_response = alt_model.generate_content(user_text)
            await update.message.reply_text(alt_response.text)
        except Exception:
            await update.message.reply_text(f"ስህተት ተከስቷል፡ {error_msg}")

# --- 4. ዋናው ማስጀመሪያ ---
if __name__ == '__main__':
    # ፖርት የሚከፍተውን ሰርቨር ማስነሳት
    Thread(target=run_server, daemon=True).start()
    
    # የቴሌግራም ቦት አፕሊኬሽን
    application = Application.builder().token(TOKEN).build()
    
    # ሁሉንም የጽሁፍ መልዕክቶች እንዲቀበል
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ በአዲሱ API Key ስራ ጀምሯል...")
    # የድሮ የተደራረቡ መልዕክቶችን ለማጽዳት drop_pending_updates እንጠቀማለን
    application.run_polling(drop_pending_updates=True)
