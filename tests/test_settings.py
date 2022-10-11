# Test settings for django-kmuhelper

DEBUG=True
SECRET_KEY="fa^c^jx6$epw$%#b3bc)=cn_dp@misn+5l-cogxw$w3lsdl3r="
DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdatabase',
    }
}
ROOT_URLCONF='kmuhelper.urls'
MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
INSTALLED_APPS=(
    'tests',
    'kmuhelper',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)
TEMPLATES=[
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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]
KMUHELPER_DOMAIN=""
KMUHELPER_LOG_EMAIL=""
KMUHELPER_EMAILS_DEFAULT_CONTEXT={
    "precontent": "",
    "postcontent": "",
    "header_title": "KMUHelper TESTS",
}
