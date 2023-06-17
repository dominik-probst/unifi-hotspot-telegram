import sqlite3

from threading import local


class SQLiteConnector:
    def __init__(self) -> None:
        """Initialize the SQLiteConnector class."""
        self.local_storage = local()
        self.create_tables()

    def __del__(self) -> None:
        """Close the connection when the SQLiteConnector instance is deleted."""
        if hasattr(self.local_storage, "conn"):
            self.local_storage.conn.close()

    def create_tables(self) -> None:
        """Create the necessary tables if they don't exist."""
        conn, cursor = self.get_conn()
        cursor.execute("CREATE TABLE IF NOT EXISTS chats (chat_id TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS requests (id TEXT, name TEXT, mac TEXT, sent INTEGER)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS messages (id TEXT, chat_id TEXT, message_id TEXT)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS confirmations (id TEXT , duration INTEGER, confirmator TEXT)"
        )
        conn.commit()

    def get_conn(self) -> tuple:
        """Get the SQLite connection and cursor objects.

        Returns:
            tuple: A tuple containing the SQLite connection and cursor objects.
                The first element is the connection object (`sqlite3.Connection`).
                The second element is the cursor object (`sqlite3.Cursor`).
        """
        if not hasattr(self.local_storage, "conn"):
            self.local_storage.conn = sqlite3.connect("data.db")
            self.local_storage.cursor = self.local_storage.conn.cursor()
        return self.local_storage.conn, self.local_storage.cursor

    def get_known_chats(self) -> list:
        """Get the list of known chats.

        Returns:
            list: A list of known chats, each represented as a dictionary with 'chat_id' key.
        """
        conn, cursor = self.get_conn()
        cursor.execute("SELECT chat_id FROM chats")
        known_chats = cursor.fetchall()
        known_chats = [{"chat_id": row[0]} for row in known_chats]
        return known_chats

    def get_messages(self, id: str) -> list:
        """Get the messages associated with a specific ID.

        Args:
            id (str): The ID of the messages.

        Returns:
            list: A list of messages, each represented as a dictionary with 'chat_id' and 'message_id' keys.
        """
        conn, cursor = self.get_conn()
        cursor.execute("SELECT chat_id, message_id FROM messages WHERE id = ?", (id,))
        messages = cursor.fetchall()
        messages = [{"chat_id": row[0], "message_id": row[1]} for row in messages]
        return messages

    def get_request(self, id: str) -> dict:
        """Get a specific request by ID.

        Args:
            id (str): The ID of the request.

        Returns:
            dict: A dictionary representing the request with 'name' and 'mac' keys, or None if the request is not found.
        """
        conn, cursor = self.get_conn()
        cursor.execute("SELECT name, mac FROM requests WHERE id = ?", (id,))
        request = cursor.fetchone()
        if request is not None:
            request = {"name": request[0], "mac": request[1]}
        return request

    def get_open_requests(self) -> list:
        """Get the open requests.

        Returns:
            list: A list of open requests, each represented as a dictionary with 'id', 'name', and 'mac' keys.
        """
        conn, cursor = self.get_conn()
        cursor.execute("SELECT id, name, mac FROM requests WHERE sent = 0")
        requests = cursor.fetchall()
        requests = [{"id": row[0], "name": row[1], "mac": row[2]} for row in requests]
        return requests

    def get_confirmation(self, unique_id: str) -> dict:
        """Get the confirmation information for a specific unique ID.

        Args:
            unique_id (str): The unique ID.

        Returns:
            dict: A dictionary representing the confirmation with 'duration' key, or None if the confirmation is not found.
        """
        conn, cursor = self.get_conn()
        cursor.execute("SELECT duration FROM confirmations WHERE id = ?", (unique_id,))
        confirmation = cursor.fetchone()
        if confirmation is not None:
            confirmation = {"duration": confirmation[0]}
        return confirmation

    def add_chat(self, chat_id: str) -> None:
        """Add a chat ID to the database.

        Args:
            chat_id (str): The chat ID to be added.
        """
        conn, cursor = self.get_conn()
        cursor.execute("INSERT INTO chats (chat_id) VALUES (?)", (chat_id,))
        conn.commit()

    def add_request(self, id: str, name: str, mac: str) -> None:
        """Add a request to the database.

        Args:
            id (str): The ID of the request.
            name (str): The name associated with the request.
            mac (str): The MAC address associated with the request.
        """
        # WARNING: The "name" field is a potential security risk, as it can be used to inject SQL code.
        # However, since we use sqlite3, we can use parameterized queries to prevent this. To be perfectly safe,
        # it might be good to perform some additional validation on the name before adding it to the database.
        conn, cursor = self.get_conn()
        cursor.execute(
            "INSERT INTO requests (id, name, mac, sent) VALUES (?, ?, ?, 0)",
            (id, name, mac),
        )
        conn.commit()

    def add_confirmation(self, id: str, duration: int, confirmator: str) -> None:
        """Add a confirmation to the database.

        Args:
            id (str): The ID of the confirmation.
            duration (int): The duration the user is allowed to be connected (in minutes)
            confirmator (str): The telegram user that approved the request.
        """
        conn, cursor = self.get_conn()
        cursor.execute(
            "INSERT INTO confirmations (id, duration, confirmator) VALUES (?, ?, ?)",
            (id, duration, confirmator),
        )
        conn.commit()

    def insert_message(self, id: str, chat_id: str, message_id: str) -> None:
        """Insert a message into the database.

        Args:
            id (str): The ID of the message.
            chat_id (str): The chat ID associated with the message.
            message_id (str): The message ID.
        """
        conn, cursor = self.get_conn()
        cursor.execute(
            "INSERT INTO messages (id, chat_id, message_id) VALUES (?, ?, ?)",
            (id, chat_id, message_id),
        )
        conn.commit()

    def update_request_sent_status(self, id: str) -> None:
        """Update the sent status of a request to "sent"

        Args:
            id (str): The ID of the request.
        """
        conn, cursor = self.get_conn()
        cursor.execute("UPDATE requests SET sent = 1 WHERE id = ?", (id,))
        conn.commit()
