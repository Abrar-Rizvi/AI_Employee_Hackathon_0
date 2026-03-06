#!/usr/bin/env python3
"""
Filesystem Watcher for Bronze Tier AI Employee
Monitors the Drop_Folder for new files and creates tasks.
"""

import os
import sys
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog library not found. Install with: pip install watchdog")
    sys.exit(1)

# Configuration
CONFIG_FILE = Path(__file__).parent / "Config" / "system_config.json"

# Try to load dry_run from config file first, then environment variable
def load_dry_run_config():
    """Load dry_run setting from config file if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("dry_run", True)
        except:
            pass
    # Fall back to environment variable
    return os.getenv('DRY_RUN', 'true').lower() == 'true'

DRY_RUN = load_dry_run_config()
DROP_FOLDER = Path(__file__).parent / "Drop_Folder"
NEEDS_ACTION_FOLDER = Path(__file__).parent / "Needs_Action"
SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.md'}
PROCESSED_FILES = set()  # Track processed files to avoid duplicates

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FileDropHandler(FileSystemEventHandler):
    """Handles file drop events in the Drop_Folder."""

    def __init__(self):
        super().__init__()
        self.file_timers = {}  # Track file creation times for debouncing

    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        logger.info(f"[DETECTED] File created event: {file_path.name}")

        self.process_file(file_path, "created")

    def on_modified(self, event):
        """Called when a file is modified (also triggered on some systems when copying)."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process supported extensions
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        # Debounce: only process if not recently processed
        now = time.time()
        last_time = self.file_timers.get(str(file_path), 0)

        if now - last_time > 2.0:  # 2 second debounce
            logger.info(f"[DETECTED] File modified event: {file_path.name}")
            self.file_timers[str(file_path)] = now
            self.process_file(file_path, "modified")

    def on_moved(self, event):
        """Called when a file is moved/renamed into the folder."""
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)
        logger.info(f"[DETECTED] File moved event: {dest_path.name}")
        self.process_file(dest_path, "moved")

    def process_file(self, file_path, event_type):
        """Process a dropped file and create a task."""
        try:
            # Check file extension
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.info(f"[IGNORED] Unsupported file type: {file_path.suffix}")
                return

            # Check if already processed
            file_key = f"{file_path}_{file_path.stat().st_size}_{file_path.stat().st_mtime}"
            if file_key in PROCESSED_FILES:
                logger.info(f"[SKIP] Already processed: {file_path.name}")
                return

            # Wait for file to be fully written
            time.sleep(0.5)

            if not file_path.exists():
                logger.warning(f"[WARNING] File disappeared: {file_path}")
                return

            # Get file info
            file_size = file_path.stat().st_size

            # Skip empty files
            if file_size == 0:
                logger.warning(f"[SKIP] Empty file: {file_path.name}")
                return

            timestamp = datetime.now().isoformat()
            original_name = file_path.name

            logger.info(f"[PROCESSING] {original_name} ({file_size} bytes) via {event_type} event")

            # Create task frontmatter
            task_content = f"""---
type: file_drop
original_name: {original_name}
source_path: {str(file_path.absolute())}
size: {file_size}
detected: {timestamp}
priority: medium
status: pending
---

# File Dropped: {original_name}

A new file has been dropped in the Drop_Folder and requires processing.

**File Details:**
- Name: {original_name}
- Size: {file_size} bytes
- Detected: {timestamp}
- Source: {file_path}

**Action Required:**
Please review and process this file.
"""

            # Create task file
            safe_timestamp = timestamp.replace(':', '-').replace('.', '-')
            task_filename = f"task_{safe_timestamp}.md"
            task_path = NEEDS_ACTION_FOLDER / task_filename

            if DRY_RUN:
                logger.info(f"[DRY RUN] Would create task: {task_filename}")
                logger.info(f"[DRY RUN] Would copy file to: {NEEDS_ACTION_FOLDER / original_name}")
            else:
                with open(task_path, 'w', encoding='utf-8') as f:
                    f.write(task_content)
                logger.info(f"[SUCCESS] Task created: {task_filename}")

                # Copy the dropped file to Needs_Action
                dest_path = NEEDS_ACTION_FOLDER / original_name
                shutil.copy2(file_path, dest_path)
                logger.info(f"[SUCCESS] File copied to: {dest_path}")

            # Log the action
            log_entry = {
                "timestamp": timestamp,
                "action": "file_dropped",
                "event_type": event_type,
                "file": str(file_path),
                "task_file": str(task_path),
                "size": file_size,
                "dry_run": DRY_RUN,
                "status": "created"
            }

            logger.info(f"[LOG] {json.dumps(log_entry, indent=2)}")

            # Mark as processed
            PROCESSED_FILES.add(file_key)

        except Exception as e:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "error",
                "file": str(file_path),
                "error": str(e),
                "status": "failed"
            }
            logger.error(f"[ERROR] Processing {file_path}: {e}")
            logger.error(f"[ERROR] {json.dumps(error_entry, indent=2)}")
            import traceback
            traceback.print_exc()


