from django.contrib import admin

# Disable "view on site" globally (for other apps too!)

admin.site.site_url = None

# Register your models here.

from kmuhelper.app import admin
from kmuhelper.main import admin
from kmuhelper.emails import admin