[app]

title = PRO-GEORADAR 3D
package.name = progeoradar3d
package.domain = tn.smart.detector

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 1.0.0

# Dependances minimales pour valider la compilation
requirements = python3,kivy

orientation = landscape
fullscreen = 1

# Permissions minimales ; Bluetooth sera ajoute apres validation
android.permissions = INTERNET
android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

android.debug = True

[buildozer]

log_level = 2
build_dir = ./.buildozer
