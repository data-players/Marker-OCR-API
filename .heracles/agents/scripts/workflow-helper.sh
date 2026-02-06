#!/bin/bash
# =============================================================================
# Workflow Helper - Fonctions utilitaires pour le workflow Heracles
# =============================================================================
# Usage: source .heracles/agents/scripts/workflow-helper.sh
# =============================================================================

set -e

# Determine script directory for sourcing
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the session ID detection script
if [ -f "${SCRIPT_DIR}/get-session-id.sh" ]; then
    source "${SCRIPT_DIR}/get-session-id.sh"
elif [ -f ".heracles/agents/scripts/get-session-id.sh" ]; then
    source ".heracles/agents/scripts/get-session-id.sh"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# PATHS & CONSTANTS
# =============================================================================

HERACLES_CONFIG_DIR=".heracles"
SESSIONS_DIR="${HERACLES_CONFIG_DIR}/sessions"
# Framework is now in .heracles/agents/ (scripts are in .heracles/agents/scripts/)
HERACLES_DIR="${SCRIPT_DIR}/.."
TEMPLATES_DIR="${HERACLES_DIR}/templates"

# Legacy support - will be removed in future versions
CURRENT_SESSION_FILE="${HERACLES_CONFIG_DIR}/current_session"

# =============================================================================
# LOGGING
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

