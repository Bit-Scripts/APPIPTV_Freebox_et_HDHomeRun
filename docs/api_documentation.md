# API Documentation

## Freebox TV Channels API

Freebox propose une API accessible à ses clients, permettant de développer des applications compagnons pour smartphones ou de fournir une alternative à l'application web FreeboxOS. Vous trouverez ici des exemples complets de l'utilisation de l'API dans ce projet. Pour plus de détails, vous pouvez consulter la [documentation officielle de l'API Freebox](https://dev.freebox.fr/sdk/os/).


### Récupérer les UUIDs des chaînes TV

La méthode `get_ordered_uuids` permet de récupérer et de trier les UUIDs des chaînes TV à partir de l'API Freebox.

#### Description

Cette méthode envoie une requête HTTP GET à l'URL `http://mafreebox.freebox.fr/api/v8/tv/channels` pour obtenir la liste des chaînes TV. Elle analyse la réponse JSON pour extraire les informations des chaînes, trie les chaînes par numéro de chaîne et retourne une liste de tuples contenant le numéro de chaîne, le nom de la chaîne, le chemin de l'icône et l'UUID de la chaîne.

#### Exemple de code

```python
import os
import requests
import logging

class MyTVApp:
    def __init__(self):
        self.channels_name = {
            "france 2": (2, "path/to/france_2_logo.png"),
            "france 3": (3, "path/to/france_3_logo.png"),
            # Ajoutez d'autres chaînes ici
        }
        self.application_path = "/path/to/application"
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('my_tv_app')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def get_ordered_uuids(self):
        channels_list_url = 'http://mafreebox.freebox.fr/api/v8/tv/channels'
        try:
            response = requests.get(channels_list_url)
            response.raise_for_status()
            data = response.json()
            ordered_uuids = []
            channel_number = 0
            for uuid, info in data['result'].items():
                channel_name = info['name']
                if channel_name.lower() in self.channels_name:
                    channel_number, icon_path = self.channels_name[channel_name.lower()]
                    ordered_uuids.append((channel_number, channel_name, icon_path, uuid))
                if channel_name == "France 3" and channel_number != 301:
                    ordered_uuids.append(("3", channel_name, os.path.join(self.application_path, 'assets/logos/France_3.png'), uuid))
                    
            ordered_uuids = sorted(ordered_uuids, key=lambda x: int(x[0]))
            return ordered_uuids
        except requests.RequestException as e:
            self.logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return []
```

### Charger les données de l'EPG
La méthode `load_epg_data` permet de récupérer les données de l'EPG (Electronic Program Guide) sur une période de temps spécifiée.

#### Description
Cette méthode envoie des requêtes HTTP GET à l'URL `http://mafreebox.freebox.fr/api/v8/tv/epg/by_time/{timestamp}` pour obtenir les données de l'EPG à des intervalles horaires. Elle analyse les réponses JSON et agrège les données pour chaque UUID de chaîne dans un dictionnaire.

#### Exemple de code

```python
import time
import requests
import logging

class MyTVApp:
    def __init__(self):
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('my_tv_app')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def load_epg_data(self):
        now = int(time.time())
        two_hours = 2 * 60 * 60
        eighteen_hours = 18 * 60 * 60
        all_data = {}
        try:
            for timestamp in range(now - two_hours, now + eighteen_hours, 3600):  # Ajout de pas d'une heure
                url = f"http://mafreebox.freebox.fr/api/v8/tv/epg/by_time/{timestamp}"
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
                if 'result' in data:
                    for uuid, value in data['result'].items():
                        if uuid in all_data:
                            all_data[uuid].update(value)  # Mise à jour des données existantes
                        else:
                            all_data[uuid] = value
            return all_data
        except requests.RequestException as e:
            self.logger.error(f"Failed to load EPG data: {e}", exc_info=True)
            return {}
```
  
### Gestion des erreurs
Les méthodes `get_ordered_uuids` et `load_epg_data` gèrent les erreurs de réseau en utilisant un bloc `try-except`. Si une erreur survient lors de la requête ou du traitement des données, l'erreur est enregistrée dans les logs et une structure vide (liste ou dictionnaire) est retournée.

## Conclusion
En documentant vos méthodes et en fournissant des exemples de code, vous facilitez l'utilisation de votre projet pour d'autres développeurs. Cela améliore la compréhension et l'adoption de votre projet, tout en facilitant les contributions futures.