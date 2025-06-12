import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Данные для входа админа
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'superpassword123'


# Замените значения на ваши данные с webhost.kg
MYSQL_CONFIG = {
    'host': '77.235.17.166',
    'user': 'user1701_hotshot',
    'password': 'Hotshot.123',
    'database': 'user1701_hotshot'
}

# Эта настройка больше не нужна для хранения файлов, но Flask может ее использовать
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Создание папки больше не является обязательным, если вы не храните там другие изображения
os.makedirs(UPLOAD_FOLDER, exist_ok=True)