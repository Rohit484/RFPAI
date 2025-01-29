import os 
import dotenv

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')
MONGODB_URL = os.getenv('MONGODB_URL')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
SCRAPER_PSWD_HASH = os.getenv('SCRAPER_PSWD_HASH')
