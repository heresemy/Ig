import os
import requests
import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ======================= CONFIGURATION =======================
BOT_TOKEN = "8039357378:AAEzzRYW7DZsDSm16EY2mJ8TExW3RpZMC_c"
API_URL = "https://r-gengpt-api.vercel.app/api/video/download"

# ============ CHANNELS ============
CHANNELS = [
    {
        "id": "-1003849265448", 
        "link": "https://t.me/SEMY_FF",
        "name": "🔥 𝐉𝐎𝐈𝐍"
    },
    {
        "id": "-1003885062938", 
        "link": "https://t.me/+n0W7fc-r35JjNDRl",
        "name": "📢 𝐉𝐎𝐈𝐍 "
    }
]

# ============ OWNER ============
OWNER_IDS = [7326248826]  # Replace with your Telegram ID

# ============ VERIFIED USERS FILE ============
VERIFIED_FILE = "verified_users.json"

# ======================= LOGGING =======================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ======================= VERIFIED USERS MANAGEMENT =======================
def load_verified_users():
    """Load verified users from file"""
    try:
        if os.path.exists(VERIFIED_FILE):
            with open(VERIFIED_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_verified_users(users):
    """Save verified users to file"""
    try:
        with open(VERIFIED_FILE, 'w') as f:
            json.dump(users, f)
    except Exception as e:
        logger.error(f"Error saving verified users: {e}")

def add_verified(user_id):
    """Add user to verified list"""
    users = load_verified_users()
    users[str(user_id)] = True
    save_verified_users(users)

def remove_verified(user_id):
    """Remove user from verified list"""
    users = load_verified_users()
    if str(user_id) in users:
        del users[str(user_id)]
        save_verified_users(users)

def is_verified(user_id):
    """Check if user is verified"""
    users = load_verified_users()
    return str(user_id) in users

# ======================= HELPERS =======================
def fetch_instagram_video(url: str):
    """Call the API to get Instagram video download URL."""
    try:
        response = requests.get(API_URL, params={"url": url}, timeout=15)
        response.raise_for_status()
        data = response.json()
        logger.info(f"API Response: {data}")

        if data.get("status") == "success" and data.get("data", {}).get("medias"):
            medias = data["data"]["medias"]
            for media in medias:
                if media.get("type") == "video":
                    return media.get("url"), data["data"].get("title")
            # fallback: try first media
            video_url = medias[0].get("url")
            return video_url, data["data"].get("title", "Instagram Video")
        return None, None
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        return None, None

def is_instagram_url(text: str) -> bool:
    """Check if text contains Instagram URL."""
    return "instagram.com" in text or "instagr.am" in text

# ======================= FORCE JOIN FUNCTIONS =======================
async def check_user_joined(user_id, context):
    """Check if user has joined all channels"""
    try:
        for channel in CHANNELS:
            try:
                member = await context.bot.get_chat_member(
                    chat_id=channel["id"], 
                    user_id=user_id
                )
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.error(f"Error checking channel {channel['id']}: {e}")
                return False
        return True
    except:
        return False

async def show_join_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show join channels message with horizontal buttons"""
    keyboard = []
    
    # Channel buttons in horizontal rows (2 per row)
    row = []
    for i, channel in enumerate(CHANNELS):
        row.append(InlineKeyboardButton(
            channel["name"], 
            url=channel["link"]
        ))
        if len(row) == 2 or i == len(CHANNELS) - 1:
            keyboard.append(row)
            row = []
    
    # Verify button (full width)
    keyboard.append([InlineKeyboardButton(
        "✅ ᴠᴇʀɪꜰʏ", 
        callback_data="verify"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "🔒 *ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟꜱ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ!*\n\n"
        "📌 *ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ʙᴇʟᴏᴡ:*\n"
    )
    
    for channel in CHANNELS:
        message_text += f"• {channel['name']}\n"
    
    message_text += "\n⏳ *ᴀꜰᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴠᴇʀɪꜰʏ ʙᴜᴛᴛᴏɴ*"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ======================= BOT HANDLERS =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message or force join."""
    user_id = update.effective_user.id
    
    # Check if user is verified
    if is_verified(user_id):
        # Check if still joined
        joined = await check_user_joined(user_id, context)
        if joined:
            await show_welcome(update, context)
            return
        else:
            # User left channel, remove verification
            remove_verified(user_id)
            await show_join_channels(update, context)
            return
    
    # Not verified - show join channels
    await show_join_channels(update, context)

async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show welcome message after verification"""
    message_text = (
        "🎬 *Instagram Video Downloader*\n\n"
        "Send me any Instagram Reel/Post link and I'll give you the video!\n\n"
        "Example: `https://www.instagram.com/reel/xyz/`\n\n"
        "✅ *You are verified!*"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            message_text,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message_text,
            parse_mode="Markdown"
        )

async def handle_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify button callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Show verifying status
    await query.message.edit_text(
        "⏳ *ᴠᴇʀɪꜰʏɪɴɢ...*",
        parse_mode="Markdown"
    )
    
    joined = await check_user_joined(user_id, context)
    
    if joined:
        add_verified(user_id)
        await query.message.delete()
        await show_welcome(update, context)
    else:
        await query.message.edit_text(
            "❌ *ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ꜰᴀɪʟᴇᴅ!*\n\n"
            "ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ʏᴇᴛ.\n\n"
            "ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ᴀɴᴅ ᴄʟɪᴄᴋ ᴠᴇʀɪꜰʏ ᴀɢᴀɪɴ.",
            parse_mode="Markdown"
        )
        # Show join channels again
        await show_join_channels(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages containing Instagram links."""
    user_id = update.effective_user.id
    
    # Check verification
    if not is_verified(user_id):
        # Check if joined
        joined = await check_user_joined(user_id, context)
        if joined:
            add_verified(user_id)
        else:
            await show_join_channels(update, context)
            return
    
    text = update.message.text
    if not is_instagram_url(text):
        await update.message.reply_text("⚠️ Please send a valid Instagram URL.")
        return

    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Fetching video... Please wait.")

    # Extract URL (just send the whole text, API handles it)
    video_url, title = fetch_instagram_video(text)

    if video_url:
        # Send video
        try:
            await update.message.reply_video(
                video=video_url,
                caption=f"🎥 {title or 'Instagram Video'}\n\n⬇️ [Download](${video_url})",
                parse_mode="Markdown",
                supports_streaming=True
            )
            await processing_msg.delete()
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await processing_msg.edit_text(
                "❌ Failed to send video. Try sending the link again or use /start."
            )
    else:
        await processing_msg.edit_text(
            "❌ Could not fetch video. Make sure the link is public and try again.\n"
            "If the issue persists, try using a different link."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command."""
    await update.message.reply_text(
        "📖 *How to use:*\n"
        "1. Copy any Instagram Reel or Post URL\n"
        "2. Paste it here and send\n"
        "3. I'll send you the video!\n\n"
        "⚠️ Note: Only works for public posts.",
        parse_mode="Markdown"
    )

# ======================= OWNER COMMANDS =======================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all verified users (Owner only)"""
    user_id = update.effective_user.id
    
    # Check if owner
    if user_id not in OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    # Check if message provided
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Usage:* `/broadcast Your message here`\n\n"
            "Example: `/broadcast Hello everyone!`",
            parse_mode="Markdown"
        )
        return
    
    # Get message
    broadcast_msg = ' '.join(context.args)
    
    # Load verified users
    users = load_verified_users()
    user_ids = list(users.keys())
    
    if not user_ids:
        await update.message.reply_text("❌ No verified users found.")
        return
    
    # Send confirmation
    status_msg = await update.message.reply_text(
        f"⏳ *Sending broadcast to {len(user_ids)} users...*\n"
        f"Message: {broadcast_msg[:100]}{'...' if len(broadcast_msg) > 100 else ''}",
        parse_mode="Markdown"
    )
    
    # Send to all users
    success_count = 0
    failed_count = 0
    
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *Broadcast Message*\n\n{broadcast_msg}",
                parse_mode="Markdown"
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            failed_count += 1
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)
    
    # Update status message
    await status_msg.edit_text(
        f"✅ *Broadcast Complete*\n\n"
        f"📨 Sent to: {success_count} users\n"
        f"❌ Failed: {failed_count} users\n\n"
        f"📝 Message: {broadcast_msg[:200]}{'...' if len(broadcast_msg) > 200 else ''}",
        parse_mode="Markdown"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (Owner only)"""
    user_id = update.effective_user.id
    
    if user_id not in OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    users = load_verified_users()
    total_users = len(users)
    
    # Get bot info
    bot_info = await context.bot.get_me()
    
    stats_text = (
        f"📊 *Bot Statistics*\n\n"
        f"🤖 Bot: {bot_info.first_name}\n"
        f"🆔 ID: {bot_info.id}\n"
        f"👥 Verified Users: {total_users}\n"
        f"📢 Channels: {len(CHANNELS)}\n"
    )
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def unverify_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove verification for a user (Owner only)"""
    user_id = update.effective_user.id
    
    if user_id not in OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Usage:* `/unverify USER_ID`\n\n"
            "Example: `/unverify 123456789`",
            parse_mode="Markdown"
        )
        return
    
    target_id = context.args[0]
    
    if not target_id.isdigit():
        await update.message.reply_text("❌ Please provide a valid user ID.")
        return
    
    target_id = int(target_id)
    
    if is_verified(target_id):
        remove_verified(target_id)
        await update.message.reply_text(
            f"✅ User `{target_id}` has been unverified.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ User `{target_id}` is not verified.",
            parse_mode="Markdown"
        )

# ======================= MAIN =======================
def main():
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        logger.error("Please set BOT_TOKEN environment variable or replace in code.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("unverify", unverify_user))
    app.add_handler(CallbackQueryHandler(handle_verify, pattern="verify"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()