import os
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///film.db'
app.config['ADMIN_REGISTRATION_SECRET'] = secrets.token_hex(16)  # Generate a secret token
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'img')
db = SQLAlchemy(app)

# Fungsi untuk mengecek current_user di template
@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    return dict(current_user=user)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(200), nullable=False)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not User.query.get(session['user_id']).is_admin:
            flash('Akses ditolak. Anda bukan admin.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    return dict(current_user=user)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        admin_code = request.form.get('admin_code', '')

        # Validasi password
        if password != confirm_password:
            flash('Password tidak cocok', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah terdaftar', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        is_admin = False
        if admin_code == app.config['ADMIN_REGISTRATION_SECRET']:
            is_admin = True
            flash('Registrasi Admin Berhasil!', 'success')
        
        new_user = User(
            username=username, 
            password=hashed_password, 
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Login gagal. Periksa username dan password.', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu', 'danger')
        return redirect(url_for('login'))
    films = Film.query.all()
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', films=films, user=user)

@app.route('/admin')
@admin_required
def admin_page():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/get_admin_code')
def get_admin_code():
    return f"Kode Admin: {app.config['ADMIN_REGISTRATION_SECRET']}"

@app.route('/edit_film/<int:film_id>', methods=['GET', 'POST'])
def edit_film(film_id):
    if not User.is_admin:
        flash('Anda tidak memiliki akses!', 'danger')
        return redirect(url_for('dashboard'))
    
    film = Film.query.get_or_404(film_id)
    
    if request.method == 'POST':
        try:
            if not request.form['judul'].strip():
                flash('Judul film tidak boleh kosong!', 'danger')
                return render_template('edit_film.html', film=film)
            
            if not request.form['deskripsi'].strip():
                flash('Deskripsi film tidak boleh kosong!', 'danger')
                return render_template('edit_film.html', film=film)
            
            film.judul = request.form['judul']
            film.deskripsi = request.form['deskripsi']
            
            if 'gambar' in request.files:
                file = request.files['gambar']
                if file.filename != '':
                    # Validasi tipe file
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if not allowed_file(file.filename):
                        flash('Tipe file tidak diizinkan! Gunakan PNG, JPG, atau GIF.', 'danger')
                        return render_template('edit_film.html', film=film)
                    
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size > 5 * 1024 * 1024:  # 5MB
                        flash('Ukuran file terlalu besar! Maks 5MB.', 'danger')
                        return render_template('edit_film.html', film=film)
                    
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    old_image_path = os.path.join('static', film.gambar)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                    
                    film.gambar = f'img/{filename}'
            
            db.session.commit()
            flash('Film berhasil diperbarui!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error editing film: {str(e)}')
            flash('Terjadi kesalahan saat memperbarui film.', 'danger')
            return render_template('edit_film.html', film=film)
    
    return render_template('edit_film.html', film=film)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/tambah_film', methods=['GET', 'POST'])
def tambah_film():
    if not User.is_admin:
        flash('Anda tidak memiliki akses!')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        judul = request.form['judul']
        deskripsi = request.form['deskripsi']
        
        if 'gambar' in request.files:
            file = request.files['gambar']
            if file.filename != '':
                # Simpan file gambar
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Buat objek Film baru
                new_film = Film(
                    judul=judul, 
                    deskripsi=deskripsi, 
                    gambar=f'img/{filename}'
                )
                
                db.session.add(new_film)
                db.session.commit()
                
                flash('Film berhasil ditambahkan!')
                return redirect(url_for('dashboard'))
    
    return render_template('tambah_film.html')

@app.route('/hapus_film/<int:film_id>', methods=['POST'])
def hapus_film(film_id):
    if not User.is_admin:
        flash('Anda tidak memiliki akses!')
        return redirect(url_for('dashboard'))
    
    film = Film.query.get_or_404(film_id)
    db.session.delete(film)
    db.session.commit()
    
    flash('Film berhasil dihapus!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Anda berhasil logout', 'success')
    return redirect(url_for('login'))

# Error handler untuk kesalahan 404 (Not Found)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Halaman tidak ditemukan'), 404

# Error handler untuk kesalahan 500 (Internal Server Error)
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Terjadi kesalahan internal'), 500

# Tambahkan logging
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/application.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Aplikasi dimulai')

# Panggil setup logging saat inisialisasi app
setup_logging(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)