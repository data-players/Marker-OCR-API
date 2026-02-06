#!/bin/bash
# =============================================================================
# Create Issue - Script multiplateforme pour créer des issues Git
# =============================================================================
# Supporte: GitLab (glab), Gitea (tea), GitHub (gh), ou mode manuel
# Usage: ./create-issue.sh "Issue Title" ["Issue Body"]
# =============================================================================

set -e

# Load helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/workflow-helper.sh" 2>/dev/null || true

# =============================================================================
# CONFIGURATION
# =============================================================================

# Detect git platform from workflow state or environment
detect_platform() {
    # Check current session state first
    if [ -f ".heracles/current_session" ]; then
        local session_id=$(cat .heracles/current_session)
        local state_file=".heracles/sessions/${session_id}/WORKFLOW_STATE.md"
        if [ -f "$state_file" ]; then
            local platform=$(grep -oP 'git_platform: \K\w+' "$state_file" 2>/dev/null || echo "")
            if [ -n "$platform" ] && [ "$platform" != "null" ]; then
                echo "$platform"
                return
            fi
        fi
    fi
    
    # Check environment variable
    if [ -n "${GIT_PLATFORM:-}" ]; then
        echo "$GIT_PLATFORM"
        return
    fi
    
    # Auto-detect based on remote URL
    local remote_url=$(git remote get-url origin 2>/dev/null || echo "")
    
    if echo "$remote_url" | grep -qi "gitlab"; then
        echo "gitlab"
    elif echo "$remote_url" | grep -qi "gitea\|forgejo\|codeberg"; then
        echo "gitea"
    elif echo "$remote_url" | grep -qi "github"; then
        echo "github"
    else
        echo "none"
    fi
}

# Check if CLI tool is available
check_cli() {
    local platform="$1"
    
    case $platform in
        "gitlab")
            command -v glab &> /dev/null
            ;;
        "gitea")
            command -v tea &> /dev/null
            ;;
        "github")
            command -v gh &> /dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

# =============================================================================
# ISSUE CREATION
# =============================================================================

create_gitlab_issue() {
    local title="$1"
    local body="${2:-}"
    
    local cmd="glab issue create --title \"$title\""
    
    if [ -n "$body" ]; then
        cmd="$cmd --description \"$body\""
    fi
    
    cmd="$cmd --label enhancement"
    
    log_info "Creating GitLab issue..."
    local result=$(eval "$cmd" 2>&1)
    
    # Extract issue number from output
    local issue_num=$(echo "$result" | grep -oP '#\K[0-9]+' | head -1)
    
    if [ -n "$issue_num" ]; then
        log_success "Issue #$issue_num created"
        echo "$issue_num"
    else
        log_error "Failed to create issue: $result"
        return 1
    fi
}

create_gitea_issue() {
    local title="$1"
    local body="${2:-}"
    
    local cmd="tea issues create --title \"$title\""
    
    if [ -n "$body" ]; then
        cmd="$cmd --body \"$body\""
    fi
    
    log_info "Creating Gitea issue..."
    local result=$(eval "$cmd" 2>&1)
    
    # Extract issue number
    local issue_num=$(echo "$result" | grep -oP '#\K[0-9]+' | head -1)
    
    if [ -n "$issue_num" ]; then
        log_success "Issue #$issue_num created"
        echo "$issue_num"
    else
        log_error "Failed to create issue: $result"
        return 1
    fi
}

create_github_issue() {
    local title="$1"
    local body="${2:-}"
    
    local cmd="gh issue create --title \"$title\""
    
    if [ -n "$body" ]; then
        cmd="$cmd --body \"$body\""
    fi
    
    cmd="$cmd --label enhancement"
    
    log_info "Creating GitHub issue..."
    local result=$(eval "$cmd" 2>&1)
    
    # Extract issue number from URL
    local issue_num=$(echo "$result" | grep -oP '/issues/\K[0-9]+' | head -1)
    
    if [ -n "$issue_num" ]; then
        log_success "Issue #$issue_num created"
        echo "$issue_num"
    else
        log_error "Failed to create issue: $result"
        return 1
    fi
}

create_manual_issue() {
    local title="$1"
    local body="${2:-}"
    
    log_warning "No Git platform CLI available. Please create issue manually:"
    echo ""
    echo "=========================================="
    echo "MANUAL ISSUE CREATION REQUIRED"
    echo "=========================================="
    echo ""
    echo "Title: $title"
    echo ""
    if [ -n "$body" ]; then
        echo "Body:"
        echo "$body"
        echo ""
    fi
    echo "=========================================="
    echo ""
    read -p "Enter the issue number after creation (or press Enter to skip): " issue_num
    
    if [ -n "$issue_num" ]; then
        echo "$issue_num"
    else
        echo "0"
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local title="${1:-}"
    local body="${2:-}"
    
    if [ -z "$title" ]; then
        log_error "Usage: $0 \"Issue Title\" [\"Issue Body\"]"
        exit 1
    fi
    
    local platform=$(detect_platform)
    log_info "Detected platform: $platform"
    
    local issue_num=""
    
    case $platform in
        "gitlab")
            if check_cli "gitlab"; then
                issue_num=$(create_gitlab_issue "$title" "$body")
            else
                log_warning "glab CLI not found, falling back to manual"
                issue_num=$(create_manual_issue "$title" "$body")
            fi
            ;;
        "gitea")
            if check_cli "gitea"; then
                issue_num=$(create_gitea_issue "$title" "$body")
            else
                log_warning "tea CLI not found, falling back to manual"
                issue_num=$(create_manual_issue "$title" "$body")
            fi
            ;;
        "github")
            if check_cli "github"; then
                issue_num=$(create_github_issue "$title" "$body")
            else
                log_warning "gh CLI not found, falling back to manual"
                issue_num=$(create_manual_issue "$title" "$body")
            fi
            ;;
        *)
            issue_num=$(create_manual_issue "$title" "$body")
            ;;
    esac
    
    # Update workflow state if available
    if [ -f ".heracles/current_session" ] && [ -n "$issue_num" ] && [ "$issue_num" != "0" ]; then
        local session_id=$(cat .heracles/current_session)
        local state_file=".heracles/sessions/${session_id}/WORKFLOW_STATE.md"
        if [ -f "$state_file" ]; then
            sed -i "s/^\(- \*\*issue_number\*\*:\).*/\1 \`${issue_num}\`/" "$state_file"
            log_success "Session state updated with issue #$issue_num"
        fi
    fi
    
    echo "$issue_num"
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi


