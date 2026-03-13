---
name: scheduler
description: Schedule tasks via cron for automated execution. Manage recurring jobs, one-time tasks, and background processes.
license: Apache-2.0
compatibility: Requires schedule, croniter (Python built-in scheduling)
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  platform: "Cross-platform"
---

# Scheduler Skill

## Purpose
Schedule tasks and background jobs for automated execution. This skill enables the AI Employee to run tasks at specific times, intervals, or based on cron expressions, providing autonomous operation without manual intervention.

## When to Use This Skill
- Running periodic email checks
- Scheduling social media posts
- Automated data backups
- Recurring report generation
- Scheduled API calls
- Background task management
- Time-based automation workflows

## Input Parameters

```json
{
  "action": "schedule|list|remove|run_once|recurring",
  "task_id": "unique_task_identifier",
  "task_name": "Email Checker",
  "command": "python gmail_reader.md",
  "schedule": {
    "type": "cron|interval|once",
    "expression": "0 */30 * * * *",
    "interval_seconds": 300,
    "run_at": "2026-02-24T12:00:00"
  },
  "max_runs": null,
  "timeout": 300,
  "enabled": true,
  "callback": "function_name",
  "parameters": {
    "param1": "value1"
  }
}
```

## Output Format

```json
{
  "status": "success",
  "action": "schedule",
  "timestamp": "2026-02-24T12:00:00",
  "task_id": "email_checker_001",
  "task_name": "Email Checker",
  "scheduled": true,
  "next_run": "2026-02-24T12:30:00",
  "schedule_type": "cron",
  "schedule_expression": "0 */30 * * * *",
  "enabled": true
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
Scheduler Skill for Silver Tier AI Employee
Schedule tasks via cron for automated execution.
"""

import os
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging

try:
    from croniter import croniter
except ImportError:
    print("Warning: croniter not found. Install with: pip install croniter")
    croniter = None

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
SCHEDULE_FILE = Path(__file__).parent.parent.parent / "Silver" / "Config" / "scheduled_tasks.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduledTask:
    """Represents a scheduled task."""

    def __init__(
        self,
        task_id: str,
        task_name: str,
        command: str,
        schedule_type: str,
        schedule_expression: str = None,
        interval_seconds: int = None,
        run_at: str = None,
        max_runs: int = None,
        timeout: int = 300,
        enabled: bool = True,
        parameters: Dict = None
    ):
        self.task_id = task_id
        self.task_name = task_name
        self.command = command
        self.schedule_type = schedule_type  # 'cron', 'interval', 'once'
        self.schedule_expression = schedule_expression
        self.interval_seconds = interval_seconds
        self.run_at = run_at
        self.max_runs = max_runs
        self.timeout = timeout
        self.enabled = enabled
        self.parameters = parameters or {}

        self.run_count = 0
        self.last_run = None
        self.next_run = None
        self.created_at = datetime.now().isoformat()

        # Calculate next run time
        self._calculate_next_run()

    def _calculate_next_run(self):
        """Calculate the next run time based on schedule."""
        now = datetime.now()

        if self.schedule_type == 'cron' and self.schedule_expression:
            if croniter:
                cron = croniter(self.schedule_expression, now)
                self.next_run = cron.get_next(datetime)
            else:
                logger.warning(f"croniter not available, cannot parse cron expression: {self.schedule_expression}")
                self.next_run = None

        elif self.schedule_type == 'interval' and self.interval_seconds:
            self.next_run = now + timedelta(seconds=self.interval_seconds)

        elif self.schedule_type == 'once' and self.run_at:
            # Parse ISO format datetime
            try:
                self.run_at_dt = datetime.fromisoformat(self.run_at.replace('Z', '+00:00'))
                if self.run_at_dt > now:
                    self.next_run = self.run_at_dt
                else:
                    self.next_run = None  # Already passed
            except:
                logger.error(f"Invalid datetime format: {self.run_at}")
                self.next_run = None

    def should_run(self) -> bool:
        """Check if task should run now."""
        if not self.enabled or not self.next_run:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        return datetime.now() >= self.next_run

    def execute(self) -> Dict[str, Any]:
        """Execute the scheduled task."""
        if DRY_RUN:
            logger.info(f"[DRY RUN] Would execute task: {self.task_name}")
            return {
                "status": "dry_run",
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat()
            }

        try:
            self.last_run = datetime.now().isoformat()
            self.run_count += 1

            # Execute command
            if self.command.startswith('python'):
                # Execute Python script/function
                result = subprocess.run(
                    self.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                success = result.returncode == 0

            else:
                # Execute shell command
                result = subprocess.run(
                    self.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                success = result.returncode == 0

            # Calculate next run
            self._calculate_next_run()

            # Log activity
            self._log_activity('task_executed', {
                'task_id': self.task_id,
                'success': success,
                'run_count': self.run_count
            })

            return {
                "status": "success" if success else "error",
                "task_id": self.task_id,
                "task_name": self.task_name,
                "timestamp": datetime.now().isoformat(),
                "run_count": self.run_count,
                "stdout": result.stdout if not success else None,
                "stderr": result.stderr if not success else None
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "task_id": self.task_id,
                "error": "Task execution timed out",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "task_id": self.task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "command": self.command,
            "schedule_type": self.schedule_type,
            "schedule_expression": self.schedule_expression,
            "interval_seconds": self.interval_seconds,
            "run_at": self.run_at,
            "max_runs": self.max_runs,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "parameters": self.parameters,
            "run_count": self.run_count,
            "last_run": self.last_run,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "created_at": self.created_at
        }

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "scheduler",
            "task_id": self.task_id,
            "dry_run": DRY_RUN
        }

        if details:
            log_entry.update(details)

        # Save to logs folder
        log_dir = Path(__file__).parent.parent.parent / "Bronze" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append(log_entry)

            if not DRY_RUN:
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")


class TaskScheduler:
    """Manages scheduled tasks."""

    def __init__(self, schedule_file: str = None):
        self.schedule_file = Path(schedule_file or SCHEDULE_FILE)
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_thread = None

        # Load existing tasks
        self._load_tasks()

    def _load_tasks(self):
        """Load tasks from schedule file."""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, 'r') as f:
                    tasks_data = json.load(f)

                for task_data in tasks_data:
                    task = ScheduledTask(
                        task_id=task_data['task_id'],
                        task_name=task_data['task_name'],
                        command=task_data['command'],
                        schedule_type=task_data['schedule_type'],
                        schedule_expression=task_data.get('schedule_expression'),
                        interval_seconds=task_data.get('interval_seconds'),
                        run_at=task_data.get('run_at'),
                        max_runs=task_data.get('max_runs'),
                        timeout=task_data.get('timeout', 300),
                        enabled=task_data.get('enabled', True),
                        parameters=task_data.get('parameters')
                    )

                    # Restore run count and last run
                    task.run_count = task_data.get('run_count', 0)
                    task.last_run = task_data.get('last_run')

                    self.tasks[task.task_id] = task

                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")

            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")

    def _save_tasks(self):
        """Save tasks to schedule file."""
        try:
            self.schedule_file.parent.mkdir(parents=True, exist_ok=True)

            tasks_data = [task.to_dict() for task in self.tasks.values()]

            with open(self.schedule_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    def schedule_task(self, task_params: Dict) -> Dict[str, Any]:
        """Schedule a new task."""
        try:
            task = ScheduledTask(
                task_id=task_params.get('task_id') or f"task_{int(time.time())}",
                task_name=task_params['task_name'],
                command=task_params['command'],
                schedule_type=task_params['schedule']['type'],
                schedule_expression=task_params['schedule'].get('expression'),
                interval_seconds=task_params['schedule'].get('interval_seconds'),
                run_at=task_params['schedule'].get('run_at'),
                max_runs=task_params.get('max_runs'),
                timeout=task_params.get('timeout', 300),
                enabled=task_params.get('enabled', True),
                parameters=task_params.get('parameters')
            )

            self.tasks[task.task_id] = task
            self._save_tasks()

            logger.info(f"Scheduled task: {task.task_name} ({task.task_id})")

            return {
                "status": "success",
                "action": "schedule",
                "timestamp": datetime.now().isoformat(),
                "task_id": task.task_id,
                "task_name": task.task_name,
                "scheduled": True,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "schedule_type": task.schedule_type
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def remove_task(self, task_id: str) -> Dict[str, Any]:
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()

            return {
                "status": "success",
                "action": "remove",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"Task {task_id} removed"
            }

        else:
            return {
                "status": "error",
                "error": f"Task not found: {task_id}",
                "timestamp": datetime.now().isoformat()
            }

    def list_tasks(self) -> List[Dict]:
        """List all scheduled tasks."""
        return [task.to_dict() for task in self.tasks.values()]

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a specific task."""
        return self.tasks.get(task_id)

    def enable_task(self, task_id: str) -> Dict[str, Any]:
        """Enable a task."""
        task = self.get_task(task_id)
        if task:
            task.enabled = True
            self._save_tasks()

            return {
                "status": "success",
                "action": "enable",
                "task_id": task_id,
                "enabled": True,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "error",
            "error": f"Task not found: {task_id}",
            "timestamp": datetime.now().isoformat()
        }

    def disable_task(self, task_id: str) -> Dict[str, Any]:
        """Disable a task."""
        task = self.get_task(task_id)
        if task:
            task.enabled = False
            self._save_tasks()

            return {
                "status": "success",
                "action": "disable",
                "task_id": task_id,
                "enabled": False,
                "timestamp": datetime.now().isoformat()
            }

        return {
            "status": "error",
            "error": f"Task not found: {task_id}",
            "timestamp": datetime.now().isoformat()
        }

    def start(self, check_interval: int = 60):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True

        def run_scheduler():
            logger.info("Scheduler started")

            while self.running:
                try:
                    for task in self.tasks.values():
                        if task.should_run():
                            logger.info(f"Executing task: {task.task_name}")
                            result = task.execute()

                            if result.get('status') == 'error':
                                logger.error(f"Task failed: {result.get('error')}")

                    time.sleep(check_interval)

                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(check_interval)

            logger.info("Scheduler stopped")

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)


def scheduler_handler(input_params: Dict) -> Dict[str, Any]:
    """Main handler function for Scheduler skill."""
    action = input_params.get('action', 'schedule')

    # Initialize scheduler
    scheduler = TaskScheduler()

    try:
        if action == 'schedule':
            return scheduler.schedule_task(input_params)

        elif action == 'list':
            return {
                "status": "success",
                "action": "list",
                "timestamp": datetime.now().isoformat(),
                "tasks": scheduler.list_tasks()
            }

        elif action == 'remove':
            return scheduler.remove_task(input_params.get('task_id'))

        elif action == 'enable':
            return scheduler.enable_task(input_params.get('task_id'))

        elif action == 'disable':
            return scheduler.disable_task(input_params.get('task_id'))

        elif action == 'start':
            scheduler.start(check_interval=input_params.get('check_interval', 60))

            return {
                "status": "success",
                "action": "start",
                "timestamp": datetime.now().isoformat(),
                "message": "Scheduler started"
            }

        elif action == 'stop':
            scheduler.stop()

            return {
                "status": "success",
                "action": "stop",
                "timestamp": datetime.now().isoformat(),
                "message": "Scheduler stopped"
            }

        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Example usage
if __name__ == "__main__":
    # Example: Schedule email check every 30 minutes
    params = {
        "action": "schedule",
        "task_name": "Email Checker",
        "command": "python gmail_reader.md",
        "schedule": {
            "type": "cron",
            "expression": "*/30 * * * *"  # Every 30 minutes
        },
        "enabled": True
    }

    result = scheduler_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **gmail_reader** - Schedule periodic email checks
- **whatsapp_monitor** - Schedule WhatsApp monitoring
- **linkedin_poster** - Schedule social media posts
- **orchestrator** - Schedule task processing runs
- All other Silver skills for background execution

## Cron Expression Examples

```
*/30 * * * *     - Every 30 minutes
0 */2 * * *      - Every 2 hours
0 9 * * 1-5      - 9am Monday to Friday
0 0 * * *        - Midnight daily
0 0 * * 0        - Midnight Sunday
*/15 9-17 * * *  - Every 15 minutes, 9am-5pm
0 9,12,17 * * *  - 9am, 12pm, 5pm daily
```

## Error Handling

1. **Task Timeout** - Kill process after timeout period
2. **Invalid Cron Expression** - Validate before scheduling
3. **Command Not Found** - Return error with command details
4. **Max Runs Exceeded** - Disable task automatically
5. **Schedule File Corrupted** - Recreate with default tasks

## Best Practices

1. **Check Interval**: Use 60 seconds for most cases
2. **Timeout**: Set appropriate timeout per task type
3. **Max Runs**: Use for one-time or limited-run tasks
4. **Task IDs**: Use descriptive, unique identifiers
5. **Logging**: All task executions logged to Bronze/Logs/

## Testing

```bash
# Schedule a task
export DRY_RUN=false
python scheduler.md --action schedule \
  --task_name "Test Task" \
  --command "echo 'Hello'" \
  --schedule "interval" \
  --interval_seconds 60

# List all tasks
python scheduler.md --action list

# Start scheduler
python scheduler.md --action start --check_interval 30
```

## Persistence

Scheduled tasks are saved to: `Silver/Config/scheduled_tasks.json`

Tasks persist across scheduler restarts with:
- Run count
- Last run time
- Next scheduled run
- Enabled/disabled state
