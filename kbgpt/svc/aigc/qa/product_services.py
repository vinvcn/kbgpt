import csv
from typing import List

from kbgpt.lib.db.mysql import Crud
from kbgpt.lib.db.mysql.product.product_catalog import ProductCatalog, ProductIntent
from kbgpt.lib.indexing.indexer import CsvColumnIndexer


class ProductImportService:
    """product import service"""

    def __init__(self, crud: Crud) -> None:
        self.crud = crud

    async def csv_to_mysql(self, paths: List[str]):
        self.crud.truncate_table(ProductCatalog.__tablename__)
        self.crud.truncate_table(ProductIntent.__tablename__)
        intents = set()
        products = set()
        for p in paths:
            with open(p, "r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    intents.add(ProductIntent.create_from_row(row))
                    products.add(ProductCatalog.create_from_row(row))

        self.crud.batch_insert(list(intents) + list(products))

    async def csv_to_redis(self, paths: List[str], **kwargs):
        indexer = CsvColumnIndexer()
        return await indexer.transactional_add_to_index(
            paths=paths, column="option_name", **kwargs
        )
