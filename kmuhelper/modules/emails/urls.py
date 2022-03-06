from django.urls import path

from kmuhelper.modules.emails import views

#######################

urlpatterns = [
    path('<int:object_id>/view/', views.email_view,
         name="email-view"),
    path('attachments/<int:object_id>/view/', views.attachment_view,
         name="attachment-view"),

    path('', views.email_index,
         name="email-index"),
]
