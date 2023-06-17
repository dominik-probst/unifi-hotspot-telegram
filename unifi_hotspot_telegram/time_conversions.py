from unifi_hotspot_telegram.i18n_manager import I18nManager


def convert_minutes_into_human_readable_string(
    minutes: int, i18n_manager: I18nManager
) -> str:
    """Convert minutes into a human-readable string.

    Args:
        minutes (int): The number of minutes to convert.
        i18n_manager (I18nManager): The I18nManager instance for translation of the time units.

    Returns:
        str: The human-readable string representation of the minutes.

    Raises:
        ValueError: If minutes is not greater than 0.
    """
    if minutes > 0:
        # Compute the number of years, months, weeks, days, hours, and minutes
        years = minutes // (60 * 24 * 365)
        months = (minutes % (60 * 24 * 365)) // (60 * 24 * 30)
        weeks = (minutes % (60 * 24 * 30)) // (60 * 24 * 7)
        days = (minutes % (60 * 24 * 7)) // (60 * 24)
        hours = (minutes % (60 * 24)) // 60
        extra_minutes = minutes % 60

        # Build the human-readable string
        human_readable = ""

        if years > 0:
            human_readable += i18n_manager.translate(
                "time_conversions.year", count=years
            )

        if months > 0:
            if human_readable != "":
                human_readable += " "
            human_readable += i18n_manager.translate(
                "time_conversions.month", count=months
            )

        if weeks > 0:
            if human_readable != "":
                human_readable += " "
            human_readable += i18n_manager.translate(
                "time_conversions.week", count=weeks
            )

        if days > 0:
            if human_readable != "":
                human_readable += " "
            human_readable += i18n_manager.translate("time_conversions.day", count=days)

        if hours > 0:
            if human_readable != "":
                human_readable += " "
            human_readable += i18n_manager.translate(
                "time_conversions.hour", count=hours
            )

        if extra_minutes > 0:
            if human_readable != "":
                human_readable += " "
            human_readable += i18n_manager.translate(
                "time_conversions.minute", count=extra_minutes
            )

        return human_readable
    else:
        raise ValueError("Minutes must be greater than 0")
