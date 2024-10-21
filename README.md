# YouTube to MP3 Downloader

This application allows users to download YouTube videos or playlists and convert them to MP3 format using a simple graphical user interface.

## Requirements for Development

- Python 3.6 or higher
- pip (Python package installer)

## Installation for Development

1. Clone this repository or download the source code.

2. Navigate to the project directory in your terminal or command prompt.

3. Install the required dependencies by running:
   ```
   pip install -r requirements.txt
   ```

4. Download FFmpeg binaries for your operating system and place them in a directory named `ffmpeg/bin` in the project root. The directory structure should look like this:
   ```
   project_root/
   ├── ffmpeg/
   │   └── bin/
   │       ├── ffmpeg (or ffmpeg.exe on Windows)
   │       └── (other FFmpeg related files)
   ├── youtube_to_mp3.py
   ├── requirements.txt
   └── README.md
   ```

## Building the Application

To build the standalone application, run:

```
python build_app.py
```

This will create a `dist` directory containing the bundled application.

## Running the Application

To run the YouTube to MP3 Downloader, execute the following command in your terminal or command prompt:

```
python youtube_to_mp3.py
```

### For users:
After building the application, users can run the standalone executable found in the `dist` directory.

## How to Use

1. Launch the application.
2. Enter a valid YouTube URL in the input field.
3. Click the "Download" button.
4. Choose a directory to save the MP3 file.
5. Wait for the download and conversion process to complete.
6. The status label will show the path of the downloaded MP3 file once finished.

## Notes

- This application is for personal use only. Please respect copyright laws and YouTube's terms of service.
- Large videos may take some time to download and convert. Be patient and do not close the application during this process.
