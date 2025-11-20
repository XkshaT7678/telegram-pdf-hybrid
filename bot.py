import os
import logging
import asyncio
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, BACKUP_CHANNEL_ID, MAX_RESULTS, RESULTS_PER_PAGE
from database import init_database, search_files, get_total_files
from link_shortener import shortener, verification_system

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PDFSearchBot:
    def __init__(self):
        self.application = None

    def clean_filename(self, filename):
        """Clean filename for better search"""
        import re
        name = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        name = re.sub(r'[._-]', ' ', name)
        return name.lower().strip()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message when user sends /start"""
        welcome_text = """
🤖 **Welcome to PDF Search Bot!**

📚 Access 80,000+ study materials with our secure download system.

**How it works:**
1. 🔍 Search for your desired book
2. 📝 Select from the results
3. 🔗 Get a verification link
4. ✅ Complete quick verification
5. 📥 Download your PDF instantly!

**Verification Process:**
- Visit the provided short link
- Complete a quick step (ad verification)
- Get your verification code
- Enter code here to download

🔍 **Examples:**
• `Calculus textbook`
• `Python programming`
• `Physics formulas`

Start by typing your search query!
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        help_text = """
❓ **How to use this bot:**

🔍 **Search:** Type book name, author, or subject
Example: `mathematics` or `python programming`

🔒 **Verification Process:**
1. Select a book from search results
2. Get a short verification link
3. Visit the link and complete verification
4. Receive verification code
5. Enter code here to download

⚡ **Tips:**
- Use specific keywords for better results
- Verification links expire in 5 minutes
- Keep the verification code safe

📞 **Support:** Contact admin for help
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user search queries"""
        query = update.message.text.strip()
        
        if not query:
            await update.message.reply_text("Please enter a search term.")
            return

        if len(query) < 2:
            await update.message.reply_text("Please enter at least 2 characters for search.")
            return

        # Show searching message
        searching_msg = await update.message.reply_text(f"🔍 Searching for: `{query}`...", parse_mode=ParseMode.MARKDOWN)

        try:
            # Search for files
            results = list(search_files(query, MAX_RESULTS))
            
            if not results:
                await searching_msg.edit_text(
                    f"❌ No results found for: `{query}`\n\n"
                    f"💡 Try:\n• Different keywords\n• Partial book names\n• Author names",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Store results in context for pagination
            context.user_data['search_results'] = results
            context.user_data['current_page'] = 0
            context.user_data['search_query'] = query

            # Show first page
            await self.show_results_page(update, context, results, 0, query)
            await searching_msg.delete()

        except Exception as e:
            logger.error(f"Search error: {e}")
            await searching_msg.edit_text("❌ An error occurred while searching. Please try again.")

    async def show_results_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              results: list, page: int, query: str):
        """Show a page of search results"""
        start_idx = page * RESULTS_PER_PAGE
        end_idx = start_idx + RESULTS_PER_PAGE
        page_results = results[start_idx:end_idx]
        
        total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
        
        # Create message text
        message_text = (
            f"🔍 **Search Results for:** `{query}`\n"
            f"📄 **Found {len(results)} files**\n"
            f"📑 **Page {page + 1}/{total_pages}**\n\n"
            f"💡 **Select a file to get verification link**\n\n"
        )

        # Add file list for current page
        for i, file_info in enumerate(page_results, start_idx + 1):
            file_size_mb = file_info.file_size // (1024 * 1024) if file_info.file_size > 0 else 0
            caption_preview = file_info.file_caption[:50] + "..." if file_info.file_caption and len(file_info.file_caption) > 50 else file_info.file_caption
            caption_text = f" - {caption_preview}" if caption_preview else ""
            
            message_text += f"**{i}. {file_info.file_name}** ({file_size_mb}MB){caption_text}\n\n"

        # Create keyboard
        keyboard = []
        
        # File selection buttons (2 per row)
        row = []
        for i, file_info in enumerate(page_results):
            idx = start_idx + i
            button_text = f"📥 {i+1}"
            row.append(InlineKeyboardButton(button_text, callback_data=f"verify_{idx}"))
            
            if len(row) == 2 or i == len(page_results) - 1:
                keyboard.append(row)
                row = []

        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page-1}"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)

        # Always show help button
        keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help_btn")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "help_btn":
            await self.help_command(update, context)
            return

        if data.startswith("page_"):
            # Handle pagination
            page = int(data.split("_")[1])
            results = context.user_data.get('search_results', [])
            search_query = context.user_data.get('search_query', '')
            
            await self.show_results_page(update, context, results, page, search_query)

        elif data.startswith("verify_"):
            # Handle file verification process
            idx = int(data.split("_")[1])
            await self.start_verification_process(update, context, idx)

    async def start_verification_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE, idx: int):
        """Start the verification process for selected file"""
        query = update.callback_query
        results = context.user_data.get('search_results', [])
        
        if not results or idx >= len(results):
            await query.edit_message_text("❌ File not found. Please search again.")
            return

        file_info = results[idx]
        user_id = query.from_user.id
        
        # Prepare file data
        file_data = {
            'file_id': file_info.file_id,
            'file_name': file_info.file_name,
            'file_size': file_info.file_size,
            'message_id': file_info.message_id,
            'file_caption': file_info.file_caption
        }
        
        try:
            # Show generating link message
            await query.edit_message_text(
                f"🔄 **Generating secure download link...**\n\n"
                f"📚 **File:** `{file_info.file_name}`\n"
                f"👤 **User:** {query.from_user.first_name}\n\n"
                f"Please wait...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Create verified download link
            verification_data = await shortener.create_verified_download_link(file_data, user_id)
            
            if verification_data.get('status') != 'success':
                await query.edit_message_text(
                    f"❌ **Error generating link**\n\n"
                    f"Failed to create verification link. Please try again later.\n"
                    f"Error: {verification_data.get('message', 'Unknown error')}",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Store verification session
            verification_system.create_verification_session(
                user_id=user_id,
                file_data=file_data,
                verification_token=verification_data['verification_token']
            )

            # Send verification instructions
            verification_msg = (
                f"🔒 **Verification Required**\n\n"
                f"📚 **File:** `{file_info.file_name}`\n\n"
                f"**Step 1:** Visit this link:\n"
                f"🔗 {verification_data['short_url']}\n\n"
                f"**Step 2:** Complete the verification process\n"
                f"**Step 3:** You'll receive a verification code\n\n"
                f"**Step 4:** Enter the code here like this:\n"
                f"`/verify CODE`\n\n"
                f"⏰ **Link expires in 5 minutes**\n"
                f"🔑 **Your token starts with:** `{verification_data['verification_token'][:3]}...`"
            )

            keyboard = [
                [InlineKeyboardButton("🔄 Generate New Link", callback_data=f"verify_{idx}")],
                [InlineKeyboardButton("❓ Help", callback_data="help_btn")],
                [InlineKeyboardButton("🔍 New Search", switch_inline_query_current_chat="")]
            ]

            await query.edit_message_text(
                verification_msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Verification process error: {e}")
            await query.edit_message_text(
                f"❌ **Verification Error**\n\n"
                f"An error occurred while setting up verification.\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle verification code input"""
        if not context.args:
            await update.message.reply_text(
                "❌ **Usage:** `/verify CODE`\n\n"
                "Enter the verification code you received after completing the ad verification.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        verification_code = context.args[0].upper().strip()
        user_id = update.message.from_user.id

        try:
            # Clean up expired sessions first
            verification_system.cleanup_expired_sessions()

            # Verify the token
            file_data = verification_system.get_verified_file(user_id, verification_code)
            
            if not file_data:
                await update.message.reply_text(
                    "❌ **Invalid or expired verification code!**\n\n"
                    "Possible reasons:\n"
                    "• Code is incorrect\n"
                    "• Code has expired (5 minutes)\n"
                    "• No active verification session\n\n"
                    "Please generate a new verification link and try again.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            # Send the file
            await self.send_verified_file(update, context, file_data)

        except Exception as e:
            logger.error(f"Verification error: {e}")
            await update.message.reply_text(
                "❌ **Verification failed!**\n\n"
                "An error occurred during verification. Please try again.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def send_verified_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_data: dict):
        """Send the verified file to user"""
        try:
            # Send preparing message
            preparing_msg = await update.message.reply_text(
                f"✅ **Verification Successful!**\n\n"
                f"📚 **File:** `{file_data['file_name']}`\n"
                f"⬇️ Preparing your download...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Forward the file from backup channel
            await context.bot.forward_message(
                chat_id=update.message.chat_id,
                from_chat_id=BACKUP_CHANNEL_ID,
                message_id=file_data['message_id']
            )

            # Send success message
            await preparing_msg.edit_text(
                f"🎉 **Download Complete!**\n\n"
                f"📚 **File:** `{file_data['file_name']}`\n"
                f"✅ **Status:** Successfully delivered\n\n"
                f"Thank you for using our service! 📖\n\n"
                f"Want another book? Just type your search query!",
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Error sending verified file: {e}")
            await update.message.reply_text(
                f"❌ **Download Error**\n\n"
                f"Failed to send: `{file_data['file_name']}`\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics"""
        total_files = get_total_files()
        
        stats_text = f"""
📊 **Bot Statistics**

📁 Total Files: {total_files:,}
🔒 Verification: Arolinks.com
⏰ Session Timeout: 5 minutes
💾 Storage: Cloud (Telegram)

💡 **Verification Process:**
1. Search & select file
2. Get short link with ads
3. Complete verification
4. Enter code here
5. Download PDF

**Start by searching for a book!**
        """
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        """Start the bot"""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment variables")
            return

        if not BACKUP_CHANNEL_ID:
            logger.error("BACKUP_CHANNEL_ID not found in environment variables")
            return

        # Initialize database
        init_database()

        # Initialize application
        self.application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("verify", self.verify_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Start the bot
        logger.info("Bot is starting...")
        logger.info(f"Total files in database: {get_total_files()}")
        self.application.run_polling()

if __name__ == '__main__':
    bot = PDFSearchBot()
    bot.run()
