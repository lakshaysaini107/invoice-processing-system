from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from backend.database.mongodb import MongoDBClient
from backend.models.inoice import Invoice, ProcessingStatus  # Note: file is named inoice.py (typo in original)
from backend.core.logging import logger
from pymongo import ReturnDocument

class InvoiceRepository:
    """Invoice CRUD operations with MongoDB"""
    
    def __init__(self):
        self.db = MongoDBClient.get_db()
        self.collection = self.db.invoices
    
    async def create(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new invoice"""
        try:
            result = await self.collection.insert_one(invoice_data)
            invoice_data["_id"] = result.inserted_id
            logger.info(f"Invoice created: {result.inserted_id}")
            return invoice_data
        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            raise
    
    async def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        try:
            invoice = await self.collection.find_one({"invoice_id": invoice_id})
            return invoice
        except Exception as e:
            logger.error(f"Error getting invoice: {str(e)}")
            raise
    
    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get user's invoices with pagination"""
        try:
            query = {"user_id": user_id}
            if status:
                query["processing_status"] = status
            
            invoices = await self.collection.find(query)\
                .skip(skip)\
                .limit(limit)\
                .sort("upload_time", -1)\
                .to_list(length=limit)
            
            return invoices
        except Exception as e:
            logger.error(f"Error getting user invoices: {str(e)}")
            raise
    
    async def update(self, invoice_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update invoice"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.find_one_and_update(
                {"invoice_id": invoice_id},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
            
            if result:
                logger.info(f"Invoice updated: {invoice_id}")
                return result
            
            raise ValueError(f"Invoice not found: {invoice_id}")
        except Exception as e:
            logger.error(f"Error updating invoice: {str(e)}")
            raise
    
    async def update_status(
        self,
        invoice_id: str,
        status: ProcessingStatus,
        **kwargs
    ) -> Dict[str, Any]:
        """Update processing status"""
        update_data = {
            "processing_status": status.value,
            **kwargs
        }
        return await self.update(invoice_id, update_data)
    
    async def delete(self, invoice_id: str) -> bool:
        """Delete invoice"""
        try:
            result = await self.collection.delete_one({"invoice_id": invoice_id})
            if result.deleted_count:
                logger.info(f"Invoice deleted: {invoice_id}")
                return True
            raise ValueError(f"Invoice not found: {invoice_id}")
        except Exception as e:
            logger.error(f"Error deleting invoice: {str(e)}")
            raise
    
    async def count_by_user(self, user_id: str) -> int:
        """Count user's invoices"""
        try:
            count = await self.collection.count_documents({"user_id": user_id})
            return count
        except Exception as e:
            logger.error(f"Error counting invoices: {str(e)}")
            raise
    
    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user's invoice statistics"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$processing_status",
                    "count": {"$sum": 1}
                }}
            ]
            
            stats = await self.collection.aggregate(pipeline).to_list(None)
            
            return {stat["_id"]: stat["count"] for stat in stats}
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise

