import json
import os
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class FirebaseAuth:
    """Firebase Authentication integration for FlowLogic RouteAI"""
    
    def __init__(self):
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
                return
            
            # Initialize from service account file
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized with service account file")
                return
            
            # Initialize from environment variable JSON
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                service_account_info = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_info)
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized with service account JSON")
                return
            
            # Initialize with default credentials (for Google Cloud environments)
            try:
                cred = credentials.ApplicationDefault()
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized with application default credentials")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize with default credentials: {e}")
            
            # Fallback: mock mode for development
            if os.getenv("ENVIRONMENT") == "development":
                logger.warning("Firebase running in mock mode for development")
                self.app = None
                return
            
            raise Exception("No valid Firebase configuration found")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            if os.getenv("ENVIRONMENT") != "development":
                raise
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user claims"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            # Mock verification for development
            return self._mock_verify_token(id_token)
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information
            user_claims = {
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "phone_number": decoded_token.get("phone_number"),
                "firebase_claims": decoded_token
            }
            
            logger.info(f"Token verified for user: {user_claims['email']}")
            return user_claims
            
        except auth.InvalidIdTokenError as e:
            logger.error(f"Invalid Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        except auth.ExpiredIdTokenError as e:
            logger.error(f"Expired Firebase token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    def _mock_verify_token(self, id_token: str) -> Dict[str, Any]:
        """Mock token verification for development"""
        if not id_token or id_token == "invalid":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # Return mock user data for development
        mock_users = {
            "dev_user_1": {
                "uid": "dev_firebase_uid_1",
                "email": "developer@flowlogic.ai",
                "email_verified": True,
                "name": "Development User",
                "picture": None,
                "phone_number": None,
                "firebase_claims": {
                    "uid": "dev_firebase_uid_1",
                    "email": "developer@flowlogic.ai",
                    "iss": "mock",
                    "aud": "flowlogic-routeai",
                    "exp": 9999999999,
                    "iat": 1700000000
                }
            },
            "admin_user": {
                "uid": "admin_firebase_uid",
                "email": "admin@flowlogic.ai",
                "email_verified": True,
                "name": "Admin User",
                "picture": None,
                "phone_number": None,
                "firebase_claims": {
                    "uid": "admin_firebase_uid",
                    "email": "admin@flowlogic.ai",
                    "iss": "mock",
                    "aud": "flowlogic-routeai",
                    "exp": 9999999999,
                    "iat": 1700000000,
                    "admin": True
                }
            }
        }
        
        return mock_users.get(id_token, mock_users["dev_user_1"])
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user information from Firebase"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            return self._mock_get_user(uid)
        
        try:
            user_record = auth.get_user(uid)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
                "display_name": user_record.display_name,
                "phone_number": user_record.phone_number,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled,
                "metadata": {
                    "creation_timestamp": user_record.user_metadata.creation_timestamp,
                    "last_sign_in_timestamp": user_record.user_metadata.last_sign_in_timestamp,
                },
                "custom_claims": user_record.custom_claims or {},
            }
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get Firebase user {uid}: {e}")
            return None
    
    def _mock_get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Mock get user for development"""
        mock_users = {
            "dev_firebase_uid_1": {
                "uid": "dev_firebase_uid_1",
                "email": "developer@flowlogic.ai",
                "email_verified": True,
                "display_name": "Development User",
                "phone_number": None,
                "photo_url": None,
                "disabled": False,
                "metadata": {
                    "creation_timestamp": 1700000000,
                    "last_sign_in_timestamp": 1700000000,
                },
                "custom_claims": {},
            },
            "admin_firebase_uid": {
                "uid": "admin_firebase_uid",
                "email": "admin@flowlogic.ai",
                "email_verified": True,
                "display_name": "Admin User",
                "phone_number": None,
                "photo_url": None,
                "disabled": False,
                "metadata": {
                    "creation_timestamp": 1700000000,
                    "last_sign_in_timestamp": 1700000000,
                },
                "custom_claims": {"admin": True},
            }
        }
        
        return mock_users.get(uid)
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for a user"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            logger.info(f"Mock: Setting custom claims for {uid}: {claims}")
            return True
        
        try:
            auth.set_custom_user_claims(uid, claims)
            logger.info(f"Custom claims set for user {uid}: {claims}")
            return True
        except Exception as e:
            logger.error(f"Failed to set custom claims for {uid}: {e}")
            return False
    
    async def create_custom_token(self, uid: str, additional_claims: Dict[str, Any] = None) -> str:
        """Create a custom token for a user"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            return f"mock_custom_token_{uid}"
        
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to create custom token for {uid}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication token"
            )
    
    async def delete_user(self, uid: str) -> bool:
        """Delete a user from Firebase"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            logger.info(f"Mock: Deleting user {uid}")
            return True
        
        try:
            auth.delete_user(uid)
            logger.info(f"User deleted from Firebase: {uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user {uid}: {e}")
            return False
    
    async def update_user(self, uid: str, **kwargs) -> bool:
        """Update user information in Firebase"""
        if not self.app and os.getenv("ENVIRONMENT") == "development":
            logger.info(f"Mock: Updating user {uid} with {kwargs}")
            return True
        
        try:
            auth.update_user(uid, **kwargs)
            logger.info(f"User updated in Firebase: {uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user {uid}: {e}")
            return False


# Global Firebase Auth instance
firebase_auth = FirebaseAuth()


# Utility functions
async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """Convenience function to verify Firebase token"""
    return await firebase_auth.verify_token(id_token)


async def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get Firebase user"""
    return await firebase_auth.get_user(uid)