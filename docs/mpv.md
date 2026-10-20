# Lecteur intégré libmpv

Le lecteur utilise `python-mpv==1.0.8` (module `mpv`) et la render API OpenGL
de libmpv. `src/MpvWidget.py` possède le lecteur et son contexte de rendu ;
`MainWindow` conserve la sélection de chaîne, les logos et l'EPG. Aucun processus
mpv externe, identifiant de fenêtre X11 ou serveur IPC n'est utilisé.

## Lancement depuis ce worktree

```bash
conda activate iptvapp
cd /home/paul/.codex/worktrees/8ab0/IPTVAPP
python -s -m pip install -r requirements.txt
QT_QPA_PLATFORM=wayland python -s main.py
```

Le `-s` évite les paquets de `~/.local`. Qt choisit normalement le backend de la
session ; la variable ci-dessus impose Wayland pour la vérification. Le checkout
original n'est pas modifié. Les modifications manuelles présentes au départ sont
conservées dans ce worktree.

Installer aussi la bibliothèque système **libmpv** (`libmpv.so.2` sur la machine
validée), les pilotes OpenGL/EGL et le plugin Qt Wayland compatible avec le Qt de
PyQt6. `pip` installe le binding, pas libmpv. Sous Debian/Ubuntu, la bibliothèque
est généralement fournie par `libmpv2`. Une erreur d'import de `mpv` doit conduire
à vérifier ces dépendances. Les specs PyInstaller des trois plateformes embarquent maintenant libmpv
via un chemin explicite `IPTV_LIBMPV` ; voir la section distribution ci-dessous.

## Réseau

Un seul cœur mpv charge les URL réellement sélectionnées dans la playlist.
`loadfile` remplace le flux précédent. RTSP utilise UDP avec
`demuxer-lavf-o=min_port=8784,max_port=8785`, comme le test externe précédent.
Aucune règle de pare-feu n'est modifiée. Cette paire peut être insuffisante pour
certains flux multipistes : relever les besoins réels du flux avant de changer
la plage et les règles. Les pertes RTP et corruptions H.264/AAC sont distinctes
du rendu Qt. Fermer tout ancien mpv de test avant de lancer l'application pour
éviter une concurrence sur ces ports.

## Validation ciblée

Avec une session graphique accessible et ffmpeg :

```bash
ffmpeg -loglevel error -f lavfi -i color=c=red:s=320x180:r=25 -t 8 -c:v mpeg4 -y /tmp/iptv-render-test.mp4
QT_QPA_PLATFORM=wayland LIBGL_ALWAYS_SOFTWARE=1 IPTV_TEST_VIDEO=/tmp/iptv-render-test.mp4 python -s -m unittest discover -s tests -v
```

Le test utilise Qt et libmpv réels ; seules les requêtes playlist/EPG sont
remplacées pour isoler le lecteur. Il vérifie la couleur rendue, l'URL, les
commandes pause/volume, le changement de chaîne, l'erreur de chargement, la
reprise et le nettoyage idempotent. Sans `IPTV_TEST_VIDEO`, il est explicitement
ignoré. La validation réseau doit se faire séparément avec la Freebox.

Validation du 20 octobre 2026 : test réussi sous Wayland avec le Python 3.11 de
Conda `iptvapp`, libmpv système et binding installé temporairement dans `/tmp`.
France 2 (`service=201`) a produit une image dans le framebuffer Qt et une
position de lecture progressant. Le pipeline GPU avancé produisait parfois une
image noire ; `gpu-dumb-mode=yes` utilise désormais le rendu OpenGL simplifié.
Les tests finaux passent sous Wayland avec le pilote par défaut et le rendu
logiciel. L'état GL partagé avec Qt est réinitialisé avant chaque rendu.
Des avertissements EGL/Mesa restent présents. En cas de problème de pilote,
`LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=wayland python -s main.py` permet de
comparer avec le rendu logiciel. Les erreurs réseau H.264/AAC restent présentes.
L'audio audible, toutes les chaînes, les flux multipistes et les exécutables
packagés ne sont pas validés par ce test.

