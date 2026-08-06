from django.urls import path
from . import views

urlpatterns = [
    path('<int:dossier_pk>/', views.score_dossier, name='score_dossier'),
]