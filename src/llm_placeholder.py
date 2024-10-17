"""
llm_placeholder.py
------------------
A minimal Python script that simulates an LLM selecting and executing
a function from the awesome-function-calling catalog.

The pipeline:
  1. Load function definitions from the functions/ directory (one JSON per function).
  2. Accept a natural-language user query.
  3. Use a keyword-matching strategy to select the best-fit function
     (this stands in for an LLM's tool-selection reasoning step).
  4. Build a demo argument set from the function's parameter schema.
  5. Execute a mock handler and print the simulated response.

No real API calls are made — all responses are mocked for demonstration.

Usage:
    python src/llm_placeholder.py
"""

import json
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import requests as _requests
except ImportError:  # requests is optional — only needed for the live llm7.io demo
    _requests = None  # type: ignore


# ─────────────────────────────────────────────────────────────
# Catalog loading
# ─────────────────────────────────────────────────────────────

def load_functions(functions_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load every *.json file from the functions/ directory and return
    the list of function definition objects, sorted by name.
    """
    if functions_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
        functions_dir = base_dir / "functions"

    functions_path = Path(functions_dir)
    if not functions_path.is_dir():
        raise FileNotFoundError(f"functions directory not found: {functions_path}")

    definitions = []
    for json_file in sorted(functions_path.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as fh:
            definitions.append(json.load(fh))

    return definitions


# Keep a thin compatibility shim so demo.py can still call get_functions().
def get_functions(functions_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Alias for load_functions — kept for backward compatibility."""
    return load_functions(functions_dir)


# ─────────────────────────────────────────────────────────────
# llm7.io — live function-calling integration
# ─────────────────────────────────────────────────────────────
# Set LLM7_API_KEY to your token (or export it as an environment
# variable) to enable the live demo section at the bottom.
# Free-tier usage does not require a key; leave the string empty
# or omit it and the live section will be skipped gracefully.

import os as _os

LLM7_API_KEY: str  = _os.environ.get("LLM7_API_KEY", "")  # optional
LLM7_BASE_URL: str = "https://api.llm7.io/v1/chat/completions"
LLM7_MODEL: str    = "openai"


def _to_openai_tool(function_def: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a catalog function definition in the OpenAI tool schema."""
    return {
        "type": "function",
        "function": {
            "name":        function_def["name"],
            "description": function_def["description"],
            "parameters":  function_def["parameters"],
        },
    }


def run_llm7(
    user_query: str,
    function_name: Optional[str] = None,
    functions_dir: Optional[str] = None,
) -> None:
    """
    Send a query to llm7.io with a dynamically selected tool from the
    catalog, handle the tool_call response, and print the final reply.

    If *function_name* is given the matching function is used; otherwise
    the query is matched with the same keyword selector used by run().

    Requires the `requests` package.  Set LLM7_API_KEY (or the env var)
    for authenticated/paid features — free-tier works without a key.
    """
    if _requests is None:
        print("  [!] 'requests' is not installed. Run: pip install requests")
        return

    # ── 1. Resolve the function to expose ────────────────────
    functions = load_functions(functions_dir)
    func_index = {f["name"]: f for f in functions}

    if function_name:
        fn_def = func_index.get(function_name)
        if fn_def is None:
            print(f"  [!] Function '{function_name}' not found in catalog.")
            return
    else:
        fn_def = select_function(user_query, functions)

    if not fn_def:
        print("  [!] Could not select a function for this query.")
        return

    tool = _to_openai_tool(fn_def)

    _hr("=")
    print(f"  [llm7.io]  Query    : {user_query}")
    print(f"  [llm7.io]  Tool sent: {fn_def['name']}")
    _hr("=")

    # ── 2. First call — let the model decide whether to invoke the tool ──
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if LLM7_API_KEY:
        headers["Authorization"] = f"Bearer {LLM7_API_KEY}"

    payload: Dict[str, Any] = {
        "model":       LLM7_MODEL,
        "messages":    [{"role": "user", "content": user_query}],
        "tools":       [tool],
        "tool_choice": "auto",
    }

    try:
        resp = _requests.post(
            LLM7_BASE_URL, headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  [!] Request to llm7.io failed: {exc}")
        return

    message = data["choices"][0]["message"]

    # ── 3. Handle tool_call → supply mock result → get final reply ───────
    if message.get("tool_calls"):
        tool_call = message["tool_calls"][0]
        func_args = json.loads(tool_call["function"].get("arguments", "{}"))

        print(f"  [llm7.io]  Tool call received: {tool_call['function']['name']}")
        print(f"  [llm7.io]  Arguments        : {json.dumps(func_args, indent=2)}")

        # Resolve mock result using the existing handler (or a generic one)
        mock_result = execute_function(fn_def, func_args)

        follow_up: List[Dict[str, Any]] = [
            {"role": "user",      "content": user_query},
            message,
            {
                "role":         "tool",
                "tool_call_id": tool_call["id"],
                "content":      json.dumps(mock_result),
            },
        ]

        try:
            final_resp = _requests.post(
                LLM7_BASE_URL,
                headers=headers,
                json={"model": LLM7_MODEL, "messages": follow_up},
                timeout=30,
            )
            final_resp.raise_for_status()
            final_data = final_resp.json()
        except Exception as exc:
            print(f"  [!] Follow-up request failed: {exc}")
            return

        print("\n  [llm7.io]  Final reply:")
        _hr("·")
        print(f"  {final_data['choices'][0]['message']['content']}")
        _hr("·")
    else:
        # Model answered directly without calling a tool
        print("\n  [llm7.io]  Direct reply (no tool call):")
        _hr("·")
        print(f"  {message['content']}")
        _hr("·")


# ─────────────────────────────────────────────────────────────
# LLM simulation — keyword-based function selector
# ─────────────────────────────────────────────────────────────

# Maps each function name to a set of trigger keywords.
# In a real pipeline this step is performed by the LLM itself.
KEYWORD_MAP: Dict[str, List[str]] = {
    "get_weather":      ["weather", "temperature", "forecast", "rain", "sunny", "humid", "climate", "degrees"],
    "convert_currency": ["currency", "convert", "exchange", "rate", "usd", "eur", "gbp", "money", "dollars", "euros"],
    "get_current_time": ["time", "clock", "hour", "timezone", "what time", "current time", "date"],
    "search_news":      ["news", "headline", "article", "latest", "breaking", "story", "report"],
    "send_email":       ["email", "mail", " send", "compose", "message", "inbox", "recipient"],
    "track_order":      ["order", "track", "delivery", "shipment", "package", "parcel", "shipping"],
    "web_search":       ["search", "find", "look up", "google", "query", "browse", "internet"],
    "create_event":     ["event", "calendar", "schedule", "meeting", "appointment", "book a slot"],
    "book_ride":        ["ride", "taxi", "uber", "cab", "transport", "car", "driver", "pick me up"],
    "play_music":       ["music", "song", "play", "track", "album", "artist", "listen", "spotify"],
    "get_stock_price":  ["stock", "price", "share", "market", "nasdaq", "nyse", "ticker", "equity"],
    "translate_text":   ["translate", "translation", "language", "spanish", "french", "german", "chinese"],
    "set_reminder":     ["remind", "reminder", "alert", "notify", "don't forget", "alarm"],
    "get_directions":   ["directions", "navigate", "route", "how to get", "map", "drive to", "walk to"],
    "summarize_text":   ["summarize", "summary", "tldr", "brief", "shorten", "condense", "key points"],
}


def select_function(
    user_query: str,
    functions: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Simulate an LLM choosing the best function for a given query.

    Scores each function by counting how many of its keywords appear in
    the query string, then returns the highest-scoring match.  Falls back
    to a random selection when no keyword matches are found.
    """
    query_lower = user_query.lower()

    scores: Dict[str, int] = {}
    for func_name, keywords in KEYWORD_MAP.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[func_name] = score

    func_index = {f["name"]: f for f in functions}

    if scores:
        best_match = max(scores, key=lambda k: scores[k])
        return func_index.get(best_match)

    # No keyword match — random fallback (mirrors LLM uncertainty)
    return random.choice(functions)


# ─────────────────────────────────────────────────────────────
# Mock function handlers
# ─────────────────────────────────────────────────────────────

MockHandler = Callable[[Dict[str, Any]], Dict[str, Any]]

MOCK_RESPONSES: Dict[str, MockHandler] = {
    "get_weather": lambda a: {
        "location":    a.get("location", "Unknown"),
        "temperature": 22,
        "unit":        a.get("unit", "celsius"),
        "condition":   "Partly cloudy",
        "humidity":    "65%",
        "wind_speed":  "14 km/h",
        "forecast":    "Mild temperatures expected for the next few days.",
    },
    "convert_currency": lambda a: {
        "amount":           a.get("amount", 0),
        "from":             a.get("from_currency", "USD"),
        "to":               a.get("to_currency", "EUR"),
        "converted_amount": round(float(a.get("amount", 0)) * 0.92, 2),
        "rate":             0.92,
        "timestamp":        "2024-11-01T10:00:00Z",
    },
    "get_current_time": lambda a: {
        "timezone":       a.get("timezone", "UTC"),
        "datetime":       "2024-11-01T10:23:45",
        "unix_timestamp": 1730456625,
        "utc_offset":     "+01:00",
    },
    "search_news": lambda a: {
        "query":   a.get("query", ""),
        "results": [
            {"title": "Major AI breakthrough announced at NeurIPS 2024", "source": "TechCrunch",      "published": "2024-11-01", "url": "https://example.com/1"},
            {"title": "Global markets rally on positive inflation data",  "source": "Reuters",         "published": "2024-11-01", "url": "https://example.com/2"},
            {"title": "Scientists discover new deep-sea species",         "source": "BBC Science",     "published": "2024-10-31", "url": "https://example.com/3"},
            {"title": "Electric vehicle sales hit record high in Europe", "source": "The Guardian",    "published": "2024-10-30", "url": "https://example.com/4"},
            {"title": "Open-source LLM surpasses GPT-4 on benchmarks",   "source": "Hugging Face Blog","published": "2024-10-29", "url": "https://example.com/5"},
        ],
        "total_results": 5,
    },
    "send_email": lambda a: {
        "status":     "sent",
        "to":         a.get("to", "unknown@example.com"),
        "subject":    a.get("subject", "(no subject)"),
        "message_id": "msg_7f3a9c1d4e2b",
        "timestamp":  "2024-11-01T10:23:45Z",
    },
    "track_order": lambda a: {
        "order_id":           a.get("order_id", "N/A"),
        "status":             "In transit",
        "estimated_delivery": "2024-11-03",
        "carrier":            "FedEx",
        "tracking_number":    "274899172985",
        "last_event":         "Package departed Madrid sorting facility at 04:32",
        "origin":             "Valencia, Spain",
        "destination":        "Paris, France",
    },
    "web_search": lambda a: {
        "query":   a.get("query", ""),
        "results": [
            {"rank": 1, "title": "Comprehensive guide to your query",     "url": "https://example.com/r1", "snippet": "An in-depth look at the subject with examples and references."},
            {"rank": 2, "title": "Related information and resources",     "url": "https://example.com/r2", "snippet": "Supporting material, tutorials, and community discussion."},
            {"rank": 3, "title": "Official documentation and standards",  "url": "https://example.com/r3", "snippet": "Formal specification and reference for the topic."},
        ],
        "total_results": 3,
    },
    "create_event": lambda a: {
        "event_id":  "evt_a1b2c3d4e5f6",
        "title":     a.get("title", "New Event"),
        "start":     a.get("start_time", "2024-11-02T09:00:00"),
        "end":       a.get("end_time",   "2024-11-02T10:00:00"),
        "calendar":  a.get("calendar",   "primary"),
        "status":    "confirmed",
        "meet_link": "https://meet.example.com/evt_a1b2c3d4e5f6",
    },
    "book_ride": lambda a: {
        "booking_id":   "ride_x9y8z7w6",
        "pickup":       a.get("pickup_location", "Current location"),
        "destination":  a.get("destination",     "Unknown"),
        "driver":       "Carlos M.",
        "vehicle":      "Toyota Prius · White · MDR-4821",
        "eta_minutes":  4,
        "fare_estimate":"$12.50–$14.00",
        "ride_type":    a.get("ride_type", "economy"),
    },
    "play_music": lambda a: {
        "status":   "playing",
        "track":    a.get("track",    "Random track"),
        "artist":   a.get("artist",   "Unknown Artist"),
        "album":    a.get("album",    "Greatest Hits"),
        "duration": "3:42",
        "service":  a.get("service",  "spotify"),
        "shuffle":  a.get("shuffle",  False),
    },
    "get_stock_price": lambda a: {
        "symbol":         a.get("symbol", "N/A"),
        "price":          182.63,
        "currency":       "USD",
        "change":         "+1.24",
        "change_percent": "+0.68%",
        "market_cap":     "2.87T",
        "volume":         "54,321,000",
        "market":         "NASDAQ",
        "timestamp":      "2024-11-01T20:00:00Z",
    },
    "translate_text": lambda a: {
        "original":           a.get("text", ""),
        "translated":         "[Mock translation of the provided text into the target language.]",
        "from_language":      a.get("from_language", "auto"),
        "detected_language":  "en",
        "to_language":        a.get("to_language",   "es"),
        "confidence":         0.98,
        "character_count":    len(a.get("text", "")),
    },
    "set_reminder": lambda a: {
        "reminder_id": "rem_5e4f3a2b1c0d",
        "message":     a.get("message",    "Reminder"),
        "remind_at":   a.get("remind_at",  "2024-11-02T09:00:00"),
        "recurrence":  a.get("recurrence", "none"),
        "channel":     a.get("channel",    "push"),
        "status":      "scheduled",
    },
    "get_directions": lambda a: {
        "origin":      a.get("origin",      "Current location"),
        "destination": a.get("destination", "Unknown"),
        "mode":        a.get("mode",        "driving"),
        "distance":    "14.3 km",
        "duration":    "22 minutes",
        "steps": [
            "Head north on Calle Gran Vía for 500 m",
            "Turn right onto Paseo de la Castellana",
            "Continue for 2.1 km",
            "Take exit 12 toward the city centre",
            "Arrive at destination on the right",
        ],
    },
    "summarize_text": lambda a: {
        "original_length":  len(a.get("text", "")),
        "summary":          "The provided text discusses key points around the central topic, highlighting the main ideas, supporting arguments, and conclusions reached by the author.",
        "word_count":       32,
        "compression_ratio":"~80%",
        "style":            a.get("style", "paragraph"),
    },
}


# ─────────────────────────────────────────────────────────────
# Argument builder
# ─────────────────────────────────────────────────────────────

# Sample values used when building demo arguments from the schema.
_DEMO_VALUES: Dict[str, Any] = {
    "location":         "Barcelona, Spain",
    "unit":             "celsius",
    "forecast_days":    3,
    "amount":           100,
    "from_currency":    "USD",
    "to_currency":      "EUR",
    "timezone":         "Europe/Madrid",
    "format":           "iso8601",
    "query":            "latest technology news",
    "language":         "en",
    "max_results":      5,
    "to":               "hello@example.com",
    "subject":          "Hello from awesome-function-calling",
    "body":             "This is an automated test message.",
    "is_html":          False,
    "order_id":         "ORD-98765",
    "carrier":          "auto",
    "num_results":      5,
    "safe_search":      True,
    "region":           "US",
    "title":            "Team Sync — Weekly Standup",
    "start_time":       "2024-11-05T10:00:00",
    "end_time":         "2024-11-05T10:30:00",
    "calendar":         "primary",
    "description":      "Weekly sync to discuss project status.",
    "pickup_location":  "1 Plaça de Catalunya, Barcelona",
    "destination":      "Barcelona El Prat Airport",
    "ride_type":        "economy",
    "payment_method":   "card",
    "track":            "Bohemian Rhapsody",
    "artist":           "Queen",
    "album":            "A Night at the Opera",
    "service":          "spotify",
    "shuffle":          False,
    "symbol":           "AAPL",
    "include_history":  False,
    "text":             "The quick brown fox jumps over the lazy dog. This is a sample sentence used to demonstrate the summarize and translate functions.",
    "to_language":      "es",
    "from_language":    "auto",
    "message":          "Buy groceries on the way home",
    "remind_at":        "2024-11-02T18:00:00",
    "recurrence":       "none",
    "channel":          "push",
    "origin":           "Plaça de Catalunya, Barcelona",
    "mode":             "driving",
    "units":            "metric",
    "max_length":       100,
    "style":            "paragraph",
}


def build_demo_args(function_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construct a demo argument dictionary from a function's parameter schema.
    Unknown parameter names receive a generic placeholder string.
    """
    props = function_def.get("parameters", {}).get("properties", {})
    return {key: _DEMO_VALUES.get(key, f"<{key}>") for key in props}


# ─────────────────────────────────────────────────────────────
# Mock executor
# ─────────────────────────────────────────────────────────────

def execute_function(
    function_def: Dict[str, Any],
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Call the mock handler for the given function and return its response.
    If no mock handler is defined, returns a generic success payload.
    """
    if args is None:
        args = build_demo_args(function_def)

    handler = MOCK_RESPONSES.get(function_def["name"])
    if handler:
        return handler(args)

    return {
        "status":  "ok",
        "message": f"Function '{function_def['name']}' executed successfully.",
        "args":    args,
    }


# ─────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────

_W = 62  # display width


def _hr(char: str = "─") -> None:
    print(char * _W)


def _print_function_card(function_def: Dict[str, Any]) -> None:
    """Print a formatted card showing the selected function's metadata."""
    params  = function_def.get("parameters", {})
    props   = params.get("properties", {})
    required = params.get("required", [])

    _hr()
    print(f"  Function   : {function_def['name']}")
    print(f"  Description: {function_def['description']}")
    print(f"  Parameters : {', '.join(props.keys()) or '(none)'}")
    print(f"  Required   : {', '.join(required) or '(none)'}")
    _hr()


def _print_response(response: Dict[str, Any]) -> None:
    """Pretty-print the mock function response."""
    print("\n  Mock response:")
    _hr("·")
    print(json.dumps(response, indent=4, ensure_ascii=False))
    _hr("·")


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def run(user_query: str, functions_dir: Optional[str] = None) -> None:
    """
    End-to-end pipeline: load functions → select → execute → display.

    Args:
        user_query:    A natural-language instruction or question.
        functions_dir: Optional path override for the functions/ directory.
    """
    print(f'\n  Query: "{user_query}"')

    functions = load_functions(functions_dir)

    selected = select_function(user_query, functions)
    if not selected:
        print("  [!] No function could be matched for this query.")
        return

    _print_function_card(selected)
    args     = build_demo_args(selected)
    response = execute_function(selected, args)
    _print_response(response)


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    banner = "  awesome-function-calling — LLM Placeholder Demo"
    print("\n" + "=" * _W)
    print(banner)
    print("=" * _W)

    demo_queries = [
        "What's the weather like in Madrid today?",
        "Convert 250 USD to EUR",
        "Search for the latest news on artificial intelligence",
        "Book me a ride to the airport",
        "Play Bohemian Rhapsody by Queen",
        "What is the current stock price of Apple?",
        "Translate 'good morning' to French",
    ]

    for query in demo_queries:
        run(query)
        print()

    # ── llm7.io live demo (runs only when requests is installed) ─────────
    # Swap the function name below for any name from the functions/ folder.
    # Leave function_name=None to let the keyword selector choose.
    print("\n" + "=" * _W)
    print("  awesome-function-calling — llm7.io Live Demo")
    print("=" * _W)
    print("  (Set LLM7_API_KEY env var for authenticated access.)")
    print()

    run_llm7(
        user_query="What's the weather like in London right now?",
        function_name="get_weather",  # replace with any catalog function name
    )

    print()
    print("=" * _W)
    print("  Demo complete.")
    print("=" * _W + "\n")
