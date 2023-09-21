# Creates a contextual QA robot
from haystack.nodes import PromptNode, PromptTemplate
from haystack import Document


class Summarizer:
    """
    This exists to make it easier to apply the Haystack GA prompt node
    to arbitrary text.
    """

    default_prompt_template = PromptTemplate("./prompts/lfqa.yml")

    def __init__(
        self, model_name_or_path: str = "google/flan-t5-large", prompt_text=None,
    ):
        if prompt_text:
            self.prompt = PromptTemplate(prompt=prompt_text)
        else:
            self.prompt = self.default_prompt_template

        self.prompt_node = PromptNode(
            model_name_or_path=model_name_or_path,
            default_prompt_template=self.prompt,
        )
        return None

    def query_texts(self, query: str, texts: list[str]):
        documents = [Document(content=text, content_type="text") for text in texts]
        results = self.prompt_node.run(documents=documents, query=query)
        return results[0]["results"][0]
