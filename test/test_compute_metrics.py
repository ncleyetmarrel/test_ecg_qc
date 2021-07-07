from dags.tasks.compute_metrics import get_scores


def test_get_score():
    assert get_scores(420, 935, 923) == [31.0, 31.27, 31.13]
