from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Accueil Public
    path('', views.landing, name='landing'),
    
    # 2. Espace Jeu (Protégé)
    path('dashboard/', views.dashboard, name='dashboard'), # Ancien index
    path('construire/', views.construire, name='construire'),
    path('rejoindre/', views.rejoindre_ville, name='rejoindre'),
    
    # 3. Authentification
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),

    # 4. Gestion des bâtiments
    path('batiment/<int:id_batiment>/', views.batiment_detail, name='batiment_detail'),
    path('detruire/<int:id_batiment>/', views.detruire_batiment, name='detruire_batiment'),
    path('reparer/<int:id_batiment>/', views.reparer_batiment, name='reparer_batiment'),
    path('nommer_directeur/<int:id_batiment>/', views.nommer_directeur, name='nommer_directeur'),

    # 5. Gestion RH
    path('proposer/<int:id_batiment>/', views.proposer_poste, name='proposer_poste'),
    path('postuler/<int:id_batiment>/', views.postuler, name='postuler'),
    path('candidature/<int:id_candidature>/<str:decision>/', views.traiter_candidature, name='traiter_candidature'),
    path('notification/delete/<int:id_candidature>/', views.supprimer_notification, name='supprimer_notification'),
    path('notification/delete-all/', views.supprimer_toutes_notifications, name='supprimer_toutes_notifications'),
    path('licencier/<int:id_citoyen>/', views.licencier, name='licencier'),
    path('demissionner/', views.demissionner, name='demissionner'),

    # 6. Logement
    path('emmenager/<int:id_batiment>/', views.emmenager, name='emmenager'),
    path('demenager/', views.demenager, name='demenager'),

    # 7. Profil
    path('profil/', views.mon_profil, name='mon_profil'),

    # 8. Administration Ville (Maire)
    path('parametres/', views.parametres_ville, name='parametres_ville'),
    path('parametres/delete_info/<int:id_info>/', views.supprimer_info, name='supprimer_info'),
    path('publier/ville/', views.publier_actualite, {'id_batiment': 0}, name='publier_news_ville'),
    path('publier/batiment/<int:id_batiment>/', views.publier_actualite, name='publier_note_interne'),
    path('supprimer_actu/<int:id_actu>/', views.supprimer_actualite, name='supprimer_actualite'),

    # 9. Gestion Citoyens (Admin)
    path('gestion/citoyens/', views.gestion_citoyens, name='gestion_citoyens'),
    path('gestion/citoyens/add/', views.ajouter_citoyen, name='ajouter_citoyen'),
    path('gestion/citoyens/edit/<int:id_citoyen>/', views.modifier_citoyen_admin, name='modifier_citoyen_admin'),
    path('gestion/citoyens/delete/<int:id_citoyen>/', views.supprimer_citoyen_admin, name='supprimer_citoyen_admin'),
    path('gestion/promouvoir/<int:id_citoyen>/', views.promouvoir_adjoint, name='promouvoir_adjoint'),
    path('finance/salaires/', views.verser_salaires, name='verser_salaires'),
    path('commerce/voiture/', views.acheter_voiture, name='acheter_voiture'),
    path('soigner/<int:id_batiment>/', views.se_soigner, name='se_soigner'),
    path('phone/', views.telephone_index, name='phone_index'),
    path('phone/chat/<int:id_destinataire>/', views.telephone_chat, name='telephone_chat'),
    path('deplacer/<int:id_batiment>/', views.deplacer_batiment, name='deplacer_batiment'),
    path('deplacer/valider/<int:id_batiment>/<int:new_x>/<int:new_y>/', views.valider_deplacement, name='valider_deplacement'),
    path('finance/impots/', views.collecter_impots, name='collecter_impots'),
    path('banque/action/<int:id_batiment>/', views.action_banque, name='action_banque'),
    # ...
    path('api/send/<int:id_destinataire>/', views.api_send_message, name='api_send_message'),
    path('api/get/<int:id_destinataire>/', views.api_get_messages, name='api_get_messages'),
    path('batiment/revocquer/<int:id_batiment>/', views.revocquer_directeur, name='revocquer_directeur'),
    path('mairie/doleance/', views.mairie_doleance, name='mairie_doleance'),
    path('mairie/aide_sociale/', views.mairie_aide_sociale, name='mairie_aide_sociale'),
    path('police/plainte/', views.police_deposer_plainte, name='police_deposer_plainte'),
    path('prison/cellule/', views.cellule_prison, name='cellule_prison'),
    path('police/arrestation/', views.arreter_citoyen, name='arreter_citoyen'),
    path('prison/liberer/<int:id_citoyen>/', views.liberer_citoyen, name='liberer_citoyen'),
    path('gestion/casier/<int:id_citoyen>/', views.voir_casier, name='voir_casier'),
    path('logement/expulser/<int:id_citoyen>/', views.expulser_locataire, name='expulser_locataire'),
    path('ecole/action/<int:id_batiment>/', views.action_ecole, name='action_ecole'),
    path('commerce/action/<int:id_batiment>/', views.action_commerce, name='action_commerce'),
    path('usine/action/<int:id_batiment>/', views.action_usine, name='action_usine'),
    path('centrale/action/<int:id_batiment>/', views.action_centrale, name='action_centrale'),
    path('concessionnaire/action/<int:id_batiment>/', views.action_concessionnaire, name='action_concessionnaire'),
    path('parking/action/<int:id_batiment>/', views.action_parking, name='action_parking'),
    path('api/chat/get/<int:id_destinataire>/', views.api_get_messages, name='api_get_messages'),
    path('api/chat/send/<int:id_destinataire>/', views.api_send_message, name='api_send_message'),
    path('api/check/unread/', views.api_check_unread, name='api_check_unread'),
    path('batiment/renommer/<int:id_batiment>/', views.renommer_batiment, name='renommer_batiment'),
    path('place/road/<int:x>/<int:y>/', views.placer_route, name='placer_route'),
    path('delete/road/<int:x>/<int:y>/', views.supprimer_route, name='supprimer_route'),
    path('place/virage/<int:x>/<int:y>/', views.placer_virage, name='placer_virage'),
    path('publier/actu/<int:id_batiment>/', views.publier_actualite, name='publier_actualite'),
    
    # Et celle-ci aussi pour la suppression (qui est aussi dans votre template)
    path('supprimer/actu/<int:id_actu>/', views.supprimer_actualite, name='supprimer_actualite'),
    path('police/action/<int:id_batiment>/', views.action_police, name='action_police'),
    path('police/classer/<int:id_plainte>/', views.classer_plainte, name='classer_plainte'),
    path('hopital/action/<int:id_batiment>/', views.action_hopital, name='action_hopital'),
    path('organiser_fete/', views.organiser_fete, name='organiser_fete'),
    path('organiser_soiree/', views.organiser_soiree, name='organiser_soiree'),
    path('bannir/<int:citoyen_id>/', views.bannir_citoyen, name='bannir_citoyen'),
]