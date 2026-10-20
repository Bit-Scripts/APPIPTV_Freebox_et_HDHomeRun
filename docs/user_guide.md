# Guide de l'utilisateur

## Introduction

Bienvenue dans IPTVAPP ! Ce guide vous aidera à configurer et utiliser l'application.

## Installation

### Prérequis

- Python 3.11 ou supérieur
- libmpv

### Étapes d'installation

1. Clonez le dépôt :
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
    python -s main.py
    ```

## Utilisation

### Interface principale

- **Liste des chaînes** : Visualisez toutes les chaînes disponibles.
- **Paramètres** : Configurez les adresses IP pour les dispositifs HDHomeRun.
- **Guide des programmes** : Consultez les programmes TV en direct via Free Télécom.

## Résolution des problèmes

### Problèmes courants

- **Erreur de chargement de `mpv-2.dll`** : Assurez-vous que libmpv est installé et que les chemins d'accès sont correctement configurés.
