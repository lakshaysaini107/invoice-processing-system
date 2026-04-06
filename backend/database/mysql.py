import re
import ssl
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse

import aiomysql

from backend.app.config import settings
from backend.core.logging import logger


class MySQLClient:
    """MySQL async client wrapper."""

    pool: Optional[aiomysql.Pool] = None

    @classmethod
    def _raise_helpful_mysql_error(cls, exc: Exception, conn_kwargs: Dict[str, Any]):
        code = exc.args[0] if getattr(exc, "args", None) else None
        if code == 1045:
            password_present = bool(conn_kwargs.get("password"))
            raise RuntimeError(
                "MySQL authentication failed (error 1045). "
                f"user={conn_kwargs.get('user')} host={conn_kwargs.get('host')} "
                f"password={'set' if password_present else 'empty'}. "
                "Set MYSQL_PASSWORD (or MYSQL_URL) in .env, then restart Streamlit."
            ) from exc
        raise exc

    @classmethod
    def _connection_kwargs(cls) -> Dict[str, Any]:
        ssl_mode = (getattr(settings, "MYSQL_SSL_MODE", "") or "").strip()
        if settings.MYSQL_URL:
            parsed = urlparse(settings.MYSQL_URL)
            if parsed.scheme not in {"mysql", "mysql+pymysql"}:
                raise ValueError("MYSQL_URL must use mysql:// or mysql+pymysql:// scheme")
            database = parsed.path.lstrip("/")
            if not database:
                raise ValueError("MYSQL_URL must include a database name")
            query = parse_qs(parsed.query)
            ssl_mode = (
                ssl_mode
                or (query.get("ssl-mode") or query.get("ssl_mode") or [""])[0]
            )
            return {
                "host": parsed.hostname or settings.MYSQL_HOST,
                "port": parsed.port or settings.MYSQL_PORT,
                "user": unquote(parsed.username or settings.MYSQL_USER),
                "password": unquote(parsed.password or settings.MYSQL_PASSWORD),
                "db": database,
                **cls._ssl_kwargs(ssl_mode),
            }
        return {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "user": settings.MYSQL_USER,
            "password": settings.MYSQL_PASSWORD,
            "db": settings.MYSQL_DATABASE,
            **cls._ssl_kwargs(ssl_mode),
        }

    @classmethod
    def _ssl_kwargs(cls, ssl_mode: str) -> Dict[str, Any]:
        normalized = (ssl_mode or "").strip().lower().replace("-", "_")
        if not normalized or normalized in {"disabled", "disable", "off", "false", "0"}:
            return {}

        context = ssl.create_default_context()

        # Match MySQL's ssl-mode semantics closely enough for managed services.
        if normalized in {"required", "preferred"}:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif normalized == "verify_ca":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
        elif normalized == "verify_identity":
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            raise ValueError(
                "MYSQL_SSL_MODE must be one of: disabled, preferred, required, "
                "verify_ca, verify_identity"
            )

        return {"ssl": context}

    @classmethod
    def _validate_database_name(cls, database: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_]+", database):
            raise ValueError(
                "MySQL database name must contain only letters, numbers, and underscores"
            )
        return database

    @classmethod
    async def _ensure_database_exists(cls, conn_kwargs: Dict[str, Any]):
        db_name = cls._validate_database_name(str(conn_kwargs["db"]))
        bootstrap_kwargs = dict(conn_kwargs)
        bootstrap_kwargs.pop("db", None)
        try:
            conn = await aiomysql.connect(autocommit=True, **bootstrap_kwargs)
        except Exception as exc:
            cls._raise_helpful_mysql_error(exc, bootstrap_kwargs)
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            conn.close()

    @classmethod
    async def connect_mysql(cls):
        """Connect to MySQL and ensure required tables exist."""
        if cls.pool is not None:
            return

        conn_kwargs = cls._connection_kwargs()
        await cls._ensure_database_exists(conn_kwargs)
        try:
            cls.pool = await aiomysql.create_pool(
                minsize=settings.MYSQL_MIN_POOL_SIZE,
                maxsize=settings.MYSQL_MAX_POOL_SIZE,
                autocommit=True,
                cursorclass=aiomysql.DictCursor,
                **conn_kwargs,
            )
        except Exception as exc:
            cls._raise_helpful_mysql_error(exc, conn_kwargs)
        await cls.initialize_schema()
        logger.info(
            "Connected to MySQL: host=%s port=%s db=%s",
            conn_kwargs["host"],
            conn_kwargs["port"],
            conn_kwargs["db"],
        )

    @classmethod
    async def close_mysql(cls):
        """Close MySQL connection pool."""
        if cls.pool is None:
            return
        cls.pool.close()
        await cls.pool.wait_closed()
        cls.pool = None
        logger.info("Closed MySQL connection pool")

    @classmethod
    def get_pool(cls) -> aiomysql.Pool:
        """Get active MySQL pool."""
        if cls.pool is None:
            raise RuntimeError("MySQL not connected. Call connect_mysql() first.")
        return cls.pool

    @classmethod
    async def initialize_schema(cls):
        """Create required tables if they do not already exist."""
        pool = cls.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(64) PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        company VARCHAR(255) NULL,
                        role VARCHAR(32) NOT NULL DEFAULT 'user',
                        is_active TINYINT(1) NOT NULL DEFAULT 1,
                        is_verified TINYINT(1) NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        last_login DATETIME NULL,
                        notifications_enabled TINYINT(1) NOT NULL DEFAULT 1,
                        theme VARCHAR(20) NOT NULL DEFAULT 'light'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id VARCHAR(64) PRIMARY KEY,
                        user_id VARCHAR(64) NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size BIGINT NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
                        upload_time DATETIME NOT NULL,
                        processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        review_status VARCHAR(50) NULL,
                        progress INT NOT NULL DEFAULT 0,
                        current_step VARCHAR(100) NULL,
                        step_description TEXT NULL,
                        started_at DATETIME NULL,
                        completed_at DATETIME NULL,
                        error_message TEXT NULL,
                        extracted_data LONGTEXT NULL,
                        confidence_scores LONGTEXT NULL,
                        ocr_result LONGTEXT NULL,
                        layout_info LONGTEXT NULL,
                        entities LONGTEXT NULL,
                        reviewed_by VARCHAR(64) NULL,
                        reviewed_at DATETIME NULL,
                        corrections LONGTEXT NULL,
                        review_notes TEXT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        last_updated DATETIME NULL,
                        INDEX idx_invoices_user_upload (user_id, upload_time),
                        INDEX idx_invoices_user_status (user_id, processing_status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS erp_invoices (
                        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        source_invoice_id VARCHAR(64) NULL,
                        invoice_number VARCHAR(255) NULL,
                        invoice_date DATE NULL,
                        due_date DATE NULL,
                        vendor_name VARCHAR(255) NULL,
                        vendor_gst VARCHAR(20) NULL,
                        vendor_address TEXT NULL,
                        buyer_name VARCHAR(255) NULL,
                        buyer_gst VARCHAR(20) NULL,
                        buyer_address TEXT NULL,
                        invoice_amount DECIMAL(15, 2) NULL,
                        tax_amount DECIMAL(15, 2) NULL,
                        total_amount DECIMAL(15, 2) NULL,
                        tax_rate DECIMAL(7, 2) NULL,
                        currency VARCHAR(16) NULL,
                        payment_terms VARCHAR(255) NULL,
                        purchase_order_number VARCHAR(255) NULL,
                        account_number VARCHAR(64) NULL,
                        account_holder VARCHAR(255) NULL,
                        bank_name VARCHAR(255) NULL,
                        ifsc VARCHAR(16) NULL,
                        branch VARCHAR(255) NULL,
                        notes TEXT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_erp_source_invoice (source_invoice_id),
                        INDEX idx_erp_invoice_number (invoice_number),
                        INDEX idx_erp_vendor_name (vendor_name)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
