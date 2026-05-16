import os
import logging
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# --- 1. CONFIGURATION ---
TOKEN = "8717535794:AAGpqenurXE06jj6vsg1Mzx57YdeQrRQMe4"
ADMIN_IDS = [8442116232, 7705713321, 7962418315]
BOT_NAME = "ዳዊት የመኪና እቁብ"

# Render የሚሰጠንን ዩአርኤል ከ Environment Variables ያገኘዋል
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

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

sold_tickets = {"ሀይሩፍ": set(), "አይሱዙ": set()}

NAME, FATHER_NAME, PHONE_NUM, CHOICE_CAR, TICKET_NUM, RECEIPT, ASK_QUESTION, ADMIN_REPLY = range(8)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 2. KEYBOARDS ---
def user_main_menu():
    kb = [
        [InlineKeyboardButton("🏁 እቁብ ለመግባት", callback_data="buy_ticket")],
        [InlineKeyboardButton("ℹ️ ስለ እቁቡ መረጃ", callback_data="bot_info")],
        [InlineKeyboardButton("❓ አድሚንን ጠይቅ", callback_data="ask_admin")]
    ]
    return InlineKeyboardMarkup(kb)

def back_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ወደ ኋላ ተመለስ", callback_data="go_back")]])

# --- 3. HANDLERS ---
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
    await update.message.reply_text("🎯 ምዝገባዎ ተጠናቋል። የሚፈልጉትን አገልግሎት ከታች ይምረጡ፦", reply_markup=user_main_menu())
    return CHOICE_CAR

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bot_info":
        await query.message.edit_text(f"ℹ️ **ስለ {BOT_NAME}**\n\nይህ ቦት የሀይሩፍ እና የአይሱዙ መኪናዎችን በእጣ የሚያስተላልፍበት ኦፊሴላዊ መድረክ ነው።", reply_markup=back_markup(), parse_mode="Markdown")
        return CHOICE_CAR
    elif query.data == "buy_ticket":
        kb = [[InlineKeyboardButton(f"🚗 ሀይሩፍ ({CARS['ሀይሩፍ']})", callback_data="car_ሀይሩፍ")], [InlineKeyboardButton(f"🚚 አይሱዙ ({CARS['አይሱዙ']})", callback_data="car_አይሱዙ")], [InlineKeyboardButton("⬅️ ተመለስ", callback_data="go_back")]]
        await query.message.edit_text("ለመግባት የሚፈልጉትን የመኪና አይነት ይምረጡ፦", reply_markup=InlineKeyboardMarkup(kb))
        return CHOICE_CAR
    elif query.data.startswith("car_"):
        selected_car = query.data.split("_")[1]
        context.user_data['car'] = selected_car
        await query.message.reply_text(f"🎯 የ **{selected_car}** መኪናን መርጠዋል።\n\nእባክዎ ከ **1 እስከ 1000** ያለ የእጣ ቁጥር ይምረጡና ቁጥሩን ብቻ ይጻፉልኝ፦")
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
    await update.message.reply_text(f"የመረጡት ቁጥር፦ **{ticket_num}**\n\n{PAYMENT_INFO}\n\n⚠️ ክፍያውን ከፈጸሙ በኋላ **የደረሰኝ ፎቶ (Screenshot)** እዚህ ላይ ይላኩ።", parse_mode="Markdown")
    return RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ እባክዎ የደረሰኝ ፎቶ (Screenshot) ብቻ ይላኩ!")
        return RECEIPT
    user = update.effective_user
    u_data = context.user_data
    admin_msg = f"📩 **አዲስ የእቁብ ክፍያ ደረሰኝ ደርሷል!**\n\n👤 ተጠቃሚ: {u_data.get('first_name')} {u_data.get('father_name')}\n📞 ስልክ: {u_data.get('user_phone')}\n🚗 የመኪና አይነት: {u_data.get('car')}\n🎟 የመረጠው ቁጥር: `{u_data.get('ticket')}`\n🆔 User ID: `{user.id}`"
    kb = [[InlineKeyboardButton("✅ አረጋግጥ (Verify)", callback_data=f"verify_{user.id}_{u_data.get('car')}_{u_data.get('ticket')}")], [InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{user.id}")], [InlineKeyboardButton("💬 መልዕክት ለመላክ", callback_data=f"reply_{user.id}")]]
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        except: pass
    await update.message.reply_text("✅ ደረሰኝዎ ለአድሚን ተልኳል! በቅርቡ ተረጋግጦ መልዕክት ይደርስዎታል። እናመሰግናለን!")
    return ConversationHandler.END

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action, target_user_id = data[0], int(data[1])
    if action == "verify":
        car_type, t_num = data[2], int(data[3])
        sold_tickets[car_type].add(t_num)
        await context.bot.send_message(chat_id=target_user_id, text=f"🎉 እንኳን ደስ አለዎት! ክፍያዎ ተረጋግጧል።\n🚗 መኪና፦ {car_type}\n🎟 የእርስዎ እጣ ቁጥር፦ **{t_num}** ነው። መልካም እድል!", parse_mode="Markdown")
        await query.message.edit_caption(caption=query.message.caption + "\n\n🟢 **ሁኔታ፦ ተረጋግጧል ✅**")
    elif action == "reject":
        await context.bot.send_message(chat_id=target_user_id, text="❌ ይቅርታ፣ የላኩት ደረሰኝ ተቀባይነት አላገኘም። እባክዎ እንደገና በትክክል ይላኩ።")
        await query.message.edit_caption(caption=query.message.caption + "\n\n🔴 **ሁኔታ፦ ውድቅ ተደርጓል ❌**")
    elif action == "reply":
        context.application.user_data[query.from_user.id] = target_user_id
        await query.message.reply_text("ለተጠቃሚው የሚላከውን መልዕክት ይጻፉ፦")
        return ADMIN_REPLY

async def send_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    target_id = context.application.user_data.get(admin_id)
    if target_id:
        await context.bot.send_message(chat_id=target_id, text=f"💬 **ከአድሚን የተላከ መልዕክት፦**\n\n{update.message.text}")
        await update.message.reply_text("✅ መልዕክቱ ለተጠቃሚው ደርሷል።")
    return ConversationHandler.END

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"❓ **አዲስ ጥያቄ ከተጠቃሚ ደርሷል!**\n\n
