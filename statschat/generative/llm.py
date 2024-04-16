import logging
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.output_parsers import PydanticOutputParser
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from statschat.generative.response_model import LlmResponse
from statschat.generative.prompts import (
    EXTRACTIVE_PROMPT_PYDANTIC,
    STUFF_DOCUMENT_PROMPT,
)
from functools import lru_cache
from statschat.generative.utils import deduplicator, highlighter
from statschat.embedding.latest_flag_helpers import time_decay


class Inquirer:
    """
    Wraps the logic for using an LLM to synthesise a written answer from
    the text of a set of searched/retrieved documents.
    """

    def __init__(
        self,
        generative_model_name: str = "google/flan-t5-large",
        faiss_db_root: str = "data/db_langchain",
        faiss_db_root_latest: str = None,
        embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
        k_docs: int = 10,
        k_contexts: int = 3,
        similarity_threshold: float = 2.0,  # noqa: E501 # higher threshold for smaller corpus! Reduce below 1.0 with larger corpus
        logger: logging.Logger = None,
        llm_temperature: float = 0.0,
        llm_max_tokens: int = 1024,
        verbose: bool = False,
    ):
        """
        Args:
            generative_model_name (str, optional): Hugging Face model id.
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
        self.verbose = verbose
        self.extractive_prompt = EXTRACTIVE_PROMPT_PYDANTIC
        self.stuff_document_prompt = STUFF_DOCUMENT_PROMPT

        # Answer generation LLM
        if generative_model_name.startswith(
            "text-"
        ) or generative_model_name.startswith("gemini"):
            self.llm = VertexAI(
                model_name=generative_model_name,
                temperature=llm_temperature,
                max_output_tokens=llm_max_tokens,
            )

        else:
            # Load LLM with text2text-generation specifications
            self.llm = HuggingFacePipeline.from_model_id(
                model_id=generative_model_name,
                task="text2text-generation",
                model_kwargs={
                    "temperature": llm_temperature,
                    "max_length": llm_max_tokens,
                },
            )

        if embedding_model_name.startswith("textembedding-"):
            embeddings = VertexAIEmbeddings(model_name=embedding_model_name)
        else:
            embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        self.db = FAISS.load_local(faiss_db_root, embeddings)
        if faiss_db_root_latest is None:
            faiss_db_root_latest = faiss_db_root + "_latest"
        self.db_latest = FAISS.load_local(faiss_db_root_latest, embeddings)

        return None

    @staticmethod
    def flatten_meta(d):
        """Utility, raise metadata within nested dicts."""
        return d | d.pop("metadata")

    def similarity_search(
        self, query: str, latest_filter: bool = True, return_dicts: bool = True
    ) -> list[dict]:
        """
        Returns k document chunks with the highest relevance to the
        query

        Args:
            query (str): Question for which most relevant articles will
            be returned
            return_dicts: if True, data returned as dictionary, key = rank

        Returns:
            List[dict]: List of top k article chunks by relevance
        """
        self.logger.info("Retrieving most relevant text chunks")
        if latest_filter:
            top_matches = self.db_latest.similarity_search_with_score(
                query=query, k=self.k_docs
            )
        else:
            top_matches = self.db.similarity_search_with_score(
                query=query, k=self.k_docs
            )

        # filter to document matches with similarity scores less than...
        # i.e. closest cosine distances to query
        top_matches = [x for x in top_matches if x[-1] <= self.similarity_threshold]

        if return_dicts:
            return [
                self.flatten_meta(doc[0].dict()) | {"score": float(doc[1])}
                for doc in top_matches
            ]
        return top_matches

    def query_texts(self, query: str, docs: list[dict]) -> LlmResponse:
        """
        Generates an answer to the query based on relationship
        to docs filtered in similarity_search

        Args:
            query (str): Question for which most relevant articles will
            be returned
            docs (list[dict]): Documents closely related to query

        Returns:
            LlmResponse: Generated response to query (pydantic model)
        """
        # Handle case: no search results
        if not docs:
            return LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
            )

        # reshape Document object structure
        top_matches = [
            Document(
                page_content=text["page_content"],
                metadata={
                    "doc_num": i + 1,
                    "date": text["date"],
                    "title": text["title"],
                },
            )
            for i, text in enumerate(docs[: self.k_contexts])
            if text["score"] <= 1.5 * docs[0]["score"]
        ]
        self.logger.info(f"Passing top {len(top_matches)} results for QA")

        # stuff all above documents to the model
        chain = load_qa_with_sources_chain(
            self.llm,
            chain_type="stuff",
            prompt=self.extractive_prompt,
            document_prompt=self.stuff_document_prompt,
            verbose=self.verbose,
        )

        # parameter values
        response = chain.invoke(
            {"input_documents": top_matches, "question": query},
            return_only_outputs=True,
        )

        parser = PydanticOutputParser(pydantic_object=LlmResponse)
        try:
            if "output_text" in response:
                validated_answer = parser.parse(response["output_text"])
            elif "properties" in response:
                validated_answer = parser.parse(response["properties"])
            else:
                validated_answer = parser.parse(response)
        except Exception as e:
            self.logger.error(f"Cannot parse response: {e}")
            self.logger.error(f"response: {response}")
            return LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
                reasoning=f"Cannot parse response: {e} /n/n  response: {response}",
            )

        return validated_answer

    @lru_cache()
    def make_query(
        self,
        question: str,
        latest_filter: str = "on",
        highlighting: bool = True,
        latest_weight: float = 1,
    ) -> tuple[list[dict], str, LlmResponse]:
        """
        Utility, wraps code for querying the search engine, and then the summarizer.
        Also handles storing the last answer made for feedback purposes.

        Args:
            question (str): The user query.
            latest_filter (str, optional): Whether to filter to bulletins with
                'latest' flag.  Values 'on', 'On', 'true', 'True' are all indicative
                for filtering. Defaults to 'on'.
            highlighting (bool, optional): Whether highlighting to be used.
                Defaults to true.
            latest_weight (float, optional): How much the score of retrieved
                publications should be reweighted towards the recent. Defaults to 1.

        Returns:
            list[dict]: supporting documents (with highlighting)
            str: formatted answer for app to display
            LlmResponse: Generated response to query (pydantic model)
        """
        self.logger.info(f"Search query: {question}")
        docs1 = self.similarity_search(
            question, latest_filter=latest_filter in ["On", "on", "true", "True", True]
        )

        if len(docs1) == 0:
            return docs1, ""
        docs = deduplicator(docs1, keys=["section", "title", "date"])

        if latest_weight > 0:
            for doc in docs:
                # Divided by decay term because similarity scores are inverted
                # Original score is L2 distance; lower is better
                # https://python.langchain.com/docs/integrations/vectorstores/faiss
                doc["score"] = doc["score"] / time_decay(
                    doc["date"], latest=latest_weight
                )
            docs.sort(key=lambda doc: doc["score"])
            self.logger.info(
                "Weighted and reordered docs to latest with "
                + f"decay = {latest_weight}"
            )

        for doc in docs:
            doc["score"] = round(doc["score"], 2)

        self.logger.info(
            f"Received {len(docs)} references"
            + f" with top distance {docs[0]['score'] if docs else 'Inf'}"
        )

        validated_response = self.query_texts(question, docs)
        self.logger.info(f"QAPAIR - Question: {question}, Answer: {validated_response}")

        if highlighting:
            docs = highlighter(
                docs, validated_response=validated_response, logger=self.logger
            )
        self.logger.info(f"QASOURCE - Docs: {docs}")

        if validated_response.answer_provided is False:
            answer_str = ""
        else:
            answer_str = (
                "Most relevant quote from publications below: "
                + '<h4 class="ons-u-fs-xxl"> <div id="answer">'
                + validated_response.most_likely_answer
                + "</div> </h4>"
            )

        return docs, answer_str, validated_response
