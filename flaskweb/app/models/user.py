from app.create_app import mongo
from pymongo.errors import PyMongoError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from bson.objectid import ObjectId

ph = PasswordHasher()

class User:

    ph = ph

    @staticmethod
    def create(firstname, lastname, email, organization, password):
        try:
            hashed_password = ph.hash(password)
            user_id = mongo.db.users.insert_one(
                {
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "organization": organization,
                    "password": hashed_password,
                    "role": "user",
                    "confirmed": False,
                }
            ).inserted_id
            return user_id
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def exists(email):
        try:
            return mongo.db.users.find_one({"email": email}) is not None
        except Exception as e:
            print(f"Error: {e}")
            return False

    @staticmethod
    def create_token(user_id,token):
                try:
                    mongo.db.tokens.insert_one({"user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id, "token": token})
                except Exception as e:
                    print(f"Error creating token: {e}")
                    return None

    @staticmethod
    def find_user(user_id):
                try:
                   return mongo.db.tokens.find_one({"_id": user_id})
                except Exception as e:
                    print(f"Error: {e}")
                    return None

    @staticmethod
    def token_entry(token):
            try:
                found_token_entry = mongo.db.tokens.find_one({"token": token})
                return found_token_entry
            except Exception as e:
                print(f"Error finding token entry: {e}")
                return None

    @staticmethod
    def confirm(user_id):
        try:
            if isinstance(user_id, str):
                user_id_obj = ObjectId(user_id)
            else:
                user_id_obj = user_id
            result = mongo.db.users.update_one({"_id": user_id_obj}, {"$set": {"confirmed": True}})
            return True
        except Exception as e:
            print(f"Error confirming user: {e}")
            return None

    @staticmethod
    def save_api_key(user_id, api_key):
        try:
            result = mongo.db.users.update_one(
                {"_id": user_id}, {"$set": {"api_key": api_key}}
            )
            if result.matched_count == 0:
                print("User ID not found.")
                return False
            elif result.modified_count == 0:
                print(
                    "API Key was not updated. It might be the same as the current value."
                )
            return True
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def verify_password(email, password):
        try:
            user = mongo.db.users.find_one({"email": email})
            if user:
                try:
                    if User.ph.verify(user["password"], password):
                        if user["role"] == "admin":
                            return "admin"
                        elif user["role"] == "user":
                            return "user"
                        elif user["role"] == "member":
                            return "member"
                        else:
                            return False
                except VerifyMismatchError:
                    return False
            return False
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def get_user_by_email(email):
        try:
            return mongo.db.users.find_one({"email": email})
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def check_api_key(api_key):
        return mongo.db.users.find_one({"api_key": api_key})

    @staticmethod
    def name_exists(firstname, lastname, email):
        return (
            mongo.db.users.find_one(
                {
                    "$or": [
                        {"$and": [{"firstname": firstname}, {"lastname": lastname}]},
                        {"email": email},
                    ]
                }
            )
            is not None
        )

    @staticmethod
    def update_status_to_member(user_id):
        try:
            from bson import ObjectId
            result = mongo.db.users.update_one(
                {"_id": ObjectId(user_id)}, {"$set": {"role": "member"}}
            )
            if result.modified_count > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def delete_user_by_id(user_id):
        try:
            result = mongo.db.users.delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    @staticmethod
    def get_all_users():
        try:
            users = mongo.db.users.find({"api_key": {"$nin": ["TNeb2nh7V6PpKwTJshr0bDHjujw7ChVL1-rFamkOiRA", "CpS4kzAOZzaY3Sqld8T_-SdAE6Kjzy5apwa5EV9ew8Y"]}})
            return list(users)
        except Exception as e:
            print(f"Error retrieving all users: {e}")
        return []

    @staticmethod
    def count_users(query=None):
        """Count users (excluding admin API keys)"""
        try:
            base_query = {"api_key": {"$nin": ["TNeb2nh7V6PpKwTJshr0bDHjujw7ChVL1-rFamkOiRA", "CpS4kzAOZzaY3Sqld8T_-SdAE6Kjzy5apwa5EV9ew8Y"]}}
            if query:
                # Merge query with base_query using $and
                combined_query = {"$and": [base_query, query]}
                return mongo.db.users.count_documents(combined_query)
            return mongo.db.users.count_documents(base_query)
        except Exception as e:
            print(f"Error count_users: {e}")
            return 0

    @staticmethod
    def find_users_for_datatable(query, start, length):
        """Find users for DataTables with pagination"""
        try:
            base_query = {"api_key": {"$nin": ["TNeb2nh7V6PpKwTJshr0bDHjujw7ChVL1-rFamkOiRA", "CpS4kzAOZzaY3Sqld8T_-SdAE6Kjzy5apwa5EV9ew8Y"]}}
            
            if query:
                combined_query = {"$and": [base_query, query]}
            else:
                combined_query = base_query
            
            results = list(
                mongo.db.users.find(combined_query)
                .skip(start)
                .limit(length)
            )
            
            # Convert ObjectId to string for JSON serialization
            normalized_results = []
            for result in results:
                normalized_result = {}
                for k, v in result.items():
                    if k == "_id":
                        normalized_result[k] = str(v)
                    elif k == "password":
                        continue  # Don't include password in response
                    else:
                        normalized_result[k] = v
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_users_for_datatable: {e}")
            return []

    @staticmethod
    def get_api(user_id):
        try:
            user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
            if user and "api_key" in user:
                return user["api_key"]
            else:
                return None
        except Exception as e:
            print(f"Error retrieving API key: {e}")
            return None

    @staticmethod
    def reset_password(email, new_password):
        try:
            hashed_password = ph.hash(new_password)
            result = mongo.db.users.update_one(
                {"email": email},
                {
                    "$set": {"password": hashed_password}
                },
            )
            if result.modified_count > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error resetting password: {e}")
        return False