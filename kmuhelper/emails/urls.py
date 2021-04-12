from django.urls import path

from kmuhelper.emails import views

#######################

urlpatterns = [
    path('<int:object_id>/view', views.email_view,
         name="email-view"),
    path('attachments/<int:object_id>/view', views.attachment_view,
         name="attachment-view"),
]
