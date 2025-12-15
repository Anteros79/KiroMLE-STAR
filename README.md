# MLE-STAR: Machine Learning Engineering Agent via Search and Targeted Refinement

[![Tests](https://img.shields.io/badge/tests-120%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

An implementation of the MLE-STAR framework from the Google DeepMind research paper. MLE-STAR is a multi-agent system that automatically builds machine learning solutions for Kaggle-style competitions.

## 🌟 Overview

MLE-STAR achieves **64% medal rate** on MLE-bench Lite competitions by:

1. **Web Search Integration** - Retrieves state-of-the-art models from the web instead of relying solely on LLM knowledge
2. **Targeted Refinement** - Uses ablation studies to identify and improve the most impactful code components
3. **Intelligent Ensembling** - Combines multiple solutions using LLM-proposed ensemble strategies

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MLE-STAR Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Initial Solution                                       │
│  ┌──────────┐  ┌───────────┐  ┌────────┐  ┌─────────────────┐  │
│  │ Retriever│→ │ Evaluator │→ │ Merger │→ │ Leakage/Usage   │  │
│  │ (Search) │  │           │  │        │  │ Checkers        │  │
│  └──────────┘  └───────────┘  └────────┘  └─────────────────┘  │
│                                                                  │
│  Phase 2: Iterative Refinement (Outer Loop × Inner Loop)        │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Ablation │→ │ Summarizer│→ │ Extractor │→ │ Planner/Coder│  │
│  │ Study    │  │           │  │           │  │ (Inner Loop) │  │
│  └──────────┘  └───────────┘  └───────────┘  └──────────────┘  │
│       ↑                                              │          │
│       └──────────────────────────────────────────────┘          │
│                                                                  │
│  Phase 3: Ensemble                                               │
│  ┌─────────────────┐  ┌───────────┐  ┌────────────┐            │
│  │ Ensemble Planner│→ │ Ensembler │→ │ Submission │            │
│  └─────────────────┘  └───────────┘  └────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/mle-star.git
cd mle-star

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

Set up your environment variables:

```bash
# For web search (optional - falls back to curated models)
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"

# For Ollama (default - local models)
# Make sure Ollama is running: ollama serve
# Pull the model: ollama pull gemma3:27b

# For AWS Bedrock (alternative)
export AWS_REGION="us-east-1"

# For OpenAI (alternative)
export OPENAI_API_KEY="your-api-key"
```

### Running the Pipeline

```python
from mle_star.orchestrator import MLEStarOrchestrator
from mle_star.models.data_models import TaskDescription
from mle_star.models.config import MLEStarConfig

# Define your task
task = TaskDescription(
    description="Binary classification on tabular data to predict customer churn",
    task_type="classification",
    data_modality="tabular",
    evaluation_metric="auc_roc",
    dataset_path="/path/to/data",
)

# Configure the pipeline
config = MLEStarConfig(
    num_retrieved_models=4,
    inner_loop_iterations=4,
    outer_loop_iterations=4,
    ensemble_iterations=5,
)

# Run the pipeline
orchestrator = MLEStarOrchestrator(config=config)
result = orchestrator.run_sync(task)

print(f"Final Score: {result.final_score}")
print(f"Solution:\n{result.final_solution}")
```

### Starting the API Server

```bash
# Start the backend API
python -m uvicorn src.mle_star.api.server:app --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to access the web UI. The frontend will:
- Automatically detect if the backend is available
- Fall back to demo mode if the backend is not running
- Show real-time updates via WebSocket when connected

## 📁 Project Structure

```
mle-star/
├── src/mle_star/
│   ├── agents/           # 14 specialized agents
│   │   ├── retriever.py      # Web search for models
│   │   ├── candidate_evaluator.py
│   │   ├── merger.py
│   │   ├── ablation_study.py
│   │   ├── summarizer.py
│   │   ├── extractor.py
│   │   ├── planner.py
│   │   ├── coder.py
│   │   ├── debugger.py
│   │   ├── ensemble_planner.py
│   │   ├── ensembler.py
│   │   ├── leakage_checker.py
│   │   ├── data_usage_checker.py
│   │   └── submission.py
│   ├── graphs/           # LangGraph-style workflows
│   │   ├── initial_solution.py
│   │   ├── refinement.py
│   │   └── ensemble.py
│   ├── models/           # Data models & config
│   ├── tools/            # Execution & search tools
│   ├── api/              # FastAPI REST server
│   └── orchestrator.py   # Main pipeline coordinator
├── frontend/             # Next.js UI
├── tests/                # 120+ tests
└── EARS_TASK_LIST.md     # Project task tracking
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/property/ -v
```

## 📊 Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_retrieved_models` | 4 | Number of models to retrieve from web search |
| `inner_loop_iterations` | 4 | Refinement iterations per code block |
| `outer_loop_iterations` | 4 | Number of code blocks to refine |
| `ensemble_iterations` | 5 | Ensemble strategy exploration rounds |
| `max_debug_retries` | 3 | Max debugging attempts per error |
| `model_id` | gemma3:27b | LLM model to use |
| `model_provider` | ollama | Model provider (ollama/bedrock/openai) |
| `ollama_base_url` | http://localhost:11434 | Ollama server URL |
| `temperature` | 0.7 | LLM temperature |
| `max_tokens` | 4096 | Max tokens per LLM response |

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pipeline/start` | POST | Start a new pipeline run |
| `/api/pipeline/status` | GET | Get pipeline status |
| `/api/pipeline/pause/{run_id}` | POST | Pause a running pipeline |
| `/api/pipeline/resume/{run_id}` | POST | Resume a paused pipeline |
| `/api/pipeline/stop/{run_id}` | POST | Stop a pipeline |
| `/api/submission/download/{run_id}` | GET | Download submission file |
| `/ws/pipeline/{run_id}` | WebSocket | Real-time updates |

## 🤖 Agent Descriptions

| Agent | Phase | Purpose |
|-------|-------|---------|
| **Retriever** | 1 | Searches web for effective ML models |
| **Candidate Evaluator** | 1 | Evaluates each model candidate |
| **Merger** | 1 | Combines best candidates into ensemble |
| **Leakage Checker** | 1 | Detects and fixes data leakage |
| **Data Usage Checker** | 1 | Ensures all data files are used |
| **Ablation Study** | 2 | Identifies component impacts |
| **Summarizer** | 2 | Parses ablation results |
| **Extractor** | 2 | Finds most impactful code block |
| **Planner** | 2 | Proposes refinement strategies |
| **Coder** | 2 | Implements refinement plans |
| **Debugger** | 2 | Fixes code errors |
| **Ensemble Planner** | 3 | Proposes ensemble strategies |
| **Ensembler** | 3 | Implements ensemble strategies |
| **Submission** | 3 | Generates final submission |

## 📈 Performance

Based on the original research paper:

| Metric | MLE-STAR | AIDE (Baseline) |
|--------|----------|-----------------|
| Any Medal | 63.6% | 25.8% |
| Gold Medal | 30.3% | 12.1% |
| Above Median | 63.6% | 39.4% |

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black src/ tests/

# Type checking
mypy src/

# Run linting
ruff check src/
```

## 📚 References

- [MLE-STAR Paper](https://arxiv.org/abs/...) - Original Google DeepMind research
- [MLE-bench](https://github.com/openai/mle-bench) - Evaluation benchmark
- [Strands Agents SDK](https://github.com/strands-agents/strands-agents) - Agent framework

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.
