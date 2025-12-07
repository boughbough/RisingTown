from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Ville, Batiment, Citoyen

# Enregistrement des modèles pour l'interface admin
admin.site.register(User, UserAdmin)
admin.site.register(Ville)
admin.site.register(Batiment)
admin.site.register(Citoyen)