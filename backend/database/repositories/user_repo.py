from typing import Optional, Dict, Any
from datetime import datetime
from backend.database.mongodb import MongoDBClient
from backend.core.logging import logger
from pymongo import ReturnDocument

class UserRepository:
    """User CRUD operations with MongoDB"""
    
    def __init__(self):
        self.db = MongoDBClient.get_db()
        self.collection = self.db.users
    
    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user"""
        try:
            result = await self.collection.insert_one(user_data)
            user_data["_id"] = result.inserted_id
            logger.info(f"User created: {result.inserted_id}")
            return user_data
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            user = await self.collection.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise
    
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            from bson import ObjectId
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        try:
            from bson import ObjectId
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
            
            if result:
                logger.info(f"User updated: {user_id}")
                return result
            
            raise ValueError(f"User not found: {user_id}")
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        try:
            from bson import ObjectId
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count:
                logger.info(f"User deleted: {user_id}")
                return True
            raise ValueError(f"User not found: {user_id}")
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise
    
    async def update_last_login(self, user_id: str) -> Dict[str, Any]:
        """Update user's last login timestamp"""
        try:
            from bson import ObjectId
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": {"last_login": datetime.utcnow()}},
                return_document=ReturnDocument.AFTER
            )
            return result
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            raise
