#!/usr/bin/env python3
"""
Base Watcher Pattern for Silver Tier AI Employee
Provides common functionality for all watcher scripts.
"""

import os
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not found. Install with: pip install python-dotenv")
    load_dotenv = lambda: None


class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, vault_path: str = None):
        # Set vault path first
        self.vault_path = Path(vault_path or os.getenv('VAULT_PATH', '/mnt/d/AI_Employee_Hackathon_0/Silver'))

        # Load environment variables from .env in vault folder
        env_file = self.vault_path / '.env'
        if env_file.exists():
            load_dotenv(dotenv_path=env_file)
        else:
            load_dotenv()  # Fallback to default locations

        self.config_path = self.vault_path / "Config"
        self.logs_path = self.vault_path / "Logs"
        self.needs_action_path = self.vault_path / "Needs_Action"

        # Get settings
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        # State tracking
        self.running = False
        self.processed_items = set()
        self.state_file = self.config_path / f"{self.__class__.__name__}_state.json"

        # Setup logging
        self._setup_logging()

        # Load previous state
        self._load_state()

        # Ensure folders exist
        self._ensure_folders()

    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.vault_path / 'Logs' / 'watcher.log')
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _ensure_folders(self):
        """Ensure all required folders exist."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

    def _load_state(self):
        """Load previous state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_items = set(state.get('processed_items', []))
                self.logger.info(f"Loaded state with {len(self.processed_items)} processed items")
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")

    def _save_state(self):
        """Save current state to file."""
        try:
            state = {
                'processed_items': list(self.processed_items),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to daily JSON log file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": self.__class__.__name__,
            "action": action,
            "dry_run": self.dry_run
        }

        if details:
            log_entry.update(details)

        # Get daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_path / f"{today}.json"

        try:
            # Read existing logs
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new log
            logs.append(log_entry)

            # Write back
            if not self.dry_run:
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)

            self.logger.info(f"Logged: {action}")

        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")

    @abstractmethod
    def check_for_updates(self) -> List[Dict]:
        """Check for new updates. Returns list of items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item: Dict) -> Dict:
        """Create an action file for the given item."""
        pass

    def _is_already_processed(self, item_id: str) -> bool:
        """Check if item has already been processed."""
        return item_id in self.processed_items

    def _mark_as_processed(self, item_id: str):
        """Mark an item as processed."""
        self.processed_items.add(item_id)
        self._save_state()

    def process_item(self, item: Dict) -> Dict:
        """Process a single item."""
        item_id = item.get('id')

        if not item_id:
            return {
                "status": "error",
                "error": "Item missing 'id' field",
                "item": item
            }

        # Check if already processed
        if self._is_already_processed(item_id):
            self.logger.info(f"Skipping already processed item: {item_id}")
            return {
                "status": "skipped",
                "reason": "already_processed",
                "item_id": item_id
            }

        # Create action file
        result = self.create_action_file(item)

        # Mark as processed if successful
        if result.get('status') == 'success':
            self._mark_as_processed(item_id)

        return result

    def run(self, check_interval: int = 60, max_iterations: int = None):
        """Run the watcher continuously."""
        self.running = True
        iteration = 0

        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Check interval: {check_interval} seconds")
        self.logger.info(f"DRY_RUN: {self.dry_run}")

        try:
            while self.running:
                if max_iterations and iteration >= max_iterations:
                    self.logger.info(f"Reached max iterations ({max_iterations})")
                    break

                iteration += 1
                self.logger.info(f"Iteration {iteration}")

                try:
                    # Check for updates
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")

                        # Process each item
                        for item in items:
                            result = self.process_item(item)

                            if result.get('status') == 'error':
                                self.logger.error(f"Error processing item: {result.get('error')}")
                    else:
                        self.logger.info("No new items found")

                except Exception as e:
                    self.logger.error(f"Error during check: {e}")
                    self._log_activity('error', {'error': str(e)})

                # Wait before next check
                if max_iterations is None or iteration < max_iterations:
                    self.logger.info(f"Waiting {check_interval} seconds...")
                    time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
        finally:
            self.running = False
            self._save_state()
            self.logger.info(f"{self.__class__.__name__} stopped")

    def stop(self):
        """Stop the watcher."""
        self.running = False
