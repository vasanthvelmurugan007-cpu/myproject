import sys
import os

# Add your project directory to the sys.path
path = '/home/vasanthvelmurugan007/myproject'
if path not in sys.path:
    sys.path.append(path)

# Set the Gemini API key environment variable for the script
os.environ['GEMINI_API_KEY'] = 'AIzaSyB5B4BsCOU53XBAksJwfs3nuiEjFUFvDQ8'

# Import your Flask app (assumes app = Flask(__name__) is in app.py)
from app import app as application
