#!/bin/bash
# =============================================================================
# Heracles Session ID Generator
# =============================================================================
# Generates and manages session IDs for Heracles workflows.
# 
# IMPORTANT: Session ID persistence is managed by the LLM agent through
# conversation memory, NOT through environment detection. The agent must:
# 1. Generate a session ID at workflow start using this script
# 2. Remember the ID across messages (conversation memory)
# 3. Mention the ID at the end of each message to ensure persistence
#
# This approach is more reliable than environment-based detection because
# multiple agents in the same IDE window share the same environment.
#
# Usage:
#   ./get-session-id.sh generate [feature-slug]  # Generate new session ID
#   ./get-session-id.sh validate <session-id>    # Validate session ID format
#   ./get-session-id.sh exists <session-id>      # Check if session exists
#   ./get-session-id.sh list                     # List all sessions
#   ./get-session-id.sh ide                      # Get IDE name (for info only)
# =============================================================================

# Generate a new unique session ID
# Format: YYYYMMDD-HHMMSS-{feature_slug}-{random}
# Args: $1 = optional feature slug (will be sanitized)
generate_session_id() {
    local feature_slug="${1:-session}"
    
    # Sanitize feature slug: lowercase, replace spaces/special chars with dashes
    feature_slug=$(echo "$feature_slug" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | head -c 30)
    
    # Ensure we have a slug
    if [ -z "$feature_slug" ]; then
        feature_slug="session"
    fi
    
    # Generate timestamp + random suffix for uniqueness
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local random_suffix=$(head -c 2 /dev/urandom | xxd -p)
    
    echo "${timestamp}-${feature_slug}-${random_suffix}"
}

# Validate session ID format
# Returns 0 if valid, 1 if invalid
validate_session_id() {
    local session_id="$1"
    
    if [ -z "$session_id" ]; then
        echo "Error: No session ID provided" >&2
        return 1
    fi
    
    # Check format: YYYYMMDD-HHMMSS-slug-xxxx
    if echo "$session_id" | grep -qE '^[0-9]{8}-[0-9]{6}-[a-z0-9-]+-[a-f0-9]{4}$'; then
        echo "valid"
        return 0
    else
        echo "invalid" >&2
        return 1
    fi
}

# Check if a session directory exists
# Returns 0 if exists, 1 if not
session_exists() {
    local session_id="$1"
    local session_dir=".heracles/sessions/${session_id}"
    
    if [ -d "$session_dir" ]; then
        echo "exists"
        return 0
    else
        echo "not_found"
        return 1
    fi
}

# List all existing sessions
list_sessions() {
    local sessions_dir=".heracles/sessions"
    
    if [ ! -d "$sessions_dir" ]; then
        echo "No sessions found"
        return 0
    fi
    
    local found=0
    for session_dir in "$sessions_dir"/*/; do
        if [ -d "$session_dir" ]; then
            local session_id=$(basename "$session_dir")
            local state_file="${session_dir}WORKFLOW_STATE.md"
            local status="unknown"
            local step="?"
            
            if [ -f "$state_file" ]; then
                status=$(grep -oP '(?<=status: )\w+' "$state_file" 2>/dev/null || echo "unknown")
                step=$(grep -oP '(?<=current_step: )\w+' "$state_file" 2>/dev/null || echo "?")
            fi
            
            echo "$session_id | status: $status | step: $step"
            found=1
        fi
    done
    
    if [ "$found" -eq 0 ]; then
        echo "No sessions found"
    fi
}

# Get IDE name for display (informational only)
get_ide_name() {
    if [ -n "$CURSOR_TRACE_ID" ] || [ -n "$CURSOR_AGENT" ]; then
        echo "Cursor"
    elif [ -n "$VSCODE_IPC_HOOK_CLI" ] || [ -n "$VSCODE_IPC_HOOK" ]; then
        echo "VSCode"
    elif [ -n "$CLAUDE_ENV_FILE" ] || [ "$TERM_PROGRAM" = "claude" ]; then
        echo "Claude Code"
    elif [ -n "$OPENCODE_SESSION_ID" ]; then
        echo "OpenCode"
    else
        echo "Terminal"
    fi
}

# =============================================================================
# Main - When executed directly
# =============================================================================

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    case "${1:-}" in
        "generate"|"gen"|"new")
            generate_session_id "${2:-}"
            ;;
        "validate"|"check")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 validate <session_id>" >&2
                exit 1
            fi
            validate_session_id "$2"
            ;;
        "exists")
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 exists <session_id>" >&2
                exit 1
            fi
            session_exists "$2"
            ;;
        "list"|"ls")
            list_sessions
            ;;
        "ide"|"name")
            get_ide_name
            ;;
        ""|"help"|"-h"|"--help")
            echo "Heracles Session ID Generator"
            echo ""
            echo "Usage: $0 <command> [args]"
            echo ""
            echo "Commands:"
            echo "  generate [slug]     Generate new session ID with optional feature slug"
            echo "  validate <id>       Check if session ID format is valid"
            echo "  exists <id>         Check if session directory exists"
            echo "  list                List all existing sessions"
            echo "  ide                 Show detected IDE name"
            echo ""
            echo "Examples:"
            echo "  $0 generate auth-feature    # 20260124-183045-auth-feature-a1b2"
            echo "  $0 validate 20260124-183045-auth-feature-a1b2"
            echo "  $0 list"
            echo ""
            echo "Note: Session ID persistence is managed by the LLM agent through"
            echo "conversation memory, not through this script."
            ;;
        *)
            echo "Unknown command: $1" >&2
            echo "Run '$0 help' for usage" >&2
            exit 1
            ;;
    esac
fi
