import os
from peewee import *
from playhouse.sqlite_ext import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
db = SqliteDatabase('data/file_index.db')

class PDFFile(Model):
    file_id = CharField(unique=True)
    file_name = CharField(index=True)
    file_size = IntegerField()
    message_id = IntegerField()
    file_caption = TextField(null=True)
    mime_type = CharField(default='application/pdf')
    search_terms = TextField(index=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        database = db

class WebSearchLog(Model):
    query = CharField()
    results_count = IntegerField()
    user_agent = TextField(null=True)
    ip_address = CharField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        database = db

def init_database():
    """Initialize database and create tables"""
    os.makedirs('data', exist_ok=True)
    db.connect()
    db.create_tables([PDFFile, WebSearchLog], safe=True)
    logger.info("Database initialized")

def close_database():
    """Close database connection"""
    db.close()

def search_files(query, limit=50):
    """Search for files matching the query"""
    query = query.lower().strip()
    
    # Search in file_name and search_terms
    return (PDFFile
            .select()
            .where(
                (PDFFile.file_name.contains(query)) |
                (PDFFile.search_terms.contains(query)) &
                (PDFFile.is_active == True)
            )
            .limit(limit)
            .execute())

def get_file_by_id(file_id):
    """Get file by file_id"""
    try:
        return PDFFile.get(PDFFile.file_id == file_id)
    except DoesNotExist:
        return None

def add_file(file_data):
    """Add a file to database"""
    try:
        return PDFFile.create(**file_data)
    except IntegrityError:
        # File already exists, update it
        return PDFFile.update(**file_data).where(PDFFile.file_id == file_data['file_id']).execute()

def get_total_files():
    """Get total number of files in database"""
    return PDFFile.select().where(PDFFile.is_active == True).count()

def search_files_web(query, limit=50, offset=0):
    """Search for files matching the query (for web)"""
    query = query.lower().strip()
    
    # Search in file_name and search_terms
    results = (PDFFile
            .select()
            .where(
                (PDFFile.file_name.contains(query)) |
                (PDFFile.search_terms.contains(query)) &
                (PDFFile.is_active == True)
            )
            .limit(limit)
            .offset(offset)
            .execute())
    
    return list(results)

def get_search_stats():
    """Get search statistics for web"""
    total_files = PDFFile.select().where(PDFFile.is_active == True).count()
    total_size = PDFFile.select(fn.SUM(PDFFile.file_size)).where(PDFFile.is_active == True).scalar() or 0
    
    return {
        'total_files': total_files,
        'total_size_gb': round(total_size / (1024**3), 2),
        'last_updated': PDFFile.select(fn.MAX(PDFFile.created_at)).scalar()
    }

def log_web_search(query, results_count, user_agent=None, ip_address=None):
    """Log web searches for analytics"""
    try:
        WebSearchLog.create(
            query=query,
            results_count=results_count,
            user_agent=user_agent,
            ip_address=ip_address
        )
    except Exception as e:
        logger.error(f"Error logging search: {e}")
