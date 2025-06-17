from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from functools import wraps
import os
import db
from io import BytesIO
from PIL import Image
from config import ADMIN_USERNAME, ADMIN_PASSWORD

app = Flask(__name__)
app.secret_key = os.urandom(24)

# При первом запуске или перезапуске, убеждаемся, что таблицы созданы
with app.app_context():
    db.create_tables()


# --- Контекстный процессор и Декораторы ---

@app.context_processor
def inject_user_data():
    if 'user_id' in session:
        unread_messages = db.get_unread_message_count(session['user_id'])
        unread_notifications = db.get_unread_notification_count(session['user_id'])
        return dict(current_user_id=session['user_id'], unread_messages=unread_messages,
                    unread_notifications=unread_notifications)
    return dict()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def guest_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Доступ запрещен. У вас нет прав администратора.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


# --- Маршруты для регистрации и авторизации ---

@app.route('/register', methods=['GET', 'POST'])
@guest_only
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        if password != confirm_password:
            flash('Пароли не совпадают.', 'danger')
            return redirect(url_for('register'))
        if db.get_user_by_username(username):
            flash('Пользователь с таким никнеймом уже существует.', 'danger')
            return redirect(url_for('register'))
        user_id = db.create_user(username, password, first_name, last_name)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            session['is_admin'] = False
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Произошла ошибка при регистрации.', 'danger')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
@guest_only
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.get_user_by_username(username)
        if user and db.verify_password(password, user['password_hash']):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            return redirect(url_for('index'))
        else:
            flash('Неверный никнейм или пароль.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('landing'))


# --- Основные маршруты приложения ---

@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('landing.html')


@app.route('/home')
@login_required
def index():
    current_user_id = session['user_id']
    feed_items = db.get_friends_feed(current_user_id)
    enriched_feed = db.get_likes_and_comments_for_feed(feed_items, current_user_id)
    suggested_friends = db.get_suggested_friends(current_user_id)
    user_data = db.get_user_by_id(current_user_id)
    user_data['active_submission_id'] = db.check_user_contest_submission(current_user_id)
    return render_template('index.html', feed=enriched_feed, suggestions=suggested_friends, user=user_data)


# --- Маршруты голосования и топа ---

@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    current_user_id = session['user_id']
    if request.method == 'POST':
        choice_id = request.form.get('choice')
        if choice_id and choice_id.isdigit():
            db.vote_for_photo(int(choice_id))
        return redirect(url_for('vote'))
    photos = db.get_photos_for_voting(current_user_id)
    if len(photos) < 2:
        flash('Новых фотографий для голосования пока нет. Зайдите позже!', 'warning')
        return redirect(url_for('index'))
    db.record_photo_view(current_user_id, photos[0]['photo_id'])
    db.record_photo_view(current_user_id, photos[1]['photo_id'])
    friendship1 = db.get_friendship_status(current_user_id, photos[0]['user_id'])
    friendship2 = db.get_friendship_status(current_user_id, photos[1]['user_id'])
    return render_template('vote.html', photo1=photos[0], photo2=photos[1], friendship1=friendship1,
                           friendship2=friendship2)


@app.route('/top')
@login_required
def top():
    top_photos = db.get_top_10_photos()
    return render_template('top.html', top_photos=top_photos)


# --- Маршруты профилей и пользователей ---

@app.route('/profile')
@login_required
def profile():
    current_user_id = session['user_id']
    user_data = db.get_user_by_id(current_user_id)
    friend_requests = db.get_friend_requests(current_user_id)
    feed_items = db.get_user_feed(current_user_id)
    enriched_feed = db.get_likes_and_comments_for_feed(feed_items, current_user_id)
    user_data['active_submission_id'] = db.check_user_contest_submission(current_user_id)
    return render_template('profile.html', user=user_data, requests=friend_requests, feed=enriched_feed)


@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    relationship_status = request.form.get('relationship_status')
    db.update_user_profile(session['user_id'], first_name, last_name, relationship_status)
    flash('Данные профиля успешно обновлены.', 'success')
    return redirect(url_for('profile'))


@app.route('/profile/avatar/upload', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')
    if file:
        img = Image.open(file.stream)
        crop_details = request.form
        left, top, right, bottom = (int(float(crop_details.get(k))) for k in ('x', 'y', 'width', 'height'))
        right += left
        bottom += top
        cropped_img = img.crop((left, top, right, bottom))
        output_buffer = BytesIO()
        cropped_img.save(output_buffer, format='PNG')
        db.update_user_avatar(session['user_id'], output_buffer.getvalue())
        flash('Аватар успешно обновлен.', 'success')
    return redirect(url_for('profile'))


@app.route('/users')
@login_required
def find_users():
    search_query = request.args.get('q', '').strip()
    found_users = db.search_users(session['user_id'], search_query)
    return render_template('users.html', users=found_users, search_query=search_query)


@app.route('/user/<int:user_id>')
@login_required
def view_profile(user_id):
    if user_id == session['user_id']:
        return redirect(url_for('profile'))
    user_data = db.get_user_by_id(user_id)
    if not user_data:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('find_users'))
    friendship = db.get_friendship_status(session['user_id'], user_id)
    is_friend = friendship and friendship['status'] == 'accepted'
    if user_data['profile_type'] == 'private' and not is_friend:
        return render_template('private_profile.html', user=user_data, friendship=friendship)
    feed_items = db.get_user_feed(user_id)
    enriched_feed = db.get_likes_and_comments_for_feed(feed_items, session['user_id'])
    return render_template('view_profile.html', user=user_data, friendship=friendship, feed=enriched_feed)


@app.route('/profile/privacy', methods=['POST'])
@login_required
def set_profile_privacy():
    privacy_type = request.form.get('privacy')
    if privacy_type in ['public', 'private']:
        db.update_profile_privacy(session['user_id'], privacy_type)
        flash('Настройки приватности обновлены.', 'success')
    return redirect(url_for('profile'))


# --- Маршруты для управления дружбой ---
@app.route('/friend/add/<int:addressee_id>')
@login_required
def add_friend(addressee_id):
    db.send_friend_request(session['user_id'], addressee_id)
    db.create_notification(addressee_id, session['user_id'], 'friend_request')
    flash('Заявка в друзья отправлена.', 'success')
    return redirect(url_for('view_profile', user_id=addressee_id))


@app.route('/friend/accept/<int:requester_id>')
@login_required
def accept_friend(requester_id):
    db.update_friendship_status(requester_id, session['user_id'], 'accepted')
    db.create_notification(requester_id, session['user_id'], 'friend_accept')
    flash('Заявка в друзья принята.', 'success')
    return redirect(url_for('profile'))


@app.route('/friend/decline/<int:requester_id>')
@login_required
def decline_friend(requester_id):
    db.update_friendship_status(requester_id, session['user_id'], 'declined')
    flash('Заявка в друзья отклонена.', 'warning')
    return redirect(url_for('profile'))


# --- Маршруты для чата и сообщений ---
@app.route('/messages')
@login_required
def messages_list():
    friends = db.get_friends_list(session['user_id'])
    return render_template('messages.html', friends=friends)


@app.route('/messages/<int:friend_id>')
@login_required
def chat(friend_id):
    current_user_id = session['user_id']
    friendship = db.get_friendship_status(current_user_id, friend_id)
    if not friendship or friendship['status'] != 'accepted':
        flash('Вы можете общаться только с друзьями.', 'danger')
        return redirect(url_for('messages_list'))
    conversation = db.get_conversation(current_user_id, friend_id)
    db.mark_messages_as_read(current_user_id, friend_id)
    friend_data = db.get_user_by_id(friend_id)
    return render_template('chat.html', friend=friend_data, conversation=conversation)


# --- Маршруты API ---
@app.route('/api/send_message/<int:friend_id>', methods=['POST'])
@login_required
def api_send_message(friend_id):
    content = request.form.get('content')
    if content:
        db.send_message(session['user_id'], friend_id, content)
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Пустое сообщение'}, 400


@app.route('/api/messages/<int:friend_id>')
@login_required
def get_new_api_messages(friend_id):
    new_messages = db.get_new_messages(session['user_id'], friend_id)
    if new_messages:
        db.mark_messages_as_read(session['user_id'], friend_id)
    messages_list = [
        {'sender_id': msg['sender_id'], 'content': msg['content'], 'sent_at_short': msg['sent_at'].strftime('%H:%M')}
        for msg in new_messages]
    return {'messages': messages_list}


# ИСПРАВЛЕННЫЙ МАРШРУТ
@app.route('/api/like', methods=['POST'])
@login_required
def like_item_route():
    item_type = request.form.get('item_type')
    item_id = int(request.form.get('item_id'))

    was_added = db.add_or_remove_like(session['user_id'], item_type, item_id)

    if was_added:
        author_id = db.get_item_author(item_type, item_id)
        if author_id and author_id != session['user_id']:
            post_id = item_id if item_type == 'post' else None
            photo_id = item_id if item_type == 'photo' else None
            db.create_notification(author_id, session['user_id'], 'new_like', post_id=post_id, photo_id=photo_id)

    return {'status': 'success'}


@app.route('/api/comment', methods=['POST'])
@login_required
def comment_item_route():
    item_type = request.form.get('item_type')
    item_id = int(request.form.get('item_id'))
    content = request.form.get('content').strip()
    if not content: return {'status': 'error', 'message': 'Комментарий не может быть пустым'}, 400

    new_comment = db.add_comment(session['user_id'], content, item_type, item_id)

    author_id = db.get_item_author(item_type, item_id)
    if author_id and author_id != session['user_id']:
        post_id = item_id if item_type == 'post' else None
        photo_id = item_id if item_type == 'photo' else None
        db.create_notification(author_id, session['user_id'], 'new_comment', post_id=post_id, photo_id=photo_id)

    new_comment['created_at'] = new_comment['created_at'].strftime('%d %b %Y в %H:%M')
    return {'status': 'success', 'comment': new_comment}


# --- Маршруты для контента ---
@app.route('/post/create', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    if content and content.strip():
        db.create_text_post(session['user_id'], content.strip())
        flash('Пост успешно опубликован!', 'success')
    else:
        flash('Текст поста не может быть пустым.', 'warning')
    return redirect(url_for('profile'))


@app.route('/gallery/add', methods=['POST'])
@login_required
def add_to_gallery():
    file = request.files.get('gallery_photo')
    caption = request.form.get('caption', '').strip()
    crop_details = request.form
    if file and crop_details.get('x'):
        try:
            img = Image.open(file.stream)
            left, top, right, bottom = (int(float(crop_details.get(k))) for k in ('x', 'y', 'width', 'height'))
            right += left
            bottom += top
            cropped_img = img.crop((left, top, right, bottom))
            output_buffer = BytesIO()
            cropped_img.save(output_buffer, format='PNG')
            db.add_gallery_photo(session['user_id'], output_buffer.getvalue(), caption)
            flash('Фото добавлено в вашу галерею!', 'success')
        except Exception as e:
            print(f"Error during image processing: {e}")
            flash('Произошла ошибка при обработке изображения.', 'danger')
    else:
        flash('Не удалось загрузить файл или отсутствуют данные для обрезки.', 'danger')
    return redirect(url_for('profile'))


@app.route('/photo/nominate/<int:photo_id>')
@login_required
def nominate_photo(photo_id):
    existing_submission = db.check_user_contest_submission(session['user_id'])
    if existing_submission:
        flash('У вас уже есть одна фотография на конкурсе или на модерации.', 'warning')
        return redirect(url_for('profile'))
    success = db.nominate_photo_for_contest(photo_id, session['user_id'])
    if success:
        flash('Фотография отправлена на модерацию!', 'success')
    else:
        flash('Не удалось отправить фото на конкурс.', 'danger')
    return redirect(url_for('profile'))


@app.route('/photo/cancel_nomination/<int:photo_id>')
@login_required
def cancel_nomination_route(photo_id):
    db.cancel_contest_submission(photo_id, session['user_id'])
    flash('Заявка на участие в конкурсе отменена.', 'success')
    return redirect(url_for('profile'))


@app.route('/avatar/<int:user_id>')
def get_avatar(user_id):
    user = db.get_user_by_id(user_id)
    if user and user.get('profile_pic_data'):
        return Response(user['profile_pic_data'], mimetype='image/png')
    return redirect(url_for('static', filename='images/default_avatar.png'))


@app.route('/photo/<int:photo_id>')
def get_contest_photo(photo_id):
    photo_data = db.get_photo_data_by_id(photo_id)
    if photo_data: return Response(photo_data, mimetype='image/jpeg')
    return 'Image not found', 404


@app.route('/post/delete/<int:post_id>')
@login_required
def delete_post_route(post_id):
    db.delete_post(post_id, session['user_id'])
    flash('Пост удален.', 'success')
    return redirect(url_for('profile'))


@app.route('/photo/delete/<int:photo_id>')
@login_required
def delete_photo_route(photo_id):
    db.delete_photo(photo_id, session['user_id'])
    flash('Фото удалено.', 'success')
    return redirect(url_for('profile'))


# --- АДМИН-ПАНЕЛЬ ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.get_user_by_username(username)
        if user and user.get('is_admin') and db.verify_password(password, user['password_hash']):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['is_admin'] = True
            flash('Вы вошли как администратор!', 'success')
            return redirect(url_for('admin_dashboard'))
        elif username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session['is_admin'] = True
            session['username'] = 'Admin'
            flash('Вы вошли как главный администратор!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверные данные или нет прав администратора.', 'danger')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pending_photos = db.get_pending_photos_with_user()
    return render_template('admin_dashboard.html', photos=pending_photos)


@app.route('/admin/approve/<int:photo_id>')
@admin_required
def approve_photo(photo_id):
    db.update_photo_status(photo_id, 'approved')
    flash('Фотография одобрена.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:photo_id>')
@admin_required
def reject_photo(photo_id):
    db.update_photo_status(photo_id, 'rejected')
    flash('Фотография отклонена.', 'warning')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reset_votes')
@admin_required
def reset_votes_route():
    db.reset_all_votes()
    flash('Все голоса сброшены, новый сезон голосования начат!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/notifications')
@login_required
def notifications():
    user_notifications = db.get_user_notifications(session['user_id'])
    db.mark_notifications_as_read(session['user_id'])
    return render_template('notifications.html', notifications=user_notifications)


# --- Запуск приложения ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)
