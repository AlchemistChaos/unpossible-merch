#!/bin/bash
# Ralph - Autonomous AI agent loop using Claude Code
# Usage: ./scripts/ralph/ralph.sh [max_iterations]

set -e

MAX_ITERATIONS=${1:-10}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRD_FILE="$PROJECT_ROOT/prd.json"
PROGRESS_FILE="$PROJECT_ROOT/progress.txt"
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"

# Ensure required files exist
if [ ! -f "$PRD_FILE" ]; then
  echo "Error: prd.json not found at $PRD_FILE"
  exit 1
fi

if [ ! -f "$CLAUDE_MD" ]; then
  echo "Error: CLAUDE.md not found at $CLAUDE_MD"
  exit 1
fi

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

  # Check if all tasks are done before running
  REMAINING=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE")
  if [ "$REMAINING" -eq 0 ]; then
    echo ""
    echo "All tasks already complete!"
    exit 0
  fi
  echo "Remaining tasks: $REMAINING"

  # Run Claude Code with the CLAUDE.md prompt
  cd "$PROJECT_ROOT"
  # Use Opus model via Bedrock for maximum capability
  OUTPUT=$(claude --dangerously-skip-permissions --model opus --print < "$CLAUDE_MD" 2>&1 | tee /dev/stderr) || true

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Ralph completed all tasks!"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "Check progress.txt for status."
exit 1
