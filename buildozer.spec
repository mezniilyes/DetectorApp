[app]

# (str) Titre de votre application sur le smartphone
title = PRO-GEORADAR 3D

# (str) Nom du package (sans espaces ni caractères spéciaux)
package.name = progeoradar3d

# (str) Domaine de l'organisation (identifiant unique)
package.domain = tn.smart.detector

# (str) Répertoire où se trouve le code source (le point '.' signifie le dossier actuel)
source.dir = .

# (list) Extensions de fichiers à inclure dans la compilation
source.include_exts = py,png,jpg,kv,atlas

# (str) Version de votre application
version = 1.0.0

# (list) Dépendances logicielles CRITIQUES pour ce projet
# python3 et kivy sont la base, pyserial est indispensable pour le module Bluetooth HC-05
requirements = python3, kivy, pyserial

# (list) Autorisations Android indispensables pour communiquer avec le matériel
# Nous activons le Bluetooth standard, l'administration Bluetooth et l'accès réseau
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, INTERNET, ACCESS_FINE_LOCATION

# (int) Orientation de l'écran (0 = Portrait, 1 = Paysage)
# Pour une interface de radar de sol avec tableau de bord complet, le mode paysage (landscape) est idéal
orientation = landscape

# (bool) Indique si l'application doit s'exécuter en plein écran
fullscreen = 1

# (str) Format de l'architecture cible (armeabi-v7a pour anciens téléphones, arm64-v8a pour les modernes)
android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a

# (bool) Autoriser le débogage de l'application
android.debug = True

[buildozer]
log_level = 2
build_dir = ./.buildozer

# (str) Chemin du dossier de stockage des outils Android
build_dir = ./.buildozer
