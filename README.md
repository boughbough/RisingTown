# 🏙️ RisingTown - Simulation de Smart City

**RisingTown** est une application web de simulation urbaine gamifiée, développée dans le cadre de la Licence 3 MIAGE à l'Université Paris Nanterre.

Ce projet permet à plusieurs utilisateurs d'interagir en temps réel au sein d'une ville virtuelle persistante, en incarnant des rôles variés (Maire, Adjoint, Directeur, Citoyen) et en gérant des aspects économiques, sociaux et urbanistiques.

---

## 🚀 Fonctionnalités Clés

* **Gestion Urbaine :** Carte isométrique interactive (construction, déplacement, rotation de bâtiments).
* **Système de Rôles :**
    * 🏛️ **Maire :** Gestion du budget, urbanisme, fiscalité et justice.
    * 🛡️ **Adjoint :** Maintenance des bâtiments (réparations), communication officielle.
    * 👔 **Directeur :** Gestion d'entreprise (recrutement, licenciement).
    * 🙋 **Citoyen :** Recherche d'emploi, logement, gestion de budget personnel.
* **Économie Temps Réel :** Salaires, impôts progressifs, loyers et consommation.
* **Mécaniques de Vie :** Jauges de Santé (fatigue/hôpital) et de Bonheur (fêtes/émeutes).
* **Social & Justice :** Chat en direct (téléphone), système de plaintes, casier judiciaire et prison.

---

## 🛠️ Stack Technique

* **Langage :** Python 3.9+
* **Framework Backend :** Django 5.2.8
* **Base de Données :** SQLite3
* **Frontend :** HTML5, CSS3, JavaScript (AJAX/Fetch API)
* **Hébergement :** PythonAnywhere

---

## 💻 Guide d'Installation (Local)

Suivez ces étapes pour lancer le projet sur votre machine.

### 1. Cloner le projet
Récupérez le code source depuis le dépôt Git :

```bash
git clone [https://github.com/boughbough/RisingTown.git](https://github.com/boughbough/RisingTown.git)
cd RisingTown
````

### 2\. Créer l'environnement virtuel

Il est nécessaire d'isoler les dépendances du projet.

**Sous Windows :**

```bash
python -m venv venv
venv\Scripts\activate
```

**Sous Mac/Linux :**

```bash
python3 -m venv venv
source venv/bin/activate
```

*(Une fois activé, vous devriez voir `(venv)` au début de votre ligne de commande).*

### 3\. Installer les dépendances

Installez Django et les bibliothèques requises via `pip` :

```bash
pip install -r requirements.txt
```

### 4\. Initialiser la Base de Données

Le projet est fourni avec une base de données pré-configurée, mais il est recommandé d'appliquer les migrations pour s'assurer de la cohérence du schéma :

```bash
python manage.py migrate
```

### 5\. Créer un Super-Utilisateur (Le Maire)

Pour accéder à l'interface d'administration et posséder les droits de Maire dans la simulation :

```bash
python manage.py createsuperuser
```

*(Suivez les instructions pour définir un nom d'utilisateur et un mot de passe).*

-----

## ▶️ Lancement du Serveur

Une fois l'installation terminée, lancez le serveur de développement :

```bash
python manage.py runserver
```

Ouvrez votre navigateur web et accédez à l'adresse suivante :
 **127.0.0.1:8000**

-----

## 📂 Structure du Projet

  * `myapp/` : Cœur logique de l'application (Views, Models, Forms, Migrations).
  * `myproject/` : Configuration globale (Settings, URLs, WSGI).
  * `templates/` : Interfaces HTML (Dashboard, Carte, Login, Admin).
  * `static/` : Fichiers statiques (CSS, Javascript, Images/Sprites).
  * `db.sqlite3` : Base de données locale.
  * `manage.py` : Utilitaire de gestion Django.

-----

## 👥 Auteurs

Projet réalisé par l'équipe **RisingTown** (L3 MIAGE) :

   * **Mohamed Boughmadi** (Architecte Logiciel & Back-End)
   * **Mohamet Thiam** (Scrum Master & Front-End)
   * **Faiz Djama** (Gestionnaire BDD & Intégration)
   * **Joël Kpinso-Folly** (DevOps & Assurance Qualité)
   * **Hamid Adenle** (UI/UX Designer & Équilibrage Économique)

-----

*Décembre 2025 - Université Paris Nanterre*

```
