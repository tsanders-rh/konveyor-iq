"""
Fetch and parse Konveyor rules from the ruleset repository.
"""
import yaml
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import re


class KonveyorRuleFetcher:
    """Fetch Konveyor rule definitions from GitHub."""

    def __init__(self):
        """Initialize the rule fetcher with a cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}

    def fetch_rule(self, source_url: str, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific rule from a Konveyor ruleset.

        Args:
            source_url: GitHub URL to the ruleset file
            rule_id: The rule ID to fetch

        Returns:
            Dictionary with rule details (message, description, etc.) or None if not found
        """
        # Check cache first
        cache_key = f"{source_url}#{rule_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Convert GitHub blob URL to raw content URL
        raw_url = self._convert_to_raw_url(source_url)
        if not raw_url:
            print(f"Warning: Could not convert URL to raw format: {source_url}")
            return None

        # Fetch and parse the ruleset
        try:
            response = requests.get(raw_url, timeout=10)
            response.raise_for_status()

            # Parse YAML content
            ruleset_data = yaml.safe_load(response.text)

            # Find the specific rule
            rule_data = self._find_rule_by_id(ruleset_data, rule_id)

            if rule_data:
                # Cache the result
                self._cache[cache_key] = rule_data
                return rule_data
            else:
                print(f"Warning: Rule '{rule_id}' not found in {source_url}")
                return None

        except requests.RequestException as e:
            print(f"Warning: Failed to fetch rule from {raw_url}: {e}")
            return None
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse YAML from {raw_url}: {e}")
            return None

    def _convert_to_raw_url(self, github_url: str) -> Optional[str]:
        """
        Convert GitHub blob URL to raw content URL.

        Args:
            github_url: GitHub blob URL (e.g., https://github.com/.../blob/main/file.yaml)

        Returns:
            Raw content URL or None if conversion fails
        """
        # Pattern: https://github.com/user/repo/blob/branch/path
        # Convert to: https://raw.githubusercontent.com/user/repo/branch/path

        if "raw.githubusercontent.com" in github_url:
            return github_url

        blob_pattern = r'https://github\.com/([^/]+)/([^/]+)/blob/(.+)'
        match = re.match(blob_pattern, github_url)

        if match:
            user, repo, path = match.groups()
            return f"https://raw.githubusercontent.com/{user}/{repo}/{path}"

        return None

    def _find_rule_by_id(self, ruleset_data: Any, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a rule by ID in the ruleset data.

        Args:
            ruleset_data: Parsed YAML ruleset
            rule_id: Rule ID to find

        Returns:
            Rule data dictionary or None
        """
        if not isinstance(ruleset_data, list):
            return None

        for item in ruleset_data:
            if not isinstance(item, dict):
                continue

            # Konveyor rulesets are flat lists where each item IS a rule
            if item.get("ruleID") == rule_id:
                # Extract relevant fields
                return {
                    "rule_id": item.get("ruleID"),
                    "message": item.get("message", ""),
                    "description": item.get("description", ""),
                    "category": item.get("category", ""),
                    "effort": item.get("effort", 0),
                    "labels": item.get("labels", [])
                }

            # Also check if this item has nested rules (for compatibility)
            if "rules" in item:
                rules = item.get("rules", [])
                for rule in rules:
                    if isinstance(rule, dict) and rule.get("ruleID") == rule_id:
                        # Extract relevant fields
                        return {
                            "rule_id": rule.get("ruleID"),
                            "message": rule.get("message", ""),
                            "description": rule.get("description", ""),
                            "category": rule.get("category", ""),
                            "effort": rule.get("effort", 0),
                            "labels": rule.get("labels", [])
                        }

        return None


# Global instance
_fetcher = None


def get_rule_fetcher() -> KonveyorRuleFetcher:
    """Get or create the global rule fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = KonveyorRuleFetcher()
    return _fetcher
