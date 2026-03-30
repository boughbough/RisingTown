# 🏙️ RisingTown : Simulation de Smart City

###

<div align="left">
  <h2>🔹 Stack Technique</h2>
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" height="40" alt="python logo" />
  <img width="12" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/django/django-plain.svg" height="40" alt="django logo" />
  <img width="12" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/sqlite/sqlite-original.svg" height="40" alt="sqlite logo" />
  <img width="12" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" height="40" alt="javascript logo"  />
  <img width="12" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" height="40" alt="html5 logo"  />
  <img width="12" />
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/css3/css3-original.svg" height="40" alt="css3 logo"  />
  <img width="12" />
</div>

###

## 🔹 Présentation du Projet

**RisingTown** est une application web de simulation urbaine gamifiée. Ce projet permet à plusieurs utilisateurs d'interagir en temps réel au sein d'une ville virtuelle persistante.

* **Contexte** : Développée dans le cadre de la Licence 3 MIAGE à l'Université Paris Nanterre (Décembre 2025).
* **Objectifs** : Gérer des aspects économiques, sociaux et urbanistiques en incarnant différents rôles dans une société simulée.
* **Fonctionnalités Clés** : 
    * **Gestion Urbaine** : Carte isométrique interactive (construction, déplacement, rotation de bâtiments).
    * **Système de Rôles** : Maire (budget, urbanisme), Adjoint (maintenance), Directeur (entreprises) et Citoyen (emploi, logement).
    * **Économie & Mécaniques** : Économie en temps réel (salaires, impôts, loyers), jauges de vie (Santé/Bonheur).
    * **Social & Justice** : Chat en direct (téléphone), système de plaintes, casier judiciaire et prison.

###

## 🔹 Installation & Déploiement

1.  **Cloner le projet** : Récupérer le code via `git clone https://github.com/boughbough/RisingTown.git` puis `cd RisingTown`.
2.  **Environnement virtuel** : Isoler les dépendances en créant un venv (`python -m venv venv`) puis l'activer (`venv\Scripts\activate` sur Windows ou `source venv/bin/activate` sur Mac/Linux).
3.  **Dépendances** : Installer les paquets requis avec la commande `pip install -r requirements.txt`.
4.  **Base de données** : Initialiser la structure SQLite fournie avec `python manage.py migrate`.
5.  **Administration** : Créer le compte Maire (super-utilisateur) via `python manage.py createsuperuser`.
6.  **Lancement** : Démarrer le serveur local avec `python manage.py runserver` et accéder à l'interface sur `127.0.0.1:8000`.

###

## 🔹 Structure du Projet

* **myapp/** : Cœur logique de l'application (Views, Models, Forms, Migrations).
* **myproject/** : Configuration globale (Settings, URLs, WSGI).
* **templates/** : Interfaces HTML (Dashboard, Carte, Login, Admin).
* **static/** : Fichiers statiques (CSS, Javascript, Images/Sprites).
* **db.sqlite3 & manage.py** : Base de données locale et utilitaire de gestion du framework Django.

###

<br clear="both">

<p align="center">
  <b>Auteurs : Mohamed Boughmadi, Mohamet Thiam, Faiz Djama, Joël Kpinso-Folly & Hamid Adenle (Projet L3 MIAGE 2025)</b>
</p>

<div align="center">
  <h3>💬 Questions ? Contacts:</h3>
  <a href="https://mail.google.com/mail/?view=cm&fs=1&to=mohamedboughmadi93300@gmail.com" target="_blank"><img src="https://img.shields.io/static/v1?message=Gmail&logo=gmail&label=&color=D14836&logoColor=white&labelColor=&style=for-the-badge" height="35" alt="gmail logo" /></a>
  <a href="https://linkedin.com/in/votre-profil" target="_blank"><img src="https://img.shields.io/static/v1?message=LinkedIn&logo=linkedin&label=&color=0077B5&logoColor=white&labelColor=&style=for-the-badge" height="35" alt="linkedin logo" /></a>
</div>

