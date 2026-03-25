#!/bin/bash
# Start the requirement-follow skill

# Parse arguments
CHAT_ID=""
REQUIREMENT_ID=""
REQUESTER_ID=""
APP_TOKEN=""
TABLE_ID=""
TIMEOUT_HOURS=24

while [[ $# -gt 0 ]]; do
  case $1 in
    --chat-id)
      CHAT_ID="$2"
      shift 2
      ;;
    --requirement-id)
      REQUIREMENT_ID="$2"
      shift 2
      ;;
    --requester-id)
      REQUESTER_ID="$2"
      shift 2
      ;;
    --app-token)
      APP_TOKEN="$2"
      shift 2
      ;;
    --table-id)
      TABLE_ID="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_HOURS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required args
if [[ -z "$CHAT_ID" || -z "$REQUIREMENT_ID" || -z "$REQUESTER_ID" ]]; then
  echo "Usage: $0 --chat-id <id> --requirement-id <id> --requester-id <id> [--app-token <token>] [--table-id <id>] [--timeout <hours>]"
  exit 1
fi

# Export environment variables
export SKILL_CHAT_ID="$CHAT_ID"
export SKILL_REQUIREMENT_ID="$REQUIREMENT_ID"
export SKILL_REQUESTER_ID="$REQUESTER_ID"
export SKILL_APP_TOKEN="$APP_TOKEN"
export SKILL_TABLE_ID="$TABLE_ID"
export SKILL_TIMEOUT_HOURS="$TIMEOUT_HOURS"
export SKILL_TRIGGER_WORDS="生成PRD,完成调研,generate_prd,prd,完成"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting Requirement Follow Skill"
echo "   Chat ID: $CHAT_ID"
echo "   Requirement ID: $REQUIREMENT_ID"
echo "   Timeout: $TIMEOUT_HOURS hours"
echo ""

# Run TypeScript or Python fallback
if command -v ts-node &> /dev/null && [[ -f "$SCRIPT_DIR/../src/index.ts" ]]; then
  cd "$SCRIPT_DIR/.."
  exec ts-node src/index.ts
else
  # Fallback to Python implementation
  echo "⚠️  TypeScript not available, using Python fallback"
  exec python3 "$SCRIPT_DIR/monitor_research_chat.py" \
    --chat-id "$CHAT_ID" \
    --requirement-id "$REQUIREMENT_ID" \
    --requester-id "$REQUESTER_ID" \
    --app-token "$APP_TOKEN" \
    --table-id "$TABLE_ID" \
    --timeout "$TIMEOUT_HOURS"
fi
