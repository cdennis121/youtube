import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QProgressBar, QFileDialog, QLabel, QMessageBox, QCheckBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from yt_dlp import YoutubeDL
from pydub import AudioSegment

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

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, save_path, is_playlist):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_playlist = is_playlist

    def run(self):
        try:
            if not check_ffmpeg():
                raise Exception("FFmpeg not found in the 'ffmpeg' folder.")

            self.status_signal.emit("Downloading video(s)...")
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
            
            if self.is_playlist:
                ydl_opts['yes_playlist'] = True
            else:
                ydl_opts['noplaylist'] = True
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if self.is_playlist:
                    playlist_title = info['title']
                    self.finished_signal.emit(f"Playlist '{playlist_title}' downloaded to {self.save_path}")
                else:
                    filename = ydl.prepare_filename(info)
                    mp3_file = os.path.splitext(filename)[0] + '.mp3'
                    self.finished_signal.emit(mp3_file)
        except Exception as e:
            self.error_signal.emit(str(e))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%')
                percent = percent.replace('%', '').strip()
                percent_float = float(percent)
                self.progress_signal.emit(int(percent_float))
                self.status_signal.emit(f"Downloading: {percent}%")
            except ValueError:
                self.progress_signal.emit(0)
                self.status_signal.emit("Downloading...")
        elif d['status'] == 'finished':
            self.status_signal.emit('Download complete. Converting to MP3...')

class YouTubeToMP3(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

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

        self.download_btn = QPushButton("Download")
        self.download_btn.setStyleSheet("""
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
        self.download_btn.clicked.connect(self.start_download)
        url_layout.addWidget(self.download_btn)

        layout.addLayout(url_layout)

        # Playlist checkbox
        self.playlist_checkbox = QCheckBox("Download as playlist")
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
        self.setGeometry(300, 300, 500, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }
        """)

    def start_download(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText("Please enter a valid YouTube URL")
            return

        default_path = get_default_music_folder()
        save_path = QFileDialog.getExistingDirectory(self, "Select Directory", default_path)
        if not save_path:
            return

        is_playlist = self.playlist_checkbox.isChecked()

        self.download_thread = DownloadThread(url, save_path, is_playlist)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.status_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

        self.download_btn.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, status):
        self.status_label.setText(status)

    def download_finished(self, result):
        self.status_label.setText(f"Download completed: {result}")
        self.progress_bar.setValue(100)
        self.download_btn.setEnabled(True)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText("Error occurred")
        self.download_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YouTubeToMP3()
    ex.show()
    sys.exit(app.exec())
