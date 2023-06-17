import uuid
import os
import markdown
import warnings

from flask import Flask, request, render_template, jsonify

from unifi_hotspot_telegram.sqlite_connector import SQLiteConnector
from unifi_hotspot_telegram.i18n_manager import I18nManager
from unifi_hotspot_telegram.time_conversions import (
    convert_minutes_into_human_readable_string,
)


class GuestPortal:
    def __init__(
        self,
        portal_host: str = "0.0.0.0",
        portal_port: int = 5000,
        portal_go_online_url: str = "https://www.google.com",
        locale: str = "en",
    ) -> None:
        """Initialize the GuestPortal class.

        Args:
            portal_host (str, optional): The host to bind the Flask application to. Defaults to '0.0.0.0'.
            portal_port (int, optional): The port to bind the Flask application to. Defaults to 5000.
            portal_go_online_url (str, optional): The URL to redirect to when the user clicks the "Go Online" button and there isn't a URL provided by UniFi. Defaults to 'https://www.google.com'.
            locale (str, optional): The locale to use then loading the portal without a specific language setting. Defaults to 'en'. Options are [de|en]
        """
        self.locale = locale
        self.portal_host = portal_host
        self.portal_port = portal_port
        self.portal_go_online_url = portal_go_online_url
        self.app = Flask(__name__)
        self.setup_routes()
        self.db_connector = SQLiteConnector()

    def __del__(self) -> None:
        """Clean up resources when the GuestPortal instance is deleted."""
        del self.db_connector

    def setup_routes(self) -> None:
        """Setup the routes for the Flask application."""
        self.app.add_url_rule(
            "/guest/s/<unifi_site_id>/", "home", self.home, methods=["GET", "POST"]
        )
        self.app.add_url_rule(
            "/guest/s/<unifi_site_id>/check_update/<unique_id>",
            "check_update",
            self.check_update,
            methods=["GET"],
        )

    def get_supported_locales(self) -> list:
        """Get a list of supported languages.

        Returns:
            list: A list of supported languages.
        """
        languages = []
        flags_folder = "unifi_hotspot_telegram/static/flags/"
        terms_folder = "unifi_hotspot_telegram/terms/"
        translations_folder = "unifi_hotspot_telegram/translations/"

        # Get a list of all available flags
        for filename in os.listdir(flags_folder):
            if filename.endswith(".png"):
                language_code = os.path.splitext(filename)[0]

                # Check if there are translations for the language
                # First check if there are translations for the guest portal
                guest_portal_translations = os.path.join(
                    translations_folder, "guest_portal.{}.json".format(language_code)
                )
                if not os.path.isfile(guest_portal_translations):
                    # Skip this language if there are no translations for the guest portal
                    continue

                # Second check if there are translations for the telegram bot
                telegram_bot_translations = os.path.join(
                    translations_folder, "telegram_bot.{}.json".format(language_code)
                )
                if not os.path.isfile(telegram_bot_translations):
                    # Skip this language if there are no translations for the telegram bot
                    continue

                # Third check if there are translations for the time conversions
                time_conversions_translations = os.path.join(
                    translations_folder,
                    "time_conversions.{}.json".format(language_code),
                )
                if not os.path.isfile(time_conversions_translations):
                    # Skip this language if there are no translations for the time conversions
                    continue

                # Also check if there are terms of use for the language
                terms_of_use_file = os.path.join(
                    terms_folder, "terms_of_use.{}.md".format(language_code)
                )
                if not os.path.isfile(terms_of_use_file):
                    # Skip this language if there are no terms of use for the guest portal
                    continue

                languages.append(language_code)

        return languages

    def get_terms(self, locale: str = "en") -> str:
        """Get the terms of use content.

        Args:
            locale (str, optional): The locale to load the terms of use for. Defaults to 'en'. Options are [de|en]

        Returns:
            str: The HTML representation of the terms of use content.
        """
        # Check if the locale is supported
        if locale not in self.get_supported_locales():
            warnings.warn(f"The locale {locale} is not supported.")
            # Use english as fallback as it is done in the I18nManager
            locale = "en"

        # Check if there is a terms of use file for the default language
        file_path = f"unifi_hotspot_telegram/terms/terms_of_use.{locale}.md"

        # Read the file if it exists
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Try to convert the markdown file into HTML
            try:
                html = markdown.markdown(content)
                return html
            except:
                warnings.warn(
                    f"Could not read the terms of use file for the language {locale}."
                )
        else:
            warnings.warn(
                f"Could not find the terms of use file for the language {locale}."
            )

        # Return an empty string if there are no terms of use to display
        return ""

    def home(self, unifi_site_id: str) -> str:
        """Handle the home route.

        Args:
            unifi_site_id (str): The ID of the Unifi site.

        Returns:
            str: The rendered template for the home page.
        """
        # Check if there is a language setting in the URL
        if request.args.get("lang"):
            locale = request.args.get("lang")
        else:
            locale = self.locale
        # Initialize the i18n manager
        i18n_manager = I18nManager(default_locale=locale)

        # If there is a POST request, the form is already submitted so we can show the wait page
        if request.method == "POST":
            name = request.form.get("name")
            mac = request.args.get("id")

            # Check if there is a URL to redirect to after the user is online
            if request.args.get("url"):
                url = request.args.get("url")
            else:
                # Otherwise use the default URL
                url = self.portal_go_online_url

            unique_id = uuid.uuid4().hex

            self.db_connector.add_request(unique_id, name, mac)

            return render_template(
                "wait.html",
                unifi_site_id=unifi_site_id,
                unique_id=unique_id,
                locale=locale,
                url=url,
                i18n_manager=i18n_manager,
            )

        # Otherwise show the form and "forward" the MAC address for later use in the UniFi verification
        mac = request.args.get("id")
        url = request.args.get("url")

        return render_template(
            "form.html",
            unifi_site_id=unifi_site_id,
            id=mac,
            locale=locale,
            url=url,
            supported_locales=self.get_supported_locales(),
            terms_of_use=self.get_terms(locale),
            i18n_manager=i18n_manager,
        )

    def check_update(self, unifi_site_id: str, unique_id: str) -> dict:
        """Check for updates.

        Args:
            unifi_site_id (str): The ID of the Unifi site.
            unique_id (str): The unique ID.

        Returns:
            dict: A JSON response containing the duration and human-readable duration if available.
        """
        # Check if there is a result for the unique ID
        result = self.db_connector.get_confirmation(unique_id)

        if result:
            # Check if the duration is above 0
            if result["duration"] > 0:
                # Only if there is a result and the duration is above 0 check if there is a language setting in the URL
                if request.args.get("lang"):
                    locale = request.args.get("lang")
                else:
                    locale = self.locale

                # Initialize the i18n manager
                i18n_manager = I18nManager(default_locale=locale)

                return jsonify(
                    {
                        "duration": result["duration"],
                        "duration_human_readable": convert_minutes_into_human_readable_string(
                            result["duration"], i18n_manager
                        ),
                    }
                )
            else:
                return jsonify({"duration": result["duration"]})
        else:
            return jsonify({})

    def run(self):
        """Run the Flask application."""
        # Normally Flask should not be used in production mode, but in this case we don't expect a lot of traffic so it should be fine
        self.app.run(host=self.portal_host, port=self.portal_port, debug=False)
