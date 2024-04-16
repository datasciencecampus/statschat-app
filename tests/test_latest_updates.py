import os
import shutil
import json
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from statschat.embedding.latest_updates import (
    find_latest,
    compare_latest,
    unflag_former_latest,
    # update_split_documents,
    find_matching_chunks,
)


def test_prep_test_data():
    """prepares temporary directory of articles
    for use in this test suite"""
    # prepare temp dir
    dir_from = "tests/data"
    dir_to = "tests/temp/data"
    shutil.copytree(dir_from, dir_to)
    os.mkdir(f"{dir_to}/temp")

    # remove filename in wrong format - not being tested here
    os.remove(
        f"{dir_to}/20230228_economic-statistics-sector-classification-–-classification-update-and-forward-work-plan-february-2023.json"  # noqa:E501
    )

    new_bulletin = (
        """{
        "id": "2024-01-01_uk-environmental-accounts-2023",
        "title": "UK Environmental Accounts: 2023",
        """
        + '"url": "https://www.ons.gov.uk/economy/environmentalaccounts/bulletins/ukenvironmentalaccounts/2023",'  # noqa:E501
        + """
        "release_date": "2024-01-01",
        "release_type": "bulletins",
        "latest": true,
        "url_keywords": [
            "economy",
            "environmentalaccounts"
        ],
        "contact_name": "pytest temporary",
        "contact_link": "pytest temporary",
        "content": []
        }"""
    )

    with open(
        f"{dir_to}/temp/2024-01-01_uk-environmental-accounts-2023.json", "w"
    ) as f:
        json.dump(new_bulletin, f)


def test_find_latest():
    """simple test of checking for latest articles
    in document store"""
    dir = "tests/temp/data"
    latest_filepaths = find_latest(dir)
    assert len(latest_filepaths) == 2


def test_compare_latest():
    """simple test of checking for older versions
    of articles in a series"""
    dir = "tests/temp/data"
    latest_filepaths = [
        f"{dir}/2023-06-05_uk-environmental-accounts-2023.json",
        f"{dir}/2023-06-09_uk-inclusive-income-2005-to-2019.json",
    ]
    new_latest, former_latest = compare_latest(dir, latest_filepaths)
    assert len(new_latest) == 1
    assert len(former_latest) == 1


def test_unflag_former_latest():
    """simple test of flag revocation"""
    dir = "tests/temp/data"
    former_latest = ["2023-06-05_uk-environmental-accounts-2023.json"]
    unflag_former_latest(dir, former_latest)
    with open(f"{dir}/{former_latest[0]}", "r") as f:
        data = json.load(f)
    assert data["latest"] is False


def test_find_matching_chunks():
    """simple test of finding db chunks linked
    to older article in series"""
    db_loc = "tests/data/db_test"
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
    db_dict = FAISS.load_local(db_loc, embeddings).docstore._dict
    docs = ["2023-06-05_uk-environmental-accounts-2023"]
    matched_chunks = find_matching_chunks(db_dict, docs)
    assert len(matched_chunks) == 29


def test_cleanup_temp_data():
    """teardown temporary test data"""
    dir = "tests/temp/data"
    shutil.rmtree(dir)
