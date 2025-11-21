"""
UI Authentication Service
Task 8.1-8.3: UI Presentation Function and User Interface
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from .oauth_session_service import OAuthSessionService
from ..middleware.access_control_middleware import AccessControlMiddleware
from ..utils.result import Result

logger = logging.getLogger(__name__)


class UIAuthError(Exception):
    """UI authentication service error"""

    pass


class UIAuthService:
    """UI authentication service for login panel and user interface management"""

    def __init__(self, db_service=None):
        """Initialize UI auth service with dependencies"""
        self.session_service = OAuthSessionService()
        self.access_control = AccessControlMiddleware(db_service)

        # UI configuration
        self.auth_base_url = os.getenv("AUTH_BASE_URL", "/auth")
        self.login_panel_position = os.getenv("LOGIN_PANEL_POSITION", "bottom-right")

    async def get_login_panel_state(
        self, request_path: str, session_id: Optional[str], ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Get login panel visibility state for current request"""
        try:
            # Check if access control is required for this path
            access_result = await self.access_control.check_access(
                request_path, session_id, ip_address
            )

            if access_result.is_success:
                access_data = access_result.data

                if not access_data["authentication_required"]:
                    # Public content - no login panel needed
                    return Result.success(
                        {"show_panel": False, "reason": "public_content", "user_context": None}
                    )

                if access_data["access_granted"]:
                    # Authenticated and authorized - hide panel
                    return Result.success(
                        {
                            "show_panel": False,
                            "reason": "authenticated",
                            "user_context": access_data.get("user_context"),
                        }
                    )

            # Authentication required - show login panel
            auth_methods = await self._get_auth_methods_config()

            return Result.success(
                {
                    "show_panel": True,
                    "reason": "authentication_required",
                    "auth_methods": auth_methods,
                    "redirect_after_auth": request_path,
                    "panel_position": self.login_panel_position,
                }
            )

        except Exception as e:
            logger.exception("Failed to get login panel state: %s", e)
            return Result.failure(UIAuthError(f"Login panel state error: {e}"))

    async def get_user_menu_info(
        self, session_id: Optional[str]
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Get user menu information for display"""
        try:
            if not session_id:
                # Unauthenticated user
                return Result.success(
                    {
                        "authenticated": False,
                        "user_type": None,
                        "login_methods": await self._get_auth_methods_config(),
                    }
                )

            # Validate session
            session_result = await self.session_service.validate_oauth_session(session_id)

            if not session_result.is_success:
                # Invalid session
                return Result.success(
                    {
                        "authenticated": False,
                        "user_type": None,
                        "login_methods": await self._get_auth_methods_config(),
                    }
                )

            session_data = session_result.data
            user_type = session_data.get("user_type", "user")

            # Get permission display info
            permission_info = await self._get_permission_display_info(user_type)

            return Result.success(
                {
                    "authenticated": True,
                    "user_type": user_type,
                    "auth_method": session_data.get("auth_method"),
                    "email_masked": session_data.get("email_masked"),
                    "permissions": permission_info["permissions"],
                    "display_name": permission_info["display_name"],
                    "color_class": permission_info["color_class"],
                    "icon": permission_info["icon"],
                    "logout_url": f"{self.auth_base_url}/logout",
                    "session_info": {
                        "created_at": session_data.get("created_at"),
                        "last_accessed": session_data.get("last_accessed"),
                    },
                }
            )

        except Exception as e:
            logger.exception("Failed to get user menu info: %s", e)
            return Result.failure(UIAuthError(f"User menu service error: {e}"))

    async def check_review_access(
        self, review_url: str, session_id: Optional[str], ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Check review access and return UI state"""
        try:
            access_result = await self.access_control.check_access(
                review_url, session_id, ip_address
            )

            if access_result.is_success:
                # Access granted
                return Result.success(
                    {
                        "access_granted": True,
                        "show_login_panel": False,
                        "user_context": access_result.data.get("user_context"),
                        "review_url": review_url,
                    }
                )

            # Access denied - show login panel
            return Result.success(
                {
                    "access_granted": False,
                    "show_login_panel": True,
                    "redirect_after_auth": review_url,
                    "auth_methods": await self._get_auth_methods_config(),
                    "reason": "authentication_required",
                }
            )

        except Exception as e:
            logger.exception("Failed to check review access: %s", e)
            return Result.failure(UIAuthError(f"Review access check error: {e}"))

    async def check_review_submission_access(
        self, session_id: Optional[str], ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Check review submission access and permissions"""
        try:
            review_submit_url = "/reviews/submit"
            access_result = await self.access_control.check_access(
                review_submit_url, session_id, ip_address
            )

            if access_result.is_success and access_result.data["access_granted"]:
                # Submission allowed
                return Result.success(
                    {
                        "submission_allowed": True,
                        "show_login_panel": False,
                        "user_context": access_result.data.get("user_context"),
                    }
                )

            # Determine why submission is not allowed
            if not session_id:
                reason = "authentication_required"
            else:
                # Check if it's authentication or permission issue
                session_result = await self.session_service.validate_oauth_session(
                    session_id, ip_address
                )
                if not session_result.is_success:
                    reason = "authentication_required"
                else:
                    reason = "insufficient_permissions"

            return Result.success(
                {
                    "submission_allowed": False,
                    "reason": reason,
                    "show_login_panel": True,
                    "auth_methods": await self._get_auth_methods_config(),
                    "required_permissions": ["user", "admin"],  # From access control rules
                }
            )

        except Exception as e:
            logger.exception("Failed to check review submission access: %s", e)
            return Result.failure(UIAuthError(f"Review submission check error: {e}"))

    async def get_available_auth_methods(self) -> Result[Dict[str, Any], UIAuthError]:
        """Get available authentication methods configuration"""
        try:
            methods = await self._get_auth_methods_config()

            return Result.success(
                {
                    "methods": {
                        "google": {
                            "enabled": methods.get("google", True),
                            "auth_url": f"{self.auth_base_url}/google",
                            "display_name": "Google",
                            "icon": "google-icon",
                        },
                        "facebook": {
                            "enabled": methods.get("facebook", True),
                            "auth_url": f"{self.auth_base_url}/facebook",
                            "display_name": "Facebook",
                            "icon": "facebook-icon",
                        },
                        "email": {
                            "enabled": methods.get("email", True),
                            "signup_url": f"{self.auth_base_url}/email/signup",
                            "login_url": f"{self.auth_base_url}/email/login",
                            "display_name": "Email",
                            "icon": "email-icon",
                        },
                    },
                    "default_method": "google",
                }
            )

        except Exception as e:
            logger.exception("Failed to get auth methods: %s", e)
            return Result.failure(UIAuthError(f"Auth methods error: {e}"))

    async def handle_post_auth_redirect(
        self, original_url: str, session_id: str, ip_address: Optional[str] = None
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Handle post-authentication redirect"""
        try:
            # Validate new session
            session_result = await self.session_service.validate_oauth_session(
                session_id, ip_address
            )

            if not session_result.is_success:
                return Result.failure(UIAuthError("Session validation failed after authentication"))

            # Check if user can access original URL
            access_result = await self.access_control.check_access(
                original_url, session_id, ip_address
            )

            redirect_url = original_url
            if not access_result.is_success or not access_result.data.get("access_granted"):
                # Redirect to safe default if still no access
                redirect_url = "/"

            return Result.success(
                {
                    "redirect_url": redirect_url,
                    "session_validated": True,
                    "show_success_message": True,
                    "user_context": session_result.data,
                }
            )

        except Exception as e:
            logger.exception("Failed to handle post-auth redirect: %s", e)
            return Result.failure(UIAuthError(f"Post-auth redirect error: {e}"))

    async def handle_logout(
        self, session_id: str, current_url: str
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Handle user logout"""
        try:
            # Logout session
            logout_result = await self.session_service.logout_session(session_id)

            if not logout_result.is_success:
                logger.warning(f"Logout failed for session {session_id[:8]}...")

            # Always return successful logout from UI perspective
            return Result.success(
                {
                    "logout_successful": True,
                    "redirect_url": current_url,
                    "clear_session": True,
                    "show_logout_message": True,
                }
            )

        except Exception as e:
            logger.exception("Failed to handle logout: %s", e)
            return Result.failure(UIAuthError(f"Logout error: {e}"))

    async def get_permission_display_info(
        self, user_type: str
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Get permission display information for UI"""
        try:
            return Result.success(await self._get_permission_display_info(user_type))

        except Exception as e:
            logger.exception("Failed to get permission display info: %s", e)
            return Result.failure(UIAuthError(f"Permission display error: {e}"))

    async def validate_session_for_ui(
        self, session_id: str, request_context: Dict[str, Any]
    ) -> Result[Dict[str, Any], UIAuthError]:
        """Validate session for UI context with security checks"""
        try:
            ip_address = request_context.get("ip_address")
            session_result = await self.session_service.validate_oauth_session(
                session_id, ip_address
            )

            if not session_result.is_success:
                return Result.success(
                    {"session_valid": False, "security_validated": False, "user_context": None}
                )

            return Result.success(
                {
                    "session_valid": True,
                    "security_validated": True,
                    "user_context": session_result.data,
                    "request_context": {
                        "path": request_context.get("path"),
                        "method": request_context.get("method"),
                        "user_agent": request_context.get("user_agent", "")[:50],  # Truncated
                    },
                }
            )

        except Exception as e:
            logger.exception("Failed to validate session for UI: %s", e)
            return Result.failure(UIAuthError(f"Session validation error: {e}"))

    async def _get_auth_methods_config(self) -> Dict[str, Any]:
        """Get authentication methods configuration"""
        return {
            "google": os.getenv("GOOGLE_AUTH_ENABLED", "true").lower() == "true",
            "facebook": os.getenv("FACEBOOK_AUTH_ENABLED", "true").lower() == "true",
            "email": os.getenv("EMAIL_AUTH_ENABLED", "true").lower() == "true",
        }

    async def _get_permission_display_info(self, user_type: str) -> Dict[str, Any]:
        """Get permission display information"""
        permission_map = {
            "admin": {
                "display_name": "管理者",
                "permissions": ["レビュー閲覧", "レビュー投稿", "管理機能", "すべてのアクセス"],
                "color_class": "text-red-600",
                "icon": "admin-crown",
            },
            "user": {
                "display_name": "ユーザー",
                "permissions": ["レビュー閲覧", "レビュー投稿"],
                "color_class": "text-blue-600",
                "icon": "user-circle",
            },
            "ally": {
                "display_name": "アライ",
                "permissions": ["レビュー閲覧", "レビュー投稿"],
                "color_class": "text-green-600",
                "icon": "user-star",
            },
            "guest": {
                "display_name": "ゲスト",
                "permissions": ["制限付きアクセス"],
                "color_class": "text-gray-600",
                "icon": "user-question",
            },
        }

        return permission_map.get(user_type, permission_map["guest"])
