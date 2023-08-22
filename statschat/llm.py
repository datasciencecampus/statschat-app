# Creates a contextual QA robot
from haystack.nodes import PromptNode, PromptTemplate
from haystack import Document


class Summarizer:
    """
    This exists to make it easier to apply the Haystack GA prompt node
    to arbitrary text.
    """

    default_prompt_template = PromptTemplate(
        name="lfqa",
        prompt_text="""Synthesize a comprehensive answer from the following text
        for the given question. Provide a clear and concise response, that summarizes
        the key points and information presented in the text. Your answer should be
        in your own words and be no longer than 50 words. If the question cannot be
        confidently answered from the information in the text, or if the question is
        not related to the text, reply 'NA'. \n\n
        Related text: {join(documents)} \n\n Question: {query} \n\n Answer:""",
    )

    def __init__(
        self, model_name_or_path: str = "google/flan-t5-large", prompt_text=None
    ):
        if prompt_text:
            self.prompt = PromptTemplate(name="lfqa", prompt_text=prompt_text)
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
