# LLM Provider Landscape for Kirosu

Katsaus LLM-palveluntarjoajiin, joita Kirosu voi hyödyntää.

---

## ☁️ Pilvi-API:t (Hosted)

| Provider | Headless CLI | Mallit | Hinta | Huom. |
|----------|--------------|--------|-------|-------|
| **OpenAI** | `openai api` | gpt-4o, gpt-5.x | $$ | Virallinen API, ei työkaluja CLI:ssä |
| **Anthropic** | `kiro-cli` (wraps) | claude-sonnet-4, claude-haiku-4.5 | $$ | MCP-työkalutuettu |
| **Google Vertex AI** | `gcloud ai` | gemini-2.x | $$ | Vision-tuki |
| **Mistral AI** | `mistral-sdk` | mistral-large, codestral | $ | Eurooppa, GDPR |
| **Cohere** | `cohere generate` | command-r-plus | $ | RAG-optimoitu |
| **Groq** | API | llama-3.x, mixtral | $ | Erittäin nopea (~100 tok/s) |

---

## 🖥️ Paikalliset / Open Source

| Provider | CLI / Integraatio | Mallit | Huom. |
|----------|-------------------|--------|-------|
| **Ollama** | `ollama run` | llama3, mistral, codellama | Helppo asentaa Macille |
| **LM Studio** | GUI + Server | GGUF-kaikki | Erinomainen GUI, REST API |
| **vLLM** | Python API | Kaikki HF-mallit | GPU-palvelimille, nopea |
| **llama.cpp** | CLI | GGUF-mallit | Minimaalinen, C++ |
| **Runpod Serverless** | REST API | Mikä tahansa | Pay-per-request GPU |
| **Together AI** | API | Llama, Mixtral, CodeLlama | Halvempi kuin OpenAI |

---

## 🔧 CLI-Wrapperit (Kuten Kirosu käyttää nyt)

| Wrapperi | Pohjalla | Headless Komento | Erikoisuus |
|----------|----------|------------------|------------|
| **Codex CLI** | OpenAI | `codex exec` | `--oss` tuki Ollamalle! |
| **Kiro-CLI** | Anthropic | `kiro-cli chat --no-interactive` | MCP-työkalut (file, bash) |
| **Aider** | OpenAI/Anthropic | `aider --yes` | Git-integraatio |
| **Continue** | Mikä tahansa | VS Code Extension | IDE-sisäinen |
| **Open Interpreter** | OpenAI | `interpreter --auto_run` | Koodi+Bash suoritus |

---

## 🎯 Erikoistuneet

| Provider | Käyttötapaus | Huom. |
|----------|--------------|-------|
| **Deepgram** | Puhe → Teksti | Whisper-kilpailija |
| **ElevenLabs** | Teksti → Puhe | Realistinen ääni |
| **Hugging Face Inference** | Malli-Hotelli | Tukkuhinta, hidas kylmäkäynnistys |
| **Replicate** | Malli-Hotelli | Pay-per-run, vision-mallit |

---

## 📊 Yhteenveto: Mitä Kirosulle Sopii?

| Tarve | Suositeltu Provider |
|-------|---------------------|
| **Nopea prototyyppi** | Codex / Kiro-CLI (jo valmiina) |
| **Halpa massaskaalaus** | Ollama + Runpod (--oss) |
| **Työkalutuettu (MCP)** | Kiro-CLI (ainoa toimiva nyt) |
| **Eurooppalainen data** | Mistral AI |
| **Offline / Air-gapped** | Ollama + llama.cpp |

---

## Seuraava Askel

Lisää `providers.py`:hin:
1. `OllamaProvider` (suora `ollama run`)
2. `CodexOssProvider` (`codex exec --oss`)
3. `GenericHttpProvider` (OpenAI-yhteensopiva REST)
