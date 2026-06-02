import os
import sqlite3
import logging
import asyncio
import threading
from datetime import datetime, timedelta
import gradio as gr
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- 1. Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_STATUS = "⏳ Starting bot engine..."

# --- 2. Configuration ---
TOKEN = "8890546990:AAFafxTxoJKnc4a6Gw5_Tgk0ELhstmyTVF4"
ADMINS = [7705713321]  

NAME, F_NAME, G_NAME, DOB_YEAR, DOB_MONTH, DOB_DAY, GENDER, PHONE, JOB, REGION, COUNTRY, KEBELE, ID_PHOTO, MAIN_MENU, ASK_QUESTION, BROADCAST = range(16)

def init_db():
    conn = sqlite3.connect('travellers.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, f_name TEXT, g_name TEXT, dob TEXT, gender TEXT, phone TEXT, job TEXT, region TEXT, country TEXT, kebele TEXT, id_photo TEXT, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def main_menu_keyboard(uid):
    kb = [["ℹ️ መረጃ ለማግኘት", "❓ ጥያቄ ለመጠየቅ"]]
    if uid in ADMINS:
        kb.append(["📢 ማስታወቂያ ላክ (አድሚን)"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, persistent=True)

# --- 3. Bot Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    uid = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text(
        "👋 እንኳን ወደ **የኢትዮ-ካናዳ ተጓዦች ምዝገባ ቦት** በደህና መጡ! 🍁✈️\n\n"
        "👤 **የመጀመሪያ ስምዎን ያስገቡ፦**",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("👤 **የአባት ስምዎን ያስገቡ፦**", parse_mode="Markdown")
    return F_NAME

async def get_f_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['f_name'] = update.message.text
    await update.message.reply_text("👤 **የአያት ስምዎን ያስገቡ፦**", parse_mode="Markdown")
    return G_NAME

async def get_g_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['g_name'] = update.message.text
    
    keyboard = []
    row = []
    for y in range(1985, 2011):
        row.append(InlineKeyboardButton(str(y), callback_data=f"year_{y}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
        
    await update.message.reply_text("📅 **እባክዎ የተወለዱበትን ዓመተ ምህረት (Year) ይምረጡ፦**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return DOB_YEAR

async def get_dob_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    year = q.data.split("_")[1]
    context.user_data['dob_year'] = year
    
    keyboard = []
    row = []
    for m in range(1, 13):
        row.append(InlineKeyboardButton(f"{m} ወር", callback_data=f"month_{m}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
        
    await q.edit_message_text(f"✅ የመረጡት ዓመት፦ {year}\n\n🌙 **እባክዎ የተወለዱበትን ወር (Month) ይምረጡ፦**", reply_markup=InlineKeyboardMarkup(keyboard))
    return DOB_MONTH

async def get_dob_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    month = q.data.split("_")[1]
    context.user_data['dob_month'] = month
    
    keyboard = []
    row = []
    for d in range(1, 32):
        row.append(InlineKeyboardButton(str(d), callback_data=f"day_{d}"))
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
        
    await q.edit_message_text(f"✅ የመረጡት ወር፦ {month}\n\n☀️ **እባክዎ የተወለዱበትን ቀን (Day) ይምረጡ፦**", reply_markup=InlineKeyboardMarkup(keyboard))
    return DOB_DAY

async def get_dob_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    day = q.data.split("_")[1]
    
    dob_str = f"{day}/{context.user_data['dob_month']}/{context.user_data['dob_year']}"
    context.user_data['dob'] = dob_str
    
    gender_kb = [
        [InlineKeyboardButton("👦 ወንድ (Male)", callback_data="gender_Male"),
         InlineKeyboardButton("👧 ሴት (Female)", callback_data="gender_Female")]
    ]
    await q.edit_message_text(f"✅ የተመረጠው የልደት ቀን፦ {dob_str}\n\n🚻 **እባክዎ ጾታዎን ይምረጡ፦**", reply_markup=InlineKeyboardMarkup(gender_kb))
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    gender = q.data.split("_")[1]
    context.user_data['gender'] = "ወንድ" if gender == "Male" else "ሴት"
    
    await q.message.reply_text("📞 **የስልክ ቁጥርዎን ያስገቡ (ምሳሌ፡ 09...)፦**", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("💼 **የአሁኑ ስራዎን (Job) ያስገቡ፦**", parse_mode="Markdown")
    return JOB

async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['job'] = update.message.text
    
    regions = [
        "አዲስ አበባ", "ኦሮሚያ", "አማራ", "ትግራይ", 
        "ሶማሌ", "አፋር", "ሲዳማ", "ሀረሪ", 
        "ጋምቤላ", "ቤንሻንጉል", "ድሬዳዋ", "ደቡብ ኢትዮጵያ"
    ]
    keyboard = []
    row = []
    for r in regions:
        row.append(InlineKeyboardButton(r, callback_data=f"reg_{r}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
        
    await update.message.reply_text("🗺️ **እባክዎ የሚኖሩበትን ክልል በባተን ይምረጡ፦**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return REGION

async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    region_name = q.data.split("_")[1]
    context.user_data['region'] = region_name
    
    await q.edit_message_text(f"✅ የተመረጠው ክልል፦ {region_name}\n\n🌍 **እባክዎ አሁን ያሉበትን ሀገር (Country) በጽሑፍ ያስገቡ፦**")
    return COUNTRY

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    await update.message.reply_text("🏡 **የመኖሪያ ቀበሌዎን (Kebele) ያስገቡ፦**", parse_mode="Markdown")
    return KEBELE

async def get_kebele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['kebele'] = update.message.text
    await update.message.reply_text("📸 **እባክዎ የቀበሌ ወይም የብሔራዊ መታወቂያዎን ፎቶ (ID Photo) እዚህ ይላኩ፦**", parse_mode="Markdown")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ እባክዎ የመታወቂያዎን ፎቶ ብቻ በትክክል ይላኩ!")
        return ID_PHOTO
        
    fid = update.message.photo[-1].file_id
    d = context.user_data
    uid = update.effective_user.id
    date_str = (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
    
    conn = sqlite3.connect('travellers.db')
    conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                 (uid, d['name'], d['f_name'], d['g_name'], d['dob'], d['gender'], d['phone'], d['job'], d['region'], d['country'], d['kebele'], fid, 'Pending', date_str))
    conn.commit()
    conn.close()
    
    admin_txt = f"🔔 **አዲስ የተጓዥ ምዝገባ ጥያቄ ደርሷል!** 🍁\n\n👤 ስም፦ {d['name']} {d['f_name']} {d['g_name']}\n📅 የልደት ቀን፦ {d['dob']}\n🚻 ጾታ፦ {d['gender']}\n📞 ስልክ፦ {d['phone']}\n💼 ስራ፦ {d['job']}\n🗺️ ክልል፦ {d['region']}\n🌍 ሀገር፦ {d['country']}\n🏡 ቀበሌ፦ {d['kebele']}\n🆔 User ID: `{uid}`"
    admin_kb = [[InlineKeyboardButton("✅ አጽድቅ (Verify)", callback_data=f"verify_{uid}"), InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{uid}")]]
    
    for a in ADMINS:
        try:
            await context.bot.send_photo(chat_id=a, photo=fid, caption=admin_txt, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending to admin {a}: {e}")
            
    await update.message.reply_text("⏳ **Your request is being processed**\n\n🕵️ መረጃዎ በአድሚን ተረጋግጦ ሲያልቅ የማረጋገጫ መልዕክት ይደርስዎታል። እናመሰግናለን! 🙏", reply_markup=main_menu_keyboard(uid), parse_mode="Markdown")
    return MAIN_MENU

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    
    if text == "ℹ️ መረጃ ለማግኘት":
        info_msg = "🍁 **ስለ ኢትዮ-ካናዳ ተጓዦች ማህበር** ✈️\n\nይህ ቦት ወደ አስተማማኝ የካናዳ ጉዞ ለመሄድ ለሚፈልጉ ኢትዮጵያውያን ተጓዦች ይፋዊ የመመዝገቢያ መድረክ ነው።"
        await update.message.reply_text(info_msg, reply_markup=main_menu_keyboard(uid), parse_mode="Markdown")
        return MAIN_MENU
    elif text == "❓ ጥያቄ ለመጠየቅ":
        await update.message.reply_text("✍️ እባክዎ ጥያቄዎን እዚህ ይጻፉልኝ፤ ለአድሚኑ በቀጥታ ይደርሳል፦")
        return ASK_QUESTION
    elif text == "📢 ማስታወቂያ ላክ (አድሚን)" and uid in ADMINS:
        await update.message.reply_text("📝 ለሁሉም ተጠቃሚዎች የሚላክ **ጽሑፍ፣ ፎቶ ወይም ቪዲዮ** ይላኩ፦")
        return BROADCAST
    return MAIN_MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admin_msg = f"📩 **አዲስ ጥያቄ ከተጠቃሚ መጥቷል!**\n\n👤 ስም: {user.first_name}\n🆔 ID: {user.id}\n📝 ጥያቄ: {update.message.text}"
    for a in ADMINS:
        try:
            await context.bot.send_message(a, admin_msg)
        except Exception as e:
            logger.error(f"Error sending question to admin: {e}")
    await update.message.reply_text("✅ ጥያቄዎ ለአድሚን በተሳካ ሁኔታ ደርሷል! በቅርቡ መልስ ይሰጥዎታል።", reply_markup=main_menu_keyboard(user.id))
    return MAIN_MENU

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action, target_id = q.data.split("_")
    target_id = int(target_id)
    
    if update.effective_user.id not in ADMINS: return
        
    conn = sqlite3.connect('travellers.db')
    if action == "verify":
        conn.execute("UPDATE users SET status='Verified' WHERE id=?", (target_id,))
        conn.commit()
        try:
            await context.bot.send_message(chat_id=target_id, text="🎉 **እንኳን ደስ አለዎት! ምዝገባዎ በአድሚን ተረጋግጧል።** ✅", reply_markup=main_menu_keyboard(target_id), parse_mode="Markdown")
        except Exception: pass
        await q.edit_message_caption(q.message.caption + "\n\n🟢 **ሁኔታ፦ ምዝገባው ጸድቋል ✅**")
    elif action == "reject":
        conn.execute("UPDATE users SET status='Rejected' WHERE id=?", (target_id,))
        conn.commit()
        try:
            await context.bot.send_message(chat_id=target_id, text="❌ **ይቅርታ፣ ያስገቡት መረጃ በአድሚን ውድቅ ተደርጓል።**")
        except Exception: pass
        await q.edit_message_caption(q.message.caption + "\n\n🔴 **ሁኔታ፦ ውድቅ ተደርጓል ❌**")
    conn.close()

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return ConversationHandler.END
    conn = sqlite3.connect('travellers.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    
    count = 0
    msg = update.message
    for u in users:
        try:
            if msg.text: await context.bot.send_message(chat_id=u[0], text=msg.text)
            elif msg.photo: await context.bot.send_photo(chat_id=u[0], photo=msg.photo[-1].file_id, caption=msg.caption)
            elif msg.video: await context.bot.send_video(chat_id=u[0], video=msg.video.file_id, caption=msg.caption)
            count += 1
        except Exception: pass
    await update.message.reply_text(f"📢 ማስታወቂያው ለ {count} ተጠቃሚዎች ተላልፏል! 🎉", reply_markup=main_menu_keyboard(update.effective_user.id))
    return MAIN_MENU

# --- 4. Engine Bootloader ---
def run_telegram_bot():
    global BOT_STATUS
    try:
        init_db()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(verify|reject)_"))
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
                F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_f_name)],
                G_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_name)],
                DOB_YEAR: [CallbackQueryHandler(get_dob_year)],
                DOB_MONTH: [CallbackQueryHandler(get_dob_month)],
                DOB_DAY: [CallbackQueryHandler(get_dob_day)],
                GENDER: [CallbackQueryHandler(get_gender)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
                JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
                REGION: [CallbackQueryHandler(get_region)],
                COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
                KEBELE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_kebele)],
                ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router)],
                ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
                BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, handle_broadcast)]
            },
            fallbacks=[CommandHandler('start', start)]
        )
        application.add_handler(conv_handler)
        
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        loop.run_until_complete(application.start())
        loop.run_until_complete(application.updater.start_polling(allowed_updates=Update.ALL_TYPES))
        
        BOT_STATUS = "🟢 Bot Engine Running Successfully!"
        loop.run_forever()
    except Exception as e:
        BOT_STATUS = f"❌ Bot crash: {str(e)}"
        logger.error(f"Bot crash: {e}")

def check_status():
    return BOT_STATUS

with gr.Blocks() as demo:
    gr.Markdown("# 🍁 Ethio-Canada Telegram Bot Platform ✈️")
    status_markdown = gr.Markdown(value=BOT_STATUS)
    demo.load(check_status, outputs=status_markdown)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    render_port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=render_port)
