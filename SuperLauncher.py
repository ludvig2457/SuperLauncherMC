import sys
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QStackedWidget, QButtonGroup, QLineEdit, QComboBox,
    QProgressBar, QSpacerItem, QSizePolicy, QMessageBox, QScrollArea, QDialog,
    QCheckBox, QFormLayout, QListWidget, QListWidgetItem, QTextEdit, QSpinBox,
    QRadioButton, QFileDialog
)
from PyQt6.QtGui import QPixmap, QCursor, QGuiApplication

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command
from tqdm import tqdm

from random_username.generate import generate_username
from uuid import uuid1
import subprocess
import requests
import threading
from pathlib import Path
import json
import shutil
import psutil
import zipfile

CONFIG_FILE = "settings.json"

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
print("Путь к Minecraft:", minecraft_directory)

if not os.path.exists(minecraft_directory):
    print("Папка Minecraft не найдена! Создаю...")
    os.makedirs(minecraft_directory, exist_ok=True)

print("Содержимое папки Minecraft:", os.listdir(minecraft_directory))

profile_path = os.path.join(minecraft_directory, 'launcher_profiles.json')
print("Путь к launcher_profiles.json:", profile_path)

if not os.path.isfile(profile_path):
    print("launcher_profiles.json не найден, создаю новый...")
    empty_profile = {
        "profiles": {},
        "settings": {},
        "selectedProfile": None
    }
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(empty_profile, f, indent=4)
    print("Создан пустой launcher_profiles.json")
