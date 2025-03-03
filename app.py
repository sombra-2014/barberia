import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
# Importa la configuración desde tu archivo config.py
import config

# --- Configuración de la aplicación ---
app = Flask(__name__)
# Carga la configuración desde el objeto 'config'
app.config.from_object(config)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# Asegúrate de crear la carpeta de uploads si no existe
# Esto es crucial para los permisos de escritura
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"Carpeta de uploads creada: {app.config['UPLOAD_FOLDER']}")
    except OSError as e:
        print(f"ERROR: No se pudo crear la carpeta de uploads {app.config['UPLOAD_FOLDER']}: {e}")
        # Considera salir o levantar una excepción si esto falla críticamente

# Asegúrate de crear la carpeta de img si no existe, si es que pones tu imagen barb.png ahí
# Este es para assets estáticos, no suele ser el problema de permisos de escritura dinámicos
if not os.path.exists('static/img'):
    os.makedirs('static/img')


def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Modelos de Base de Datos ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Corte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen_filename = db.Column(db.String(255), nullable=True)
    fecha_subida = db.Column(db.DateTime, default=db.func.current_timestamp())
    comentarios = db.relationship('Comentario', backref='corte', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Corte {self.nombre}>'

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    corte_id = db.Column(db.Integer, db.ForeignKey('corte.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Comentario {self.id} en Corte {self.corte_id}>'

@login_manager.user_loader
def load_user(user_id):
    # WARNING: LegacyAPIWarning: The Query.get() method is considered legacy
    # This warning is from SQLAlchemy, you can ignore it for now or
    # update to Session.get() if you're comfortable with SQLAlchemy 2.0+ patterns.
    return User.query.get(int(user_id))

# --- Rutas de la Aplicación ---

@app.route('/')
def index():
    cortes_recientes = Corte.query.order_by(Corte.fecha_subida.desc()).limit(4).all()
    return render_template('public/index.html', title='Barbería Estilo', cortes_recientes=cortes_recientes)

@app.route('/servicios')
def servicios():
    servicios_data = [
        {"nombre": "Corte Clásico", "descripcion": "Un corte atemporal y elegante, perfecto para cualquier ocasión."},
        {"nombre": "Afeitado Tradicional", "descripcion": "Experiencia de afeitado con navaja, toallas calientes y productos de calidad."},
        {"nombre": "Arreglo de Barba", "descripcion": "Diseño y mantenimiento profesional para tu barba."},
        {"nombre": "Corte de Niño", "descripcion": "Cortes divertidos y cómodos para los más pequeños."},
    ]
    return render_template('public/servicios.html', title='Nuestros Servicios', servicios=servicios_data)

@app.route('/galeria')
def galeria():
    cortes = Corte.query.options(joinedload(Corte.comentarios)).order_by(Corte.fecha_subida.desc()).all()
    for corte in cortes:
        corte.comentarios.sort(key=lambda c: c.fecha_creacion, reverse=False)
    return render_template('public/galeria.html', title='Nuestra Galería', cortes=cortes)

@app.route('/corte/<int:corte_id>/comentar', methods=['POST'])
def comentar_corte(corte_id):
    corte = Corte.query.get_or_404(corte_id)
    texto_comentario = request.form.get('comentario_texto')

    if not texto_comentario or not texto_comentario.strip():
        flash('El comentario no puede estar vacío.', 'danger')
    else:
        nuevo_comentario = Comentario(texto=texto_comentario.strip(), corte_id=corte.id)
        try:
            db.session.add(nuevo_comentario)
            db.session.commit()
            flash('¡Gracias por tu comentario!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al guardar el comentario: {e}', 'danger')
            app.logger.error(f"Error al guardar comentario en DB: {e}")

    return redirect(url_for('galeria', _anchor=f'corte-{corte_id}'))

@app.route('/testimonios')
def testimonios():
    comentarios = [
        {"nombre": "Juan P.", "texto": "¡Excelente servicio y atención! Siempre salgo contento con mi corte."},
        {"nombre": "Carlos R.", "texto": "Los mejores barberos de la ciudad, un ambiente increíble."},
        {"nombre": "Maria S.", "texto": "Aunque es una barbería, su atención es de primera. ¡Muy recomendado!"},
    ]
    return render_template('public/testimonios.html', title='Lo que dicen de nosotros', testimonios=comentarios)

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        mensaje = request.form['mensaje']
        print(f"Mensaje recibido: Nombre: {nombre}, Email: {email}, Mensaje: {mensaje}")
        flash('¡Tu mensaje ha sido enviado exitosamente!', 'success')
        return redirect(url_for('contacto'))
    return render_template('public/contacto.html', title='Contáctanos')

# --- Rutas de Administración ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
    return render_template('admin/login.html', title='Admin Login')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_cortes = Corte.query.count()
    total_comentarios = Comentario.query.count()
    return render_template('admin/dashboard.html', title='Dashboard', total_cortes=total_cortes, total_comentarios=total_comentarios)

@app.route('/admin/cortes')
@login_required
def admin_cortes():
    cortes = Corte.query.order_by(Corte.fecha_subida.desc()).all()
    return render_template('admin/cortes.html', title='Administrar Cortes', cortes=cortes)

@app.route('/admin/cortes/add', methods=['GET', 'POST'])
@login_required
def admin_add_corte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']

        if 'imagen' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(request.url)

        file = request.files['imagen']

        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                # Intenta guardar el archivo en el sistema de archivos
                file.save(file_path)
            except Exception as e:
                flash(f'Error al guardar la imagen en el servidor. Verifica los permisos de la carpeta {app.config["UPLOAD_FOLDER"]}. Error: {e}', 'danger')
                app.logger.error(f"Error saving file {file_path}: {e}") # Log detallado para depuración
                return redirect(request.url)

            # Si el archivo se guardó correctamente, procede con la base de datos
            try:
                new_corte = Corte(nombre=nombre, descripcion=descripcion, imagen_filename=unique_filename)
                db.session.add(new_corte)
                db.session.commit()
                flash('Corte añadido exitosamente.', 'success')
                return redirect(url_for('admin_cortes'))
            except Exception as e:
                db.session.rollback() # Deshace la transacción de la base de datos si falla
                flash(f'Error al guardar el corte en la base de datos: {e}', 'danger')
                app.logger.error(f"Error adding corte to DB: {e}") # Log detallado
                # Si la base de datos falla, intenta borrar el archivo que ya se subió
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        app.logger.info(f"Archivo {file_path} borrado tras fallo en DB.")
                    except OSError as remove_e:
                        app.logger.error(f"Error al intentar borrar el archivo {file_path} después del fallo en DB: {remove_e}")
                return redirect(request.url)
        else:
            flash(f'Tipo de archivo no permitido. Solo se aceptan: {", ".join(app.config["ALLOWED_EXTENSIONS"])}.', 'error')

    return render_template('admin/add_corte.html', title='Añadir Nuevo Corte')

@app.route('/admin/cortes/edit/<int:corte_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_corte(corte_id):
    corte = Corte.query.get_or_404(corte_id)

    if request.method == 'POST':
        corte.nombre = request.form['nombre']
        corte.descripcion = request.form['descripcion']

        # Si se sube una nueva imagen
        if 'imagen' in request.files and request.files['imagen'].filename != '':
            old_filename = corte.imagen_filename # Guarda el nombre del archivo antiguo
            file = request.files['imagen']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(file_path) # Intenta guardar la nueva imagen
                except Exception as e:
                    flash(f'Error al guardar la nueva imagen en el servidor. Verifica los permisos de la carpeta {app.config["UPLOAD_FOLDER"]}. Error: {e}', 'danger')
                    app.logger.error(f"Error saving new file during edit {file_path}: {e}")
                    return redirect(request.url)

                # Si la nueva imagen se guardó correctamente, procede a borrar la antigua
                if old_filename:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                            flash('Imagen anterior eliminada correctamente.', 'info')
                            app.logger.info(f"Imagen anterior {old_file_path} eliminada.")
                        except OSError as e:
                            flash(f'Advertencia: No se pudo eliminar la imagen anterior del servidor: {e}', 'warning')
                            app.logger.warning(f"Could not remove old file {old_file_path}: {e}")
                    else:
                        app.logger.info(f"La imagen antigua {old_file_path} no se encontró para eliminarla.")

                corte.imagen_filename = unique_filename # Actualiza el nombre del archivo en el modelo
                flash('Imagen actualizada exitosamente.', 'info')
            else:
                flash(f'Tipo de archivo de imagen no permitido. Solo se aceptan: {", ".join(app.config["ALLOWED_EXTENSIONS"])}.', 'error')
                return redirect(request.url)
        
        # Guarda los cambios en la base de datos (nombre, descripción, y/o nuevo filename)
        try:
            db.session.commit()
            flash('Corte actualizado exitosamente.', 'success')
            return redirect(url_for('admin_cortes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el corte en la base de datos: {e}', 'danger')
            app.logger.error(f"Error updating corte in DB: {e}")
            return redirect(request.url)

    return render_template('admin/edit_corte.html', title='Editar Corte', corte=corte)

@app.route('/admin/cortes/delete/<int:corte_id>', methods=['POST'])
@login_required
def admin_delete_corte(corte_id):
    corte = Corte.query.get_or_404(corte_id)

    # Primero intenta eliminar la imagen del servidor
    if corte.imagen_filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], corte.imagen_filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                flash('Archivo de imagen eliminado del servidor.', 'info')
                app.logger.info(f"Archivo {file_path} eliminado del servidor.")
            except OSError as e:
                flash(f'Error: No se pudo eliminar el archivo de imagen del servidor: {e}', 'danger')
                app.logger.error(f"Error deleting file {file_path}: {e}")
                # No retornamos aquí; intentamos borrar de la DB de todas formas para no dejar la entrada huérfana
        else:
            flash('Advertencia: El archivo de imagen no se encontró en el servidor, solo se eliminará de la base de datos.', 'warning')
            app.logger.warning(f"Archivo de imagen {file_path} no encontrado para eliminar.")

    # Luego intenta eliminar la entrada de la base de datos
    try:
        db.session.delete(corte)
        db.session.commit()
        flash('Corte eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el corte de la base de datos: {e}', 'danger')
        app.logger.error(f"Error deleting corte from DB: {e}")

    return redirect(url_for('admin_cortes'))

@app.cli.command('initdb')
def initdb_command():
    """Inicializa la base de datos."""
    with app.app_context():
        db.create_all()
        print('Base de datos inicializada.')

@app.cli.command('create-admin')
def create_admin_command():
    """Crea un usuario administrador."""
    with app.app_context():
        username = input("Introduce el nombre de usuario para el admin: ")
        password = input("Introduce la contraseña para el admin: ")

        if User.query.filter_by(username=username).first():
            print(f"El usuario '{username}' ya existe.")
            return

        admin_user = User(username=username)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Usuario administrador '{username}' creado exitosamente.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Asegura que las tablas existan al iniciar
        # Solo crea el admin por defecto si no hay ningún usuario
        if not User.query.first():
            print("No hay usuarios. Creando usuario 'admin' con contraseña 'password' (CÁMBIALA INMEDIATAMENTE).")
            default_admin = User(username='admin')
            default_admin.set_password('password')
            db.session.add(default_admin)
            db.session.commit()
    # Esta es la línea modificada para permitir acceso desde la red local
    app.run(debug=True, host='0.0.0.0')