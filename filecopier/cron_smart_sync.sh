#!/bin/bash

# Cron Helper Script for Smart File Sync
# This script is designed to be called from cron for automated file synchronization

# Configuration - Modify these paths according to your setup
ORIGIN_DIR="/path/to/incoming/files"    # Directory where files are received
TARGET_DIR="/path/to/shared/mount"      # Shared mount directory
SCRIPT_DIR="$(dirname "$0")"            # Directory where this script is located
LOG_FILE="/var/log/smart_sync.log"      # Log file location
LOCK_FILE="/tmp/smart_sync.lock"        # Lock file to prevent concurrent runs

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check if another instance is running
if [ -f "$LOCK_FILE" ]; then
    if ps -p "$(cat "$LOCK_FILE")" > /dev/null 2>&1; then
        log_message "Another instance is already running. Exiting."
        exit 0
    else
        # Remove stale lock file
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file
echo $$ > "$LOCK_FILE"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Log start of synchronization
log_message "Starting file synchronization from $ORIGIN_DIR to $TARGET_DIR"

# Run the smart sync script
if "$SCRIPT_DIR/smart_file_sync.sh" -l "$LOG_FILE" "$ORIGIN_DIR" "$TARGET_DIR"; then
    log_message "File synchronization completed successfully"
    exit_code=0
    # Remove lock file
    rm -f "$LOCK_FILE"
else
    log_message "File synchronization failed with exit code $?"
    exit_code=1
fi


# Log completion
log_message "File synchronization process finished with exit code $exit_code"

exit $exit_code
