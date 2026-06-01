import os
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- 1. ቦቱ ሳይዘጋ በRender ላይ ንቁ ሆኖ እንዲቆይ (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home(): 
    return "Ethio-Canada Bot is Online and Active! 🍁✈️"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. ዋና ቅንብሮች (የታደሰው አዲስ TOKEN እና ADMIN ID) ---
TOKEN = "8971919038:AAEDbX6BS8zPUQg5AgE0Wag5uiu0eTXpLu0"
ADMINS = [7705713321]  # የእርስዎ የአድሚን ID

# የቦቱ ስቴቶች (States)
NAME, F_NAME, G_NAME, DOB, GENDER, PHONE, JOB, REGION_COUNTRY, KEBELE, ID_PHOTO, MAIN_MENU, ASK_QUESTION, BROADCAST = range(13)

# የዳታቤዝ መዋቅር ማዘጋጃ
def init_db():
    conn = sqlite3.connect('travellers.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, name TEXT, f_name TEXT, g_name TEXT, dob TEXT, gender TEXT, phone TEXT, job TEXT, region TEXT, kebele TEXT, id_photo TEXT, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

# ቋሚ የተጠቃሚ ማውጫ አዝራሮች
def main_menu_keyboard(uid):
    kb = [
        ["ℹ️ መረጃ ለማግኘት", "❓ ጥያቄ ለመጠየቅ"]
    ]
    if uid in ADMINS:
        kb.append(["📢 ማስታወቂያ ላክ (አድሚን)"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, persistent=True)

# --- 3. የቦቱ ዋና ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    uid = update.effective_user.id
    context.user_data.clear() # አሮጌ ዳታን ለማጽዳት
    
    await update.message.reply_text(
        "👋 እንኳን ወደ **የኢትዮ-ካናዳ ተጓዦች ምዝገባ ቦት** በደህና መጡ! 🍁✈️\n\n"
        "✨ እባክዎ መጀመሪያ የምዝገባ ቅጹን በትክክል ይሙሉ::\n\n"
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
    await update.message.reply_text("📅 **የልደት ቀንዎን ያስገቡ (ቀን/ወር/ዓመት - ምሳሌ፡ 24/08/1998)፦**", parse_mode="Markdown")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dob'] = update.message.text
    gender_kb = [["👦 ወንድ", "👧 ሴት"]]
    await update.message.reply_text(
        "🚻 **እባክዎ ጾታዎን ይምረጡ፦**", 
        reply_markup=ReplyKeyboardMarkup(gender_kb, resize_keyboard=True)
    )
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['gender'] = update.message.text
    await update.message.reply_text(
        "📞 **የስልክ ቁጥርዎን ያስገቡ (ምሳሌ፡ 09...)፦**", 
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("💼 **የአሁኑ ስራዎን (Job) ያስገቡ፦**", parse_mode="Markdown")
    return JOB

async def get_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['job'] = update.message.text
    await update.message.reply_text("🌍 **የሚኖሩበትን ሀገር እና ክልል (Country & Region) ያስገቡ፦**", parse_mode="Markdown")
    return REGION_COUNTRY

async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['region'] = update.message.text
    await update.message.reply_text("🏡 **የመኖሪያ ቀበሌዎን (Kebele) ያስገቡ፦**", parse_mode="Markdown")
    return KEBELE

async def get_kebele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['kebele'] = update.message.text
    await update.message.reply_text("📸 **እባክዎ የቀበሌ ወይም የብሔራዊ መታወቂያዎን ፎቶ (ID Photo) እዚህ ይላኩ፦**", parse_mode="Markdown")
    return ID_PHOTO

async def get_id_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ እባክዎ የመታወቂያዎን ፎቶ (Image) ብቻ በትክክል ይላኩ!")
        return ID_PHOTO
        
    fid = update.message.photo[-1].file_id
    d = context.user_data
    uid = update.effective_user.id
    date_str = (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
    
    # መረጃውን ዳታቤዝ ውስጥ ማስቀመጥ
    conn = sqlite3.connect('travellers.db')
    conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", 
                 (uid, d['name'], d['f_name'], d['g_name'], d['dob'], d['gender'], d['phone'], d['job'], d['region'], d['kebele'], fid, 'Pending', date_str))
    conn.commit()
    conn.close()
    
    # ለአድሚን የሚላክ ሙሉ መረጃ
    admin_txt = (
        f"🔔 **አዲስ የተጓዥ ምዝገባ ጥያቄ ደርሷል!** 🍁\n\n"
        f"👤 ስም፦ {d['name']} {d['f_name']} {d['g_name']}\n"
        f"📅 የልደት ቀን፦ {d['dob']}\n"
        f"🚻 ጾታ፦ {d['gender']}\n"
        f"📞 ስልክ፦ {d['phone']}\n"
        f"💼 ስራ፦ {d['job']}\n"
        f"🌍 ሀገር/ክልል፦ {d['region']}\n"
        f"🏡 ቀበሌ፦ {d['kebele']}\n"
        f"🆔 User ID: `{uid}`"
    )
    
    # የማረጋገጫ ኢንላይን አዝራሮች
    admin_kb = [[
        InlineKeyboardButton("✅ አጽድቅ (Verify)", callback_data=f"verify_{uid}"),
        InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{uid}")
    ]]
    
    # ለአድሚኖች መላክ
    for a in ADMINS:
        try:
            await context.bot.send_photo(chat_id=a, photo=fid, caption=admin_txt, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")
        except Exception:
            pass
            
    await update.message.reply_text(
        "⏳ **ጥያቄዎ በአሁኑ ሰዓት እየተሰራ ነው (Your request is being processed)...**\n\n"
        "🕵️ መረጃዎ በአድሚን ተረጋግጦ ሲያልቅ የማረጋገጫ መልዕክት ይደርስዎታል። እናመሰግናለን! 🙏",
        reply_markup=main_menu_keyboard(uid),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# --- 4. ዋና ማውጫ እና የተጠቃሚ ገጽ ቁልፎች ማስተናገጃ ---
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    
    if text == "ℹ️ መረጃ ለማግኘት":
        info_msg = (
            "🍁 **ስለ ኢትዮ-ካናዳ ተጓዦች ማህበር** ✈️\n\n"
            "ይህ ቦት ወደ ካናዳ ለመጓዝ ለሚፈልጉ ኢትዮጵያውያን ተጓዦች ይፋዊ የመመዝገቢያ መድረክ ነው። "
            "የሚያስገቡት መረጃ ሙሉ በሙሉ በምስጢር ተጠብቆ ለአስተዳዳሪዎች የሚተላለፍ ይሆናል።"
        )
        await update.message.reply_text(info_msg, reply_markup=main_menu_keyboard(uid), parse_mode="Markdown")
        return MAIN_MENU
        
    elif text == "❓ ጥያቄ ለመጠየቅ":
        await update.message.reply_text("✍️ እባክዎ ጥያቄዎን እዚህ ይጻፉልኝ፤ ለአድሚኑ በቀጥታ ይደርሳል፦")
        return ASK_QUESTION
        
    elif text == "📢 ማስታወቂያ ላክ (አድሚን)" and uid in ADMINS:
        await update.message.reply_text("📝 ለሁሉም ተጠቃሚዎች የሚላክ **ጽሑፍ፣ ፎቶ (Photo) ወይም ቪዲዮ (Video)** ይላኩ፦")
        return BROADCAST
        
    return MAIN_MENU

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    txt = update.message.text
    
    admin_msg = f"📩 **አዲስ ጥያቄ ከተጠቃሚ መጥቷል!**\n\n👤 ስም: {user.first_name}\n🆔 ID: {user.id}\n📝 ጥያቄ: {txt}"
    for a in ADMINS:
        try:
            await context.bot.send_message(a, admin_msg)
        except Exception:
            pass
            
    await update.message.reply_text("✅ ጥያቄዎ ለአድሚን በተሳካ ሁኔታ ደርሷል! በቅርቡ መልስ ይሰጥዎታል።", reply_markup=main_menu_keyboard(user.id))
    return MAIN_MENU

# --- 5. የአድሚን ማረጋገጫ (Verify/Reject) ቁልፍ ተግባር ---
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    action, target_id = q.data.split("_")
    target_id = int(target_id)
    
    if update.effective_user.id not in ADMINS:
        return
        
    conn = sqlite3.connect('travellers.db')
    if action == "verify":
        conn.execute("UPDATE users SET status='Verified' WHERE id=?", (target_id,))
        u = conn.execute("SELECT name, f_name, g_name, phone FROM users WHERE id=?", (target_id,)).fetchone()
        conn.commit()
        
        if u:
            success_msg = (
                f"🎉 **እንኳን ደስ አለዎት! ምዝገባዎ በአድሚን ተረጋግጧል።** ✅\n\n"
                f"🍁 **የተጓዥ መረጃ ማረጋገጫ**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 ሙሉ ስም፦ {u[0]} {u[1]} {u[2]}\n"
                f"📞 ስልክ ቁጥር፦ {u[3]}\n"
                f"📋 ሁኔታ፦ **የተረጋገጠ (Verified) ✅**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👍 መልካም የጉዞ ዝግጅት ይሁንልዎት!"
            )
            try:
                await context.bot.send_message(chat_id=target_id, text=success_msg, reply_markup=main_menu_keyboard(target_id), parse_mode="Markdown")
            except Exception:
                pass
        await q.edit_message_caption(q.message.caption + "\n\n🟢 **ሁኔታ፦ ምዝገባው ጸድቋል ✅**")
        
    elif action == "reject":
        conn.execute("UPDATE users SET status='Rejected' WHERE id=?", (target_id,))
        conn.commit()
        try:
            await context.bot.send_message(chat_id=target_id, text="❌ **ይቅርታ፣ ያስገቡት የምዝገባ መረጃ ወይም መታወቂያ በአድሚን ውድቅ ተደርጓል።**\nእባክዎ እንደገና በ /start በመግባት በትክክል ይመዝገቡ።")
        except Exception:
            pass
        await q.edit_message_caption(q.message.caption + "\n\n🔴 **ሁኔታ፦ ውድቅ ተደርጓል ❌**")
        
    conn.close()

# --- 6. ማስታወቂያ (ጽሑፍ፣ ፎቶ፣ ቪዲዮ) ለሁሉም መላኪያ ---
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: 
        return ConversationHandler.END
        
    conn = sqlite3.connect('travellers.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    
    count = 0
    msg = update.message
    
    for u in users:
        try:
            if msg.text:
                await context.bot.send_message(chat_id=u[0], text=msg.text)
            elif msg.photo:
                await context.bot.send_photo(chat_id=u[0], photo=msg.photo[-1].file_id, caption=msg.caption)
            elif msg.video:
                await context.bot.send_video(chat_id=u[0], video=msg.video.file_id, caption=msg.caption)
            count += 1
        except Exception:
            pass
            
    await update.message.reply_text(f"📢 ማስታወቂያው ለ {count} ተጠቃሚዎች በተሳካ ሁኔታ ተላልፏል! 🎉", reply_markup=main_menu_keyboard(update.effective_user.id))
    return MAIN_MENU

# --- 7. ዋናው የማስነሻ ክፍል ---
if __name__ == '__main__':
    keep_alive() # ቦቱ ሳይዘጋ 24 ሰዓት እንዲሰራ መለቀቂያ
    
    application = Application.builder().token(TOKEN).build()
    
    # የኢንላይን አዝራሮች መያዣ
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^(verify|reject)_"))
    
    # የምዝገባ እና የዋና ማውጫ ፍሰት መቆጣጠሪያ
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_f_name)],
            G_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_name)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_job)],
            REGION_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
            KEBELE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_kebele)],
            ID_PHOTO: [MessageHandler(filters.PHOTO, get_id_photo)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
            BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, handle_broadcast)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    application.add_handler(conv_handler)
    
    print("Ethio-Canada Bot Started...")
    application.run_polling()
