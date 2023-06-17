import json

from multiprocessing import Process

from unifi_hotspot_telegram.guest_portal import GuestPortal
from unifi_hotspot_telegram.telegram_bot import TelegramBot


def load_config() -> dict:
    """Load the configuration from the settings.json file.

    Returns:
        dict: The configuration values from the settings.json file. At least the following keys are present: bot_password, telegram_token, unifi_username, unifi_password
    """
    # Try to load the configuration from the settings.json file
    try:
        with open("settings.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            "Could not find the configuration file. Please make sure that the file settings.json is present in the same directory as main.py."
        )

    # Check if all required values are present in the configuration
    required_keys = [
        "bot_password",
        "telegram_token",
        "unifi_username",
        "unifi_password",
    ]
    if not all(key in config for key in required_keys):
        raise ValueError(
            f"Not all required keys are present in the configuration file. Required keys are: {required_keys}"
        )

    # Return the configuration
    return config


def run_guest_portal(config: dict):
    """Start the guest portal.

    Args:
        config (dict): The configuration values from the settings.json file.
    """
    guest_portal = GuestPortal(
        portal_host=config.get("portal_host", "0.0.0.0"),
        portal_port=config.get("portal_port", "5000"),
        portal_go_online_url=config.get(
            "portal_go_online_url", "https://www.google.com"
        ),
        locale=config.get("locale", "en"),
    )
    guest_portal.run()


def run_telegram_bot(config: dict):
    """Start the telegram bot.

    Args:
        config (dict): The configuration values from the settings.json file.
    """
    bot_handler = TelegramBot(
        config["bot_password"],
        config["telegram_token"],
        config["unifi_username"],
        config["unifi_password"],
        unifi_ip=config.get("unifi_ip", "192.168.1.1"),
        unifi_api_version=config.get("unifi_api_version", "UDMP-unifiOS"),
        unifi_ssl_verify=config.get("unifi_ssl_verify", True),
        locale=config.get("locale", "en"),
        bot_accept_options=config.get("bot_accept_options", [60, 1440, 4320, 10080]),
    )
    bot_handler.run()


if __name__ == "__main__":
    # Load the configuration from settings.json
    config = load_config()

    # Create and start the guest portal process
    guest_portal_process = Process(target=run_guest_portal, args=(config,))
    guest_portal_process.start()

    # Create and start the telegram bot process
    telegram_bot_process = Process(target=run_telegram_bot, args=(config,))
    telegram_bot_process.start()

    # Wait for the guest portal process to finish
    guest_portal_process.join()

    # Wait for the telegram bot process to finish
    telegram_bot_process.join()
