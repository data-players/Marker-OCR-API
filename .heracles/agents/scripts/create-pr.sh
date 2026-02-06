#!/bin/bash
# =============================================================================
# Create PR/MR - Script multiplateforme pour créer des Pull/Merge Requests
# =============================================================================
# Supporte: GitLab (glab), Gitea (tea), GitHub (gh), ou mode manuel
# Usage: ./create-pr.sh ["PR Title"] ["PR Body"]
# =============================================================================

set -e

# Load helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/workflow-helper.sh" 2>/dev/null || true

# =============================================================================
# CONFIGURATION
# =============================================================================

# Detect git platform
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
    
    if [ -n "${GIT_PLATFORM:-}" ]; then
        echo "$GIT_PLATFORM"
        return
    fi
    
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

# Get PR info from workflow state
get_pr_info() {
    local state_file=""
    
    # Try to find the session state file
    if [ -f ".heracles/current_session" ]; then
        local session_id=$(cat .heracles/current_session)
        state_file=".heracles/sessions/${session_id}/WORKFLOW_STATE.md"
    fi
    
    if [ -f "$state_file" ]; then
        FEATURE_ID=$(grep -oP 'feature_id.*`\K[^`]+' "$state_file" | head -1)
        FEATURE_DESC=$(grep -oP 'feature_description.*: \K.*' "$state_file" | head -1)
        ISSUE_NUM=$(grep -oP 'issue_number.*`\K[^`]+' "$state_file" | head -1)
        BRANCH_NAME=$(grep -oP 'branch_name.*`\K[^`]+' "$state_file" | head -1)
        SESSION_DIR=".heracles/sessions/${session_id}"
    else
        FEATURE_ID=""
        FEATURE_DESC=""
        ISSUE_NUM=""
        BRANCH_NAME=$(git branch --show-current)
        SESSION_DIR=""
    fi
}

# Check if CLI tool is available
check_cli() {
    local platform="$1"
    
    case $platform in
        "gitlab") command -v glab &> /dev/null ;;
        "gitea") command -v tea &> /dev/null ;;
        "github") command -v gh &> /dev/null ;;
        *) return 1 ;;
    esac
}

# =============================================================================
# PR/MR CREATION
# =============================================================================

create_gitlab_mr() {
    local title="$1"
    local body="$2"
    
    log_info "Creating GitLab Merge Request..."
    
    local cmd="glab mr create"
    cmd="$cmd --title \"$title\""
    cmd="$cmd --description \"$body\""
    cmd="$cmd --remove-source-branch"
    cmd="$cmd --squash"
    
    if [ -n "$ISSUE_NUM" ] && [ "$ISSUE_NUM" != "null" ]; then
        cmd="$cmd --related-issue $ISSUE_NUM"
    fi
    
    local result=$(eval "$cmd" 2>&1)
    
    local mr_url=$(echo "$result" | grep -oP 'https?://[^\s]+' | head -1)
    
    if [ -n "$mr_url" ]; then
        log_success "Merge Request created: $mr_url"
        echo "$mr_url"
    else
        log_error "Failed to create MR: $result"
        return 1
    fi
}

create_gitea_pr() {
    local title="$1"
    local body="$2"
    
    log_info "Creating Gitea Pull Request..."
    
    local cmd="tea pulls create"
    cmd="$cmd --title \"$title\""
    cmd="$cmd --description \"$body\""
    cmd="$cmd --base main"
    cmd="$cmd --head $BRANCH_NAME"
    
    local result=$(eval "$cmd" 2>&1)
    
    local pr_url=$(echo "$result" | grep -oP 'https?://[^\s]+' | head -1)
    
    if [ -n "$pr_url" ]; then
        log_success "Pull Request created: $pr_url"
        echo "$pr_url"
    else
        log_error "Failed to create PR: $result"
        return 1
    fi
}

create_github_pr() {
    local title="$1"
    local body="$2"
    
    log_info "Creating GitHub Pull Request..."
    
    local cmd="gh pr create"
    cmd="$cmd --title \"$title\""
    cmd="$cmd --body \"$body\""
    cmd="$cmd --base main"
    cmd="$cmd --head $BRANCH_NAME"
    
    local result=$(eval "$cmd" 2>&1)
    
    local pr_url=$(echo "$result" | grep -oP 'https?://[^\s]+' | head -1)
    
    if [ -n "$pr_url" ]; then
        log_success "Pull Request created: $pr_url"
        echo "$pr_url"
    else
        log_error "Failed to create PR: $result"
        return 1
    fi
}

