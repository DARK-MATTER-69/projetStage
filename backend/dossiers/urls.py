from django.urls import path
from . import views

urlpatterns = [
    # Clients
    path('clients/',                               views.ListeClientsView.as_view(),   name='liste_clients'),
    path('clients/<int:pk>/',                      views.DetailClientView.as_view(),   name='detail_client'),
    path('clients/<int:client_pk>/salaires/',      views.historique_salaires,          name='historique_salaires'),
    path('clients/<int:client_pk>/impayes/',       views.impayes_client,               name='impayes_client'),
    path('impayes/<int:impaye_pk>/regulariser/',   views.regulariser_impaye,           name='regulariser_impaye'),

    # Dossiers
    path('',                                       views.ListeDossiersView.as_view(),  name='liste_dossiers'),
    path('<int:pk>/',                              views.DetailDossierView.as_view(),  name='detail_dossier'),
    path('<int:pk>/soumettre/',                    views.soumettre_dossier,            name='soumettre_dossier'),
    path('<int:pk>/valider/',                      views.valider_dossier,              name='valider_dossier'),
    path('<int:pk>/documents/',                    views.upload_document,              name='upload_document'),
    path('<int:pk>/recalculer/',                   views.recalculer_score,             name='recalculer_score'),
    path('clients/recherche/',                     views.rechercher_client,            name='rechercher_client'),
    path('notifications/',                         views.mes_notifications,            name='mes_notifications'),
    path('notifications/<int:pk>/lue/',            views.marquer_notification_lue,     name='notification_lue'),

    # Dashboard
    path('dashboard/stats/',                       views.stats_dashboard,              name='stats_dashboard'),
]