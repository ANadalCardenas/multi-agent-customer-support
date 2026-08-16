# Multi-Agent Customer Support

A multi-agent customer support system built with LangGraph. It handles support tickets for CultPass, a cultural experiences subscription app. A supervisor agent reads each ticket and routes it to one of four specialized agents. Each agent can resolve the ticket or escalate it to a human.

## Project Structure

- `data/models/`: SQLAlchemy models for the two databases (`cultpass.py`, `udahub.py`).
- `data/external/`: CultPass data (`cultpass.db`, users, experiences, and knowledge base articles).
- `data/core/`: Udahub data (`udahub.db`, tickets, accounts, and knowledge base).
- `agentic/agents/`: the 4 specialized agents.
- `agentic/tools/`: tools used by the agents (database access, knowledge search, escalation, memory).
- `agentic/workflow.py`: the LangGraph orchestration graph, including the supervisor.
- `agentic/design/`: architecture documentation.
- `agentic/logs/`: structured logs written while the system runs.
- `tests/`: automated tests (pytest).
- `01_external_db_setup.ipynb`, `02_core_db_setup.ipynb`: notebooks to set up both databases.
- `03_agentic_app.ipynb`: notebook to run the system, including sample ticket demos.

## Getting Started

### Dependencies

- Python 3.12.3
- See `requirements.txt` for all packages.

### Installation

1. Create a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your OpenAI API key (and, if you use a Vocareum key, the base URL it gave you):
   ```
   cp .env.example .env
   ```

### Setup

Run these notebooks once, in order, to create both databases:

1. `01_external_db_setup.ipynb`: creates `cultpass.db` with users, experiences, subscriptions, and reservations.
2. `02_core_db_setup.ipynb`: creates `udahub.db` with the account, the knowledge base, and a sample ticket.

### Running the App

Open `03_agentic_app.ipynb`. It:

- Loads the orchestrator from `agentic/workflow.py`.
- Runs an interactive chat with `chat_interface`.
- Includes 3 sample tickets that show the system resolving a request through the knowledge, reservation, and subscription agents, without escalating.

## Testing

Run the test suite from the project root:

```
pytest
```

The tests cover the 9 tools (database access, knowledge search, escalation, memory) and the structured logging. They run against the real `cultpass.db` and `udahub.db` files and clean up after themselves. They require no API key, so they also run in CI on every push (see `.github/workflows/tests.yml`).

## Running with Docker

The project ships with a `Dockerfile` and `docker-compose.yml` covering two independent use cases. Neither one runs the notebooks automatically — pick the one you need.

**Run the automated tests** (no `.env` needed, this is also what CI runs):

```
docker compose run --rm tests
```

This builds the image, runs `pytest` inside the container, and prints the results to your terminal. Nothing stays running afterwards.

**Explore the notebooks interactively** (requires a `.env` file, see `.env.example`):

```
docker compose up app
```

This starts a Jupyter Lab *server* inside the container, exposed at [http://localhost:8888](http://localhost:8888). Open that URL, then open and run `03_agentic_app.ipynb` yourself, cell by cell, exactly as you would locally — the container just saves you from installing Python/dependencies on your machine. It does not execute any notebook or open any output on its own.

## Architecture

See `agentic/design/README.md` for the full architecture: the graph diagram, the role of each agent, routing logic, knowledge retrieval, memory, and logging.

## Built With

- [LangGraph](https://www.langchain.com/langgraph): the orchestration graph.
- [LangChain](https://www.langchain.com/): agent and tool framework.
- [FastMCP](https://gofastmcp.com/): MCP server for the subscription status tool.
- [SQLAlchemy](https://www.sqlalchemy.org/): database models and queries.
- [scikit-learn](https://scikit-learn.org/): TF-IDF search for the knowledge base.
- [pytest](https://pytest.org/): automated tests.
- [Docker](https://www.docker.com/): containerized tests and app.

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
