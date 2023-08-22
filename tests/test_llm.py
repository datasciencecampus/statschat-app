from statschat.llm import Inquirer


def test_llm_answer():
    """Independently test it instantiates and runs QA"""
    inquirer = Inquirer(
        model_name_or_path="google/flan-t5-small", faiss_db_root="tests/data/db_test"
    )

    docs = [
        {
            "page_content": "Today is Tuesday.",
            "source": "dummy1.json",
            "seq_num": 1,
            "score": 0.4644126296043396,
        },
        {
            "page_content": "My birthday is on Thursday.",
            "source": "dummy2.json",
            "seq_num": 1,
            "score": 0.6272023320198059,
        },
    ]

    result = inquirer.query_texts(query="What day is it today?", top_matches=docs)

    assert "Tuesday" in result


def test_llm_search():
    """Just tests that this instantiates and runs."""
    inquirer = Inquirer(
        model_name_or_path="google/flan-t5-small", faiss_db_root="tests/data/db_test"
    )

    result = inquirer.similarity_search(
        query="How many national parks are there in England?"
    )

    assert "National parks" in result[0]["page_content"]
