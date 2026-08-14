from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    # Authentification JWT
    path('login/',              TokenObtainPairView.as_view(),  name='login'),
    path('token/refresh/',      TokenRefreshView.as_view(),     name='token_refresh'),

    # Profil utilisateur connecté
    path('profil/',             views.profil,                   name='profil'),
    path('profil/modifier/',    views.modifier_profil,          name='modifier_profil'),
    path('mot-de-passe/modifier/', views.modifier_mot_de_passe, name='modifier_mdp'),

    # Gestion des utilisateurs (admin)
    path('utilisateurs/',       views.ListeUtilisateursView.as_view(),   name='liste_utilisateurs'),
    path('utilisateurs/<int:pk>/', views.DetailUtilisateurView.as_view(), name='detail_utilisateur'),
    path('utilisateurs/analystes/', views.liste_analystes, name='liste_analystes'),
]