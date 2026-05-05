import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. Render Health Check (ሁልጊዜ ክፍት እንዲሆን) ---
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
ADMIN_ID = 7705713321 

def init_db():
    conn = sqlite3.connect('ekub_final_pro_v5.db')
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
    keyboard = [
        [InlineKeyboardButton("ለመመዝገብ (Register)", callback_data="reg_start")],
        [InlineKeyboardButton("የእኔ ፕሮፋይል (Profile)", callback_data="login_profile")],
        [InlineKeyboardButton("ጥያቄ ለመጠየቅ (Ask Admin)", callback_data="ask_admin")],
        [InlineKeyboardButton("መረጃ (Info)", callback_data="get_info")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📢 ብሮድካስት", callback_data="admin_broadcast")])
        keyboard.append([InlineKeyboardButton("🏁 እቁብ ጀምር", callback_data="admin_start_ekub")])
    return InlineKeyboardMarkup(keyboard)

# --- 4. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("እንኳን ወደ አዳነ ሳምንታዊ እቁብ በደህና መጡ!", reply_markup=main_menu_keyboard(user_id))

# --- Registration Flow ---
async def start_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("መጠሪያ ስምዎን ያስገቡ፦")
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
    await update.message.reply_text("ከተማ?")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"ከተማ: {update.message.text}\n"
    await update.message.reply_text("ስልክ ቁጥር?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"ስልክ: {update.message.text}\n"
    kb = [[InlineKeyboardButton("Telebirr", callback_data="b_tele"), InlineKeyboardButton("CBE", callback_data="b_cbe")]]
    await update.message.reply_text("ገንዘብ የሚቀበሉበት መንገድ?", reply_markup=InlineKeyboardMarkup(kb))
    return BANK_CHOICE

async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank = "Telebirr" if update.callback_query.data == "b_tele" else "CBE"
    context.user_data['reg'] += f"ባንክ: {bank}\n"
    await update.callback_query.message.reply_text(f"የ{bank} አካውንት ቁጥር?")
    return ACC_INFO

async def get_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg'] += f"አካውንት: {update.message.text}\n"
    await update.message.reply_text("ለፕሮፋይልዎ ባለ 4 አሃዝ ፓስወርድ ይፍጠሩ፦")
    return PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['pass'] = update.message.text
    kb = [[InlineKeyboardButton("ሙሉ (5000)", callback_data="f_full"), InlineKeyboardButton("ግማሽ (2500)", callback_data="f_half")]]
    await update.message.reply_text("እቁብ አይነት?", reply_markup=InlineKeyboardMarkup(kb))
    return E_TYPE

async def get_etype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    etype = "ሙሉ" if update.callback_query.data == "f_full" else "ግማሽ"
    context.user_data['reg'] += f"እቁብ: {etype}\n"
    await update.callback_query.message.reply_text("የመታወቂያ ፎቶ ይላኩ፦")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['id_img'] = update.message.photo[-1].file_id
    kb = [[InlineKeyboardButton("Telebirr", callback_data="p_tele"), InlineKeyboardButton("CBE", callback_data="p_cbe")]]
    await update.message.reply_text("የመመዝገቢያ 200 ብር መክፈያ መንገድ ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
    return PAY_CHOICE

async def get_pay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank = "Telebirr 0954873397" if update.callback_query.data == "p_tele" else "CBE 1000536009276"
    await update.callback_query.message.reply_text(f"በ {bank} ከፍለው ደረሰኙን (Screenshot) ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    info, password = context.user_data['reg'], context.user_data['pass']
    
    conn = sqlite3.connect('ekub_final_pro_v5.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)", (user_id, info, password, "Pending", "Not Paid"))
    conn.commit()
    conn.close()

    verify_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Verify Registration ✅", callback_data=f"v_reg_{user_id}")]])
    await context.bot.send_photo(ADMIN_ID, photo=context.user_data['id_img'], caption="🆔 መታወቂያ")
    await context.bot.send_photo(ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"🔔 አዲስ ምዝገባ\n\n{info}", reply_markup=verify_kb)
    
    await update.message.reply_text("ክፍያው እስኪረጋገጥ ትንሽ ይጠብቁ።", reply_markup=main_menu_keyboard(user_id))
    return ConversationHandler.END

# --- Profile & Admin Tasks ---
async def login_profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("የፕሮፋይል ሚስጥር ቁጥርዎን ያስገቡ፦")
    return LOGIN_PASS

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('ekub_final_pro_v5.db')
    c = conn.cursor()
    c.execute("SELECT info, password, status, weekly_pay FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    if user and str(user[1]) == str(update.message.text):
        profile_msg = f"👤 **የእርስዎ ፕሮፋይል**\n\n{user[0]}\nሁኔታ፦ {user[2]}\nሳምንታዊ ክፍያ፦ {user[3]}"
        await update.message.reply_text(profile_msg, parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id))
    else:
        await update.message.reply_text("❌ የተሳሳተ ፓስወርድ!")
    return ConversationHandler.END

async def admin_verify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, action, user_id = query.data.split("_")
    user_id = int(user_id)
    
    conn = sqlite3.connect('ekub_final_pro_v5.db')
    c = conn.cursor()
    if action == "reg":
        c.execute("UPDATE users SET status='Verified' WHERE user_id=?", (user_id,))
        await context.bot.send_message(user_id, "✅ ምዝገባዎ ተረጋግጧል!")
    elif action == "week":
        c.execute("UPDATE users SET weekly_pay='Paid' WHERE user_id=?", (user_id,))
        await context.bot.send_message(user_id, "✅ የሳምንት ክፍያዎ ተረጋግጧል! Good luck!")
    conn.commit()
    conn.close()
    await query.edit_message_caption(caption="🟢 ተረጋግጧል")

# --- Weekly Payment ---
async def admin_start_ekub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('ekub_final_pro_v5.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("በ Telebirr", callback_data="pay_e_tele"), InlineKeyboardButton("በ CBE", callback_data="pay_e_cbe")]])
    for u in users:
        try: await context.bot.send_message(u[0], "🏁 እቁብ ተጀምሯል! ክፍያዎን ይፈጽሙ፦", reply_markup=kb)
        except: continue
    await update.callback_query.message.reply_text("ተልኳል!")

async def ekub_pay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank = "Telebirr 0954873397" if update.callback_query.data == "pay_e_tele" else "CBE 1000536009276"
    await update.callback_query.message.reply_text(f"በ {bank} ከፍለው ደረሰኙን ይላኩ፦")
    return EKUB_PAY_SCREENSHOT

async def get_ekub_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    verify_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Verify Weekly Payment ✅", callback_data=f"v_week_{user_id}")]])
    await context.bot.send_photo(ADMIN_ID, photo=update.message.photo[-1].file_id, caption=f"💰 የሳምንት ክፍያ ደረሰኝ ከ: {user_id}", reply_markup=verify_kb)
    await update.message.reply_text("ክፍያው እስኪረጋገጥ ይጠብቁ።", reply_markup=main_menu_keyboard(user_id))
    return ConversationHandler.END

# --- Main App ---
if __name__ == '__main__':
    Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_reg, pattern="reg_start"),
            CallbackQueryHandler(login_profile_start, pattern="login_profile"),
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
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_profile)],
            EKUB_PAY_SCREENSHOT: [MessageHandler(filters.PHOTO, get_ekub_screenshot)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_verify_handler, pattern="^v_"))
    app.add_handler(CallbackQueryHandler(admin_start_ekub, pattern="admin_start_ekub"))
    
    app.run_polling()