## Cycle de vie

Les callbacks mpv émettent des signaux Qt ; ils ne manipulent pas les widgets.
Le callback de résolution GL reste référencé tant que le contexte existe.
Le callback de rendu reste vivant jusqu'au retour de `free()` pour éviter une
course avec les threads mpv. Le contexte est libéré avec le contexte Qt courant,
puis le cœur mpv est terminé à la fermeture ou à `aboutToQuit`. Une erreur de
chaîne affiche une seule page réutilisable et ne recrée pas le widget OpenGL.

Références primaires :
- [python-mpv et dépendances](https://github.com/jaseg/python-mpv)
- [Binding render API](https://github.com/jaseg/python-mpv/blob/main/mpv.py)
- [Cycle de vie QOpenGLWidget](https://doc.qt.io/qt-6/qopenglwidget.html)

## Distribution

Les specs utilisent `specs/mpv_build.py` et un runtime hook qui résout la
bibliothèque embarquée avant l'import du binding. Sur chaque OS, fournir une
bibliothèque libmpv native de même architecture que Python, puis construire :

```bash
# Linux (adapter le chemin système si nécessaire)
IPTV_LIBMPV=/usr/lib/x86_64-linux-gnu/libmpv.so.2 python -s -m PyInstaller specs/main-linux.spec
# macOS : IPTV_LIBMPV=$(brew --prefix mpv)/lib/libmpv.dylib
# Windows PowerShell : $env:IPTV_LIBMPV='C:\mpv\mpv-2.dll'
```

PyInstaller collecte récursivement les dépendances natives résolues de libmpv
sur Linux et macOS. Sous Windows, les DLL voisines de la bibliothèque sont aussi
incluses. Les hooks PyInstaller PyQt6 collectent Qt OpenGL et ses plugins de
plateforme ; le workflow vérifie leur présence dans le paquet final pour chaque
OS (Wayland, Windows ou Cocoa), ainsi que la bibliothèque libmpv elle-même.
Un smoke test charge la bibliothèque exacte choisie avant le build : une mauvaise
architecture ou une dépendance introuvable fait échouer ce contrôle.

### Source Windows reproductible

La variable externe `MPV_WINDOWS_LIB_URL` n'est plus nécessaire. Le fichier
`specs/windows-mpv.json` fixe une archive **x86_64 standard**, sa version, son URL
et son SHA-256. Il s'agit du build tiers shinchiro référencé par la
[page d'installation de mpv](https://mpv.io/installation/), et non d'un binaire
officiel du projet mpv. La version épinglée est `20261020`, commit mpv
`6a262d11f6`. Le téléchargement réel de 31 611 843 octets a été vérifié contre le
SHA-256 publié dans les métadonnées de la release GitHub et contient
`libmpv-2.dll` au format PE x86_64.

```powershell
# 7-Zip doit être disponible dans PATH (fourni par windows-latest).
$dll = python specs/fetch_windows_mpv.py --output "$env:TEMP/iptv-mpv"
$env:IPTV_LIBMPV = $dll
python -s specs/smoke_libmpv.py
python -s -m PyInstaller specs/main-windows.spec
python -s specs/verify_bundle.py dist/APPIPTV.exe
```

Le script vérifie le SHA-256 avant extraction et rejette une DLL d'une autre
architecture. Pour mettre à jour la source, choisir une nouvelle archive
`mpv-dev-x86_64` dans les releases du fournisseur, vérifier son contenu et son
SHA-256 publié, puis mettre à jour le manifeste dans Git. Il ne télécharge pas
une URL `latest` variable à chaque build.

### Workflow de publication

Les deux commits distants de mise à jour des artefacts sont intégrés. Les actions
sont désormais épinglées par commit : upload-artifact `v7.0.2` et
download-artifact `v8.0.2`, compatibles avec les artefacts de la génération v4+
et les runners GitHub hébergés actuels. Le job de publication reçoit explicitement
`contents: write` ; les jobs de build gardent `contents: read`. Aucune variable
ni permission d'administration d'organisation n'est requise pour la source DLL.
Validation locale de ce lot : workflow analysé par actionlint 1.7.12 ; six
contrôles ciblés de distribution réussis ; archive Windows réellement téléchargée,
SHA-256 et PE x64 vérifiés ; paquet Linux réellement construit avec PyInstaller
6.22.3. Son archive contient le binding Python `mpv`, libmpv, libavcodec,
libavformat, libass, Qt OpenGL/OpenGLWidgets et le plugin Qt Wayland. Le paquet
Linux a également démarré sous Wayland en locale française, avec
rafraîchissement complet des 928 logos. Les binaires Windows et macOS doivent
encore être construits et exécutés sur leurs OS
respectifs avant de considérer leur fonctionnement intégral validé.

## Catalogue et logos Freebox

`src/FreeboxLogos.py` utilise l'endpoint déjà employé par le projet,
`/api/v8/tv/channels`, puis télécharge les URL `logo_url` fournies par le routeur
(sans construire d'endpoint image supposé). Le 20 octobre 2026 : **928 entrées,
928 logos retéléchargés, 0 échec** ; fichiers dans `assets/logos/freebox` et
catalogue indexé par UUID. Cet endpoint et les images ont répondu sans demande
d'authentification sur le routeur testé.

À chaque lancement, tous les logos sont rafraîchis dans un thread, dans
`<config_path>/freebox-logos`. Les écritures sont atomiques ; une erreur réseau
ou une image invalide conserve le fichier précédent. Le cache utilisateur est
prioritaire, puis le catalogue/logo embarqué, puis les anciens logos et l'icône
générique. Aucun accès HDHomeRun n'est lancé. Les logos sont appliqués aux boutons,
aux pages d'erreur et aux fiches programme ; la prochaine ouverture du guide EPG
utilise les nouveaux chemins. Les correspondances suivent le nom normalisé,
le nom court et les troncatures uniques ; les doublons privilégient un service
unique explicitement annoncé par l'API, sinon restent ambigus. Aucun remplacement
de chaîne n'est déduit de l'ancien nom. Les anciens fichiers restent disponibles
uniquement pour le repli hors réseau.

La playlist réelle contient **494 chaînes distinctes**, toutes ajoutées à la
grille ; les variantes de qualité sont fusionnées en préférant HD, standard,
bas débit, puis auto. Le mode auto seul est maintenant conservé. La limite à
deux chaînes appartient uniquement au test isolé, pas au produit. Le catalogue
API est plus large que la playlist et ne doit pas être confondu avec le nombre
de chaînes lisibles ou incluses dans un abonnement.

Le contrôle réel des correspondances donne 493 UUID EPG non ambigus pour les
494 boutons. `TLC` reste ambigu : le routeur annonce deux UUID avec le même nom
et un service actif dans les deux cas. Les deux logos ont été téléchargés,
mais l'application garde le repli pour ce nom plutôt que de choisir un UUID
arbitrairement. Les anciennes références au lecteur précédent sont conservées
uniquement dans la ligne historique de `docs/CHANGELOG.md`.

## Correction du démarrage en locale française

Qt peut rétablir la locale système lors de la création de `QApplication`, après
l'import de `python-mpv`. Le correctif exécuté à l'import du binding ne suffit
alors plus. `MpvWidget` fixe maintenant `LC_NUMERIC` à `C` immédiatement avant
`mpv.MPV()` ; les autres catégories de locale restent inchangées. C'est une
[exigence de libmpv](https://github.com/mpv-player/mpv/blob/master/include/mpv/client.h).

Le crash signalé a été reproduit avec `LANG=fr_FR.UTF-8 LC_ALL=fr_FR.UTF-8` dans
Conda `iptvapp` et le binding installé dans cet environnement : message
`Non-C locale`, puis SIGSEGV dans `mpv_set_option`. Après correction, le démarrage
complet (splash, thème, playlist réelle, rafraîchissement des logos et fenêtre)
a été vérifié avec fermeture automatique propre : contexte GL valide et 494
chaînes. Les huit tests passent en locale française, dont le test de régression
`tests/test_mpv_locale.py` exécuté dans un sous-processus pour détecter également
un crash natif. Le pilote GPU matériel n'est pas accessible dans l'environnement
de validation ; cette correction porte sur la locale, indépendamment du GPU.
Aucune variable de locale supplémentaire n'est nécessaire dans la commande de
lancement habituelle.

## Dimensionnement des erreurs

Les messages d'erreur sont du texte brut avec retour à la ligne, y compris les
URL sans espaces grâce à des possibilités de coupure invisibles. Une zone à
défilement vertical conserve l'intégralité des longs messages sans imposer leur
largeur minimale au `QStackedWidget` et à la fenêtre. Le test de la fenêtre
complète avec le thème de l'application vérifie un message comprenant une URL
de 3 000 caractères : largeur conservée à 1 000 px, redimensionnement à 820 px,
liste de chaînes maintenue à 300 px, défilement vertical sans débordement
horizontal, puis retour à une image vidéo après une sélection valide.

## Cadre TV et superpositions

`src/VideoArea.py` centre un cadre TV 16:9 dans l'espace disponible. La fenêtre
reste librement redimensionnable : son chrome et les commandes ne sont pas
forcés au même ratio. mpv conserve le ratio de la source ; une source 4:3 a des
bandes noires latérales dans le cadre TV. La liste des chaînes est un enfant
superposé, animé au survol ; son ouverture ne change pas la géométrie vidéo.
Les informations de chaîne et du programme actuel se superposent en bas, avec
défilement si nécessaire. Le guide EPG complet garde une zone distincte.

Les erreurs d'accès et d'abonnement restent des états normaux : la présence
dans le catalogue ne garantit pas la lecture. Le message d'erreur reste dans
le cadre TV, avec retour à la ligne et défilement. Aucun droit n'est modifié.
Le test d'intégration vérifie géométrie inchangée avec liste ouverte/fermée et
fiche programme visible, redimensionnement large/court, message long et reprise.
Pour vérifier aussi les pixels d'une source 4:3 bleue :

```bash
ffmpeg -loglevel error -f lavfi -i color=c=blue:s=320x240:r=25 -t 8 -c:v mpeg4 -y /tmp/iptv-4-3.mp4
QT_QPA_PLATFORM=wayland IPTV_TEST_VIDEO=/tmp/iptv-render-test.mp4 IPTV_TEST_4_3=/tmp/iptv-4-3.mp4 python -s -m unittest discover -s tests -v
```

## Workflows indépendants par OS

Les workflows `build-linux.yml`, `build-windows.yml` et `build-macos.yml` sont
indépendants : chacun se lance sur `main` ou manuellement pour un tag/commit.
Leur logique commune reste dans `build-platform.yml` (workflow réutilisable,
sans matrice). L'échec d'un OS n'annule pas les autres. Chaque run conserve son
artefact et le journal de la révision exacte des sources. Les contrôles et outils
CI viennent du commit du workflow ; les sources de l'application viennent de
`source_ref`.

```bash
gh workflow run build-linux.yml --ref main -f source_ref=v1.5.0
gh workflow run build-windows.yml --ref main -f source_ref=v1.5.0
gh workflow run build-macos.yml --ref main -f source_ref=v1.5.0
```

Ces reconstructions ne déplacent aucun tag et ne créent aucune release.
`release.yml` est l'unique orchestrateur de publication sur les futurs tags :
il appelle les trois workflows OS dans le même run, puis publie seulement si les
trois réussissent. Les artefacts téléchargés appartiennent donc à la même révision
et au même run ; ils ne sont pas choisis parmi des constructions indépendantes
potentiellement différentes.

La reconstruction manuelle du tag public `v1.5.0` avec les contrôles corrigés a
réussi pour les trois OS : run GitHub Actions `39384077044`. Les trois paquets
sont disponibles comme artefacts de ce run ; aucune nouvelle release n'a été
créée et le tag pointe toujours sur `b101d5e`.
