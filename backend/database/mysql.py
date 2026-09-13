import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
import aiomysql
from backend.app.config import settings
from backend.core.logging import logger


class DatabaseManager:
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self.use_sqlite: bool = False
        self.sqlite_db_path: str = "data/invoices_fallback.db"

    async def connect(self):
        if self.use_sqlite or not settings.MYSQL_HOST:
            await self._init_sqlite()
            return

        try:
            db_name = settings.MYSQL_DATABASE or "invoices"
            self.pool = await aiomysql.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=db_name,
                autocommit=True,
                minsize=settings.MYSQL_MIN_POOL_SIZE,
                maxsize=settings.MYSQL_MAX_POOL_SIZE,
                connect_timeout=5,
            )
            logger.info("Successfully connected to MySQL database pool.")
            await self.init_db()
        except Exception as exc:
            logger.warning(f"MySQL connection failed ({exc}). Falling back to SQLite database at {self.sqlite_db_path}.")
            self.use_sqlite = True
            await self._init_sqlite()

    async def _init_sqlite(self):
        os.makedirs(os.path.dirname(self.sqlite_db_path), exist_ok=True)
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_status TEXT DEFAULT 'pending',
            overall_confidence REAL DEFAULT 0.0,
            extracted_data TEXT,
            confidence_scores TEXT,
            ocr_result TEXT,
            layout_info TEXT,
            entities TEXT,
            corrections TEXT,
            review_status TEXT DEFAULT 'unreviewed',
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            review_notes TEXT,
            error_message TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS erp_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_invoice_id TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            due_date TEXT,
            vendor_name TEXT,
            vendor_gst TEXT,
            vendor_address TEXT,
            buyer_name TEXT,
            buyer_gst TEXT,
            buyer_address TEXT,
            invoice_amount REAL,
            tax_amount REAL,
            total_amount REAL,
            tax_rate REAL,
            currency TEXT,
            payment_terms TEXT,
            purchase_order_number TEXT,
            notes TEXT,
            bank_details TEXT,
            line_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        conn.close()
        logger.info("SQLite schema initialized successfully.")

    async def init_db(self):
        if self.use_sqlite:
            await self._init_sqlite()
            return
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(64) PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(128),
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(128),
                    role VARCHAR(32) DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """)

                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id VARCHAR(64) PRIMARY KEY,
                    user_id VARCHAR(64),
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    file_size BIGINT NOT NULL,
                    upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    processing_status VARCHAR(32) DEFAULT 'pending',
                    overall_confidence FLOAT DEFAULT 0.0,
                    extracted_data JSON,
                    confidence_scores JSON,
                    ocr_result JSON,
                    layout_info JSON,
                    entities JSON,
                    corrections JSON,
                    review_status VARCHAR(32) DEFAULT 'unreviewed',
                    reviewed_by VARCHAR(64),
                    reviewed_at DATETIME,
                    review_notes TEXT,
                    error_message TEXT
                );
                """)

                await cursor.execute("""
                CREATE TABLE IF NOT EXISTS erp_invoices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    source_invoice_id VARCHAR(64),
                    invoice_number VARCHAR(128),
                    invoice_date VARCHAR(64),
                    due_date VARCHAR(64),
                    vendor_name VARCHAR(255),
                    vendor_gst VARCHAR(64),
                    vendor_address TEXT,
                    buyer_name VARCHAR(255),
                    buyer_gst VARCHAR(64),
                    buyer_address TEXT,
                    invoice_amount DECIMAL(15,2),
                    tax_amount DECIMAL(15,2),
                    total_amount DECIMAL(15,2),
                    tax_rate DECIMAL(5,2),
                    currency VARCHAR(16),
                    payment_terms VARCHAR(128),
                    purchase_order_number VARCHAR(128),
                    notes TEXT,
                    bank_details JSON,
                    line_items JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """)
        logger.info("MySQL database tables verified/created.")

    async def disconnect(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def execute_query(self, query: str, args: tuple = ()) -> List[Dict[str, Any]]:
        if self.use_sqlite:
            return await asyncio.to_thread(self._sqlite_execute, query, args)

        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, args)
                    if cursor.description:
                        rows = await cursor.fetchall()
                        return [dict(r) for r in rows]
                    return []
        except Exception as exc:
            logger.error(f"Query execution error: {exc}. Retrying on SQLite fallback...")
            return await asyncio.to_thread(self._sqlite_execute, query, args)

    def _sqlite_execute(self, query: str, args: tuple = ()) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Replace MySQL specific syntax for SQLite compatibility
        query_sql = query.replace("%s", "?")
        cursor.execute(query_sql, args)
        
        if query_sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            conn.commit()
            lastrowid = cursor.lastrowid
            conn.close()
            return [{"lastrowid": lastrowid}]
            
        rows = cursor.fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return result


db_manager = DatabaseManager()
