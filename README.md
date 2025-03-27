<p align="center">
  <img src="https://avatars.githubusercontent.com/u/138057124?s=200&v=4" width="150" />
</p>
<h1 align="center">ParsonLabs Caption</h1>

<p align="center">
  <img width="1280" alt="image" src="https://github.com/user-attachments/assets/a633ab47-e29d-4df8-95fc-79ef02df68e3" />
</p>

<p align="center">
ParsonLabs Caption is a powerful tool that automatically removes silent parts from videos and adds subtitles, making it perfect for creating engaging social media clips, YouTube Shorts, TikToks, and more.
</p>

## Features

- **Smart Silence Detection**: Automatically detects and removes silent parts of videos
- **Smooth Transitions**: Preserves context around speech for natural-sounding cuts
- **Automatic Subtitles**: Uses OpenAI's Whisper model to generate accurate subtitles
- **GPU Acceleration**: Leverages CUDA (NVIDIA), VideoToolbox (macOS), or VAAPI (Linux) for faster processing
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Customizable**: Configure silence thresholds, context preservation, and video quality

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg
- ImageMagick
- PyTorch (with CUDA for GPU acceleration, optional)

### Step 1: Install dependencies

#### Windows:
```bash
# Install FFmpeg and ImageMagick
winget install ImageMagick
winget install FFmpeg

# Create a virtual environment
python -m venv init
init\Scripts\activate

# Install Python dependencies
pip install moviepy pydub openai-whisper torch torchvision torchaudio
```

#### macOS:
```bash
# Install FFmpeg and ImageMagick
brew install ffmpeg imagemagick

# Create a virtual environment
python -m venv init
source init/bin/activate

# Install Python dependencies
pip install moviepy pydub openai-whisper torch torchvision torchaudio
```

#### Linux:
```bash
# Install FFmpeg and ImageMagick
sudo apt-get update
sudo apt-get install ffmpeg imagemagick

# Create a virtual environment
python -m venv init
source init/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Clone the repository
```bash
git clone https://github.com/ParsonLabs/caption.git
cd caption
```

## Usage

### Basic Usage

```bash
python main.py input_video.mp4
```

This will generate `input_video_processed.mp4` with silent parts removed and subtitles added.

### Advanced Options

```bash
python main.py input_video.mp4 --output output.mp4 --silence-length 1500 --silence-threshold -35 --context 300 --pause 500
```

#### Parameters:

- `--output, -o`: Specify output file path
- `--silence-length, -sl`: Minimum silence length in milliseconds to be removed (default: 700)
- `--silence-threshold, -st`: Audio level (in dB) below which is considered silence (default: -35)
- `--context, -c`: Milliseconds of context to add before each speech segment (default: 300)
- `--pause, -p`: Milliseconds of silence to keep at the end of each segment (default: 500)
- `--no-gpu`: Disable GPU usage even if available
- `--threads, -t`: Number of threads to use for video processing (default: auto-detect)
- `--high-quality`: Use higher quality (slower) encoding

### Examples

#### Remove long pauses (1.5+ seconds)
```bash
python main.py input_video.mp4 --silence-length 1500
```

#### More aggressive silence removal
```bash
python main.py input_video.mp4 --silence-length 500 --silence-threshold -30
```

#### Higher quality output
```bash
python main.py input_video.mp4 --high-quality
```

#### Disable GPU (use CPU only)
```bash
python main.py input_video.mp4 --no-gpu
```

## How It Works

1. **Silence Detection**: Analyzes the audio track to find silent segments
2. **Smart Segmentation**: Cuts out silent parts while preserving context around speech
3. **Transcription**: Uses OpenAI's Whisper model to transcribe the audio
4. **Subtitle Generation**: Creates readable, properly timed subtitles
5. **Video Compilation**: Combines the non-silent video segments with subtitles

## Troubleshooting

### Subtitles not appearing
Make sure ImageMagick is properly installed and in your PATH.

### GPU acceleration not working
Check that you have:
- An NVIDIA GPU with CUDA support (Windows)
- Proper NVIDIA drivers installed
- CUDA-enabled PyTorch installation

### Slow processing
Try these options:
- Ensure GPU acceleration is enabled
- Increase thread count (`--threads`)
- Use fast mode (default) instead of `--high-quality`
- Process shorter videos first

### Poor cuts or speech detection
Adjust these parameters:
- Increase `--silence-threshold` to a higher negative number (e.g., -40) to detect more speech
- Decrease `--silence-length` to remove shorter pauses
- Increase `--context` to keep more context around speech segments

## License

MIT License

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech transcription
- [MoviePy](https://zulko.github.io/moviepy/) for video processing
- [PyDub](https://github.com/jiaaro/pydub) for audio analysis
