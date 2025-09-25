# Smart File Synchronization Scripts

This directory contains a script for efficient file synchronization between directories, particularly useful for handling files received from clients and moving them to other shares.

## Scripts Overview

### `smart_file_sync.sh`
The main synchronization script that intelligently handles file operations.

**Features:**
- Compares files by relative path, size, and MD5 checksum
- Removes duplicates from origin if they already exist in target
- Moves new/different files from origin to target
- Preserves directory structure
- Provides detailed logging and statistics
- Supports dry-run mode for testing
- Cross-platform compatible (Linux/macOS)

**Usage:**
```bash
./smart_file_sync.sh [OPTIONS] <ORIGIN_DIR> <TARGET_DIR>

Options:
  -h, --help     Show help message
  -v, --verbose  Enable verbose output
  -n, --dry-run  Show what would be done without making changes
  -l, --log-file Specify log file path (default: /tmp/smart_sync.log)
```

**Examples:**
```bash
# Basic sync
./smart_file_sync.sh /incoming/files /mnt/shared/storage

# Verbose dry run
./smart_file_sync.sh -v -n /tmp/upload /backup/files

# With custom log file
./smart_file_sync.sh -l /var/log/my_sync.log /source /destination
```

### `cron_smart_sync.sh`
A cron-friendly wrapper script for automated synchronization.

**Features:**
- Prevents concurrent execution with lock files
- Automatic logging to specified log file
- Configurable source and target directories
- Error handling and exit codes suitable for cron

**Setup:**
1. Edit the script to configure your directories:
   ```bash
   ORIGIN_DIR="/path/to/incoming/files"
   TARGET_DIR="/path/to/shared/mount"
   ```

2. Add to crontab for regular execution:
   ```bash
   # Run every 5 minutes
   */5 * * * * /path/to/useful-scripts/cron_smart_sync.sh
   
   # Run every hour
   0 * * * * /path/to/useful-scripts/cron_smart_sync.sh
   
   # Run every day at 2 AM
   0 2 * * * /path/to/useful-scripts/cron_smart_sync.sh
   ```

## How It Works

The script performs the following operations:

1. **Discovery**: Lists all files in the origin directory recursively
2. **Comparison**: For each file, checks if an identical file exists in the target:
   - Compares relative path
   - Compares file size (quick check)
   - Compares MD5 checksum (thorough verification)
3. **Action**: Based on comparison results:
   - If identical file exists in target: removes duplicate from origin
   - If file doesn't exist or is different: moves file from origin to target
4. **Cleanup**: Removes empty directories from origin after processing

## Benefits Over Simple `cp` Command

- **Efficiency**: Only processes files that need to be moved or removed
- **Deduplication**: Automatically removes duplicates without unnecessary copying
- **Safety**: Verifies file integrity with checksums before removing
- **Logging**: Provides detailed logs of all operations
- **Reliability**: Handles edge cases like concurrent execution and interrupted transfers
- **Testing**: Dry-run mode allows safe testing before actual operations

## File Comparison Logic

The script uses a three-tier comparison approach:

1. **Path Comparison**: Files must have the same relative path
2. **Size Comparison**: Quick elimination of obviously different files
3. **Checksum Comparison**: MD5 hash verification for identical content

This ensures that only truly identical files are considered duplicates.

## Logging

All operations are logged with timestamps and different log levels:
- **INFO**: Normal operations (file moves, removals, directory creation)
- **WARN**: Warnings (missing target directory, dry-run mode)
- **ERROR**: Errors (missing tools, invalid directories)
- **DEBUG**: Detailed operations (enabled with -v flag)

## Error Handling

The script includes robust error handling:
- Validates directory existence and permissions
- Checks for required tools (md5sum/md5)
- Prevents same source/target directory
- Handles interrupted operations gracefully
- Provides meaningful exit codes for cron jobs

## Performance Considerations

- File size comparison is performed before MD5 calculation for efficiency
- Directory structure is preserved and created as needed
- Empty directories are cleaned up automatically
- Lock files prevent multiple concurrent executions

## Migration from Simple `cp` Command

To replace your current cron job:

1. **Current setup** (inefficient):
   ```bash
   # Cron job
   */30 * * * * cp -r /incoming/files/* /mnt/shared/storage/
   ```

2. **New setup** (efficient):
   ```bash
   # Edit cron_smart_sync.sh with your directories
   # Add to cron
   */30 * * * * /path/to/useful-scripts/cron_smart_sync.sh
   ```

## Testing

Always test with dry-run mode first:
```bash
./smart_file_sync.sh -n -v /your/origin /your/target
```

This will show exactly what operations would be performed without making any changes.
