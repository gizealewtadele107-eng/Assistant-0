import os
import logging
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# --- 1. CONFIGURATION ---
TOKEN = "8687440246:AAF2TwGdbBnP47kRd0YK8nVNGOCGEl8wzJs"
ADMIN_IDS = [8442116232, 7705713321, 7962418315]
BOT_NAME = "ዳዊት የመኪና ሎተሪ እና እቁብ"

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

# የክፍያ መረጃዎች
TELEBIRR_INFO = "📱 **በቴሌብር (Telebirr) ለመክፈል**\n\n📞 ስልክ ቁጥር: `0974671344`\n👤 ስም: [እባክዎ እዚህ ጋ ትክክለኛውን ስም ይተኩ]"
CBE_INFO = "🏦 **በንግድ ባንክ (CBE) ለመክፈል**\n\n💳 አካውንት: `1000701313821`\n👤 ስም: ዳዊት"

CARS = {
    "ሀይሩፍ": "2,500 ብር",
    "አይሱዙ": "3,000 ብር"
}

sold_tickets = {"ሀይሩፍ": set(), "አይሱዙ": set()}

NAME, FATHER_NAME, PHONE_NUM, CHOICE_CAR, TICKET_NUM, CHOOSE_PAYMENT, RECEIPT, ASK_QUESTION, ADMIN_REPLY = range(9)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 2. KEYBOARDS ---
# ልክ እንደ ግዜው ቦት ሁልጊዜ ከታች የሚቀመጥ ዋና ማውጫ
def main_reply_keyboard():
    kb = [
        [KeyboardButton("🎟 እጣ ለመቁረጥ"), KeyboardButton("ℹ️ ስለ ቦቱ መረጃ")],
        [KeyboardButton("❓ አድሚንን ጠይቅ")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, persistent=True)

# --- 3. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 ሰላም! እንኳን ወደ **{BOT_NAME}** በደህና መጡ! 🎉\n\n"
        "✨ እባክዎ መጀመሪያ ምዝገባ ያካሂዱ።\n"
        "👤 **የእርስዎን ስም (First Name)** ያስገቡ፦",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("✨ በጣም ጥሩ! አሁን ደግሞ **የአባትዎን ስም (Second Name)** ያስገቡ፦", parse_mode="Markdown")
    return FATHER_NAME

async def get_father_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['father_name'] = update.message.text
    btn = [[KeyboardButton(text="📲 ስልክ ቁጥርዎን ለማጋራት እዚህ ይጫኑ", request_contact=True)]]
    await update.message.reply_text(
        "✨ በመጨረሻም **የስልክ ቁጥርዎን** ከታች ያለውን አዝራር ተጭነው ያጋሩን ወይም እዚህ ይጻፉልን፦",
        reply_markup=ReplyKeyboardMarkup(btn, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return PHONE_NUM

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data['user_phone'] = update.message.contact.phone_number
    else:
        context.user_data['user_phone'] = update.message.text
        
    await update.message.reply_text(
        "✅ **ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል!** 🎉\n\n"
        "👇 ከታች ካሉት አማራጮች አንዱን በመጫን እጣ መቁረጥ ይችላሉ፦",
        reply_markup=main_reply_keyboard(),
        parse_mode="Markdown"
    )
    return CHOICE_CAR

# የቴክስት መልዕክቶችን (ከታች ኪቦርድ የሚመጡትን) መቆጣጠሪያ
async def handle_text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "ℹ️ ስለ ቦቱ መረጃ":
        info_text = f"ℹ️ **ስለ {BOT_NAME}**\n\n" \
                    f"ይህ ቦት በታማኝነት የሀይሩፍ እና የአይሱዙ መኪናዎችን በእጣ እና በእቁብ የሚያስተላልፍበት ኦፊሴላዊ መድረክ ነው! 🚗🚚"
        await update.message.reply_text(info_text, parse_mode="Markdown")
        return CHOICE_CAR
        
    elif text == "🎟 እጣ ለመቁረጥ" or text == "🔄 ሌላ እጣ ይቁረጡ":
        kb = [
            [InlineKeyboardButton("🚗 ሀይሩፍ (2,500 ብር)", callback_data="car_ሀይሩፍ")],
            [InlineKeyboardButton("🚚 አይሱዙ (3,000 ብር)", callback_data="car_አይሱዙ")]
        ]
        await update.message.reply_text("👇 ለመቁረጥ የሚፈልጉትን የመኪና አይነት ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
        return CHOICE_CAR
        
    elif text == "❓ አድሚንን ጠይቅ":
        await update.message.reply_text("✍️ ለአድሚን ለመላክ የሚፈልጉትን ጥያቄ ወይም መልዕክት እዚህ ይጻፉልኝ፦")
        return ASK_QUESTION
        
    return CHOICE_CAR

async def car_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    selected_car = query.data.split("_")[1]
    context.user_data['car'] = selected_car
    
    await query.message.reply_text(
        f"🎯 የ **{selected_car}** መኪናን መርጠዋል።\n\n"
        f"🎟 እባክዎ ከ **1 እስከ 1000** ያለ የእጣ ቁጥር ይምረጡና ቁጥሩን ብቻ ይጻፉልኝ (ለምሳሌ: `45`)፦",
        parse_mode="Markdown"
    )
    return TICKET_NUM

async def check_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticket_text = update.message.text
    selected_car = context.user_data.get('car')
    
    if not ticket_text.isdigit() or not (1 <= int(ticket_text) <= 1000):
        await update.message.reply_text("❌ እባክዎ ከ 1 እስከ 1000 ያለ ትክክለኛ ቁጥር ብቻ ያስገቡ!")
        return TICKET_NUM
        
    ticket_num = int(ticket_text)
    if ticket_num in sold_tickets[selected_car]:
        await update.message.reply_text(f"❌ ይቅርታ፣ የእጣ ቁጥር {ticket_num} አስቀድሞ ተሽጧል! እባክዎ ሌላ ቁጥር ይምረጡ፦")
        return TICKET_NUM
        
    context.user_data['ticket'] = ticket_num
    
    # የክፍያ አማራጭ በተኖች (ልክ እንደ ግዜው ቦት)
    pay_kb = [
        [InlineKeyboardButton("📱 ቴሌብር (Telebirr)", callback_data="pay_telebirr")],
        [InlineKeyboardButton("🏦 የኢትዮጵያ ንግድ ባንክ (CBE)", callback_data="pay_cbe")]
    ]
    
    await update.message.reply_text(
        f"✔️ የመረጡት የእጣ ቁጥር፦ **{ticket_num}**\n\n"
        f"👇 እባክዎ ክፍያ መፈጸም የሚፈልጉበትን ባንክ ይምረጡ፦",
        reply_markup=InlineKeyboardMarkup(pay_kb),
        parse_mode="Markdown"
    )
    return CHOOSE_PAYMENT

async def payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "pay_telebirr":
        await query.message.reply_text(f"{TELEBIRR_INFO}\n\n⚠️ ክፍያውን ከፈጸሙ በኋላ **የክፍያ ደረሰኝ ፎቶ (Screenshot)** እዚህ ላይ ይላኩ።", parse_mode="Markdown")
    elif query.data == "pay_cbe":
        await query.message.reply_text(f"{CBE_INFO}\n\n⚠️ ክፍያውን ከፈጸሙ በኋላ **የክፍያ ደረሰኝ ፎቶ (Screenshot)** እዚህ ላይ ይላኩ።", parse_mode="Markdown")
        
    return RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ እባክዎ የደረሰኝ ፎቶ (Screenshot) ብቻ ይላኩ!")
        return RECEIPT
        
    user = update.effective_user
    u_data = context.user_data
    
    admin_msg = f"📩 **አዲስ የእጣ ክፍያ ደረሰኝ ደርሷል!**\n\n" \
                f"👤 ተጠቃሚ: {u_data.get('first_name')} {u_data.get('father_name')}\n" \
                f"📞 ስልክ: {u_data.get('user_phone')}\n" \
                f"🚗 መኪና: {u_data.get('car')}\n" \
                f"🎟 እጣ ቁጥር: `{u_data.get('ticket')}`\n" \
                f"🆔 User ID: `{user.id}`"
    
    kb = [
        [InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data=f"verify_{user.id}_{u_data.get('car')}_{u_data.get('ticket')}")],
        [InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{user.id}")],
        [InlineKeyboardButton("💬 መልዕክት ለመላክ", callback_data=f"reply_{user.id}")]
    ]
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=admin_msg, parse_mode="Markdown")
            await context.bot.send_message(chat_id=admin_id, text="👇 የአድሚን ውሳኔ፦", reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass
            
    # "ሌላ እጣ ይቁረጡ" በተን ከታች ባለው ኪቦርድ እንዲመጣ እናደርጋለን
    retry_kb = ReplyKeyboardMarkup([[KeyboardButton("🔄 ሌላ እጣ ይቁረጡ")]], resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ **ደረሰኝዎ ለአድሚን በተሳካ ሁኔታ ተልኳል!**\n\n"
        "🕵️ በቅርቡ በአድሚን ተረጋግጦ የማረጋገጫ መልዕክት ይደርስዎታል። እናመሰግናለን! 🙏",
        reply_markup=retry_kb,
        parse_mode="Markdown"
    )
    return CHOICE_CAR

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action, target_user_id = data[0], int(data[1])
    
    if action == "verify":
        car_type, t_num = data[2], int(data[3])
        sold_tickets[car_type].add(t_num)
        await context.bot.send_message(
            chat_id=target_user_id, 
            text=f"🎉 **እንኳን ደስ አለዎት! ክፍያዎ ተረጋግጧል።**\n\n🚗 መኪና፦ {car_type}\n🎟 የእርስዎ እጣ ቁጥር፦ **{t_num}** ነው።\n\n👍 መልካም እድል!",
            reply_markup=main_reply_keyboard(),
            parse_mode="Markdown"
        )
        await query.message.edit_text("🟢 **ሁኔታ፦ ተረጋግጧል ✅**")
    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id, 
            text="❌ **ይቅርታ፣ የላኩት ደረሰኝ በአድሚን ተቀባይነት አላገኘም።**\n\nእባክዎ እንደገና በትክክል ይላኩ ወይም አድሚንን ያነጋግሩ።",
            reply_markup=main_reply_keyboard()
        )
        await query.message.edit_text("🔴 **ሁኔታ፦ ውድቅ ተደርጓል ❌**")
    elif action == "reply":
        context.application.user_data[query.from_user.id] = target_user_id
        await query.message.reply_text("✍️ ለተጠቃሚው የሚላከውን መልዕክት ይጻፉ፦")
        return ADMIN_REPLY

async def send_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    target_id = context.application.user_data.get(admin_id)
    if target_id:
        await context.bot.send_message(chat_id=target_id, text=f"💬 **ከአድሚን የተላከ መልዕክት፦**\n\n{update.message.text}")
        await update.message.reply_text("✅ መልዕክቱ ለተጠቃሚው ደርሷል።")
    return CHOICE_CAR

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id, 
                text=f"❓ **አዲስ ጥያቄ ደርሷል!**\n\n👤 ስም: {user.first_name}\n🆔 ID: {user.id}\n📝 ጥያቄ: {update.message.text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 መልስ ስጥ", callback_data=f"reply_{user.id}")]])
            )
        except:
            pass
    await update.message.reply_text("✅ ጥያቄዎ ለአድሚን ደርሷል! በቅርቡ ይመልሱልዎታል።")
    return CHOICE_CAR

# --- 4. WEBHOOK SETUP ---
async def main():
    app_tg = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            FATHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_father_name)],
            PHONE_NUM: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            CHOICE_CAR: [
                CallbackQueryHandler(car_callback, pattern="^car_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_menu)
            ],
            TICKET_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_ticket)],
            CHOOSE_PAYMENT: [CallbackQueryHandler(payment_callback, pattern="^pay_")],
            RECEIPT: [MessageHandler(filters.PHOTO, get_receipt)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)],
            ADMIN_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_admin_reply)]
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app_tg.add_handler(conv_handler)
    app_tg.add_handler(CallbackQueryHandler(admin_buttons, pattern="^(verify|reject|reply)_"))

    await app_tg.initialize()

    async def webhook_handle(request):
        req_body = await request.json()
        update = Update.de_json(req_body, app_tg.bot)
        await app_tg.process_update(update)
        return web.Response(text="OK")

    app_web = web.Application()
    app_web.router.add_post('/webhook', webhook_handle)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        await app_tg.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to: {webhook_url}")

    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
