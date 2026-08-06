from django.urls import path
from . import views

urlpatterns = [
    # Clients
    path('clients/',            views.ListeClientsView.as_view(),   name='liste_clients'),
    path('clients/<int:pk>/',   views.DetailClientView.as_view(),   name='detail_client'),

    # Dossiers
    path('',                    views.ListeDossiersView.as_view(),  name='liste_dossiers'),
    path('<int:pk>/',           views.DetailDossierView.as_view(),  name='detail_dossier'),
    path('<int:pk>/soumettre/', views.soumettre_dossier,            name='soumettre_dossier'),
    path('<int:pk>/valider/',   views.valider_dossier,              name='valider_dossier'),
    path('<int:pk>/documents/', views.upload_document,              name='upload_document'),
]