from django.contrib import admin

# Disable "view on site" globally (for other apps too!)

admin.site.site_url = None

# Register your models here.

from kmuhelper.app import admin as appadmin
from kmuhelper.main import admin as mainadmin
from kmuhelper.emails import admin as emailadmin
from kmuhelper.api import admin as apiadmin

# Custom Admin

from django.urls import path, include

modeladmins = appadmin.modeladmins + mainadmin.modeladmins + emailadmin.modeladmins + apiadmin.modeladmins
