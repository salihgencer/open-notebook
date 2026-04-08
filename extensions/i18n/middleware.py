from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from extensions.i18n.service import I18nService


class LocaleMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, i18n_service: I18nService):
        super().__init__(app)
        self.i18n = i18n_service

    async def dispatch(self, request: Request, call_next):
        locale = self.i18n.default_locale

        user = getattr(request.state, "user", None)
        if user and "locale" in user:
            locale = user["locale"]
        else:
            accept_lang = request.headers.get("Accept-Language", "")
            if accept_lang:
                primary = accept_lang.split(",")[0].split(";")[0].strip()
                lang_code = primary.split("-")[0].lower()
                if lang_code in self.i18n.supported_locales():
                    locale = lang_code

        request.state.locale = locale
        request.state.i18n = self.i18n
        response = await call_next(request)
        return response
