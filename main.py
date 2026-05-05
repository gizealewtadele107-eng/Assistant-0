import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. Render Health Check ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Adane Ekub Bot is Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. Configuration & Database ---
TOKEN = "8717535794:AAEypF9pE-IBTjtI-N_YQvgFiJVSbxAaQ0s"
ADMIN_ID = 7705713321 #

def init_db():
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, info TEXT, password TEXT, status TEXT, weekly_pay TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Conversation States
(F_NAME, L_NAME, AGE, COUNTRY, PHONE, BANK_CHOICE, ACC_INFO, PASS, E_TYPE, ID_PHOTO, 
 PAY_CHOICE, SCREENSHOT, LOGIN_PASS, ASK_ADMIN, ADMIN_BROADCAST, EKUB_PAY_SCREENSHOT) = range(16)

# --- 3. Keyboards ---
def main_menu_keyboard(user_id):
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    keyboard = []
    # ተጠቃሚው ካልተመዘገበ ወይም ፔንዲንግ ከሆነ የሪጅስተር በተን ይታያል
    if not user or user[0] != 'Verified':
        keyboard.append([InlineKeyboardButton("ለመመዝገብ (Register)", callback_data="reg_start")])
    
    keyboard.append([InlineKeyboardButton("የእኔ ፕሮፋይል (Profile)", callback_data="login_profile")])
    keyboard.append([InlineKeyboardButton("ጥያቄ ለመጠየቅ (Ask Admin)", callback_data="ask_admin")])
    keyboard.append([InlineKeyboardButton("መረጃ (Info)", callback_data="get_info")])
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📢 ብሮድካስት (Podcast)", callback_data="admin_broadcast")])
        keyboard.append([InlineKeyboardButton("🏁 እቁብ ጀምር", callback_data="admin_start_ekub")])
        keyboard.append([InlineKeyboardButton("📊 የተጠቃሚዎች ብዛት", callback_data="admin_stats")])
    
    return InlineKeyboardMarkup(keyboard)

back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ወደ ኋላ (Back)", callback_data="go_home")]])

# --- 4. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("እንኳን ወደ አዳነ ሳምንታዊ እቁብ በደህና መጡ!\n\nእቁቡ እሁድ 8:00pm ይመታል። አዳነ እቁብን ስለመረጡ እናመሰግናለን።", 
                                  reply_markup=main_menu_keyboard(user_id))

async def go_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("ዋና ገጽ", reply_markup=main_menu_keyboard(update.effective_user.id))

# --- መረጃ (Info) ---
async def info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "ℹ️ **መረጃ**\n\nእቁቡ በየሳምንቱ እሁድ 8:00 PM ይወጣል።\nለማንኛውም ጥያቄ 'Ask Admin' የሚለውን ይጠቀሙ።"
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_kb)

# --- ፕሮፋይል (Profile) ---
async def login_profile_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        await update.callback_query.answer("እባክዎ መጀመሪያ ይመዝገቡ!", show_alert=True)
        return ConversationHandler.END
    
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ሚስጥር ቁጥርዎን ያስገቡ፦", reply_markup=back_kb)
    return LOGIN_PASS

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute("SELECT info, password, status, weekly_pay FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user and str(user[1]) == str(update.message.text):
        msg = f"👤 **የእርስዎ ፕሮፋይል**\nID: `{user_id}`\n\n{user[0]}\nሁኔታ፦ {user[2]}\nክፍያ፦ {user[3]}"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id))
    else:
        await update.message.reply_text("❌ የተሳሳተ ፓስወርድ።")
    return ConversationHandler.END

# --- Ask Admin ---
async def ask_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ጥያቄዎን እዚህ ይጻፉ፦", reply_markup=back_kb)
    return ASK_ADMIN

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(ADMIN_ID, f"❓ ጥያቄ ከ: {user.first_name}\nID: `{user.id}`\n\n{update.message.text}", parse_mode="Markdown")
    await update.message.reply_text("ጥያቄዎ ተልኳል!", reply_markup=main_menu_keyboard(user.id))
    return ConversationHandler.END

# --- Admin Stats ---
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(f"📊 አጠቃላይ ተጠቃሚዎች፦ {count}", reply_markup=back_kb)

# --- Broadcast (Podcast) ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ለሁሉም የሚላክ መልዕክት (ጽሁፍ/ፎቶ/ቪዲዮ) ይላኩ፦", reply_markup=back_kb)
    return ADMIN_BROADCAST

async def run_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('ekub_final_v6.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    for u in users:
        try:
            await update.message.copy(chat_id=u[0])
        except: continue
    await update.message.reply_text("ተልኳል!", reply_markup=main_menu_keyboard(ADMIN_ID))
    return ConversationHandler.END

# --- Registration Flow (F_NAME, etc. are same as before) ---
async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ስምዎን ያስገቡ፦", reply_markup=back_kb)
    return F_NAME

# ... [የቀደሙት get_fname, get_lname... እስከ get_screenshot ያሉትን ተግባራት እዚህ ይጨምሩ] ...

# --- Main Setup ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_reg, pattern="reg_start"),
            CallbackQueryHandler(login_profile_check, pattern="login_profile"),
            CallbackQueryHandler(ask_admin_start, pattern="ask_admin"),
            CallbackQueryHandler(broadcast_start, pattern="admin_broadcast")
        ],
        states={
            # ... [ሌሎች ስቴቶች እዚህ ይገባሉ] ...
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_profile)],
            ASK_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_admin)],
            ADMIN_BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, run_broadcast)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: F_NAME + 1)], # ማሳያ ብቻ
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(go_home, pattern="go_home")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(info_callback, pattern="get_info"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="admin_stats"))
    app.add_handler(CallbackQueryHandler(go_home, pattern="go_home"))
    
    # በ Screenshot_20260505-222303.png ላይ ያለውን የ syntax ስህተት እዚህ አርሜዋለሁ
    app.run_polling()
