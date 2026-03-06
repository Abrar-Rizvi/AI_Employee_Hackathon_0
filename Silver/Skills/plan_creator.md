---
name: plan-creator
description: Create detailed Plan.md files with Claude reasoning loop. Generate structured plans with multiple iterations for complex problem-solving.
license: Apache-2.0
compatibility: Requires Claude API or Anthropic SDK
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  model: "Claude Sonnet 4.5"
---

# Plan Creator Skill

## Purpose
Create detailed, multi-step Plan.md files using Claude's reasoning capabilities. This skill enables the AI Employee to break down complex tasks into actionable steps, iterate on plans based on feedback, and maintain structured planning documentation.

## When to Use This Skill
- Creating execution plans for complex projects
- Breaking down ambiguous requests into steps
- Iterative planning with human feedback
- Multi-step reasoning for problem-solving
- Task decomposition for automation
- Strategic planning and analysis

## Input Parameters

```json
{
  "action": "create|iterate|refine|validate",
  "goal": "Launch new product marketing campaign",
  "context": "Product is AI-powered automation tool",
  "constraints": [
    "Budget under $10,000",
    "Timeline 6 weeks",
    "Focus on tech industry"
  ],
  "iterations": 3,
  "plan_file": "/path/to/Plan.md",
  "previous_plan": "/path/to/previous/Plan.md",
  "feedback": "Focus more on LinkedIn strategy",
  "include_reasoning": true,
  "claude_model": "claude-sonnet-4-5"
}
```

## Output Format

