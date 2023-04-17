from typing import List
from langchain.prompts import StringPromptTemplate
from pydantic import BaseModel, validator
from langchain.docstore.document import Document

TEMPLATE = """
你是一个律师，你的客户卷入了法务纠纷，向你做法务咨询，你需要为他提供一些信息，如果你无法从如下法律文件中找到答案，就输出“我无法回答你的问题。”，在回答时你必须遵循律师守则。

法律文件是：
{files_strings}


使用如下格式：
问题： <问题>

答案: <答案 或者 "我无法找到相关法律文件" 或者 "这不是个有效的问题">

问题是：
{question_string}

回答：
"""


class ConsultantQATemplate(StringPromptTemplate, BaseModel):
    """A custom prompt template that takes in the function name as input, and formats the prompt template to provide the source code of the function."""

    @validator("input_variables")
    def validate_input_variables(cls, v):
        """Validate that the input variables are correct."""
        if "question_str" not in v:
            raise ValueError("question_str must be in input_variable.")
        if "documents" not in v:
            raise ValueError("documents must be the in input_variable.")
        if "attoney_guide" not in v:
            raise ValueError("attoney_guide must be the in input_variable.")
        return v

    def format(self, **kwargs) -> str:
        docs: List[Document] = kwargs["documents"]
        guides: List[Document] = kwargs["attoney_guide"]

        qestion_str = kwargs["question_str"]

        file_strings = []
        # Generate the prompt to be sent to the language model
        for i, d in enumerate(docs):
            file_string = f"- {d.page_content} \n"
            file_strings.append(file_string)

        guides_strings = []
        for i, g in enumerate(guides):
            guide_string = f"- {g.page_content} \n"
            guides_strings.append(guide_string)

        prompt = TEMPLATE.format(
            question_string=qestion_str, files_strings="\n".join(file_strings)
        )

        return prompt

    def _prompt_type(self):
        return "file-qa"
