"""知识图谱核心算法测试（纯函数，不依赖 LLM）。

覆盖：HTML 清洗、分词、TF-IDF 向量、余弦相似度。
"""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.services.knowledge_graph_service import (
    _clean_html,
    _compute_tfidf,
    _cosine_similarity,
    _tokenize,
)
from main import app


def _note(nid: int, title: str = "", content: str = ""):
    return SimpleNamespace(id=nid, title=title, content=content)


class TestCleanHtml:
    def test_strips_tags(self):
        assert _clean_html("<p>hello</p>").strip() == "hello"
        assert "<" not in _clean_html("<div><span>hi</span></div>")

    def test_strips_html_entities(self):
        assert _clean_html("a&nbsp;b") == "a b"
        assert _clean_html("&amp;") == " "

    def test_empty_and_none(self):
        assert _clean_html("") == ""
        assert _clean_html(None) == ""


class TestTokenize:
    def test_chinese_words_kept(self):
        words = _tokenize("机器学习 深度学习 算法")
        assert "机器学习" in words
        assert "算法" in words

    def test_english_stopwords_removed(self):
        words = _tokenize("the quick brown fox jumps")
        assert "quick" in words
        assert "the" not in words

    def test_short_tokens_dropped(self):
        assert _tokenize("a b c") == []

    def test_html_cleaned_before_tokenize(self):
        words = _tokenize("<p>note content here</p>")
        assert "note" in words

    def test_common_chinese_stopword_removed(self):
        words = _tokenize("我 是 学生")
        assert "学生" in words
        assert "我" not in words


class TestComputeTfidf:
    def test_empty_notes(self):
        assert _compute_tfidf([]) == ({}, {})

    def test_single_note_builds_vector(self):
        vectors, idf = _compute_tfidf([_note(1, "机器学习", "机器学习 深度学习 机器学习")])
        assert 1 in vectors
        assert "机器学习" in vectors[1]
        assert idf

    def test_idf_smaller_for_common_word(self):
        notes = [_note(1, "t", "机器学习 深度学习"), _note(2, "t", "机器学习 算法")]
        _, idf = _compute_tfidf(notes)
        assert idf["机器学习"] < idf["深度学习"]


class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = {"机器学习": 1.0, "算法": 0.5}
        assert _cosine_similarity(a, dict(a)) == pytest.approx(1.0)

    def test_no_common_keys(self):
        assert _cosine_similarity({"机器学习": 1.0}, {"深度学习": 1.0}) == 0.0

    def test_zero_vector(self):
        assert _cosine_similarity({}, {"机器学习": 1.0}) == 0.0
        assert _cosine_similarity({}, {}) == 0.0


class TestKgApi:
    """知识图谱 API（无图谱时返回 idle 状态）。"""

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    @pytest.fixture
    def auth_token(self, client):
        import uuid

        email = f"kg_api_{uuid.uuid4().hex[:8]}@example.com"
        client.post(
            "/api/v1/user/register",
            json={"email": email, "password": "Test123456", "nickname": "kgtest"},
        )
        r = client.post("/api/v1/user/login", json={"email": email, "password": "Test123456"})
        assert r.status_code == 200
        return r.json()["access_token"]

    def test_kg_status_requires_auth(self, client):
        assert client.get("/api/v1/kg/status").status_code == 401

    def test_kg_status_idle_when_no_graph(self, client, auth_token):
        r = client.get(
            "/api/v1/kg/status", headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "idle"
        assert data["progress"] == 0