def scan_existing_files():
    """Scan Drop_Folder for files that were dropped before script started."""
    logger.info("[SCAN] Checking for existing files in Drop_Folder...")

    if not DROP_FOLDER.exists():
        logger.warning(f"[WARNING] Drop_Folder does not exist: {DROP_FOLDER}")
        return

    files = list(DROP_FOLDER.glob("*"))
    files = [f for f in files if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if files:
        logger.info(f"[SCAN] Found {len(files)} existing file(s) to process")
        handler = FileDropHandler()

        for file_path in files:
            logger.info(f"[SCAN] Processing existing file: {file_path.name}")
            handler.process_file(file_path, "scan")
    else:
        logger.info("[SCAN] No existing files found")


def main():
    """Main entry point for the filesystem watcher."""
    logger.info("=" * 60)
    logger.info("Bronze Tier - Filesystem Watcher Starting")
    logger.info("=" * 60)
    logger.info(f"DRY_RUN: {DRY_RUN}")
    logger.info(f"Monitoring: {DROP_FOLDER.absolute()}")
    logger.info(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    logger.info("Press Ctrl+C to stop...")
    logger.info("")

    # Ensure folders exist
    DROP_FOLDER.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)

    # Scan for existing files first
    scan_existing_files()
    logger.info("")

    # Setup observer
    event_handler = FileDropHandler()
    observer = Observer()

    # Use recursive=True to catch events in subdirectories too
    observer.schedule(event_handler, str(DROP_FOLDER), recursive=True)

    try:
        observer.start()
        logger.info("[WATCHING] Filesystem watcher is now active...")
        logger.info("")

        # Polling for WSL2 compatibility (check every 5 seconds)
        last_scan = time.time()
        poll_interval = 5  # Scan for new files every 5 seconds
        handler = event_handler

        count = 0
        while True:
            time.sleep(10)
            count += 1

            # Periodic poll for WSL2 compatibility
            now = time.time()
            if now - last_scan >= poll_interval:
                # Quick scan for unprocessed files
                for file_path in DROP_FOLDER.glob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        try:
                            file_key = f"{file_path}_{file_path.stat().st_size}_{file_path.stat().st_mtime}"
                            if file_key not in PROCESSED_FILES:
                                logger.info(f"[POLL] Found new file: {file_path.name}")
                                handler.process_file(file_path, "poll")
                        except:
                            pass
                last_scan = now

            if count % 6 == 0:  # Every minute
                logger.info(f"[HEARTBEAT] Watching... (checked {count} times)")

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down gracefully...")
        observer.stop()
    finally:
        observer.join()
        logger.info("Filesystem watcher stopped.")


if __name__ == "__main__":
    main()
