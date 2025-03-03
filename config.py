import os

# Obtiene la ruta base del directorio donde se encuentra este archivo config.py
basedir = os.path.abspath(os.path.dirname(__file__))

# Clave secreta para seguridad de Flask (sesiones, CSRF, etc.)
# Se recomienda usar una variable de entorno en producción.
# ¡CAMBIA 'una_clave_secreta_muy_dificil_de_adivinar_y_larga' por algo único y complejo!
SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar_y_larga'

# Configuración de la base de datos SQLite
# Se guardará en la carpeta 'instance' dentro de la ruta base
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'barberia.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False # Desactiva el seguimiento de modificaciones para ahorrar recursos

# Carpeta donde se subirán las imágenes
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')

# Extensiones de archivo permitidas para las subidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'} # Asegúrate de que 'webp' esté aquí si lo necesitas

# Tamaño máximo del contenido (archivos) que se pueden subir (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024