from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from backend.app.config import settings
from backend.core.logging import logger
from pymongo.database import Database


class MongoDBClient:
    """MongoDB async client wrapper"""
    
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[Database] = None
    
    @classmethod
    async def connect_mongodb(cls):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await cls.client.admin.command('ping')
            
            # Get database name from URL or use default
            db_name = settings.MONGODB_URL.split('/')[-1].split('?')[0]
            if not db_name or db_name == settings.MONGODB_URL:
                db_name = "invoice_system"
            
            cls.database = cls.client[db_name]
            logger.info(f"Connected to MongoDB: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def close_mongodb(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")
    
    @classmethod
    def get_db(cls) -> Database:
        """Get database instance"""
        if cls.database is None:
            raise RuntimeError("MongoDB not connected. Call connect_mongodb() first.")
        return cls.database
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get MongoDB client"""
        if cls.client is None:
            raise RuntimeError("MongoDB not connected. Call connect_mongodb() first.")
        return cls.client
