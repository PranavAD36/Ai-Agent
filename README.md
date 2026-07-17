<div align="center">

# 🤖 Autonomous Code Review & Debugging Agent

**An AI-powered agent that clones a GitHub repository, statically analyzes it, detects bugs with an LLM, generates and validates fixes, writes missing tests, and produces a structured review report — all through an interactive Streamlit dashboard.**

[![GitHub Repo](https://img.shields.io/badge/GitHub-PranavAD36%2FAi--Agent-181717?logo=github)](https://github.com/PranavAD36/Ai-Agent)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Agent%20Framework-LangGraph-1C3C3C)](https://www.langchain.com/langgraph)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![E2B Sandbox](https://img.shields.io/badge/Sandbox-E2B-0A0A0A)](https://e2b.dev/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: Not Specified](https://img.shields.io/badge/License-Not%20Specified-lightgrey)](#-license)

</div>

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Problem It Solves](#-problem-it-solves)
- [How It Works](#-how-it-works)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Docker Deployment](#-docker-deployment)
- [Multi-Provider LLM Failover](#-multi-provider-llm-failover)
- [Reports](#-reports)
- [Testing](#-testing)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [Acknowledgements](#-acknowledgements)
- [License](#-license)
- [Contact](#-contact)

---

## 🧭 Overview

**Ai-Agent** (internally named `code_review_agent`) is an autonomous, LLM-driven code review and debugging system built on **LangGraph**. Given a public GitHub repository URL, the agent clones the project, reads its source files, runs static analysis, uses an LLM to detect logic bugs and security issues, generates candidate fixes, validates those fixes by re-running the test suite inside an isolated **E2B sandbox**, generates unit tests for uncovered code paths, and finally compiles everything into a structured JSON/PDF report — all exposed through a **Streamlit** web dashboard.

The project is organized as a multi-stage pipeline (visible in the codebase as `week3_pipeline.py` and `week4_pipeline.py`), reflecting an iterative build-out of bug detection/fix validation and, later, test-coverage analysis with self-healing test generation.

---

## 🎯 Problem It Solves

Manually reviewing a codebase for bugs, security issues, and missing test coverage is slow and error-prone. This project automates that workflow end-to-end:

- Removes the need to manually run linters/security scanners on every repo.
- Uses an LLM to catch logic-level bugs that static analyzers miss.
- Safely executes untrusted/third-party code and test suites inside a sandbox instead of the host machine.
- Automatically proposes and *validates* fixes rather than just flagging problems.
- Fills test-coverage gaps by generating new unit tests for functions that lack them.
- Produces a single, shareable report (JSON and PDF) summarizing the entire review.

---

## ⚙️ How It Works

The core workflow is defined as a **LangGraph `StateGraph`** (`agent/graph.py`) that passes a shared `AgentState` (`agent/state.py`) through nine sequential nodes:

1. **`clone_repo`** — Clones the target public GitHub repository (`tools/repo_cloner.py`, via GitPython) into a local working directory.
2. **`read_files`** — Reads and chunks source files for the detected project language (`tools/file_reader.py`, `tools/chunker.py`, `tools/language_manager.py`).
3. **`run_static_analysis`** — Runs **Bandit** (security) and **Pylint** (style/quality) over the codebase (`tools/static_analysis.py`, `tools/bandit_tool.py`).
4. **`llm_bug_detection`** — Sends code chunks to an LLM to detect logic bugs beyond what static tools can catch (`tools/bug_detector.py`, `agent/prompts.py`).
5. **`generate_fixes`** — Asks the LLM to produce targeted patches for each detected bug (`tools/fix_generator.py`).
6. **`run_tests`** — Executes the project's `pytest` suite with coverage inside an **E2B** sandbox (`tools/test_runner.py`, `sandbox/e2b_client.py`).
7. **`generate_tests`** — Identifies functions with no test coverage and asks the LLM to write new tests for them, in an iterative "self-healing" loop that re-validates generated tests until they pass or attempts are exhausted (`tools/coverage_analyzer.py`, `tools/iterative_test_loop.py`, `tools/test_generator.py`).
8. **`validate_fixes`** — Applies each proposed fix to a temporary copy of the file and re-validates it inside a Docker/E2B sandbox (`tools/sandbox_validator.py`).
9. **`build_report`** — Aggregates static analysis results, LLM findings, fixes, test results, and generated tests into one structured report, optionally re-running the sandboxed test suite to compute final coverage (`report/report_builder.py`).

All LLM calls are routed through a **provider abstraction layer** (`providers/`, `services/provider_manager.py`, `services/failover_llm.py`) that supports automatic failover and key rotation across multiple Gemini/Groq API keys, with per-provider retry counts, backoff, and cooldown settings defined in `config/llm_config.json`.

---

## ✨ Features

- 🔗 **Repository Ingestion** — Accepts a public GitHub URL, clones it, and validates that the URL is a well-formed GitHub repository link.
- 🌐 **Automatic Language Detection** — Detects whether a repository is Python or JavaScript based on manifest files (`requirements.txt`, `pyproject.toml`, `package.json`) or file-extension counts (`tools/language_manager.py`).
- 🛡️ **Static Analysis** — Runs Bandit for security scanning and Pylint for style/quality checks.
- 🧠 **LLM-Powered Bug Detection** — Detects logic bugs via configurable LLM providers (Gemini, Groq, and optional OpenAI/Anthropic integrations declared in dependencies).
- 🩹 **Automated Fix Generation & Validation** — Generates candidate fixes and validates them by re-running the test suite in an isolated sandbox before accepting them.
- 🧪 **Coverage-Aware Test Generation** — Finds functions lacking test coverage and generates new unit tests in an iterative, self-correcting loop.
- 📦 **Sandboxed Execution** — Runs tests and fix validation inside **E2B** cloud sandboxes (and a Docker image for the sandboxed test environment) to isolate untrusted code from the host.
- 🔁 **Multi-Provider LLM Failover** — Rotates across multiple API keys/providers (Gemini, Groq) with configurable retries, exponential backoff, and cooldown periods.
- 📊 **Structured JSON Report** — Combines all pipeline outputs into a single structured report.
- 📄 **PDF Report Export** — Converts the review report into a formatted PDF via `fpdf` (`report/report_to_pdf.py`, `report/convert_report_to_pdf.py`).
- 🖥️ **Streamlit Dashboard** — Interactive UI to submit a repository URL, track pipeline progress step-by-step, browse results, and view scan history (`report/history.json`).
- 🕒 **Scan History** — Persists past scan results and lets users revisit previous reports from the dashboard.

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.11 |
| Agent Orchestration | LangGraph, LangChain Core |
| LLM Integrations | `langchain-google-genai` (Gemini), `langchain-groq` (Groq), `langchain-openai`, `langchain-anthropic`, `google-generativeai` |
| Sandboxed Execution | E2B SDK (`e2b`, `e2b-code-interpreter`) |
| Repository Handling | GitPython |
| Static/Security Analysis | Bandit, Pylint |
| Testing & Coverage | pytest, pytest-cov, coverage.py |
| Report Generation | fpdf (PDF export), JSON |
| Web UI | Streamlit, pandas |
| Configuration & Validation | python-dotenv, pydantic |
| Terminal Output | rich |
| Containerization | Docker |

---

## 🏗️ Architecture
            ┌────────────────────┐
            │   Streamlit UI     │  (ui/app.py)
            └─────────┬──────────┘
                      │ invokes
            ┌─────────▼──────────┐
            │  LangGraph Pipeline │  (agent/graph.py + agent/state.py)
            └─────────┬──────────┘
┌───────────┬──────────┼───────────┬─────────────┬──────────────┐
▼           ▼          ▼           ▼             ▼              ▼
clone_repo → read_files → static_analysis → llm_bug_detection → generate_fixes
│
▼
run_tests (E2B sandbox) → generate_tests (coverage loop)
│
▼
validate_fixes (sandbox re-check)
│
▼
build_report (JSON + PDF)
LLM calls throughout the pipeline are routed through:
providers/ (Gemini / Groq adapters) → services/provider_manager.py
→ services/failover_llm.py (LangChain-compatible failover chat model)
The agent, tools, providers, and report layers are decoupled: `agent/` orchestrates the workflow, `tools/` implements each discrete capability (cloning, analysis, fix/test generation), `providers/` and `services/` abstract LLM access with failover, `sandbox/` isolates code execution, and `report/` assembles and exports the final output.

---

## 📁 Project Structure

Ai-Agent/
├── Dockerfile                       # Builds and runs the Streamlit UI dashboard
└── code_review_agent/
├── agent/
│   ├── graph.py                 # LangGraph StateGraph wiring all pipeline nodes
│   ├── state.py                 # AgentState TypedDict shared across nodes
│   ├── nodes.py                 # Node function implementations
│   └── prompts.py               # LLM prompt templates
├── tools/
│   ├── repo_cloner.py           # Clones & validates public GitHub repo URLs
│   ├── file_reader.py           # Reads source files from the cloned repo
│   ├── chunker.py               # Splits source files into LLM-sized chunks
│   ├── language_manager.py      # Detects project language (Python/JavaScript)
│   ├── static_analysis.py       # Runs Bandit + Pylint
│   ├── bandit_tool.py           # Bandit security scan wrapper
│   ├── bug_detector.py          # LLM-based logic bug detection
│   ├── fix_generator.py         # LLM-based fix generation
│   ├── sandbox_validator.py     # Applies fixes and validates them in a sandbox
│   ├── test_runner.py           # Runs pytest + coverage inside E2B sandbox
│   ├── testRunner.py            # Legacy/simple test runner helper
│   ├── coverage_analyzer.py     # Finds functions without test coverage
│   ├── test_generator.py        # LLM-based unit test generation
│   ├── iterative_test_loop.py   # Self-healing loop for generated tests
│   ├── dependencyMapper_tool.py # Maps project dependencies
│   ├── code_summarizer.py       # Summarizes code chunks
│   ├── report_generator.py      # Helper for building report sections
│   └── vulnerable.py            # Sample vulnerable code used for testing/demo
├── providers/
│   ├── base_provider.py         # Abstract base class for LLM provider adapters
│   ├── gemini_provider.py       # Google Gemini adapter
│   ├── groq_provider.py         # Groq adapter
│   └── factory.py               # Registers/instantiates provider adapters
├── services/
│   ├── provider_manager.py      # Manages provider health, rotation, and selection
│   └── failover_llm.py          # LangChain-compatible chat model with failover
├── sandbox/
│   └── e2b_client.py            # E2B sandbox wrapper (create, upload, run, cleanup)
├── report/
│   ├── report_builder.py        # Assembles the final structured JSON report
│   ├── report_to_pdf.py         # Converts a report into a formatted PDF
│   ├── convert_report_to_pdf.py # PDF conversion helper/CLI
│   └── history.json             # Persisted scan history used by the UI
├── ui/
│   └── app.py                   # Streamlit dashboard application
├── docker/
│   └── Dockerfile               # Sandbox test-execution image (pytest, coverage, bandit, pylint)
├── config/
│   └── llm_config.json          # Provider list, models, priorities, retry/backoff/cooldown
├── tests/                       # Project test suite and sample fixtures
├── week3_pipeline.py            # Standalone bug-detection → fix → validation pipeline
├── week4_pipeline.py            # Standalone coverage analysis → test generation pipeline
├── run_vulnerable_end_to_end.py # End-to-end demo script
├── .env.example                 # Template for required/optional environment variables
└── requirements.txt              # Python dependencies

---

## ✅ Prerequisites

- **Python 3.11**
- **Git** (required by GitPython for cloning target repositories)
- At least one LLM provider API key: **Gemini** and/or **Groq** (OpenAI/Anthropic packages are also included as dependencies)
- An **E2B** account and API key (required for sandboxed test execution)
- **Docker** (optional, for containerized deployment of the UI, and for the sandbox test-execution image)

---

## 📥 Installation

```bash
# 1. Clone this repository
git clone https://github.com/PranavAD36/Ai-Agent.git
cd Ai-Agent/code_review_agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY_1` | Primary Google Gemini API key |
| `GEMINI_API_KEY_2` | Secondary Gemini API key (used for failover) |
| `GOOGLE_API_KEY` | Backwards-compatible alias for the primary Gemini key |
| `GROQ_API_KEY_1` | Primary Groq API key |
| `GROQ_API_KEY_2` | Secondary Groq API key (used for failover) |
| `GROQ_API_KEY` | Backwards-compatible alias for the primary Groq key |
| `OPENAI_API_KEY` | Optional OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional Anthropic API key |
| `E2B_API_KEY` | Required for sandboxed test execution and fix validation |
| `GITHUB_TOKEN` | Optional GitHub personal access token (for private repos) |
| `LLM_PROVIDER` | Default LLM provider: `gemini` \| `openai` \| `anthropic` |
| `LLM_MODEL` | Default model name (e.g. `gemini-2.0-flash`) |

Provider priority, retry counts, timeouts, backoff, and cooldown behavior for automatic failover are defined in [`config/llm_config.json`](code_review_agent/config/llm_config.json).

---

## ▶️ Usage

### Run the Streamlit Dashboard

```bash
streamlit run ui/app.py
```

Open the local URL Streamlit prints (default `http://localhost:8501`), paste a public GitHub repository URL into the dashboard, and monitor each pipeline stage (cloning, static analysis, bug detection, fix generation, testing, report building) in real time. Past scans are available from the built-in history view.

### Run Standalone Pipeline Scripts

```bash
# Bug detection → fix generation → sandbox validation for a single file
python week3_pipeline.py

# Coverage analysis → self-healing test generation for a single file
python week4_pipeline.py
```

### Run an End-to-End Demo

```bash
python run_vulnerable_end_to_end.py
```

---

## 🐳 Docker Deployment

The root `Dockerfile` builds and serves the Streamlit dashboard:

```bash
# From the repository root
docker build -t ai-code-review-agent .
docker run -p 8501:8501 --env-file code_review_agent/.env ai-code-review-agent
```

The dashboard will be available at `http://localhost:8501`.

A second Dockerfile (`code_review_agent/docker/Dockerfile`) defines the sandbox test-execution image, pre-installing `pytest`, `coverage`, `bandit`, and `pylint` alongside the project's own dependencies, for use by the sandboxed test/validation stages.

---

## 🔁 Multi-Provider LLM Failover

The agent does not depend on a single LLM vendor. `services/provider_manager.py` and `services/failover_llm.py` implement a **LangChain-compatible chat model** that:

- Selects an active provider based on priority order defined in `config/llm_config.json`.
- Automatically rotates between multiple API keys per provider (e.g. two Gemini keys, two Groq keys).
- Retries failed calls with exponential backoff (configurable `retry_count`, `backoff_factor`, `backoff_base`).
- Applies a cooldown period to a provider/key after repeated failures before retrying it again.

This makes the pipeline resilient to individual provider rate limits or outages during a review run.

---

## 📊 Reports

Each review produces:

- A **structured JSON report** (`report/report_builder.py`) combining static analysis results, LLM-detected bugs, suggested fixes, test results, generated tests, and validation outcomes.
- A **PDF export** of the same report (`report/report_to_pdf.py`, `report/convert_report_to_pdf.py`) suitable for sharing outside the dashboard.
- A **persisted scan history** (`report/history.json`) that the Streamlit UI reads to let users revisit prior reviews by repository URL.

---

## 🧪 Testing

The project's own test suite lives under `code_review_agent/tests/`, covering tools, pipeline execution, PDF generation error handling, failover behavior, and polyglot (multi-language) verification:

```bash
cd code_review_agent
pytest
```

---

## 🖼️ Screenshots

> _Add screenshots or a short demo GIF of the Streamlit dashboard here._

| Dashboard Home | Pipeline Progress | Generated Report |
|---|---|---|
| _placeholder_ | _placeholder_ | _placeholder_ |

---

## 🚀 Future Improvements

- Expand automatic static analysis coverage for the JavaScript language path already recognized by `language_manager.py`.
- Add first-class OpenAI and Anthropic provider adapters to the `providers/` factory (currently only Gemini and Groq adapters are registered, though both packages are listed as dependencies).
- Extend the sandboxed pipeline to non-Python ecosystems end-to-end (cloning/detection already supports JavaScript projects).
- Add authentication/rate-limiting to the Streamlit dashboard for multi-user deployments.

---

## 🤝 Contributing

Contributions are welcome. To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Make your changes and add/update tests under `code_review_agent/tests/`.
4. Ensure `pytest` passes locally.
5. Commit your changes and open a Pull Request describing the change.

Please open an issue first for larger changes or new provider integrations so the approach can be discussed.

---

## 🙏 Acknowledgements

This project builds on the following open-source tools and services:

- [LangGraph](https://www.langchain.com/langgraph) & [LangChain](https://www.langchain.com/) for agent orchestration
- [E2B](https://e2b.dev/) for sandboxed code execution
- [Bandit](https://bandit.readthedocs.io/) and [Pylint](https://pylint.readthedocs.io/) for static analysis
- [Streamlit](https://streamlit.io/) for the interactive dashboard
- [GitPython](https://gitpython.readthedocs.io/) for repository cloning
- [pytest](https://docs.pytest.org/) and [coverage.py](https://coverage.readthedocs.io/) for testing and coverage
- [fpdf](https://pyfpdf.github.io/fpdf2/) for PDF report generation

---

## 📄 License

No `LICENSE` file is currently included in this repository. Until one is added, all rights to the source code are reserved by the author. If you are the maintainer and intend for this project to be open source, consider adding a license file (e.g. MIT, Apache-2.0) to clarify usage terms for contributors and users.

---

## 📬 Contact

**Maintainer:** [PranavAD36](https://github.com/PranavAD36)
**Repository:** [github.com/PranavAD36/Ai-Agent](https://github.com/PranavAD36/Ai-Agent)

For bugs, questions, or feature requests, please [open an issue](https://github.com/PranavAD36/Ai-Agent/issues).

---

<div align="center">

Made with 🤖 + ☕ — Autonomous Code Review & Debugging Agent

</div>


            
