# -*- coding: utf-8 -*-
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from talentscope.config import MongoConfig
import logging

logger = logging.getLogger("talentscope.mongo")

class MatchMongoClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()

    def _connect(self):
        try:
            self.client = MongoClient(MongoConfig.URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[MongoConfig.DB_NAME]
            self.collection = self.db[MongoConfig.COLLECTION_MATCHES]
            # Trigger a connection attempt to check availability
            # self.client.admin.command('ping') 
            logger.info("MongoDB client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB client: {e}")
            self.client = None

    def insert_match_results(self, documents: list) -> bool:
        """
        Inserts a list of match result documents into MongoDB.
        """
        if not self.collection:
            self._connect()
            
        if not self.collection:
            logger.warning("MongoDB collection not available. Skipping insert.")
            return False
            
        if not documents:
            return True

        try:
            result = self.collection.insert_many(documents)
            logger.info(f"Inserted {len(result.inserted_ids)} match records into MongoDB.")
            return True
        except PyMongoError as e:
            logger.error(f"MongoDB Insert Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected MongoDB Error: {e}")
            return False

# Global instance
mongo_client = MatchMongoClient()
