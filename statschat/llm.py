import logging
from langchain import HuggingFacePipeline
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts.prompt import PromptTemplate
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from typing import List


# Prompt specific to text2text-generation LLM task
generate_template = """Synthesize a comprehensive answer from the following text
        for the given question. Provide a clear and concise response, that summarizes
        the key points and information presented in the text. Your answer should be
        in your own words and be no longer than 50 words. If the question cannot be
        confidently answered from the information in the text, or if the question is
        not related to the text, reply 'NA'. \n\n
        Related text: {context} \n\n Question: {question} \n\n Helpful answer: """

generate_prompt = PromptTemplate(
    template=generate_template, input_variables=["context", "question"]
)

# Prompt specific to summarization LLM task
summarise_template = """The following is a set of documents
{text}.
Take these and distill it into a final, consolidated summary of the main themes.

Summary:"""

summarise_prompt = PromptTemplate.from_template(summarise_template)


class Inquirer:
    """
    Wraps the logic for using an LLM to synthesise a written answer from
    the text of a set of searched/retrieved documents.
    """

    def __init__(
        self,
        model_name_or_path: str = "google/flan-t5-large",
        faiss_db_root: str = "db_lc",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        k_docs: int = 3,
        k_contexts: int = 3,
        similarity_threshold: float = 2.0,  # noqa: E501 # higher threshold for smaller corpus! Reduce below 1.0 with larger corpus
        return_source_documents: bool = True,
        logger: logging.Logger = None,
        summarizer_on: bool = False,
        llm_summarize_temperature: float = 0.0,
        llm_generate_temperature: float = 0.0,
    ):
        """
        Args:
            model_name_or_path (str, optional): Hugging Face model id.
                Defaults to "google/flan-t5-large".
            prompt_text (str, optional): Alternative prompt text.
                Defaults to None.
        """

        # Initialise logger
        if logger is None:
            self.logger = logging.getLogger(__name__)

        else:
            self.logger = logger

        self.k_docs = k_docs
        self.k_contexts = k_contexts
        self.similarity_threshold = similarity_threshold
        self.return_source_documents = return_source_documents
        self.summarizer_on = summarizer_on
        self.llm_summarise_temperature = llm_summarize_temperature
        self.llm_generate_temperature = llm_generate_temperature

        # Load LLM with text2text-generation specifications
        self.llm_generate = HuggingFacePipeline.from_model_id(
            model_id=model_name_or_path,
            task="text2text-generation",
            model_kwargs={
                "temperature": self.llm_generate_temperature,
                "max_length": 512,
            },
        )

        if self.summarizer_on:
            # Load LLM with summarization specifications
            self.llm_summarise = HuggingFacePipeline.from_model_id(
                model_id=model_name_or_path,
                task="summarization",
                model_kwargs={
                    "temperature": self.llm_summarise_temperature,
                    "max_length": 512,
                },
            )

        embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

        self.db = FAISS.load_local(faiss_db_root, embeddings)

        return None

    @staticmethod
    def flatten_meta(d):
        """Utility, raise metadata within nested dicts."""
        return d | d.pop("metadata")

    def similarity_search(self, query: str, return_dict: bool = True) -> List[Document]:
        """
        Returns k document chunks with the highest relevance to the
        query

        Args:
            query (str): Question for which most relevant articles will
            be returned
            return_dict: if True, data returned as dictionary, key = rank

        Returns:
            List[Document]: List of top k article chunks by relevance
        """
        self.logger.info("Retrieving most relevant text chunks")
        top_matches = self.db.similarity_search_with_score(query=query, k=self.k_docs)

        # filter to document matches with similarity scores less than...
        # i.e. closest cosine distances to query
        top_matches = [x for x in top_matches if x[-1] <= self.similarity_threshold]

        if return_dict:
            return [
                self.flatten_meta(doc[0].dict()) | {"score": float(doc[1])}
                for doc in top_matches
            ]

        return top_matches

    def query_texts(self, query: str, top_matches: list[dict]) -> str:
        """
        Generates an answer to the query based on realtionship
        to docs filtered in similarity_search

        Args:
            query (str): Question for which most relevant articles will
            be returned
            top_matches (list[dict]): Documents closely related to query

        Returns:
            str: Generated response to query
        """
        # reshape Document object structure
        top_matches = [
            Document(page_content=text["page_content"], metadata={"source": "NA"})
            for text in top_matches[: self.k_contexts]
        ]

        self.logger.info(f"Passing top {len(top_matches)} results for QA")

        # stuff all above documents to the model
        chain = load_qa_chain(
            self.llm_generate, chain_type="stuff", prompt=generate_prompt
        )

        # parameter values
        response = chain(
            {"input_documents": top_matches, "question": query},
            return_only_outputs=True,
        )

        return response["output_text"]

    def summarizer(self, top_matches: List[Document]) -> str:
        """
        Produces a summary of the documents passed in

        Args:
            top_matches (List[Document]): Documents closely related to query

        Returns:
            str: Generated summary text
        """
        # responds well to key words and phrases rather than questions

        if not self.summarizer_on:
            self.logger.info(
                "Please reinstantiate the Interrogater class \
                        and specify summarizer_on=True"
            )
            pass

        else:
            top_matches = [
                Document(page_content=text["page_content"], metadata={"source": "NA"})
                for text in top_matches[: self.k_contexts]
            ]

            # are there any closely matched documents passed in?
            if top_matches:
                self.logger.info(f"Passing top {len(top_matches)} results for QA")
                llm_chain = LLMChain(llm=self.llm_summarise, prompt=summarise_prompt)

                stuff_chain = StuffDocumentsChain(
                    llm_chain=llm_chain, document_variable_name="text"
                )

                response = stuff_chain.run(top_matches)

                return response

            else:
                print("No relevant documents found")
