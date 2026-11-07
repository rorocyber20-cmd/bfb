[app]

title = BFB Reminder
package.name = bfbreminder
package.domain = org.bfb

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf

version = 0.2

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,plyer,certifi,pyjnius,android,arabic-reshaper,python-bidi==0.4.2,six

orientation = portrait
fullscreen = 0

services = reminder:service.py:foreground

# الأيقونة وشاشة التحميل
icon.filename = icon.png
presplash.filename = presplash.png
android.presplash_color = #3919CB

# Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.permissions = POST_NOTIFICATIONS, VIBRATE, WAKE_LOCK, INTERNET, SCHEDULE_EXACT_ALARM, USE_EXACT_ALARM, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE

# تثبيت إصدار python-for-android
p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
