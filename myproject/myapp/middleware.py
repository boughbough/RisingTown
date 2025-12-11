# myapp/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class PrisonMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profil_citoyen'):
            citoyen = request.user.profil_citoyen
            
            if citoyen.est_en_prison:
                
                # A. LIBÉRATION AUTOMATIQUE
                if citoyen.date_liberation and timezone.now() > citoyen.date_liberation:
                    
                    # 1. On le libère
                    citoyen.est_en_prison = False
                    citoyen.date_liberation = None
                    citoyen.save()
                    
                    # 2. 👇 ON ENVOIE LA NOTIFICATION DE SORTIE (NOUVEAU) 👇
                    # On doit importer les modèles ICI (pas en haut du fichier)
                    from .models import Batiment, Candidature
                    
                    # On cherche le commissariat pour signer le message
                    commissariat = Batiment.objects.filter(type_batiment='COMMISSARIAT').first()
                    
                    # Si un commissariat existe, il envoie la notif
                    if commissariat:
                        Candidature.objects.create(
                            batiment=commissariat,
                            citoyen=citoyen,
                            message="✅ LIBÉRATION\nVotre peine est terminée. Vous êtes libre. Tâchez de rester dans le droit chemin.",
                            statut='ACCEPTEE', # Apparaîtra en vert
                            initiateur_est_citoyen=False
                        )
                    
                else:
                    # B. RESTE EN PRISON (Code existant pour bloquer la navigation)
                    current_path = request.path
                    allowed_paths = [
                        reverse('cellule_prison'), 
                        reverse('logout'),
                        '/admin/', 
                        '/static/'
                    ]
                    if not any(current_path.startswith(path) for path in allowed_paths):
                        return redirect('cellule_prison')

        response = self.get_response(request)
        return response

class NoCacheMiddleware:
    """
    Empêche le navigateur de garder les pages en mémoire
    quand l'utilisateur est connecté.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si l'utilisateur est connecté, on force le navigateur à ne rien stocker
        if request.user.is_authenticated:
            response['Cache-Control'] = "no-cache, no-store, must-revalidate"
            response['Pragma'] = "no-cache"
            response['Expires'] = "0"
            
        return response