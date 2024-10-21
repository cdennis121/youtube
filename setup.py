from setuptools import setup, find_packages

setup(
    name="YouTube_to_MP3_Downloader",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'yt-dlp',
        'pydub',
        'PyQt6',
    ],
    entry_points={
        'console_scripts': [
            'youtube_to_mp3=youtube_to_mp3:main',
        ],
    },
)
