import json
import os
from typing import Any, Dict, List, Optional

from loguru import logger


class I18nService:
    def __init__(self, locales_dir: str, default_locale: str = "en"):
        self.default_locale = default_locale
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_locales(locales_dir)

    def _load_locales(self, locales_dir: str) -> None:
        if not os.path.isdir(locales_dir):
            logger.warning(f"Locales directory not found: {locales_dir}")
            return

        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                locale = filename[:-5]
                filepath = os.path.join(locales_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._translations[locale] = json.load(f)
                    logger.info(f"Loaded locale: {locale}")
                except Exception as e:
                    logger.error(f"Failed to load locale {locale}: {e}")

    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale if locale in self._translations else self.default_locale
        translations = self._translations.get(loc, {})

        parts = key.split(".")
        value = translations
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return key

        if value is None:
            return key

        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value) if value else key

    def supported_locales(self) -> List[str]:
        return list(self._translations.keys())
