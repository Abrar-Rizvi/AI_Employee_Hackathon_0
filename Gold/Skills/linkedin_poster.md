---
name: linkedin-poster
description: Auto-post content to LinkedIn for business promotion. Schedule posts, manage drafts, and track engagement metrics.
license: Apache-2.0
compatibility: Requires linkedin-api, selenium, or LinkedIn Marketing API
metadata:
  author: AI Employee Silver Tier
  version: "1.0"
  tier: silver
  api: "LinkedIn API / LinkedIn UAPI"
---

# LinkedIn Poster Skill

## Purpose
Automate posting content to LinkedIn for business promotion and professional networking. This skill enables the AI Employee to schedule and publish posts, manage drafts, and track engagement metrics while maintaining compliance with approval requirements for social media posts.

## When to Use This Skill
- Publishing company updates and announcements
- Sharing industry insights and thought leadership
- Promoting products or services
- Scheduling posts for optimal times
- Managing content calendar
- Tracking post performance metrics

## Input Parameters

```json
{
  "action": "post|schedule|get_drafts|delete|get_metrics",
  "credentials": {
    "access_token": "LinkedIn access token",
    "person_urn": "urn:li:person:abc123",
    "organization_urn": "urn:li:organization:123456"
  },
  "content": {
    "text": "Post content here...",
    "media_urls": ["https://example.com/image.jpg"],
    "hashtags": ["#AI", "#Automation"],
    "mentions": ["urn:li:person:xyz789"]
  },
  "post_visibility": "PUBLIC|CONNECTIONS|CONTAINER",
  "scheduled_time": "2026-02-24T12:00:00",
  "dry_run": true,
  "requires_approval": true
}
```

## Output Format

```json
{
  "status": "success",
  "action": "post",
  "timestamp": "2026-02-24T12:00:00",
  "post_id": "urn:li:activity:1234567890",
  "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:1234567890",
  "scheduled": false,
  "visibility": "PUBLIC",
  "content_preview": "Post content here...",
  "approval_status": "granted",
  "metrics": {
    "views": 0,
    "likes": 0,
    "comments": 0,
    "shares": 0
  }
}
```

## Python Implementation

