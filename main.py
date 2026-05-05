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
        self.wfile.write(b"Adane Ekub Bot is Live")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. Configuration & Database ---
TOKEN = "8717535794:AAEypF9pE-IBTjtI-N_YQvgFiJVSbxAaQ0s"
ADMIN_ID = 7705713321 

def init_db():
    conn = sqlite3.connect('ekub_final_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, info TEXT, password TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, msg TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Conversation States
(F_NAME, L_NAME, AGE, COUNTRY, PHONE, BANK_CHOICE, ACC_INFO, PASS, E_TYPE, ID_PHOTO, 
 PAY_CHOICE, SCREENSHOT, LOGIN_PASS, ASK_ADMIN, ADMIN_BROADCAST, EKUB_PAY_SCREENSHOT) = range(16)

# --- 3. Keyboards ---
def main_menu_keyboard(user_id):
    keyboard = [
        [InlineKeyboardButton("ለመመዝገብ (Register)", callback_data="reg_start")],
        [InlineKeyboardButton("የእኔ ፕሮፋይል (Profile)", callback_data="login_profile")],
        [InlineKeyboardButton("ጥያቄ ለመጠየቅ (Ask Admin)", callback_data="ask_admin")],
        [InlineKeyboardButton("መረጃ (Info)", callback_data="get_info")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📢 ብሮድካስት (ለሁሉም መላኪያ)", callback_data="admin_broadcast")])
        keyboard.append([InlineKeyboardButton("🏁 እቁብ ጀምር (Start Ekub)", callback_data="admin_start_ekub")])
    return InlineKeyboardMarkup(keyboard)

back_home_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ወደ ኋላ", callback_data="go_home")]])

# --- 4. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"እንኳን ወደ አዳነ ሳምንታዊ እቁብ በደህና መጡ {user.first_name}!", 
                                  reply_markup=main_menu_keyboard(user.id))

async def go_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("ዋና ገጽ", reply_markup=main_menu_keyboard(update.effective_user.id))

# --- Registration Flow ---
async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("መጠሪያ ስምዎን ያስገቡ (ለመመለስ /cancel):")
    return F_NAME

async def get_fname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] = f"ስም: {update.message.text}\n"
    await update.message.reply_text("የአባት ስም?")
    return L_NAME

async def get_lname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"አባት: {update.message.text}\n"
    await update.message.reply_text("እድሜ?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"እድሜ: {update.message.text}\n"
    await update.message.reply_text("ሀገር/ከተማ?")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"ሀገር: {update.message.text}\n"
    await update.message.reply_text("ስልክ ቁጥር?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"ስልክ: {update.message.text}\n"
    kb = [[InlineKeyboardButton("Telebirr", callback_data="b_tele"), InlineKeyboardButton("CBE", callback_data="b_cbe")]]
    await update.message.reply_text("ገንዘብ የሚቀበሉበት መንገድ?", reply_markup=InlineKeyboardMarkup(kb))
    return BANK_CHOICE

async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['reg'] += f"ባንክ: {query.data}\n"
    await query.message.reply_text("የአካውንት ቁጥርዎን ያስገቡ፦")
    return ACC_INFO

async def get_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"አካውንት: {update.message.text}\n"
    await update.message.reply_text("ለፕሮፋይልዎ ባለ 4 አሃዝ ሚስጥር ቁጥር ይፍጠሩ፦")
    return PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pass'] = update.message.text
    kb = [[InlineKeyboardButton("ሙሉ እጣ (5000)", callback_data="f_full"), InlineKeyboardButton("ግማሽ እጣ (2500)", callback_data="f_half")]]
    await update.message.reply_text("የእቁብ አይነት?", reply_markup=InlineKeyboardMarkup(kb))
    return E_TYPE

async def get_etype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data['reg'] += f"እቁብ: {update.callback_query.data}\n"
    await update.callback_query.message.reply_text("የመታወቂያ ፎቶ ይላኩ፦")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id_img'] = update.message.photo[-1].file_id
    kb = [[InlineKeyboardButton("Telebirr", callback_data="p_tele"), InlineKeyboardButton("CBE", callback_data="p_cbe")]]
    await update.message.reply_text("የመመዝገቢያ 200 ብር መክፈያ መንገድ ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return PAY_CHOICE

async def get_pay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    bank = "Telebirr 0954873397" if update.callback_query.data == "p_tele" else "CBE 1000536009276"
    await update.callback_query.message.reply_text(f"በ {bank} ከፍለው ደረሰኙን ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info, password = context.user_data['reg'], context.user_data['pass']
    
    conn = sqlite3.connect('ekub_final_v3.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)", (user_id, info, password, "Pending"))
    conn.commit()
    conn.close()

    await context.bot.send_photo(ADMIN_ID, photo=context.user_data['id_img'], caption="🆔 መታወቂያ")
    await context.bot.send_photo(ADMIN_ID, photo=update.message.photo[-1].file_id, 
                               caption=f"🔔 አዲስ ምዝገባ\n\n{info}", 
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("አረጋግጥ", callback_data=f"verify_{user_id}")]]))
    
    await update.message.reply_text("ክፍያው እስኪረጋገጥ ትንሽ ይጠብቁ።", reply_markup=main_menu_keyboard(user_id))
    return ConversationHandler.END

# --- Ask Admin ---
async def ask_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ጥያቄዎን እዚህ ይጻፉ (ለአድሚን ይላካል):")
    return ASK_ADMIN

async def get_admin_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text
    await context.bot.send_message(ADMIN_ID, f"❓ ጥያቄ ከ {user.first_name} (ID: {user.id}):\n\n{msg}")
    await update.message.reply_text("ጥያቄዎ ተልኳል። አድሚኑ ሲያይ ይመልስልዎታል።", reply_markup=main_menu_keyboard(user.id))
    return ConversationHandler.END

# --- Admin Broadcast ---
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("ለሁሉም ተጠቃሚዎች የሚላክ ጽሁፍ፣ ፎቶ ወይም ቪዲዮ ይላኩ፦")
    return ADMIN_BROADCAST

async def send_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('ekub_final_v3.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()

    count = 0
    for user in users:
        try:
            if update.message.text:
                await context.bot.send_message(user[0], update.message.text)
            elif update.message.photo:
                await context.bot.send_photo(user[0], update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video:
                await context.bot.send_video(user[0], update.message.video.file_id, caption=update.message.caption)
            count += 1
        except: continue
    
    await update.message.reply_text(f"መልዕክቱ ለ {count} ተጠቃሚዎች ተልኳል።", reply_markup=main_menu_keyboard(ADMIN_ID))
    return ConversationHandler.END

# --- Ekub Start & Payment ---
async def admin_start_ekub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    conn = sqlite3.connect('ekub_final_v3.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("በ Telebirr ክፈል", callback_data="pay_e_tele"), 
                                InlineKeyboardButton("በ CBE ክፈል", callback_data="pay_e_cbe")]])
    
    for user in users:
        try:
            await context.bot.send_message(user[0], "🏁 እቁቡ ተጀምሯል! እባክዎ የሳምንት ክፍያዎን ይፈጽሙ፦", reply_markup=kb)
        except: continue
    await update.callback_query.message.reply_text("የክፍያ ጥሪ ለሁሉም ተልኳል።")

async def ekub_pay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    bank = "Telebirr 0954873397" if update.callback_query.data == "pay_e_tele" else "CBE 1000536009276"
    await update.callback_query.message.reply_text(f"በ {bank} ከፍለው የክፍያ ደረሰኝ (Screenshot) ይላኩ፦")
    return EKUB_PAY_SCREENSHOT

async def get_ekub_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_photo(ADMIN_ID, photo=update.message.photo[-1].file_id, 
                               caption=f"💰 የእቁብ ክፍያ ደረሰኝ\nከ: {user.first_name} (ID: {user.id})")
    await update.message.reply_text("ክፍያው እስኪረጋገጥ ትንሽ ይጠብቁ።", reply_markup=main_menu_keyboard(user.id))
    return ConversationHandler.END

# --- Main Application ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    # Conversation Handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_reg, pattern="reg_start"),
            CallbackQueryHandler(ask_admin_start, pattern="ask_admin"),
            CallbackQueryHandler(admin_broadcast_start, pattern="admin_broadcast"),
            CallbackQueryHandler(ekub_pay_choice, pattern="^pay_e_")
        ],
        states={
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fname)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_lname)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            BANK_CHOICE: [CallbackQueryHandler(get_bank)],
            ACC_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_acc)],
            PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            E_TYPE: [CallbackQueryHandler(get_etype)],
            ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
            PAY_CHOICE: [CallbackQueryHandler(get_pay_choice)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            ASK_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_question)],
            ADMIN_BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, send_admin_broadcast)],
            EKUB_PAY_SCREENSHOT: [MessageHandler(filters.PHOTO, get_ekub_screenshot)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(go_home_callback, pattern="go_home"))
    app.add_handler(CallbackQueryHandler(admin_start_ekub, pattern="admin_start_ekub"))
    
    print("Bot is ready...")
    app.run_polling()
