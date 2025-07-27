"""
Database-based trigger management for conversation processing.

This module provides PostgreSQL-based persistent storage for user triggers,
replacing the in-memory UserTriggerManager with a database-backed implementation.
"""

import os
import json
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import time

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages PostgreSQL connection pool for parallel processing."""
    
    def __init__(self, max_connections: int = 10):
        """
        Initialize the connection pool.
        
        Args:
            max_connections: Maximum number of connections in the pool
        """
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=max_connections,
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=int(os.environ.get('POSTGRES_PORT', 5432)),
            database=os.environ.get('POSTGRES_DB', 'triggers'),
            user=os.environ.get('POSTGRES_USER'),
            password=os.environ.get('POSTGRES_PASSWORD')
        )
        logger.info(f"Database connection pool initialized with max {max_connections} connections")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            psycopg2 connection object
        """
        conn = None
        try:
            # print(f"🔒 [{time.strftime('%H:%M:%S')}] Getting connection from pool (available: {self.pool.maxconn - len(self.pool._used)})")
            conn = self.pool.getconn()
            # print(f"🔒 [{time.strftime('%H:%M:%S')}] Got connection from pool (available: {self.pool.maxconn - len(self.pool._used)})")
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                # print(f"🔓 [{time.strftime('%H:%M:%S')}] Returning connection to pool")
                self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in the pool."""
        self.pool.closeall()
        logger.info("All database connections closed")