```python
#!/usr/bin/env python3
"""
LinkedIn Poster Skill for Silver Tier AI Employee
Auto-post content to LinkedIn with approval workflow.
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

try:
    import requests
except ImportError:
    print("Error: requests not found. Install with: pip install requests")
    raise

# Configuration
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
LINKEDIN_UGC_API_BASE = "https://api.linkedin.com/v2/ugcPosts"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInPoster:
    """Post content to LinkedIn with approval workflow."""

    def __init__(
        self,
        access_token: str,
        person_urn: str = None,
        organization_urn: str = None
    ):
        self.access_token = access_token
        self.person_urn = person_urn
        self.organization_urn = organization_urn
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

    def post_content(
        self,
        text: str,
        media_urls: List[str] = None,
        hashtags: List[str] = None,
        mentions: List[str] = None,
        visibility: str = 'PUBLIC',
        schedule_time: str = None,
        approval_granted: bool = False
    ) -> Dict[str, Any]:
        """Post content to LinkedIn."""
        try:
            # Check approval requirement (per Company_Handbook.md)
            if not approval_granted:
                return {
                    "status": "requires_approval",
                    "action": "post",
                    "timestamp": datetime.now().isoformat(),
                    "reason": "Social media posts require approval per Company_Handook.md",
                    "content_preview": text[:200] + "..." if len(text) > 200 else text,
                    "approval_required": True
                }

            # Determine author (person or organization)
            author = self.organization_urn or self.person_urn
            if not author:
                return {
                    "status": "error",
                    "error": "No author URN provided (person_urn or organization_urn required)",
                    "timestamp": datetime.now().isoformat()
                }

            # Build post content
            post_content = self._build_post_content(
                text=text,
                media_urls=media_urls,
                hashtags=hashtags,
                mentions=mentions
            )

            # Create post request body
            post_body = {
                "author": author,
                "lifecycleState": "PUBLISHED" if not schedule_time else "SCHEDULED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            # Add media if provided
            if media_urls:
                post_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                # Note: Media upload requires separate API calls
                # This is a simplified version

            if schedule_time:
                post_body["scheduledPublishTime"] = schedule_time

            if DRY_RUN:
                logger.info(f"[DRY RUN] Would post to LinkedIn:")
                logger.info(f"  Author: {author}")
                logger.info(f"  Content: {text[:100]}...")

                return {
                    "status": "dry_run",
                    "action": "post",
                    "timestamp": datetime.now().isoformat(),
                    "content_preview": text[:200],
                    "scheduled": schedule_time is not None
                }

            # Make API request
            response = requests.post(
                LINKEDIN_UGC_API_BASE,
                headers=self.headers,
                json=post_body
            )

            if response.status_code == 201:
                post_data = response.json()
                post_id = post_data.get('id')

                # Log activity
                self._log_activity('linkedin_posted', {
                    'post_id': post_id,
                    'scheduled': schedule_time is not None,
                    'visibility': visibility
                })

                # Generate post URL
                post_url = f"https://www.linkedin.com/feed/update/{post_id}"

                return {
                    "status": "success",
                    "action": "post",
                    "timestamp": datetime.now().isoformat(),
                    "post_id": post_id,
                    "post_url": post_url,
                    "scheduled": schedule_time is not None,
                    "scheduled_time": schedule_time,
                    "visibility": visibility,
                    "content_preview": text[:200],
                    "approval_status": "granted",
                    "metrics": {
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "shares": 0
                    }
                }

            else:
                return {
                    "status": "error",
                    "error": f"LinkedIn API error: {response.status_code} - {response.text}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def schedule_post(
        self,
        text: str,
        schedule_time: str,
        media_urls: List[str] = None,
        hashtags: List[str] = None,
        mentions: List[str] = None,
        visibility: str = 'PUBLIC'
    ) -> Dict[str, Any]:
        """Schedule a post for future publication."""
        return self.post_content(
            text=text,
            media_urls=media_urls,
            hashtags=hashtags,
            mentions=mentions,
            visibility=visibility,
            schedule_time=schedule_time
        )

    def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get engagement metrics for a post."""
        try:
            # LinkedIn API requires specific permissions for metrics
            # This is a simplified implementation
            url = f"{LINKEDIN_API_BASE}/socialActions/{post_id}"

            response = requests.get(
                url,
                headers=self.headers
            )

            if response.status_code == 200:
                data = response.json()

                return {
                    "status": "success",
                    "action": "get_metrics",
                    "timestamp": datetime.now().isoformat(),
                    "post_id": post_id,
                    "metrics": {
                        "likes": data.get('numLikes', 0),
                        "comments": data.get('numComments', 0),
                        "shares": data.get('numShares', 0),
                        "views": data.get('impressions', 0)
                    }
                }

            else:
                return {
                    "status": "error",
                    "error": f"Failed to get metrics: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a post."""
        try:
            url = f"{LINKEDIN_UGC_API_BASE}/{post_id}"

            if DRY_RUN:
                logger.info(f"[DRY RUN] Would delete post: {post_id}")

                return {
                    "status": "dry_run",
                    "action": "delete",
                    "post_id": post_id,
                    "timestamp": datetime.now().isoformat()
                }

            response = requests.delete(url, headers=self.headers)

            if response.status_code == 204:
                self._log_activity('linkedin_post_deleted', {'post_id': post_id})

                return {
                    "status": "success",
                    "action": "delete",
                    "post_id": post_id,
                    "timestamp": datetime.now().isoformat()
                }

            else:
                return {
                    "status": "error",
                    "error": f"Failed to delete post: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _build_post_content(
        self,
        text: str,
        media_urls: List[str] = None,
        hashtags: List[str] = None,
        mentions: List[str] = None
    ) -> str:
        """Build the complete post content with hashtags and mentions."""
        content = text

        # Add mentions at the beginning
        if mentions:
            mention_text = ' '.join(mentions)
            content = f"{mention_text}\n\n{content}"

        # Add hashtags at the end
        if hashtags:
            hashtag_text = ' '.join(hashtags)
            content = f"{content}\n\n{hashtag_text}"

        return content

    def _log_activity(self, action: str, details: Dict = None):
        """Log activity to JSON file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "skill": "linkedin_poster",
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


class LinkedInScheduler:
    """Schedule LinkedIn posts for optimal times."""

    def __init__(self, poster: LinkedInPoster):
        self.poster = poster
        self.scheduled_posts = []

    def schedule_post(
        self,
        text: str,
        schedule_time: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Schedule a post and track it."""
        result = self.poster.schedule_post(
            text=text,
            schedule_time=schedule_time,
            **kwargs
        )

        if result.get('status') == 'success':
            self.scheduled_posts.append({
                'post_id': result.get('post_id'),
                'scheduled_time': schedule_time,
                'content': text[:100]
            })

        return result

    def get_scheduled_posts(self) -> List[Dict]:
        """Get all scheduled posts."""
        return self.scheduled_posts


def linkedin_poster_handler(input_params: Dict) -> Dict:
    """Main handler function for LinkedIn Poster skill."""
    action = input_params.get('action', 'post')
    credentials = input_params.get('credentials', {})

    # Initialize poster
    poster = LinkedInPoster(
        access_token=credentials.get('access_token'),
        person_urn=credentials.get('person_urn'),
        organization_urn=credentials.get('organization_urn')
    )

    content = input_params.get('content', {})

    try:
        if action == 'post':
            return poster.post_content(
                text=content.get('text', ''),
                media_urls=content.get('media_urls', []),
                hashtags=content.get('hashtags', []),
                mentions=content.get('mentions', []),
                visibility=input_params.get('post_visibility', 'PUBLIC'),
                schedule_time=input_params.get('scheduled_time'),
                approval_granted=input_params.get('approval_granted', False)
            )

        elif action == 'schedule':
            return poster.schedule_post(
                text=content.get('text', ''),
                schedule_time=input_params.get('scheduled_time'),
                media_urls=content.get('media_urls', []),
                hashtags=content.get('hashtags', []),
                mentions=content.get('mentions', []),
                visibility=input_params.get('post_visibility', 'PUBLIC')
            )

        elif action == 'get_metrics':
            return poster.get_post_metrics(
                post_id=input_params.get('post_id')
            )

        elif action == 'delete':
            return poster.delete_post(
                post_id=input_params.get('post_id')
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
    # Example: Post to LinkedIn
    params = {
        "action": "post",
        "credentials": {
            "access_token": "your_access_token_here",
            "organization_urn": "urn:li:organization:123456"
        },
        "content": {
            "text": "Excited to announce our new AI-powered automation platform! #AI #Automation",
            "hashtags": ["#AI", "#Automation", "#Innovation"]
        },
        "post_visibility": "PUBLIC",
        "approval_granted": True
    }

    result = linkedin_poster_handler(params)
    print(json.dumps(result, indent=2))
```

