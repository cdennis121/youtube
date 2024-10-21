import PyInstaller.__main__
import os
import sys

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to your main script
main_script = os.path.join(script_dir, 'youtube_to_mp3.py')

# Path to the ffmpeg binary directory
ffmpeg_dir = os.path.join(script_dir, 'ffmpeg', 'bin')

PyInstaller.__main__.run([
    main_script,
    '--name=YouTube_to_MP3_Downloader',
    '--onefile',
    '--windowed',
    '--add-data', f'{ffmpeg_dir};ffmpeg/bin',
    '--add-binary', f'{os.path.join(ffmpeg_dir, "ffmpeg.exe")};ffmpeg/bin',
    '--hidden-import', 'pydub.exceptions',
    '--exclude-module', 'FixTk',
    '--exclude-module', 'tcl',
    '--exclude-module', 'tk',
    '--exclude-module', '_tkinter',
    '--exclude-module', 'tkinter',
    '--exclude-module', 'Tkinter',
    '--clean',
])
