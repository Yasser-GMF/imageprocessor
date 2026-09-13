[app]

title = Image Processor
package.name = imageprocessor
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy,requests,arabic-reshaper,python-bidi,plyer

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE


[buildozer]

log_level = 2
warn_on_root = 1
