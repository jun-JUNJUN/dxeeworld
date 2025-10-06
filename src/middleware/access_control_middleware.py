"""
Access Control Middleware
Task 7.1-7.3: アクセス制御ミドルウェアの実装
"""

import logging
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from ..services.oauth_session_service import OAuthSessionService
from ..utils.result import Result

logger = logging.getLogger(__name__)


class AccessControlError(Exception):
    """Access control middleware error"""

    pass


class AccessControlMiddleware:
    """Access control middleware for URL pattern matching and permission checking"""

    def __init__(self):
        """Initialize access control middleware"""
        self.access_rules: List[Dict[str, Any]] = []
        self.session_service = OAuthSessionService()
        self.last_config_load = None
        self.reload_interval = int(os.getenv("ACCESS_CONTROL_RELOAD_INTERVAL", "30"))
        # Note: load_access_control_rules() is async, so it will be called on first check_access()

    async def load_access_control_rules(self):
        """Load access control rules from environment configuration"""
        try:
            rules_env = os.getenv("ACCESS_CONTROL_RULES", "")

            if not rules_env.strip():
                logger.info("No access control rules configured")
                self.access_rules = []
                return

            # Parse rules from environment: "pattern,perm1,perm2;pattern2,perm1"
            rules = []
            rule_entries = rules_env.split(";")

            for entry in rule_entries:
                entry = entry.strip()
                if not entry:
                    continue

                parts = entry.split(",")
                if len(parts) < 2:
                    raise AccessControlError(f"Malformed configuration: {entry}")

                pattern = parts[0].strip()
                permissions = [perm.strip() for perm in parts[1:] if perm.strip()]

                if not pattern or not permissions:
                    raise AccessControlError(f"Malformed configuration: {entry}")

                rules.append({"pattern": pattern, "permissions": permissions})

            self.access_rules = rules
            self.last_config_load = datetime.now(timezone.utc)

            logger.info(f"Loaded {len(rules)} access control rules")
            for rule in rules:
                logger.debug(f"Rule: {rule['pattern']} -> {rule['permissions']}")

        except Exception as e:
            if isinstance(e, AccessControlError):
                raise
            logger.exception("Failed to load access control rules: %s", e)
            raise AccessControlError(f"Configuration load failed: {e}")

    async def reload_configuration(self):
        """Reload configuration from environment"""
        logger.info("Reloading access control configuration")
        await self.load_access_control_rules()

    def match_url_pattern(self, url: str) -> Optional[Dict[str, Any]]:
        """Match URL against configured patterns, return first match"""
        logger.info(f"D-00007: Matching URL '{url}' against {len(self.access_rules)} rules")

        for rule in self.access_rules:
            pattern = rule["pattern"]

            # Check if URL contains the pattern (for path matching)
            # Also support patterns like /reviews/new matching /companies/{id}/reviews/new
            if url.startswith(pattern) or pattern in url:
                logger.info(f"D-00007: URL '{url}' matched pattern '{pattern}'")
                return rule

            # Also check if the URL ends with the pattern (for dynamic routes)
            if url.endswith(pattern):
                logger.info(f"D-00007: URL '{url}' matched pattern '{pattern}' (suffix match)")
                return rule

        logger.info(f"D-00007: No matching rule found for URL '{url}', rules: {self.access_rules}")
        return None

    def _mask_sensitive_data(self, data: str, mask_length: int = 8) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= mask_length:
            return "***"
        return data[: mask_length // 2] + "***" + data[-mask_length // 2 :]

    async def check_access(
        self, url: str, session_id: Optional[str], ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], AccessControlError]:
        """Check access permissions for URL and session"""
        try:
            # Load rules if not loaded yet
            if self.last_config_load is None:
                await self.load_access_control_rules()

            # Find matching rule
            matched_rule = self.match_url_pattern(url)

            if not matched_rule:
                # No rule matches, allow access
                return Result.success(
                    {
                        "access_granted": True,
                        "authentication_required": False,
                        "matched_rule": None,
                        "user_context": None,
                    }
                )

            # Rule found, authentication required
            if not session_id:
                return Result.failure(AccessControlError("Authentication required"))

            # Validate session
            session_validation = await self.session_service.validate_oauth_session(
                session_id, ip_address
            )

            if not session_validation.is_success:
                return Result.failure(AccessControlError("Authentication required"))

            session_data = session_validation.data
            user_type = session_data.get("user_type", "")
            required_permissions = matched_rule["permissions"]

            # Check if user has required permission
            if user_type not in required_permissions:
                masked_identity = self._mask_sensitive_data(session_data.get("identity_id", ""))
                logger.warning(
                    f"Access denied: user {masked_identity} with type '{user_type}' "
                    f"attempted access to {url} (requires: {required_permissions})"
                )
                return Result.failure(AccessControlError("Insufficient permissions"))

            # Access granted
            masked_session = self._mask_sensitive_data(session_id)
            logger.info(f"Access granted to {url} for session {masked_session}")

            return Result.success(
                {
                    "access_granted": True,
                    "authentication_required": True,
                    "matched_rule": matched_rule,
                    "user_context": {
                        "user_type": user_type,
                        "auth_method": session_data.get("auth_method"),
                        "identity_id": session_data.get("identity_id"),
                    },
                }
            )

        except Exception as e:
            logger.exception("Access control check failed: %s", e)
            if isinstance(e, AccessControlError):
                return Result.failure(e)
            return Result.failure(AccessControlError(f"Access control error: {e}"))

    async def process_request(
        self, request_context: Dict[str, Any], session_id: Optional[str]
    ) -> Result[Dict[str, Any], AccessControlError]:
        """Process request with full context for middleware integration"""
        try:
            url = request_context.get("path", "")
            ip_address = request_context.get("remote_addr")
            user_agent = request_context.get("headers", {}).get("User-Agent", "")

            # Check if configuration needs reloading
            if (
                self.last_config_load is None
                or (datetime.now(timezone.utc) - self.last_config_load).seconds
                > self.reload_interval
            ):
                await self.reload_configuration()

            # Perform access control check
            access_result = await self.check_access(url, session_id, ip_address)

            if not access_result.is_success:
                return access_result

            # Add request context to result
            result_data = access_result.data.copy()
            result_data.update(
                {
                    "request_method": request_context.get("method"),
                    "request_path": url,
                    "client_ip": ip_address,
                    "user_agent": user_agent[:50] if user_agent else None,  # Truncated for security
                }
            )

            return Result.success(result_data)

        except Exception as e:
            logger.exception("Request processing failed: %s", e)
            return Result.failure(AccessControlError(f"Request processing error: {e}"))

    async def get_access_rules(self) -> List[Dict[str, Any]]:
        """Get current access control rules (for debugging/monitoring)"""
        return self.access_rules.copy()

    async def validate_configuration(self, rules_config: str) -> Result[bool, AccessControlError]:
        """Validate access control configuration format"""
        try:
            if not rules_config.strip():
                return Result.success(True)  # Empty config is valid

            rule_entries = rules_config.split(";")

            for entry in rule_entries:
                entry = entry.strip()
                if not entry:
                    continue

                parts = entry.split(",")
                if len(parts) < 2:
                    return Result.failure(AccessControlError(f"Invalid rule format: {entry}"))

                pattern = parts[0].strip()
                permissions = [perm.strip() for perm in parts[1:] if perm.strip()]

                if not pattern or not permissions:
                    return Result.failure(
                        AccessControlError(f"Empty pattern or permissions: {entry}")
                    )

            return Result.success(True)

        except Exception as e:
            return Result.failure(AccessControlError(f"Configuration validation failed: {e}"))
