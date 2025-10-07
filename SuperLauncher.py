import sys
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QButtonGroup,
    QLineEdit, QComboBox, QProgressBar, QSpacerItem, QSizePolicy,
    QMessageBox, QScrollArea, QDialog, QCheckBox, QFormLayout,
    QListWidget, QListWidgetItem, QRadioButton, QFileDialog,
)
from PyQt6.QtGui import QPixmap, QCursor, QIcon
from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command
from packaging import version
from tqdm import tqdm
from pypresence import Presence
from random_username.generate import generate_username
from uuid import uuid1
import subprocess
import requests
import threading
from pathlib import Path
import json
import shutil
import time

CONFIG_FILE = "settings.json"

translations = {
    "ru": {
        # --- SettingsPage ---
        "Theme:": "Тема:",
        "Language:": "Язык:",
        "Minecraft launch mode:": "Способ запуска Minecraft:",
        "minecraft-launcher-lib (default)": "minecraft-launcher-lib (по умолчанию)",
        "Java (specify path)": "Java (указать путь)",
        "Java path (if Java is selected):": "Путь к Java (если выбран Java):",
        "Browse Java path": "Выбрать путь к Java",
        "Page backgrounds:": "Фоны страниц:",
        "Save settings": "Сохранить настройки",

        # --- MinecraftPage ---
        "Play": "Играть",
        "Username": "Имя пользователя",
        "No versions available": "Версии недоступны",

        # --- ModsPage ---
        "Mods from Modrinth": "Моды из Modrinth",
        "Search mod...": "Найти мод...",
        "Open mods folder": "Открыть папку модов",
        "Delete all mods": "Удалить все моды",
        "Error": "Ошибка",
        "Downloading mod": "Загрузка мода",
        "Done": "Готово",
        "All mods deleted": "Удалено модов",
        "No available versions": "Нет доступных версий",
        "No supported builds": "Нет поддерживаемых билдов",
        "File not found": "Файл не найден",
        "Install mod": "Установка мода",
        "Minecraft version and loader:": "Версия Minecraft и ядро:",

        # --- NewsPage ---
        "News": "Новости",
        "2025-08-12 v1.4.0.7: Discord RPC added": "2025-08-12 v1.4.0.7: Добавлен Discord RPC",
        "2025-07-24 v1.4.0.5: Added support for downloading mods from Modrind and launcher settings": "2025-07-24 v1.4.0.5: Добавлена поддержка скачивания модов из Modrind и настроек лаунчера",
        "2025-07-23 v1.4.0.4: Added ability to create and manage local Minecraft servers directly from the launcher...": "2025-07-23 v1.4.0.4: Добавлена возможность создавать и управлять локальными Minecraft-серверами прямо из лаунчера...",
        "2025-07-23 v1.4.0.3: New design added and code restored": "2025-07-23 v1.4.0.3: Добавлен новый дизайн и восстановлен код",
        "2025-06-26 v1.4.0.2: New design added, but code lost": "2025-06-26 v1.4.0.2: Добавлен новый дизайн, но утерян код",
        "2025-06-26 v1.4.0.1: Bugs fixed, but design outdated": "2025-06-26 v1.4.0.1: Исправлены баги, но дизайн устаревший",
        "2025-06-26 v1.4.0.0: Bugs fixed, but design outdated": "2025-06-26 v1.4.0.0: Исправлены баги, но дизайн устаревший",
        "2025-06-26 v1.3: Launcher will exit beta in the next release": "2025-06-26 v1.3: Лаунчер выйдет из бета в следующем релизе",
        "No news available": "Новости недоступны",

        # --- HomePage ---
        "Welcome to SuperLauncher!": "Добро пожаловать в SuperLauncher!",

        # --- ServersPage ---
        "🖧 Minecraft Servers": "🖧 Серверы Minecraft",
        "Create your own server": "Создать свой сервер",
        "Server Name": "Имя сервера",
        "IP or domain": "IP или домен",
        "Add server": "Добавить сервер",
        "Manage": "Управление",
        "Delete": "Удалить",
        "Delete confirmation": "Подтверждение удаления",
        "Are you sure you want to delete the server '{server_name}'? This action cannot be undone.": "Вы уверены, что хотите удалить сервер '{server_name}'? Это действие нельзя отменить.",
        "Folder in use": "Папка занята",
        "Cannot delete folder because it is used by the following processes:\n{proc_names}\n\nDo you want to terminate them and try again?": "Не удалось удалить папку, так как её используют процессы:\n{proc_names}\n\nХотите завершить эти процессы и попробовать снова?",
        "Terminate processes": "Завершить процессы",
        "Cancel": "Отмена",
        "Success": "Успех",
        "Folder successfully deleted after terminating processes.": "Папка успешно удалена после завершения процессов.",
        "Failed to delete folder:\n{error}": "Не удалось удалить папку:\n{error}",
        "Deletion canceled.": "Удаление папки отменено.",
        "Please fill in the server name and IP.": "Пожалуйста, заполните имя и IP сервера.",

        # --- ServerControlPanel ---
        "Settings": "Настройки",
        "I accept the EULA": "Я принимаю лицензионное соглашение EULA",
        "Enable offline mode (cracked)": "Включить оффлайн режим (пиратка)",
        "Use playit.gg (tunnel)": "Использовать playit.gg (туннель)",
        "Control": "Управление",
        "Start server": "Запустить сервер",
        "Stop server": "Остановить сервер",
        "You must accept the EULA!": "Вы должны принять лицензионное соглашение EULA!",
        "Managing server: ": "Управление сервером: ",
        "Manage server": "Управление сервером",
        "Server started.": "Сервер запущен.",
        "Server stopped.": "Сервер остановлен.",
        "Server is already running.": "Сервер уже запущен.",
        "Server is not running.": "Сервер не запущен.",
        "Server forcefully stopped.": "Сервер принудительно остановлен.",

        # --- CreateServerDialog ---
        "Create your own server": "Создать свой сервер Minecraft",
        "Port": "Порт",
        "Version": "Версия",
        "Core": "Ядро",
        "Create": "Создать",
        "Please enter a valid server name and port (number).": "Пожалуйста, введите корректное имя и порт (число).",
        "Error": "Ошибка"
    },

    "en": {
        # --- SettingsPage ---
        "Theme:": "Theme:",
        "Language:": "Language:",
        "Minecraft launch mode:": "Minecraft launch mode:",
        "minecraft-launcher-lib (default)": "minecraft-launcher-lib (default)",
        "Java (specify path)": "Java (specify path)",
        "Java path (if Java is selected):": "Java path (if Java is selected):",
        "Browse Java path": "Browse Java path",
        "Page backgrounds:": "Page backgrounds:",
        "Save settings": "Save settings",

        # --- MinecraftPage ---
        "Play": "Play",
        "Username": "Username",
        "No versions available": "No versions available",

        # --- ModsPage ---
        "Mods from Modrinth": "Mods from Modrinth",
        "Search mod...": "Search mod...",
        "Open mods folder": "Open mods folder",
        "Delete all mods": "Delete all mods",
        "Error": "Error",
        "Downloading mod": "Downloading mod",
        "Done": "Done",
        "All mods deleted": "All mods deleted",
        "No available versions": "No available versions",
        "No supported builds": "No supported builds",
        "File not found": "File not found",
        "Install mod": "Install mod",
        "Minecraft version and loader:": "Minecraft version and loader:",

        # --- NewsPage ---
        "News": "News",
        "2025-08-12 v1.4.0.7: Discord RPC added": "2025-08-12 v1.4.0.7: Discord RPC added",
        "2025-07-24 v1.4.0.5: Added support for downloading mods from Modrind and launcher settings": "2025-07-24 v1.4.0.5: Added support for downloading mods from Modrind and launcher settings",
        "2025-07-23 v1.4.0.4: Added ability to create and manage local Minecraft servers directly from the launcher...": "2025-07-23 v1.4.0.4: Added ability to create and manage local Minecraft servers directly from the launcher...",
        "2025-07-23 v1.4.0.3: New design added and code restored": "2025-07-23 v1.4.0.3: New design added and code restored",
        "2025-06-26 v1.4.0.2: New design added, but code lost": "2025-06-26 v1.4.0.2: New design added, but code lost",
        "2025-06-26 v1.4.0.1: Bugs fixed, but design outdated": "2025-06-26 v1.4.0.1: Bugs fixed, but design outdated",
        "2025-06-26 v1.4.0.0: Bugs fixed, but design outdated": "2025-06-26 v1.4.0.0: Bugs fixed, but design outdated",
        "2025-06-26 v1.3: Launcher will exit beta in the next release": "2025-06-26 v1.3: Launcher will exit beta in the next release",
        "No news available": "No news available",

        # --- HomePage ---
        "Welcome to SuperLauncher!": "Welcome to SuperLauncher!",

        # --- ServersPage ---
        "🖧 Minecraft Servers": "🖧 Minecraft Servers",
        "Create your own server": "Create your own server",
        "Server Name": "Server Name",
        "IP or domain": "IP or domain",
        "Add server": "Add server",
        "Manage": "Manage",
        "Delete": "Delete",
        "Delete confirmation": "Delete confirmation",
        "Are you sure you want to delete the server '{server_name}'? This action cannot be undone.": "Are you sure you want to delete the server '{server_name}'? This action cannot be undone.",
        "Folder in use": "Folder in use",
        "Cannot delete folder because it is used by the following processes:\n{proc_names}\n\nDo you want to terminate them and try again?": "Cannot delete folder because it is used by the following processes:\n{proc_names}\n\nDo you want to terminate them and try again?",
        "Terminate processes": "Terminate processes",
        "Cancel": "Cancel",
        "Success": "Success",
        "Folder successfully deleted after terminating processes.": "Folder successfully deleted after terminating processes.",
        "Failed to delete folder:\n{error}": "Failed to delete folder:\n{error}",
        "Deletion canceled.": "Deletion canceled.",
        "Please fill in the server name and IP.": "Please fill in the server name and IP.",

        # --- ServerControlPanel ---
        "Settings": "Settings",
        "I accept the EULA": "I accept the EULA",
        "Enable offline mode (cracked)": "Enable offline mode (cracked)",
        "Use playit.gg (tunnel)": "Use playit.gg (tunnel)",
        "Control": "Control",
        "Start server": "Start server",
        "Stop server": "Stop server",
        "You must accept the EULA!": "You must accept the EULA!",
        "Managing server: ": "Managing server: ",
        "Manage server": "Manage server",
        "Server started.": "Server started.",
        "Server stopped.": "Server stopped.",
        "Server is already running.": "Server is already running.",
        "Server is not running.": "Server is not running.",
        "Server forcefully stopped.": "Server forcefully stopped.",

        # --- CreateServerDialog ---
        "Create your own server": "Create your own server",
        "Port": "Port",
        "Version": "Version",
        "Core": "Core",
        "Create": "Create",
        "Please enter a valid server name and port (number).": "Please enter a valid server name and port (number).",
        "Error": "Error"
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Если файла нет или ошибка, возвращаем значения по умолчанию
    return {
        "java_path": "",
        "ram": 4096,
        "language": "ru",
        "theme": "dark",
        "launch_mode": "launcher_lib"
    }

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Ошибка сохранения настроек:", e)

MODRINTH_API = "https://api.modrinth.com/v2"

# Путь к папке Minecraft
minecraft_directory = get_minecraft_directory()
print("Path to Minecraft:", minecraft_directory)

if not os.path.exists(minecraft_directory):
    print("Minecraft folder not found! Creating...")
    os.makedirs(minecraft_directory, exist_ok=True)

print("Contents of the Minecraft folder:", os.listdir(minecraft_directory))

profile_path = os.path.join(minecraft_directory, 'launcher_profiles.json')
print("Path to launcher_profiles.json:", profile_path)

if not os.path.isfile(profile_path):
    print("launcher_profiles.json not found, creating new...")
    empty_profile = {
        "profiles": {},
        "settings": {},
        "selectedProfile": None
    }
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(empty_profile, f, indent=4)
    print("Empty launcher_profiles.json created")
else:
    print("launcher_profiles.json already exists")

class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)
        self.version_id = ''
        self.username = ''
        self.loader_type = 'vanilla'  # по умолчанию ванилла
        self.progress = 0
        self.progress_max = 100
        self.progress_label = ''

    def launch_setup(self, version_id, username):
        self.username = username
        # Убираем проверку forge и fabric
        self.loader_type = "vanilla"
        self.version_id = version_id

    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        self.state_update_signal.emit(True)
        try:
            if self.loader_type == "vanilla":
                install_minecraft_version(
                    versionid=self.version_id,
                    minecraft_directory=minecraft_directory,
                    callback={
                        'setStatus': self.update_progress_label,
                        'setProgress': self.update_progress,
                        'setMax': self.update_progress_max
                    }
                )
            else:
                raise Exception("Неизвестный тип загрузчика")

            if self.username == '':
                self.username = generate_username()[0]

            options = {
                'username': self.username,
                'uuid': str(uuid1()),
                'token': ''
            }
            cmd = get_minecraft_command(
                version=self.version_id,
                minecraft_directory=minecraft_directory,
                options=options
            )
            print("Запускаем команду:", cmd)
            proc = subprocess.Popen(cmd, cwd=minecraft_directory)
            proc.wait()
            print(f"Процесс Minecraft завершился с кодом: {proc.returncode}")
        except Exception as e:
            print("Ошибка при запуске Minecraft:", e)
        finally:
            self.state_update_signal.emit(False)

# Функция возвращает все версии без фильтрации (Vanilla + Snapshots + Fabric + Forge)
def get_all_versions():
    versions = get_version_list()  # vanilla + snapshots
    versions_dir = os.path.join(minecraft_directory, 'versions')
    if os.path.exists(versions_dir):
        for folder in os.listdir(versions_dir):
            full_path = os.path.join(versions_dir, folder)
            if os.path.isdir(full_path):
                if not any(v['id'] == folder for v in versions):
                    versions.append({'id': folder})
    return versions

class MinecraftLauncherPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # сохраняем ссылку на родителя
        self.config = load_config()  # читаем текущий язык

        # Логотип
        self.logo = QLabel()
        self.logo.setMaximumSize(QSize(256, 37))
        pixmap = QPixmap('assets/title.png')
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap)
        self.logo.setScaledContents(True)

        # Spacer
        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Поле для имени пользователя
        self.username = QLineEdit()
        self.username.setPlaceholderText(self.tr("Username"))
        self.username.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 5px;
        """)

        # Список версий
        self.version_select = QComboBox()
        self.version_select.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 3px;
        """)
        self.update_versions_list()

        # Прогрессбар
        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.start_progress_label = QLabel('')
        self.start_progress_label.setVisible(False)
        self.start_progress = QProgressBar()
        self.start_progress.setValue(0)
        self.start_progress.setVisible(False)

        # Кнопка запуска
        self.start_button = QPushButton(self.tr("Play"))
        self.start_button.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #4facfe;
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        """)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addItem(self.titlespacer)
        layout.addWidget(self.username)
        layout.addWidget(self.version_select)
        layout.addItem(self.progress_spacer)
        layout.addWidget(self.start_progress_label)
        layout.addWidget(self.start_progress)
        layout.addWidget(self.start_button)

    # --- Перевод ---
    def tr(self, key: str) -> str:
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def refresh_language(self):
        self.username.setPlaceholderText(self.tr("Username"))
        self.start_button.setText(self.tr("Play"))

    # --- Версии Minecraft ---
    def update_versions_list(self):
        self.version_select.clear()
        versions = self.get_all_versions()
        for version in versions:
            self.version_select.addItem(version['id'])

    @staticmethod
    def get_all_versions():
        from minecraft_launcher_lib.utils import get_version_list, get_minecraft_directory
        versions = []

        try:
            online_versions = get_version_list()
            versions.extend(online_versions)
        except Exception as e:
            print("Онлайн-версии недоступны, используем локальные:", e)

        versions_dir = os.path.join(get_minecraft_directory(), 'versions')
        if os.path.exists(versions_dir):
            for folder in os.listdir(versions_dir):
                full_path = os.path.join(versions_dir, folder)
                if os.path.isdir(full_path):
                    if not any(v['id'] == folder for v in versions):
                        versions.append({'id': folder})

        if not versions:
            versions.append({'id': 'No versions available'})
        return versions

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.labels = {}
        self.buttons = {}

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ===== Тема =====
        self.labels["theme"] = QLabel()
        layout.addWidget(self.labels["theme"])
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "dark"))
        layout.addWidget(self.theme_combo)

        # ===== Язык =====
        self.labels["lang"] = QLabel()
        layout.addWidget(self.labels["lang"])
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(translations.keys()))
        self.lang_combo.setCurrentText(self.config.get("language", "ru"))
        self.lang_combo.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.lang_combo)

        # ===== Способ запуска =====
        self.labels["launch_mode"] = QLabel()
        layout.addWidget(self.labels["launch_mode"])
        self.rb_launcher_lib = QRadioButton()
        self.rb_java = QRadioButton()
        layout.addWidget(self.rb_launcher_lib)
        layout.addWidget(self.rb_java)
        launch_mode = self.config.get("launch_mode", "launcher_lib")
        if launch_mode == "java":
            self.rb_java.setChecked(True)
        else:
            self.rb_launcher_lib.setChecked(True)

        # ===== Путь к Java =====
        self.labels["java_path"] = QLabel()
        layout.addWidget(self.labels["java_path"])
        self.java_path_input = QLineEdit(self.config.get("java_path", ""))
        layout.addWidget(self.java_path_input)
        self.buttons["browse_java"] = QPushButton()
        layout.addWidget(self.buttons["browse_java"])
        self.buttons["browse_java"].clicked.connect(self.browse_java)

        self.java_path_input.setEnabled(self.rb_java.isChecked())
        self.buttons["browse_java"].setEnabled(self.rb_java.isChecked())
        self.rb_java.toggled.connect(self.java_path_input.setEnabled)
        self.rb_java.toggled.connect(self.buttons["browse_java"].setEnabled)

        # ===== Фоны страниц =====
        self.labels["page_bg"] = QLabel()
        layout.addWidget(self.labels["page_bg"])
        self.bg_buttons = {}
        self.bg_options = {
            "dark": "assets/bg_dark.png",
            "gray": "assets/bg_gray.png"
        }
        bg_layout = QHBoxLayout()
        for key, img in self.bg_options.items():
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setIcon(QIcon(img))
            btn.setIconSize(QSize(120, 80))
            btn.setFixedSize(130, 90)
            btn.setStyleSheet("border: 2px solid transparent; border-radius: 8px;")
            btn.clicked.connect(lambda checked, k=key: self.select_bg(k))
            bg_layout.addWidget(btn)
            self.bg_buttons[key] = btn
        layout.addLayout(bg_layout)
        current_bg = self.config.get("page_bg", "dark")
        self.select_bg(current_bg)

        # ===== Кнопка сохранить =====
        self.buttons["save"] = QPushButton()
        layout.addWidget(self.buttons["save"])
        self.buttons["save"].clicked.connect(self.save_settings)

        self.setLayout(layout)
        self.update_texts()

    def tr(self, key: str) -> str:
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def update_texts(self):
        self.labels["theme"].setText(self.tr("Theme:"))
        self.labels["lang"].setText(self.tr("Language:"))
        self.labels["launch_mode"].setText(self.tr("Minecraft launch mode:"))
        self.rb_launcher_lib.setText(self.tr("minecraft-launcher-lib (default)"))
        self.rb_java.setText(self.tr("Java (specify path)"))
        self.labels["java_path"].setText(self.tr("Java path (if Java is selected):"))
        self.buttons["browse_java"].setText(self.tr("Browse Java path"))
        self.labels["page_bg"].setText(self.tr("Page backgrounds:"))
        self.buttons["save"].setText(self.tr("Save settings"))

        # если родитель имеет метод refresh_language, обновляем и его
        parent = self.parent()
        if parent and hasattr(parent, "refresh_language"):
            parent.refresh_language()

    def change_language(self, lang):
        self.config["language"] = lang
        self.update_texts()

    def select_bg(self, key):
        for k, btn in self.bg_buttons.items():
            if k == key:
                btn.setChecked(True)
                btn.setStyleSheet("border: 2px solid #4facfe; border-radius: 8px;")
            else:
                btn.setChecked(False)
                btn.setStyleSheet("border: 2px solid transparent; border-radius: 8px;")
        self.config["page_bg"] = key

    def browse_java(self):
        file, _ = QFileDialog.getOpenFileName(
            self, self.tr("Browse Java path"), "", "Executable Files (*.exe);;All Files (*)"
        )
        if file:
            self.java_path_input.setText(file)

    def save_settings(self):
        self.config["theme"] = self.theme_combo.currentText()
        self.config["language"] = self.lang_combo.currentText()
        self.config["launch_mode"] = "java" if self.rb_java.isChecked() else "launcher_lib"
        self.config["java_path"] = self.java_path_input.text()
        self.config["page_bg"] = self.config.get("page_bg", "dark")
        save_config(self.config)
        self.update_texts()

class ModDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0

                with open(self.save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                self.progress.emit(int(downloaded * 100 / total))
            self.finished.emit(self.save_path)
        except Exception as e:
            self.finished.emit(f"ERROR: {e}")

class DiscordRPCThread(threading.Thread):
    def __init__(self, main_window):
        super().__init__()
        self.client_id = "1405145554027155456"
        self.rpc = None
        self.main_window = main_window
        self.running = True
        self.connected = False  # Флаг успешного подключения

    def run(self):
        try:
            self.rpc = Presence(self.client_id)
            try:
                self.rpc.connect()
                self.connected = True
                print("Discord RPC connected successfully.")
            except Exception as e:
                print(f"Discord RPC not connected: {e}")
                self.connected = False
                return  # Если не подключилось, выходим из потока

            while self.running:
                current_page = self.main_window.pages.currentIndex()
                page_names = ["Home", "Mods", "News", "Updates", "Servers", "Settings", "Minecraft"]
                details = f"На странице: {page_names[current_page]}"
                state = "Суперлаунчер 1.4.0.8"

                try:
                    self.rpc.update(
                        details=details,
                        state=state,
                        large_image="superlauncher",
                        small_image="minecraft",
                        start=time.time()
                    )
                except Exception as e:
                    print(f"Discord RPC update error: {e}")

                time.sleep(15)
        except Exception as e:
            print(f"Discord RPC thread error: {e}")

    def stop(self):
        self.running = False
        if self.rpc and self.connected:
            try:
                self.rpc.close()
                print("Discord RPC closed successfully.")
            except Exception as e:
                print(f"Error closing Discord RPC: {e}")

class ModsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config = load_config()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.mods_dir = os.path.join(minecraft_directory, "mods")
        os.makedirs(self.mods_dir, exist_ok=True)

        # Заголовок
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 10px; color: white;")
        self.layout.addWidget(self.title)

        # Поиск
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.search_mods)
        self.layout.addWidget(self.search_input)

        # Список результатов
        self.results_list = QListWidget()
        self.results_list.setIconSize(QSize(64, 64))
        self.layout.addWidget(self.results_list)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.open_folder_button = QPushButton()
        self.open_folder_button.clicked.connect(self.open_mods_folder)
        buttons_layout.addWidget(self.open_folder_button)

        self.delete_all_button = QPushButton()
        self.delete_all_button.setStyleSheet("background-color: #d9534f; color: white;")
        self.delete_all_button.clicked.connect(self.delete_all_mods)
        buttons_layout.addWidget(self.delete_all_button)

        self.layout.addLayout(buttons_layout)

        self.load_featured_mods()
        self.update_texts()

    def tr(self, key: str) -> str:
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def update_texts(self):
        self.title.setText(f"🧩 {self.tr('Mods from Modrinth')}")
        self.search_input.setPlaceholderText(f"🔍 {self.tr('Search mod...')}")
        self.open_folder_button.setText(f"📂 {self.tr('Open mods folder')}")
        self.delete_all_button.setText(f"🗑 {self.tr('Delete all mods')}")

    def load_featured_mods(self):
        try:
            url = f"{MODRINTH_API}/search?limit=20&index=relevance"
            resp = requests.get(url)
            data = resp.json()
            self.results_list.clear()
            for hit in data["hits"]:
                item = QListWidgetItem(f"{hit['title']} — {hit.get('description', '')}")
                item.setData(Qt.ItemDataRole.UserRole, hit["project_id"])
                self.results_list.addItem(item)
            self.results_list.itemClicked.connect(self.show_mod_dialog)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def search_mods(self):
        query = self.search_input.text()
        if not query.strip():
            return
        try:
            url = f"{MODRINTH_API}/search?query={query}"
            resp = requests.get(url)
            data = resp.json()
            self.results_list.clear()
            for hit in data["hits"]:
                item = QListWidgetItem(f"{hit['title']} — {hit.get('description', '')}")
                item.setData(Qt.ItemDataRole.UserRole, hit["project_id"])
                self.results_list.addItem(item)
            self.results_list.itemClicked.connect(self.show_mod_dialog)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def show_mod_dialog(self, item):
        project_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            versions_url = f"{MODRINTH_API}/project/{project_id}/version"
            resp = requests.get(versions_url)
            versions = resp.json()

            if not versions:
                QMessageBox.warning(self, self.tr("No available versions"),
                                    self.tr("No versions available"))
                return

            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Install mod"))
            layout = QVBoxLayout(dialog)

            version_box = QComboBox()
            version_loader_map = {}
            for v in versions:
                mc_versions = v["game_versions"]
                loaders = v["loaders"]
                if not mc_versions or not loaders:
                    continue
                display_text = f"{mc_versions[0]} | {loaders[0]}"
                version_loader_map[display_text] = v

            if not version_loader_map:
                QMessageBox.warning(self, self.tr("No supported builds"),
                                    self.tr("No supported builds"))
                return

            version_box.addItems(version_loader_map.keys())
            layout.addWidget(QLabel(self.tr("Minecraft version and loader:")))
            layout.addWidget(version_box)

            install_button = QPushButton(self.tr("Install mod"))
            layout.addWidget(install_button)

            install_button.clicked.connect(
                lambda: self.download_selected_mod(version_loader_map[version_box.currentText()], dialog)
            )

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))

    def download_selected_mod(self, version_data, dialog):
        files = version_data["files"]
        for file in files:
            if file["filename"].endswith(".jar"):
                url = file["url"]
                filename = file["filename"]
                save_path = os.path.join(self.mods_dir, filename)
                dialog.close()
                self.start_download(url, save_path)
                return
        QMessageBox.warning(self, self.tr("File not found"),
                            self.tr("File not found"))

    def start_download(self, url, save_path):
        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle(self.tr("Downloading mod"))
        self.progress_dialog.setModal(True)

        dialog_layout = QVBoxLayout(self.progress_dialog)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        dialog_layout.addWidget(self.progress_bar)

        self.progress_dialog.show()

        self.download_thread = ModDownloadThread(url, save_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, result):
        self.progress_dialog.hide()
        if result.startswith("ERROR:"):
            QMessageBox.critical(self, self.tr("Error"), result)
        else:
            QMessageBox.information(self, self.tr("Done"),
                                    f"{self.tr('Mod installed successfully:')}\n{result}")

    def open_mods_folder(self):
        path = os.path.realpath(self.mods_dir)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f"open \"{path}\"")
        else:
            os.system(f"xdg-open \"{path}\"")

    def delete_all_mods(self):
        confirm = QMessageBox.question(
            self, self.tr("Delete all mods"),
            self.tr("Are you sure you want to delete all mods?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            deleted = 0
            for file in os.listdir(self.mods_dir):
                if file.endswith(".jar"):
                    try:
                        os.remove(os.path.join(self.mods_dir, file))
                        deleted += 1
                    except Exception as e:
                        QMessageBox.warning(self, self.tr("Error"),
                                            f"{self.tr('Could not delete')} {file}: {e}")
            QMessageBox.information(self, self.tr("Done"),
                                    f"{self.tr('All mods deleted')}: {deleted}")

class NewsPage(QWidget):
    def __init__(self, parent=None, language="en"):
        super().__init__(parent)
        self.parent_window = parent
        self.language = language  # Текущий язык

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: white;")
        layout.addWidget(self.title)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.scroll_area.setWidget(self.container)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(12)

        # Новости
        self.news_list = [
            ("2025-08-12 v1.4.0.7", "Добавлен Discord RPC"),
            ("2025-07-24 v1.4.0.5", "Добавлена поддержка скачивания модов из Modrind и настроек лаунчера"),
            ("2025-07-23 v1.4.0.4", "Добавлена возможность создавать и управлять локальными Minecraft-серверами прямо из лаунчера..."),
            ("2025-07-23 v1.4.0.3", "Добавлен новый дизайн и восстановлен код"),
            ("2025-06-26 v1.4.0.2", "Добавлен новый дизайн, но утерян код"),
            ("2025-06-26 v1.4.0.1", "Исправлены баги, но дизайн устаревший"),
            ("2025-06-26 v1.4.0.0", "Исправлены баги, но дизайн устаревший"),
            ("2025-06-26 v1.3", "Лаунчер выйдет из бета в следующем релизе")
        ]

        self.news_labels = []  # Сохраняем лейблы для обновления текста
        self.update_texts()
        self.populate_news()

    def _tr(self, text):
        return translations.get(self.language, {}).get(text, text)

    def update_texts(self):
        self.title.setText(self._tr("News"))

    def populate_news(self):
        # Очищаем контейнер перед заполнением
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Добавление новостей
        for date, text in self.news_list:
            translated_text = self._tr(text)
            news_label = QLabel(f"<b>{date}</b>: {translated_text}")
            news_label.setWordWrap(True)
            news_label.setStyleSheet("font-size: 16px; color: #c0c0c0;")
            self.container_layout.addWidget(news_label)
            self.news_labels.append(news_label)

        self.container_layout.addStretch()

    def set_language(self, language):
        self.language = language
        self.update_texts()
        self.populate_news()

CURRENT_VERSION = "v1.4.0.5"

class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        try:
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(self.filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = int(downloaded * 100 / total_length)
                                self.progress.emit(percent)
            self.finished.emit(str(self.filename))
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")


class UpdatesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.title = QLabel("🔄 Проверка обновлений")
        self.title.setStyleSheet("font-size:26px;font-weight:bold;color:white;")
        self.layout.addWidget(self.title)

        self.status_label = QLabel("Проверка доступных обновлений...")
        self.status_label.setStyleSheet("color:#c0c0c0;font-size:14px;")
        self.layout.addWidget(self.status_label)

        self.update_button = QPushButton("Скачать и установить обновление")
        self.update_button.setVisible(False)
        self.update_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_button.clicked.connect(self.download_latest)
        self.layout.addWidget(self.update_button)

        self.latest_version_info = None
        self.checked = False  # флаг, чтобы проверить только один раз

        QTimer.singleShot(100, self.check_for_updates)  # запуск проверки один раз после запуска UI

    def check_for_updates(self):
        if self.checked:
            return
        self.checked = True

        def task():
            try:
                url = "https://raw.githubusercontent.com/ludvig2457/SuperLauncher/main/versions.txt"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                lines = r.text.splitlines()

                versions = []
                for line in lines:
                    if "=" in line:
                        ver, link = line.split("=", 1)
                        versions.append((ver.strip(), link.strip()))

                if not versions:
                    QTimer.singleShot(0, lambda: self.status_label.setText("Версии не найдены."))
                    return

                # сортировка по семантической версии
                versions.sort(key=lambda x: version.parse(x[0]), reverse=True)
                latest_version, download_url = versions[0]

                if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                    self.latest_version_info = (latest_version, download_url)
                    QTimer.singleShot(0, lambda: self.show_update_button(latest_version))
                else:
                    QTimer.singleShot(0, lambda: self.status_label.setText("У вас установлена последняя версия."))

            except Exception as e:
                QTimer.singleShot(0, lambda: self.status_label.setText(f"Ошибка: {e}"))

        from threading import Thread
        Thread(target=task, daemon=True).start()

    def show_update_button(self, version):
        self.status_label.setText(f"Доступна новая версия: {version}")
        self.update_button.setVisible(True)

    def download_latest(self):
        if not self.latest_version_info:
            return

        latest_version, download_url = self.latest_version_info
        downloads_path = Path(__file__).parent
        filename = downloads_path / f"SuperLauncher{latest_version}.exe"

        self.update_button.setEnabled(False)
        self.status_label.setText(f"Загрузка версии {latest_version}...")

        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle(f"Загрузка {latest_version}")
        layout = QVBoxLayout(self.progress_dialog)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.progress_dialog.show()

        self.download_thread = UpdateDownloadThread(download_url, str(filename))
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(lambda result: self.finish_update(result))
        self.download_thread.start()

    def finish_update(self, result):
        self.progress_dialog.hide()
        if result.startswith("ERROR:"):
            QMessageBox.critical(self, "Ошибка", result)
            self.update_button.setEnabled(True)
            return

        subprocess.Popen([str(result)], close_fds=True)
        QApplication.quit()

class CreateServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()  # Загружаем текущие настройки (например, язык)

        self.setWindowTitle(self.tr("Create your own server"))
        self.setFixedSize(350, 220)

        layout = QFormLayout(self)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(self.tr("Server Name"))

        self.input_port = QLineEdit()
        self.input_port.setPlaceholderText(self.tr("Port (e.g., 25565)"))
        self.input_port.setText("25565")

        self.combo_version = QComboBox()
        self.combo_version.addItems(["1.20.4", "1.20.1", "1.19.4"])  # Можно расширить

        self.combo_core = QComboBox()
        self.combo_core.addItems(["Paper", "Purpur", "Vanilla"])

        layout.addRow(self.tr("Server Name") + ":", self.input_name)
        layout.addRow(self.tr("Port") + ":", self.input_port)
        layout.addRow(self.tr("Version") + ":", self.combo_version)
        layout.addRow(self.tr("Core") + ":", self.combo_core)

        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton(self.tr("Create"))
        self.btn_cancel = QPushButton(self.tr("Cancel"))
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

        self.btn_create.clicked.connect(self.create_server)
        self.btn_cancel.clicked.connect(self.reject)

    def tr(self, key: str) -> str:
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def refresh_language(self):
        self.setWindowTitle(self.tr("Create your own server"))
        self.input_name.setPlaceholderText(self.tr("Server Name"))
        self.input_port.setPlaceholderText(self.tr("Port (e.g., 25565)"))
        # Обновляем подписи полей
        layout: QFormLayout = self.layout()
        layout.labelForField(self.input_name).setText(self.tr("Server Name") + ":")
        layout.labelForField(self.input_port).setText(self.tr("Port") + ":")
        layout.labelForField(self.combo_version).setText(self.tr("Version") + ":")
        layout.labelForField(self.combo_core).setText(self.tr("Core") + ":")
        self.btn_create.setText(self.tr("Create"))
        self.btn_cancel.setText(self.tr("Cancel"))

    def create_server(self):
        name = self.input_name.text().strip()
        port = self.input_port.text().strip()
        version = self.combo_version.currentText()
        core = self.combo_core.currentText()

        if not name or not port.isdigit():
            QMessageBox.warning(self, self.tr("Error"), self.tr("Please enter a valid server name and port (number)."))
            return

        self.server_name = name
        self.server_port = int(port)
        self.server_version = version
        self.server_core = core
        self.accept()

class DownloadThread(QThread):
    progress_changed = pyqtSignal(int)  # проценты
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, core, version, save_path):
        super().__init__()
        self.core = core
        self.version = version
        self.save_path = save_path

    def run(self):
        try:
            url = self.get_jar_url(self.core, self.version)
            r = requests.get(url, stream=True)
            r.raise_for_status()

            total_length = r.headers.get('content-length')
            if total_length is None:
                with open(self.save_path, 'wb') as f:
                    f.write(r.content)
                self.progress_changed.emit(100)
            else:
                total_length = int(total_length)
                downloaded = 0
                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = int(downloaded * 100 / total_length)
                            self.progress_changed.emit(percent)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def get_jar_url(self, core, version):
        core = core.lower()
        if core == "paper":
            builds_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}"
            resp = requests.get(builds_url)
            resp.raise_for_status()
            build = resp.json()["builds"][-1]
            return f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{build}/downloads/paper-{version}-{build}.jar"

        elif core == "purpur":
            builds_url = f"https://api.purpurmc.org/v2/purpur/{version}"
            resp = requests.get(builds_url)
            resp.raise_for_status()
            build = resp.json()["builds"][-1]
            return f"https://api.purpurmc.org/v2/purpur/{version}/{build}/download"

        elif core == "vanilla":
            manifest = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json").json()
            version_data = next((v for v in manifest["versions"] if v["id"] == version), None)
            if not version_data:
                raise Exception(f"Версия {version} не найдена")
            version_json = requests.get(version_data["url"]).json()
            return version_json["downloads"]["server"]["url"]

        else:
            raise Exception(f"Ядро {core} не поддерживается")

class ServerControlDialog(QDialog):
    def __init__(self, server_name, server_path, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.server_path = server_path
        self.process = None
        self.playit_process = None

        self.setWindowTitle(self.tr("Manage server") + f" '{server_name}'")
        self.setFixedSize(350, 300)

        layout = QVBoxLayout(self)

        self.label = QLabel(self.tr("Managing server: ") + server_name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Чекбоксы
        self.checkbox_eula = QCheckBox(self.tr("I accept the EULA license agreement"))
        layout.addWidget(self.checkbox_eula)

        self.checkbox_offline = QCheckBox(self.tr("Enable offline mode (pirate)"))
        layout.addWidget(self.checkbox_offline)

        self.checkbox_playit = QCheckBox(self.tr("Use playit.gg (tunnel)"))
        layout.addWidget(self.checkbox_playit)

        # Кнопка сохранить настройки
        self.btn_save_settings = QPushButton(self.tr("Save settings"))
        self.btn_save_settings.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save_settings)

        # Кнопки управления сервером
        self.btn_start = QPushButton(self.tr("Start server"))
        self.btn_stop = QPushButton(self.tr("Stop server"))
        self.btn_close = QPushButton(self.tr("Close"))

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_close)

        self.btn_start.clicked.connect(self.start_server)
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_close.clicked.connect(self.close)

        self.update_buttons()
        self.load_settings()

    def tr(self, key: str) -> str:
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def refresh_language(self):
        self.setWindowTitle(self.tr("Manage server"))
        self.label.setText(self.tr("Managing server: ") + os.path.basename(self.server_path))
        self.checkbox_eula.setText(self.tr("I accept the EULA license agreement"))
        self.checkbox_offline.setText(self.tr("Enable offline mode (pirate)"))
        self.checkbox_playit.setText(self.tr("Use playit.gg (tunnel)"))
        self.btn_save_settings.setText(self.tr("Save settings"))
        self.btn_start.setText(self.tr("Start server"))
        self.btn_stop.setText(self.tr("Stop server"))
        self.btn_close.setText(self.tr("Close"))

    def load_settings(self):
        eula_path = os.path.join(self.server_path, "eula.txt")
        self.checkbox_eula.setChecked(os.path.isfile(eula_path) and "eula=true" in open(eula_path, "r", encoding="utf-8").read().lower())

        prop_path = os.path.join(self.server_path, "server.properties")
        online_mode = True
        if os.path.isfile(prop_path):
            with open(prop_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("online-mode="):
                        online_mode = line.strip().split("=")[1].lower() == "true"
                        break
        self.checkbox_offline.setChecked(not online_mode)
        self.checkbox_playit.setChecked(False)

    def save_settings(self):
        eula_path = os.path.join(self.server_path, "eula.txt")
        try:
            with open(eula_path, "w", encoding="utf-8") as f:
                f.write(f"eula={'true' if self.checkbox_eula.isChecked() else 'false'}\n")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to save eula.txt") + f":\n{e}")
            return

        prop_path = os.path.join(self.server_path, "server.properties")
        props = {}
        if os.path.isfile(prop_path):
            try:
                with open(prop_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            props[k] = v
            except Exception:
                pass
        props["online-mode"] = "false" if self.checkbox_offline.isChecked() else "true"

        try:
            with open(prop_path, "w", encoding="utf-8") as f:
                for k, v in props.items():
                    f.write(f"{k}={v}\n")
                if not props:
                    f.write(f"online-mode={'false' if self.checkbox_offline.isChecked() else 'true'}\n")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to save server.properties") + f":\n{e}")
            return

        QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved!"))

    def update_buttons(self):
        running = self.process is not None and self.process.poll() is None
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def download_and_install_playit(self):
        import requests, tempfile

        msi_url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-windows-x86_64-signed.msi"
        temp_dir = tempfile.gettempdir()
        msi_path = os.path.join(temp_dir, "playit-agent.msi")

        if not os.path.isfile(msi_path):
            try:
                response = requests.get(msi_url, stream=True)
                response.raise_for_status()
                with open(msi_path, "wb") as f:
                    for chunk in response.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                os.system(f'powershell -Command "Unblock-File -Path \'{msi_path}\'"')
            except Exception as e:
                QMessageBox.critical(self, self.tr("Download error"), self.tr("Failed to download playit MSI") + f":\n{e}")
                return False

        try:
            result = subprocess.run(["msiexec", "/i", msi_path, "/quiet", "/qn"], capture_output=True, text=True, shell=False)
            if result.returncode != 0:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle(self.tr("Installation error"))
                msg.setText(self.tr("Installation failed with code") + f" {result.returncode}:\n{result.stderr.strip()}\n\n" + self.tr("Try opening the file manually:"))

                btn_copy = QPushButton(self.tr("Copy MSI path"))
                btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(msi_path))
                layout = msg.layout()
                layout.addWidget(btn_copy, layout.rowCount(), 0, 1, layout.columnCount())
                msg.exec()
                return False

            QMessageBox.information(self, self.tr("Installation"), self.tr("Playit-agent installed successfully."))
            return True
        except Exception as e:
            QMessageBox.critical(self, self.tr("Installation error"), self.tr("Failed to install playit") + f":\n{e}")
            return False

    def start_playit(self):
        import os, subprocess
        possible_paths = [
            os.path.expandvars(r"%ProgramFiles%\playit\playit.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\playit\playit.exe"),
            os.path.join(self.server_path, "playit.exe"),
        ]
        playit_exe = next((p for p in possible_paths if os.path.isfile(p)), None)
        if not playit_exe and not self.download_and_install_playit():
            QMessageBox.warning(self, "playit.gg", self.tr("playit.exe not found after installation"))
            return False

        try:
            self.playit_process = subprocess.Popen([playit_exe], cwd=os.path.dirname(playit_exe))
            return True
        except Exception as e:
            QMessageBox.critical(self, self.tr("Playit error"), str(e))
            return False

    def stop_playit(self):
        if self.playit_process and self.playit_process.poll() is None:
            try:
                self.playit_process.terminate()
                self.playit_process.wait(5)
            except Exception:
                self.playit_process.kill()
            finally:
                self.playit_process = None

    def start_server(self):
        import os, subprocess
        if self.process is None or self.process.poll() is not None:
            if not self.checkbox_eula.isChecked():
                QMessageBox.warning(self, "EULA", self.tr("You must accept the EULA!"))
                return

            bat_path = os.path.join(self.server_path, "start.bat")
            if not os.path.isfile(bat_path):
                QMessageBox.warning(self, self.tr("Error"), self.tr("start.bat not found!"))
                return

            try:
                self.process = subprocess.Popen(["cmd.exe", "/k", "start.bat"], cwd=self.server_path, shell=True)
                if self.checkbox_playit.isChecked() and not self.start_playit():
                    QMessageBox.warning(self, "playit.gg", self.tr("Playit tunnel will not be started."))
                QMessageBox.information(self, self.tr("Server"), self.tr("Server started."))
                self.update_buttons()
            except Exception as e:
                QMessageBox.critical(self, self.tr("Start error"), str(e))
        else:
            QMessageBox.information(self, self.tr("Info"), self.tr("Server is already running."))
            self.update_buttons()

    def stop_server(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(5)
                self.stop_playit()
                QMessageBox.information(self, self.tr("Server"), self.tr("Server stopped."))
            except Exception:
                self.process.kill()
                self.stop_playit()
                QMessageBox.information(self, self.tr("Server"), self.tr("Server forcefully stopped."))
            finally:
                self.process = None
                self.update_buttons()
        else:
            QMessageBox.information(self, self.tr("Info"), self.tr("Server is not running."))
            self.update_buttons()

class ServersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # для возможности доступа к родителю при переводе
        self.config = load_config()  # для текущего языка

        self.servers_file = "servers_list.json"
        self.servers_list = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # Заголовок
        self.title_label = QLabel(self.tr("🖧 Minecraft Servers"))
        self.title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; margin-bottom: 15px; color: white;"
        )
        self.layout.addWidget(self.title_label)

        # Кнопка создания сервера
        self.btn_create_server = QPushButton(self.tr("Create your own server"))
        self.btn_create_server.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_create_server.setStyleSheet(
            "padding: 8px; font-weight: bold; background-color: #4facfe; color: black; border-radius: 8px;"
        )
        self.btn_create_server.clicked.connect(self.open_create_server_dialog)
        self.layout.addWidget(self.btn_create_server)

        # Форма добавления сервера вручную
        form_layout = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(self.tr("Server Name"))
        self.input_ip = QLineEdit()
        self.input_ip.setPlaceholderText(self.tr("IP or domain"))

        self.btn_add_server = QPushButton(self.tr("Add server"))
        self.btn_add_server.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_server.clicked.connect(self.add_server)

        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_ip)
        form_layout.addWidget(self.btn_add_server)
        self.layout.addLayout(form_layout)

        # Прогрессбар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        # Скролл для серверов
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.scroll_area.setWidget(self.container)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(12)

        self.load_servers()
        self.update_servers_ui()

    # --- Перевод ---
    def tr(self, key: str) -> str:
        # если есть родитель с tr — используем его
        if self.parent_window and hasattr(self.parent_window, "tr"):
            return self.parent_window.tr(key)
        lang = self.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def refresh_language(self):
        self.title_label.setText(self.tr("🖧 Minecraft Servers"))
        self.btn_create_server.setText(self.tr("Create your own server"))
        self.input_name.setPlaceholderText(self.tr("Server Name"))
        self.input_ip.setPlaceholderText(self.tr("IP or domain"))
        self.btn_add_server.setText(self.tr("Add server"))
        self.update_servers_ui()

    # --- Методы сервера ---
    def open_create_server_dialog(self):
        dialog = CreateServerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.server_name
            port = dialog.server_port
            version = dialog.server_version
            core = dialog.server_core
            ip = f"localhost:{port}"

            server_path = os.path.join("servers", name)
            os.makedirs(server_path, exist_ok=True)

            self.progress_bar.setValue(0)
            self.progress_bar.show()

            self.download_thread = DownloadThread(core, version, os.path.join(server_path, "server.jar"))
            self.download_thread.progress_changed.connect(self.progress_bar.setValue)
            self.download_thread.finished.connect(lambda: self.on_download_finished(name, ip, server_path))
            self.download_thread.error.connect(self.on_download_error)
            self.download_thread.start()

    def on_download_finished(self, name, ip, server_path):
        self.progress_bar.hide()
        self.generate_start_bat(server_path)

        self.servers_list.append({"name": name, "ip": ip, "managed": True})
        self.save_servers()
        self.update_servers_ui()

        QMessageBox.information(
            self,
            self.tr("Done"),
            f"{self.tr('Server')} '{name}' {self.tr('successfully created!')}"
        )

    def on_download_error(self, error_message):
        self.progress_bar.hide()
        QMessageBox.critical(self, self.tr("Error"), error_message)

    def generate_start_bat(self, path):
        with open(os.path.join(path, "start.bat"), "w", encoding="utf-8") as f:
            f.write("""@echo off
