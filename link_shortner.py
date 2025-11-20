import aiohttp
import asyncio
import logging
from config import AROLINKS_API_KEY, AROLINKS_API_URL
import random
import string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArolinksShortener:
    def __init__(self):
        self.api_key = AROLINKS_API_KEY
        self.base_url = AROLINKS_API_URL

    def generate_verification_token(self, length=8):
        """Generate a random verification token"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    async def create_short_link(self, destination_url: str, custom_alias: str = None) -> dict:
        """Create a short link using Arolinks.com API"""
        params = {
            'api': self.api_key,
            'url': destination_url
        }
        
        if custom_alias:
            params['alias'] = custom_alias

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.error(f"API request failed with status: {response.status}")
                        return {'status': 'error', 'message': 'API request failed'}
                        
        except Exception as e:
            logger.error(f"Error creating short link: {e}")
            return {'status': 'error', 'message': str(e)}

    async def create_verified_download_link(self, file_data: dict, user_id: int) -> dict:
        """Create a verified download link with token verification"""
        
        # Generate verification token
        verification_token = self.generate_verification_token()
        
        # Create verification URL that user will visit
        # This would be your verification service URL
        # For now, we'll create a direct download link but in real implementation,
        # you'd have a web service that verifies the token
        
        # Create a unique alias for the download link
        file_alias = f"pdf_{user_id}_{file_data['file_id'][:8]}_{verification_token}"
        
        # Create the short link
        result = await self.create_short_link(
            destination_url=f"https://t.me/share/url?url={file_data['file_name']}",
            custom_alias=file_alias
        )
        
        if result.get('status') == 'success':
            return {
                'status': 'success',
                'short_url': result['shortenedUrl'],
                'verification_token': verification_token,
                'file_data': file_data
            }
        else:
            return result

class VerificationSystem:
    def __init__(self):
        self.pending_verifications = {}  # user_id -> verification_data
        self.verified_tokens = set()

    def create_verification_session(self, user_id: int, file_data: dict, verification_token: str):
        """Create a new verification session"""
        session_data = {
            'user_id': user_id,
            'file_data': file_data,
            'verification_token': verification_token,
            'created_at': asyncio.get_event_loop().time(),
            'attempts': 0
        }
        self.pending_verifications[user_id] = session_data
        return session_data

    def verify_token(self, user_id: int, token: str) -> bool:
        """Verify if the provided token is correct"""
        if user_id not in self.pending_verifications:
            return False
            
        session = self.pending_verifications[user_id]
        
        # Check if token matches and not expired
        if (token.upper() == session['verification_token'] and
            self.is_session_valid(session)):
            
            # Mark as verified
            self.verified_tokens.add(token)
            return True
            
        session['attempts'] += 1
        return False

    def is_session_valid(self, session: dict) -> bool:
        """Check if verification session is still valid"""
        from config import VERIFICATION_TIMEOUT
        current_time = asyncio.get_event_loop().time()
        return (current_time - session['created_at']) < VERIFICATION_TIMEOUT

    def get_verified_file(self, user_id: int, token: str) -> dict:
        """Get file data for verified token"""
        if self.verify_token(user_id, token):
            file_data = self.pending_verifications[user_id]['file_data']
            # Clean up
            self.cleanup_session(user_id)
            return file_data
        return None

    def cleanup_session(self, user_id: int):
        """Clean up verification session"""
        if user_id in self.pending_verifications:
            token = self.pending_verifications[user_id]['verification_token']
            if token in self.verified_tokens:
                self.verified_tokens.remove(token)
            del self.pending_verifications[user_id]

    def cleanup_expired_sessions(self):
        """Clean up expired verification sessions"""
        current_time = asyncio.get_event_loop().time()
        expired_users = []
        
        for user_id, session in self.pending_verifications.items():
            if not self.is_session_valid(session):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            self.cleanup_session(user_id)

# Global instances
shortener = ArolinksShortener()
verification_system = VerificationSystem()
