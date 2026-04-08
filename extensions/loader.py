"""
Extension loader — single integration point with open-notebook core.
Registers all extension routers and middleware on the FastAPI app.
"""

import os
from typing import Optional

from fastapi import FastAPI
from loguru import logger

from extensions.auth.middleware import JWTAuthMiddleware
from extensions.auth.router import create_auth_router
from extensions.auth.service import AuthService
from extensions.i18n.middleware import LocaleMiddleware
from extensions.i18n.service import I18nService
from extensions.outputs.briefing import BriefingGenerator
from extensions.outputs.faq import FAQGenerator
from extensions.outputs.registry import OutputRegistry
from extensions.outputs.router import create_outputs_router
from extensions.outputs.study_guide import StudyGuideGenerator
from extensions.outputs.timeline import TimelineGenerator


def load_extensions(app: FastAPI) -> None:
    """Load all enabled extensions onto the FastAPI app."""
    enabled = os.getenv("EXTENSIONS_ENABLED", "").split(",")
    enabled = [e.strip() for e in enabled if e.strip()]

    if not enabled:
        logger.info("No extensions enabled (EXTENSIONS_ENABLED is empty)")
        return

    logger.info(f"Loading extensions: {enabled}")

    auth_service: Optional[AuthService] = None

    # Auth extension
    if "auth" in enabled:
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            logger.error("JWT_SECRET not set — auth extension disabled")
        else:
            auth_service = AuthService(jwt_secret=jwt_secret)
            auth_router = create_auth_router(auth_service)
            app.include_router(auth_router, prefix="/api/ext/auth", tags=["ext-auth"])

            app.add_middleware(
                JWTAuthMiddleware,
                auth_service=auth_service,
                excluded_paths=[
                    "/",
                    "/health",
                    "/docs",
                    "/openapi.json",
                    "/redoc",
                    "/api/ext/auth/login",
                    "/api/ext/auth/register",
                    "/api/auth/status",
                    "/api/config",
                ],
            )
            logger.success("Auth extension loaded")

    # i18n extension
    if "i18n" in enabled:
        locales_dir = os.path.join(
            os.path.dirname(__file__), "i18n", "locales"
        )
        default_locale = os.getenv("DEFAULT_LOCALE", "en")
        i18n_service = I18nService(locales_dir=locales_dir, default_locale=default_locale)
        app.add_middleware(LocaleMiddleware, i18n_service=i18n_service)
        logger.success(f"i18n extension loaded (default: {default_locale}, locales: {i18n_service.supported_locales()})")

    # Outputs extension
    if "outputs" in enabled:
        registry = OutputRegistry()
        registry.register(StudyGuideGenerator)
        registry.register(FAQGenerator)
        registry.register(TimelineGenerator)
        registry.register(BriefingGenerator)
        outputs_router = create_outputs_router(registry)
        app.include_router(outputs_router, prefix="/api/ext/outputs", tags=["ext-outputs"])
        logger.success(f"Outputs extension loaded ({registry.list_types()})")
