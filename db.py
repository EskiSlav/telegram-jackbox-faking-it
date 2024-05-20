import sqlite3
import logging
import logging.config
from typing import List

from models import Question, User
from logging_config import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)
class Database():
    def __init__(self, db_path='db.db') -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.curr = self.conn.cursor()
        self.init()
        
    def init(self) -> None:
        """
        Init basic schema
        """
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_bot INTEGER NOT NULL,
            status TEXT
        );
        """        
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER NOT NULL UNIQUE,
            description TEXT,
            title TEXT,
            type TEXT
        );
        """
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS "users_chats" (
            "chat_id"	INTEGER NOT NULL,
            "user_id"	INTEGER NOT NULL,
            FOREIGN KEY("user_id") REFERENCES "users"("id"),
            FOREIGN KEY("chat_id") REFERENCES "chats"("id")
        );"""
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS games (
            "id"	INTEGER,
            "chat_id"	INTEGER NOT NULL,
            "ended"	INTEGER NOT NULL,
            "admin_id"	INTEGER NOT NULL,
            "message_id"	INTEGER NOT NULL,
            PRIMARY KEY("id"),
            FOREIGN KEY("chat_id") REFERENCES "chats"("id") ON DELETE CASCADE ON UPDATE NO ACTION,
            FOREIGN KEY("admin_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE NO ACTION
        )
        """
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS users_in_game (
            game_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users (id) 
                    ON DELETE CASCADE 
                    ON UPDATE NO ACTION,
            FOREIGN KEY (game_id)
                REFERENCES games (id) 
                    ON DELETE CASCADE 
                    ON UPDATE NO ACTION
        );
        """
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS game_traitors (
            "game_id"	INTEGER NOT NULL,
            "traitor_id"	INTEGER NOT NULL,
            FOREIGN KEY("traitor_id") REFERENCES "users"("id"),
            FOREIGN KEY("game_id") REFERENCES "games"("id")
        )
        """
        self.curr.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS "questions" (
            "id" INTEGER PRIMARY KEY,
            "question"	TEXT NOT NULL,
            "game_id"	INTEGER NOT NULL,
            "used"      INTEGER NOT NULL,
            FOREIGN KEY("game_id") REFERENCES "games"("id")
        )"""
        self.curr.execute(sql)
        self.conn.commit()
    
    def create_game(self, chat_id, admin_id, message_id) -> int:
        if self.is_chat_in_game(chat_id):
            return 2
        sql = """
        INSERT INTO games (chat_id, admin_id, message_id, ended) VALUES (?, ?, ?, ?)
        """
        try:
            self.curr.execute(sql, (chat_id, admin_id, message_id, 0))
            self.conn.commit()
            return 0
        except sqlite3.OperationalError as e:
            print(e)
            return 1

    
    def create_user(self, id, username=None, first_name=None, last_name=None, is_bot=None) -> None:
        sql = """
        INSERT INTO users (id, username, first_name, last_name, is_bot) VALUES (?, ?, ?, ?, ?)
        """
        self.curr.execute(sql, (id, username, first_name, last_name, is_bot,))
        self.conn.commit()

    def create_question(self, question, game_id):
        sql = """
        INSERT INTO questions (question, game_id, used) VALUES (?, ?, 0)
        """
        self.curr.execute(sql, (question, game_id,))
        self.conn.commit()

    def create_chat(self, id, title, type, description=None) -> None:
        if self.get_chat(chat_id=id) is None:
            return 0
        sql = """
        INSERT INTO chats (id, description, title, type) VALUES (?, ?, ?, ?)
        """
        try:
            self.curr.execute(sql, (id, description, title, type,))
            self.conn.commit()
            return 0
        except sqlite3.OperationalError as e:
            print(e)
            return 1
    
    def add_user_to_game(self, user_id, chat_id) -> int:
        game = self.get_chat_game(chat_id)
        # print(game, message_id)
        if self.is_user_in_game(user_id, game[0]):
            return 1
        sql = """
        INSERT INTO users_in_game (game_id, user_id) VALUES (?, ?)
        """
        self.curr.execute(sql, (game[0], user_id,))
        self.conn.commit()
        return 0

    def get_chat_game(self, chat_id):
        sql = """
        SELECT id FROM games WHERE chat_id=? and ended=0 LIMIT 1
        """
        self.curr.execute(sql, (chat_id,))
        return self.curr.fetchone()
    
    def get_game_id_by_admin_id(self, admin_id):
        self.curr.execute("SELECT id FROM games WHERE admin_id=? AND ended=0 LIMIT 1", (admin_id,))
        return self.curr.fetchone()[0]
    
    def get_game_by_message_id(self, message_id):
        sql = """
        SELECT id FROM games WHERE message_id=?
        """
        self.curr.execute(sql, (message_id,))
        return self.curr.fetchone()
    
    def get_user(self, user_id):
        sql = """
        SELECT * FROM users WHERE id=?
        """
        self.curr.execute(sql, (user_id,))
        return self.curr.fetchone()
    
    def get_user_status(self, user_id):
        sql = """
        SELECT status FROM users WHERE id=?
        """
        self.curr.execute(sql, (user_id,))
        return self.curr.fetchone()[0]
    
    def update_user_status(self, user_id, status):
        self.curr.execute("UPDATE users SET status=? WHERE id=?", (status, user_id,))
        self.conn.commit

    def get_chat(self, chat_id):
        self.curr.execute("SELECT * FROM chats WHERE id=?", (chat_id,))
        return self.curr.fetchone()
    
    def get_users_in_game(self, game_id):
        sql = """
        SELECT u.id, u.username, u.first_name, u.last_name FROM users_in_game AS ug JOIN users AS u ON u.id=ug.user_id WHERE game_id=?
        """
        self.curr.execute(sql, (game_id,))
        return self.curr.fetchall()
    
    def get_users_in_game_by_chat_id(self, chat_id):
        game_id = self.get_chat_game(chat_id)[0]
        return self.get_users_in_game(game_id)

    def get_game_admin(self, chat_id) -> int:
        sql = """
        SELECT admin_id FROM games WHERE chat_id=? AND ended=0 LIMIT 1
        """
        self.curr.execute(sql, (chat_id,))
        res = int(self.curr.fetchone()[0])
        return res
    
    def get_traitors_by_game_id(self, game_id) -> List[User]:
        self.curr.execute("SELECT traitor_id FROM game_traitors WHERE game_id=?", (game_id,))
        users = [User(user[0]) for user in self.curr.fetchall()]
        return users
    
    def get_random_question(self, game_id) -> Question:
        self.curr.execute("SELECT id, question, used FROM questions WHERE used=0 AND game_id=? LIMIT 1", (game_id,))
        res = self.curr.fetchone()
        question = Question(res[0], res[1], res[2])
        return question
    
    def set_question_as_used(self, question_id):
        self.curr.execute("UPDATE questions SET used=1 WHERE id=?", (question_id,))
        self.conn.commit()
    
    def set_traitor_in_game(self, traitor_id, game_id):
        self.curr.execute("INSERT INTO game_traitors (traitor_id, game_id) VALUES (?, ?)", (traitor_id, game_id,))
        self.conn.commit()
    
    # def set_admin_in_game(self, admin_id, game_id)
    def is_chat_in_game(self, chat_id) -> int:
        sql = """
        SELECT 1 FROM games WHERE chat_id=? AND ended=0
        """
        self.curr.execute(sql, (chat_id,))
        res = self.curr.fetchall()
        if len(res) == 0:
            return 0
        else:
            return 1
    
    def is_user_in_game(self, user_id, game_id) -> int:
        sql = """
        SELECT 1 FROM users_in_game WHERE game_id=? AND user_id=?
        """
        self.curr.execute(sql, (game_id, user_id))
        res = self.curr.fetchall()
        if len(res) == 0:
            return 0
        else:
            return 1
        

    def stop_game(self, chat_id):
        self.curr.execute("UPDATE games SET ended=1 WHERE chat_id=?", (chat_id,))
        self.conn.commit()

    def __del__(self):
        self.curr.close()
        self.conn.close()
