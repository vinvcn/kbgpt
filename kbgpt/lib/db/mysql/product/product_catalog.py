import hashlib
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from kbgpt.lib.db.mysql import Base
from kbgpt.lib.utils import calculate_hash


class ProductCatalog(Base):
    """product catalog table"""

    __tablename__ = "product_catalog_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    module = Column(String(50, collation="utf8mb4_unicode_ci"))
    name = Column(String(256, collation="utf8mb4_unicode_ci"))
    desc = Column(Text(collation="utf8mb4_unicode_ci"))
    uri = Column(String(256, collation="utf8mb4_unicode_ci"))
    ext1 = Column(Text(collation="utf8mb4_unicode_ci"))
    ext2 = Column(Text(collation="utf8mb4_unicode_ci"))
    ext3 = Column(Text(collation="utf8mb4_unicode_ci"))
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow())

    __table_args__ = (UniqueConstraint("product_id", name="uq_product_catalog_record"),)

    @classmethod
    def create_from_row(cls, row):
        obj = cls()
        obj.module = row["module"]
        obj.name = row["function"]
        obj.desc = row["description_long"]
        obj.uri = row["entrance"]
        obj.ext1 = row["button_name"]
        obj.product_id = calculate_hash(f"{obj.module}.{obj.name}")
        return obj


class ProductIntent(Base):
    """product intent record table"""

    __tablename__ = "product_catalog_intent_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    intent = Column(String(1000, collation="utf8mb4_unicode_ci"))
    sha_256_hash = Column(String(100, collation="utf8mb4_unicode_ci"))
    uri = Column(String(500, collation="utf8mb4_unicode_ci"))
    desc = Column(Text(collation="utf8mb4_unicode_ci"))
    ext1 = Column(String(500, collation="utf8mb4_unicode_ci"))
    ext2 = Column(String(500, collation="utf8mb4_unicode_ci"))
    ext3 = Column(String(500, collation="utf8mb4_unicode_ci"))
    priority = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow())

    __table_args__ = (
        UniqueConstraint("sha_256_hash", name="uq_product_catalog_intent_record"),
    )

    @classmethod
    def create_from_row(cls, row):
        obj = cls()
        obj.product_id = calculate_hash(f"{row['module']}.{row['function']}")
        obj.intent = row["option_name"]
        obj.sha_256_hash = calculate_hash(obj.intent)
        return obj
