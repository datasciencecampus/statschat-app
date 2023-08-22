import shutil
import json
from statschat.preprocess import PrepareVectorStore


def test_faiss_docs_load():
    """simple test of documents loaded from faiss db"""
    searcher = PrepareVectorStore(
        directory="tests/data",
        split_directory="tests/temp/json_split",
        faiss_db_root="tests/temp/db_langchain",
    )
    assert (
        len(searcher.db.docstore._dict) == 101
    ), "Langchain searcher did not load expected number of documents"
    shutil.rmtree("tests/temp/db_langchain")
    shutil.rmtree("tests/temp/json_split")


def test_redundancy_filter():
    """simple test checking removal of duplicate documents"""
    data_from = "tests/data"
    data_to = "tests/temp/data"
    shutil.copytree(data_from, data_to)

    amend_file_from = f"{data_to}/2023-06-05_uk-environmental-accounts-2023.json"
    amend_file_to = f"{data_to}/2023-06-05_uk-environmental-accounts-2023_copy.json"
    shutil.copy(amend_file_from, amend_file_to)

    # amend copied json with additional _copy string for recognition
    with open(amend_file_to, "r") as i:
        data = json.load(i)
        data["id"] = data["id"] + "_copy"
        data["title"] = data["title"] + "_copy"

    with open(
        f"{data_to}/2023-06-05_uk-environmental-accounts-2023_copy.json", "w"
    ) as o:
        json.dump(data, o, indent=4)

    searcher = PrepareVectorStore(
        directory=data_to,
        split_directory="tests/temp/data/json_split",
        faiss_db_root="tests/temp/db_langchain",
    )

    # check if section_urls are duplicated in pre-split docs
    docs = getattr(searcher, "docs")
    matched_files = [x.metadata["section_url"] for x in docs]
    shutil.rmtree("tests/temp")
    print(len(matched_files))
    print(len(set(matched_files)))

    assert len(set(matched_files)) == len(
        matched_files
    ), "Some identical document sections have not been dropped correctly"
