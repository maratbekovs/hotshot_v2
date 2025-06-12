import mysql.connector
from config import MYSQL_CONFIG


def connect_db():
    """Подключается к базе данных MySQL."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG, charset='utf8mb4', collation='utf8mb4_unicode_ci')
        return conn
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к БД: {err}")
        return None


def create_tables():
    """Создает и обновляет таблицы."""
    conn = connect_db()
    if not conn:
        return

    with conn:
        cursor = conn.cursor()
        # Таблица для фото
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS photos
                       (
                           photo_id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           file_name
                           VARCHAR
                       (
                           255
                       ) NOT NULL,
                           photo_data LONGBLOB NOT NULL,
                           votes INT DEFAULT 0,
                           status ENUM
                       (
                           'pending',
                           'approved',
                           'rejected'
                       ) NOT NULL DEFAULT 'pending'
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")

        # Таблица для просмотров
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS viewed_photos
                       (
                           session_id
                           VARCHAR
                       (
                           40
                       ) NOT NULL,
                           photo_id INT NOT NULL,
                           PRIMARY KEY
                       (
                           session_id,
                           photo_id
                       ),
                           FOREIGN KEY
                       (
                           photo_id
                       ) REFERENCES photos
                       (
                           photo_id
                       ) ON DELETE CASCADE
                           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci""")

        # Безопасное добавление колонки status, если ее нет
        try:
            cursor.execute(
                "ALTER TABLE photos ADD COLUMN status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending'")
        except mysql.connector.Error as err:
            if err.errno == 1060:  # Код ошибки "Duplicate column name"
                pass  # Колонка уже существует, ничего не делаем
            else:
                raise

        conn.commit()


def add_photo(file_name, file_data):
    """Добавляет фото со статусом 'pending'."""
    with connect_db() as conn:
        cursor = conn.cursor()
        # Статус по умолчанию 'pending'
        cursor.execute(
            "INSERT INTO photos (file_name, photo_data, status) VALUES (%s, %s, 'pending')",
            (file_name, file_data))
        conn.commit()


def get_two_random_photos(session_id):
    """Выбирает два случайных ОДОБРЕННЫХ фото, которые пользователь не видел."""
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        query = """
                SELECT p.photo_id, p.file_name \
                FROM photos p
                WHERE p.status = 'approved' \
                  AND p.photo_id NOT IN (SELECT v.photo_id \
                                         FROM viewed_photos v \
                                         WHERE v.session_id = %s)
                ORDER BY RAND() LIMIT 2 \
                """
        cursor.execute(query, (session_id,))
        return cursor.fetchall()


def get_pending_photos():
    """Получает все фото, ожидающие модерации."""
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT photo_id, file_name FROM photos WHERE status = 'pending' ORDER BY photo_id DESC")
        return cursor.fetchall()


def update_photo_status(photo_id, status):
    """Обновляет статус фото ('approved' или 'rejected')."""
    with connect_db() as conn:
        cursor = conn.cursor()
        # Для отклоненных фото можно реализовать удаление или просто смену статуса
        if status == 'rejected':
            cursor.execute("DELETE FROM photos WHERE photo_id = %s", (photo_id,))
        else:
            cursor.execute(
                "UPDATE photos SET status = %s WHERE photo_id = %s",
                (status, photo_id))
        conn.commit()


# Остальные функции (vote_photo, record_view, get_top_photos, get_photo_data) остаются без изменений.

def record_view(session_id, photo_id):
    """Записывает, что пользователь увидел фотографию."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO viewed_photos (session_id, photo_id) VALUES (%s, %s)",
            (session_id, photo_id))
        conn.commit()


def vote_photo(photo_id):
    """Добавляет один голос фотографии по её ID."""
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE photos SET votes = votes + 1 WHERE photo_id = %s",
            (photo_id,))
        conn.commit()


def get_top_photos():
    """Возвращает топ-10 ОДОБРЕННЫХ фото."""
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT photo_id, file_name, votes FROM photos WHERE status = 'approved' ORDER BY votes DESC LIMIT 10")
        return cursor.fetchall()


def get_photo_data(photo_id):
    """Получает бинарные данные фото по его ID."""
    with connect_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT photo_data FROM photos WHERE photo_id = %s", (photo_id,))
        result = cursor.fetchone()
        return result['photo_data'] if result else None