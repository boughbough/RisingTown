from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# 1. Extension de l'utilisateur
class User(AbstractUser):
    is_directeur = models.BooleanField(default=False, help_text="Est directeur d'un bâtiment spécifique")
    is_adjoint = models.BooleanField(default=False, help_text="Est adjoint au Maire (Droit de construction)")
    
    def __str__(self):
        return self.username

# 2. La Ville
class Ville(models.Model):
    nom = models.CharField(max_length=100)
    budget = models.IntegerField(default=100000)
    energie_stock = models.IntegerField(default=1000)
    population_totale = models.IntegerField(default=0)
    dernier_calcul = models.DateTimeField(auto_now=True)
    
    # NOUVEAUX CHAMPS : Dimensions de la carte
    largeur_map = models.IntegerField(default=10, help_text="Nombre de cases en largeur (X)")
    hauteur_map = models.IntegerField(default=5, help_text="Nombre de cases en hauteur (Y)")

    def __str__(self):
        return self.nom

# 3. Les Bâtiments
class Batiment(models.Model):
    TYPE_CHOICES = (
        ('MAIRIE', 'Mairie'),
        ('COMMISSARIAT', 'Commissariat de Police'),
        ('MAISON', 'Maison'),
        ('IMMEUBLE', 'Immeuble résidentiel'),
        ('HOPITAL', 'Hôpital'),
        ('ECOLE', 'École'),
        ('COMMERCE', 'Commerce / Supermarché'),
        ('USINE', 'Usine'),
        ('BUREAUX', 'Immeuble de Bureaux'),
        ('CENTRALE', 'Centrale Électrique'),
        ('PARKING', 'Parking Souterrain'),
        ('CONCESSIONNAIRE', 'Concessionnaire Auto'),
        ('BANQUE', 'Banque'),
        ('PRISON', 'Prison d\'État'),
        ('ROUTE', 'Route Droite'),
        ('ROUTE_VIRAGE', 'Route Virage'), # <--- NOUVEAU
    )

    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="batiments")
    nom = models.CharField(max_length=100, default="Nouveau Bâtiment")
    type_batiment = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    niveau = models.IntegerField(default=1)
    cout_construction = models.IntegerField(default=5000)
    consommation_energie = models.IntegerField(default=10)
    production_argent = models.IntegerField(default=0)

    loyer = models.IntegerField(default=0, help_text="Loyer mensuel pour les locataires")
    
    # NOUVEAU CHAMP : Capacité d'accueil (Logement)
    capacite = models.IntegerField(default=0, help_text="Nombre max d'habitants")
    etat = models.IntegerField(default=100)

    x = models.IntegerField(default=0, help_text="Position horizontale (0-9)")
    y = models.IntegerField(default=0, help_text="Position verticale (0-9)")

    # NOUVEAUX CHAMPS
    largeur = models.IntegerField(default=1, help_text="Taille en X")
    hauteur = models.IntegerField(default=1, help_text="Taille en Y")

    rotation = models.IntegerField(default=0, help_text="Rotation en degrés (0 ou 90)")

    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="batiments_diriges")
    def __str__(self):
        return f"{self.nom} ({self.get_type_batiment_display()})"

    @property
    def peut_embaucher(self):
        NON_TRAVAIL = ['MAISON', 'IMMEUBLE', 'PARKING']
        return self.type_batiment not in NON_TRAVAIL
    
    # NOUVELLE PROPRIÉTÉ : Est-ce un logement ?
    @property
    def est_logement(self):
        TYPES_LOGEMENT = ['MAISON', 'IMMEUBLE']
        return self.type_batiment in TYPES_LOGEMENT
    
    # NOUVELLE PROPRIÉTÉ : Places restantes
    @property
    def places_disponibles(self):
        # On compte combien de citoyens ont ce bâtiment comme lieu_vie
        return self.capacite - self.locataires.count()

