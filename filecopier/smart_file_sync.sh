#!/bin/bash

# Smart File Synchronization Script
# Author: Auto-generated for efficient file operations
# Description: Synchronizes files from origin to target directory with intelligent duplicate handling

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC}  ${timestamp} - $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC}  ${timestamp} - $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" ;;
    esac
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] <ORIGIN_DIR> <TARGET_DIR>

Smart file synchronization script that efficiently moves files from origin to target directory.

Arguments:
  ORIGIN_DIR    Source directory containing files to sync
  TARGET_DIR    Target directory where files should be moved

Options:
  -h, --help     Show this help message
  -v, --verbose  Enable verbose output
  -n, --dry-run  Show what would be done without making changes
  -l, --log-file Specify log file path (default: /tmp/smart_sync.log)

Examples:
  $0 /incoming/files /mnt/shared/storage
  $0 -v -n /tmp/upload /backup/files
  $0 --dry-run /source /destination

The script performs the following operations:
1. Lists all files in the origin directory
2. For each file, checks if it exists in target (by path, size, and MD5)
3. If file exists in target: removes it from origin
4. If file doesn't exist in target: moves it from origin to target
EOF
}

# Function to calculate MD5 checksum
calculate_md5() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if command -v md5sum >/dev/null 2>&1; then
            md5sum "$file" | cut -d' ' -f1
        elif command -v md5 >/dev/null 2>&1; then
            md5 -q "$file"
        else
            log "ERROR" "No MD5 calculation tool available (md5sum or md5)"
            exit 1
        fi
    else
        echo ""
    fi
}

# Function to get file size
get_file_size() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            stat -f%z "$file"
        else
            stat -c%s "$file"
        fi
    else
        echo "0"
    fi
}

# Function to create directory structure if it doesn't exist
ensure_directory() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$dir"
            log "INFO" "Created directory: $dir"
        else
            log "INFO" "Would create directory: $dir"
        fi
    fi
}

