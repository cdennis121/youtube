import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
                             QProgressBar, QFileDialog, QLabel, QMessageBox, QCheckBox, QListWidget, 
                             QListWidgetItem, QStyledItemDelegate)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QThreadPool, QSize
from PyQt6.QtGui import QColor, QPainter
from yt_dlp import YoutubeDL
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_ffmpeg_path():
    # Get the directory of the script or executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as a script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    ffmpeg_dir = os.path.join(base_path, 'ffmpeg/bin')
    
    if sys.platform.startswith('win'):
        return os.path.join(ffmpeg_dir, 'ffmpeg.exe')
    else:
        return os.path.join(ffmpeg_dir, 'ffmpeg')

def check_ffmpeg():
    ffmpeg_path = get_ffmpeg_path()
    return os.path.exists(ffmpeg_path)

def get_default_music_folder():
    if sys.platform.startswith('win'):
        return os.path.join(os.path.expanduser('~'), 'Music')
    elif sys.platform.startswith('darwin'):  # macOS
        return os.path.join(os.path.expanduser('~'), 'Music')
    else:  # Linux and other Unix-like systems
        return os.path.join(os.path.expanduser('~'), 'Music')

class ProgressDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        progress = index.data(Qt.ItemDataRole.UserRole)
        if progress is not None:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw progress bar
            bar_height = option.rect.height() // 2
            bar_y = option.rect.y() + (option.rect.height() - bar_height) // 2
            bar_width = option.rect.width() - 100  # Leave space for text
            
            # Background
            painter.setBrush(QColor(200, 200, 200))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(option.rect.x() + 80, bar_y, bar_width, bar_height, 5, 5)
            
            # Progress
            painter.setBrush(QColor(52, 152, 219))
            painter.drawRoundedRect(option.rect.x() + 80, bar_y, int(bar_width * progress / 100), bar_height, 5, 5)
            
            # Text
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(option.rect.x() + 80 + bar_width + 5, option.rect.y(), 
                             option.rect.width() - bar_width - 85, option.rect.height(), 
                             Qt.AlignmentFlag.AlignVCenter, f"{progress}%")
            
            painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 40)

class DownloadWorker(QThread):
    progress_signal = pyqtSignal(int, int)  # (row, progress)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, save_path, row):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.row = row

    def run(self):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.save_path, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [self.progress_hook],
                'ffmpeg_location': os.path.dirname(get_ffmpeg_path()),
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.finished_signal.emit(f"Downloaded: {self.url}")
        except Exception as e:
            self.error_signal.emit(f"Error downloading {self.url}: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%')
                percent = percent.replace('%', '').strip()
                percent_float = float(percent)
                self.progress_signal.emit(self.row, int(percent_float))
                self.status_signal.emit(f"Downloading {self.url}: {percent}%")
            except ValueError:
                self.progress_signal.emit(self.row, 0)
                self.status_signal.emit(f"Downloading {self.url}...")
        elif d['status'] == 'finished':
            self.status_signal.emit(f'Download complete for {self.url}. Converting to MP3...')

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int, int)  # Change this line
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    song_list_signal = pyqtSignal(list)

    def __init__(self, url, save_path, is_playlist, selected_songs=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_playlist = is_playlist
        self.selected_songs = selected_songs or []

    def run(self):
        try:
            if not check_ffmpeg():
                raise Exception("FFmpeg not found in the 'ffmpeg' folder.")

            self.status_signal.emit("Fetching video information...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'extract_flat': 'in_playlist',
                'ffmpeg_location': os.path.dirname(get_ffmpeg_path()),
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if 'entries' in info:
                    songs = [entry['title'] for entry in info['entries'] if entry.get('title')]
                    self.song_list_signal.emit(songs)
                    self.status_signal.emit(f"Found {len(songs)} songs in playlist '{info.get('title', 'Untitled')}'")
                else:
                    songs = [info['title']]
                    self.song_list_signal.emit(songs)
                    self.status_signal.emit(f"Found video: {info['title']}")

            # Wait for user selection before downloading
            while not self.selected_songs:
                self.msleep(100)

            self.status_signal.emit("Downloading selected song(s)...")
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i, song in enumerate(self.selected_songs):
                    worker = DownloadWorker(f"ytsearch:{song}", self.save_path, i)
                    worker.progress_signal.connect(lambda row, value: self.progress_signal.emit(row, value))  # Change this line
                    worker.status_signal.connect(self.status_signal.emit)
                    worker.error_signal.connect(self.error_signal.emit)
                    futures.append(executor.submit(worker.run))

                for future in as_completed(futures):
                    future.result()

            self.finished_signal.emit(f"All downloads completed. Files saved to {self.save_path}")
        except Exception as e:
            self.error_signal.emit(str(e))

class YouTubeToMP3(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.download_thread = None

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL (video or playlist)")
        self.url_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        url_layout.addWidget(self.url_input)

        self.fetch_btn = QPushButton("Fetch")
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.fetch_btn.clicked.connect(self.fetch_songs)
        url_layout.addWidget(self.fetch_btn)

        layout.addLayout(url_layout)

        # Playlist checkbox
        self.playlist_checkbox = QCheckBox("Fetch as playlist")
        self.playlist_checkbox.setChecked(True)  # Set default to checked
        self.playlist_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        layout.addWidget(self.playlist_checkbox)

        # Song list
        self.song_list = QListWidget()
        self.song_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 5px;
                font-size: 14px;
                background-color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e0e0e0;
                color: black;
            }
        """)
        self.song_list.setItemDelegate(ProgressDelegate())
        layout.addWidget(self.song_list)

        # Download button
        self.download_btn = QPushButton("Download Selected")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 10px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #555;
            }
        """)
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.setWindowTitle('YouTube to MP3 Downloader')
        self.setGeometry(300, 300, 500, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }
        """)

    def fetch_songs(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText("Please enter a valid YouTube URL")
            return

        is_playlist = self.playlist_checkbox.isChecked()

        self.download_thread = DownloadThread(url, "", is_playlist)
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.song_list_signal.connect(self.populate_song_list)
        self.download_thread.start()

        self.fetch_btn.setEnabled(False)

    def populate_song_list(self, songs):
        self.song_list.clear()
        for song in songs:
            item = QListWidgetItem(song)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, 0)  # Initialize progress to 0
            self.song_list.addItem(item)
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)

    def start_download(self):
        selected_songs = [self.song_list.item(i).text() for i in range(self.song_list.count()) 
                          if self.song_list.item(i).checkState() == Qt.CheckState.Checked]
        
        if not selected_songs:
            self.status_label.setText("Please select at least one song to download")
            return

        default_path = get_default_music_folder()
        save_path = QFileDialog.getExistingDirectory(self, "Select Directory", default_path)
        if not save_path:
            return

        self.download_thread.save_path = save_path
        self.download_thread.selected_songs = selected_songs
        self.download_thread.progress_signal.connect(self.update_song_progress)  # Change this line
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.show_error)

        self.download_btn.setEnabled(False)
        self.download_thread.start()  # Add this line

    def update_song_progress(self, row, value):
        item = self.song_list.item(row)
        if item:
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.song_list.update()
        self.progress_bar.setValue(value)  # Add this line to update the main progress bar

    def update_status(self, status):
        self.status_label.setText(status)

    def download_finished(self, result):
        self.status_label.setText(result)
        self.progress_bar.setValue(100)
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText("Error occurred")
        self.download_btn.setEnabled(True)
        self.fetch_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YouTubeToMP3()
    ex.show()
    sys.exit(app.exec())
