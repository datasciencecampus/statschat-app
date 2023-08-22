import os
import logging

from haystack import Pipeline
from haystack.nodes import PreProcessor
from haystack.document_stores import InMemoryDocumentStore, FAISSDocumentStore
from haystack.nodes import BM25Retriever, FARMReader, EmbeddingRetriever, JoinDocuments

from statschat.custom_json_convertor import CustomJsonConverter
from statschat.llm import Summarizer
from statschat.handle_meta import prep_response, deduplicate_answers
from statschat.latest_flag_helpers import time_decay


class BasicSearcher:
    """
    Encapsulates the Haystack components, so that we don't keep re-instantiating
    the readers etc.
    Should make it easier to extend the functionality.
    """

    def __init__(
        self,
        directory: str,
        confidence_threshold: float = 0.03,
        reader_model="deepset/bert-large-uncased-whole-word-masking-squad2",
        embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
        embedding_dim: int = 768,
        answer_model: str = "google/flan-t5-large",
        answer_prompt: str = None,
        search_mode: str = "BM25",
        faiss_db_root: str = "data/db",
        split_length: int = 200,
        split_overlap: int = 20,
        k_docs: int = 10,
        k_answers: int = 3,
        use_latest: bool = True,
        logger: logging.Logger = None,
    ):
        # Store settings
        self.confidence_threshold = confidence_threshold
        self.reader_model = reader_model
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.answer_model = answer_model
        self.answer_prompt = answer_prompt
        self.search_mode = search_mode
        self.faiss_index_path = os.path.join(faiss_db_root, "faiss_index.faiss")
        self.faiss_config_path = os.path.join(faiss_db_root, "faiss_config.json")
        self.faiss_db_path = "sqlite:///" + str(
            os.path.join(faiss_db_root, "faiss_db.db")
        )
        self.db_exists = False
        self.split_length = split_length
        self.split_overlap = split_overlap
        self.k_docs = k_docs
        self.k_answers = k_answers
        self.use_latest = use_latest

        # Initialise logger
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        # Create the document store on instantiation
        self.logger.info("Create the document store on instantiation")
        self._create_document_pipeline()
        self.logger.info("Index documents in provided directory")
        self._index_documents(directory)

        # Create the search pipeline
        self.logger.info("Create the search pipeline")
        self._create_search_pipe()

        # Create a text summarizer for creating answers
        self.logger.info("Create a text summarizer for creating answers")
        self.summarizer = Summarizer(
            model_name_or_path=self.answer_model, prompt_text=self.answer_prompt
        )
        self.logger.info("Done BasicSearch object initiation (Haystack pipeline)")
        return None

    def __add_document_store(self):
        if self.search_mode in ["embedding", "both"]:
            if os.path.exists(self.faiss_index_path):
                self.embedding_document_store = FAISSDocumentStore.load(
                    index_path=self.faiss_index_path, config_path=self.faiss_config_path
                )
                self.db_exists = True
            else:
                self.embedding_document_store = FAISSDocumentStore(
                    sql_url=self.faiss_db_path,
                    faiss_index_factory_str="Flat",
                    embedding_dim=self.embedding_dim,
                )
                self.indexing_pipeline.add_node(
                    component=self.embedding_document_store,
                    name="EmbeddingDocumentStore",
                    inputs=["PreProcessor"],
                )
            self.embedding_retriever = EmbeddingRetriever(
                document_store=self.embedding_document_store,
                embedding_model=self.embedding_model,
            )

        if self.search_mode in ["BM25", "both", "bm25"]:
            self.bm25_document_store = InMemoryDocumentStore(use_bm25=True)
            self.bm25_retriever = BM25Retriever(document_store=self.bm25_document_store)
            self.indexing_pipeline.add_node(
                component=self.bm25_document_store,
                name="BM25DocumentStore",
                inputs=["PreProcessor"],
            )

        if self.search_mode not in ["embedding", "both", "BM25", "bm25"]:
            raise ValueError(
                "search mode should be one of: 'BM25', 'embedding', 'both'"
            )

        return None

    def _create_document_pipeline(self):
        """
        Build the document indexer and the document store, including defining
        a preprocessor.  There are a lot of hard-coded variables here for now,
        and honestly if they're sensible defaults and we're never changing them
        it might be more sensible to leave them as part of the code rather than
        clutter a config file with them.
        """
        self.indexing_pipeline = Pipeline()
        self.text_converter = CustomJsonConverter()
        self.preprocessor = PreProcessor(
            clean_whitespace=True,
            clean_empty_lines=True,
            split_length=self.split_length,
            split_overlap=self.split_overlap,
            split_respect_sentence_boundary=True,
        )

        self.indexing_pipeline.add_node(
            component=self.text_converter, name="TextConverter", inputs=["File"]
        )
        self.indexing_pipeline.add_node(
            component=self.preprocessor, name="PreProcessor", inputs=["TextConverter"]
        )
        self.__add_document_store()
        return None

    def _index_documents(self, directory: str):
        """
        Triggers indexing pipeline to ingest our JSON files and dump them to
        our document store.

        Args:
            directory (str): Folder holding your text documents
        """
        if self.db_exists and (self.search_mode == "embedding"):
            return None

        files_to_index = [
            directory + "/" + file
            for file in os.listdir(directory)
            if file.endswith(".json")
        ]
        self.indexing_pipeline.run_batch(file_paths=files_to_index)

        # Embedding model takes an extra command to trigger the expensive
        # embedding calculations
        if self.search_mode in ["embedding", "both"]:
            self.embedding_document_store.update_embeddings(
                self.embedding_retriever, update_existing_embeddings=False
            )
            # And let's keep that for later, since it's expensive!
            self.embedding_document_store.save(
                index_path=self.faiss_index_path, config_path=self.faiss_config_path
            )
        return None

    def _create_search_pipe(self):
        """
        Creates A document retriever and a reader to sit on top of it and
        distil an answer.
        """
        # The reader has a few useful options at
        # https://docs.haystack.deepset.ai/reference/reader-api
        # Note the context window is larger than the preprocessor split size,
        # So it'll return the entire segment from which it drew an answer
        self.reader = FARMReader(
            model_name_or_path=self.reader_model,
            context_window_size=500,
            # confidence_threshold=self.confidence_threshold,
        )
        self.pipe = Pipeline()
        if self.search_mode == "both":
            self.pipe.add_node(
                component=self.bm25_retriever, name="BM25Retriever", inputs=["Query"]
            )
            self.pipe.add_node(
                component=self.embedding_retriever,
                name="EmbeddingRetriever",
                inputs=["Query"],
            )
            self.pipe.add_node(
                component=JoinDocuments(join_mode="merge"),
                name="JoinRetriever",
                inputs=["BM25Retriever", "EmbeddingRetriever"],
            )
            self.pipe.add_node(
                component=self.reader, name="Reader", inputs=["JoinRetriever"]
            )
        elif self.search_mode == "embedding":
            self.pipe.add_node(
                component=self.embedding_retriever,
                name="EmbeddingRetriever",
                inputs=["Query"],
            )
            self.pipe.add_node(
                component=self.reader, name="Reader", inputs=["EmbeddingRetriever"]
            )
        else:
            self.pipe.add_node(
                component=self.bm25_retriever, name="BM25Retriever", inputs=["Query"]
            )
            self.pipe.add_node(
                component=self.reader, name="Reader", inputs=["BM25Retriever"]
            )
        return None

    def query(
        self, question: str, k_answers: int = None, k_docs: int = None, latest=1
    ) -> dict:
        """
        Handles questions - Note that UI can't handle more than one
        answer yet!

        Args:
            question (str): The text question a user has asked
            top_k (int, optional): Number of results to return. Defaults to 1.
            latest (int): how much weight to put on latest date. Defaults to 1.
                For no published date effect choose 0 or None.

        Returns:
            _type_: _description_
        """
        params = {"Reader": {"top_k": k_answers if k_answers else self.k_answers}}
        if self.search_mode in ["embedding", "both"]:
            params["EmbeddingRetriever"] = {"top_k": k_docs if k_docs else self.k_docs}
        if self.search_mode in ["bm25", "both", "BM25"]:
            params["BM25Retriever"] = {"top_k": k_docs if k_docs else self.k_docs}

        prediction = self.pipe.run(query=question, params=params)

        n_answers = len(prediction["answers"])
        # Handle case, no results:
        if n_answers == 0:
            return None, None

        if latest:
            for ans in prediction["answers"]:
                ans.score = ans.score * time_decay(ans.meta["release_date"], latest)
            prediction["answers"].sort(key=lambda x: -x.score)

        if prediction["answers"][0].score < self.confidence_threshold:
            summary = "NA"
        else:
            context = [
                prediction["answers"][i].context
                for i in range(min(2, n_answers))
                if prediction["answers"][i].score
                >= 0.8 * prediction["answers"][0].score
            ]
            summary = self.summarizer.query_texts(query=question, texts=context)

        result = {
            "answer": summary,
            "confidence": f"{int(prediction['answers'][0].score*100)}%",
            "references": deduplicate_answers(
                [
                    prep_response(prediction["answers"][i])
                    for i in range(n_answers)
                    # if prediction["answers"][i].score
                    # >= 0.8 * prediction["answers"][0].score
                ]
            ),
        }

        return result, prediction
