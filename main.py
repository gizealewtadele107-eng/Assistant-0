import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# --- 1. RENDER PORT BINDING FIX ---
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Live and Running")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheck)
    server.serve_forever()

# --- 2. CONFIGURATION ---
TOKEN = "8717535794:AAGpqenurXE06jj6vsg1Mzx57YdeQrRQMe4"
ADMIN_IDS = [8442116232, 7705713321, 7962418315]
BOT_NAME = "ዳዊት የመኪና እቁብ"

# የክፍያ መረጃዎች
PAYMENT_INFO = (
    "🎯 **የክፍያ አማራጮች (Payment Methods)**\n\n"
    "📱 **በቴሌብር (Telebirr):**\n"
    "📞 ስልክ ቁጥር: `0974671344`\n"
    "👤 ስም: ዳዊት\n\n"
    "🏦 **በንግድ ባንክ (CBE):**\n"
    "💳 አካውንት: `1000701313821`\n"
    "👤 ስም: ዳዊት"
)

CARS = {
    "ሀይሩፍ": "2,500 ብር",
    "አይሱዙ": "3,000 ብር"
}

# የእጣ ቁጥሮችን መቆጣጠሪያ (በእውነተኛ ስራ ላይ በዳታቤዝ ቢተካ ይመረጣል)
sold_tickets = {
    "ሀይሩፍ": set(),
    "አይሱዙ": set()
}

# Conversation States
NAME, FATHER_NAME, PHONE_NUM, CHOICE_CAR, TICKET_NUM, RECEIPT, ASK_QUESTION, ADMIN_REPLY = range(8)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 3. KEYBOARDS ---
def user_main_menu():
    kb = [
        [InlineKeyboardButton("🏁 እቁብ ለመግባት", callback_data="buy_ticket")],
        [InlineKeyboardButton("ℹ️ ስለ እቁቡ መረጃ", callback_data="bot_info")],
        [InlineKeyboardButton("❓ አድሚንን ጠይቅ", callback_data="ask_admin")]
    ]
    return InlineKeyboardMarkup(kb)

def back_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ወደ ኋላ ተመለስ", callback_data="go_back")]])

# --- 4. HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"እንኳን ወደ **{BOT_NAME}** በደህና መጡ! 🎉\n\nእባክዎ መጀመሪያ ምዝገባ ያካሂዱ።\n**የእርስዎን ስም (First Name)** ያስገቡ፦",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['first_name'] = update.message.text
    await update.message.reply_text("አመሰግናለሁ! አሁን ደግሞ **የአባትዎን ስም** ያስገቡ፦", parse_mode="Markdown")
    return FATHER_NAME

