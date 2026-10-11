import gh_pick as gp

REPO = {
    "full_name": "o/r", "description": "x", "language": "Python",
    "stargazers_count": 10000, "forks_count": 500, "open_issues_count": 100,
    "archived": False, "license": {"spdx_id": "MIT"},
    "pushed_at": "2026-10-01T00:00:00Z", "created_at": "2020-01-01T00:00:00Z",
}
NOW = "2026-10-11T00:00:00Z"


def test_score_fresh_active_repo_is_high():
    s = gp.score(REPO, now=NOW)
    assert 70 <= s["total"] <= 100


def test_score_archived_repo_penalized():
    assert gp.score(dict(REPO, archived=True), now=NOW)["total"] < gp.score(REPO, now=NOW)["total"]


def test_score_stale_repo_penalized():
    stale = gp.score(dict(REPO, pushed_at="2021-01-01T00:00:00Z"), now=NOW)
    assert stale["total"] < 70


def test_score_no_license_penalized():
    assert gp.score(dict(REPO, license=None), now=NOW)["total"] < gp.score(REPO, now=NOW)["total"]


def test_score_has_named_components():
    s = gp.score(REPO, now=NOW)
    assert set(s) >= {"total", "activity", "community", "issues", "meta"}


def test_parse_repo_accepts_url_and_slug():
    assert gp.parse_repo("https://github.com/o/r") == "o/r"
    assert gp.parse_repo("o/r") == "o/r"
    assert gp.parse_repo("https://github.com/o/r.git") == "o/r"


def test_parse_repo_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        gp.parse_repo("just-a-name")
