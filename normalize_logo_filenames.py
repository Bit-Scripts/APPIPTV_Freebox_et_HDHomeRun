import requests
import os
from unidecode import unidecode

def download_and_save_logos(logo_folder='assets/logos'):
    if not os.path.exists(logo_folder):
        os.makedirs(logo_folder)

    response = requests.get('http://mafreebox.freebox.fr/api/v8/tv/channels')
    data = response.json()

    for uuid, channel_info in data['result'].items():
        channel_name = channel_info['name']
        logo_url = channel_info.get('logo_url')

        # Continuez uniquement si le logo existe
        if logo_url:
            logo_url = f"http://mafreebox.freebox.fr{logo_url}"
            sanitized_channel_name = unidecode(channel_name.lower()).replace(' ', '_').replace('-', '_').replace("'", '').replace("/", '-')
            response = requests.get(logo_url)

            # Vérifiez la taille du contenu de la réponse
            if len(response.content) < 100:  # 100 Ko = 100 * 1024 octets
                print(f"Logo de {channel_name} ignoré car il est trop petit ({len(response.content)} octets).")
                continue

            if response.status_code == 200:
                filename = f"{sanitized_channel_name}.png"
                filepath = os.path.join(logo_folder, filename)

                # Écrivez le contenu de l'image dans le fichier local
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"Logo de {channel_name} sauvegardé sous {filepath}")
            else:
                print(f"Impossible de télécharger le logo de {channel_name}")
        else:
            print(f"Aucun logo disponible pour {channel_name}")

# Appel de la fonction
download_and_save_logos('assets/logos')
