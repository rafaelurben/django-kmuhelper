from django.contrib import admin

from kmuhelper.modules.api import admin as apiadmin
from kmuhelper.modules.emails import admin as emailadmin
from kmuhelper.modules.main import admin as mainadmin
from kmuhelper.modules.app import admin as appadmin
from kmuhelper.modules.settings import admin as settingsadmin

from kmuhelper.modules.integrations.paymentimport import admin as paymentimportadmin

# Disable "view on site" globally (for other apps too!)

admin.site.site_url = None

# List of all models and their corresponding admins

modeladmins = []

for adminclass in [apiadmin, emailadmin, mainadmin, appadmin, settingsadmin, paymentimportadmin]:
    modeladmins.extend(adminclass.modeladmins)
