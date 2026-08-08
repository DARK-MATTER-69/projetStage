from django.urls import path
from . import views

urlpatterns = [
    path('<int:dossier_pk>/', views.telecharger_rapport, name='telecharger_rapport'),
]