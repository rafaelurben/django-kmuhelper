from django.contrib import admin

from kmuhelper.api import admin as apiadmin
from kmuhelper.emails import admin as emailadmin
from kmuhelper.main import admin as mainadmin
from kmuhelper.app import admin as appadmin

# Disable "view on site" globally (for other apps too!)

admin.site.site_url = None

# List of all models and their corresponding admins

modeladmins = appadmin.modeladmins + mainadmin.modeladmins + \
    emailadmin.modeladmins + apiadmin.modeladmins