# 4. Les Citoyens
class Citoyen(models.Model):
    compte = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="profil_citoyen")
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="habitants")
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    age = models.IntegerField(default=18)
    lieu_travail = models.ForeignKey(Batiment, on_delete=models.SET_NULL, null=True, blank=True, related_name="employes")
    sante = models.IntegerField(default=100)
    bonheur = models.IntegerField(default=100)
    # Dans la classe Citoyen
    epargne = models.IntegerField(default=0) # Argent à la banque (à l'abri du vol et des impôts)
    lieu_vie = models.ForeignKey(
        Batiment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="locataires" # Pour faire batiment.locataires.all()
    )
    argent = models.IntegerField(default=0) # Porte-monnaie
    vehicule = models.BooleanField(default=False) # A-t-il une voiture ?
    est_en_prison = models.BooleanField(default=False)
    date_liberation = models.DateTimeField(null=True, blank=True)
    prochain_loyer = models.DateTimeField(null=True, blank=True)
    nom_voiture = models.CharField(max_length=100, blank=True, null=True, default="Aucune")

    def __str__(self):
        return f"{self.prenom} {self.nom}"

# 5. Les Candidatures (Le fameux modèle qui posait problème)
class Candidature(models.Model):
    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('ACCEPTEE', 'Acceptée'),
        ('REFUSEE', 'Refusée'),
        ('VIRE', 'Licencié'),
        ('DEMISSION', 'Démission'),
        ('VIREMENT', 'Virement Reçu'),
        ('DOLEANCE', 'Doléance Citoyenne'),
        ('PLAINTE', 'Plainte / Main Courante'),
    )

    # Ces champs doivent impérativement être là !
    citoyen = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="candidatures")
    batiment = models.ForeignKey(Batiment, on_delete=models.SET_NULL, null=True, related_name="candidatures")
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_creation = models.DateTimeField(auto_now_add=True)
    initiateur_est_citoyen = models.BooleanField(default=True)
    
    # Le nouveau champ message
    message = models.TextField(null=True, blank=True, help_text="Motivation, motif de refus ou de licenciement")

    def __str__(self):
        return f"{self.citoyen} -> {self.batiment} ({self.statut})"
    
class Information(models.Model):
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="informations")
    # Ex: "Code Postal", "Arrondissement", "Superficie"
    nom_info = models.CharField(max_length=100, verbose_name="Nom de l'information")
    # Ex: "75001", "5ème", "105 km²"
    valeur_info = models.CharField(max_length=255, verbose_name="Valeur")

    def __str__(self):
        return f"{self.nom_info} : {self.valeur_info}"
    

class Actualite(models.Model):
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name="actualites")
    # Si renseigné, c'est une note interne au bâtiment. Sinon, c'est public.
    batiment = models.ForeignKey(Batiment, on_delete=models.CASCADE, null=True, blank=True, related_name="notes_service")
    
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    titre = models.CharField(max_length=100)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.batiment:
            return f"[Interne {self.batiment}] {self.titre}"
        return f"[Public] {self.titre}"
    

class Message(models.Model):
    expediteur = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="messages_envoyes")
    destinataire = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="messages_recus")
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False) # Pour gérer les notifications "non lu"

    def __str__(self):
        return f"De {self.expediteur} à {self.destinataire}"
    


class Transaction(models.Model):
    TYPES = (
        ('DEPOT', 'Dépôt'),
        ('RETRAIT', 'Retrait'),
        ('VIREMENT', 'Virement'),
        ('SALAIRE', 'Salaire'),
        ('IMPOT', 'Impôts'),
    )
    
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    # L'initiateur (celui qui perd l'argent ou dépose)
    expediteur = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="debits", null=True, blank=True)
    # Le bénéficiaire (celui qui reçoit)
    destinataire = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name="credits", null=True, blank=True)
    
    montant = models.IntegerField()
    type_trans = models.CharField(max_length=20, choices=TYPES)
    date = models.DateTimeField(auto_now_add=True)

    motif = models.CharField(max_length=100, blank=True, null=True, help_text="Message optionnel") 
    
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.type_trans} : {self.montant} €"
    

class Casier(models.Model):
    citoyen = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name='casiers')
    
    # 👇 C'EST CETTE LIGNE QUI MANQUAIT 👇
    juge_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    motif = models.CharField(max_length=255)
    sanction = models.CharField(max_length=255)
    date_jugement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sanction de {self.citoyen.nom} ({self.date_jugement})"