#!/bin/bash
# Ralph - Autonomous AI agent loop using Claude Code
# Usage: ./scripts/ralph/ralph.sh [max_iterations]

set -e

MAX_ITERATIONS=${1:-10}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRD_FILE="$PROJECT_ROOT/prd.json"
PROGRESS_FILE="$PROJECT_ROOT/progress.txt"
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"
LOG_DIR="$PROJECT_ROOT/logs"

# Ensure required files exist
if [ ! -f "$PRD_FILE" ]; then
  echo "Error: prd.json not found at $PRD_FILE"
  exit 1
fi

if [ ! -f "$CLAUDE_MD" ]; then
  echo "Error: CLAUDE.md not found at $CLAUDE_MD"
  exit 1
fi

mkdir -p "$LOG_DIR"

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

echo "Starting Ralph - Max iterations: $MAX_ITERATIONS"
echo "Project root: $PROJECT_ROOT"

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "==============================================================="
  echo "  Ralph Iteration $i of $MAX_ITERATIONS"
  echo "==============================================================="

  # Show task status
  TOTAL=$(jq '[.userStories[]] | length' "$PRD_FILE")
  DONE=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE")
  REMAINING=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE")

  if [ "$REMAINING" -eq 0 ]; then
    echo ""
    echo "All tasks already complete!"
    exit 0
  fi

  echo "Progress: $DONE/$TOTAL done, $REMAINING remaining"
  echo ""
  jq -r '.userStories[] | select(.passes == true) | "  ✓ \(.id) — \(.title)"' "$PRD_FILE" 2>/dev/null || true
  echo ""
  echo "Next up:"
  jq -r '[.userStories[] | select(.passes == false)] | sort_by(.priority) | .[0] | "  → \(.id) — \(.title)"' "$PRD_FILE"
  echo ""
  echo "---------------------------------------------------------------"

  # Run Claude Code with streaming JSON output
  # tee saves raw log; jq parses stream to show live activity
  cd "$PROJECT_ROOT"
  LOG_FILE="$LOG_DIR/ralph-iteration-$i.log"

  claude --dangerously-skip-permissions --model opus --print --verbose --output-format stream-json < "$CLAUDE_MD" 2>&1 \
    | tee "$LOG_FILE" \
    | while IFS= read -r line; do
        # Show tool calls as they happen
        TOOL=$(echo "$line" | jq -r '
          select(.type == "assistant")
          | .message.content[]?
          | select(.type == "tool_use")
          | "\(.name): \(.input.command // .input.file_path // .input.pattern // "")"
        ' 2>/dev/null)
        if [ -n "$TOOL" ]; then
          echo "  🔧 $TOOL"
        fi
        # Show text output from Claude
        echo "$line" | jq -r '
          select(.type == "assistant")
          | .message.content[]?
          | select(.type == "text")
          | .text
        ' 2>/dev/null || true
      done || true

  # Check for completion signal
  if grep -q "<promise>COMPLETE</promise>" "$LOG_FILE" 2>/dev/null; then
    echo ""
    echo "Ralph completed all tasks!"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi

  echo ""
  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "Check progress.txt for status."
exit 1
