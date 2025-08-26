#!/bin/bash

# Function to show usage
show_usage() {
    echo "Usage: $0 -d TESTDIR -s SIZE [-h]"
    echo ""
    echo "Options:"
    echo "  -d TESTDIR    Directory to test (required)"
    echo "  -s SIZE       Test file size in MB (required)"
    echo "  -h            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -d /mnt/myshare -s 1024"
    echo "  $0 -d /tmp -s 512"
    echo "  $0 -h"
}

# Initialize variables
TESTDIR=""
FILESIZE=""

# Parse command line arguments
while getopts "d:s:h" opt; do
    case $opt in
        d)
            TESTDIR="$OPTARG"
            ;;
        s)
            FILESIZE="$OPTARG"
            ;;
        h)
            show_usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Check if required parameters are provided
if [ -z "$TESTDIR" ] || [ -z "$FILESIZE" ]; then
    echo "Error: Both -d (directory) and -s (size) parameters are required."
    echo ""
    show_usage
    exit 1
fi

# Validate test directory
if [ ! -d "$TESTDIR" ]; then
    echo "Error: Directory '$TESTDIR' does not exist or is not accessible."
    exit 1
fi

# Check if directory is writable
if [ ! -w "$TESTDIR" ]; then
    echo "Error: Directory '$TESTDIR' is not writable."
    exit 1
fi

TESTFILE="$TESTDIR/speedtest.tmp"

echo "=== Filesystem Speed Test ==="
echo "Test directory: $TESTDIR"
echo "Test file size: ${FILESIZE}MB"
echo ""

echo "Testing write speed..."
sudo dd if=/dev/zero of="$TESTFILE" bs=1M count="$FILESIZE" conv=fdatasync 2>&1 | grep -E "(copied|MB/s|GB/s)"

echo ""
echo "Testing read speed..."
sudo dd if="$TESTFILE" of=/dev/null bs=1M 2>&1 | grep -E "(copied|MB/s|GB/s)"

echo ""
echo "Cleaning up..."
sudo rm -f "$TESTFILE"

echo "Speed test completed."