## Integration Points

This skill integrates with:
- **approval_manager** - Manages approval workflow for posts
- **scheduler** - Schedules posts for optimal times
- **Company_Handbook.md** - Enforces approval rules
- **data_extractor** - Extracts post performance metrics

## Approval Workflow

Per Company_Handbook.md, **all social media posts require approval**:

1. **Draft Creation** - Create post with approval_required=true
2. **Human Review** - Manager reviews content
3. **Approval Granted** - Re-submit with approval_granted=true
4. **Publish** - Post published to LinkedIn

## Best Practices

1. **Optimal Times**: Post 9-11am or 2-4pm on weekdays
2. **Hashtags**: Use 3-5 relevant hashtags
3. **Media**: Include images/videos for higher engagement
4. **Length**: Keep posts under 3,000 characters
5. **Mentions**: Tag relevant people and companies

## Error Handling

1. **Authentication Error** - Refresh access token
2. **Rate Limit Exceeded** - Implement backoff and retry
3. **Invalid URN** - Validate person/organization URN
4. **Media Upload Failed** - Check URL validity and format
5. **Post Rejected** - Review content policy compliance

## Security Notes

- Access tokens should be stored securely (environment variables)
- Tokens have limited lifetime (~60 days)
- Organization posts require Marketing API access
- Personal posts require Member API access
- DRY_RUN mode for testing without posting

## Testing

```bash
# Test in dry-run mode
export DRY_RUN=true
python linkedin_poster.md

# Test with actual LinkedIn API
export DRY_RUN=false
export LINKEDIN_ACCESS_TOKEN="your_token"
python linkedin_poster.md
```

## LinkedIn API Setup

1. **Create LinkedIn App**: https://www.linkedin.com/developers/
2. **Enable Permissions**:
   - w_member_social (posts)
   - w_organization_social (organization posts)
   - r_liteprofile (profile data)
3. **Get Access Token**: OAuth 2.0 flow
4. **Get URN**: From profile or organization page