create_manual_pr() {
    local title="$1"
    local body="$2"
    
    log_warning "No Git platform CLI available. Please create PR/MR manually:"
    echo ""
    echo "=========================================="
    echo "MANUAL PR/MR CREATION REQUIRED"
    echo "=========================================="
    echo ""
    echo "Title: $title"
    echo "Source Branch: $BRANCH_NAME"
    echo "Target Branch: main"
    echo ""
    echo "Body:"
    echo "$body"
    echo ""
    echo "=========================================="
    echo ""
    read -p "Enter the PR/MR URL after creation (or press Enter to skip): " pr_url
    
    echo "${pr_url:-manual}"
}

# =============================================================================
# BODY GENERATION
# =============================================================================

generate_pr_body() {
    local body=""
    
    # Add feature description
    if [ -n "$FEATURE_DESC" ]; then
        body="## Description\n\n$FEATURE_DESC\n\n"
    fi
    
    # Add issue reference
    if [ -n "$ISSUE_NUM" ] && [ "$ISSUE_NUM" != "null" ]; then
        body="${body}## Related Issue\n\nCloses #$ISSUE_NUM\n\n"
    fi
    
    # Add spec reference if exists
    if [ -n "$SESSION_DIR" ] && [ -f "${SESSION_DIR}/specs/specification.md" ]; then
        body="${body}## Specification\n\nSee \`${SESSION_DIR}/specs/specification.md\`\n\n"
    fi
    
    # Add checklist
    body="${body}## Checklist\n\n"
    body="${body}- [x] Code implemented according to specification\n"
    body="${body}- [x] All tests passing\n"
    body="${body}- [x] Code review completed\n"
    body="${body}- [x] Documentation updated (if needed)\n"
    
    # Add review report reference if exists
    if [ -n "$SESSION_DIR" ]; then
        local review_file="${SESSION_DIR}/review-reports/final-review.md"
        if [ -f "$review_file" ]; then
            body="${body}\n## Review Report\n\nSee \`$review_file\`\n"
        fi
    fi
    
    echo -e "$body"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    # Get info from workflow state
    get_pr_info
    
    # Generate title
    local title="${1:-}"
    if [ -z "$title" ]; then
        if [ -n "$FEATURE_ID" ] && [ -n "$FEATURE_DESC" ]; then
            title="feat(${FEATURE_ID}): ${FEATURE_DESC}"
        else
            title="Feature: $(git branch --show-current)"
        fi
    fi
    
    # Generate or use provided body
    local body="${2:-}"
    if [ -z "$body" ]; then
        body=$(generate_pr_body)
    fi
    
    # Detect platform and create PR
    local platform=$(detect_platform)
    log_info "Detected platform: $platform"
    
    local pr_url=""
    
    case $platform in
        "gitlab")
            if check_cli "gitlab"; then
                pr_url=$(create_gitlab_mr "$title" "$body")
            else
                log_warning "glab CLI not found, falling back to manual"
                pr_url=$(create_manual_pr "$title" "$body")
            fi
            ;;
        "gitea")
            if check_cli "gitea"; then
                pr_url=$(create_gitea_pr "$title" "$body")
            else
                log_warning "tea CLI not found, falling back to manual"
                pr_url=$(create_manual_pr "$title" "$body")
            fi
            ;;
        "github")
            if check_cli "github"; then
                pr_url=$(create_github_pr "$title" "$body")
            else
                log_warning "gh CLI not found, falling back to manual"
                pr_url=$(create_manual_pr "$title" "$body")
            fi
            ;;
        *)
            pr_url=$(create_manual_pr "$title" "$body")
            ;;
    esac
    
    # Add to history
    if [ -f ".heracles/current_session" ] && [ -n "$pr_url" ]; then
        local session_id=$(cat .heracles/current_session)
        local state_file=".heracles/sessions/${session_id}/WORKFLOW_STATE.md"
        if [ -f "$state_file" ]; then
            local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            sed -i "/^## Notes/i | ${timestamp} | finalize | pr_created | ${pr_url} |" "$state_file"
        fi
    fi
    
    echo "$pr_url"
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi


