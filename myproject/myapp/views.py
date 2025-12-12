from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Ville, Batiment, Citoyen, User, Candidature, Information, Message, Actualite, Transaction, Casier
from .forms import BatimentForm, CitoyenForm, UpdateCitoyenForm, VilleForm, InformationForm, CitoyenCreationForm, MessageForm, ActualiteForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Sum, Avg
from django.utils import timezone
# --- IMPORTS ESSENTIELS POUR LE TÉLÉPHONE (AJAX) ---
from django.http import JsonResponse
import json
import random
import datetime
from datetime import timedelta

from django.db.models import Q


# Configuration des tailles (Largeur X, Hauteur Y)
BATIMENT_SIZES = {
    'MAIRIE': (7, 7),
    'USINE': (6, 6),
    'HOPITAL': (4, 3),
    'ECOLE': (10, 10),
    'IMMEUBLE': (4, 4), # Tour
    'MAISON': (3, 3),
    'CONCESSIONNAIRE': (5, 5),
    'BANQUE': (4, 4),
    'COMMISSARIAT': (3, 3),
    'COMMERCE': (2, 2),
    'PRISON': (8, 8),
    'CENTRALE': (5, 5),
    'PARKING': (5, 5),
    'ROUTE': (2, 2),
    'ROUTE_VIRAGE': (2, 2), # <--- Même taille
    # Par défaut 1x1 pour le reste
}

# Catalogue des véhicules
CAR_CATALOG = [
    {'id': 'eco', 'nom': 'Citadine Eco', 'prix': 200, 'icon': 'fa-leaf', 'color': 'success', 'desc': 'Petite, pratique et pas chère.'},
    {'id': 'berline', 'nom': 'Berline Familiale', 'prix': 500, 'icon': 'fa-car-side', 'color': 'primary', 'desc': 'Le confort pour toute la famille.'},
    {'id': 'suv', 'nom': '4x4 Baroudeur', 'prix': 1500, 'icon': 'fa-truck-pickup', 'color': 'warning', 'desc': 'Pour dominer la route.'},
    {'id': 'sport', 'nom': 'Supercar GT', 'prix': 5000, 'icon': 'fa-tachometer-alt', 'color': 'danger', 'desc': 'Vitesse et prestige absolu.'},
]
# --- PARTIE PUBLIQUE ---

def landing(request):
    """Page d'accueil publique (Vitrine)"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def signup(request):
    """Inscription d'un nouveau Citoyen"""
    ville = Ville.objects.first() # On récupère la ville pour l'y installer

    if request.method == 'POST':
        # 1. Infos de connexion
        username = request.POST['username']
        password = request.POST['password']
        
        # 2. Infos de Citoyen (Profil)
        prenom = request.POST['prenom']
        nom = request.POST['nom']
        age = request.POST['age']

        # Vérification si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
        else:
            # A. Création du Compte Utilisateur
            user = User.objects.create_user(username=username, password=password)
            
            # B. Création de la Fiche Citoyen liée
            Citoyen.objects.create(
                compte=user,   # Le lien se fait ici !
                ville=ville,
                prenom=prenom,
                nom=nom,
                age=age,
                bonheur=100
            )
            
            # C. Mise à jour de la population
            ville.population_totale += 1
            ville.save()

            # D. Connexion et redirection
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'registration/signup.html')

# --- PARTIE PRIVÉE (JEU) ---


def generer_evenement_aleatoire(ville):
    """Génère un événement aléatoire avec une probabilité"""
    chance = random.randint(1, 100)
    evenement = None

    # 1. INCENDIE (5% de chance)
    if chance <= 5:
        batiment = Batiment.objects.filter(ville=ville).order_by('?').first()
        if batiment:
            degats = random.randint(20, 50)
            batiment.etat -= degats
            if batiment.etat < 0: batiment.etat = 0
            batiment.save()
            evenement = {
                'type': 'danger',
                'icone': 'fa-fire',
                'titre': 'Incendie !',
                'message': f"Le bâtiment <strong>{batiment.nom}</strong> a pris feu ! Dégâts : -{degats}% d'état. Réparez-le vite !"
            }

    # 2. DONATION (10% de chance)
    elif chance <= 15:
        gain = random.randint(1000, 5000)
        ville.budget += gain
        ville.save()
        evenement = {
            'type': 'success',
            'icone': 'fa-hand-holding-usd',
            'titre': 'Donation',
            'message': f"Un investisseur anonyme a offert <strong>{gain} €</strong> à la ville !"
        }

    # 3. PANNE DE COURANT (5% de chance)
    elif chance <= 20:
        perte = random.randint(100, 500)
        ville.energie_stock -= perte
        if ville.energie_stock < 0: ville.energie_stock = 0
        ville.save()
        evenement = {
            'type': 'warning',
            'icone': 'fa-bolt',
            'titre': 'Panne électrique',
            'message': f"Une surtension a grillé <strong>{perte} kWh</strong> de vos réserves."
        }
        
    return evenement


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from .models import Ville, Batiment, Citoyen, Message # Assure-toi que les imports sont là

# Si tu as mis ta fonction 'get_mon_profil' ailleurs, importe-la, 
# sinon laisse-la dans ce fichier avant 'dashboard'

@login_required
def dashboard(request):
    ville = Ville.objects.first()
    
    # 1. On s'assure que le Maire a un profil citoyen
    try:
        moi = request.user.profil_citoyen
    except:
        moi = None

    if moi and getattr(moi, 'est_en_prison', False):
        return redirect('cellule_prison')

    # 2. Gestion des SMS non lus
    nb_sms_non_lus = 0
    if moi:
        nb_sms_non_lus = Message.objects.filter(destinataire=moi, lu=False).count()
    
    # --- LOGIQUE DU SWITCH (Admin vs Citoyen) ---
    mode = request.GET.get('mode', 'admin')

    # CAS 1 : C'est le MAIRE/ADJOINT (Mode Gestion)
    if (request.user.is_superuser or getattr(request.user, 'is_adjoint', False)) and mode != 'citoyen':
        
        # Création de ville par défaut si inexistante
        if not ville:
            ville = Ville.objects.create(nom="Ville Nouvelle")
            Batiment.objects.create(ville=ville, nom="Hôtel de Ville", type_batiment='MAIRIE', cout_construction=0, consommation_energie=5)
        
        # --- CALCUL DES INDICATEURS (KPIs) ---
        citoyens = Citoyen.objects.filter(ville=ville)
        total_pop = citoyens.count()
        
        # On cherche ceux sans travail, en excluant ceux qui s'appellent "Maire" ou "Adjoint"
        candidats_recrutement = citoyens.filter(lieu_travail__isnull=True).exclude(
            Q(nom='Maire') | Q(nom='Adjoint')
        )
        
        nb_chomeurs = candidats_recrutement.count()
        
        # Calcul des pourcentages
        taux_chomage = round((nb_chomeurs / total_pop * 100), 1) if total_pop > 0 else 0
        
        sdf = citoyens.filter(lieu_vie__isnull=True).count()
        taux_sdf = round((sdf / total_pop * 100), 1) if total_pop > 0 else 0
        
        # Stats Santé / Bonheur
        sante_moyenne = citoyens.aggregate(Avg('sante'))['sante__avg'] or 0
        sante_moyenne = round(sante_moyenne, 1)
        bonheur_moyen = citoyens.aggregate(Avg('bonheur'))['bonheur__avg'] or 0
        bonheur_moyen = round(bonheur_moyen, 1)

        # --- LOGIQUE DEPLACEMENT & EVENEMENTS ---
        empty_spots = [] 
        moving_batiment = None 
        evenement_du_jour = None # <--- INITIALISATION ICI
        move_id = request.GET.get('move_id')
        
        if move_id and request.user.is_superuser:
            try:
                moving_batiment = Batiment.objects.get(id=move_id)
                # Calcul des positions occupées
                occupied_coords = set() 
                for b in ville.batiments.all():
                    if b.id != moving_batiment.id:
                        for dx in range(b.largeur):
                            for dy in range(b.hauteur):
                                occupied_coords.add((b.x + dx, b.y + dy))
                
                # Recherche des places libres
                for x in range(ville.largeur_map):
                    for y in range(ville.hauteur_map):
                        is_free = True
                        for dx in range(moving_batiment.largeur):
                            for dy in range(moving_batiment.hauteur):
                                target_x = x + dx
                                target_y = y + dy
                                if target_x >= ville.largeur_map or target_y >= ville.hauteur_map or (target_x, target_y) in occupied_coords:
                                    is_free = False
                                    break
                            if not is_free: break
                        if is_free:
                            empty_spots.append({'x': x, 'y': y})
            except Batiment.DoesNotExist:
                pass
        
        # Si on ne déplace rien, on génère un événement aléatoire
        elif not move_id:
             # evenement_du_jour = generer_evenement_aleatoire(ville) # Décommente si tu as la fonction
             pass 
        
        # =================================================================
        # 🚨 C'EST ICI QU'ON PLACE LA RÉVOLTE (APRÈS TOUT LE RESTE) 🚨
        # =================================================================
        # Elle écrase l'événement aléatoire si la situation est critique
        
        print(f"DEBUG ALERTE: Bonheur={bonheur_moyen}, Pop={total_pop}") # Debug console
        
        if bonheur_moyen < 30 and total_pop > 0:
            print("DEBUG: CA RENTRE DANS LA REVOLTE !!!")
            
            perte_argent = 500 * total_pop
            ville.budget -= perte_argent
            ville.save()
            
            evenement_du_jour = {
                'titre': 'ÉMEUTES EN VILLE ! 🔥',
                'message': f"Le bonheur est catastrophique ({bonheur_moyen}%). Les citoyens cassent tout ! Dégâts : -{perte_argent} €.",
                'type': 'danger', 
                'icone': 'fa-fire'
            }
        # =================================================================


        # 1. GÉNÉRER LA LISTE DES OBSTACLES POUR LE JS
        obstacles_data = []
        if request.user.is_superuser: # Seul le maire a besoin de ça
            for b in ville.batiments.all():
                if moving_batiment and b.id == moving_batiment.id:
                    continue
                    
                obstacles_data.append({
                    'x': b.x,
                    'y': b.y,
                    'w': b.largeur,
                    'h': b.hauteur
                })

        return render(request, 'index.html', {
            'ville': ville,
            'total_pop': total_pop,
            'chomeurs': nb_chomeurs,
            'taux_chomage': taux_chomage,
            'sdf': sdf,
            'taux_sdf': taux_sdf,
            'sante_moyenne': sante_moyenne,
            'bonheur_moyen': bonheur_moyen,
            'nb_sms_non_lus': nb_sms_non_lus,
            'empty_spots': empty_spots,
            'moving_batiment': moving_batiment,
            'evenement': evenement_du_jour,
            'candidats_recrutement': candidats_recrutement,
            'obstacles_json': json.dumps(obstacles_data),
        })
    
    # CAS 2 : C'est un CITOYEN LAMBDA (ou Maire en mode visiteur)
    else:
        try:
            citoyen = request.user.profil_citoyen
            
            all_candidatures = citoyen.candidatures.all().order_by('-id')
            notifications_visibles = []
            
            # Filtre des notifications
            for c in all_candidatures:
                if c.statut == 'REFUSEE' and not c.initiateur_est_citoyen and "SANCTION" not in c.message:
                    continue
                if c.statut == 'DEMISSION': 
                    continue
                notifications_visibles.append(c)
            
            ids_candidatures = list(citoyen.candidatures.filter(statut='EN_ATTENTE').values_list('batiment_id', flat=True))
            
            return render(request, 'dashboard_citoyen.html', {
                'citoyen': citoyen, 
                'ville': ville,
                'ids_candidatures': ids_candidatures,
                'notifications': notifications_visibles,
                'nb_sms_non_lus': nb_sms_non_lus,
            })
        except Exception:
            # Si pas de profil, retour à l'accueil simple
            return render(request, 'index.html', {'ville': ville})
        
@login_required
def construire(request):
    """Construire un bâtiment : Étape 1 (Choix du type) -> Redirection Carte"""
    if not request.user.is_superuser:
        messages.error(request, "Seul le Maire peut construire.")
        return redirect('dashboard')
    
    ville = Ville.objects.first()
    
    # --- DÉFINITION DES COÛTS (DOIT CORRESPONDRE AU HTML) ---
    BATIMENT_COSTS = {
        'MAIRIE': 5000,
        'MAISON': 500,
        'IMMEUBLE': 1500,
        'HOPITAL': 3000,
        'BANQUE': 2500,
        'COMMERCE': 1000,
        'USINE': 4000,
        'ECOLE': 1500,
        'COMMISSARIAT': 3500,
        'CONCESSIONNAIRE': 500,
        'ROUTE': 10,
        'ROUTE_VIRAGE': 10, # <--- Même prix
    }
    
    if request.method == 'POST':
        form = BatimentForm(request.POST)
        if form.is_valid():
            batiment = form.save(commit=False)
            batiment.ville = ville
            
            # 1. Définir la taille
            size = BATIMENT_SIZES.get(batiment.type_batiment, (1, 1))
            batiment.largeur = size[0]
            batiment.hauteur = size[1]
            
            # 2. Définir le COÛT (Correction ici)
            # On prend le prix dans le dictionnaire, sinon 100 par défaut
            batiment.cout_construction = BATIMENT_COSTS.get(batiment.type_batiment, 100)

            if batiment.type_batiment == 'MAISON':
                batiment.capacite = 4
                batiment.loyer = 50 # Loyer maison
            elif batiment.type_batiment == 'IMMEUBLE':
                batiment.capacite = 20
                batiment.loyer = 20 # Loyer appart moins cher

            # Vous pouvez ajouter d'autres capacités ici...
            
            # 4. Vérification Mairie Unique
            if batiment.type_batiment == 'MAIRIE' and Batiment.objects.filter(ville=ville, type_batiment='MAIRIE').exists():
                messages.error(request, "Une seule Mairie autorisée.")
                return render(request, 'construire.html', {'form': form, 'ville': ville})

            # 5. Paiement
            if ville.budget >= batiment.cout_construction:
                ville.budget -= batiment.cout_construction
                ville.save()
                
                # 6. SAUVEGARDE TEMPORAIRE (Hors Map)
                batiment.x = -10
                batiment.y = -10
                batiment.save()
                
                messages.success(request, f"{batiment.nom} créé ! Cliquez sur la carte pour le placer.")
                return redirect(f"{reverse('dashboard')}?move_id={batiment.id}")
            
            else:
                messages.error(request, f"Pas assez d'argent ! Il faut {batiment.cout_construction} €.")
    else:
        form = BatimentForm()

    return render(request, 'construire.html', {'form': form, 'ville': ville})

@login_required
def rejoindre_ville(request):
    """Formulaire d'immigration (S'inscrire en tant que citoyen)"""
    ville = Ville.objects.first()
    
    if request.method == 'POST':
        form = CitoyenForm(request.POST)
        if form.is_valid():
            nouveau_citoyen = form.save(commit=False)
            nouveau_citoyen.ville = ville
            nouveau_citoyen.bonheur = 100
            
            ville.population_totale += 1
            ville.save()
            nouveau_citoyen.save()
            
            messages.success(request, f"{nouveau_citoyen.prenom} a bien rejoint la ville !")
            return redirect('dashboard')
    else:
        form = CitoyenForm()

    return render(request, 'rejoindre.html', {'form': form, 'ville': ville})

@login_required
def batiment_detail(request, id_batiment):
    """Vue de gestion d'un bâtiment (Maire/Directeur) OU de visite (Citoyen/Adjoint)"""
    
    # 1. SÉCURITÉ ET RÉCUPÉRATION
    try:
        batiment = Batiment.objects.get(id=id_batiment)
    except Batiment.DoesNotExist:
        messages.error(request, "Ce bâtiment n'existe plus ou a été détruit.")
        return redirect('dashboard')
    
    ville = batiment.ville
    
    # 2. DÉFINITION DU "MANAGER" (Celui qui a les boutons d'action : Recruter, Produire, Virer)
    # IMPORTANT : L'Adjoint n'est PAS manager par défaut (sauf s'il est aussi le directeur nommé).
    # 2. DROITS D'ADMINISTRATION
    is_manager = False
    
    # CORRECTIF : L'Adjoint est maintenant MANAGER PARTOUT (Héritage de Directeur)
    # Il a les mêmes droits que le Maire ou le Responsable attitré
    if request.user.is_superuser or request.user.is_adjoint or request.user == batiment.responsable:
        is_manager = True

    # Récupération profil citoyen (si existe)
    moi = None
    try:
        moi = request.user.profil_citoyen
    except:
        pass

    # 3. DROIT DE VOIR LE STAFF (Inspection)
    # Visible si : Admin OU Directeur OU Employé OU ADJOINT (Droit de regard sur la ville)
    can_see_staff = False
    if is_manager or request.user.is_adjoint: # L'Adjoint peut VOIR, mais pas TOUCHER
        can_see_staff = True
    elif moi and moi.lieu_travail == batiment:
        can_see_staff = True

    # 4. DONNÉES COMMUNES
    # On ne montre que les "vrais" joueurs (avec compte)
    employes = batiment.employes.filter(compte__isnull=False)
    
    # --- FILTRE CHÔMEURS (CORRECTIF MAIRE/ADJOINT) ---
    # On récupère les IDs des utilisateurs admins/adjoints pour les exclure
    admin_users = User.objects.filter(Q(is_superuser=True) | Q(is_adjoint=True))

    # On filtre les citoyens sans emploi MAIS qui n'ont PAS un compte admin
    chomeurs = Citoyen.objects.filter(
        ville=ville,
        lieu_travail__isnull=True
    ).exclude(
        compte__in=admin_users # Force l'exclusion des Admins/Adjoints de la liste d'embauche
    )
    
    # 5. CANDIDATURES REÇUES (Seul le vrai Manager peut les traiter)
    candidatures_recues = []
    if is_manager:
        candidatures_recues = Candidature.objects.filter(
            batiment=batiment,
            statut='EN_ATTENTE',
            initiateur_est_citoyen=True # C'est le citoyen qui demande
        ).order_by('-date_creation')

    # 6. COMPTEUR DE SMS
    nb_sms_non_lus = 0
    if moi:
        nb_sms_non_lus = Message.objects.filter(destinataire=moi, lu=False).count()

    # --- LOGIQUES SPÉCIFIQUES PAR TYPE DE BÂTIMENT ---
    transactions = []
    destinataires_possibles = []
    doleances = []
    nom_maire = "Non Élu"
    nom_adjoint = "Aucun"
    plaintes = []
    citoyens_list = []
    detenus = []
    malades = []
    taux_motorisation = 0
    nb_voitures = 0
    notes_service = Actualite.objects.filter(batiment=batiment).order_by('-date_creation')
    # On instancie le formulaire pour l'afficher dans le HTML
    from .forms import ActualiteForm # Assurez-vous que l'import est là
    form_note = ActualiteForm()

    # A. BANQUE
    if batiment.type_batiment == 'BANQUE' and moi:
        transactions = Transaction.objects.filter(
            Q(expediteur=moi) | Q(destinataire=moi)
        ).order_by('-date')[:10] 
        destinataires_possibles = Citoyen.objects.filter(ville=ville, compte__isnull=False).exclude(id=moi.id)

    # B. MAIRIE
    elif batiment.type_batiment == 'MAIRIE':
        if is_manager: # Seul le Maire voit les doléances (pas l'adjoint par défaut ici sauf si tu veux)
            doleances = Candidature.objects.filter(batiment=batiment, statut='DOLEANCE').order_by('-date_creation')
        
        maire_user = User.objects.filter(is_superuser=True).first()
        if maire_user:
            try:
                p = maire_user.profil_citoyen
                nom_maire = f"{p.prenom} {p.nom}"
            except:
                nom_maire = maire_user.username

        adjoint_user = User.objects.filter(is_adjoint=True).first()
        if adjoint_user:
            try:
                p = adjoint_user.profil_citoyen
                nom_adjoint = f"{p.prenom} {p.nom}"
            except:
                nom_adjoint = adjoint_user.username

    # C. COMMISSARIAT
    elif batiment.type_batiment == 'COMMISSARIAT':
        # Liste pour le menu déroulant (tout le monde sauf moi)
        if moi:
            citoyens_list = Citoyen.objects.filter(ville=ville, compte__isnull=False).exclude(id=moi.id).order_by('nom')
        
        # Liste des plaintes (Visible seulement par la Police/Maire)
        if is_manager:
            plaintes = Candidature.objects.filter(batiment=batiment, statut='PLAINTE').order_by('-date_creation')

    # D. PRISON
    elif batiment.type_batiment == 'PRISON':
        # On récupère juste les détenus, sans bloquer l'accès
        detenus = Citoyen.objects.filter(ville=ville, est_en_prison=True, compte__isnull=False).order_by('date_liberation')

    # E. HOPITAL
    elif batiment.type_batiment == 'HOPITAL':
        # Visible par Manager ou Employés
        if is_manager or (moi and moi.lieu_travail == batiment):
            malades = Citoyen.objects.filter(ville=ville, sante__lt=100, compte__isnull=False).order_by('sante')

    # F. CONCESSIONNAIRE
    elif batiment.type_batiment == 'CONCESSIONNAIRE':
        if is_manager:
            nb_voitures = Citoyen.objects.filter(ville=ville, vehicule=True).count()
            pop_totale = ville.population_totale
            if pop_totale > 0:
                taux_motorisation = int((nb_voitures / pop_totale) * 100)
            else:
                taux_motorisation = 0
    
    # G. PARKING
    elif batiment.type_batiment == 'PARKING':
        nb_voitures = Citoyen.objects.filter(ville=ville, vehicule=True).count()

    return render(request, 'batiment_detail.html', {
        'batiment': batiment,
        'employes': employes,
        'chomeurs': chomeurs,
        'is_manager': is_manager,       # FALSE pour l'Adjoint (Cache les boutons d'action)
        'can_see_staff': can_see_staff, # TRUE pour l'Adjoint (Voit la liste)
        'candidatures_recues': candidatures_recues,
        'nb_sms_non_lus': nb_sms_non_lus,
        
        'transactions': transactions,
        'destinataires': destinataires_possibles,
        'doleances': doleances,
        'nom_maire': nom_maire,
        'nom_adjoint': nom_adjoint,
        'plaintes': plaintes,
        'citoyens_list': citoyens_list,
        'detenus': detenus,
        'malades': malades,
        'taux_motorisation': taux_motorisation,
        'car_catalog': CAR_CATALOG,
        'nb_voitures': nb_voitures,
        'notes_service': notes_service,  # <--- AJOUT CRUCIAL
        'form_note': form_note,          # <--- POUR LE FORMULAIRE
    })
# --- LOGIQUE DE RECRUTEMENT ---

@login_required
def proposer_poste(request, id_batiment):
    """Gère les dépôts de plainte avec accusation précise"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    if request.method == 'POST':
        type_demande = request.POST.get('type_demande', 'OFFRE')
        message = request.POST.get('message', '')
        
        # --- CAS PLAINTE ---
        if type_demande == 'PLAINTE':
            try:
                citoyen_cible = request.user.profil_citoyen
                
                # 1. RÉCUPÉRATION DE L'ACCUSÉ (Nouveau)
                accuse_id = request.POST.get('accuse_id')
                sanction_souhaitee = request.POST.get('sanction_souhaitee', '')
                
                # On enrichit le message avec les infos techniques pour la police
                info_accuse = ""
                if accuse_id:
                    try:
                        accuse = Citoyen.objects.get(id=accuse_id)
                        # On met un tag spécial [ID:12] pour pouvoir retrouver le citoyen automatiquement plus tard si besoin
                        info_accuse = f"\n[ACCUSÉ: {accuse.prenom} {accuse.nom} (ID:{accuse.id})]"
                    except:
                        pass
                
                full_message = f"{message}{info_accuse}\n[DEMANDE: {sanction_souhaitee}]"

            except:
                messages.error(request, "Erreur de profil.")
                return redirect('batiment_detail', id_batiment=batiment.id)
            
            # Création de la plainte
            Candidature.objects.create(
                batiment=batiment,
                citoyen=citoyen_cible,
                message=full_message, # Le message contient maintenant le nom du coupable
                statut='PLAINTE',
                initiateur_est_citoyen=True
            )
            messages.success(request, "Plainte enregistrée.")

        # --- CAS OFFRE EMPLOI (Reste inchangé) ---
        else:
            # ... (Garde ton code existant pour l'embauche ici) ...
            pass # (Je ne le remets pas pour raccourcir, mais ne l'efface pas !)

    return redirect('batiment_detail', id_batiment=batiment.id)

@login_required
def postuler(request, id_batiment):
    """Le Citoyen postule à une offre"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    # Attention : Il faut bien vérifier que c'est une méthode POST
    if request.method == 'POST':
        # 1. RÉCUPÉRATION DU MESSAGE
        message = request.POST.get('message')
        
        try:
            citoyen = request.user.profil_citoyen
            
            # Vérification doublon
            if Candidature.objects.filter(citoyen=citoyen, batiment=batiment, statut='EN_ATTENTE').exists():
                messages.warning(request, "Patience ! Vous avez déjà une candidature en cours ici.")
            else:
                Candidature.objects.create(
                    citoyen=citoyen,
                    batiment=batiment,
                    initiateur_est_citoyen=True,
                    message=message # 2. ENREGISTREMENT DU MESSAGE
                )
                messages.success(request, f"Candidature envoyée pour {batiment.nom} !")
        except:
            messages.error(request, "Erreur d'identification citoyen.")
            
    base_url = reverse('dashboard')
    return redirect(f"{base_url}?tab=market")

@login_required
def traiter_candidature(request, id_candidature, decision):
    """Valider ou Refuser une demande (Utilisé par les deux camps)"""
    candidature = get_object_or_404(Candidature, id=id_candidature)
    
    if decision == 'accepter':
        candidature.statut = 'ACCEPTEE'
        # ACTION RÉELLE : On met à jour le travail du citoyen !
        citoyen = candidature.citoyen
        citoyen.lieu_travail = candidature.batiment
        citoyen.save()
        messages.success(request, "Félicitations ! Le contrat est signé.")
        
    elif decision == 'refuser':
        candidature.statut = 'REFUSEE'
        messages.warning(request, "La proposition a été déclinée.")
    
    candidature.save()
    
    # Redirection intelligente (si c'est le maire ou le citoyen)
    if request.user.is_superuser:
        return redirect('batiment_detail', id_batiment=candidature.batiment.id)
    else:
        return redirect('dashboard')
    
from django.http import JsonResponse # Assurez-vous d'avoir cet import

@login_required
def supprimer_notification(request, id_candidature):
    """Supprime une notification (Compatible AJAX)"""
    # Note : Adaptez 'Candidature' si votre modèle de notif s'appelle autrement
    notif = get_object_or_404(Candidature, id=id_candidature)
    
    # Vérification de sécurité (C'est bien ma notif ?)
    if request.user.profil_citoyen == notif.citoyen or request.user.is_superuser:
        notif.delete()
        
        # Si c'est une requête AJAX (JS), on répond en JSON sans recharger
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})
            
    return redirect('dashboard')

@login_required
def supprimer_toutes_notifications(request):
    """Supprime toutes les notifs, SAUF les offres d'emploi actives"""
    citoyen = request.user.profil_citoyen
    
    # 1. On récupère toutes les notifications du citoyen
    toutes_notifs = Candidature.objects.filter(citoyen=citoyen)
    
    # 2. On exclut SEULEMENT les "Offres d'emploi en attente" (celles qu'on doit traiter)
    #    C'est-à-dire : Statut EN_ATTENTE ET initié par l'entreprise (pas par moi)
    a_supprimer = toutes_notifs.exclude(
        statut='EN_ATTENTE',
        initiateur_est_citoyen=False 
    )
    
    # 3. On supprime le reste (Infos, Licenciements, Virements, Refus, etc.)
    nb_suppr, _ = a_supprimer.delete()
    
    if nb_suppr > 0:
        messages.success(request, "Toutes les notifications ont été effacées.")
    else:
        messages.info(request, "Aucune notification archivée à supprimer.")
        
    return redirect('dashboard')


@login_required
def licencier(request, id_citoyen):
    """Le Directeur/Maire vire un employé"""
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    batiment = citoyen.lieu_travail
    
    if request.method == 'POST':
        message = request.POST.get('message')
        
        if batiment and (request.user.is_superuser or request.user.is_directeur):
            
            # Création notif
            Candidature.objects.create(
                citoyen=citoyen,
                batiment=batiment,
                statut='VIRE',
                initiateur_est_citoyen=False,
                message=message
            )
            
            # --- NOUVEAU : SI ON VIRE LE DIRECTEUR ---
            user_compte = citoyen.compte
            if user_compte and batiment.responsable == user_compte:
                batiment.responsable = None
                batiment.save()
                
                user_compte.is_directeur = False
                user_compte.save()
            # -----------------------------------------

            citoyen.lieu_travail = None
            citoyen.bonheur -= 20
            citoyen.save()
            
            messages.warning(request, f"{citoyen.prenom} a été licencié.")
            return redirect('batiment_detail', id_batiment=batiment.id)
    
    return redirect('dashboard')

@login_required
def demissionner(request):
    """Le Citoyen quitte son emploi"""
    if request.method == 'POST':
        message = request.POST.get('message')
        try:
            citoyen = request.user.profil_citoyen
            batiment = citoyen.lieu_travail
            
            if batiment:
                # Création de la notif pour le Maire/RH
                Candidature.objects.create(
                    citoyen=citoyen,
                    batiment=batiment,
                    statut='DEMISSION',
                    initiateur_est_citoyen=True,
                    message=message
                )
                
                # --- NOUVEAU : GESTION DU DIRECTEUR DÉMISSIONNAIRE ---
                # Si le citoyen était le responsable de ce bâtiment
                if batiment.responsable == request.user:
                    batiment.responsable = None
                    batiment.save()
                    
                    request.user.is_directeur = False
                    request.user.save()
                    messages.warning(request, "Vous avez abandonné votre poste de Direction.")
                # -----------------------------------------------------

                citoyen.lieu_travail = None
                citoyen.save()
                
                if not batiment.responsable: # Message standard si pas directeur
                     messages.info(request, "Vous avez démissionné.")
                     
        except:
            messages.error(request, "Erreur lors de la démission.")
            
    return redirect('dashboard')

@login_required
def detruire_batiment(request, id_batiment):
    """Action critique : Démolition d'une infrastructure"""
    if not request.user.is_superuser:
        messages.error(request, "Action non autorisée.")
        return redirect('dashboard')

    batiment = get_object_or_404(Batiment, id=id_batiment)
    nom_bat = batiment.nom # On garde le nom en mémoire pour le message
    
    # 1. Gestion des employés : On envoie une notif et on vire
    employes = batiment.employes.all()
    for citoyen in employes:
        # Création de la notification "VIRE" avec motif spécial
        Candidature.objects.create(
            citoyen=citoyen,
            batiment=batiment, # Il existe encore à cet instant
            statut='VIRE',
            initiateur_est_citoyen=False,
            message=f"Le bâtiment '{nom_bat}' a été définitivement démoli sur ordre du Maire."
        )
        
        # Mise à jour du statut citoyen
        citoyen.lieu_travail = None
        citoyen.bonheur -= 30
        citoyen.save()

    # 2. Destruction
    batiment.delete() # Maintenant on peut détruire, les notifs resteront (avec batiment=None)
    
    messages.success(request, f"Le bâtiment '{nom_bat}' a été démoli avec succès.")
    return redirect('dashboard')

@login_required
def emmenager(request, id_batiment):
    """Le Citoyen s'installe dans un logement"""
    try:
        citoyen = request.user.profil_citoyen
        batiment = get_object_or_404(Batiment, id=id_batiment)
        
        # Vérifications
        if not batiment.est_logement:
            messages.error(request, "Ce n'est pas une habitation !")
        elif batiment.places_disponibles <= 0:
            messages.error(request, "Complet !")
        
        # NOUVEAU : Vérification Argent
        elif citoyen.argent < batiment.loyer:
            messages.error(request, f"Fonds insuffisants. Loyer : {batiment.loyer} €.")
            
        else:
            # PAIEMENT 1er MOIS (Caution)
            citoyen.argent -= batiment.loyer
            batiment.ville.budget += batiment.loyer
            
            # Action
            citoyen.lieu_vie = batiment
            citoyen.bonheur += 10 
            
            # 👇 NOUVEAU : On fixe le prochain loyer dans 24 heures (1 jour)
            citoyen.prochain_loyer = timezone.now() + timedelta(days=1)
            
            batiment.ville.save()
            citoyen.save()
            messages.success(request, f"Bienvenue ! Loyer payé. Prochain prélèvement le {citoyen.prochain_loyer.strftime('%d/%m à %H:%M')}.")
    except:
        messages.error(request, "Erreur profil.")
        
    return redirect('dashboard') # Ou batiment_detail

@login_required
def demenager(request):
    """Le Citoyen quitte son logement"""
    try:
        citoyen = request.user.profil_citoyen
        if citoyen.lieu_vie:
            ancien_domicile = citoyen.lieu_vie.nom
            citoyen.lieu_vie = None
            citoyen.bonheur -= 5
            citoyen.save()
            messages.info(request, f"Vous avez quitté {ancien_domicile}.")
    except:
        pass
        
    base_url = reverse('dashboard')
    return redirect(f"{base_url}?tab=housing")

@login_required
def mon_profil(request):
    """Page de gestion du profil citoyen"""
    try:
        citoyen = request.user.profil_citoyen
    except:
        return redirect('dashboard') # Sécurité si c'est le maire

    if request.method == 'POST':
        form = UpdateCitoyenForm(request.POST, instance=citoyen)
        if form.is_valid():
            # 1. Sauvegarde des infos Citoyen (Nom, Age...)
            form.save()
            
            # 2. Sauvegarde de l'Email (sur le modèle User)
            new_email = form.cleaned_data['email']
            request.user.email = new_email
            request.user.save()
            
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('mon_profil')
    else:
        # On pré-remplit le formulaire avec les infos actuelles
        form = UpdateCitoyenForm(instance=citoyen, initial={'email': request.user.email})

    return render(request, 'profil.html', {'form': form, 'citoyen': citoyen})


@login_required
def parametres_ville(request):
    """Gestion des paramètres globaux de la ville (Maire)"""
    # Seul le Maire ou Adjoint peut toucher à ça
    if not (request.user.is_superuser or request.user.is_adjoint):
        messages.error(request, "Accès réservé à l'administration.")
        return redirect('dashboard')
    
    # On récupère la ville (on suppose qu'il n'y en a qu'une ou liée au user)
    # Adaptez selon votre modèle, ici je prends la première trouvée
    ville = Ville.objects.first() 
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # CHANGEMENT DES DIMENSIONS
        if action == 'redimensionner':
            try:
                largeur = int(request.POST.get('largeur', 20))
                hauteur = int(request.POST.get('hauteur', 20))
                
                # --- NOUVELLE LIMITE : 100 ---
                if largeur < 10 or hauteur < 10:
                    messages.error(request, "La ville doit faire au moins 10x10.")
                elif largeur > 100 or hauteur > 100:
                    messages.error(request, "Taille maximum limitée à 100x100 pour les performances.")
                else:
                    ville.largeur_map = largeur
                    ville.hauteur_map = hauteur
                    ville.save()
                    messages.success(request, f"La carte a été redimensionnée en {largeur}x{hauteur}.")
            except ValueError:
                messages.error(request, "Valeurs invalides.")
        
        # (Vos autres actions de paramètres ici, ex: renommer ville...)
        elif action == 'renommer':
            nom = request.POST.get('nom')
            if nom:
                ville.nom = nom
                ville.save()
                messages.success(request, "Ville renommée avec succès.")

        return redirect('parametres_ville')

    return render(request, 'parametres_ville.html', {'ville': ville})

@login_required
def supprimer_info(request, id_info):
    """Supprimer une information"""
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    info = get_object_or_404(Information, id=id_info)
    info.delete()
    messages.info(request, "Information supprimée.")
    return redirect('parametres_ville')


