import sqlite3


class Database:
    def __init__(self, database: str):
        self.db = sqlite3.connect(database)
        self.cur = self.db.cursor()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS parse_channels (
                post_channel_id BIGINT NOT NULL,
                parse_channel_id BIGINT NOT NULL,
                UNIQUE(post_channel_id, parse_channel_id) ON CONFLICT REPLACE
            )
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def add_parse_channel(self, post_channel_id: int, parse_channel_id: int):
        self.cur.execute("INSERT INTO parse_channels VALUES (?, ?)", (post_channel_id, parse_channel_id))
        self.db.commit()

    def remove_parse_channel(self, post_channel_id: int, parse_channel_id: int):
        self.cur.execute("DELETE FROM parse_channels WHERE post_channel_id = ? AND parse_channel_id = ?", (post_channel_id, parse_channel_id))
        self.db.commit()

    def get_post_channel_ids(self, parse_channel_id: int) -> list[tuple[int]]:
        self.cur.execute("SELECT post_channel_id FROM parse_channels WHERE parse_channel_id = ?", (parse_channel_id,))
        return self.cur.fetchall()
