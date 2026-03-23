# meso_negotiator

Meso-level negotiation assistant that generates equal-utility offer cards using MAUT, Boulware concession curves, and opponent preference learning. Built for the Kood/Jobfair Pactum challenge.

## Prerequisites

- [mise](https://mise.jdx.dev/) (manages Python 3.12, Node 22, and task runner)

## Setup

```sh
mise trust
mise install
mise run setup        # installs Python + Node dependencies
```

### Windows

Most tasks (`setup`, `lint`, `test`, `format`, `typecheck`, `check`) work natively on Windows. The `dev` and `dev:stop` tasks require bash (Git Bash or WSL).

To start servers manually on Windows:

```powershell
uv run uvicorn back.server:create_app --factory --port 8000
# in a separate terminal:
cd front; npx vite --port 5173
```

## Running

### Docker

```sh
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Local dev servers

```sh
mise run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

To stop:

```sh
mise run dev:stop
```

The backend seeds a demo negotiation automatically. After reaching a terminal state (deal agreed or no deal), use the "Reset demo" button to start over.

## Commands

| Command | Description |
|---|---|
| `mise run dev` | Start backend + frontend dev servers |
| `mise run dev:stop` | Stop both dev servers |
| `mise run setup` | Install all dependencies (Python + Node) |
| `mise run test` | Run pytest |
| `mise run lint` | Run all linters (ruff + biome) |
| `mise run lint:fix` | Auto-fix lint issues |
| `mise run format` | Auto-format all files |
| `mise run typecheck` | Run mypy + tsc |
| `mise run check` | Lint + test |

## Stack

- **Backend** -- Python 3.12, FastAPI, clean architecture (domain/application/infrastructure)
- **Frontend** -- React 19, TypeScript, Tailwind CSS, Vite
- **Linting** -- ruff (Python), biome (JS/TS)
- **Testing** -- pytest (unit + BDD + API integration)
