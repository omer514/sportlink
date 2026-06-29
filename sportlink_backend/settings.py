# ============================================================
# SPORTLINK — Configuration principale Django
# Ce fichier contrôle tout le comportement du projet
# ============================================================

from pathlib import Path
from decouple import config       # Lit les variables du fichier .env
from datetime import timedelta    # Pour définir la durée des tokens JWT

import os
import dj_database_url

# Chemin de base du projet (le dossier sportlink/)
BASE_DIR = Path(__file__).resolve().parent.parent

# ── SÉCURITÉ ────────────────────────────────────────────────
# La clé secrète est lue depuis le fichier .env — jamais en dur dans le code
SECRET_KEY = config('SECRET_KEY')

# En mode DEBUG=True, Django affiche les erreurs en détail
# Mettre False absolument avant de mettre en production
DEBUG = config('DEBUG', default=True, cast=bool)

# Hôtes autorisés à accéder au serveur
# '*' = tout le monde (ok en développement, à restreindre en production)
ALLOWED_HOSTS = ['*']


# ── APPLICATIONS INSTALLÉES ─────────────────────────────────
INSTALLED_APPS = [
    # Applications natives Django
    'django.contrib.admin',           # Panneau d'administration
    'django.contrib.auth',            # Système d'authentification
    'django.contrib.contenttypes',    # Gestion des types de contenu
    'django.contrib.sessions',        # Gestion des sessions
    'django.contrib.messages',        # Système de messages flash
    'django.contrib.staticfiles',     # Gestion des fichiers statiques (CSS, JS)

    # Packages externes installés via pip
    'rest_framework',                 # Django REST Framework — pour créer l'API
    'rest_framework_simplejwt',       # Authentification par tokens JWT
    'corsheaders',                    # Autorise Flutter à appeler l'API depuis un autre domaine
    'cloudinary',                     # SDK Cloudinary pour gérer les médias
    'cloudinary_storage',             # Stockage des fichiers sur Cloudinary

    # Nos applications SportLink (créées à l'étape 6)
    'accounts',    # Inscription, connexion, gestion des utilisateurs
    'profiles',    # Profils joueurs et recruteurs
    'media',       # Photos et vidéos
    'feed',        # Feed de découverte style TikTok
]


# ── MIDDLEWARE ───────────────────────────────────────────────
# Les middlewares sont des couches qui traitent chaque requête avant qu'elle arrive à la vue
MIDDLEWARE = [
    # CORS doit être en premier pour intercepter les requêtes Flutter
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← ajoute cette ligne juste après SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

# Fichier qui contient toutes les URLs du projet
ROOT_URLCONF = 'sportlink_backend.urls'


# ── TEMPLATES ───────────────────────────────────────────────
# Configuration du moteur de templates Django (pages HTML si besoin)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sportlink_backend.wsgi.application'


# ── BASE DE DONNÉES ──────────────────────────────────────────
# SQLite pour le développement local — simple, pas besoin d'installation
# On passera à PostgreSQL quand on déploie en ligne
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}


# ── MODÈLE UTILISATEUR PERSONNALISÉ ─────────────────────────
# On dit à Django d'utiliser notre propre modèle User
# au lieu du modèle par défaut — IMPORTANT : à définir avant la 1ère migration
AUTH_USER_MODEL = 'accounts.User'


# ── DJANGO REST FRAMEWORK ────────────────────────────────────
# Configuration globale de l'API REST
REST_FRAMEWORK = {
    # Par défaut, toutes les requêtes doivent avoir un token JWT valide
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Par défaut, l'utilisateur doit être connecté pour accéder à l'API
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Pagination automatique — 20 profils par page dans les listes
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# ── CONFIGURATION JWT ────────────────────────────────────────
# Durée de vie des tokens d'authentification
SIMPLE_JWT = {
    # Le token d'accès expire après 1 heure
    # L'app Flutter devra en demander un nouveau avec le refresh token
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),

    # Le refresh token est valable 7 jours
    # Après 7 jours sans connexion, l'utilisateur doit se reconnecter
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # À chaque refresh, un nouveau refresh token est généré
    # Ça améliore la sécurité
    'ROTATE_REFRESH_TOKENS': True,
}


# ── CORS ─────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Sans ça, Flutter ne peut pas appeler l'API Django (bloqué par le navigateur)
# True = tout le monde peut appeler l'API (ok en développement)
# En production, on listera uniquement les domaines autorisés
CORS_ALLOW_ALL_ORIGINS = True


# ── CLOUDINARY ───────────────────────────────────────────────
# Configuration du service de stockage des photos et vidéos
# Les valeurs sont lues depuis le fichier .env
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# Django utilisera Cloudinary pour stocker tous les fichiers uploadés
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# ── FICHIERS STATIQUES ET MÉDIAS ─────────────────────────────
MEDIA_URL  = '/media/'     # URL pour les fichiers uploadés par les utilisateurs
MEDIA_ROOT = BASE_DIR / 'media_files'   # Dossier local (utilisé si pas Cloudinary)


# ── LANGUE ET FUSEAU HORAIRE ─────────────────────────────────
LANGUAGE_CODE = 'fr-fr'                 # Interface Django en français
TIME_ZONE     = 'Africa/Porto-Novo'     # Fuseau horaire du Bénin
USE_I18N      = True                    # Internationalisation activée
USE_TZ        = True                    # Dates stockées en UTC dans la BDD


# ── DIVERS ───────────────────────────────────────────────────
# Type de clé primaire par défaut pour tous les modèles
# BigAutoField = entier 64 bits, évite les dépassements à grande échelle
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