else:
    print("launcher_profiles.json уже существует")

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

            cmd = get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options)
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
    def __init__(self):
        super().__init__()

        self.logo = QLabel()
        self.logo.setMaximumSize(QSize(256, 37))
        pixmap = QPixmap('assets/title.png')
        if not pixmap.isNull():
            self.logo.setPixmap(pixmap)
            self.logo.setScaledContents(True)

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.username.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 5px;
        """)

        self.version_select = QComboBox()
        self.version_select.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 3px;
        """)

        self.update_versions_list()

        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.start_progress_label = QLabel('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar()
        self.start_progress.setValue(0)
        self.start_progress.setVisible(False)

        self.start_button = QPushButton('Play')
        self.start_button.setStyleSheet("""
            background-color: #2f2f2f;
            color: white;
            border: 1px solid #4facfe;
            border-radius: 8px;
            padding: 8px;
            font-weight: bold;
        """)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)

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

    def update_versions_list(self):
        self.version_select.clear()
        versions = get_all_versions()
        for version in versions:
            self.version_select.addItem(version['id'])

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Тема
        layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "dark"))
        layout.addWidget(self.theme_combo)

        # Язык
        layout.addWidget(QLabel("Язык:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ru", "en"])
        self.lang_combo.setCurrentText(self.config.get("language", "ru"))
        layout.addWidget(self.lang_combo)

        # Способ запуска
        layout.addWidget(QLabel("Способ запуска Minecraft:"))
        self.rb_launcher_lib = QRadioButton("minecraft-launcher-lib (по умолчанию)")
        self.rb_java = QRadioButton("Java (указать путь)")
        layout.addWidget(self.rb_launcher_lib)
        layout.addWidget(self.rb_java)

        launch_mode = self.config.get("launch_mode", "launcher_lib")
        if launch_mode == "java":
            self.rb_java.setChecked(True)
        else:
            self.rb_launcher_lib.setChecked(True)

        # Путь к Java
        layout.addWidget(QLabel("Путь к Java (если выбран Java):"))
        self.java_path_input = QLineEdit(self.config.get("java_path", ""))
        layout.addWidget(self.java_path_input)
        btn_browse_java = QPushButton("Выбрать путь к Java")
        layout.addWidget(btn_browse_java)

        btn_browse_java.clicked.connect(self.browse_java)

        # Активность поля пути и кнопки в зависимости от выбора
        self.java_path_input.setEnabled(self.rb_java.isChecked())
        btn_browse_java.setEnabled(self.rb_java.isChecked())
        self.rb_java.toggled.connect(self.java_path_input.setEnabled)
        self.rb_java.toggled.connect(btn_browse_java.setEnabled)

        # Кнопка сохранить
        self.save_btn = QPushButton("Сохранить настройки")
        layout.addWidget(self.save_btn)
        self.save_btn.clicked.connect(self.save_settings)

        self.setLayout(layout)

    def browse_java(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выберите java.exe", "", "Executable Files (*.exe);;All Files (*)")
        if file:
            self.java_path_input.setText(file)

    def save_settings(self):
        self.config["theme"] = self.theme_combo.currentText()
        self.config["language"] = self.lang_combo.currentText()
        self.config["launch_mode"] = "java" if self.rb_java.isChecked() else "launcher_lib"
        self.config["java_path"] = self.java_path_input.text()
        save_config(self.config)
        if self.parent():
            self.parent().apply_settings()

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

class ModsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        self.mods_dir = os.path.join(minecraft_directory, "mods")
        os.makedirs(self.mods_dir, exist_ok=True)

        title = QLabel("🧩 Моды из Modrinth")
        title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 10px; color: white;")
        self.layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Найти мод...")
        self.search_input.returnPressed.connect(self.search_mods)
        self.layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        self.results_list.setIconSize(QSize(64, 64))
        self.layout.addWidget(self.results_list)

        buttons_layout = QHBoxLayout()

        open_folder_button = QPushButton("📂 Открыть папку модов")
        open_folder_button.clicked.connect(self.open_mods_folder)
        buttons_layout.addWidget(open_folder_button)

        delete_all_button = QPushButton("🗑 Удалить все моды")
        delete_all_button.setStyleSheet("background-color: #d9534f; color: white;")
        delete_all_button.clicked.connect(self.delete_all_mods)
        buttons_layout.addWidget(delete_all_button)

        self.layout.addLayout(buttons_layout)

        self.load_featured_mods()

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
            QMessageBox.critical(self, "Ошибка", str(e))

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
            QMessageBox.critical(self, "Ошибка поиска", str(e))

    def show_mod_dialog(self, item):
        project_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            versions_url = f"{MODRINTH_API}/project/{project_id}/version"
            resp = requests.get(versions_url)
            versions = resp.json()

            if not versions:
                QMessageBox.warning(self, "Нет доступных версий", "Для этого мода пока нет доступных загрузок.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Установка мода")
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
                QMessageBox.warning(self, "Нет поддерживаемых билдов", "Нет совместимых версий для установки.")
                return

            version_box.addItems(version_loader_map.keys())
            layout.addWidget(QLabel("Версия Minecraft и ядро:"))
            layout.addWidget(version_box)

            install_button = QPushButton("Установить")
            layout.addWidget(install_button)

            install_button.clicked.connect(
                lambda: self.download_selected_mod(version_loader_map[version_box.currentText()], dialog)
            )

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

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
        QMessageBox.warning(self, "Файл не найден", "Не удалось найти подходящий .jar файл.")

    def start_download(self, url, save_path):
        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle("Загрузка мода")
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
            QMessageBox.critical(self, "Ошибка загрузки", result)
        else:
            QMessageBox.information(self, "Готово", f"Мод успешно установлен:\n{result}")

    def open_mods_folder(self):
        path = os.path.realpath(self.mods_dir)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f"open \"{path}\"")
        else:
            os.system(f"xdg-open \"{path}\"")

    def delete_all_mods(self):
        confirm = QMessageBox.question(self, "Подтверждение",
            "Ты уверен, что хочешь удалить **все моды**?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            deleted = 0
            for file in os.listdir(self.mods_dir):
                if file.endswith(".jar"):
                    try:
                        os.remove(os.path.join(self.mods_dir, file))
                        deleted += 1
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Не удалось удалить {file}: {e}")
            QMessageBox.information(self, "Готово", f"Удалено модов: {deleted}")

class NewsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel("📢 Новости")
        title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: white;")
        layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        container = QWidget()
        scroll_area.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        news_list = [
            ("2025-07-12", "Добавлен новый сервер в мультиплеер"),
            ("2025-07-10", "Добавлена новая версия Minecraft 1.20.1"),
            ("2025-07-05", "Исправлены ошибки при запуске игры"),
        ]

        for date, text in news_list:
            news_label = QLabel(f"<b>{date}</b>: {text}")
            news_label.setWordWrap(True)
            news_label.setStyleSheet("font-size: 16px; color: #c0c0c0;")
            container_layout.addWidget(news_label)

        container_layout.addStretch()

class UpdateDownloadThread(QThread):
    progress = pyqtSignal(int)  # процент загрузки
    finished = pyqtSignal(str)  # путь к сохранённому файлу или ошибка

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        try:
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(self.filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length > 0:
                                percent = int(downloaded * 100 / total_length)
                                self.progress.emit(percent)
            self.finished.emit(self.filename)
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")

class UpdatesPage(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.title = QLabel("🔄 Обновления")
        self.title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: white;")
        self.layout.addWidget(self.title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.scroll_area.setWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(12)

        self.status_label = QLabel("Загрузка списка обновлений...")
        self.status_label.setStyleSheet("color: #c0c0c0; font-size: 14px;")
        self.layout.addWidget(self.status_label)

        self.fetch_releases()

    def fetch_releases(self):
        def task():
            try:
                response = requests.get('https://api.github.com/repos/ludvig2457/SuperLauncher/releases')
                response.raise_for_status()
                releases = response.json()
                self.update_ui_with_releases(releases)
            except Exception as e:
                self.status_label.setText(f"Ошибка при загрузке релизов: {e}")

        from threading import Thread
        Thread(target=task, daemon=True).start()

    def update_ui_with_releases(self, releases):
        from PyQt6.QtCore import QTimer

        def add_release_widgets():
            self.status_label.hide()

            if not releases:
                self.container_layout.addWidget(QLabel("Релизы не найдены."))
                return

            for release in releases:
                version = release.get('tag_name', 'N/A')
                name = release.get('name', '')
                body = release.get('body', '')
                published_at = release.get('published_at', 'N/A')
                assets = release.get('assets', [])

                release_widget = QWidget()
                layout = QVBoxLayout(release_widget)
                layout.setSpacing(6)
                layout.setContentsMargins(6, 6, 6, 6)

                ver_label = QLabel(f"<b>Версия:</b> {version}")
                ver_label.setStyleSheet("color: white; font-size: 18px;")
                layout.addWidget(ver_label)

                date_label = QLabel(f"<b>Дата:</b> {published_at}")
                date_label.setStyleSheet("color: #a0a0a0; font-size: 14px;")
                layout.addWidget(date_label)

                body_label = QLabel(body.replace('\n', '<br>'))
                body_label.setWordWrap(True)
                body_label.setStyleSheet("color: #c0c0c0; font-size: 14px; max-height: 80px;")
                layout.addWidget(body_label)

                btn_layout = QHBoxLayout()
                btn_layout.addStretch()

                for asset in assets:
                    asset_name = asset.get('name')
                    download_url = asset.get('browser_download_url')

                    btn = QPushButton(f"Скачать {asset_name}")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.clicked.connect(
                        lambda checked, url=download_url, name=asset_name: self.download_asset(url, name)
                    )
                    btn_layout.addWidget(btn)

                layout.addLayout(btn_layout)
                layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                release_widget.setStyleSheet("background-color: #222; border-radius: 8px; padding: 10px;")
                self.container_layout.addWidget(release_widget)

            self.container_layout.addStretch()

        QTimer.singleShot(0, add_release_widgets)

    def download_asset(self, url, name):
        from pathlib import Path
        downloads_path = Path.home() / "Downloads"
        downloads_path.mkdir(exist_ok=True)
        save_path = downloads_path / name

        self.progress_dialog = QDialog(self)
        self.progress_dialog.setWindowTitle(f"Загрузка {name}")
        self.progress_dialog.setModal(True)
        layout = QVBoxLayout(self.progress_dialog)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.progress_dialog.show()

        self.download_thread = UpdateDownloadThread(url, str(save_path))
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def download_finished(self, result):
        self.progress_dialog.hide()
        if result.startswith("ERROR:"):
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {result}")
        else:
            QMessageBox.information(self, "Загрузка завершена", f"Файл сохранён: {result}")

class CreateServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать свой сервер Minecraft")
        self.setFixedSize(350, 220)

        layout = QFormLayout(self)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Имя сервера")

        self.input_port = QLineEdit()
        self.input_port.setPlaceholderText("Порт (например, 25565)")
        self.input_port.setText("25565")

        self.combo_version = QComboBox()
        self.combo_version.addItems(["1.20.4", "1.20.1", "1.19.4"])  # Можно расширить

        self.combo_core = QComboBox()
        self.combo_core.addItems(["Paper", "Purpur", "Vanilla"])

        layout.addRow("Имя сервера:", self.input_name)
        layout.addRow("Порт:", self.input_port)
        layout.addRow("Версия:", self.combo_version)
        layout.addRow("Ядро:", self.combo_core)

        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton("Создать")
        self.btn_cancel = QPushButton("Отмена")
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_cancel)
        layout.addRow(btn_layout)

        self.btn_create.clicked.connect(self.create_server)
        self.btn_cancel.clicked.connect(self.reject)

    def create_server(self):
        name = self.input_name.text().strip()
        port = self.input_port.text().strip()
        version = self.combo_version.currentText()
        core = self.combo_core.currentText()

        if not name or not port.isdigit():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректное имя и порт (число).")
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
        self.setWindowTitle(f"Управление сервером '{server_name}'")
        self.setFixedSize(350, 300)  # чуть выше, чтобы поместился чекбокс playit
        self.server_path = server_path
        self.process = None
        self.playit_process = None

        layout = QVBoxLayout(self)

        label = QLabel(f"Управление сервером: {server_name}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Чекбокс согласия с EULA
        self.checkbox_eula = QCheckBox("Я принимаю лицензионное соглашение EULA")
        layout.addWidget(self.checkbox_eula)

        # Чекбокс оффлайн режима (пиратки)
        self.checkbox_offline = QCheckBox("Включить оффлайн режим (пиратка)")
        layout.addWidget(self.checkbox_offline)

        # Чекбокс использования playit.gg
        self.checkbox_playit = QCheckBox("Использовать playit.gg (туннель)")
        layout.addWidget(self.checkbox_playit)

        # Кнопка сохранить настройки
        btn_save_settings = QPushButton("Сохранить настройки")
        btn_save_settings.clicked.connect(self.save_settings)
        layout.addWidget(btn_save_settings)

        self.btn_start = QPushButton("Запустить сервер")
        self.btn_stop = QPushButton("Остановить сервер")
        self.btn_close = QPushButton("Закрыть")

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_close)

        self.btn_start.clicked.connect(self.start_server)
        self.btn_stop.clicked.connect(self.stop_server)
        self.btn_close.clicked.connect(self.close)

        self.update_buttons()
        self.load_settings()

    def load_settings(self):
        # eula.txt
        eula_path = os.path.join(self.server_path, "eula.txt")
        if os.path.isfile(eula_path):
            with open(eula_path, "r", encoding="utf-8") as f:
                text = f.read()
            self.checkbox_eula.setChecked("eula=true" in text.lower())
        else:
            self.checkbox_eula.setChecked(False)

        # server.properties (online-mode)
        prop_path = os.path.join(self.server_path, "server.properties")
        if os.path.isfile(prop_path):
            with open(prop_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            online_mode = True
            for line in lines:
                if line.startswith("online-mode="):
                    online_mode = line.strip().split("=")[1].lower() == "true"
                    break
            self.checkbox_offline.setChecked(not online_mode)
        else:
            self.checkbox_offline.setChecked(False)

        # Здесь можно расширить, чтобы сохранять и загружать состояние playit (например, файл playit_settings.json)
        # Пока по умолчанию отключаем
        self.checkbox_playit.setChecked(False)

    def save_settings(self):
        # eula.txt
        eula_path = os.path.join(self.server_path, "eula.txt")
        try:
            with open(eula_path, "w", encoding="utf-8") as f:
                f.write(f"eula={'true' if self.checkbox_eula.isChecked() else 'false'}\n")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить eula.txt:\n{e}")
            return

        # server.properties (online-mode)
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
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить server.properties:\n{e}")
            return

        QMessageBox.information(self, "Успех", "Настройки сохранены!")

    def update_buttons(self):
        running = self.process is not None and self.process.poll() is None
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def download_and_install_playit(self):
        import requests

        msi_url = "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-windows-x86_64-signed.msi"
        import tempfile
        import os

        temp_dir = tempfile.gettempdir()
        msi_path = os.path.join(temp_dir, "playit-agent.msi")

        if not os.path.isfile(msi_path):
            try:
                response = requests.get(msi_url, stream=True)
                response.raise_for_status()
                with open(msi_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                os.system(f'powershell -Command "Unblock-File -Path \'{msi_path}\'"')
            except Exception as e:
                QMessageBox.critical(self, "Ошибка скачивания", f"Не удалось скачать playit MSI:\n{e}")
                return False

        try:
            result = subprocess.run(
                ["msiexec", "/i", msi_path, "/quiet", "/qn"],
                capture_output=True,
                text=True,
                shell=False
            )
            if result.returncode != 0:
                # Создаем QMessageBox с кнопкой "Копировать путь"
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Ошибка установки")
                msg.setText(f"Установка завершилась с ошибкой (код {result.returncode}):\n{result.stderr.strip()}\n\nПопробуйте открыть файл вручную:")

                # Кнопка копирования пути
                btn_copy = QPushButton("Копировать путь к MSI")
                def copy_path():
                    QApplication.clipboard().setText(msi_path)
                    btn_copy.setText("Скопировано!")
                btn_copy.clicked.connect(copy_path)

                # Добавляем кнопку в диалог
                layout = msg.layout()
                layout.addWidget(btn_copy, layout.rowCount(), 0, 1, layout.columnCount())

                msg.exec()
                return False

            QMessageBox.information(self, "Установка", "Playit-agent успешно установлен.")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка установки", f"Не удалось установить playit:\n{e}")
            return False

    def start_playit(self):
        possible_paths = [
            os.path.expandvars(r"%ProgramFiles%\playit\playit.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\playit\playit.exe"),
            os.path.join(self.server_path, "playit.exe"),
        ]
        playit_exe = None
        for path in possible_paths:
            if os.path.isfile(path):
                playit_exe = path
                break

        if not playit_exe:
            installed = self.download_and_install_playit()
            if not installed:
                return False
            for path in possible_paths:
                if os.path.isfile(path):
                    playit_exe = path
                    break
            if not playit_exe:
                QMessageBox.warning(self, "playit.gg", "Не удалось найти playit.exe после установки.")
                return False

        try:
            self.playit_process = subprocess.Popen([playit_exe], cwd=os.path.dirname(playit_exe))
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка запуска playit", str(e))
            return False

    def stop_playit(self):
        if self.playit_process and self.playit_process.poll() is None:
            try:
                self.playit_process.terminate()
                self.playit_process.wait(timeout=5)
            except Exception:
                self.playit_process.kill()
            finally:
                self.playit_process = None

    def start_server(self):
        if self.process is None or self.process.poll() is not None:
            if not self.checkbox_eula.isChecked():
                QMessageBox.warning(self, "EULA", "Вы должны принять лицензионное соглашение EULA!")
                return

            bat_path = os.path.join(self.server_path, "start.bat")
            if not os.path.isfile(bat_path):
                QMessageBox.warning(self, "Ошибка", "Файл start.bat не найден!")
                return

            try:
                self.process = subprocess.Popen(
                    ["cmd.exe", "/k", "start.bat"],
                    cwd=self.server_path,
                    shell=True
                )
                if self.checkbox_playit.isChecked():
                    started = self.start_playit()
                    if not started:
                        QMessageBox.warning(self, "playit.gg", "Туннель playit.gg не будет запущен.")
                QMessageBox.information(self, "Запуск", "Сервер запущен.")
                self.update_buttons()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка запуска", str(e))
        else:
            QMessageBox.information(self, "Информация", "Сервер уже запущен.")
            self.update_buttons()

    def stop_server(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.stop_playit()  # Останавливаем playit при остановке сервера
                QMessageBox.information(self, "Остановка", "Сервер остановлен.")
            except Exception:
                self.process.kill()
                self.stop_playit()
                QMessageBox.information(self, "Остановка", "Сервер принудительно остановлен.")
            finally:
                self.process = None
                self.update_buttons()
        else:
            QMessageBox.information(self, "Информация", "Сервер не запущен.")
            self.update_buttons()

class ServersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.servers_file = "servers_list.json"
        self.servers_list = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        title = QLabel("🖧 Серверы Minecraft")
        title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px; color: white;")
        self.layout.addWidget(title)

        self.btn_create_server = QPushButton("Создать свой сервер")
        self.btn_create_server.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_create_server.setStyleSheet(
            "padding: 8px; font-weight: bold; background-color: #4facfe; color: black; border-radius: 8px;"
        )
        self.btn_create_server.clicked.connect(self.open_create_server_dialog)
        self.layout.addWidget(self.btn_create_server)

        form_layout = QHBoxLayout()
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Имя сервера")
        self.input_ip = QLineEdit()
        self.input_ip.setPlaceholderText("IP или домен")

        self.btn_add_server = QPushButton("Добавить сервер")
        self.btn_add_server.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_server.clicked.connect(self.add_server)

        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_ip)
        form_layout.addWidget(self.btn_add_server)
        self.layout.addLayout(form_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

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

        QMessageBox.information(self, "Готово", f"Сервер '{name}' успешно создан!")

    def on_download_error(self, error_message):
        self.progress_bar.hide()
        QMessageBox.critical(self, "Ошибка загрузки", error_message)

    def generate_start_bat(self, path):
        with open(os.path.join(path, "start.bat"), "w", encoding="utf-8") as f:
            f.write("""@echo off
java -Xmx2G -Xms2G -jar server.jar nogui
pause
""")

    def load_servers(self):
        try:
            with open(self.servers_file, "r", encoding="utf-8") as f:
                self.servers_list = json.load(f)
        except Exception:
            self.servers_list = [
                {"name": "Игровой сервер 1", "ip": "play.server1.ru", "managed": False},
                {"name": "Игровой сервер 2", "ip": "mc.server2.com", "managed": False},
                {"name": "Приватный сервер", "ip": "192.168.1.100", "managed": False},
                {"name": "Тестовый сервер", "ip": "test.mc.example.com", "managed": False},
            ]

    def save_servers(self):
        try:
            with open(self.servers_file, "w", encoding="utf-8") as f:
                json.dump(self.servers_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Ошибка сохранения серверов:", e)

    def update_servers_ui(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for server in self.servers_list:
            name = server['name']
            ip = server['ip']
            managed = server.get('managed', False)
            self.add_server_widget(name, ip, managed)

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
            btn_manage = QPushButton("Управление")
            btn_manage.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_manage.setStyleSheet("padding: 4px 12px; font-weight: bold;")

            server_path = os.path.join("servers", name)

            def open_control():
                dlg = ServerControlDialog(name, server_path, self)
                dlg.exec()

            btn_manage.clicked.connect(open_control)
            layout.addWidget(btn_manage)

        btn_delete = QPushButton("Удалить")
        btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_delete.setStyleSheet("background-color: #fe4c4c; color: white; border-radius: 5px; padding: 3px 8px;")
        btn_delete.clicked.connect(lambda _, n=name, m=managed: self.delete_server(n, m))
        layout.addWidget(btn_delete)

        self.container_layout.addWidget(container)

    def delete_server(self, server_name, managed):
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить сервер '{server_name}'? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Удаляем из списка
            self.servers_list = [s for s in self.servers_list if s['name'] != server_name]
            self.save_servers()
            self.update_servers_ui()

            # Если управляемый — удаляем папку с проверкой
            if managed:
                server_path = os.path.join("servers", server_name)
                if os.path.exists(server_path) and os.path.isdir(server_path):
                    self.try_remove_server_folder(server_path)

    def try_remove_server_folder(self, folder_path):
        try:
            shutil.rmtree(folder_path)
        except PermissionError as e:
            blocking_procs = self.find_processes_using_path(folder_path)

            if blocking_procs:
                proc_names = "\n".join(f"{p.name()} (PID {p.pid})" for p in blocking_procs)
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Папка занята")
                msg.setText(f"Не удалось удалить папку, так как её используют процессы:\n{proc_names}\n\n"
                            "Хотите завершить эти процессы и попробовать снова?")
                btn_yes = msg.addButton("Завершить процессы", QMessageBox.ButtonRole.AcceptRole)
                btn_no = msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
                msg.exec()

                if msg.clickedButton() == btn_yes:
                    for proc in blocking_procs:
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                    psutil.wait_procs(blocking_procs, timeout=3)
                    try:
                        shutil.rmtree(folder_path)
                        QMessageBox.information(self, "Успех", "Папка успешно удалена после завершения процессов.")
                    except Exception as e2:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось удалить папку после завершения процессов:\n{e2}")
                else:
                    QMessageBox.information(self, "Отмена", "Удаление папки отменено.")
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить папку:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить папку:\n{e}")

    def find_processes_using_path(self, path):
        blocking = []
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                files = proc.info['open_files']
                if files:
                    for f in files:
                        if f.path.startswith(os.path.abspath(path)):
                            blocking.append(proc)
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return blocking

    def add_server(self):
        name = self.input_name.text().strip()
        ip = self.input_ip.text().strip()

        if not name or not ip:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните имя и IP сервера.")
            return

        self.servers_list.append({"name": name, "ip": ip, "managed": False})
        self.save_servers()
        self.update_servers_ui()

        self.input_name.clear()
        self.input_ip.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperLauncher 1.4.0.5")
        self.resize(1080, 720)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #1e1e1e;")

        main_layout = QHBoxLayout(central_widget)

        sidebar = QFrame()
        sidebar.setFixedWidth(110)
        sidebar.setStyleSheet("""
        QFrame {
            background-color: #121212;
            border-radius: 30px;
            margin: 20px 10px;
        }
        QPushButton {
            background-color: transparent;
            color: white;
            font-size: 26px;
            padding: 10px;
            border: none;
            outline: none;
        }
        QPushButton:focus {
            outline: none;
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
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
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
            self.btn_home, self.btn_builds, self.btn_news,
            self.btn_updates, self.btn_servers,
            self.btn_settings, self.btn_minecraft
        ]

        for i, btn in enumerate(buttons):
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.button_group.addButton(btn, i)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_page("🏠 Добро пожаловать в SuperLauncher!"))      # 0
        self.builds_page = ModsPage()  # Твой класс, предполагается определён
        self.pages.addWidget(self.builds_page)  # 1
        self.news_page = NewsPage()  # Твой класс
        self.pages.addWidget(self.news_page)                                               # 2
        self.updates_page = UpdatesPage()  # Твой класс
        self.pages.addWidget(self.updates_page)                                           # 3
        self.servers_page = ServersPage()  # Твой класс
        self.pages.addWidget(self.servers_page)                                           # 4

        # Заменяем пустую страницу настроек на SettingsPage
        self.settings_page = SettingsPage(self)
        self.pages.addWidget(self.settings_page)                                         # 5

        self.minecraft_page = MinecraftLauncherPage()  # Твой класс
        self.pages.addWidget(self.minecraft_page)                                         # 6

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

        self.button_group.buttonClicked.connect(self.on_button_clicked)
        self.btn_home.setChecked(True)  # По умолчанию первая кнопка

        # Поток запуска
        self.launch_thread = LaunchThread()  # Твой класс
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.minecraft_page.start_button.clicked.connect(self.launch_game)

        # Применяем сохранённые настройки UI
        self.apply_settings()

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
        self.minecraft_page.start_progress.setMaximum(max_value)
        self.minecraft_page.start_progress.setValue(value)
        self.minecraft_page.start_progress_label.setText(label)

    def state_update(self, running):
        self.minecraft_page.start_button.setDisabled(running)
        self.minecraft_page.start_progress.setVisible(running)
        self.minecraft_page.start_progress_label.setVisible(running)

    def apply_settings(self):
        config = self.settings_page.config
        theme = config.get("theme", "dark")
        if theme == "dark":
            self.setStyleSheet("background-color: #1e1e1e; color: white;")
        else:
            self.setStyleSheet("background-color: white; color: black;")

        # TODO: переключение языка UI

    def launch_game(self):
        config = self.settings_page.config
        version = self.minecraft_page.version_select.currentText()
        username = self.minecraft_page.username.text() or "player"

        if config.get("launch_mode") == "java" and config.get("java_path"):
            java_path = config["java_path"]
            # Здесь надо реализовать запуск через java_path
            print(f"Запуск Minecraft через Java: {java_path} с версией {version} и игроком {username}")
            # Можно вызвать subprocess.Popen с нужными параметрами
        else:
            self.launch_thread.launch_setup_signal.emit(version, username)
            self.launch_thread.start()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
