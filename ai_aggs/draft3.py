import csv
from typing import Any


class QA:
    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        return "hi how are you"


class Products:
    def make_json(self, csvFilePath):
        data = {}

        # Open a csv reader called DictReader
        with open(csvFilePath, encoding="utf-8") as csvf:
            csvReader = csv.DictReader(csvf)

            # Convert each row into a dictionary
            # and add it to data
            for rows in csvReader:
                # Assuming a column named 'No' to
                # be the primary key
                key = rows["No"]
                data[key] = rows

        return data

    def __init__(self) -> None:
        pass

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class Chat:
    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass


class Chain:
    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass
