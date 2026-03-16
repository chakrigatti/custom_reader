#!/usr/bin/env bash
#
# Run all Reader services: API server, UI, API docs (Swagger), man pages.
#
# Usage:
#   ./run.sh              Start all servers (production mode)
#   ./run.sh --dev        Start all servers with hot-reload on file changes
#   ./run.sh api          Start only the API server
#   ./run.sh ui           Start only the UI server
#   ./run.sh docs         Start only the API docs server
#   ./run.sh man          Start only the man pages server
#   ./run.sh stop         Stop all running servers
#   ./run.sh --dev api ui Start selected servers in dev mode
#
# Ports (override with environment variables):
#   API_PORT    (default: 8000)
#   UI_PORT     (default: 5173)
#   DOCS_PORT   (default: 8080)
#   MAN_PORT    (default: 8081)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Use python3 explicitly (python may point to Python 2)
PYTHON="$(command -v python3 || command -v python)"

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"
DOCS_PORT="${DOCS_PORT:-8080}"
MAN_PORT="${MAN_PORT:-8081}"

DEV_MODE=false
SERVICES=()

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --dev|-d) DEV_MODE=true ;;
        stop)
            # Stop servers from a previous run and exit
            PIDFILE="$ROOT/.reader-pids"
            if [ -f "$PIDFILE" ]; then
                echo "Stopping servers..."
                while read -r pid; do
                    kill "$pid" 2>/dev/null || true
                done < "$PIDFILE"
                sleep 1
                while read -r pid; do
                    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
                done < "$PIDFILE"
                rm -f "$PIDFILE"
                echo "All servers stopped."
            else
                echo "No running servers found."
            fi
            exit 0
            ;;
        api|ui|docs|man) SERVICES+=("$arg") ;;
        --help|-h)
            sed -n '3,/^$/p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--dev] [api] [ui] [docs] [man]" >&2
            exit 1
            ;;
    esac
done

# Default: run all services
if [ ${#SERVICES[@]} -eq 0 ]; then
    SERVICES=(api ui docs man)
fi

PIDS=()
PIDFILE="$ROOT/.reader-pids"

# Stop servers from a previous run of this script (using saved PID file)
stop_previous() {
    if [ -f "$PIDFILE" ]; then
        echo "Stopping servers from previous run..."
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PIDFILE"
        sleep 1
        # Force-kill any that didn't exit gracefully
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        done < "$PIDFILE"
        rm -f "$PIDFILE"
        echo "Previous servers stopped."
    fi
}

save_pids() {
    printf '%s\n' "${PIDS[@]}" > "$PIDFILE"
}

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    rm -f "$PIDFILE"
    echo "All servers stopped."
}

trap cleanup EXIT INT TERM

want() {
    local svc="$1"
    for s in "${SERVICES[@]}"; do
        [ "$s" = "$svc" ] && return 0
    done
    return 1
}

# Stop any servers started by a previous run of this script
stop_previous
echo ""

# --- API Server ---
if want api; then
    echo "Starting API server on http://localhost:${API_PORT}"
    if [ "$DEV_MODE" = true ]; then
        uvicorn reader.server:app --host 0.0.0.0 --port "$API_PORT" --reload \
            --reload-dir "$ROOT/src" &
    else
        uvicorn reader.server:app --host 0.0.0.0 --port "$API_PORT" &
    fi
    PIDS+=($!)
fi

# --- UI Server ---
if want ui; then
    if [ "$DEV_MODE" = true ]; then
        echo "Starting UI dev server on http://localhost:${UI_PORT}"
        cd "$ROOT/ui"
        npx vite --port "$UI_PORT" --host &
        PIDS+=($!)
        cd "$ROOT"
    else
        # In production mode, build the UI and let FastAPI serve it from /static
        if [ ! -f "$ROOT/static/index.html" ]; then
            echo "Building UI..."
            cd "$ROOT/ui"
            npm run build
            cd "$ROOT"
        fi
        echo "UI served by API server at http://localhost:${API_PORT}/static/index.html"
    fi
fi

# --- API Docs (Swagger UI) ---
if want docs; then
    echo "Starting API docs on http://localhost:${DOCS_PORT}"
    "$PYTHON" -m http.server "$DOCS_PORT" --directory "$ROOT/docs/api" &
    PIDS+=($!)
fi

# --- Man Pages Server ---
if want man; then
    echo "Starting man pages on http://localhost:${MAN_PORT}"
    "$PYTHON" "$ROOT/docs/cli/server.py" "$MAN_PORT" &
    PIDS+=($!)
fi

# Save PIDs so a future run can stop these servers
save_pids

# Summary
echo ""
echo "=== Reader Services ==="
if [ "$DEV_MODE" = true ]; then
    echo "  Mode:      DEVELOPMENT (hot-reload enabled)"
else
    echo "  Mode:      PRODUCTION"
fi
want api  && echo "  API:       http://localhost:${API_PORT}"
want ui   && {
    if [ "$DEV_MODE" = true ]; then
        echo "  UI (dev):  http://localhost:${UI_PORT}"
    else
        echo "  UI:        http://localhost:${API_PORT}/static/index.html"
    fi
}
want docs && echo "  API Docs:  http://localhost:${DOCS_PORT}"
want man  && echo "  Man Pages: http://localhost:${MAN_PORT}"
echo ""
echo "Press Ctrl+C to stop all servers."
echo ""

# Wait for all background processes
wait
