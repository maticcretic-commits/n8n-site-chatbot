# n8n Site Chatbot (practice project)

> **Practice/demo project for learning** — modeled on the type of work in a real
> $250 Upwork posting ("Chatbot help on n8n": build a knowledge-base chatbot
> that loads on a Google Site, using n8n).
>
> This is a learning exercise, not client work. There is no paid experience,
> client project, or endorsement behind it.

A knowledge-base chatbot that lives on a Google Site. Visitors chat in an
embeddable widget → the message hits an n8n webhook → n8n looks the question up
in a knowledge base → confident answers come straight from the KB, anything else
falls back to a human handoff (with an OpenAI-drafted reply).

## What's in here

| Path | What it is |
|---|---|
| `n8n/workflow.json` | Importable n8n workflow: Webhook → Extract Input → KB Lookup → IF (confident?) → Respond / OpenAI handoff draft → Respond |
| `widget/chat-widget.html` | Self-contained chat widget (HTML+CSS+vanilla JS, one file) to paste into Google Sites |
| `kb/knowledge-base.json` | Sample KB: 10 Q&A pairs for a fictional dental clinic ("BrightSmile") |
| `server/mock_responder.py` | Dependency-free local webhook that mirrors the n8n logic — practice/testing without n8n |
| `tests/test_responder.py` | pytest suite (12 tests) for the mock responder logic |

## Run it locally (no n8n needed)

```bash
cd n8n-site-chatbot
pip install -r requirements.txt          # installs pytest
python -m pytest tests/ -q              # all 12 tests should pass

# Start the mock webhook (mirrors the n8n workflow's logic)
python server/mock_responder.py          # listens on http://localhost:8080

# In another terminal, talk to it:
curl -s -X POST http://localhost:8080 \
  -H 'Content-Type: application/json' \
  -d '{"message":"What are your opening hours?","session_id":"demo1"}'
```

## Import the workflow into n8n

1. In n8n: **Workflows → ⋯ → Import from file**, choose `n8n/workflow.json`.
2. Set two environment variables in n8n (see the sticky note inside the workflow):
   - `KB_LOOKUP_URL` — for practice, `http://localhost:8080` with the mock responder running.
   - `HUMAN_WEBHOOK_URL` (optional) — where handoff requests go.
3. Attach your OpenAI credential to the **Draft Handoff (OpenAI)** node
   (or delete that node and hardcode a message in **Format Handoff**).
4. **Activate** the workflow, open the **Chat Webhook** node, and copy the
   **Production URL**.

## Embed the widget on a Google Site

1. Open `widget/chat-widget.html`, set `WIDGET_WEBHOOK_URL` (top of the `<script>`)
   to the Production URL from the step above.
2. On your Google Site: **Insert → Embed → Embed code** → paste the entire
   contents of `widget/chat-widget.html` → Insert.
3. The widget runs entirely client-side; no server or build step needed.

## Test each chat flow

| Test | What to send | Expected |
|---|---|---|
| KB hit (exact) | "What are your opening hours?" | Bot answers from the KB (`source: knowledge_base`) |
| KB hit (partial) | "how much is a cleaning" | Matches the cleaning-price FAQ |
| Low confidence → handoff | "What is photosynthesis?" | `handoff: true` + "Talk to a human" button appears |
| Malformed input | POST `{}` or non-JSON | 400 with an explanatory error |
| Human button | Click "Talk to a human" | Shows the front-desk contact message |

## Learning roadmap

- [ ] Import the workflow into a free n8n instance (n8n Cloud trial or self-hosted)
- [ ] Swap the mock KB for a real source (Google Sheet, Notion, or vector DB)
- [ ] Add conversation memory with the n8n "Conversation Memory" node
- [ ] Log handoff requests to a Google Sheet for follow-up
- [ ] Style the widget to match a real site's theme

## Disclaimer

Demo code for learning only. The "BrightSmile Dental Clinic" business,
prices, phone number, and hours are fictional. No real client data is involved.
