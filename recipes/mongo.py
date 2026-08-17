import os
import logging
from datetime import datetime, timezone
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from dotenv import load_dotenv
import certifi

logger = logging.getLogger(__name__)

# Fallback URI string
DEFAULT_MONGODB_URI = "mongodb+srv://rajuhakki21_db_user:NcvPtWkHYMeRUHAR@cluster0.nsvze8d.mongodb.net/?appName=Cluster0"

_mongo_client = None

def reset_mongo_client():
    global _mongo_client
    _mongo_client = None

def get_mongo_client():
    global _mongo_client
    uri = os.getenv('MONGODB_URI') or getattr(settings, 'MONGODB_URI', '') or DEFAULT_MONGODB_URI
    if not uri:
        logger.error("No MONGODB_URI configured.")
        return None

    if _mongo_client is not None:
        try:
            _mongo_client.admin.command('ping')
            return _mongo_client
        except Exception:
            _mongo_client = None

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        client.admin.command('ping')
        _mongo_client = client
        return _mongo_client
    except Exception as e:
        logger.warning(f"MongoClient with certifi failed: {e}. Trying default SSL context...")
        try:
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000
            )
            client.admin.command('ping')
            _mongo_client = client
            return _mongo_client
        except Exception as err:
            logger.error(f"Failed to connect to MongoDB: {err}")
            return None


def get_mongo_db():
    try:
        client = get_mongo_client()
        if client:
            return client['foodyfi_db']
    except Exception as e:
        logger.error(f"Failed to get MongoDB database: {e}")
    return None

def get_users_collection():
    try:
        db = get_mongo_db()
        if db is not None:
            collection = db['users']
            try:
                collection.create_index("email", unique=True)
                collection.create_index("username", unique=True)
            except Exception as e:
                logger.warning(f"Failed to create MongoDB index: {e}")
            return collection
    except Exception as e:
        logger.error(f"Failed to access users collection: {e}")
    return None

def create_user(username, email, password, full_name=""):
    """
    Creates a new user in MongoDB with hashed password.
    Returns (success: bool, result: dict or str)
    """
    clean_email = email.strip().lower()
    clean_username = username.strip()

    try:
        users = get_users_collection()
        if users is None:
            return False, "Unable to connect to MongoDB Atlas. Please check your credentials in .env and IP Whitelist in MongoDB Atlas."

        # Check if user or email already exists
        if users.find_one({"email": clean_email}):
            return False, "An account with this email address already exists."
        
        if users.find_one({"username": clean_username}):
            return False, "This username is already taken."

        hashed_pw = make_password(password)

        user_doc = {
            "username": clean_username,
            "email": clean_email,
            "password": hashed_pw,
            "full_name": full_name.strip(),
            "bio": "",
            "favorite_cuisine": "All Cuisines",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        res = users.insert_one(user_doc)
        user_doc['_id'] = str(res.inserted_id)
        return True, user_doc

    except errors.DuplicateKeyError:
        return False, "Username or email already exists."
    except errors.OperationFailure as e:
        reset_mongo_client()
        logger.error(f"MongoDB Authentication Error: {e}")
        return False, "MongoDB Authentication failed ('bad auth'). Please check your database user password in .env and Database Access settings in MongoDB Atlas."

    except errors.ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB Server Selection Timeout: {e}")
        return False, "MongoDB connection timed out. Please ensure your IP address is whitelisted in MongoDB Atlas Network Access."
    except errors.PyMongoError as e:
        logger.error(f"MongoDB Error in create_user: {e}")
        return False, f"Database error: {str(e)}"

    except Exception as e:
        logger.error(f"Error inserting user into MongoDB: {e}")
        return False, f"Failed to save user: {str(e)}"

def get_user_by_email(email):
    try:
        users = get_users_collection()
        if users is not None:
            doc = users.find_one({"email": email.strip().lower()})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
    return None

def get_user_by_username(username):
    try:
        users = get_users_collection()
        if users is not None:
            doc = users.find_one({"username": username.strip()})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
    except Exception as e:
        logger.error(f"Error fetching user by username: {e}")
    return None

def get_user_by_id(user_id_str):
    try:
        users = get_users_collection()
        if users is not None:
            doc = users.find_one({"_id": ObjectId(user_id_str)})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
    except Exception as e:
        logger.error(f"Error fetching user by ID: {e}")
    return None

def verify_user(identifier, raw_password):
    """
    Verifies user by email or username and password.
    Returns (user_doc, error_message)
    """
    clean_identifier = identifier.strip()
    if not clean_identifier:
        return None, "Please provide your username or email."

    try:
        user_doc = get_user_by_email(clean_identifier)
        if not user_doc:
            user_doc = get_user_by_username(clean_identifier)

        if not user_doc:
            return None, "No account found with those credentials (or unable to connect to database)."

        if check_password(raw_password, user_doc['password']):
            return user_doc, None
        else:
            return None, "Invalid password. Please try again."
    except errors.OperationFailure:
        return None, "MongoDB authentication failed ('bad auth'). Please check your database user password in .env."
    except errors.ServerSelectionTimeoutError:
        return None, "MongoDB connection timed out. Please check your IP Whitelist in MongoDB Atlas."
    except Exception as e:
        logger.error(f"Error during verify_user: {e}")
        return None, "Database connection error. Please verify your MongoDB configuration."


def update_user_profile(username, full_name, bio, favorite_cuisine):
    """
    Updates user profile data in MongoDB.
    """
    try:
        users = get_users_collection()
        if users is None:
            return False, "Database connection unavailable."

        result = users.update_one(
            {"username": username.strip()},
            {"$set": {
                "full_name": full_name.strip(),
                "bio": bio.strip(),
                "favorite_cuisine": favorite_cuisine.strip(),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        if result.matched_count > 0:
            return True, "Profile updated successfully."
        return False, "User profile not found."
    except errors.ServerSelectionTimeoutError:
        return False, "MongoDB connection timed out."
    except Exception as e:
        return False, f"Failed to update profile: {str(e)}"
