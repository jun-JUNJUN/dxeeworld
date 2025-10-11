"""
User Info API Handler
Get current user information from session
"""

import json
import logging
import tornado.web
from .base_handler import BaseHandler
from ..services.oauth_session_service import OAuthSessionService

logger = logging.getLogger(__name__)


class UserInfoHandler(BaseHandler):
    """Get current user info from session"""

    def initialize(self):
        """Initialize handler dependencies"""
        self.session_service = OAuthSessionService()

    async def get(self):
        """Get current user information"""
        try:
            # Get session ID from cookie
            session_id = self.get_secure_cookie("session_id")

            if not session_id:
                self.set_status(401)
                self.write(json.dumps({"authenticated": False, "error": "No session found"}))
                return

            session_id = session_id.decode("utf-8") if isinstance(session_id, bytes) else session_id

            # Validate session
            session_result = await self.session_service.validate_oauth_session(
                session_id, self.request.remote_ip
            )

            if not session_result.is_success:
                self.set_status(401)
                self.write(
                    json.dumps({"authenticated": False, "error": "Invalid or expired session"})
                )
                return

            # Get session data
            session_data = session_result.data

            # Prepare user data for client
            user_data = {
                "id": session_data.get("identity_id"),
                "email_masked": session_data.get("email_masked"),
                "user_type": session_data.get("user_type"),
                "auth_method": session_data.get("auth_method"),
                "name": session_data.get("email_masked", "").split("@")[0]
                if session_data.get("email_masked")
                else "User",
            }

            logger.info(
                "User info API called - returning data for user: %s",
                user_data.get("id", "unknown")[:8],
            )

            # Return user data
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"authenticated": True, "user": user_data}))

        except Exception as e:
            logger.exception("Failed to get user info: %s", e)
            self.set_status(500)
            self.write(json.dumps({"authenticated": False, "error": "Internal server error"}))
