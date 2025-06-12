from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS
import db

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Создаем таблицы и инициализируем фото при старте
db.create_tables()
db.initialize_photos_from_folder()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            db.add_photo(filename)
            flash('Фото успешно загружено!', 'success')
            return redirect(url_for('upload'))
        flash('Ошибка загрузки. Разрешены файлы: png, jpg, jpeg, gif', 'danger')
    return render_template('upload.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice:
            db.vote_photo(choice)
        return redirect(url_for('vote'))

    photos = db.get_two_random_photos()
    if len(photos) < 2:
        flash('Недостаточно фотографий для голосования!', 'warning')
        return redirect(url_for('index'))
    return render_template('vote.html', photo1=photos[0], photo2=photos[1])

@app.route('/top')
def top():
    top_photos = db.get_top_photos()
    return render_template('top.html', top_photos=top_photos)

if __name__ == '__main__':
    app.run(debug=True)
