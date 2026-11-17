from flask import Flask, request, redirect, send_from_directory, render_template_string
import sqlite3

app = Flask(__name__, static_folder='.')

# Функция подключения к БД
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- 1. отдача html страниц ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# --- 2. логика регистрации ---
@app.route('/register', methods=['POST'])
def register():
    # Получаем данные из формы
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')

    # ПРОВЕРКА: Если данных нет, выводим ошибку
    if not name or not email or not password:
        return "<h2>Ошибка: Не все поля заполнены! <a href='/register.html'>Назад</a></h2>"

    conn = get_db()
    try:
        # Сохраняем в базу
        conn.execute('INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)', 
                     (name, email, password))
        conn.commit()
        conn.close()
        # Если всё ок, перекидываем на страницу входа
        return redirect('/login.html')
        
    except sqlite3.IntegrityError:
        # Если такой email уже есть
        conn.close()
        return "<h2>Ошибка: Этот email уже зарегистрирован! <a href='/login.html'>Войти</a></h2>"

# --- 3. логика входа ---
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    conn = get_db()
    
    # 1. Ищем пользователя только по email
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    # Если такого email нет вообще
    if not user:
        conn.close()
        return "<h2>Пользователь с таким email не найден. <a href='/register.html'>Зарегистрируйтесь</a></h2>"

    # 2. Если нашли, проверяем пароль
    if user['password_hash'] != password:
        conn.close()
        return "<h2>Неверный пароль. <a href='/login.html'>Назад</a></h2>"

    # 3. Если всё совпало — пускаем
    conn.close()
    return redirect('/')
    
@app.route('/api/users')
def show_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    if not users:
        return "<h2>База данных пуста! Вы никто не зарегистрировались.</h2>"
        
    html = "<h2>Список пользователей в базе:</h2><ul>"
    for u in users:
        html += f"<li>Имя: <b>{u['full_name']}</b> | Email: <b>{u['email']}</b> | Пароль: <b>{u['password_hash']}</b></li>"
    html += "</ul>"
    return html

if __name__ == '__main__':
    # создаем базу данных при первом запуске, если её нет
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY, full_name TEXT, email TEXT UNIQUE, password_hash TEXT)''')
    conn.commit()
    conn.close()
    app.run(debug=True, port=5000)