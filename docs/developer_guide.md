#### Developer Guide
# Developer Guide
  
## Introduction
  
Bienvenue dans le guide du développeur de APPIPTV Freebox et HDHomeRun. Ce document vous fournira une vue d'ensemble de l'architecture du projet, des principales fonctionnalités, des dépendances, et des instructions sur la manière de contribuer efficacement.
  
## Table des matières
1. Architecture du projet
2. Dépendances
3. Configuration de l'environnement de développement
4. Principales fonctionnalités
5. Structure du code
6. Tests et qualité du code
7. Contribuer au projet
  
## Architecture du projet
  
L'application APPIPTV Freebox et HDHomeRun est conçue pour fournir une interface utilisateur graphique (GUI) pour le streaming IPTV à l'aide de PyQt6 et de la bibliothèque VLC en Python. Voici un aperçu de l'architecture du projet :
  
* **GUI** : Basée sur PyQt6 pour l'interface utilisateur.
* **Streaming** : Intégration de VLC pour le streaming des chaînes TV.
* **API Freebox** : Utilisation de l'API Freebox pour récupérer les informations sur les chaînes TV et les données EPG.
  
## Dépendances 
   
L'application dépend des bibliothèques Python suivantes, spécifiées dans `requirements.txt` :

```plaintext
PyQt6
requests
python-vlc
pytz
qdarkstyle
```
  
## Configuration de l'environnement de développement
  
### Prérequis
  
* Python 3.8 ou une version ultérieure doit être installé sur votre machine.
  
* VLC media player doit être installé pour le support du streaming.
  
### Installation
  
Clonez le dépôt GitHub et installez les dépendances :
```bash
git clone https://github.com/Bit-Scripts/APPIPTV_Freebox_et_HDHomeRun.git
cd APPIPTV_Freebox_et_HDHomeRun
pip install -r requirements.txt
```
### Configuration
  
Assurez-vous que les chemins d'accès à VLC sont correctement configurés dans votre environnement.
   

## Principales fonctionnalités
* **Streaming IPTV** : Visualisation des programmes TV en direct.
* **Gestion des playlists M3U** : Chargement et gestion des playlists.
* **EPG** : Affichage du guide des programmes TV.
* **Configuration des appareils HDHomeRun** : Paramétrage des adresses IP pour les appareils HDHomeRun.
  
## Structure du code
  
Voici une vue d'ensemble de la structure des fichiers et des répertoires du projet :
  
```arduino
IPTVAPP/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── demande-de-fonctionnalité.md
│   │   ├── rapport-de-bug.md
│   ├── PULL_REQUEST_TEMPLATE/
│   │   ├── pull_request_template.md
│   ├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
├── assets/
│   ├── image/
│   ├── logos/
├── build/
├── dist/
├── docs/
│   ├── user_guide.md
│   ├── developer_guide.md
│   ├── api_documentation.md
│   ├── faq.md
│   ├── CHANGELOG.md
├── src/
│   ├── CustomSplashScreen.py
│   ├── DataLoadThread.py
│   ├── EPGTable.py
│   ├── ImageCache.py
│   ├── MainWindow.py
│   ├── SemiTransparentBlurWidget.py
│   ├── SettingsDialog.py
│   ├── VLCStateMonitor.py
├── tests/
│   ├── test_MainWindow.py
│   ├── test_SettingsDialog.py
├── main.py
├── README.md
├── README-en.md
├── requirements.txt
└── setup.py
```
  
### Description des principaux fichiers et répertoires
* **main.py** : Point d'entrée principal de l'application.
* **src/** : Contient les fichiers sources du projet.
    * **MainWindow.py** : Contient la définition de la fenêtre principale de l'application.
    * **EPGTable.py** : Gère l'affichage du guide des programmes TV.
    * **SettingsDialog.py** : Gère la boîte de dialogue des paramètres.
    * **VLCStateMonitor.py** : Surveille l'état de VLC pour le streaming.
* **tests/** : Contient les tests unitaires pour les composants principaux.
* **assets/** : Contient les ressources graphiques (images et logos).
* **docs/** : Contient la présente documentation pour mieux comprendre le projet et ses ressources.
* **.github/** : Contient les modèles pour les issues et les pull requests, ainsi que les fichiers de contribution et de code de conduite.
  
## Tests et qualité du code
  
### Exécution des tests
  
Les tests unitaires sont situés dans le répertoire tests/. Pour exécuter les tests, utilisez pytest :
  
```bash
pytest tests/
```
  
### Linting
Utilisez `flake8` pour vérifier la qualité du code :
  
```bash
flake8 src/
```

## Contribuer au projet
  
Les contributions sont les bienvenues ! Pour contribuer, veuillez suivre les étapes suivantes :
  
1. **Fork** le projet sur GitHub.
2. **Clonez** votre fork sur votre machine locale.
3. **Créez** une nouvelle branche pour vos modifications.
4. **Effectuez** vos modifications.
5. **Committez** vos changements avec des messages de commit explicatifs.
6. **Poussez** votre branche sur votre fork.
7. **Ouvrez** une pull request de votre branche vers la branche principale du projet original.
8. **Décrivez** en détail les modifications proposées et toute autre information pertinente.
  
Pour plus de détails, veuillez consulter le fichier [CONTRIBUTING.md](../.github/CONTRIBUTING.md).
  
### Code de Conduite
  
Nous attendons de tous les contributeurs qu'ils adhèrent à notre [Code de Conduite](../.github/CODE_OF_CONDUCT.md). En participant à ce projet, vous acceptez de respecter ses termes.
  
## Remerciements
  
Merci à tous ceux qui contribuent à ce projet, que ce soit par des suggestions, des contributions directes au code ou par des discussions utiles. Votre aide est essentielle pour améliorer continuellement ce projet.

