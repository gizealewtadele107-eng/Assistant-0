import os
import sqlite3
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# መረጃዎችን ለመከታተል
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
ADMIN_ID = 7705713321 # የእርስዎ ትክክለኛ ID መሆኑን ያረጋግጡ

def init_db():
    conn = sqlite3.connect('ekub_final_v2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, info TEXT, password TEXT, status TEXT, id_photo TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Conversation States
F_NAME, L_NAME, AGE, COUNTRY, PHONE, BANK_CHOICE, ACC_INFO, PASS, E_TYPE, ID_PHOTO, PAY_CHOICE, SCREENSHOT, LOGIN_PASS = range(13)

# --- 3. ቦት ተግባራት ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = "እንኳን ወደ አዳነ ሳምንታዊ የብር እቁብ በደህና መጡ"
    
    keyboard = [
        [InlineKeyboardButton("ለመመዝገብ", callback_data="register_start")],
        [InlineKeyboardButton("የእኔ ፕሮፋይል", callback_data="login_profile")],
        [InlineKeyboardButton("መረጃ ለማግኘት", callback_data="get_info")]
    ]
    
    # አድሚን ከሆነ ተጨማሪ በተን ይታየዋል
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("እቁብ ጀምር (Admin)", callback_data="admin_start_ekub")])

    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- መረጃ (Info) ---
async def info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    info_text = (
        "ℹ️ **ስለ አዳነ ሳምንታዊ እቁብ**\n\n"
        "1. ሙሉ እጣ፦ 5,000 ብር በሳምንት\n"
        "2. ግማሽ እጣ፦ 2,500 ብር በሳምንት\n"
        "3. መመዝገቢያ፦ 200 ብር (አንድ ጊዜ)\n\n"
        "ለተጨማሪ ጥያቄዎች አድሚኑን ያነጋግሩ።"
    )
    await update.callback_query.message.reply_text(info_text, parse_mode="Markdown")

# --- ምዝገባ (Registration) ---
async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ለመመዝገብ መጠሪያ ስምዎን ይላኩ፦")
    return F_NAME

async def get_fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] = f"👤 ስም: {update.message.text}\n"
    await update.message.reply_text("የአባት ስም?")
    return L_NAME