# Generate unique session ID
generate_session_id() {
    local feature_slug="$1"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    
    if [ -n "$feature_slug" ]; then
        # Slugify the feature name
        local slug=$(echo "$feature_slug" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//' | head -c 30)
        echo "${timestamp}-${slug}"
    else
        echo "${timestamp}-session"
    fi
}

# Get current timestamp in ISO format
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Get current session ID for this IDE instance
# Priority: 1. IDE-linked session, 2. Legacy current_session file
get_current_session() {
    # 1. Try to find session linked to current IDE instance
    if type find_session_for_ide &>/dev/null; then
        local ide_session=$(find_session_for_ide)
        if [ -n "$ide_session" ]; then
            echo "$ide_session"
            return 0
        fi
    fi
    
    # 2. Legacy fallback: check current_session file
    if [ -f "$CURRENT_SESSION_FILE" ]; then
        cat "$CURRENT_SESSION_FILE"
        return 0
    fi
    
    echo ""
}

# Set current session and link to IDE
set_current_session() {
    local session_id="$1"
    mkdir -p "$HERACLES_CONFIG_DIR"
    
    # Link session to current IDE instance
    if type link_session_to_ide &>/dev/null; then
        link_session_to_ide "$session_id"
        log_success "Session linked to $(get_ide_name 2>/dev/null || echo 'IDE'): $session_id"
    else
        # Legacy fallback
        echo "$session_id" > "$CURRENT_SESSION_FILE"
        log_success "Session active: $session_id"
    fi
}

# Get session state file path
get_state_file() {
    local session_id="${1:-$(get_current_session)}"
    echo "${SESSIONS_DIR}/${session_id}/WORKFLOW_STATE.md"
}

# Get session directory path
get_session_dir() {
    local session_id="${1:-$(get_current_session)}"
    echo "${SESSIONS_DIR}/${session_id}"
}

# Check if session exists
session_exists() {
    local session_id="$1"
    [ -d "${SESSIONS_DIR}/${session_id}" ] && [ -f "${SESSIONS_DIR}/${session_id}/WORKFLOW_STATE.md" ]
}

# List all sessions
list_sessions() {
    if [ ! -d "$SESSIONS_DIR" ]; then
        log_warning "No sessions found"
        return
    fi
    
    echo ""
    echo "=========================================="
    echo "         WORKFLOW SESSIONS"
    echo "=========================================="
    echo ""
    
    local current=$(get_current_session)
    local current_ide_id=""
    if type get_ide_session_id &>/dev/null; then
        current_ide_id=$(get_ide_session_id)
    fi
    
    for session_dir in "$SESSIONS_DIR"/*/; do
        if [ -d "$session_dir" ]; then
            local session_id=$(basename "$session_dir")
            local state_file="${session_dir}WORKFLOW_STATE.md"
            local ide_link_file="${session_dir}.ide_session"
            
            if [ -f "$state_file" ]; then
                local phase=$(grep -oP 'current_phase: `\K[^`]+' "$state_file" 2>/dev/null || echo "unknown")
                local feature=$(grep -oP 'feature_description: \K.*' "$state_file" 2>/dev/null | head -c 40 || echo "")
                
                # Check if this session is linked to current IDE
                local is_current=false
                local linked_ide=""
                if [ -f "$ide_link_file" ]; then
                    linked_ide=$(cat "$ide_link_file")
                    if [ "$linked_ide" = "$current_ide_id" ]; then
                        is_current=true
                    fi
                fi
                
                if [ "$is_current" = true ]; then
                    echo -e "  ${GREEN}► $session_id${NC} (this IDE)"
                elif [ -n "$linked_ide" ]; then
                    echo -e "  ${YELLOW}● $session_id${NC} (other IDE)"
                else
                    echo "    $session_id"
                fi
                echo "      Phase: $phase"
                [ -n "$feature" ] && echo "      Feature: $feature..."
                echo ""
            fi
        fi
    done
    
    echo "=========================================="
    echo ""
    if type get_ide_name &>/dev/null; then
        echo "Current IDE: $(get_ide_name)"
    fi
}

# Create new session
create_session() {
    local feature_description="$1"
    
    if [ -z "$feature_description" ]; then
        log_error "Feature description required"
        return 1
    fi
    
    local session_id=$(generate_session_id "$feature_description")
    local session_dir="${SESSIONS_DIR}/${session_id}"
    
    # Create session directory structure
    mkdir -p "${session_dir}/specs"
    mkdir -p "${session_dir}/review-reports"
    mkdir -p "${session_dir}/logs"
    
    # Copy and fill template
    local template="${TEMPLATES_DIR}/WORKFLOW_STATE.template.md"
    local state_file="${session_dir}/WORKFLOW_STATE.md"
    
    if [ -f "$template" ]; then
        local timestamp=$(get_timestamp)
        local feature_slug=$(echo "$feature_description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | head -c 30)
        local feature_num=$(get_next_feature_id)
        
        # Copy and replace placeholders
        sed -e "s/{SESSION_ID}/${session_id}/g" \
            -e "s/{STARTED_AT}/${timestamp}/g" \
            -e "s/{UPDATED_AT}/${timestamp}/g" \
            -e "s/{FEATURE_ID}/${feature_num}/g" \
            -e "s/{FEATURE_DESCRIPTION}/${feature_description}/g" \
            -e "s/{FEATURE_SLUG}/${feature_slug}/g" \
            -e "s/{ISSUE_NUMBER}/null/g" \
            -e "s/{BRANCH_NAME}/feature\/${feature_num}-${feature_slug}/g" \
            -e "s/{CURRENT_PHASE}/init/g" \
            -e "s/{CURRENT_STEP}/starting/g" \
            -e "s/{LOOP_COUNT}/0/g" \
            "$template" > "$state_file"
    else
        log_error "Template not found: $template"
        return 1
    fi
    
    # Set as current session
    set_current_session "$session_id"
    
    log_success "Session created: $session_id"
    echo "$session_id"
}

# Switch to another session
switch_session() {
    local session_id="$1"
    
    if session_exists "$session_id"; then
        set_current_session "$session_id"
        log_success "Switched to session: $session_id"
    else
        log_error "Session not found: $session_id"
        return 1
    fi
}

# Archive completed session
archive_session() {
    local session_id="${1:-$(get_current_session)}"
    local session_dir=$(get_session_dir "$session_id")
    
    if [ -d "$session_dir" ]; then
        # Unlink from IDE before archiving
        if type unlink_session_from_ide &>/dev/null; then
            unlink_session_from_ide "$session_id"
        fi
        
        # Create archive directory
        mkdir -p "${SESSIONS_DIR}/archived"
        
        # Move to archive
        mv "$session_dir" "${SESSIONS_DIR}/archived/${session_id}"
        
        # Legacy cleanup: remove current_session file if it points to this session
        if [ -f "$CURRENT_SESSION_FILE" ]; then
            local legacy_current=$(cat "$CURRENT_SESSION_FILE")
            if [ "$legacy_current" = "$session_id" ]; then
                rm -f "$CURRENT_SESSION_FILE"
            fi
        fi
        
        log_success "Session archived: $session_id"
    else
        log_error "Session not found: $session_id"
        return 1
    fi
}

# =============================================================================
# FEATURE MANAGEMENT
# =============================================================================

# Get next feature ID (auto-increment)
get_next_feature_id() {
    local max_id=0
    
    # Check existing sessions
    if [ -d "$SESSIONS_DIR" ]; then
        for state_file in "$SESSIONS_DIR"/*/WORKFLOW_STATE.md; do
            if [ -f "$state_file" ]; then
                local id=$(grep -oP 'feature_id: `\K[0-9]+' "$state_file" 2>/dev/null || echo "0")
                id=$((10#$id))  # Force decimal
                if [ "$id" -gt "$max_id" ]; then
                    max_id=$id
                fi
            fi
        done
    fi
    
    # Check archived sessions too
    if [ -d "${SESSIONS_DIR}/archived" ]; then
        for state_file in "${SESSIONS_DIR}/archived"/*/WORKFLOW_STATE.md; do
            if [ -f "$state_file" ]; then
                local id=$(grep -oP 'feature_id: `\K[0-9]+' "$state_file" 2>/dev/null || echo "0")
                id=$((10#$id))
                if [ "$id" -gt "$max_id" ]; then
                    max_id=$id
                fi
            fi
        done
    fi
    
    printf "%03d" $((max_id + 1))
}

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

# Read a value from workflow state
read_state_value() {
    local key="$1"
    local session_id="${2:-$(get_current_session)}"
    local state_file=$(get_state_file "$session_id")
    
    if [ -f "$state_file" ]; then
        grep -oP "\*\*${key}\*\*: \`?\K[^\`\n]+" "$state_file" | head -1
    fi
}

# Update workflow state field
update_state_field() {
    local key="$1"
    local value="$2"
    local session_id="${3:-$(get_current_session)}"
    local state_file=$(get_state_file "$session_id")
    local timestamp=$(get_timestamp)
    
    if [ -f "$state_file" ]; then
        # Update the field
        sed -i "s/^\(- \*\*${key}\*\*:\).*/\1 \`${value}\`/" "$state_file"
        
        # Update timestamp
        sed -i "s/^\(- \*\*updated_at\*\*:\).*/\1 \`${timestamp}\`/" "$state_file"
    else
        log_error "State file not found"
        return 1
    fi
}

# Update condition in yaml block
update_condition() {
    local condition="$1"
    local value="$2"
    local session_id="${3:-$(get_current_session)}"
    local state_file=$(get_state_file "$session_id")
    
    if [ -f "$state_file" ]; then
        sed -i "s/^${condition}: .*/${condition}: ${value}/" "$state_file"
        update_state_field "updated_at" "$(get_timestamp)" "$session_id"
    fi
}

# Add history entry
add_history_entry() {
    local phase="$1"
    local action="$2"
    local result="$3"
    local session_id="${4:-$(get_current_session)}"
    local state_file=$(get_state_file "$session_id")
    local timestamp=$(get_timestamp)
    
    if [ -f "$state_file" ]; then
        sed -i "/^## Notes/i | ${timestamp} | ${phase} | ${action} | ${result} |" "$state_file"
    fi
}

# Check if a condition is met
check_condition() {
    local condition="$1"
    local session_id="${2:-$(get_current_session)}"
    local state_file=$(get_state_file "$session_id")
    
    grep -q "^${condition}: true" "$state_file"
}

# =============================================================================
# PROJECT STATUS
# =============================================================================

# Check if project is ready (constitution + architecture exist)
check_project_ready() {
    local ready="false"
    local has_constitution="false"
    local has_architecture="false"
    local project_type="unknown"
    
    # Check constitution
    if [ -f "constitution.md" ]; then
        has_constitution="true"
    fi
    
    # Check architecture
    if [ -f "spec/architecture.md" ]; then
        has_architecture="true"
    elif grep -q "architecture" AGENTS.md 2>/dev/null; then
        has_architecture="true"
    fi
    
    # Determine if ready
    if [ "$has_constitution" = "true" ] && [ "$has_architecture" = "true" ]; then
        ready="true"
    fi
    
    # Detect project type (virgin vs existing)
    if [ "$ready" = "false" ]; then
        if [ -f "package.json" ] || [ -f "requirements.txt" ] || [ -f "go.mod" ] || \
           [ -f "Cargo.toml" ] || [ -f "pom.xml" ] || [ -d "src" ] || [ -d "lib" ] || [ -d "app" ]; then
            project_type="existing"
        else
            project_type="virgin"
        fi
    fi
    
    echo "PROJECT_READY=$ready"
    echo "HAS_CONSTITUTION=$has_constitution"
    echo "HAS_ARCHITECTURE=$has_architecture"
    echo "PROJECT_TYPE=$project_type"
}

# Show project status
show_project_status() {
    echo ""
    echo "=========================================="
    echo "         PROJECT STATUS"
    echo "=========================================="
    echo ""
    
    # Check files
    local constitution_status="❌"
    local architecture_status="❌"
    local prd_status="❌"
    
    if [ -f "constitution.md" ]; then
        constitution_status="✅"
    fi
    
    if [ -f "spec/architecture.md" ]; then
        architecture_status="✅"
    elif grep -q "architecture" AGENTS.md 2>/dev/null; then
        architecture_status="⚠️  (referenced in AGENTS.md)"
    fi
    
    if [ -f "spec/PRD.md" ]; then
        prd_status="✅"
    fi
    
    echo "Configuration Files:"
    echo "  - constitution.md:      $constitution_status"
    echo "  - spec/architecture.md: $architecture_status"
    echo "  - spec/PRD.md:          $prd_status"
    echo ""
    
    # Check readiness
    eval "$(check_project_ready)"
    
    if [ "$PROJECT_READY" = "true" ]; then
        echo -e "${GREEN}✅ Project is READY for feature workflows${NC}"
    else
        echo -e "${YELLOW}⚠️  Project NOT READY${NC}"
        echo ""
        if [ "$PROJECT_TYPE" = "virgin" ]; then
            echo "This appears to be a virgin project."
            echo "→ Run: /workflow init"
        else
            echo "This appears to be an existing project."
            echo "→ Run: /workflow analyze"
        fi
    fi
    
    echo ""
    echo "=========================================="
}

# =============================================================================
# GIT OPERATIONS
# =============================================================================

# Create feature branch
create_feature_branch() {
    local branch_name="$1"
    
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        log_warning "Branch ${branch_name} already exists, switching to it"
        git checkout "$branch_name"
    else
        git checkout -b "$branch_name"
        log_success "Created and switched to branch: $branch_name"
    fi
}

# =============================================================================
# DISPLAY
# =============================================================================

# Show workflow status
show_status() {
    local session_id=$(get_current_session)
    
    if [ -z "$session_id" ]; then
        log_warning "No active session for this IDE instance"
        echo ""
        # Show IDE info
        if type get_ide_name &>/dev/null; then
            echo "IDE:         $(get_ide_name)"
            echo "IDE Session: $(get_ide_session_id)"
        fi
        echo ""
        echo "To start a new workflow: ./workflow-helper.sh start \"feature description\""
        echo "To list sessions: ./workflow-helper.sh sessions"
        return 1
    fi
    
    local state_file=$(get_state_file "$session_id")
    
    if [ ! -f "$state_file" ]; then
        log_error "State file not found for session: $session_id"
        return 1
    fi
    
    echo ""
    echo "=========================================="
    echo "         WORKFLOW STATUS"
    echo "=========================================="
    echo ""
    # Show IDE info
    if type get_ide_name &>/dev/null; then
        echo "IDE:         $(get_ide_name)"
        echo "IDE Session: $(get_ide_session_id | head -c 12)..."
    fi
    echo ""
    echo "Session:     $session_id"
    echo "Feature:     $(read_state_value 'feature_id') - $(read_state_value 'feature_description')"
    echo "Branch:      $(read_state_value 'branch_name')"
    echo ""
    echo "Phase:       $(read_state_value 'current_phase')"
    echo "Step:        $(read_state_value 'current_step')"
    echo "Loop Count:  $(read_state_value 'loop_count')"
    echo ""
    echo "Conditions:"
    echo "  - init_complete:           $(check_condition 'init_complete' && echo '✅' || echo '❌')"
    echo "  - spec_complete:           $(check_condition 'spec_complete' && echo '✅' || echo '❌')"
    echo "  - test_scenarios_written:  $(check_condition 'test_scenarios_written' && echo '✅' || echo '❌')"
    echo "  - implementation_complete: $(check_condition 'implementation_complete' && echo '✅' || echo '❌')"
    echo "  - code_review_passed:      $(check_condition 'code_review_passed' && echo '✅' || echo '❌')"
    echo "  - browser_tests_passed:    $(check_condition 'browser_tests_passed' && echo '✅' || echo '❌')"
    echo "  - auto_tests_passed:       $(check_condition 'auto_tests_passed' && echo '✅' || echo '❌')"
    echo "  - final_review_passed:     $(check_condition 'final_review_passed' && echo '✅' || echo '❌')"
    echo "  - workflow_complete:       $(check_condition 'workflow_complete' && echo '✅' || echo '❌')"
    echo ""
    echo "State file:  $state_file"
    echo "=========================================="
}

# =============================================================================
# MAIN - CLI Interface
# =============================================================================

if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    case "${1:-}" in
        "start"|"new")
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 start \"feature description\""
                exit 1
            fi
            create_session "$2"
            ;;
        "status")
            show_status
            ;;
        "sessions"|"list")
            list_sessions
            ;;
        "switch")
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 switch <session_id>"
                exit 1
            fi
            switch_session "$2"
            ;;
        "current")
            get_current_session
            ;;
        "archive")
            archive_session "${2:-}"
            ;;
        "read")
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 read <field>"
                exit 1
            fi
            read_state_value "$2"
            ;;
        "update")
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                log_error "Usage: $0 update <field> <value>"
                exit 1
            fi
            update_state_field "$2" "$3"
            ;;
        "condition")
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                log_error "Usage: $0 condition <name> <true|false>"
                exit 1
            fi
            update_condition "$2" "$3"
            ;;
        "history")
            if [ -z "${2:-}" ] || [ -z "${3:-}" ] || [ -z "${4:-}" ]; then
                log_error "Usage: $0 history <phase> <action> <result>"
                exit 1
            fi
            add_history_entry "$2" "$3" "$4"
            ;;
        "ide")
            # Show IDE information
            if type get_ide_name &>/dev/null; then
                echo "IDE Name:    $(get_ide_name)"
                echo "IDE Session: $(get_ide_session_id)"
            else
                log_error "IDE detection not available"
                exit 1
            fi
            ;;
        "unlink")
            # Unlink session from current IDE
            _sid="${2:-$(get_current_session)}"
            if [ -z "$_sid" ]; then
                log_error "No session to unlink"
                exit 1
            fi
            if type unlink_session_from_ide &>/dev/null; then
                unlink_session_from_ide "$_sid"
                log_success "Session unlinked: $_sid"
            else
                log_error "IDE unlinking not available"
                exit 1
            fi
            ;;
        "project"|"project-status")
            # Show project status (ready for workflow?)
            show_project_status
            ;;
        "check-ready")
            # Check if project is ready (for scripts)
            check_project_ready
            ;;
        *)
            echo "Heracles Workflow Helper - CLI"
            echo ""
            echo "Usage: $0 <command> [args]"
            echo ""
            echo "Project Commands:"
            echo "  project                Show project status (ready for workflow?)"
            echo "  check-ready            Output project readiness as variables"
            echo ""
            echo "Session Commands:"
            echo "  start <description>    Create and start new session"
            echo "  status                 Show current session status"
            echo "  sessions               List all sessions"
            echo "  switch <id>            Switch to another session"
            echo "  current                Print current session ID"
            echo "  archive [id]           Archive session (current if no id)"
            echo "  unlink [id]            Unlink session from current IDE"
            echo ""
            echo "State Commands:"
            echo "  read <field>           Read state field value"
            echo "  update <field> <val>   Update state field"
            echo "  condition <name> <val> Update condition (true/false)"
            echo "  history <p> <a> <r>    Add history entry"
            echo ""
            echo "IDE Commands:"
            echo "  ide                    Show current IDE info"
            ;;
    esac
fi

