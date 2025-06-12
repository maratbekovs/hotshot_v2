from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from werkzeug.utils import secure_filename
from functools import wraps
import os
import db
from config import ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Инициализируем таблицы при первом запуске
with app.app_context():
    db.create_tables()


# --- АДМИН-ЧАСТЬ ---

def admin_required(f):
    """Декоратор для защиты страниц, требующих прав администратора."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pending_photos = db.get_pending_photos()
    return render_template('admin_dashboard.html', photos=pending_photos)


@app.route('/admin/approve/<int:photo_id>')
@admin_required
def approve_photo(photo_id):
    db.update_photo_status(photo_id, 'approved')
    flash('Фото одобрено.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:photo_id>')
@admin_required
def reject_photo(photo_id):
    db.update_photo_status(photo_id, 'rejected')
    flash('Фото отклонено и удалено.', 'warning')
    return redirect(url_for('admin_dashboard'))


# --- ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_data = file.read()
            db.add_photo(filename, file_data)
            # Изменено сообщение для пользователя
            flash('Спасибо! Ваше фото отправлено на модерацию.', 'success')
            return redirect(url_for('upload'))
        flash('Ошибка загрузки. Разрешены файлы: png, jpg, jpeg, gif', 'danger')
    return render_template('upload.html')


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    session.setdefault('user_id', os.urandom(16).hex())
    user_session_id = session['user_id']

    if request.method == 'POST':
        choice_id = request.form.get('choice')
        if choice_id and choice_id != 'skip':
            db.vote_photo(int(choice_id))
        return redirect(url_for('vote'))

    photos = db.get_two_random_photos(user_session_id)
    if len(photos) < 2:
        flash('Новых фотографий для голосования пока нет. Зайдите позже!', 'warning')
        return redirect(url_for('index'))

    db.record_view(user_session_id, photos[0]['photo_id'])
    db.record_view(user_session_id, photos[1]['photo_id'])

    return render_template('vote.html', photo1=photos[0], photo2=photos[1])


@app.route('/top')
def top():
    top_photos = db.get_top_photos()
    return render_template('top.html', top_photos=top_photos)


@app.route('/image/<int:photo_id>')
def get_image(photo_id):
    image_data = db.get_photo_data(photo_id)
    if image_data:
        return Response(image_data, mimetype='image/jpeg')
    return 'Image not found', 404


if __name__ == '__main__':
    app.run(debug=True)