async def get_father_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['father_name'] = update.message.text
    
    # ስልክ ቁጥር በተን
    btn = [[KeyboardButton(text="📲 ስልክ ቁጥርዎን ለማጋራት እዚህ ይጫኑ", request_contact=True)]]
    await update.message.reply_text(
        "በመጨረሻም **የስልክ ቁጥርዎን** ያጋሩን ወይም እዚህ ይጻፉ፦",
        reply_markup=ReplyKeyboardMarkup(btn, one_time_keyboard=True, resize_keyboard=True)
    )
    return PHONE_NUM

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data['user_phone'] = update.message.contact.phone_number
    else:
        context.user_data['user_phone'] = update.message.text

    await update.message.reply_text(
        "🎯 ምዝገባዎ ተጠናቋል። የሚፈልጉትን አገልግሎት ከታች ይምረጡ፦",
        reply_markup=user_main_menu()
    )
    return CHOICE_CAR

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "bot_info":
        info_text = f"ℹ️ **ስለ {BOT_NAME}**\n\nይህ ቦት በታማኝነት የሀይሩፍ እና የአይሱዙ መኪናዎችን በእጣ የሚያስተላልፍበት ኦፊሴላዊ መድረክ ነው።"
        await query.message.edit_text(info_text, reply_markup=back_markup(), parse_mode="Markdown")
        return CHOICE_CAR

    elif query.data == "buy_ticket":
        kb = [
            [InlineKeyboardButton(f"🚗 ሀይሩፍ ({CARS['ሀይሩፍ']})", callback_data="car_ሀይሩፍ")],
            [InlineKeyboardButton(f"🚚 አይሱዙ ({CARS['አይሱዙ']})", callback_data="car_አይሱዙ")],
            [InlineKeyboardButton("⬅️ ተመለስ", callback_data="go_back")]
        ]
        await query.message.edit_text("ለመግባት የሚፈልጉትን የመኪና አይነት ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
        return CHOICE_CAR

    elif query.data == "car_ሀይሩፍ" or query.data == "car_አይሱዙ":
        selected_car = query.data.split("_")[1]
        context.user_data['car'] = selected_car
        await query.message.reply_text(
            f"🎯 የ **{selected_car}** መኪናን መርጠዋል።\n\n"
            f"እባክዎ ከ **1 እስከ 1000** ያለ የእጣ ቁጥር ይምረጡና ቁጥሩን ብቻ ይጻፉልኝ (ለምሳሌ፡ `10`)፦"
        )
        return TICKET_NUM

    elif query.data == "ask_admin":
        await query.message.reply_text("ለአድሚን ለመላክ የሚፈልጉትን ጥያቄ ወይም መልዕክት እዚህ ይጻፉ፦")
        return ASK_QUESTION

    elif query.data == "go_back":
        await query.message.edit_text("ዋና ማውጫ፦", reply_markup=user_main_menu())
        return CHOICE_CAR

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

    await update.message.reply_text(
        f"የመረጡት ቁጥር፦ **{ticket_num}**\n\n"
        f"{PAYMENT_INFO}\n\n"
        "⚠️ ክፍያውን ከፈጸሙ በኋላ **የደረሰኝ ፎቶ (Screenshot)** እዚህ ላይ ይላኩ።",
        parse_mode="Markdown"
    )
    return RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ እባክዎ የደረሰኝ ፎቶ (Screenshot) ብቻ ይላኩ!")
        return RECEIPT

    user = update.effective_user
    u_data = context.user_data

    admin_msg = (
        f"📩 **አዲስ የእቁብ ክፍያ ደረሰኝ ደርሷል!**\n\n"
        f"👤 ተጠቃሚ: {u_data.get('first_name')} {u_data.get('father_name')}\n"
        f"📞 ስልክ: {u_data.get('user_phone')}\n"
        f"🚗 የመኪና አይነት: {u_data.get('car')}\n"
        f"🎟 የመረጠው ቁጥር: `{u_data.get('ticket')}`\n"
        f"🆔 User ID: `{user.id}`"
    )

    # አድሚን በተኖች
    kb = [
        [InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data=f"verify_{user.id}_{u_data.get('car')}_{u_data.get('ticket')}")],
        [InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{user.id}")],
        [InlineKeyboardButton("💬 መልዕክት ለመላክ", callback_data=f"reply_{user.id}")]
    ]

    # ለሁሉም አድሚኖች ደረሰኙን መላክ
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=update.message.photo[-1].file_id,
                caption=admin_msg,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )
        except Exception:
            pass

    await update.message.reply_text("✅ ደረሰኝዎ ለአድሚን ተልኳል! በቅርቡ ተረጋግጦ መልዕክት ይደርስዎታል። እናመሰግናለን!")
    return ConversationHandler.END

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[0]
    target_user_id = int(data[1])

    if action == "verify":
        car_type = data[2]
        t_num = int(data[3])
        sold_tickets[car_type].add(t_num) # ቁጥሩን መያዝ
        
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 እንኳን ደስ አለዎት! ክፍያዎ ተረጋግጧል።\n🚗 መኪና፦ {car_type}\n🎟 የእርስዎ እጣ ቁጥር፦ **{t_num}** ነው። መልካም እድል!",
            parse_mode="Markdown"
        )
        await query.message.edit_caption(caption=query.message.caption + "\n\n🟢 **ሁኔታ፦ ተረጋግጧል (Verified) ✅**")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ ይቅርታ፣ የላኩት ደረሰኝ ተቀባይነት አላገኘም። እባክዎ እንደገና በትክክል ይላኩ ወይም አድሚንን ያነጋግሩ።"
        )
        await query.message.edit_caption(caption=query.message.caption + "\n\n🔴 **ሁኔታ፦ ውድቅ ተደርጓል ❌**")

    elif action == "reply":
        context.shadow_data = target_user_id
        await query.message.reply_text("ለተጠቃሚው የሚላከውን መልዕክት ይጻፉ፦")
        return ADMIN_REPLY

async def send_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = getattr(context, 'shadow_data', None)
    if target_id:
        await context.bot.send_message(chat_id=target_id, text=f"💬 **ከአድሚን የተላከ መልዕክት፦**\n\n{update.message.text}")
        await update.message.reply_text("✅ መልዕክቱ ለተጠቃሚው ደርሷል።")
    return ConversationHandler.END

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u_msg = update.message.text

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"❓ **አዲስ ጥያቄ ከተጠቃሚ ደርሷል!**\n\n👤 ስም: {user.first_name}\n🆔 ID: `{user.id}`\n📝 ጥያቄ: {u_msg}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 መልስ ስጥ", callback_data=f"reply_{user.id}")]])
            )
        except Exception:
            pass

    await update.message.reply_text("✅ ጥያቄዎ ለአድሚን ደርሷል! በቅርቡ ይመልሱልዎታል።")
    return ConversationHandler.END

# --- 5. MAIN ---
if __name__ == '__main__':
    # Render መዘጋትን ለመከላከል Health Check ማስጀመር
    Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            FATHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_father_name)],
            PHONE_NUM: [MessageHandler((filters.TEXT | filters.CONTACT) & ~filters.COMMAND, get_phone)],
            CHOICE_CAR: [CallbackQueryHandler(menu_callback)],
            TICKET_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_ticket)],
            RECEIPT: [MessageHandler(filters.PHOTO, get_receipt)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin)],
            ADMIN_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_admin_reply)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^(verify|reject|reply)_"))

    print(f
