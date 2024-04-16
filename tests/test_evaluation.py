import os
from datetime import datetime
from statschat.model_evaluation.evaluation import pipeline


# @pytest.mark.skipif(sys.platform.startswith("linux"), reason="Takes too long in CI")
def test_evaluation_runs():
    """simple end-to-end test of evaluation pipeline"""
    pipeline(app_config_file="tests/config/test_eval_config.toml", n_questions=1)
    test_file = f"data/test_outcomes/{format(datetime.now(), '%Y-%m-%d_%H:%M')}_"
    file_exists = None
    if os.path.exists(test_file + "questions.csv"):
        file_exists = True
        for ext in ["questions.csv", "config.json", "metrics.json"]:
            os.remove(test_file + ext)

    assert file_exists, "Did not create/find evaluation test results csv."
