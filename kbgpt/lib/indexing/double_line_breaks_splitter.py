import re
from typing import List

import tiktoken
from langchain.text_splitter import TextSplitter


class PondAstonPondSplitter(TextSplitter):
    """
    Split text by double line breaks.
    """

    # create a regex that matches a line break followed by a question mark
    question_regex = re.compile(r"\n.+\?\n")

    def __init__(self, encoding_model: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.seperator = "#!#"
        self.encoding = tiktoken.encoding_for_model(encoding_model)
        self._length_function = lambda text: len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[str]:
        return text.split(self.seperator)
