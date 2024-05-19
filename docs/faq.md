#### FAQ (Frequently Asked Questions - Foire Aux Questions (en français))
  
# FAQ
  
## Général
  
### Qu'est-ce qu'APPIPTV Freebox et HDHomeRun ?
  
APPIPTV Freebox et HDHomeRun est une application de streaming IPTV avec une interface utilisateur graphique basée sur PyQt6, permettant de visualiser des programmes TV en direct via la bibliothèque VLC media player en Python. L'application permet également la gestion des playlists M3U et la configuration des dispositifs HDHomeRun.
  
### Installation
  
#### Quels sont les prérequis pour installer l'application ?
  
Pour installer l'application, vous devez disposer de :
  
* Python 3.8 ou une version ultérieure.
* VLC media player.
* Une connexion Internet, de préférence fournie par Free Télécom pour un accès optimal aux fonctionnalités de l'application.
  
#### Comment installer l'application ?
  
1. Clonez le dépôt GitHub :
  
```bash
git clone https://github.com/Bit-Scripts/APPIPTV_Freebox_et_HDHomeRun.git
cd APPIPTV_Freebox_et_HDHomeRun
```
  
2. Installez les dépendances :
  
```bash
pip install -r requirements.txt
```
  
3. Lancez l'application :
  
```bash
python main.py
```
  
### Utilisation
  
#### Comment ajouter une playlist M3U ?
  
Vous pouvez ajouter une playlist M3U en utilisant l'interface de gestion des playlists de l'application. Accédez aux paramètres, sélectionnez "Ajouter une playlist" et suivez les instructions pour importer votre fichier M3U.

#### L'application ne parvient pas à charger certaines chaînes. Que puis-je faire ?
  
Assurez-vous que :
  
* Votre connexion Internet fonctionne correctement.
* Vous utilisez une connexion Free Télécom pour un accès optimal aux chaînes et aux données EPG.
* Le fichier M3U est correctement formaté et contient des liens valides.
  
#### Comment configurer un dispositif HDHomeRun ?
   
Pour configurer un dispositif HDHomeRun, accédez aux paramètres de l'application, sélectionnez "Configurer HDHomeRun" et entrez l'adresse IP de votre dispositif HDHomeRun. Suivez les instructions à l'écran pour terminer la configuration.
  
### Dépannage
  
#### Je reçois une erreur indiquant que libvlc.dll ne peut pas être chargé. Que faire ?
  
Cette erreur peut survenir si VLC media player n'est pas correctement installé ou si l'application ne parvient pas à trouver le fichier libvlc.dll. Assurez-vous que VLC est installé et que le chemin d'accès à VLC est correctement configuré dans votre environnement.
  
#### L'application se bloque ou ne répond pas. Comment puis-je résoudre ce problème ?
  
Essayez les étapes suivantes :
  
* Redémarrez l'application.
* Vérifiez les logs pour des messages d'erreur spécifiques.
* Assurez-vous que toutes les dépendances sont correctement installées.
* Si le problème persiste, ouvrez une issue sur le dépôt GitHub avec une description détaillée du problème et des logs pertinents.

### Contribution
  
#### Comment puis-je contribuer au projet ?
  
Les contributions sont les bienvenues ! Pour contribuer, suivez les étapes décrites dans le fichier [CONTRIBUTING.md](../.github/CONTRIBUTING.md). Vous pouvez rapporter des bugs, proposer des fonctionnalités, ou soumettre des pull requests.
   
#### Quel est le code de conduite pour les contributeurs ?
Tous les contributeurs doivent adhérer à notre [Code de Conduite](../.github/CODE_OF_CONDUCT.md). En participant à ce projet, vous acceptez de respecter ses termes.
  
### Autres
   
Où puis-je trouver plus d'informations sur l'API Freebox ?
Pour plus d'informations sur l'API Freebox, consultez la [documentation officielle de l'API Freebox](https://dev.freebox.fr/sdk/os/).
  
### J'ai une question qui n'est pas listée ici. Où puis-je obtenir de l'aide ?
   
Si vous avez des questions supplémentaires, n'hésitez pas à ouvrir une [issue sur le dépôt GitHub](https://github.com/Bit-Scripts/APPIPTV_Freebox_et_HDHomeRun/issues) ou à contacter les mainteneurs du projet.