```json
{
  "status": "success",
  "action": "create",
  "timestamp": "2026-02-24T12:00:00",
  "plan_id": "plan_001",
  "plan_file": "/path/to/Plan.md",
  "iterations": 3,
  "final_iteration": 3,
  "goal": "Launch new product marketing campaign",
  "steps_count": 12,
  "estimated_duration": "6 weeks",
  "reasoning_summary": "Based on constraints and context...",
  "confidence": 0.85
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
Plan Creator Skill for Silver Tier AI Employee
Create detailed Plan.md files with Claude reasoning loop.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    import anthropic
except ImportError:
    print("Error: anthropic not found. Install with: pip install anthropic")
    raise

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlanCreator:
    """Create detailed plans using Claude reasoning."""

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or CLAUDE_API_KEY
        self.model = model
        self.client = None

        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def create_plan(
        self,
        goal: str,
        context: str = None,
        constraints: List[str] = None,
        iterations: int = 3,
        plan_file: str = None,
        include_reasoning: bool = True
    ) -> Dict[str, Any]:
        """Create a detailed plan with multiple reasoning iterations."""

        if not self.client:
            return {
                "status": "error",
                "error": "Claude client not initialized (missing API key)",
                "timestamp": datetime.now().isoformat()
            }

        try:
            current_plan = None
            reasoning_history = []

            for iteration in range(1, iterations + 1):
                logger.info(f"Planning iteration {iteration}/{iterations}")

                # Build prompt for this iteration
                prompt = self._build_prompt(
                    goal=goal,
                    context=context,
                    constraints=constraints,
                    current_plan=current_plan,
                    iteration=iteration,
                    total_iterations=iterations
                )

                # Call Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                # Extract plan content
                plan_content = response.content[0].text
                reasoning = response.content[0].text if include_reasoning else None

                reasoning_history.append({
                    "iteration": iteration,
                    "reasoning": reasoning,
                    "timestamp": datetime.now().isoformat()
                })

                # Parse plan structure
                current_plan = self._parse_plan(plan_content)

                if iteration < iterations:
                    # Prepare for next iteration
                    current_plan['feedback_needed'] = True

            # Generate final plan file
            plan_file_path = self._save_plan(
                plan=current_plan,
                goal=goal,
                plan_file=plan_file,
                reasoning_history=reasoning_history if include_reasoning else None
            )

            # Log activity
            self._log_activity('plan_created', {
                'plan_id': current_plan.get('plan_id'),
                'goal': goal,
                'iterations': iterations,
                'steps_count': len(current_plan.get('steps', []))
            })

            return {
                "status": "success",
                "action": "create",
                "timestamp": datetime.now().isoformat(),
                "plan_id": current_plan.get('plan_id'),
                "plan_file": str(plan_file_path),
                "iterations": iterations,
                "final_iteration": iterations,
                "goal": goal,
                "steps_count": len(current_plan.get('steps', [])),
                "estimated_duration": current_plan.get('estimated_duration'),
                "reasoning_summary": reasoning_history[-1]['reasoning'][:500] if reasoning_history else None,
                "confidence": current_plan.get('confidence', 0.8)
            }

        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def iterate_plan(
        self,
        previous_plan_file: str,
        feedback: str,
        iterations: int = 1
    ) -> Dict[str, Any]:
        """Refine an existing plan based on feedback."""
        try:
            # Read previous plan
            plan_path = Path(previous_plan_file)
            if not plan_path.exists():
                return {
                    "status": "error",
                    "error": f"Plan file not found: {previous_plan_file}",
                    "timestamp": datetime.now().isoformat()
                }

            with open(plan_path, 'r') as f:
                previous_content = f.read()

            # Extract plan data
            previous_plan = self._parse_plan_from_markdown(previous_content)

            # Build refinement prompt
            prompt = f"""You are refining an existing plan based on feedback.

Previous Plan:
{previous_content}

Feedback:
{feedback}

Please analyze the feedback and create an improved version of the plan that addresses the feedback. Maintain the same structure but improve the content where needed.

Format your response as a markdown plan with:
- Updated goal (if changed)
- Revised steps addressing feedback
- Updated timeline (if needed)
- Confidence assessment
- Changes made summary
"""

            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            refined_plan = response.content[0].text
            refined_plan_data = self._parse_plan(refined_plan)

            # Save refined plan
            new_plan_file = plan_path.parent / f"{plan_path.stem}_v{previous_plan.get('version', 1) + 1}{plan_path.suffix}"

            if not DRY_RUN:
                with open(new_plan_file, 'w') as f:
                    f.write(refined_plan)

            return {
                "status": "success",
                "action": "iterate",
                "timestamp": datetime.now().isoformat(),
                "previous_plan": str(plan_path),
                "new_plan": str(new_plan_file),
                "iterations": iterations,
                "feedback_applied": feedback
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def validate_plan(self, plan_file: str) -> Dict[str, Any]:
        """Validate a plan against best practices."""
        try:
            plan_path = Path(plan_file)
            if not plan_path.exists():
                return {
                    "status": "error",
                    "error": f"Plan file not found: {plan_file}",
                    "timestamp": datetime.now().isoformat()
                }

            with open(plan_path, 'r') as f:
                content = f.read()

            # Validation checks
            checks = {
                "has_goal": bool(re.search(r'#+\s*Goal', content, re.I)),
                "has_steps": bool(re.search(r'#+\s*Steps?', content, re.I)),
                "has_timeline": bool(re.search(r'#+\s*Timeline|Duration', content, re.I)),
                "has_resources": bool(re.search(r'#+\s*Resources?', content, re.I)),
                "step_count": len(re.findall(r'^\s*-\s+\*\*', content, re.M)),
                "has_confidence": bool(re.search(r'confidence', content, re.I)),
                "has_dependencies": bool(re.search(r'depend|require|after', content, re.I))
            }

            # Calculate score
            score = sum(1 for v in checks.values() if v is True)
            total = len([k for k in checks.keys() if k != "step_count"])
            percentage = (score / total) * 100 if total > 0 else 0

            validation_result = {
                "status": "success",
                "action": "validate",
                "timestamp": datetime.now().isoformat(),
                "plan_file": str(plan_path),
                "validation_checks": checks,
                "score": percentage,
                "is_valid": percentage >= 70,
                "recommendations": []
            }

            # Generate recommendations
            if not checks["has_goal"]:
                validation_result["recommendations"].append("Add a clear goal section")
            if checks["step_count"] < 3:
                validation_result["recommendations"].append("Add more detailed steps (minimum 3)")
            if not checks["has_timeline"]:
                validation_result["recommendations"].append("Add a timeline or duration estimate")
            if not checks["has_resources"]:
                validation_result["recommendations"].append("List required resources")

            return validation_result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _build_prompt(
        self,
        goal: str,
        context: str,
        constraints: List[str],
        current_plan: Dict,
        iteration: int,
        total_iterations: int
    ) -> str:
        """Build prompt for Claude API."""

        prompt_parts = [
            f"You are an expert planning assistant. Create a detailed, actionable plan for the following goal.",
            "",
            f"## Goal",
            f"{goal}",
            ""
        ]

        if context:
            prompt_parts.extend([
                f"## Context",
                f"{context}",
                ""
            ])

        if constraints:
            prompt_parts.extend([
                f"## Constraints",
                ""
            ])
            for i, constraint in enumerate(constraints, 1):
                prompt_parts.append(f"{i}. {constraint}")
            prompt_parts.append("")

        if current_plan and iteration > 1:
            prompt_parts.extend([
                f"## Current Plan (Iteration {iteration - 1})",
                f"Review and improve upon this plan:",
                "",
                f"```",
                f"Steps: {len(current_plan.get('steps', []))}",
                f"Duration: {current_plan.get('estimated_duration', 'Unknown')}",
                f"Confidence: {current_plan.get('confidence', 'Unknown')}",
                f"```",
                ""
            ])

        prompt_parts.extend([
            f"## Instructions",
            f"",
            f"Create a detailed plan with the following structure:",
            f"",
            f"1. **Goal Summary**: Brief overview of what needs to be achieved",
            f"2. **Approach**: High-level strategy for accomplishing the goal",
            f"3. **Detailed Steps**: 8-12 concrete, actionable steps",
            f"4. **Timeline**: Estimated duration and key milestones",
            f"5. **Resources Required**: Tools, skills, budget, dependencies",
            f"6. **Risk Assessment**: Potential obstacles and mitigation strategies",
            f"7. **Success Criteria**: How to measure completion",
            f"8. **Confidence**: Your confidence level (0-1) and reasoning",
            f"",
            f"Format your response as clean markdown with clear sections.",
            f"",
            f"This is iteration {iteration} of {total_iterations}. ",
            f"{'Focus on creating the initial plan.' if iteration == 1 else 'Refine and improve the plan with deeper reasoning.'}",
            ""
        ])

        return "\n".join(prompt_parts)

    def _parse_plan(self, plan_content: str) -> Dict:
        """Parse structured plan from markdown content."""
        import re

        plan = {
            "plan_id": f"plan_{int(time.time())}",
            "created_at": datetime.now().isoformat(),
            "raw_content": plan_content
        }

        # Extract goal
        goal_match = re.search(r'#+\s*Goal\s*\n+(.+?)(?:\n#{1,3}|\Z)', plan_content, re.I | re.DOTALL)
        if goal_match:
            plan["goal"] = goal_match.group(1).strip()

        # Extract steps
        steps = []
        step_matches = re.findall(r'^\s*-\s+\*\*(.+?)\*\*:\s*(.+)', plan_content, re.M)
        for step_num, (step_title, step_desc) in enumerate(step_matches, 1):
            steps.append({
                "step": step_num,
                "title": step_title,
                "description": step_desc.strip()
            })
        plan["steps"] = steps

        # Extract timeline
        timeline_match = re.search(r'#+\s*Timeline\s*\n+(.+?)(?:\n#{1,3}|\Z)', plan_content, re.I | re.DOTALL)
        if timeline_match:
            plan["timeline"] = timeline_match.group(1).strip()

        # Extract duration
        duration_match = re.search(r'(\d+)\s+(week|day|hour|month)', plan_content, re.I)
        if duration_match:
            plan["estimated_duration"] = f"{duration_match.group(1)} {duration_match.group(2)}s"

        # Extract confidence
        confidence_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', plan_content, re.I)
        if confidence_match:
            plan["confidence"] = float(confidence_match.group(1))

        return plan

    def _parse_plan_from_markdown(self, content: str) -> Dict:
        """Parse plan from existing markdown file."""
        return self._parse_plan(content)

    def _save_plan(
        self,
        plan: Dict,
        goal: str,
        plan_file: str = None,
        reasoning_history: List[Dict] = None
    ) -> Path:
        """Save plan to markdown file."""

        bronze_dir = Path(__file__).parent.parent.parent / "Bronze"
        plans_folder = bronze_dir / "Plans"
        plans_folder.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if not plan_file:
            safe_goal = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in goal)[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            plan_file = plans_folder / f"plan_{timestamp}_{safe_goal}.md"

        plan_path = Path(plan_file)

        # Build markdown content
        content = f"""---
type: plan
created: {datetime.now().isoformat()}
goal: {goal[:100]}
steps: {len(plan.get('steps', []))}
confidence: {plan.get('confidence', 0.8)}
---

# {goal}

## Overview
Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Estimated Duration: {plan.get('estimated_duration', 'TBD')}
Confidence: {plan.get('confidence', 0.8) * 100:.0f}%

## Approach
{plan.get('approach', 'Execute plan systematically with regular review points.')}

## Steps

"""

        for step in plan.get('steps', []):
            content += f"### {step['title']}\n\n{step['description']}\n\n"

        content += f"""
## Timeline
{plan.get('timeline', 'To be determined based on execution')}

## Resources Required
{plan.get('resources', '- Skills: To be identified\\n- Tools: To be determined\\n- Budget: TBD')}

## Risk Assessment
{plan.get('risks', '- Identify risks during execution\\n- Mitigation: Address as they arise')}

## Success Criteria
- Plan fully executed
- Goal achieved
- Lessons documented

---

## Reasoning History
"""

        if reasoning_history:
            for entry in reasoning_history:
                content += f"\n### Iteration {entry['iteration']}\n"
                content += f"**Time:** {entry['timestamp']}\n\n"
                content += f"{entry['reasoning'][:500]}...\n\n"

        if not DRY_RUN:
            with open(plan_path, 'w') as f:
                f.write(content)

        logger.info(f"Plan saved to: {plan_path}")
        return plan_path

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "plan_creator",
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


def plan_creator_handler(input_params: Dict) -> Dict[str, Any]:
    """Main handler function for Plan Creator skill."""
    action = input_params.get('action', 'create')

    creator = PlanCreator(
        api_key=input_params.get('api_key') or os.getenv('ANTHROPIC_API_KEY'),
        model=input_params.get('claude_model', 'claude-sonnet-4-20250514')
    )

    try:
        if action == 'create':
            return creator.create_plan(
                goal=input_params['goal'],
                context=input_params.get('context'),
                constraints=input_params.get('constraints', []),
                iterations=input_params.get('iterations', 3),
                plan_file=input_params.get('plan_file'),
                include_reasoning=input_params.get('include_reasoning', True)
            )

        elif action == 'iterate':
            return creator.iterate_plan(
                previous_plan_file=input_params['previous_plan'],
                feedback=input_params.get('feedback', ''),
                iterations=input_params.get('iterations', 1)
            )

        elif action == 'validate':
            return creator.validate_plan(
                plan_file=input_params.get('plan_file')
            )

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
    # Example: Create a marketing plan
    params = {
        "action": "create",
        "goal": "Launch new AI automation tool to tech industry",
        "context": "B2B SaaS product, $10k budget, 6 week timeline",
        "constraints": [
            "Budget under $10,000",
            "Timeline: 6 weeks",
            "Target: Tech industry decision makers"
        ],
        "iterations": 3
    }

    result = plan_creator_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **orchestrator** - Execute plans step by step
- **task_planner** (Bronze) - Simple task planning
- **approval_manager** - Get plan approval before execution
- **scheduler** - Schedule plan execution steps
- All Bronze tier skills for plan execution

## Best Practices

1. **Iterations**: Use 2-3 iterations for complex plans
2. **Context**: Provide as much context as possible
3. **Constraints**: List all limitations upfront
4. **Validation**: Always validate plans before execution
5. **Feedback Loop**: Iterate based on human feedback

## Error Handling

1. **API Key Missing** - Return error with setup instructions
2. **API Rate Limit** - Implement exponential backoff
3. **Invalid Plan Format** - Retry with clarifying prompt
4. **File Write Error** - Log and return alternative path
5. **Parse Failure** - Return raw content as fallback

## Testing

```bash
# Set up Claude API key
export ANTHROPIC_API_KEY="your-api-key"

# Create a plan
python plan_creator.md --action create \
  --goal "Launch product" \
  --iterations 3

# Validate existing plan
python plan_creator.md --action validate \
  --plan_file "./Bronze/Plans/plan_xxx.md"

# Iterate on plan with feedback
python plan_creator.md --action iterate \
  --previous_plan "./Bronze/Plans/plan_xxx.md" \
  --feedback "Add more LinkedIn focus"
```

## Plan File Format

Plans are saved as markdown in `Bronze/Plans/` with:
- YAML frontmatter (metadata)
- Goal and overview
- Step-by-step instructions
- Timeline and resources
- Reasoning history (if enabled)
