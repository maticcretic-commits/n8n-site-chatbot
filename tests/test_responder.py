"""Tests for server/mock_responder.py — mirrors the n8n workflow's chat logic."""

import json
import os
import sys

import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "server"))

from mock_responder import best_match, load_kb, respond, score_match, tokenize

KB = load_kb(os.path.join(BASE_DIR, "kb", "knowledge-base.json"))


def test_kb_has_enough_faqs():
    assert len(KB["faqs"]) >= 8


def test_exact_kb_match():
    res = respond({"message": "What are your opening hours?", "session_id": "s1"})
    assert res["status"] == "ok"
    assert res["source"] == "knowledge_base"
    assert res["faq_id"] == "hours"
    assert "9:00" in res["reply"] or "Monday" in res["reply"]


def test_partial_match():
    res = respond({"message": "How much for a cleaning please", "session_id": "s2"})
    assert res["status"] == "ok"
    assert res["source"] == "knowledge_base"
    assert res["faq_id"] == "price-cleaning"


def test_low_confidence_handoff():
    res = respond(
        {"message": "What is the square root of photosynthesis?", "session_id": "s3"}
    )
    assert res["status"] == "ok"
    assert res["handoff"] is True
    assert "Talk to a human" in res["reply"]


def test_missing_message_field():
    res = respond({"session_id": "s4"})
    assert res["status"] == "error"
    assert "message" in res["error"]


def test_empty_message():
    res = respond({"message": "   ", "session_id": "s5"})
    assert res["status"] == "error"


def test_non_dict_payload():
    res = respond(["not", "a", "dict"])
    assert res["status"] == "error"


def test_session_id_echoed():
    res = respond({"message": "Where is the clinic?", "session_id": "abc-123"})
    assert res["session_id"] == "abc-123"
    assert res["faq_id"] == "location"


def test_tokenize_strips_punctuation_and_lowercases():
    assert tokenize("Opening HOURS?!") == ["opening", "hours"]


def test_score_match_counts_overlap():
    faq = {
        "question": "What are your hours?",
        "answer": "Open Monday to Friday.",
        "keywords": ["timing"],
    }
    assert score_match(tokenize("What are your opening hours timing"), faq) >= 3
    assert score_match(tokenize("quantum entanglement"), faq) == 0


def test_stopwords_do_not_inflate_scores():
    faq = {
        "question": "Where is the clinic?",
        "answer": "We are at 42 Rosewood Lane.",
        "keywords": ["location"],
    }
    # only content word "clinic" overlaps -> below threshold
    assert score_match(tokenize("Is the clinic open"), faq) < 2


def test_best_match_returns_none_on_no_overlap():
    match, score = best_match("quantum entanglement banana", KB)
    assert match is None
    assert score == 0


def test_kb_file_is_valid_json():
    with open(os.path.join(BASE_DIR, "kb", "knowledge-base.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    assert all("question" in f and "answer" in f for f in data["faqs"])
