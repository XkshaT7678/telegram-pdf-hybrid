import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BACKUP_CHANNEL_ID = os.getenv('BACKUP_CHANNEL_ID')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')

# Arolinks.com Configuration
AROLINKS_API_KEY = os.getenv('AROLINKS_API_KEY', '5055b2359bd39f316c468acefd9553ebae5f3e6f')
AROLINKS_API_URL = "https://arolinks.com/api"

# Bot Settings
MAX_RESULTS = 50
RESULTS_PER_PAGE = 10
VERIFICATION_TIMEOUT = 300  # 5 minutes for verification
MAX_DOWNLOAD_ATTEMPTS = 3
