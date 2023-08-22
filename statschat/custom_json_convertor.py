import json
from typing import List, Optional, Any, Dict

import logging
from pathlib import Path

from haystack import Document
from haystack.nodes.file_converter import BaseConverter


logger = logging.getLogger(__name__)


class CustomJsonConverter(BaseConverter):
    """Extracts text from JSON files and casts it into Document objects."""

    outgoing_edges = 1

    def convert(
        self,
        file_path: Path,
        meta: Optional[Dict[str, Any]] = None,
        encoding: Optional[str] = "UTF-8",
        remove_numeric_tables: Optional[bool] = None,
        valid_languages: Optional[List[str]] = None,
        id_hash_keys: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Reads a JSON file and converts it into a list of Documents.

        It expects one of these formats:
        - A JSON file with a list of Document dicts.

        :param file_path: Path to the JSON file you want to convert.
        :param meta: Optional for inheritence purposes, taken from json.
        :param remove_numeric_tables: Uses heuristics to remove numeric rows.
                     Note: Not currently used in this Converter.
        :param valid_languages: Validates languages from a list of languages.
                     Note: Not currently used in this Converter.
        :param encoding: Encoding used when opening the json file.
        :param id_hash_keys: Optional for inheritence purposes, uses ['meta'].
        """

        docs: List[Document] = []

        with open(file_path, mode="r", encoding=encoding, errors="ignore") as f:
            try:
                data = json.load(f)
                for section in data["content"]:
                    if section["section_text"]:
                        doc_dict = {
                            "content": section["section_text"],
                            "content_type": "text",
                            "meta": {
                                **{i: data[i] for i in data if i != "content"},
                                **{
                                    i: section[i]
                                    for i in section
                                    if i != "section_text"
                                },
                            },
                            "id_hash_keys": ["meta", "content"],
                        }

                        docs.append(Document.from_dict(doc_dict))
            except KeyError:
                logger.warning(f"Could not parse {file_path}")
        return docs