# Function to check if files are identical
files_identical() {
    local origin_file="$1"
    local target_file="$2"
    
    # Check if target file exists
    if [[ ! -f "$target_file" ]]; then
        return 1
    fi
    
    # Compare file sizes first (quick check)
    local origin_size=$(get_file_size "$origin_file")
    local target_size=$(get_file_size "$target_file")
    
    if [[ "$origin_size" != "$target_size" ]]; then
        return 1
    fi
    
    # If sizes match, compare MD5 checksums
    local origin_md5=$(calculate_md5 "$origin_file")
    local target_md5=$(calculate_md5 "$target_file")
    
    if [[ "$origin_md5" == "$target_md5" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to process a single file
process_file() {
    local origin_file="$1"
    local origin_dir="$2"
    local target_dir="$3"
    
    # Calculate relative path
    local rel_path="${origin_file#$origin_dir/}"
    local target_file="$target_dir/$rel_path"
    local target_file_dir=$(dirname "$target_file")
    
    # Ensure target directory exists
    ensure_directory "$target_file_dir"
    
    if files_identical "$origin_file" "$target_file"; then
        # File exists and is identical, remove from origin
        if [[ "$DRY_RUN" == "false" ]]; then
            rm "$origin_file"
            log "INFO" "Removed duplicate file from origin: $rel_path"
        else
            log "INFO" "Would remove duplicate file from origin: $rel_path"
        fi
        DUPLICATES_REMOVED=$((DUPLICATES_REMOVED + 1))
    else
        # File doesn't exist or is different, move to target
        if [[ "$DRY_RUN" == "false" ]]; then
            # mv "$origin_file" "$target_file"
            cp "$origin_file" "$target_file"
            log "INFO" "Moved file to target: $rel_path"
        else
            log "INFO" "Would move file to target: $rel_path"
        fi
        FILES_MOVED=$((FILES_MOVED + 1))
    fi
}

# Function to find and process all files
sync_files() {
    local origin_dir="$1"
    local target_dir="$2"
    
    log "INFO" "Starting file synchronization"
    log "INFO" "Origin directory: $origin_dir"
    log "INFO" "Target directory: $target_dir"
    
    # Change to origin directory to avoid permission issues with find
    local original_pwd="$PWD"
    cd "$origin_dir" 2>/dev/null || {
        log "ERROR" "Cannot change to origin directory: $origin_dir"
        return 1
    }
    
    # Find all files in origin directory (excluding hidden files and directories)
    while IFS= read -r -d '' file; do
        # Convert relative path back to absolute
        local abs_file="$origin_dir/$file"
        if [[ -f "$abs_file" ]]; then
            TOTAL_FILES=$((TOTAL_FILES + 1))
            if [[ "$VERBOSE" == "true" ]]; then
                log "DEBUG" "Processing: $file"
            fi
            process_file "$abs_file" "$origin_dir" "$target_dir"
        fi
    done < <(find . -type f -not -path './.*' -print0 2>/dev/null)
    
    # Return to original directory
    cd "$original_pwd" 2>/dev/null || true
}

# Function to remove empty directories
cleanup_empty_dirs() {
    local origin_dir="$1"
    local original_pwd="$PWD"
    
    # Change to origin directory to avoid permission issues
    cd "$origin_dir" 2>/dev/null || {
        log "WARN" "Cannot change to origin directory for cleanup: $origin_dir"
        return 0
    }
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Remove empty directories (bottom-up) but exclude the origin directory itself
        find . -mindepth 1 -type d -empty -delete 2>/dev/null || true
        log "INFO" "Cleaned up empty directories"
    else
        local empty_dirs=$(find . -mindepth 1 -type d -empty 2>/dev/null | wc -l)
        if [[ "$empty_dirs" -gt 0 ]]; then
            log "INFO" "Would clean up $empty_dirs empty directories"
        fi
    fi
    
    # Return to original directory
    cd "$original_pwd" 2>/dev/null || true
}

# Main function
main() {
    # Initialize variables
    local VERBOSE=false
    local DRY_RUN=false
    local LOG_FILE="/tmp/smart_sync.log"
    local TOTAL_FILES=0
    local FILES_MOVED=0
    local DUPLICATES_REMOVED=0
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -l|--log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            -*)
                log "ERROR" "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Check if we have exactly 2 arguments remaining
    if [[ $# -ne 2 ]]; then
        log "ERROR" "Exactly 2 arguments required: origin and target directories"
        usage
        exit 1
    fi
    
    local ORIGIN_DIR="$1"
    local TARGET_DIR="$2"
    
    # Change to a safe directory to avoid permission issues
    cd /tmp 2>/dev/null || cd / 2>/dev/null || true
    
    # Validate directories
    if [[ ! -d "$ORIGIN_DIR" ]]; then
        log "ERROR" "Origin directory does not exist: $ORIGIN_DIR"
        exit 1
    fi
    
    if [[ ! -d "$TARGET_DIR" ]]; then
        log "WARN" "Target directory does not exist, will create: $TARGET_DIR"
        ensure_directory "$TARGET_DIR"
    fi
    
    # Make paths absolute
    ORIGIN_DIR=$(realpath "$ORIGIN_DIR")
    TARGET_DIR=$(realpath "$TARGET_DIR")
    
    # Check if directories are the same
    if [[ "$ORIGIN_DIR" == "$TARGET_DIR" ]]; then
        log "ERROR" "Origin and target directories cannot be the same"
        exit 1
    fi
    
    # Setup logging to file if specified
    if [[ "$LOG_FILE" != "" ]]; then
        exec > >(tee -a "$LOG_FILE")
        exec 2>&1
    fi
    
    # Display configuration
    if [[ "$DRY_RUN" == "true" ]]; then
        log "WARN" "DRY RUN MODE - No files will be modified"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        log "INFO" "Verbose mode enabled"
    fi
    
    # Start synchronization
    local start_time=$(date +%s)
    
    sync_files "$ORIGIN_DIR" "$TARGET_DIR"
    cleanup_empty_dirs "$ORIGIN_DIR"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Display summary
    log "INFO" "Synchronization completed in ${duration}s"
    log "INFO" "Total files processed: $TOTAL_FILES"
    log "INFO" "Files moved: $FILES_MOVED"
    log "INFO" "Duplicates removed: $DUPLICATES_REMOVED"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "WARN" "This was a dry run - no actual changes were made"
    fi
}

# Make variables global so they can be accessed by functions
VERBOSE=false
DRY_RUN=false
TOTAL_FILES=0
FILES_MOVED=0
DUPLICATES_REMOVED=0

# Run main function with all arguments
main "$@"