java -Xmx2G -Xms2G -jar server.jar nogui
pause
""")

    # --- Работа с JSON ---
    def load_servers(self):
        try:
            with open(self.servers_file, "r", encoding="utf-8") as f:
                self.servers_list = json.load(f)
        except Exception:
            self.servers_list = []

    def save_servers(self):
        try:
            with open(self.servers_file, "w", encoding="utf-8") as f:
                json.dump(self.servers_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving servers:", e)

    # --- Добавление сервера вручную ---
    def add_server(self):
        name = self.input_name.text().strip()
        ip = self.input_ip.text().strip()

        if not name or not ip:
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Please fill in server name and IP.")
            )
            return

        self.servers_list.append({"name": name, "ip": ip, "managed": False})
        self.save_servers()
        self.update_servers_ui()

        self.input_name.clear()
        self.input_ip.clear()

    # --- Обновление UI серверов ---
    def update_servers_ui(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for server in self.servers_list:
            self.add_server_widget(server['name'], server['ip'], server.get('managed', False))

        self.container_layout.addStretch()

    def add_server_widget(self, name, ip, managed):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        server_label = QLabel(f"<b>{name}</b> — <span style='color:#4facfe;'>{ip}</span>")
        server_label.setWordWrap(True)
        server_label.setStyleSheet("font-size: 16px; color: #c0c0c0;")
        layout.addWidget(server_label)
        layout.addStretch()

        if managed:
            btn_manage = QPushButton(self.tr("Manage"))
            btn_manage.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_manage.setStyleSheet("padding: 4px 12px; font-weight: bold;")
            server_path = os.path.join("servers", name)
            btn_manage.clicked.connect(lambda _, n=name, p=server_path: ServerControlDialog(n, p, self).exec())
            layout.addWidget(btn_manage)

        btn_delete = QPushButton(self.tr("Delete"))
        btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_delete.setStyleSheet(
            "background-color: #fe4c4c; color: white; border-radius: 5px; padding: 3px 8px;"
        )
        btn_delete.clicked.connect(lambda _, n=name, m=managed: self.delete_server(n, m))
        layout.addWidget(btn_delete)

        self.container_layout.addWidget(container)

    # --- Удаление сервера ---
    def delete_server(self, server_name, managed):
        reply = QMessageBox.question(
            self,
            self.tr("Confirm deletion"),
            f"{self.tr('Are you sure you want to delete the server')} '{server_name}'? {self.tr('This action cannot be undone.')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.servers_list = [s for s in self.servers_list if s['name'] != server_name]
            self.save_servers()
            self.update_servers_ui()

            if managed:
                server_path = os.path.join("servers", server_name)
                if os.path.exists(server_path) and os.path.isdir(server_path):
                    try:
                        shutil.rmtree(server_path)
                    except Exception as e:
                        QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to delete folder')}:\n{e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperLauncher 1.4.0.8")
        self.setWindowIcon(QIcon("/home/artem/Downloads/LudvigAI/assets/icon.png"))
        self.resize(1080, 720)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #1e1e1e;")
        main_layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(110)
        sidebar.setStyleSheet("""
            QFrame { 
                background-color: #111111; 
                border-radius: 30px; 
                margin: 20px 10px; 
            }
            QPushButton { 
                background-color: transparent; 
                color: white; 
                font-size: 26px; 
                padding: 10px; 
                border: none; 
            }
            QPushButton:hover { 
                background-color: #3a3a3a; 
                border-radius: 12px; 
            }
            QPushButton:checked { 
                background-color: #4facfe; 
                color: black; 
                border-radius: 16px; 
                font-weight: bold; 
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        sidebar_layout.setSpacing(20)

        # Кнопки
        self.btn_home = QPushButton("🏠")
        self.btn_builds = QPushButton("🧩")
        self.btn_news = QPushButton("📢")
        self.btn_updates = QPushButton("🔄")
        self.btn_servers = QPushButton("🖧")
        self.btn_settings = QPushButton("⚙️")
        self.btn_minecraft = QPushButton("⛏️")

        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        buttons = [
            self.btn_home, self.btn_builds, self.btn_news, self.btn_updates,
            self.btn_servers, self.btn_settings, self.btn_minecraft
        ]
        for i, btn in enumerate(buttons):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.button_group.addButton(btn, i)
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch()

        # Pages
        self.pages = QStackedWidget()

        # Домашняя страница
        self.home_page = self.create_page(f"🏠 {self.tr('Welcome to SuperLauncher!')}")
        self.pages.addWidget(self.home_page)  # 0

        self.pages.addWidget(ModsPage())         # 1
        self.pages.addWidget(NewsPage())         # 2
        self.pages.addWidget(UpdatesPage())      # 3
        self.pages.addWidget(ServersPage())      # 4
        self.settings_page = SettingsPage(self)
        self.pages.addWidget(self.settings_page) # 5
        self.pages.addWidget(MinecraftLauncherPage())  # 6

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        self.button_group.buttonClicked.connect(self.on_button_clicked)
        self.btn_home.setChecked(True)

        # Потоки для запуска Minecraft
        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)
        self.pages.widget(6).start_button.clicked.connect(self.launch_game)

        # Discord RPC
        self.discord_rpc_thread = DiscordRPCThread(self)
        self.discord_rpc_thread.start()

        # Применяем настройки
        self.apply_settings()

    # --- Метод перевода с безопасной проверкой settings_page ---
    def tr(self, key: str) -> str:
        lang = "ru"  # язык по умолчанию
        if hasattr(self, "settings_page") and self.settings_page:
            lang = self.settings_page.config.get("language", "ru")
        return translations.get(lang, {}).get(key, key)

    def create_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setStyleSheet("font-size: 24px; margin: 30px; color: white;")
        layout.addWidget(label)
        layout.addStretch()
        return page

    def on_button_clicked(self, button):
        idx = self.button_group.id(button)
        self.pages.setCurrentIndex(idx)

    def update_progress(self, value, max_value, label):
        page = self.pages.widget(6)
        page.start_progress.setMaximum(max_value)
        page.start_progress.setValue(value)
        page.start_progress_label.setText(label)

    def state_update(self, running):
        page = self.pages.widget(6)
        page.start_button.setDisabled(running)
        page.start_progress.setVisible(running)
        page.start_progress_label.setVisible(running)

    def apply_settings(self):
        theme = self.settings_page.config.get("theme", "dark")
        if theme == "dark":
            self.setStyleSheet("background-color: #1e1e1e; color: white;")
        else:
            self.setStyleSheet("background-color: white; color: black;")

    def launch_game(self):
        page = self.pages.widget(6)
        config = self.settings_page.config
        version = page.version_select.currentText()
        username = page.username.text() or "player"

        if config.get("launch_mode") == "java" and config.get("java_path"):
            java_path = config["java_path"]
            print(f"Запуск Minecraft через Java: {java_path} с версией {version} и игроком {username}")
        else:
            self.launch_thread.launch_setup_signal.emit(version, username)
            self.launch_thread.start()

    def closeEvent(self, event):
        if self.discord_rpc_thread:
            self.discord_rpc_thread.stop()
        super().closeEvent(event)

    # --- Метод обновления домашней страницы при смене языка ---
    def refresh_home_page(self):
        if hasattr(self, "home_page"):
            home_text = self.tr("Welcome to SuperLauncher!")
            label = self.home_page.layout().itemAt(0).widget()
            label.setText(f"🏠 {home_text}")

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    
