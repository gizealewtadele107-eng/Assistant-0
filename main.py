import os
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. Render Health Check (ቦቱ ሁልጊዜ ክፍት እንዲሆን) ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Adane Ekub Bot is Always Live")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. Configuration & Database ---
TOKEN = "8717535794:AAEypF9pE-IBTjtI-N_YQvgFiJVSbxAaQ0s"
ADMIN_ID = 7705713321 # አዲሱ አድሚን መታወቂያ
MAX_USERS = 30

def init_db():
    conn = sqlite3.connect('ekub_pro_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, info TEXT, password TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Conversation States
F_NAME, L_NAME, AGE, COUNTRY, PHONE, BANK_CHOICE, ACC_INFO, PASS, E_TYPE, ID_PHOTO, SCREENSHOT, LOGIN_PASS = range(12)

# --- 3. Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "እንኳን ወደ አዳነ ሳምንታዊ የብር እቁብ በደህና መጡ"
    keyboard = [
        [InlineKeyboardButton("ለመመዝገብ", callback_data="register_start")],
        [InlineKeyboardButton("መረጃ ለማግኘት", callback_data="info")],
        [InlineKeyboardButton("የእኔ ፕሮፋይል (My Profile)", callback_data="login_profile")],
        [InlineKeyboardButton("የእኔ መታወቂያ", callback_data="send_id")]
    ]
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("እቁብ ጀምር (Admin)", callback_data="admin_start_ekub")])

    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- Registration Flow ---
async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("መጠሪያ ስምዎን ይላኩ፦")
    return F_NAME

async def get_fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] = f"ስም: {update.message.text}\n"
    await update.message.reply_text("የአባት ስምዎን ይላኩ፦")
    return L_NAME

async def get_lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] += f"አባት: {update.message.text}\n"
    await update.message.reply_text("እድሜዎን ይላኩ፦")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] += f"እድሜ: {update.message.text}\n"
    await update.message.reply_text("ሀገር (ከተማ) ይላኩ፦")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] += f"ሀገር: {update.message.text}\n"
    await update.message.reply_text("የስልክ ቁጥርዎን ያስገቡ፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] += f"ስልክ: {update.message.text}\n"
    kb = [[InlineKeyboardButton("Telebirr", callback_data="bank_tele"), InlineKeyboardButton("CBE", callback_data="bank_cbe")]]
    await update.message.reply_text("የሚጠቀሙበትን ባንክ ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return BANK_CHOICE

async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bank = "Telebirr" if query.data == "bank_tele" else "CBE"
    context.user_data['reg_data'] += f"ባንክ: {bank}\n"
    await query.message.reply_text(f"የ{bank} አካውንት ቁጥርዎን ያስገቡ፦")
    return ACC_INFO

async def get_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_data'] += f"አካውንት: {update.message.text}\n"
    await update.message.reply_text("ለፕሮፋይልዎ የሚሆን ባለ 4 አሃዝ ሚስጥር ቁጥር (Password) ይፍጠሩ፦")
    return PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    kb = [[InlineKeyboardButton("ሙሉ እጣ (5,000)", callback_data="full"), InlineKeyboardButton("ግማሽ እጣ (2,500)", callback_data="half")]]
    await update.message.reply_text("የእቁብ አይነት ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return E_TYPE

async def get_etype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    etype = "ሙሉ እጣ" if update.callback_query.data == "full" else "ግማሽ እጣ"
    context.user_data['reg_data'] += f"እቁብ: {etype}\n"
    await update.callback_query.message.reply_text("የብሔራዊ ወይም የቀበሌ መታወቂያ ፎቶ (National ID) ይላኩ፦")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id_img'] = update.message.photo[-1].file_id
    pay_msg = (
        "✅ የምዝገባ ክፍያ 200 ብር በነዚህ አማራጮች ይክፈሉ፦\n"
        "🔸 Telebirr: `0954873397` (Drbew)\n"
        "🔸 CBE: `1000536009276` (Gizachew)\n\n"
        "ከፈሉ በኋላ ደረሰኙን (Screenshot) ይላኩ፦"
    )
    await update.message.reply_text(pay_msg, parse_mode="Markdown")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = context.user_data['reg_data']
    password = context.user_data['password']
    
    # ዳታቤዝ ውስጥ ማስቀመጥ
    conn = sqlite3.connect('ekub_pro_v6.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, info, password, status) VALUES (?, ?, ?, ?)", (user_id, info, password, "Pending"))
    conn.commit()
    conn.close()

    # ለአድሚን መላክ
    verify_kb = [[InlineKeyboardButton("አረጋግጥ", callback_data=f"verify_{user_id}")]]
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=context.user_data['id_img'], caption="🆔 መታወቂያ")
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"🔔 አዲስ ምዝገባ\n\n{info}", reply_markup=InlineKeyboardMarkup(verify_kb))
    
    await update.message.reply_text("መዝጋቢው አስከሚያረጋግጥ ይጠብቁ።")
    return ConversationHandler.END

# --- Profile Section ---
async def login_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ወደ ፕሮፋይልዎ ለመግባት ሚስጥር ቁጥርዎን (Password) ያስገቡ፦")
    return LOGIN_PASS

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    entered_pass = update.message.text
    
    conn = sqlite3.connect('ekub_pro_v6.db')
    c = conn.cursor()
    c.execute("SELECT info, password, status FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user and user[1] == entered_pass:
        profile_text = f"👤 **የእርስዎ ፕሮፋይል**\n\n{user[0]}\nሁኔታ፦ {user[2]}"
        await update.message.reply_text(profile_text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ የተሳሳተ ፓስወርድ ነው። እባክዎ እንደገና ይሞክሩ። /start")
    return ConversationHandler.END

# --- Main Setup ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_reg, pattern="register_start")],
        states={
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fname)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lname)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            BANK_CHOICE: [CallbackQueryHandler(get_bank, pattern="^bank_")],
            ACC_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_acc)],
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            E_TYPE: [CallbackQueryHandler(get_etype, pattern="^(full|half)$")],
            ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    profile_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(login_profile, pattern="login_profile")],
        states={LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_profile)]},
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(reg_conv)
    app.add_handler(profile_conv)
    
    print("Bot is Always Live & Protected...")
    app.run_polling()
