#!/bin/bash
#
# USB Auto PDF Copy Script
# ------------------------
# This script automatically copies PDF files from a mounted USB flash drive
# to the internal storage directory of the Raspberry Pi e-book reader.
#
# The script is intended to be triggered via udev rules or manual execution.
# It enables plug-and-play file transfer without user interaction.
#

# Path where the USB device is mounted (passed as argument)
USB_PATH="$1"

# Target directory for storing PDF files
TARGET_DIR="/home/ebook/e-Paper/RaspberryPi_JetsonNano/python/examples/pdf_first"

# Log file for copy operations
LOG_FILE="/home/ebook/reader/bin/usb_copy.log"

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Check if USB path exists
if [ ! -d "$USB_PATH" ]; then
    echo "USB path not found: $USB_PATH" >> "$LOG_FILE"
    exit 1
fi

# Copy all PDF files from USB to target directory
for pdf in "$USB_PATH"/*.pdf; do
    if [ -f "$pdf" ]; then
        filename=$(basename "$pdf")
        cp "$pdf" "$TARGET_DIR/$filename"
        echo "$(date): Copied $filename to $TARGET_DIR" >> "$LOG_FILE"
    fi
done

exit 0
