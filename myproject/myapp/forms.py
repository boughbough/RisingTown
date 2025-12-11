from django import forms
from .models import Batiment, Citoyen, Ville, Information, Actualite, Candidature, Message

class BatimentForm(forms.ModelForm):
    class Meta:
        model = Batiment
        fields = ['nom', 'type_batiment'] # PLUS DE X NI DE Y
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du bâtiment'}),
            'type_batiment': forms.Select(attrs={'class': 'form-select'}),
        }

class CitoyenForm(forms.ModelForm):
    class Meta:
        model = Citoyen
        fields = ['prenom', 'nom', 'age', 'sexe'] # On ajoute le sexe pour être précis
        # Note: Si tu n'as pas le champ 'sexe' dans ton model, enlève-le de la liste !
        # Restons sur tes champs actuels :
        fields = ['prenom', 'nom', 'age']
        
        widgets = {
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Jean'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dupont'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 18, 'max': 99}),
        }

class UpdateCitoyenForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Citoyen
        fields = ['prenom', 'nom', 'age']
        widgets = {
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class VilleForm(forms.ModelForm):
    class Meta:
        model = Ville
        # On ajoute les champs de dimensions
        fields = ['nom', 'largeur_map', 'hauteur_map']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la ville'}),
            'largeur_map': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 50}),
            'hauteur_map': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 50}),
        }
        labels = {
            'largeur_map': 'Largeur du terrain (Cases X)',
            'hauteur_map': 'Profondeur du terrain (Cases Y)',
        }
class InformationForm(forms.ModelForm):
    class Meta:
        model = Information
        fields = ['nom_info', 'valeur_info']
        widgets = {
            'nom_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Code Postal, Altitude...'}),
            'valeur_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 75000, 300m...'}),
        }
        labels = {
            'nom_info': 'Intitulé (ex: Code Postal)',
            'valeur_info': 'Valeur',
        }


# Formulaire pour que le Maire inscrive manuellement quelqu'un
class CitoyenCreationForm(forms.ModelForm):
    # Champs pour le compte de connexion (User)
    username = forms.CharField(label="Identifiant de connexion", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Mot de passe provisoire", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Citoyen
        fields = ['prenom', 'nom', 'age']
        widgets = {
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ActualiteForm(forms.ModelForm):
    class Meta:
        model = Actualite
        fields = ['titre', 'contenu']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de l\'info'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Votre message...'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['contenu']
        widgets = {
            'contenu': forms.TextInput(attrs={
                'class': 'form-control rounded-pill',
                'placeholder': 'Votre message...',
                'autocomplete': 'off'
            }),
        }