import mysql.connector
from config import MYSQL_CONFIG
import bcrypt


def connect_db():
    """Подключается к базе данных MySQL."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG, charset='utf8mb4', collation='utf8mb4_unicode_ci')
        return conn
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к БД: {err}")
        return None


def create_tables():
    """Создает и обновляет все таблицы в базе данных."""
    conn = connect_db()
    if not conn:
        print("Не удалось подключиться к БД для создания таблиц.")
        return

    with conn:
        cursor = conn.cursor()

        # --- Таблицы ---
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS users
                       (
                           user_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           username
                           VARCHAR
                       (
                           50
                       ) UNIQUE NOT NULL, password_hash VARCHAR
                       (
                           255
                       ) NOT NULL,
                           first_name VARCHAR
                       (
                           100
                       ), last_name VARCHAR
                       (
                           100
                       ),
                           relationship_status ENUM
                       (
                           'not_specified',
                           'single',
                           'in_relationship'
                       ) DEFAULT 'not_specified',
                           profile_type ENUM
                       (
                           'public',
                           'private'
                       ) DEFAULT 'public',
                           profile_pic_data LONGBLOB, is_admin BOOLEAN DEFAULT FALSE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS photos
                       (
                           photo_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           photo_data
                           LONGBLOB
                           NOT
                           NULL,
                           caption
                           TEXT,
                           votes
                           INT
                           DEFAULT
                           0,
                           contest_status
                           ENUM
                       (
                           'none',
                           'pending',
                           'approved',
                           'rejected'
                       ) NOT NULL DEFAULT 'none',
                           upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS posts
                       (
                           post_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           content
                           TEXT
                           NOT
                           NULL,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           FOREIGN
                           KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS friendships
                       (
                           friendship_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           requester_id
                           INT
                           NOT
                           NULL,
                           addressee_id
                           INT
                           NOT
                           NULL,
                           status
                           ENUM
                       (
                           'pending',
                           'accepted',
                           'declined',
                           'blocked'
                       ) NOT NULL DEFAULT 'pending',
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY
                       (
                           requester_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           addressee_id
                       ) REFERENCES users
                       (
                           user_id
                       )
                         ON DELETE CASCADE,
                           UNIQUE KEY unique_friendship
                       (
                           requester_id,
                           addressee_id
                       )
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS messages
                       (
                           message_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           sender_id
                           INT
                           NOT
                           NULL,
                           receiver_id
                           INT
                           NOT
                           NULL,
                           content
                           TEXT
                           NOT
                           NULL,
                           sent_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           is_read
                           BOOLEAN
                           DEFAULT
                           FALSE,
                           FOREIGN
                           KEY
                       (
                           sender_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           receiver_id
                       ) REFERENCES users
                       (
                           user_id
                       )
                         ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS viewed_photos
                       (
                           user_id
                           INT
                           NOT
                           NULL,
                           photo_id
                           INT
                           NOT
                           NULL,
                           PRIMARY
                           KEY
                       (
                           user_id,
                           photo_id
                       ),
                           FOREIGN KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           photo_id
                       ) REFERENCES photos
                       (
                           photo_id
                       )
                         ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS likes
                       (
                           like_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           post_id
                           INT,
                           photo_id
                           INT,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           FOREIGN
                           KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           post_id
                       ) REFERENCES posts
                       (
                           post_id
                       )
                         ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           photo_id
                       ) REFERENCES photos
                       (
                           photo_id
                       )
                         ON DELETE CASCADE,
                           UNIQUE KEY unique_like
                       (
                           user_id,
                           post_id,
                           photo_id
                       )
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS comments
                       (
                           comment_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           post_id
                           INT,
                           photo_id
                           INT,
                           content
                           TEXT
                           NOT
                           NULL,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           FOREIGN
                           KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           post_id
                       ) REFERENCES posts
                       (
                           post_id
                       )
                         ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           photo_id
                       ) REFERENCES photos
                       (
                           photo_id
                       )
                         ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS notifications
                       (
                           notification_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           initiator_id
                           INT
                           NOT
                           NULL,
                           notification_type
                           ENUM
                       (
                           'friend_request',
                           'friend_accept',
                           'new_comment',
                           'new_like'
                       ) NOT NULL,
                           post_id INT, photo_id INT, is_read BOOLEAN DEFAULT FALSE,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       ) ON DELETE CASCADE,
                           FOREIGN KEY
                       (
                           initiator_id
                       ) REFERENCES users
                       (
                           user_id
                       )
                         ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")

        # --- Безопасное обновление существующих таблиц ---
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_type ENUM('public', 'private') DEFAULT 'public'")
        except mysql.connector.Error:
            pass
        try:
            cursor.execute(
                "ALTER TABLE photos CHANGE COLUMN status contest_status ENUM('none', 'pending', 'approved', 'rejected') NOT NULL DEFAULT 'none'")
        except mysql.connector.Error:
            pass
        try:
            cursor.execute("ALTER TABLE photos ADD COLUMN caption TEXT")
        except mysql.connector.Error:
            pass

        print("Проверка и создание/обновление таблиц завершены.")
        conn.commit()


# --- Функции для пользователей ---
def create_user(username, password, first_name, last_name):
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
                       (username, password_hash, first_name, last_name))
        conn.commit()
        return cursor.lastrowid


def get_user_by_id(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def get_user_by_username(username):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def update_user_profile(user_id, first_name, last_name, relationship_status):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET first_name = %s, last_name = %s, relationship_status = %s WHERE user_id = %s",
                       (first_name, last_name, relationship_status, user_id))
        conn.commit()


def update_user_avatar(user_id, image_data):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_pic_data = %s WHERE user_id = %s", (image_data, user_id))
        conn.commit()


def update_profile_privacy(user_id, profile_type):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_type = %s WHERE user_id = %s", (profile_type, user_id))
        conn.commit()


# --- Функции для постов и галереи ---
def add_gallery_photo(user_id, image_data, caption):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO photos (user_id, photo_data, caption, contest_status) VALUES (%s, %s, %s, 'none')",
                       (user_id, image_data, caption))
        conn.commit()


def create_text_post(user_id, content):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (user_id, content) VALUES (%s, %s)", (user_id, content))
        conn.commit()


def get_user_feed(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        photo_query = "SELECT 'photo' as type, p.photo_id as item_id, p.user_id, u.username, p.caption as content, p.upload_date as created_at, p.contest_status FROM photos p JOIN users u ON p.user_id = u.user_id WHERE p.user_id = %s"
        post_query = "SELECT 'post' as type, po.post_id as item_id, po.user_id, u.username, po.content, po.created_at, NULL as contest_status FROM posts po JOIN users u ON po.user_id = u.user_id WHERE po.user_id = %s"
        full_query = f"({photo_query}) UNION ALL ({post_query}) ORDER BY created_at DESC"
        cursor.execute(full_query, (user_id, user_id))
        return cursor.fetchall()


def delete_post(post_id, user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        conn.commit()


def delete_photo(photo_id, user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM photos WHERE photo_id = %s AND user_id = %s", (photo_id, user_id))
        conn.commit()


def get_photo_data_by_id(photo_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT photo_data FROM photos WHERE photo_id = %s", (photo_id,))
        result = cursor.fetchone()
        return result['photo_data'] if result else None


def get_user_contest_photos(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT photo_id, votes FROM photos WHERE user_id = %s AND contest_status = 'approved' ORDER BY votes DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()


def nominate_photo_for_contest(photo_id, user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT contest_status FROM photos WHERE photo_id = %s AND user_id = %s", (photo_id, user_id))
        result = cursor.fetchone()
        if result and result['contest_status'] in ['none', 'rejected']:
            cursor.execute("UPDATE photos SET contest_status = 'pending' WHERE photo_id = %s", (photo_id,))
            conn.commit()
            return True
        return False


def check_user_contest_submission(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT photo_id FROM photos WHERE user_id = %s AND contest_status IN ('pending', 'approved')",
                       (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def cancel_contest_submission(photo_id, user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE photos SET contest_status = 'none' WHERE photo_id = %s AND user_id = %s AND contest_status = 'pending'",
            (photo_id, user_id))
        conn.commit()


# --- Функции для системы дружбы ---
def search_users(current_user_id, search_query=None):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id, username FROM users WHERE user_id != %s"
        params = [current_user_id]
        if search_query:
            query += " AND username LIKE %s"
            params.append(f"%{search_query}%")
        query += " ORDER BY username"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


def get_friendship_status(user1_id, user2_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM friendships WHERE (requester_id = %s AND addressee_id = %s) OR (requester_id = %s AND addressee_id = %s)",
            (user1_id, user2_id, user2_id, user1_id))
        return cursor.fetchone()


def send_friend_request(requester_id, addressee_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO friendships (requester_id, addressee_id, status) VALUES (%s, %s, 'pending')",
                       (requester_id, addressee_id))
        conn.commit()


def update_friendship_status(requester_id, addressee_id, new_status):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE friendships SET status = %s WHERE requester_id = %s AND addressee_id = %s",
                       (new_status, requester_id, addressee_id))
        conn.commit()


def get_friend_requests(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT u.user_id, u.username FROM friendships f JOIN users u ON f.requester_id = u.user_id WHERE f.addressee_id = %s AND f.status = 'pending'",
            (user_id,))
        return cursor.fetchall()


def get_friends_list(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT u.user_id, u.username, u.first_name, u.last_name FROM users u JOIN friendships f ON (u.user_id = f.addressee_id OR u.user_id = f.requester_id) WHERE f.status = 'accepted' AND (f.requester_id = %s OR f.addressee_id = %s) AND u.user_id != %s"
        cursor.execute(query, (user_id, user_id, user_id))
        return cursor.fetchall()


def get_suggested_friends(user_id, limit=5):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id, username, first_name, last_name FROM users WHERE user_id != %s AND user_id NOT IN (SELECT addressee_id FROM friendships WHERE requester_id = %s UNION SELECT requester_id FROM friendships WHERE addressee_id = %s) ORDER BY RAND() LIMIT %s"
        cursor.execute(query, (user_id, user_id, user_id, limit))
        return cursor.fetchall()


# --- Функции для системы голосования ---
def get_photos_for_voting(current_user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT p.photo_id, p.user_id, u.username FROM photos p JOIN users u ON p.user_id = u.user_id WHERE p.contest_status = 'approved' AND p.user_id != %s AND p.photo_id NOT IN (SELECT photo_id FROM viewed_photos WHERE user_id = %s) ORDER BY RAND() LIMIT 2"
        cursor.execute(query, (current_user_id, current_user_id))
        return cursor.fetchall()


def vote_for_photo(photo_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE photos SET votes = votes + 1 WHERE photo_id = %s", (photo_id,))
        conn.commit()


def record_photo_view(user_id, photo_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT IGNORE INTO viewed_photos (user_id, photo_id) VALUES (%s, %s)", (user_id, photo_id))
        conn.commit()


def get_top_10_photos():
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.photo_id, p.votes, p.user_id, u.username FROM photos p JOIN users u ON p.user_id = u.user_id WHERE p.contest_status = 'approved' ORDER BY votes DESC LIMIT 10")
        return cursor.fetchall()


# --- Функции для чата ---
def get_conversation(user1_id, user2_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) ORDER BY sent_at ASC",
            (user1_id, user2_id, user2_id, user1_id))
        return cursor.fetchall()


def send_message(sender_id, receiver_id, content):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                       (sender_id, receiver_id, content))
        conn.commit()


def mark_messages_as_read(receiver_id, sender_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE messages SET is_read = TRUE WHERE receiver_id = %s AND sender_id = %s AND is_read = FALSE",
            (receiver_id, sender_id))
        conn.commit()


def get_unread_message_count(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages WHERE receiver_id = %s AND is_read = FALSE", (user_id,))
        count = cursor.fetchone()[0]
        return count


def get_new_messages(receiver_id, sender_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM messages WHERE receiver_id = %s AND sender_id = %s AND is_read = FALSE ORDER BY sent_at ASC",
            (receiver_id, sender_id))
        return cursor.fetchall()


# --- Функции для лайков и комментариев ---
# ИСПРАВЛЕННАЯ ФУНКЦИЯ
def add_or_remove_like(user_id, item_type, item_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        was_added = False

        # Определяем, с какой колонкой работать
        id_column = 'post_id' if item_type == 'post' else 'photo_id'

        # Проверяем, есть ли уже лайк
        query = f"SELECT like_id FROM likes WHERE user_id = %s AND {id_column} = %s"
        cursor.execute(query, (user_id, item_id))
        existing_like = cursor.fetchone()

        if existing_like:
            cursor.execute("DELETE FROM likes WHERE like_id = %s", (existing_like[0],))
        else:
            query = f"INSERT INTO likes (user_id, {id_column}) VALUES (%s, %s)"
            cursor.execute(query, (user_id, item_id))
            was_added = True

        conn.commit()
        return was_added


def get_likes_and_comments_for_feed(feed_items, current_user_id):
    if not feed_items: return []
    with connect_db() as conn:
        for item in feed_items:
            cursor = conn.cursor(dictionary=True)
            id_column = 'post_id' if item['type'] == 'post' else 'photo_id'

            # Считаем лайки
            query_likes_count = f"SELECT COUNT(*) as count FROM likes WHERE {id_column} = %s"
            cursor.execute(query_likes_count, (item['item_id'],))
            item['likes_count'] = cursor.fetchone()['count']

            # Проверяем, лайкнул ли текущий пользователь
            query_user_liked = f"SELECT COUNT(*) as count FROM likes WHERE {id_column} = %s AND user_id = %s"
            cursor.execute(query_user_liked, (item['item_id'], current_user_id))
            item['user_has_liked'] = cursor.fetchone()['count'] > 0

            # Получаем комментарии
            query_comments = f"SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.user_id WHERE c.{id_column} = %s ORDER BY c.created_at ASC"
            cursor.execute(query_comments, (item['item_id'],))
            item['comments'] = cursor.fetchall()
    return feed_items


def add_comment(user_id, content, item_type, item_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        id_column = 'post_id' if item_type == 'post' else 'photo_id'

        query = f"INSERT INTO comments (user_id, {id_column}, content) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, item_id, content))
        conn.commit()

        comment_id = cursor.lastrowid
        cursor.execute(
            "SELECT c.*, u.username FROM comments c JOIN users u ON c.user_id = u.user_id WHERE c.comment_id = %s",
            (comment_id,))
        return cursor.fetchone()


# --- Функции для администрирования и уведомлений ---
def get_pending_photos_with_user():
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.photo_id, u.user_id, u.username FROM photos p JOIN users u ON p.user_id = u.user_id WHERE p.contest_status = 'pending' ORDER BY p.upload_date DESC")
        return cursor.fetchall()


def update_photo_status(photo_id, new_status):
    with connect_db() as conn:
        cursor = conn.cursor()
        if new_status == 'rejected':
            cursor.execute("UPDATE photos SET contest_status = 'rejected' WHERE photo_id = %s", (photo_id,))
        else:
            cursor.execute("UPDATE photos SET contest_status = %s WHERE photo_id = %s", (new_status, photo_id))
        conn.commit()


def reset_all_votes():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE photos SET votes = 0")
        cursor.execute("TRUNCATE TABLE viewed_photos")
        conn.commit()


def get_friends_feed(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT 'photo' as type, p.photo_id as item_id, p.caption as content, p.upload_date as created_at, u.user_id, u.username FROM photos p JOIN users u ON p.user_id = u.user_id WHERE p.user_id IN (SELECT addressee_id FROM friendships WHERE requester_id = %s AND status = 'accepted' UNION SELECT requester_id FROM friendships WHERE addressee_id = %s AND status = 'accepted') UNION ALL SELECT 'post' as type, po.post_id as item_id, po.content, po.created_at, u.user_id, u.username FROM posts po JOIN users u ON po.user_id = u.user_id WHERE po.user_id IN (SELECT addressee_id FROM friendships WHERE requester_id = %s AND status = 'accepted' UNION SELECT requester_id FROM friendships WHERE addressee_id = %s AND status = 'accepted') ORDER BY created_at DESC LIMIT 50"
        cursor.execute(query, (user_id, user_id, user_id, user_id))
        return cursor.fetchall()


def create_notification(user_id, initiator_id, notif_type, post_id=None, photo_id=None):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notifications (user_id, initiator_id, notification_type, post_id, photo_id) VALUES (%s, %s, %s, %s, %s)",
            (user_id, initiator_id, notif_type, post_id, photo_id))
        conn.commit()


def get_user_notifications(user_id):
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT n.*, u.username as initiator_username FROM notifications n JOIN users u ON n.initiator_id = u.user_id WHERE n.user_id = %s ORDER BY n.created_at DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()


def mark_notifications_as_read(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE", (user_id,))
        conn.commit()


def get_unread_notification_count(user_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE", (user_id,))
        return cursor.fetchone()[0]


def get_item_author(item_type, item_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        table_name = 'posts' if item_type == 'post' else 'photos'
        id_column = 'post_id' if item_type == 'post' else 'photo_id'
        query = f"SELECT user_id FROM {table_name} WHERE {id_column} = %s"
        cursor.execute(query, (item_id,))
        result = cursor.fetchone()
        return result[0] if result else None
