[app]

title = BFB Reminder
package.name = bfbreminder
package.domain = org.bfb

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf

version = 0.1

requirements = python3,kivy==2.3.0,plyer,certifi,pyjnius

orientation = portrait
fullscreen = 0

# Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = POST_NOTIFICATIONS, VIBRATE, WAKE_LOCK, INTERNET
android.allow_backup = True

[buildozer]

log_level = 2
warn_on_root = 1