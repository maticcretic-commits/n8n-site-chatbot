"""Dependency-free mock of the n8n workflow's respond logic.

Mirrors the n8n workflow: receives {"message", "session_id"}, scores KB matches
by keyword/overlap, returns a KB answer when confident, otherwise a human-handoff
payload. Used for local testing without n8n installed.
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(BASE_DIR, "kb", "knowledge-base.json")

CONFIDENCE_THRESHOLD = 2  # minimum keyword-overlap score to answer from the KB

# Common words carry no topical signal and inflate overlap scores.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had", "having",
    "i", "me", "my", "mine", "you", "your", "yours",
    "we", "our", "ours", "us", "it", "its",
    "they", "them", "their", "theirs",
    "he", "him", "his", "she", "her", "hers",
    "and", "or", "but", "if", "then", "else", "so",
    "of", "to", "in", "on", "at", "for", "from", "by", "with", "as", "into",
    "this", "that", "these", "those",
    "not", "no", "yes", "can", "will", "would", "could", "should",
    "may", "might", "must", "please", "very", "just", "like", "get", "got",
}


def load_kb(kb_path=KB_PATH):
    with open(kb_path, encoding="utf-8") as fh:
        return json.load(fh)


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in STOPWORDS]


def score_match(message_tokens, faq):
    """Count keyword overlaps between message tokens and a FAQ entry."""
    haystack = set(
        tokenize(faq.get("question", ""))
        + tokenize(faq.get("answer", ""))
        + [k.lower() for k in faq.get("keywords", [])]
    )
    return sum(1 for tok in message_tokens if tok in haystack)


def best_match(message, kb):
    tokens = tokenize(message)
    best, best_score = None, 0
    for faq in kb.get("faqs", []):
        score = score_match(tokens, faq)
        if score > best_score:
            best, best_score = faq, score
    return best, best_score


def respond(payload, kb=None):
    """Core chat logic shared by the HTTP handler and the tests.

    Returns a dict shaped like the n8n workflow's Respond to Webhook output.
    """
    kb = kb if kb is not None else load_kb()

    if not isinstance(payload, dict):
        return {"status": "error", "error": "Request body must be a JSON object."}

    message = payload.get("message")
    session_id = payload.get("session_id", "anonymous")

    if not message or not str(message).strip():
        return {
            "status": "error",
            "session_id": session_id,
            "error": "Please provide a 'message' field with your question.",
        }

    match, score = best_match(str(message), kb)
    if match is not None and score >= CONFIDENCE_THRESHOLD:
        return {
            "status": "ok",
            "session_id": session_id,
            "reply": match["answer"],
            "source": "knowledge_base",
            "faq_id": match["id"],
        }

    return {
        "status": "ok",
        "session_id": session_id,
        "reply": (
            "I couldn't find an answer to that. Tap 'Talk to a human' or call "
            "(555) 123-4567 and our team will help you."
        ),
        "source": "handoff",
        "handoff": True,
    }


class ChatHandler(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send({"status": "error", "error": "Invalid JSON body."}, code=400)
            return
        result = respond(payload)
        code = 200 if result["status"] == "ok" else 400
        self._send(result, code=code)

    def log_message(self, *args):  # keep console output quiet
        pass


def main():
    port = int(os.environ.get("MOCK_PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), ChatHandler)
    print(f"Mock responder listening on http://localhost:{port}/ (POST JSON here)")
    server.serve_forever()


if __name__ == "__main__":
    main()