async def get_lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] += f"👨‍👦 አባት: {update.message.text}\n"
    await update.message.reply_text("እድሜ?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] += f"🔢 እድሜ: {update.message.text}\n"
    await update.message.reply_text("ሀገር/ከተማ?")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] += f"📍 ሀገር: {update.message.text}\n"
    await update.message.reply_text("ስልክ ቁጥር ያስገቡ፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] += f"📞 ስልክ: {update.message.text}\n"
    kb = [[InlineKeyboardButton("Telebirr", callback_data="b_tele"), InlineKeyboardButton("CBE", callback_data="b_cbe")]]
    await update.message.reply_text("ገንዘብ የሚቀበሉበትን ባንክ ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return BANK_CHOICE

async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bank = "Telebirr" if query.data == "b_tele" else "CBE"
    context.user_data['reg_info'] += f"🏦 ባንክ: {bank}\n"
    await query.message.reply_text(f"የ{bank} አካውንት ቁጥርዎን ያስገቡ፦")
    return ACC_INFO

async def get_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_info'] += f"💳 አካውንት: {update.message.text}\n"
    await update.message.reply_text("ለፕሮፋይልዎ ሚስጥር ቁጥር (4 አሃዝ Password) ይፍጠሩ፦")
    return PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    kb = [[InlineKeyboardButton("ሙሉ እጣ (5000)", callback_data="f_full"), InlineKeyboardButton("ግማሽ እጣ (2500)", callback_data="f_half")]]
    await update.message.reply_text("የእቁብ አይነት ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return E_TYPE

async def get_etype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    etype = "ሙሉ" if update.callback_query.data == "f_full" else "ግማሽ"
    context.user_data['reg_info'] += f"🎰 እቁብ: {etype}\n"
    await update.callback_query.message.reply_text("የመታወቂያ ፎቶ (ID Photo) ይላኩ፦")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id_file'] = update.message.photo[-1].file_id
    kb = [[InlineKeyboardButton("Telebirr", callback_data="p_tele"), InlineKeyboardButton("CBE", callback_data="p_cbe")]]
    await update.message.reply_text("የ200 ብር መመዝገቢያ ክፍያ የሚከፍሉበትን መንገድ ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return PAY_CHOICE

async def get_pay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "p_tele":
        msg = "በ Telebirr `0954873397` (Drbew) 200 ብር ከፍለው ደረሰኙን (Screenshot) ይላኩ።"
    else:
        msg = "በ CBE `1000536009276` (Gizachew) 200 ብር ከፍለው ደረሰኙን (Screenshot) ይላኩ።"
    await query.message.reply_text(msg, parse_mode="Markdown")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info = context.user_data['reg_info']
    password = context.user_data['password']
    id_photo = context.user_data['id_file']
    screenshot = update.message.photo[-1].file_id
    
    # ዳታቤዝ ላይ ማስቀመጥ
    conn = sqlite3.connect('ekub_final_v2.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, info, password, status, id_photo) VALUES (?, ?, ?, ?, ?)", 
              (user_id, info, password, "Pending", id_photo))
    conn.commit()
    conn.close()

    # ለአድሚን መላክ (ይህ ክፍል ነው ማረጋገጫውን የሚልከው)
    verify_kb = [[InlineKeyboardButton("አረጋግጥ (Verify)", callback_data=f"verify_{user_id}")]]
    
    # መጀመሪያ መታወቂያውን ይልካል
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=id_photo, caption="🆔 የተጠቃሚ መታወቂያ")
    # በመቀጠል ደረሰኙን እና መረጃውን ይልካል
    await context.bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=screenshot, 
        caption=f"💰 የክፍያ ደረሰኝ እና መረጃ\n\n{info}", 
        reply_markup=InlineKeyboardMarkup(verify_kb)
    )
    
    await update.message.reply_text("✅ መረጃዎ እና ደረሰኝዎ ለአድሚን ተልኳል። አድሚኑ እስኪያረጋግጥ ይጠብቁ።")
    return ConversationHandler.END

# --- ፕሮፋይል (Profile) ---
async def login_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("የፕሮፋይል ሚስጥር ቁጥርዎን (Password) ያስገቡ፦")
    return LOGIN_PASS

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    entered_pass = update.message.text
    conn = sqlite3.connect('ekub_final_v2.db')
    c = conn.cursor()
    c.execute("SELECT info, password, status FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user and str(user[1]) == str(entered_pass):
        await update.message.reply_text(f"👤 **የእርስዎ ፕሮፋይል**\n\n{user[0]}\nሁኔታ፦ {user[2]}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ የተሳሳተ ፓስወርድ ነው። እባክዎ /start ብለው ይሞክሩ።")
    return ConversationHandler.END

# --- አድሚን ተግባራት ---
async def admin_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id_to_verify = int(query.data.split("_")[1])
    await query.answer()
    
    conn = sqlite3.connect('ekub_final_v2.db')
    c = conn.cursor()
    c.execute("UPDATE users SET status='Verified' WHERE user_id=?", (user_id_to_verify,))
    conn.commit()
    conn.close()
    
    await context.bot.send_message(chat_id=user_id_to_verify, text="🎉 እንኳን ደስ አለዎት! ምዝገባዎ በአድሚን ተረጋግጧል። አሁን እቁብተኛ ሆነዋል።")
    await query.edit_message_caption(caption="🟢 ተረጋግጧል (Verified)")

async def admin_start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    conn = sqlite3.connect('ekub_final_v2.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    
    msg = "እቁቡ በይፋ ተጀምሯል የእቁቡን ገንዘብ ገቢ በማድረግ ይጀምሩ ገቢ ማድረጊያ የሚያልቅበት ቀን እሁድ - 7 ሰዓት"
    for user in users:
        try: await context.bot.send_message(chat_id=user[0], text=msg)
        except: continue
    await update.callback_query.message.reply_text("መልዕክቱ ለሁሉም ተልኳል።")

# --- 4. Main ---
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
            BANK_CHOICE: [CallbackQueryHandler(get_bank, pattern="^b_")],
            ACC_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_acc)],
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            E_TYPE: [CallbackQueryHandler(get_etype, pattern="^f_")],
            ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
            PAY_CHOICE: [CallbackQueryHandler(get_pay_choice, pattern="^p_")],
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
    app.add_handler(CallbackQueryHandler(info_callback, pattern="get_info"))
    app.add_handler(CallbackQueryHandler(admin_start_broadcast, pattern="admin_start_ekub"))
    app.add_handler(CallbackQueryHandler(admin_verify_callback, pattern="^verify_"))
    
    print("Bot is Starting...")
    app.run_polling()
