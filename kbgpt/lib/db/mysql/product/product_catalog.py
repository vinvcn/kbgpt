from sqlalchemy import Column, DateTime, Integer, String, Text

from kbgpt.lib.db.mysql import Base


class ProductCatalog(Base):
    """product catalog table"""

    __tablename__ = "product_catalog_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(100, collation="utf8mb4_unicode_ci"))
    name = Column(String(256, collation="utf8mb4_unicode_ci"))
    desc = Column(Text(collation="utf8mb4_unicode_ci"))
    url = Column(String(256, collation="utf8mb4_unicode_ci"))
    intent1 = Column(String(100, collation="utf8mb4_unicode_ci"))
    intent2 = Column(String(100, collation="utf8mb4_unicode_ci"))
    intent3 = Column(String(100, collation="utf8mb4_unicode_ci"))
    ext1 = Column(String(256, collation="utf8mb4_unicode_ci"))
    ext2 = Column(String(256, collation="utf8mb4_unicode_ci"))
    ext3 = Column(String(256, collation="utf8mb4_unicode_ci"))
    updated_at = Column(DateTime)
    created_at = Column(DateTime)
