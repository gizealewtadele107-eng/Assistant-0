import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# --- 1. Configuration ---
TOKEN = "8717535794:AAFSxkKwjV8G62M7kJZ15GeZmpiRWJ4nJsc"
ADMIN_ID = 7705713321  # የእርስዎ ቴሌግራም ID
BOT_NAME = "ዳዊት የመኪና እቁብ"

# የሽልማት አይነቶች እና ዋጋ
CARS = {
    "ሀይሩፍ": "2,500 ብር",
    "አይሱዙ": "3,000 ብር"
}

# የንግድ ባንክ አካውንት (እዚህ ጋር የራስዎን ቁጥር ያስገቡ)
BANK_INFO = "የንግድ ባንክ (CBE): 1000123456789\nስም: ዳዊት _____"

# Conversation States
CHOOSING_CAR, SENDING_RECEIPT = range(2)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 2. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"ሰላም {user_name} 👋 እንኳን ወደ {BOT_NAME} በደህና መጡ።\n\n"
        "የእጣ ቁጥር ለመግዛት መጀመሪያ የሚፈልጉትን የመኪና አይነት ይምረጡ፦"
    )
    
    keyboard = [
        [InlineKeyboardButton(f"🚗 ሀይሩፍ ({CARS['ሀይሩፍ']})", callback_data="ሀይሩፍ")],
        [InlineKeyboardButton(f"🚚 አይሱዙ ({CARS['አይሱዙ']})", callback_data="አይሱዙ")],
        [InlineKeyboardButton("ℹ️ ስለ እቁቡ መረጃ", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return CHOOSING_CAR

async def car_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    if choice == "info":
        await query.message.reply_text(f"{BOT_NAME} በታማኝነት ለረጅም ጊዜ የቆየ እና በርካታ እድለኞችን የመኪና ባለቤት ያደረገ ድርጅት ነው።")
        return CHOOSING_CAR

    context.user_data['selected_car'] = choice
    price = CARS[choice]
    
    payment_text = (
        f"✅ የ {choice} እቁብን መርጠዋል።\n\n"
        f"ለመመዝገብ የ {price} ክፍያ በታች ባለው አካውንት ይፈጽሙ፦\n\n"
        f"🏦 {BANK_INFO}\n\n"
        "⚠️ ክፍያውን ከፈጸሙ በኋላ የደረሰኝ ፎቶ (Screenshot) እዚህ ላይ ይላኩ።"
    )
    
    await query.message.reply_text(payment_text)
    return SENDING_RECEIPT

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    selected_car = context.user_data.get('selected_car', 'ያልታወቀ')
    
    # ደረሰኙን ለአድሚን መላክ
    admin_msg = (
        f"📩 **አዲስ የክፍያ ደረሰኝ ደርሷል!**\n\n"
        f"👤 ስም: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"username: @{user.username}\n"
        f"🚗 የመረጠው መኪና: {selected_car}\n"
    )
    
    # ፎቶውን ለአድሚን አስተላልፍ
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=admin_msg, parse_mode="Markdown")
    
    # ለተጠቃሚው ማረጋገጫ መስጠት
    await update.message.reply_text(
        "✅ ደረሰኝዎ ደርሶናል። በአጭር ጊዜ ውስጥ አድሚኖቻችን አረጋግጠው የእጣ ቁጥርዎን ይልኩልዎታል። እናመሰግናለን!"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሂደቱ ተቋርጧል። ለመጀመር /start ይበሉ።")
    return ConversationHandler.END

# --- 3. Main ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_CAR: [CallbackQueryHandler(car_choice_handler)],
            SENDING_RECEIPT: [MessageHandler(filters.PHOTO, handle_receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    
    print(f"{BOT_NAME} እየሰራ ነው...")
    app.run_polling()
