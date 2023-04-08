from typing import List
from langchain.prompts import StringPromptTemplate
from pydantic import BaseModel, validator
from langchain.docstore.document import Document

TEMPLATE = """
Given a question, try to answer it using the content of the file extracts below, and if you cannot answer, or find 
a relevant file, just output "I couldn't find the answer to that question in your files.


If the answer is not contained in the files or if there are no file extracts, respond with "I couldn't find the answer
to that question in your files." If the question is not actually a question, respond with "That's not a valid question.


In the cases where you can find the answer, first give the answer. Then explain how you found the answer from the source or sources,
and use the exact filenames of the source files you mention. Do not make up the names of any other files other than those mentioned
in the files context. Give the answer in markdown format.
Use the following format:

Question: <question>

Files:
<### "filename 1" 
file text>
<### "filename 2"
file text>...

Answer: <answer or "I couldn't find the answer to that question in your files" or "That's not a valid question.">
Question: {question_string}
Files:
{files_strings}
Answer:
"""


class FileQATemplate(StringPromptTemplate, BaseModel):
    """A custom prompt template that takes in the function name as input, and formats the prompt template to provide the source code of the function."""

    @validator("input_variables")
    def validate_input_variables(cls, v):
        """Validate that the input variables are correct."""
        if "question_str" not in v:
            raise ValueError("question_str must be in input_variable.")
        if "documents" not in v:
            raise ValueError("documents must be the in input_variable.")
        return v

    def format(self, **kwargs) -> str:
        docs: List[Document] = kwargs["documents"]

        qestion_str = kwargs["question_str"]

        file_strings = []
        # Generate the prompt to be sent to the language model
        for d in docs:
            file_string = f"###\n\"{d.metadata.get('source')}\"\n{d.page_content}\n"
            file_strings.append(file_string)

        prompt = TEMPLATE.format(
            question_string=qestion_str, files_strings="\n".join(file_strings)
        )
        
        return prompt

    def _prompt_type(self):
        return "file-qa"
