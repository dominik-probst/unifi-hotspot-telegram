import i18n


class I18nManager:
    def __init__(
        self,
        default_locale: str = "en",
        fallback_locale: str = "en",
        supported_locales: list = ["en", "de"],
        translation_path: str = "unifi_hotspot_telegram/translations",
    ) -> None:
        """Initialize the I18nManager class.

        Args:
            default_locale (str): The default locale. Defaults to 'en'.
            fallback_locale (str): The fallback locale. Defaults to 'en'.
            supported_locales (list): A list of supported locales. Defaults to ['en', 'de'].
            translation_path (str): The path to the translation files. Defaults to 'unifi_hotspot_telegram/translations'.
        """
        self.default_locale = default_locale  # str: The default locale
        self.fallback_locale = fallback_locale  # str: The fallback locale
        self.supported_locales = supported_locales  # list: A list of supported locales
        self.translation_path = (
            translation_path  # str: The path to the translation files
        )

        self.setup_i18n()  # Setup i18n

    def setup_i18n(self) -> None:
        """Setup i18n with the configured settings."""
        i18n.set("locale", self.default_locale)
        i18n.set("fallback", self.fallback_locale)
        i18n.set("supported_locales", self.supported_locales)
        i18n.set("file_format", "json")

        if self.translation_path:
            i18n.load_path.append(self.translation_path)

    def translate(self, message: str, **kwargs) -> str:
        """Translate a message using the configured locale.

        Args:
            message (str): The message to be translated.
            **kwargs: Additional keyword arguments for message interpolation.

        Returns:
            str: The translated message.
        """
        return i18n.t(message, **kwargs)
