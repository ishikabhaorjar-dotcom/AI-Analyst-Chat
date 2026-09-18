# 📊 AI Data Analyst Agent

**Upload your data. Ask anything. Let AI analyze it.**

An agentic data-analysis app: upload a CSV/Excel file and an AI agent profiles it, runs automated EDA, answers natural-language questions by *actually executing* pandas code (never guessing numbers), generates interactive Plotly visualizations, and produces a downloadable PDF report — all through a LangGraph agent pipeline with structured, validated outputs.

This is not a wrapper around a single LLM call. It's a multi-node agent that plans, executes, self-repairs on failure, and explains — with every quantitative claim traceable back to real, executed code.

---

## Why this project is different

Most "AI + data" portfolio projects either:
- hard-code a chatbot over a static prompt, or
- let the LLM guess numbers from a few sample rows (and hallucinate).

This project instead separates **reasoning** from **calculation**:

```
User question
      │
      ▼
 Planner Agent  ──── classifies the request (profile / calculation / insight)
      │
      ▼
Pandas Code Agent ── LLM writes a pandas snippet
      │
      ▼
Sandboxed Executor ─ code runs against the REAL dataframe, in an isolated
      │                process, with a hard timeout and a blocked builtin set
      ▼
   Actual Result  ── a real number/DataFrame, not a guess
      │
      ▼
 Insight Agent  ──── LLM explains the real result in plain language
```

If the generated code fails, the agent is shown its own error and asked to fix it — one self-repair pass — before falling back to an honest "I couldn't compute this" rather than a hallucinated answer.

---

## Features

- 📥 **Robust upload** — CSV/Excel, multiple encodings, multi-sheet Excel handling, file-size/type validation
- 🧬 **Automatic dataset profiling** — row/column counts, missing values, duplicates, column-role detection (numerical / categorical / date / identifier)
- 🔬 **Automated EDA** — correlation analysis, outlier detection (z-score), category distributions, time trends, descriptive statistics
- 💬 **Natural-language Q&A** — ask questions in plain English; answers come from real executed pandas code
- 🕵️ **Visible agent trace** — see each step the agent took (planned → executed → explained)
- 📈 **Interactive Plotly visualizations** — bar, line, scatter, histogram, box, heatmap, pie
- 🧾 **Structured outputs** — every agent response is validated against a Pydantic schema before it reaches the UI
- 📄 **One-click PDF report** — dataset overview, data quality, correlations, insights, and recommendations
- 🖥️ **Modern dashboard UI** — sidebar navigation, metric cards, insight cards, dark sidebar theme

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit + custom CSS |
| Agent orchestration | LangGraph |
| LLM | Groq API (Llama 3.3 70B) |
| Structured output | Pydantic |
| Data | Pandas, NumPy |
| Visualization | Plotly |
| Reports | ReportLab |
| Sandboxed execution | Python `multiprocessing` + AST-level static checks |

---

## Project Structure

```
ai-data-analyst-agent/
├── app.py                    # Streamlit entry point (routing only)
├── config/settings.py        # all configuration in one place
├── src/
│   ├── core/                 # loader, profiler, sandboxed executor
│   ├── llm/                  # Groq client wrapper, prompt templates
│   ├── agents/                # LangGraph state, nodes, graph wiring
│   ├── tools/                 # pandas tool, EDA tool, Plotly viz tool
│   ├── schemas/                # Pydantic models for structured output
│   └── reports/                # PDF report generator
├── ui/
│   ├── views/                  # one file per sidebar page
│   ├── components/             # sidebar, metric cards, agent status
│   └── styles/custom.css       # premium SaaS-style theme
├── data/samples/sample_sales.csv
└── tests/test_profiler.py
```

---

## Getting Started

```bash
git clone <your-repo-url>
cd ai-data-analyst-agent

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then add your free Groq API key (console.groq.com) to .env

streamlit run app.py
```

No dataset handy? Click **"Load sample sales dataset"** on the dashboard to try it immediately.

### Run tests

```bash
pytest tests/ -v
```

The test suite covers the deterministic parts of the pipeline (loading, profiling, the execution sandbox) that don't require an API key.

---

## Safety Notes on Code Execution

The app executes LLM-generated Python. That's inherently risky, so `src/core/executor.py`:
- runs every snippet in an **isolated subprocess**, never the main process
- statically rejects `import`, file I/O, `eval`/`exec`, and dunder access via AST inspection *before* running anything
- enforces a **hard timeout** (8s) and kills runaway processes
- exposes only `pd`, `np`, and the dataframe — nothing else

This is treated as a security-relevant module; see the file's docstring before modifying it.

---

## Roadmap Ideas

- Multi-turn conversation memory (follow-up questions referencing prior results)
- DuckDB backend for datasets too large for in-memory pandas
- Support for joining multiple uploaded files
- Auth + per-user session persistence for a hosted deployment

---

## Author

Built by **Ishika** as part of a Data Science / AI-ML portfolio, demonstrating agentic architecture, tool calling, sandboxed code execution, and structured LLM outputs — deliberately distinct from a RAG-based Q&A project.
