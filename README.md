# awesome-function-calling

***A curated, open-source catalog of LLM function/tool definitions in JSON Schema format.***

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Functions](https://img.shields.io/badge/functions-15-brightgreen.svg)](functions/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## What is function calling?

Modern LLMs (GPT-4, Claude, Gemini, …) can do more than generate text — they can decide to **call a tool** when answering a question.  
You describe a function in JSON Schema, attach it to your API request, and the model returns a structured `tool_call` object instead of prose when it decides the function is needed.

```
User  ──► "Play something upbeat by Daft Punk on Spotify"
           │
           ▼
         LLM (with tools)
           │
           └──► tool_call: play_music({
                    "artist":  "Daft Punk",
                    "playlist": "upbeat",
                    "service":  "spotify",
                    "shuffle":  true
                })
                    │
                    ▼
              your code runs
              (calls Spotify SDK / API)
                    │
                    ▼
         LLM ◄── tool result: {
                    "status":  "playing",
                    "track":   "Harder, Better, Faster, Stronger",
                    "artist":  "Daft Punk",
                    "service": "spotify"
                 }
           │
           ▼
User  ◄── "Now playing 'Harder, Better, Faster, Stronger' by Daft Punk on Spotify 🎵"
```

This repo collects **ready-to-use function definitions** so you don't have to write them from scratch.

---


## Function catalog

| Function | Description |
|---|---|
| `get_weather` | Current conditions + multi-day forecast for any location |
| `convert_currency` | ISO 4217 currency conversion with live rates |
| `get_current_time` | Current date/time for any IANA timezone |
| `search_news` | Recent articles by keyword, language, and date range |
| `send_email` | Compose and send email with CC/BCC support |
| `track_order` | Shipping status and ETA for any major carrier |
| `web_search` | General web search with ranked results and snippets |
| `create_event` | Calendar event creation with attendees and reminders |
| `book_ride` | Ride-hailing booking with scheduling and ride type |
| `play_music` | Play track / album / playlist on any streaming service |
| `get_stock_price` | Real-time stock price, change, and market stats |
| `translate_text` | Neural machine translation with auto language detection |
| `set_reminder` | One-time or recurring reminders via push/email/SMS |
| `get_directions` | Turn-by-turn routing for driving, walking, transit, cycling |
| `summarize_text` | Concise summaries in paragraph, bullet, or TL;DR style |

Each file in `functions/` is a self-contained JSON Schema object ready to drop into any OpenAI-compatible API call.

---

## Quick start

No external dependencies are required to run the offline mock demo.

```bash
# Clone the repo
git clone https://github.com/edujbarrios/awesome-function-calling.git
cd awesome-function-calling

# Run the offline mock demo (no API key needed)
python src/llm_placeholder.py
```

### Live demo with llm7.io

[llm7.io](https://llm7.io) provides a free OpenAI-compatible endpoint. Set your API key (optional for free-tier) and run:

```bash
# Optional — only needed for paid features
export LLM7_API_KEY="your-token"   # macOS / Linux
$env:LLM7_API_KEY = "your-token"   # Windows PowerShell

python src/llm_placeholder.py
```

---

## How to add a new function

1. Create a new file in `functions/` named `<your_function>.json`.
2. Follow the existing schema:

```json
{
  "name": "your_function_name",
  "description": "A clear, one-sentence description.",
  "parameters": {
    "type": "object",
    "properties": {
      "param_one": {
        "type": "string",
        "description": "What this parameter controls."
      }
    },
    "required": ["param_one"]
  }
}
```

3. The function is automatically discovered — no registration needed.
4. Open a PR.

---

## Contributing

Contributions are welcome and encouraged! If you have a useful function definition, a bug fix, or an improvement to the demo code:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-new-function`)
3. Commit your changes (`git commit -m "feat: add my_new_function"`)
4. Push and open a Pull Request

Please keep function descriptions concise, parameter names consistent with the existing catalog, and JSON valid.

---

## License

[MIT](LICENSE) — Eduardo J. Barrios, 2024.

Free to use, modify, and distribute with attribution.

---

## Citation

If you use this catalog in your research, project, or product, please cite it as:

```bibtex
@misc{barrios2024awesomefunctioncalling,
  author       = {Eduardo J. Barrios},
  title        = {awesome-function-calling: A curated catalog of LLM function/tool definitions in JSON Schema format},
  year         = {2026},
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/edujbarrios/awesome-function-calling}}
}
```
