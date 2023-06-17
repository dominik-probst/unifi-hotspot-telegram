# UniFi-Hotspot-Telegram

## Introduction

UniFi-Hotspot-Telegram is a simple and lightweight hotspot portal for UniFi.

It allows guests to request access to the guest WLAN via a web interface. Requests are then forwarded via a Telegram bot to all registered administrators, who can confirm or deny the request with a simple click of a button.

This way, especially in domestic guest networks or small businesses, vouchers and/or passwords can be avoided, while the network owners still have full control over who uses the network and who does not.

![Test](.github/images/demo.gif)

The program is written in Python and utilizes Flask and SQLite. Both Flask and SQLite are not designed for heavy usage. However, since the same applies to the general authentication procedure of this hotspot portal, this should not be a problem.

## Installation

For the sake of simplicity, this documentation distinguishes between the installation of UniFi Hotspot Telegram itself and the necessary steps in UniFi or Telegram that are required for the proper operation of the portal.

### Installation of UniFi-Hotspot-Telegram

Prerequisites: `git` and `python`

1. Clone the repository:

   ```
   git clone https://github.com/dominik-probst/unifi-hotspot-telegram.git
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Configure the program by creating a `settings.json` file in the root folder.

   An example `settings.json` might look like this:

   ```
   {
      "bot_password": "super_secret_pass",
      "telegram_token": "1111111111:AABBCCDDEEFFGGHHIIJJKKLLMMNN_OPQRST",
      "unifi_username": "hotspot-admin",
      "unifi_password": "even_more_secret_pass"
   }
   ```

   Supported settings are:

   |       **Setting**      |                                               **Explanation**                                               |         **Default**        | **Required** |
   |:----------------------:|:-----------------------------------------------------------------------------------------------------------:|:--------------------------:|:------------:|
   |     `bot_password`     |                        Password that can be used to register a new admin with the bot                       |                            |      Yes     |
   |    `telegram_token`    |                          Telegram token of the bot - see "Setup Steps in Telegram"                          |                            |      Yes     |
   |    `unifi_username`    |     Username of an UniFi account with rights to authenticate hotspot users - see "Setup Steps in UniFi"     |                            |      Yes     |
   |    `unifi_password`    |     Password of an UniFi account with rights to authenticate hotspot users - see "Setup Steps in UniFi"     |                            |      Yes     |
   |       `unifi_ip`       |                                          IP of the UniFi Controller                                         |       `"192.168.1.1"`      |      No      |
   |   `unifi_api_version`  |         API version of the UniFi Controller (options: `"v4"`\|`"v5"`\|`"unifiOS"`\|`"UDMP-unifiOS"`)        |      `"UDMP-unifiOS"`      |      No      |
   |   `unifi_ssl_verify`   |       Whether to verify the SSL certificate of the UniFi controller or not (options: `True`\|`False`)       |           `True`           |      No      |
   |        `locale`        |                    (Default) language of the portal and the bot (options: `"de"`\|`"en"`)                   |           `"en"`           |      No      |
   |      `portal_host`     |                                 Hostname the hotspot portal should listen on                                |         `"0.0.0.0"`        |      No      |
   |      `portal_port`     |                                          Port of the hotspot portal                                         |          `"5000"`          |      No      |
   |  `bot_accept_options`  |             A list of options (in minutes) for the user to select from when accepting a request             |  `[60, 1440, 4320, 10080]` |      No      |
   | `portal_go_online_url` | The URL to redirect to when the user clicks the "Go Online" button and there isn't a URL provided by UniFi. | `"https://www.google.com"` |      No      |


4. Run the application:

   ```
   python unifi_hotspot_telegram.py
   ```

### Setup Steps in Telegram

#### Creating a Telegram Bot

1. Message `@BotFather` on telegram:

   ```
   \newbot
   ```

2. Follow the instructions until you receive a token to use in `settings.json`

#### Get Guest Requests on Telegram

Prerequisites: Running UniFi-Hotspot-Telegram application

1. Message your bot on telegram:

   ```
   \register [bot_password]
   ```

2. Wait for incoming requests

### Setup Steps in UniFi

The setup steps in UniFi may vary depending on your product and software version. This is an example guide to give an idea of what to look for.

#### New UniFi User for Hotspot Authentification

Tested on: UniFi OS 2.5.17 (with only Network and Protect installed)

1. Log in to your UniFi OS
2. Create a new `Hotspot` role:

   `Admins` &rarr; `Roles` &rarr; `Add Role`:

   - Role Name: `Hotspot`
   - Privilege &rarr; UniFi OS: `None`
   - Privilege &rarr; Network: `Site Admin`
      - The Role `Hotspot Operator` is unfortunately not enough to get `pyunifi` running although we only use `authorize_guest()` (see: `unifi_hotspot_telegram/telegram_bot.py`)
   - Privilege &rarr; Protect: `None`

3. Create a new user with the `Hotspot` role:

   `Admins` &rarr; `Users` &rarr; `Add User`:

   - Role: `Hotspot`
   - Account Type: `Local Access Only`
   - Preferred Username and Password

#### Add Hotspot Portal to UniFi

Tested on: UniFi Network 7.3.83

1. Get to the `Guest Hotspot` settings:

   `Profiles` &rarr; `Guest Hotspot`

2. Change the `Authentication Type` to `External Portal Server`

3. Enter the IP address where your UniFi-Hotspot-Telegram instance is running as `External Portal`.

4. In the `Advanced` (&rarr; `Manual`) settings set:

   - `HTTPS Redirection` (if you have a SSL certificate for your portal server)
   - `Encrypted redirect URL`
   - `Redirect Using Hostname`:
      - Enter the hostname of your UniFi-Hotspot-Telegram portal server. As no ports are allowed in this field I recommend to use an reverse proxy, however it might work to set your `portal_port` setting to `80` or `443` (not tested)
   - `Secure Portal`

5. Apply your changes

## Disclaimer

UniFi-Hotspot-Telegram is a very basic implementation developed in less then half a day and may not meet the requirements of all environments. It is provided as an open-source project without any warranties. The authors are not responsible for any damages or misuse of this software.

## Acknowledgement

The idea is based on the work of @thomas-br, available at https://github.com/thomas-br/unifi-hotspot-portal. His Node.js-based hotspot portal is very nice work but turned out to be too ressource heavy to run on my Raspberry Pi 3 Model B (1 GB RAM), which is why I decided to take the idea and implement a more lightweight variant on my own.

## License

This project is licensed under the MIT License. See the [LICENSE.md](LICENSE.md) file for more information.