# 1. LISTE / CONSULTER
# myapp/views.py
@login_required
def gestion_citoyens(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    # C'est cette variable 'citoyens' qui est utilisée dans le template
    citoyens = Citoyen.objects.all().order_by('-id')
    
    return render(request, 'gestion_citoyens.html', {'citoyens': citoyens})

# 2. CRÉER / INSCRIRE
@login_required
def ajouter_citoyen(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    ville = Ville.objects.first()
    
    if request.method == 'POST':
        form = CitoyenCreationForm(request.POST)
        if form.is_valid():
            # A. Créer le User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            
            # B. Créer le Citoyen lié
            citoyen = form.save(commit=False)
            citoyen.compte = user
            citoyen.ville = ville
            citoyen.bonheur = 100
            citoyen.save()
            
            # C. Stats ville
            ville.population_totale += 1
            ville.save()
            
            messages.success(request, f"Le citoyen {citoyen.prenom} {citoyen.nom} a été inscrit avec succès.")
            return redirect('gestion_citoyens')
    else:
        form = CitoyenCreationForm()
        
    return render(request, 'form_citoyen_admin.html', {'form': form, 'titre': 'Inscrire un habitant'})

# 3. MODIFIER
@login_required
def modifier_citoyen_admin(request, id_citoyen):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    
    if request.method == 'POST':
        # On réutilise UpdateCitoyenForm qu'on avait fait pour le profil (prénom, nom, age, email)
        form = UpdateCitoyenForm(request.POST, instance=citoyen)
        if form.is_valid():
            form.save()
            # Update email user if needed
            if citoyen.compte:
                citoyen.compte.email = form.cleaned_data['email']
                citoyen.compte.save()
                
            messages.success(request, "Informations mises à jour.")
            return redirect('gestion_citoyens')
    else:
        # Pré-remplir
        initial_data = {}
        if citoyen.compte:
            initial_data['email'] = citoyen.compte.email
        form = UpdateCitoyenForm(instance=citoyen, initial=initial_data)
        
    return render(request, 'form_citoyen_admin.html', {'form': form, 'titre': f'Modifier {citoyen.prenom}'})

# 4. SUPPRIMER
@login_required
def supprimer_citoyen_admin(request, id_citoyen):
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    nom_complet = f"{citoyen.prenom} {citoyen.nom}"
    
    # Suppression du compte User lié (Cascade supprimera peut-être le citoyen selon tes settings, 
    # mais on assure le coup en supprimant le User car c'est le plus important pour la connexion)
    if citoyen.compte:
        citoyen.compte.delete() # Supprime le User ET le Citoyen (si on_delete=CASCADE sur Citoyen -> User)
        # Note: Dans notre modèle actuel, on a mis on_delete=SET_NULL sur Citoyen.compte.
        # Donc supprimer le User ne supprime PAS le Citoyen, ça le rend juste "orphelin" (IA).
        # Si tu veux tout supprimer :
        citoyen.delete()
    else:
        citoyen.delete()
        
    # Mise à jour population
    ville = Ville.objects.first()
    ville.population_totale -= 1
    ville.save()
    
    messages.warning(request, f"{nom_complet} a été banni de la ville.")
    return redirect('gestion_citoyens')

@login_required
def nommer_directeur(request, id_batiment):
    """Le Maire nomme un directeur (et vire l'ancien s'il existe)"""
    if not request.user.is_superuser:
        messages.error(request, "Seul le Maire peut nommer un directeur.")
        return redirect('dashboard')
        
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    if request.method == 'POST':
        citoyen_id = request.POST.get('citoyen_id')
        nouveau_directeur = Citoyen.objects.get(id=citoyen_id)
        nouv_user_account = nouveau_directeur.compte
        
        if nouv_user_account:
            # --- NOUVELLE SÉCURITÉ : UN SEUL MANDAT ---
            # On vérifie si ce user est déjà responsable d'un AUTRE bâtiment
            autre_mandat = Batiment.objects.filter(responsable=nouv_user_account).exclude(id=batiment.id).first()
            
            if autre_mandat:
                messages.error(request, f"Impossible ! {nouveau_directeur.prenom} dirige déjà '{autre_mandat.nom}'. Il doit quitter ce poste d'abord.")
                return redirect('batiment_detail', id_batiment=batiment.id)
            # ------------------------------------------

            # GESTION DE L'ANCIEN DIRECTEUR (inchangé)
            ancien_user = batiment.responsable
            if ancien_user and ancien_user != nouv_user_account:
                try:
                    ancien_citoyen = ancien_user.profil_citoyen
                    Candidature.objects.create(
                        citoyen=ancien_citoyen,
                        batiment=batiment,
                        statut='VIRE',
                        initiateur_est_citoyen=False,
                        message=f"Vous avez été relevé de vos fonctions de Directeur au profit de {nouveau_directeur.prenom} {nouveau_directeur.nom}."
                    )
                    
                    ancien_user.is_directeur = False
                    ancien_user.save()
                    ancien_citoyen.lieu_travail = None
                    ancien_citoyen.bonheur -= 30
                    ancien_citoyen.save()
                except:
                    pass

            # NOMINATION (inchangé)
            nouv_user_account.is_directeur = True
            nouv_user_account.save()
            batiment.responsable = nouv_user_account
            batiment.save()
            nouveau_directeur.lieu_travail = batiment
            nouveau_directeur.save()
            
            messages.success(request, f"Changement de direction effectué : {nouveau_directeur.prenom} est aux commandes !")
        else:
            messages.error(request, "Ce citoyen n'a pas de compte utilisateur.")
            
    return redirect('batiment_detail', id_batiment=batiment.id)

@login_required
def revocquer_directeur(request, id_batiment):
    """Le Maire retire le titre de directeur (rétrogradation en simple employé)"""
    if not request.user.is_superuser:
        messages.error(request, "Seul le Maire peut révoquer un directeur.")
        return redirect('dashboard')
        
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ancien_boss = batiment.responsable
    
    if ancien_boss:
        # 1. On retire le statut 'is_directeur' du compte utilisateur
        ancien_boss.is_directeur = False
        ancien_boss.save()
        
        # 2. On retire le responsable du bâtiment
        batiment.responsable = None
        batiment.save()
        
        # 3. Feedback
        try:
            nom = ancien_boss.profil_citoyen.prenom
            messages.warning(request, f"{nom} n'est plus directeur, mais reste employé.")
        except:
            messages.warning(request, "Le directeur a été révoqué.")
            
    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def promouvoir_adjoint(request, id_citoyen):
    """Le Maire nomme un Adjoint (ou le destitue)"""
    if not request.user.is_superuser:
        messages.error(request, "Seul le Maire peut nommer un adjoint.")
        return redirect('dashboard')
        
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    user = citoyen.compte
    
    if user:
        # On inverse le statut (S'il est adjoint, il ne l'est plus, et vice-versa)
        user.is_adjoint = not user.is_adjoint
        user.save()
        
        statut = "Adjoint" if user.is_adjoint else "Citoyen"
        messages.success(request, f"{citoyen.prenom} est maintenant {statut}.")
    else:
        messages.error(request, "Ce citoyen n'a pas de compte, impossible de le promouvoir.")
        
    return redirect('gestion_citoyens')


@login_required
def reparer_batiment(request, id_batiment):
    """Réparer un bâtiment (Maire ou Adjoint)"""
    
    # SÉCURITÉ : L'Adjoint est AUTORISÉ ici (Maintenance de la ville)
    if not (request.user.is_superuser or request.user.is_adjoint):
        messages.error(request, "Vous n'avez pas les droits de maintenance.")
        return redirect('dashboard')

    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    
    # Calcul du coût (Ex: 10% du prix de construction pour remettre à neuf)
    cout_reparation = int(batiment.cout_construction * 0.1)
    
    if batiment.etat >= 100:
        messages.info(request, "Ce bâtiment est déjà en parfait état.")
    elif ville.budget >= cout_reparation:
        # On paye et on répare
        ville.budget -= cout_reparation
        batiment.etat = 100
        
        ville.save()
        batiment.save()
        messages.success(request, f"{batiment.nom} a été réparé pour {cout_reparation} €.")
    else:
        messages.error(request, f"Pas assez d'argent ! Il faut {cout_reparation} €.")
        
    return redirect('batiment_detail', id_batiment=batiment.id)

# Ajoute Actualite et ActualiteForm dans les imports

@login_required
def publier_actualite(request, id_batiment=0):
    """
    Si id_batiment == 0 : C'est une News Ville (Maire/Adjoint)
    Si id_batiment > 0  : C'est une Note de Service (Directeur)
    """
    ville = Ville.objects.first()
    
    # Cas 1 : Note Interne (Liée à un bâtiment spécifique)
    if id_batiment > 0:
        batiment = get_object_or_404(Batiment, id=id_batiment)
        # On AJOUTE request.user.is_adjoint
        if not (request.user.is_superuser or request.user.is_adjoint or request.user == batiment.responsable):
            messages.error(request, "Accès refusé.")
            return redirect('batiment_detail', id_batiment=batiment.id)
            
        target_batiment = batiment
        redirect_url = 'batiment_detail'
        redirect_args = {'id_batiment': batiment.id}
        
    # Cas 2 : News Publique (Ville entière)
    else:
        # SÉCURITÉ : Maire ou Adjoint (C'est leur rôle d'informer la ville)
        if not (request.user.is_superuser or request.user.is_adjoint):
            messages.error(request, "Droit insuffisant.")
            return redirect('dashboard')
            
        target_batiment = None
        redirect_url = 'dashboard'
        redirect_args = {}

    # Traitement du formulaire
    if request.method == 'POST':
        form = ActualiteForm(request.POST)
        if form.is_valid():
            actu = form.save(commit=False)
            actu.ville = ville
            actu.auteur = request.user
            actu.batiment = target_batiment # Sera None si public
            actu.save()
            messages.success(request, "Message publié avec succès !")
            
    return redirect(redirect_url, **redirect_args)

@login_required
def supprimer_actualite(request, id_actu):
    actu = get_object_or_404(Actualite, id=id_actu)
    
    # On vérifie si l'utilisateur a le droit de supprimer
    can_delete = False
    redirect_url = 'dashboard'
    redirect_args = {}

    # Si c'est le Maire, il peut tout supprimer
    if request.user.is_superuser:
        can_delete = True
    # Si c'est l'auteur (Adjoint ou Directeur)
    elif request.user == actu.auteur:
        can_delete = True
        
    if actu.batiment:
        redirect_url = 'batiment_detail'
        redirect_args = {'id_batiment': actu.batiment.id}

    if can_delete:
        actu.delete()
        messages.info(request, "Message supprimé.")
    
    return redirect(redirect_url, **redirect_args)

@login_required
def verser_salaires(request):
    """Le Maire paye les salaires, collecte loyers/parking et notifie tout le monde"""
    
    if not request.user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')
        
    ville = Ville.objects.first()
    mairie = Batiment.objects.filter(ville=ville, type_batiment='MAIRIE').first()
    
    # On vérifie UNE SEULE FOIS si un hôpital est actif (pour optimiser)
    hopital_actif = Batiment.objects.filter(ville=ville, type_batiment='HOPITAL').exists()
    
    # --- 1. SYSTÈME DE LOGS ---
    bilans_citoyens = {}

    def ajouter_ligne(citoyen, texte):
        if citoyen.id not in bilans_citoyens:
            bilans_citoyens[citoyen.id] = {'obj': citoyen, 'lignes': []}
        bilans_citoyens[citoyen.id]['lignes'].append(texte)

    # =================================================
    # 2. SALAIRES
    # =================================================
    travailleurs = Citoyen.objects.filter(ville=ville, lieu_travail__isnull=False)
    total_salaires = 0
    
    for c in travailleurs:
        salaire_net = 100
        details_grade = "Employé"
        
        if c.compte:
            if getattr(c.compte, 'is_directeur', False):
                salaire_net = 250
                details_grade = "Directeur"
            if getattr(c.compte, 'is_adjoint', False):
                salaire_net += 50
                details_grade += " + Adjoint"
        
        if ville.budget >= salaire_net:
            ville.budget -= salaire_net
            c.argent += salaire_net
            total_salaires += salaire_net
            ajouter_ligne(c, f"💰 Salaire ({details_grade}) : +{salaire_net} €")
    
    # =================================================
    # 3. ALLOCATION CHÔMAGE (RSA)
    # =================================================
    chomeurs = Citoyen.objects.filter(
        ville=ville, 
        lieu_travail__isnull=True,
        est_en_prison=False
    ).exclude(Q(nom='Maire') | Q(nom='Adjoint'))
    
    total_rsa = 0
    alloc_rsa = 40
    
    for c in chomeurs:
        if ville.budget >= alloc_rsa:
            ville.budget -= alloc_rsa
            c.argent += alloc_rsa
            total_rsa += alloc_rsa
            ajouter_ligne(c, f"🛡️ Aide Sociale (RSA) : +{alloc_rsa} €")

    # =================================================
    # 4. COLLECTE DES LOYERS
    # =================================================
    locataires = Citoyen.objects.filter(ville=ville, lieu_vie__isnull=False)
    total_loyers = 0
    now = timezone.now()
    
    for l in locataires:
        loyer = getattr(l.lieu_vie, 'loyer', 50)
        
        if l.argent >= loyer:
            l.argent -= loyer
            total_loyers += loyer
            l.prochain_loyer = now + timedelta(days=1)
            ajouter_ligne(l, f"🏠 Loyer ({l.lieu_vie.nom}) : -{loyer} €")
        else:
            nom_logement = l.lieu_vie.nom
            batiment_logement = l.lieu_vie
            l.lieu_vie = None
            l.prochain_loyer = None
            l.bonheur -= 20 
            
            Candidature.objects.create(
                citoyen=l,
                batiment=batiment_logement,
                statut='VIRE',
                initiateur_est_citoyen=False,
                message=f"🚫 EXPULSION IMMÉDIATE\nLoyer impayé de {loyer} €."
            )
            ajouter_ligne(l, f"⚠️ EXPULSÉ de {nom_logement} (Impayé)")

    # =================================================
    # 5. COLLECTE PARKING
    # =================================================
    total_parking = 0
    parking = Batiment.objects.filter(ville=ville, type_batiment='PARKING').first()
    
    if parking:
        tarif = getattr(parking, 'production_argent', 10)
        automobilistes = Citoyen.objects.filter(ville=ville, vehicule=True)
        
        for auto in automobilistes:
            if auto.argent >= tarif:
                auto.argent -= tarif
                total_parking += tarif
                ajouter_ligne(auto, f"🅿️ Stationnement : -{tarif} €")
            else:
                auto.bonheur -= 2
                ajouter_ligne(auto, f"⚠️ Impayé Parking (Amende morale)")

    ville.budget += total_loyers + total_parking
    ville.save()

    # =================================================
    # 6. TEMPS, SANTÉ & BONHEUR (Cycle de vie)
    # =================================================
    all_citoyens = Citoyen.objects.filter(ville=ville)
    
    for c in all_citoyens:
        
        # --- A. SANTÉ DYNAMIQUE (Nouveau !) ---
        variation_sante = -5 # Fatigue naturelle de base
        
        # S'il y a un hôpital en ville, on compense la fatigue (+6)
        # Résultat net : +1 (légère guérison)
        if hopital_actif:
            variation_sante += 6
            
        # Si on dort dans un lit, on récupère mieux (+2)
        if c.lieu_vie:
            variation_sante += 2
        else:
            # Si on dort dehors (SDF), on tombe malade (-2)
            variation_sante -= 2
            
        # Accident aléatoire (5% de chance) -> Gros coup dur
        if random.randint(1, 20) == 1:
            variation_sante -= 10
            ajouter_ligne(c, "📉 Accident / Maladie : -10 Santé")
            
        c.sante += variation_sante

        # --- B. BONHEUR PASSIF (Stabilité) ---
        gain_bonheur = 0
        if c.lieu_travail: gain_bonheur += 1
        if c.lieu_vie: gain_bonheur += 2
        if not c.lieu_vie and not c.lieu_travail: gain_bonheur -= 2
            
        c.bonheur += gain_bonheur
        
        # C. SAUVEGARDE (Le modèle gère le blocage 0-100)
        c.save()

    # =================================================
    # 7. ENVOI DES NOTIFICATIONS
    # =================================================
    for citoyen_id, data in bilans_citoyens.items():
        citoyen = data['obj']
        lignes = data['lignes']
        
        if lignes: 
            citoyen.refresh_from_db()
            message_final = "📅 BILAN QUOTIDIEN\n" + "\n".join(lignes)
            message_final += f"\n\nNouveau Solde : {citoyen.argent} €"
            
            Candidature.objects.create(
                citoyen=citoyen,
                batiment=mairie,
                statut='VIREMENT',
                initiateur_est_citoyen=False,
                message=message_final
            )

    messages.success(request, 
        f"✅ Journée terminée.\n"
        f"📉 Salaires: -{total_salaires}€ | RSA: -{total_rsa}€\n"
        f"📈 Loyers: +{total_loyers}€ | Parking: +{total_parking}€"
    )
        
    return redirect('dashboard')

@login_required
def acheter_voiture(request):
    """Le Citoyen achète un véhicule"""
    try:
        citoyen = request.user.profil_citoyen
        ville = citoyen.ville
        prix_voiture = 500
        
        # Vérifier s'il y a un concessionnaire dans la ville
        if not Batiment.objects.filter(ville=ville, type_batiment='CONCESSIONNAIRE').exists():
            messages.error(request, "Il n'y a pas de Concessionnaire dans la ville !")
        elif citoyen.vehicule:
            messages.warning(request, "Vous avez déjà une voiture.")
        elif citoyen.argent >= prix_voiture:
            citoyen.argent -= prix_voiture
            citoyen.vehicule = True
            citoyen.bonheur += 15 # Vroum vroum = content
            citoyen.save()
            
            # L'argent retourne dans les caisses de la ville (TVA à 100% lol)
            ville.budget += prix_voiture
            ville.save()
            
            messages.success(request, "Félicitations ! Vous avez acheté une voiture.")
        else:
            messages.error(request, f"Pas assez d'argent. Il faut {prix_voiture} €.")
            
    except:
        pass
        
    return redirect('dashboard')


@login_required
def se_soigner(request, id_batiment):
    """Action citoyenne : Aller à l'hôpital"""
    try:
        citoyen = request.user.profil_citoyen
        batiment = get_object_or_404(Batiment, id=id_batiment)
        ville = batiment.ville
        prix_consultation = 50
        
        # 1. Vérifications
        if batiment.type_batiment != 'HOPITAL':
            messages.error(request, "Ce n'est pas un hôpital !")
        elif batiment.employes.count() == 0:
            messages.error(request, "L'hôpital est désert ! Il n'y a pas de médecins.")
        elif citoyen.sante >= 100:
            messages.info(request, "Vous êtes en pleine forme, pas besoin de médecin.")
        elif citoyen.argent < prix_consultation:
            messages.error(request, f"Vous n'avez pas assez d'argent ({prix_consultation} €).")
        else:
            # 2. Le Soin
            citoyen.argent -= prix_consultation
            citoyen.sante = 100 # Guérison complète
            citoyen.save()
            
            # L'argent va à la ville
            ville.budget += prix_consultation
            ville.save()
            
            messages.success(request, "Vous avez été soigné ! Santé revenue à 100%.")
            
    except:
        messages.error(request, "Erreur profil.")
        
    # On retourne sur la page du bâtiment pour voir le résultat
    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def telephone_index(request):
    """Accueil du téléphone : Liste des contacts"""
    from .models import Message # Import de secours
    from django.utils import timezone # Pour gérer les dates
    import datetime 
    
    moi = get_mon_profil(request.user)
    if not moi:
        return redirect('dashboard')
        
    ville = moi.ville
    autres_citoyens = Citoyen.objects.filter(ville=ville).exclude(id=moi.id)
    
    contacts_data = []
    
    for contact in autres_citoyens:
        last_msg = Message.objects.filter(
            (Q(expediteur=moi) & Q(destinataire=contact)) | 
            (Q(expediteur=contact) & Q(destinataire=moi))
        ).order_by('-date_envoi').first()
        
        has_unread = Message.objects.filter(expediteur=contact, destinataire=moi, lu=False).exists()
        
        contacts_data.append({
            'citoyen': contact,
            'last_message': last_msg,
            'has_unread': has_unread
        })
    
    # --- LA CORRECTION EST ICI ---
    # On crée une date par défaut (l'an 2000) compatible avec les fuseaux horaires
    def get_sort_date(item):
        if item['last_message']:
            return item['last_message'].date_envoi
        else:
            return timezone.now() - datetime.timedelta(days=365*50) # Il y a 50 ans

    contacts_data.sort(key=get_sort_date, reverse=True)
    # -----------------------------

    return render(request, 'phone/index.html', {'contacts_data': contacts_data})

@login_required
def telephone_chat(request, id_destinataire):
    """Écran de conversation"""
    # --- IMPORT DE SECOURS (Indispensable ici) ---
    from .models import Message 
    # ---------------------------------------------

    moi = get_mon_profil(request.user)
    autre = get_object_or_404(Citoyen, id=id_destinataire)
    
    # 1. Gestion de l'envoi
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.expediteur = moi
            msg.destinataire = autre
            msg.save()
            return redirect('telephone_chat', id_destinataire=autre.id)
    else:
        form = MessageForm()
    
    # 2. Récupération de l'historique
    # On utilise Q pour avoir les messages dans les deux sens
    messages_echanges = Message.objects.filter(
        (Q(expediteur=moi) & Q(destinataire=autre)) | 
        (Q(expediteur=autre) & Q(destinataire=moi))
    ).order_by('date_envoi')
    
    # 3. Marquer comme lu
    Message.objects.filter(expediteur=autre, destinataire=moi, lu=False).update(lu=True)

    return render(request, 'phone/chat.html', {
        'autre': autre,
        'messages_echanges': messages_echanges,
        'form': form
    })

def get_mon_profil(user):
    """Récupère le profil citoyen, ou le crée pour le Maire si besoin"""
    try:
        return user.profil_citoyen
    except:
        # Si c'est le Maire (Superuser) et qu'il n'a pas de profil, on le crée
        if user.is_superuser:
            ville = Ville.objects.first()
            # On crée un profil "Système" pour le Maire
            profil = Citoyen.objects.create(
                compte=user, 
                ville=ville, 
                prenom="Le", 
                nom="Maire", 
                age=45
            )
            return profil
    return None



@login_required
def deplacer_batiment(request, id_batiment):
    """Le Maire déplace un bâtiment (Via formulaire manuel)"""
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    if request.method == 'POST':
        try:
            new_x = int(request.POST.get('x'))
            new_y = int(request.POST.get('y'))
            
            # Utilisation de la fonction centrale de collision
            # On n'oublie pas exclude_id pour ne pas qu'il collisionne avec lui-même
            if check_collision(batiment.ville, new_x, new_y, batiment.largeur, batiment.hauteur, exclude_id=batiment.id):
                messages.error(request, "Déplacement impossible : Zone occupée ou hors carte.")
            else:
                batiment.x = new_x
                batiment.y = new_y
                batiment.save()
                messages.success(request, f"{batiment.nom} a été déplacé.")
                
        except ValueError:
             messages.error(request, "Coordonnées invalides.")
            
    return redirect('batiment_detail', id_batiment=batiment.id)

@login_required
def valider_deplacement(request, id_batiment, new_x, new_y):
    if not request.user.is_superuser: return redirect('dashboard')
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    # On vérifie la collision en excluant le bâtiment lui-même
    # (car on le déplace, il ne peut pas entrer en collision avec sa propre ancienne position)
    if check_collision(batiment.ville, new_x, new_y, batiment.largeur, batiment.hauteur, exclude_id=batiment.id):
        messages.error(request, "Emplacement invalide ou occupé.")
    else:
        batiment.x = new_x
        batiment.y = new_y
        batiment.save()
        messages.success(request, "Déplacement réussi.")
        
    return redirect('dashboard')


def check_collision(ville, x, y, w, h, exclude_id=None):
    """Vérifie si la zone (x,y,w,h) touche un bâtiment ou sort de la carte"""
    # 1. Vérification des limites de la ville (Largeur/Hauteur dynamiques)
    if x < 0 or y < 0 or (x + w) > ville.largeur_map or (y + h) > ville.hauteur_map:
        return True # Hors map

    # 2. Vérification des collisions avec les autres bâtiments
    batiments = ville.batiments.all()
    if exclude_id:
        batiments = batiments.exclude(id=exclude_id)

    for b in batiments:
        # Logique de collision de rectangles (AABB)
        if not (x + w <= b.x or  # Trop à gauche
                x >= b.x + b.largeur or  # Trop à droite
                y + h <= b.y or  # Trop en haut
                y >= b.y + b.hauteur):   # Trop en bas
            return True # Ça touche !
            
    return False


@login_required
def collecter_impots(request):
    """Le Maire prélève des impôts progressifs (Les riches paient plus, les SDF rien)"""
    if not request.user.is_superuser:
        return redirect('dashboard')
        
    ville = Ville.objects.first()
    citoyens = Citoyen.objects.filter(ville=ville)
    total_recolte = 0
    nb_imposables = 0
    
    for c in citoyens:
        # RÈGLE 1 : Les SDF (sans logement) ne paient pas d'impôts
        if not c.lieu_vie:
            continue

        # RÈGLE 2 : Barème Progressif (Tranches)
        taxe = 0
        taux = 0
        
        # Tranche 1 : Pauvres (< 100€) -> 0%
        if c.argent < 100:
            taux = 0
            taxe = 0
            
        # Tranche 2 : Classe Moyenne Basse (100€ - 500€) -> 5%
        elif c.argent < 500:
            taux = 5
            taxe = int(c.argent * 0.05)
            
        # Tranche 3 : Classe Moyenne Haute (500€ - 2000€) -> 10%
        elif c.argent < 2000:
            taux = 10
            taxe = int(c.argent * 0.10)
            
        # Tranche 4 : Les Riches (> 2000€) -> 20%
        else:
            taux = 20
            taxe = int(c.argent * 0.20)

        # Application de la taxe
        if taxe > 0:
            c.argent -= taxe
            total_recolte += taxe
            nb_imposables += 1
            
            # Impact Bonheur (Plus on paie, plus on râle)
            perte_bonheur = 2
            if taux >= 10: perte_bonheur = 5
            if taux >= 20: perte_bonheur = 10
            
            c.bonheur -= perte_bonheur
            if c.bonheur < 0: c.bonheur = 0
            
            c.save()
    
    # Enregistrement dans la caisse de la ville
    ville.budget += total_recolte
    ville.save()
    
    if total_recolte > 0:
        messages.success(request, f"Grand Recensement Fiscal terminé.\nMontant collecté : +{total_recolte} € (sur {nb_imposables} foyers imposables).")
    else:
        messages.warning(request, "La population est trop pauvre ou sans-abri. Aucun impôt collecté.")
        
    return redirect('dashboard')

@login_required
def action_banque(request, id_batiment):
    """Déposer, Retirer ou Virer de l'argent"""
    try:
        citoyen = request.user.profil_citoyen
        batiment = get_object_or_404(Batiment, id=id_batiment)
        ville = batiment.ville
        
        if request.method == 'POST':
            action = request.POST.get('action')
            montant = int(request.POST.get('montant'))
            
            if montant <= 0:
                messages.error(request, "Montant invalide.")
                return redirect('batiment_detail', id_batiment=id_batiment)
            
            # 1. DÉPÔT
            if action == 'deposer':
                if citoyen.argent >= montant:
                    citoyen.argent -= montant
                    citoyen.epargne += montant
                    citoyen.save()
                    
                    Transaction.objects.create(
                        ville=ville, expediteur=citoyen, montant=montant, type_trans='DEPOT'
                    )
                    messages.success(request, f"{montant} € déposés sur votre compte épargne.")
                else:
                    messages.error(request, "Pas assez d'argent liquide.")
                    
            # 2. RETRAIT
            elif action == 'retirer':
                if citoyen.epargne >= montant:
                    citoyen.epargne -= montant
                    citoyen.argent += montant
                    citoyen.save()
                    
                    Transaction.objects.create(
                        ville=ville, destinataire=citoyen, montant=montant, type_trans='RETRAIT'
                    )
                    messages.success(request, f"{montant} € retirés.")
                else:
                    messages.error(request, "Solde épargne insuffisant.")

            # 3. VIREMENT (AVEC NOTIFICATION)
            # 3. VIREMENT
            # 3. VIREMENT
            elif action == 'virement':
                destinataire_id = request.POST.get('destinataire_id')
                motif = request.POST.get('motif') # <--- ON RÉCUPÈRE LE MESSAGE
                destinataire = get_object_or_404(Citoyen, id=destinataire_id)
                
                if citoyen.epargne >= montant:
                    # Transfert
                    citoyen.epargne -= montant
                    destinataire.epargne += montant 
                    citoyen.save()
                    destinataire.save()
                    
                    # Enregistrement Transaction (AVEC LE MOTIF)
                    Transaction.objects.create(
                        ville=ville, 
                        expediteur=citoyen, 
                        destinataire=destinataire, 
                        montant=montant, 
                        type_trans='VIREMENT',
                        motif=motif # <--- ON SAUVEGARDE ICI
                    )

                    # Notification SMS personnalisée
                    contenu_sms = f"🏦 VIREMENT REÇU : +{montant} €."
                    if motif:
                        contenu_sms += f"\n💬 Message : {motif}"

                    Message.objects.create(
                        expediteur=citoyen, 
                        destinataire=destinataire,
                        contenu=contenu_sms,
                        lu=False
                    )

                    # Notification Dashboard (Optionnel, on garde le standard ou on ajoute le motif)
                    Candidature.objects.create(
                        citoyen=destinataire,
                        batiment=batiment,
                        statut='VIREMENT',
                        initiateur_est_citoyen=False,
                        message=f"Virement de {montant} € reçu. Motif : {motif if motif else 'Aucun'}."
                    )

                    messages.success(request, f"{montant} € virés à {destinataire.prenom}.")
                else:
                    messages.error(request, "Solde épargne insuffisant.")
                    
    except Exception as e:
        # En prod, on loguerait l'erreur 'e'
        messages.error(request, "Erreur lors de la transaction.")
        
    return redirect('batiment_detail', id_batiment=id_batiment)



@login_required
def api_send_message(request, id_destinataire):
    """API pour envoyer un message sans recharger la page"""
    # --- IMPORTS DE SÉCURITÉ ---
    from django.http import JsonResponse
    import json
    from .models import Message, Citoyen
    # ---------------------------

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            contenu = data.get('contenu')
            
            moi = get_mon_profil(request.user)
            autre = get_object_or_404(Citoyen, id=id_destinataire)
            
            if contenu:
                msg = Message.objects.create(expediteur=moi, destinataire=autre, contenu=contenu)
                # On renvoie la date formatée pour l'affichage immédiat
                return JsonResponse({'status': 'ok', 'date': msg.date_envoi.strftime("%H:%M")})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def api_get_messages(request, id_destinataire):
    """API pour récupérer les messages en temps réel"""
    # --- IMPORTS DE SÉCURITÉ ---
    from django.http import JsonResponse
    from django.db.models import Q
    from .models import Message, Citoyen
    # ---------------------------

    try:
        moi = get_mon_profil(request.user)
        autre = get_object_or_404(Citoyen, id=id_destinataire)
        
        # On récupère la conversation
        messages = Message.objects.filter(
            (Q(expediteur=moi) & Q(destinataire=autre)) | 
            (Q(expediteur=autre) & Q(destinataire=moi))
        ).order_by('date_envoi')
        
        # On marque tout comme lu (si c'est moi le destinataire)
        Message.objects.filter(expediteur=autre, destinataire=moi, lu=False).update(lu=True)
        
        # On transforme en JSON
        data = []
        for m in messages:
            is_me = (m.expediteur == moi)
            data.append({
                'contenu': m.contenu,
                'is_me': is_me,
                'date': m.date_envoi.strftime("%H:%M")
            })
            
        return JsonResponse({'messages': data})
        
    except Exception as e:
        # En cas d'erreur, on le voit dans la console du navigateur
        return JsonResponse({'error': str(e)}, status=500)
    


# myapp/views.py

@login_required
def mairie_doleance(request):
    """Envoyer une doléance au bureau du Maire"""
    # On récupère le bâtiment Mairie de la ville du citoyen
    mairie = Batiment.objects.filter(type_batiment='MAIRIE', ville=request.user.profil_citoyen.ville).first()
    
    if request.method == 'POST' and mairie:
        message = request.POST.get('message')
        moi = request.user.profil_citoyen
        
        # On crée une "Candidature" de type DOLEANCE
        Candidature.objects.create(
            citoyen=moi,
            batiment=mairie,
            statut='DOLEANCE',
            initiateur_est_citoyen=True,
            message=message
        )
        messages.success(request, "Votre doléance a été déposée sur le bureau du Maire.")
            
    return redirect('batiment_detail', id_batiment=mairie.id)


@login_required
def mairie_aide_sociale(request):
    """Demander une aide financière d'urgence"""
    citoyen = request.user.profil_citoyen
    ville = citoyen.ville
    montant_aide = 200
    seuil_pauvrete = 50
    
    if request.method == 'POST':
        # Vérification d'éligibilité
        if citoyen.argent > seuil_pauvrete:
            messages.warning(request, f"Refusé. Vous n'êtes pas éligible (Richesse > {seuil_pauvrete}€).")
        elif ville.budget < montant_aide:
            messages.error(request, "La ville n'a plus de budget pour les aides sociales.")
        else:
            # Virement Ville -> Citoyen
            ville.budget -= montant_aide
            citoyen.argent += montant_aide
            
            # Petit boost de bonheur (soulagement)
            citoyen.bonheur += 5 
            if citoyen.bonheur > 100: citoyen.bonheur = 100
            
            ville.save()
            citoyen.save()
            
            # On crée une transaction pour la traçabilité (Optionnel si vous avez le modèle Transaction)
            # Transaction.objects.create(ville=ville, destinataire=citoyen, montant=montant_aide, type_trans='VIREMENT')

            messages.success(request, f"Aide sociale de {montant_aide} € accordée. Bon courage !")
            
    mairie = Batiment.objects.filter(type_batiment='MAIRIE', ville=ville).first()
    return redirect('batiment_detail', id_batiment=mairie.id)


@login_required
def police_deposer_plainte(request):
    """Un citoyen porte plainte contre un autre"""
    # On trouve le commissariat
    commissariat = Batiment.objects.filter(type_batiment='COMMISSARIAT', ville=request.user.profil_citoyen.ville).first()
    
    if request.method == 'POST' and commissariat:
        accus_id = request.POST.get('accuse_id')
        motif = request.POST.get('motif')
        moi = request.user.profil_citoyen
        
        accuse = get_object_or_404(Citoyen, id=accus_id)
        
        # On crée le dossier
        Candidature.objects.create(
            citoyen=moi,          # Le plaignant
            batiment=commissariat,
            statut='PLAINTE',
            initiateur_est_citoyen=True,
            # On stocke l'info dans le message
            message=f"CONTRE : {accuse.prenom} {accuse.nom} ({accuse.age} ans).\nMOTIF : {motif}"
        )
        
        messages.warning(request, "Votre plainte a été enregistrée dans la main courante.")
        
    return redirect('batiment_detail', id_batiment=commissariat.id)


# 1. LA VUE "CELLULE" (Page Reclue)
@login_required
def cellule_prison(request):
    """Page d'incarcération (Sécurisée)"""
    # 1. Récupération sécurisée du profil
    try:
        citoyen = request.user.profil_citoyen
    except:
        # Si pas de profil, impossible d'être en prison
        return redirect('dashboard')

    # 2. Vérification : Est-il vraiment en prison ?
    if not citoyen.est_en_prison:
        return redirect('dashboard')

    # 3. Vérification de la date (Protection contre le crash NoneType)
    if not citoyen.date_liberation:
        # Si bug (pas de date), on le libère immédiatement pour éviter le blocage
        citoyen.est_en_prison = False
        citoyen.save()
        messages.warning(request, "Erreur administrative : Vous avez été libéré.")
        return redirect('dashboard')

    # 4. Calcul du temps
    now = timezone.now()
    if now >= citoyen.date_liberation:
        # Libération légale
        citoyen.est_en_prison = False
        citoyen.date_liberation = None
        citoyen.save()
        messages.success(request, "Vous avez purgé votre peine. Vous êtes libre !")
        return redirect('dashboard')
        
    # Calcul d'affichage
    temps_restant = citoyen.date_liberation - now
    # On utilise max(1, ...) pour afficher au moins "1 min" s'il reste des secondes
    minutes_restantes = max(1, int(temps_restant.total_seconds() / 60))
    
    return render(request, 'batiments/prison.html', {
        'citoyen': citoyen,
        'minutes': minutes_restantes
    })

# 2. LOGIQUE DE JUGEMENT (Police)
@login_required
def police_juger(request, id_candidature):
    """Transformer une plainte en condamnation"""
    plainte = get_object_or_404(Candidature, id=id_candidature)
    commissariat = plainte.batiment
    
    # Sécurité : Seul le Maire ou le Commissaire (Directeur) peut juger
    if not (request.user.is_superuser or request.user == commissariat.responsable):
        messages.error(request, "Seul le Commissaire ou le Maire peut rendre la justice.")
        return redirect('batiment_detail', id_batiment=commissariat.id)

    # On cherche la prison
    prison = Batiment.objects.filter(type_batiment='PRISON', ville=commissariat.ville).first()
    if not prison:
        messages.error(request, "Impossible d'incarcérer : Il n'y a pas de Prison dans la ville !")
        return redirect('batiment_detail', id_batiment=commissariat.id)

    # L'accusé est la personne qui a créé la plainte? NON ! 
    # Dans notre système précédent, "citoyen" était le PLAIGNANT.
    # Pour simplifier, nous allons dire que l'accusé est passé via un champ caché ou qu'on juge le plaignant pour diffamation (lol).
    # -> Pour faire propre, je vais supposer qu'on a ajouté un champ 'cible' ou qu'on parse le message.
    # MAIS, pour l'instant, faisons simple : On ne peut condamner que via une ACTION DIRECTE, pas via la plainte.
    # CHANGEONS L'APPROCHE : On va créer une vue "Arrestation Immédiate" depuis la liste des citoyens.
    
    return redirect('batiment_detail', id_batiment=commissariat.id)

# 3. VUE D'ARRESTATION DIRECTE
@login_required
def arreter_citoyen(request):
    """Mettre un citoyen en prison avec durée variable"""
    if request.method == 'POST':
        citoyen_id = request.POST.get('citoyen_id')
        
        # --- SÉCURITÉ : VÉRIFIER SI UN CITOYEN EST CHOISI ---
        if not citoyen_id:
            messages.error(request, "Erreur : Vous devez sélectionner un suspect dans la liste.")
            # On renvoie vers la page précédente (le commissariat)
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        # ----------------------------------------------------

        motif = request.POST.get('motif')
        
        # 1. Récupération des valeurs
        try:
            valeur_duree = int(request.POST.get('duree'))
        except (ValueError, TypeError):
            valeur_duree = 10 # Sécurité si le champ est vide ou invalide
            
        unite = request.POST.get('unite_temps', 'minutes')
        
        # On récupère l'accusé maintenant qu'on est sûr d'avoir un ID
        accuse = get_object_or_404(Citoyen, id=citoyen_id)
        
        # 2. Conversion en minutes
        multiplicateur = 1
        texte_unite = "minutes"
        
        if unite == 'heures':
            multiplicateur = 60
            texte_unite = "heures"
        elif unite == 'jours':
            multiplicateur = 60 * 24 
            texte_unite = "jours"
        elif unite == 'semaines':
            multiplicateur = 60 * 24 * 7
            texte_unite = "semaines"
        elif unite == 'annees':
            multiplicateur = 60 * 24 * 365
            texte_unite = "années"

        total_minutes = valeur_duree * multiplicateur
        
        # 3. Application de la peine
        accuse.est_en_prison = True
        accuse.date_liberation = timezone.now() + datetime.timedelta(minutes=total_minutes)
        
        accuse.lieu_travail = None 
        accuse.bonheur = 0 
        accuse.save()
        
        # 4. Casier Judiciaire
        from .models import Casier
        Casier.objects.create(
            citoyen=accuse,
            motif=motif,
            sanction=f"Prison fermée : {valeur_duree} {texte_unite}",
            uge_par=request.user
        )
        
        messages.warning(request, f"{accuse.prenom} a été écroué pour {valeur_duree} {texte_unite}.")
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def liberer_citoyen(request, id_citoyen):
    """Libération anticipée (Grâce présidentielle/bon conduite)"""
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    
    # Sécurité : Seul le Maire ou le Directeur de la prison peut faire ça
    prison = Batiment.objects.filter(type_batiment='PRISON', ville=citoyen.ville).first()
    if not (request.user.is_superuser or (prison and request.user == prison.responsable)):
        messages.error(request, "Vous n'avez pas l'autorité pour signer une libération.")
        return redirect('dashboard')

    if citoyen.est_en_prison:
        citoyen.est_en_prison = False
        citoyen.date_liberation = None
        citoyen.save()
        
        messages.success(request, f"{citoyen.prenom} a été libéré de prison.")
        
        # Petit message pour le prévenir
        if citoyen.compte: # S'il a un compte utilisateur
             from .models import Message # Import local si besoin
             # On pourrait lui envoyer un SMS, mais il le verra en se connectant
             
    return redirect('batiment_detail', id_batiment=prison.id)


@login_required
def voir_casier(request, id_citoyen):
    """Consulter le casier judiciaire d'un citoyen"""
    # Sécurité : Maire ou Police seulement
    # (On vérifie si le user est le directeur du commissariat)
    commissariat = Batiment.objects.filter(type_batiment='COMMISSARIAT', ville=request.user.profil_citoyen.ville).first()
    is_police = (commissariat and request.user == commissariat.responsable)
    
    if not (request.user.is_superuser or is_police):
        messages.error(request, "Accès interdit : Dossier confidentiel.")
        return redirect('dashboard')

    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    # On récupère les entrées du casier (modèle Casier créé plus tôt)
    casiers = citoyen.casier_judiciaire.all().order_by('-date_jugement')

    return render(request, 'casier_detail.html', {
        'citoyen': citoyen,
        'casiers': casiers
    })


@login_required
def expulser_locataire(request, id_citoyen):
    """Le Maire/Propriétaire vire un locataire"""
    citoyen = get_object_or_404(Citoyen, id=id_citoyen)
    batiment = citoyen.lieu_vie
    
    # Sécurité : Seul le Maire ou le responsable du bâtiment peut expulser
    if not (request.user.is_superuser or (batiment and request.user == batiment.responsable)):
        messages.error(request, "Vous n'avez pas le droit d'expulser cet habitant.")
        return redirect('dashboard')

    if batiment:
        # On crée une trace (Optionnel : Notification ou Casier ?)
        # Pour l'instant, simple message flash
        
        citoyen.lieu_vie = None
        citoyen.bonheur -= 15 # Ça fait mal de devenir SDF
        if citoyen.bonheur < 0: citoyen.bonheur = 0
        citoyen.save()
        
        messages.warning(request, f"{citoyen.prenom} a été expulsé du logement.")
        return redirect('batiment_detail', id_batiment=batiment.id)
        
    return redirect('dashboard')


@login_required
def action_ecole(request, id_batiment):
    """Actions spécifiques à l'École"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    citoyen = request.user.profil_citoyen
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. ORGANISER UNE KERMESSE (Maire/Directeur seulement)
        if action == 'kermesse':
            if not (request.user.is_superuser or request.user == batiment.responsable):
                messages.error(request, "Vous n'avez pas l'autorité pour organiser cela.")
            elif ville.budget < 500:
                messages.error(request, "Budget insuffisant (Coût : 500 €).")
            else:
                # On paye
                ville.budget -= 500
                ville.save()
                
                # On augmente le bonheur de TOUS les habitants
                habitants = Citoyen.objects.filter(ville=ville)
                for h in habitants:
                    h.bonheur += 5
                    if h.bonheur > 100: h.bonheur = 100
                    h.save()
                    
                messages.success(request, "La Kermesse est un succès ! Le bonheur général augmente.")

        # 2. SUIVRE UN COURS (Citoyen)
        elif action == 'cours':
            cout_cours = 20
            if citoyen.argent < cout_cours:
                messages.error(request, "Pas assez d'argent pour payer l'inscription.")
            else:
                citoyen.argent -= cout_cours
                citoyen.bonheur += 2 # La connaissance rend heureux !
                if citoyen.bonheur > 100: citoyen.bonheur = 100
                citoyen.save()
                
                # L'argent va à l'école (la ville)
                ville.budget += cout_cours
                ville.save()
                
                messages.success(request, "Cours terminé ! Vous vous sentez plus cultivé.")
                
    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def action_commerce(request, id_batiment):
    """Faire ses courses ou jouer au loto"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    citoyen = request.user.profil_citoyen
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. FAIRE SES COURSES (Basic)
        if action == 'courses':
            prix = 50
            if citoyen.argent >= prix:
                citoyen.argent -= prix
                # Manger remonte la santé et le moral
                citoyen.sante = min(100, citoyen.sante + 5)
                citoyen.bonheur = min(100, citoyen.bonheur + 5)
                citoyen.save()
                
                # L'argent va dans la caisse de la ville (TVA)
                ville.budget += prix
                ville.save()
                
                messages.success(request, "Frigo rempli ! (+5 Santé, +5 Bonheur)")
            else:
                messages.error(request, f"Pas assez d'argent (Il faut {prix} €).")

        # 2. TICKET DE LOTERIE (Fun)
        # 2. TICKET DE LOTERIE (Corrigé : Gain déduit de la ville)
        elif action == 'loto':
            prix_ticket = 10
            gros_lot = 500

            if citoyen.argent >= prix_ticket:
                citoyen.argent -= prix_ticket
                
                # Le prix du ticket va TOUJOURS à la ville (c'est une taxe indirecte)
                ville.budget += prix_ticket 
                
                # 1 chance sur 10 de gagner
                import random
                if random.randint(1, 10) == 1:
                    # VÉRIFICATION : La ville a-t-elle les moyens de payer le jackpot ?
                    if ville.budget >= gros_lot:
                        citoyen.argent += gros_lot
                        ville.budget -= gros_lot # <--- L'ARGENT SORT DE LA MAIRIE
                        
                        citoyen.bonheur = 100 # Jackpot !
                        messages.success(request, f"🎰 INCROYABLE ! Vous avez gagné {gros_lot} € ! (Versés par la ville)")
                    else:
                        # Cas rare : La ville est en faillite et ne peut pas payer
                        # On rembourse le ticket et on donne un petit dédommagement
                        citoyen.argent += prix_ticket + 10 
                        messages.warning(request, "🎰 GAGNÉ... Mais la ville est en faillite et ne peut pas payer le jackpot ! Ticket remboursé.")
                else:
                    messages.info(request, "Perdu... retentez votre chance !")
                
                citoyen.save()
                ville.save()
            else:
                messages.error(request, "Pas assez d'argent pour un ticket.")

    return redirect('batiment_detail', id_batiment=batiment.id)



@login_required
def action_usine(request, id_batiment):
    """Gestion de la production industrielle"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    citoyen = request.user.profil_citoyen
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. HEURES SUP (Accessible à tous les employés, même sans grade)
        if action == 'heures_sup':
            if citoyen.sante > 10:
                # Gain
                salaire_sup = 20
                citoyen.argent += salaire_sup
                
                # Coût
                citoyen.sante -= 5 # C'est fatiguant
                citoyen.bonheur -= 2 # C'est pas drôle
                
                citoyen.save()
                messages.success(request, f"Beau travail ! Vous avez gagné {salaire_sup} € (mais vous êtes fatigué).")
            else:
                messages.error(request, "Vous êtes trop faible pour travailler. Allez à l'hôpital !")

        # 2. PRODUCTION INTENSIVE (Réservé Directeur / Maire)
        elif action == 'production':
            # SÉCURITÉ STRICTE : L'Adjoint est EXCLU ici.
            if not (request.user.is_superuser or request.user.is_adjoint or request.user == batiment.responsable):
                messages.error(request, "Accès refusé : Seul le Directeur peut lancer la production.")
            elif batiment.etat < 20:
                messages.error(request, "Les machines sont trop abîmées ! Réparez l'usine d'abord.")
            else:
                gain_ville = 1000
                degats = 10
                
                ville.budget += gain_ville
                batiment.etat -= degats # L'usine s'use
                
                ville.save()
                batiment.save()
                
                messages.success(request, f"Production terminée ! +{gain_ville} € au budget (État usine : -{degats}%).")

    return redirect('batiment_detail', id_batiment=batiment.id)

@login_required
def action_centrale(request, id_batiment):
    """Gestion de l'énergie de la ville"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    citoyen = request.user.profil_citoyen
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. ACHAT DE COMBUSTIBLE (Manager : Maire/Directeur)
        if action == 'produire':
            cout_achat = 500
            gain_energie = 100
            
            if not (request.user.is_superuser or request.user == batiment.responsable):
                 messages.error(request, "Accès refusé aux commandes.")
            elif ville.budget < cout_achat:
                messages.error(request, f"Budget insuffisant (Il faut {cout_achat} €).")
            else:
                ville.budget -= cout_achat
                ville.energie_stock += gain_energie
                
                # L'usine s'abîme un peu
                batiment.etat -= 5
                
                ville.save()
                batiment.save()
                messages.success(request, f"Production lancée : +{gain_energie} kWh ajoutés au réseau.")

        # 2. MAINTENANCE À HAUT RISQUE (Employé)
        elif action == 'maintenance':
            if citoyen.sante > 20:
                prime = 60 # Paye mieux que l'usine (20€)
                
                citoyen.argent += prime
                citoyen.sante -= 15 # Mais beaucoup plus dangereux/fatiguant
                
                # Petit risque d'accident (1 chance sur 10)
                import random
                if random.randint(1, 10) == 1:
                    citoyen.sante -= 30
                    messages.warning(request, "⚠️ Accident de travail ! Vous avez pris une décharge électrique.")
                
                citoyen.save()
                
                # La maintenance répare un peu le bâtiment
                batiment.etat = min(100, batiment.etat + 2)
                batiment.save()
                
                messages.success(request, f"Maintenance effectuée. Prime de risque reçue : {prime} €.")
            else:
                messages.error(request, "Santé trop fragile pour entrer dans le réacteur.")

    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def action_concessionnaire(request, id_batiment):
    """Achat de véhicules et gestion"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    ville = batiment.ville
    citoyen = request.user.profil_citoyen
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. ACHETER UNE VOITURE
        if action == 'acheter':
            try:
                prix = int(request.POST.get('prix', 500))
                modele = request.POST.get('modele', 'Voiture Standard') # On récupère le nom
            except:
                prix = 500
                modele = 'Voiture Standard'

            if citoyen.argent < prix:
                messages.error(request, f"Fonds insuffisants. Ce modèle coûte {prix} €.")
            else:
                citoyen.argent -= prix
                citoyen.vehicule = True
                
                # 👇 ON SAUVEGARDE LE NOM ICI 👇
                citoyen.nom_voiture = modele
                
                # Bonus de bonheur
                bonus_bonheur = 10 + int(prix / 100)
                citoyen.bonheur = min(100, citoyen.bonheur + bonus_bonheur)
                
                citoyen.save()
                
                # L'argent va à la ville
                ville.budget += prix
                ville.save()
                
                messages.success(request, f"Félicitations ! Vous roulez désormais en {modele}.")

        # 2. CAMPAGNE DE PUB (Manager)
        elif action == 'pub':
            cout_pub = 200
            if not (request.user.is_superuser or request.user == batiment.responsable):
                messages.error(request, "Action réservée au directeur.")
            elif ville.budget < cout_pub:
                messages.error(request, "Budget ville insuffisant.")
            else:
                ville.budget -= cout_pub
                
                # Prime de sponsoring (50€ par voiture en ville)
                nb_voitures = Citoyen.objects.filter(ville=ville, vehicule=True).count()
                prime_sponsoring = nb_voitures * 50 
                
                ville.budget += prime_sponsoring
                ville.save()
                
                # Bonus bonheur pour les conducteurs
                proprietaires = Citoyen.objects.filter(ville=ville, vehicule=True)
                for c in proprietaires:
                    c.bonheur = min(100, c.bonheur + 5)
                    c.save()
                    
                messages.success(request, f"Campagne réussie ! Prime constructeur reçue : {prime_sponsoring} €.")

    return redirect('batiment_detail', id_batiment=batiment.id)



@login_required
def action_parking(request, id_batiment):
    """Gestion du tarif de stationnement"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    if request.method == 'POST' and (request.user.is_superuser or request.user == batiment.responsable):
        nouveau_tarif = int(request.POST.get('tarif', 10))
        
        # On utilise le champ 'production_argent' pour sauvegarder le tarif fixé par le maire
        batiment.production_argent = nouveau_tarif
        batiment.save()
        
        messages.success(request, f"Le tarif de stationnement est fixé à {nouveau_tarif} € / jour.")
        
    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def api_get_messages(request, id_destinataire):
    """API pour récupérer les messages en JSON (Poling)"""
    moi = request.user.profil_citoyen
    autre = get_object_or_404(Citoyen, id=id_destinataire)
    
    # Récupérer l'historique
    messages = Message.objects.filter(
        (Q(expediteur=moi) & Q(destinataire=autre)) | 
        (Q(expediteur=autre) & Q(destinataire=moi))
    ).order_by('date_envoi')
    
    # Marquer comme lu ce qui vient de l'autre
    Message.objects.filter(expediteur=autre, destinataire=moi, lu=False).update(lu=True)
    
    # On transforme en liste de dictionnaires pour le JSON
    data = []
    for msg in messages:
        data.append({
            'contenu': msg.contenu,
            'date': msg.date_envoi.strftime("%H:%M"), # Format Heure:Minute
            'is_me': (msg.expediteur == moi)
        })
        
    return JsonResponse({'messages': data})

@login_required
def api_send_message(request, id_destinataire):
    """API pour envoyer un message en JSON"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            contenu = data.get('contenu')
            
            if contenu:
                moi = request.user.profil_citoyen
                autre = get_object_or_404(Citoyen, id=id_destinataire)
                
                Message.objects.create(
                    expediteur=moi,
                    destinataire=autre,
                    contenu=contenu
                )
                return JsonResponse({'status': 'ok'})
        except:
            pass
            
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def api_check_unread(request):
    """Vérifie s'il y a des nouveaux messages pour le badge global"""
    moi = request.user.profil_citoyen
    count = Message.objects.filter(destinataire=moi, lu=False).count()
    return JsonResponse({'count': count})


@login_required
def renommer_batiment(request, id_batiment):
    """Permet au Maire ou au Directeur de renommer un bâtiment"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    # Sécurité : Maire ou Responsable seulement
    if not (request.user.is_superuser or request.user == batiment.responsable):
        messages.error(request, "Action non autorisée.")
        return redirect('batiment_detail', id_batiment=batiment.id)
    
    if request.method == 'POST':
        nouveau_nom = request.POST.get('nom')
        if nouveau_nom:
            batiment.nom = nouveau_nom
            batiment.save()
            messages.success(request, f"Bâtiment renommé : {nouveau_nom}")
    
    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def placer_route(request, x, y):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Interdit'}, status=403)

    ville = request.user.profil_citoyen.ville
    rotation = int(request.GET.get('rotation', 0))
    
    # PRIX DE LA ROUTE
    COUT = 10 

    # 1. VÉRIFICATION DU BUDGET
    if ville.budget < COUT:
        return JsonResponse({'status': 'error', 'message': 'Pas assez d\'argent !'}, status=402)

    # 2. VÉRIFICATION COLLISION
    if check_collision(ville, x, y, 2, 2):
        return JsonResponse({'status': 'error', 'message': 'Occupé'}, status=409)

    try:
        # 3. PAIEMENT
        ville.budget -= COUT
        ville.save()

        # 4. CRÉATION
        batiment = Batiment.objects.create(
            ville=ville,
            nom="Route",
            type_batiment='ROUTE',
            x=x, y=y, largeur=2, hauteur=2,
            cout_construction=COUT, # On enregistre le vrai prix
            production_argent=0, consommation_energie=0,
            rotation=rotation
        )
        return JsonResponse({'status': 'ok', 'x': x, 'y': y, 'id': batiment.id, 'rotation': rotation})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



@login_required
def action_police(request, id_batiment):
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    if request.method == 'POST':
        # Sécurité
        if not (request.user.is_superuser or request.user.is_adjoint or request.user == batiment.responsable):
            return redirect('batiment_detail', id_batiment=batiment.id)

        target_id = request.POST.get('citoyen_id')
        action = request.POST.get('action_type')
        motif = request.POST.get('motif', 'Infraction mineure') # On récupère le motif
        
        try:
            target = Citoyen.objects.get(id=target_id)
            ville = batiment.ville
            description_sanction = "" # Pour le casier

            if action == 'amende':
                montant = int(request.POST.get('montant', 135))
                if target.argent >= montant:
                    target.argent -= montant
                    ville.budget += montant
                    target.bonheur -= 10
                    messages.success(request, f"Amende de {montant}€.")
                else:
                    recup = target.argent
                    target.argent = 0
                    ville.budget += recup
                    target.bonheur -= 20
                    messages.warning(request, f"Insolvable. Saisie de {recup}€.")
                
                description_sanction = f"Amende de {montant} €"

                Candidature.objects.create(
                    batiment=batiment, # Le commissariat
                    citoyen=target,
                    message=f"👮 SANCTION ADMINISTRATIVE\nVous avez reçu une amende de {montant} €.\nMOTIF : {motif}",
                    statut='REFUSEE', # Apparaîtra en rouge (Badge "Refus" ou similaire dans le dash)
                    initiateur_est_citoyen=False
                )

            elif action == 'prison':
                duree_minutes = int(request.POST.get('duree', 10))
                target.est_en_prison = True
                target.date_liberation = timezone.now() + timedelta(minutes=duree_minutes)
                target.bonheur -= 30
                messages.success(request, f"Prison pour {duree_minutes} min.")
                
                description_sanction = f"Prison ferme ({duree_minutes} min)"

                # 👇 NOTIFICATION INCARCÉRATION (NOUVEAU) 👇
                Candidature.objects.create(
                    batiment=batiment,
                    citoyen=target,
                    message=f"⚖️ DÉCISION DE JUSTICE\nVous avez été incarcéré pour {duree_minutes} minutes.\nMOTIF : {motif}",
                    statut='VIRE', # Apparaîtra en noir/sombre pour marquer le coup
                    initiateur_est_citoyen=False
                )

            # SAUVEGARDE DE L'ÉTAT DU CITOYEN
            target.save()
            ville.save()

            # --- CRÉATION DU CASIER JUDICIAIRE (ARCHIVAGE) ---
            Casier.objects.create(
                citoyen=target,
                juge_par=request.user,  # L'officier qui a cliqué
                motif=motif,
                sanction=description_sanction,
                # La date se mettra automatiquement grâce à auto_now_add dans ton modèle
            )
            # ---------------------------------------------------

            # Suppression de la plainte liée
            plainte_id = request.POST.get('plainte_id')
            if plainte_id:
                Candidature.objects.filter(id=plainte_id).delete()

        except Citoyen.DoesNotExist:
            messages.error(request, "Citoyen introuvable.")

    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def classer_plainte(request, id_plainte):
    """Permet de supprimer une plainte et RESTER dans le commissariat"""
    plainte = get_object_or_404(Candidature, id=id_plainte)
    batiment_id = plainte.batiment.id # On sauvegarde l'ID avant de supprimer
    
    # Sécurité (Police/Maire/Adjoint uniquement)
    if request.user.is_superuser or request.user.is_adjoint or request.user == plainte.batiment.responsable:
        plainte.delete()
        messages.info(request, "Plainte classée sans suite.")
    else:
        messages.error(request, "Droit insuffisant.")
        
    # RETOUR AU BATIMENT (C'est ça qui règle ton problème de redirection)
    return redirect('batiment_detail', id_batiment=batiment_id)


@login_required
def supprimer_route(request, x, y):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Interdit'}, status=403)
    
    ville = request.user.profil_citoyen.ville
    
    # On cherche une route (droite OU virage) qui couvre la case cliquée
    routes = Batiment.objects.filter(
        ville=ville, 
        type_batiment__in=['ROUTE', 'ROUTE_VIRAGE'], # <--- LA CORRECTION EST ICI
        x__lte=x, 
        y__lte=y
    )
    
    target_road = None
    for r in routes:
        # On vérifie que le clic est bien DANS le carré 2x2 de la route
        if (r.x + r.largeur > x) and (r.y + r.hauteur > y):
            target_road = r
            break
            
    if target_road:
        road_id = target_road.id 
        target_road.delete()
        return JsonResponse({'status': 'ok', 'id_deleted': road_id})
    else:
        return JsonResponse({'status': 'error', 'message': 'Rien à supprimer ici.'})
    
@login_required
def placer_virage(request, x, y):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Interdit'}, status=403)

    ville = request.user.profil_citoyen.ville
    rotation = int(request.GET.get('rotation', 0))
    
    # PRIX DU VIRAGE
    COUT = 10

    # 1. VÉRIFICATION DU BUDGET
    if ville.budget < COUT:
        return JsonResponse({'status': 'error', 'message': 'Pas assez d\'argent !'}, status=402)

    # 2. VÉRIFICATION COLLISION
    if check_collision(ville, x, y, 2, 2):
        return JsonResponse({'status': 'error', 'message': 'Occupé'}, status=409)

    try:
        # 3. PAIEMENT
        ville.budget -= COUT
        ville.save()

        # 4. CRÉATION
        batiment = Batiment.objects.create(
            ville=ville,
            nom="Virage",
            type_batiment='ROUTE_VIRAGE',
            x=x, y=y, largeur=2, hauteur=2,
            cout_construction=COUT,
            production_argent=0, consommation_energie=0,
            rotation=rotation
        )
        return JsonResponse({'status': 'ok', 'x': x, 'y': y, 'id': batiment.id, 'rotation': rotation})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    

@login_required
def action_hopital(request, id_batiment):
    """Actions administratives de l'Hôpital (Rappels de santé)"""
    batiment = get_object_or_404(Batiment, id=id_batiment)
    
    # Sécurité : Seul le Maire ou le Directeur peut envoyer des rappels
    if not (request.user.is_superuser or request.user == batiment.responsable):
        messages.error(request, "Accès refusé.")
        return redirect('batiment_detail', id_batiment=batiment.id)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. RAPPEL INDIVIDUEL (Au clic sur un patient)
        if action == 'rappel_individuel':
            try:
                target_id = request.POST.get('citoyen_id')
                target = Citoyen.objects.get(id=target_id)
                
                # On utilise 'DOLEANCE' initié par False pour que ça apparaisse comme une INFO (Badge Gris)
                # ou tu peux créer un statut 'SANTE' si tu veux un badge spécifique plus tard
                Candidature.objects.create(
                    citoyen=target,
                    batiment=batiment,
                    statut='DOLEANCE', # Apparaîtra comme "Info" dans le dashboard
                    initiateur_est_citoyen=False,
                    message=f"🏥 RAPPEL SANTÉ\nBonjour {target.prenom}, votre état de santé semble préoccupant ({target.sante}%). Merci de passer nous voir rapidement."
                )
                messages.success(request, f"Rappel envoyé à {target.prenom} {target.nom}.")
            except Citoyen.DoesNotExist:
                messages.error(request, "Patient introuvable.")

        # 2. CAMPAGNE GÉNÉRALE (À tous les citoyens)
        elif action == 'rappel_global':
            targets = Citoyen.objects.filter(ville=batiment.ville)
            count = 0
            
            for t in targets:
                # On évite de spammer ceux qui sont déjà à l'hôpital (optionnel)
                if t.sante < 100:
                    msg = "🏥 PRÉVENTION\nLa santé est notre priorité. N'hésitez pas à consulter si vous vous sentez faible."
                    
                    Candidature.objects.create(
                        citoyen=t,
                        batiment=batiment,
                        statut='DOLEANCE',
                        initiateur_est_citoyen=False,
                        message=msg
                    )
                    count += 1
            
            # On retire un peu de budget pour la campagne de pub ? (Optionnel)
            cout_campagne = 100
            if batiment.ville.budget >= cout_campagne:
                batiment.ville.budget -= cout_campagne
                batiment.ville.save()
                messages.success(request, f"Campagne de prévention lancée auprès de {count} citoyens (Coût : {cout_campagne} €).")
            else:
                messages.warning(request, "Campagne lancée (Gratuitement car budget insuffisant).")

    return redirect('batiment_detail', id_batiment=batiment.id)


@login_required
def organiser_fete(request):
    if request.method == 'POST':
        ville = Ville.objects.first()
        
        cout_fete = 5000
        
        if ville.budget >= cout_fete:
            # 1. On paye
            ville.budget -= cout_fete
            ville.save()
            
            # 2. On augmente le bonheur de TOUS les habitants
            citoyens = Citoyen.objects.filter(ville=ville)
            for c in citoyens:
                c.bonheur += 15  # Le save() du modèle gère le blocage à 100
                c.save()
                
            messages.success(request, f"🎉 La fête est un succès ! Le bonheur a augmenté (+15). Budget: -{cout_fete}€")
        else:
            messages.error(request, "Pas assez d'argent pour organiser une fête !")
            
    return redirect('dashboard')

@login_required
def organiser_soiree(request):
    try:
        # On récupère le citoyen connecté
        citoyen = request.user.profil_citoyen
        cout_soiree = 200 # C'est pas cher, c'est une pizza party !
        
        if citoyen.argent >= cout_soiree:
            # 1. Il paye
            citoyen.argent -= cout_soiree
            
            # 2. Il gagne du bonheur (max 100)
            # On donne un bon boost car c'est une action active
            citoyen.bonheur += 10 
            
            citoyen.save()
            messages.success(request, f"🍕 Super soirée ! Votre moral remonte (+10). Portefeuille : -{cout_soiree}€")
        else:
            messages.error(request, "Vous n'avez pas assez d'argent pour organiser une soirée (200€ requis).")
            
    except:
        pass
        
    return redirect('dashboard')


@login_required
def bannir_citoyen(request, citoyen_id):
    # Sécurité : Seul le Maire peut bannir
    if not request.user.is_superuser:
        messages.error(request, "Seul le Maire a le pouvoir de bannissement.")
        return redirect('dashboard')

    citoyen = get_object_or_404(Citoyen, id=citoyen_id)
    
    # Empêcher le Maire de se bannir lui-même
    if citoyen.compte == request.user:
        messages.error(request, "Vous ne pouvez pas vous bannir vous-même !")
        return redirect('gestion_citoyens')

    # --- 1. DESTITUTION ---
    if citoyen.compte:
        # On cherche le bâtiment dirigé par ce COMPTE UTILISATEUR
        batiment_dirige = Batiment.objects.filter(responsable=citoyen.compte).first()
        
        if batiment_dirige:
            nom_batiment = batiment_dirige.nom
            
            # On vire le directeur (Poste vacant)
            batiment_dirige.responsable = None 
            batiment_dirige.save()
            
            messages.warning(request, f"⚠️ {citoyen.prenom} a été destitué de la direction de : {nom_batiment}.")

            # --- CORRECTION ICI ---
            # L'auteur doit être un User (request.user), pas un Citoyen
            Actualite.objects.create(
                ville=batiment_dirige.ville,
                titre="Poste Vacant",
                contenu=f"Le poste de directeur de {nom_batiment} est libre suite au départ de l'ancien responsable.",
                auteur=request.user  # <-- C'est ça qui bloquait !
            )

    # --- 2. BANNISSEMENT (Désactivation) ---
    if citoyen.compte:
        user_account = citoyen.compte
        user_account.is_active = False # Désactive le compte (Empêche la connexion)
        user_account.save()
        
        # On vide ses infos dans le jeu (Chômage + SDF)
        citoyen.lieu_travail = None
        citoyen.lieu_vie = None
        citoyen.save()

    messages.success(request, f"⛔ {citoyen.prenom} {citoyen.nom} a été banni et son compte désactivé.")
    
    return redirect('gestion_citoyens')