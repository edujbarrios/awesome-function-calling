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
