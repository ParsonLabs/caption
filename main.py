import os
import sys
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import whisper
import tempfile
import torch  
import shutil
from pathlib import Path
from moviepy.config import change_settings


def configure_imagemagick():
    """Configure ImageMagick path properly"""
    potential_paths = [
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\convert.exe",
        r"C:\Program Files\ImageMagick-7.1.1-Q16\convert.exe",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ImageMagick-7.1.1-Q16-HDRI", "magick.exe"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ImageMagick", "magick.exe"),
    ]
    
    existing_paths = [p for p in potential_paths if os.path.exists(p)]
    
    if existing_paths:
        im_path = existing_paths[0]
        print(f"Found ImageMagick at: {im_path}")
        change_settings({"IMAGEMAGICK_BINARY": im_path})
        return True
    else:
        print("Warning: ImageMagick not found in common locations")
        try:
            import subprocess
            result = subprocess.run(["where", "magick"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                print(f"Found ImageMagick in PATH: {path}")
                change_settings({"IMAGEMAGICK_BINARY": path})
                return True
        except Exception as e:
            print(f"Error finding ImageMagick in PATH: {e}")
        
        print("ERROR: ImageMagick not found. Subtitles may not render correctly.")
        print("Please install ImageMagick from: https://imagemagick.org/script/download.php")
        print("  ... or continue without proper text rendering")
        return False

configure_imagemagick()

def detect_speech_segments(audio_path, min_silence_len=700, silence_thresh=-35, context_ms=300, pause_ms=500):
    """
    Detect non-silent parts of the audio with added context and smooth transitions
    
    Args:
        audio_path: Path to audio file
        min_silence_len: Minimum silence length in milliseconds
        silence_thresh: Audio level (in dB) below which is considered silence
        context_ms: Milliseconds of context to add before each speech segment
        pause_ms: Milliseconds of silence to retain at the end of each segment
    """
    audio = AudioSegment.from_file(audio_path)
    
    non_silent_chunks = detect_nonsilent(
        audio, 
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )
    
    non_silent_ranges = []
    for start, end in non_silent_chunks:
        context_start = max(0, start - context_ms)
        
        extended_end = end + pause_ms
        
        non_silent_ranges.append((context_start/1000, extended_end/1000))
    
    merged_ranges = []
    if non_silent_ranges:
        current_start, current_end = non_silent_ranges[0]
        for start, end in non_silent_ranges[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                if (start - current_end) * 1000 > (min_silence_len - pause_ms - context_ms):
                    merged_ranges.append((current_start, current_end))
                    current_start, current_end = start, end
                else:
                    current_end = end
        merged_ranges.append((current_start, current_end))
    
    print(f"Found {len(merged_ranges)} speech segments after merging overlaps and adding smooth transitions")
    return merged_ranges

def transcribe_audio(audio_path, use_gpu=True):
    """Transcribe audio using Whisper with GPU if available"""
    print("Loading Whisper model...")
    
    if use_gpu:
        try:
            if torch.cuda.is_available():
                device = "cuda"
                torch.cuda.init()
                print(f"Using GPU: {torch.cuda.get_device_name(0)}")
                print(f"CUDA Version: {torch.version.cuda}")
                print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                device = "cpu"
                print("CUDA is not available. Using CPU for transcription.")
                print(f"PyTorch version: {torch.__version__}")
        except Exception as e:
            device = "cpu"
            print(f"Error initializing GPU: {str(e)}")
            print("Falling back to CPU for transcription.")
    else:
        device = "cpu"
        print("GPU usage disabled. Using CPU for transcription.")
    
    try:
        model = whisper.load_model("base", device=device)
        print(f"Model loaded successfully on {device}")
        
        print("Transcribing audio...")
        result = model.transcribe(audio_path, language="en")
        
        return result["segments"]
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        if device == "cuda":
            print("Attempting fallback to CPU...")
            try:
                model = whisper.load_model("base", device="cpu")
                result = model.transcribe(audio_path, language="en")
                return result["segments"]
            except Exception as e2:
                print(f"CPU fallback also failed: {str(e2)}")
                return []
        return []

def create_subtitle_clips(transcription, video_width, video_height):
    """Create TextClips for each transcribed segment"""
    subtitle_clips = []
    
    try:
        for segment in transcription:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]
            
            try:
                txt_clip = (TextClip(text, fontsize=70, color='white', bg_color='black',
                                   stroke_color='black', stroke_width=2, 
                                   font='Arial-Bold', method='caption', align='center',
                                   size=(video_width * 0.9, None))
                           .set_position(('center', 'bottom'))
                           .set_start(start_time)
                           .set_end(end_time))
            except Exception as e:
                print(f"Error with default font, trying simplified version: {e}")
                txt_clip = (TextClip(text, fontsize=60, color='white',
                                   font='Arial', method='label', align='center')
                           .set_position(('center', 'bottom'))
                           .set_start(start_time)
                           .set_end(end_time))
            
            subtitle_clips.append(txt_clip)
    except Exception as e:
        print(f"Error creating subtitle clips: {e}")
    
    return subtitle_clips

def process_video(input_video, output_video=None, min_silence_len=700, silence_thresh=-35, context_ms=300, pause_ms=500, use_gpu=True, threads=4, fast_mode=True):
    """
    Process video by removing silent parts and adding subtitles
    
    Args:
        input_video: Path to input video
        output_video: Path to output video (optional)
        min_silence_len: Minimum silence length in milliseconds to be considered silence
        silence_thresh: Audio level (in dB) below which is considered silence
        context_ms: Milliseconds of context to add before each speech segment
        pause_ms: Milliseconds of silence to retain at the end of each segment
        use_gpu: Whether to use GPU for transcription
        threads: Number of threads to use for video processing
        fast_mode: Whether to use faster encoding (lower quality but much faster)
    """
    temp_dir = None
    try:
        if output_video is None:
            filename, ext = os.path.splitext(input_video)
            output_video = f"{filename}_processed{ext}"
        
        output_dir = os.path.dirname(os.path.abspath(output_video))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Loading video: {input_video}")
        video = VideoFileClip(input_video)
        
        video_duration = video.duration
        print(f"Video duration: {video_duration:.2f} seconds")
        
        temp_dir = tempfile.mkdtemp()
        temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")
        video.audio.write_audiofile(temp_audio_path, codec='pcm_s16le', verbose=False, logger=None)
        
        print("Detecting speech segments...")
        non_silent_ranges = detect_speech_segments(
            temp_audio_path, 
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            context_ms=context_ms,
            pause_ms=pause_ms
        )
        
        bounded_ranges = []
        for start, end in non_silent_ranges:
            if end > video_duration:
                print(f"Warning: Segment end time {end:.2f}s exceeds video duration {video_duration:.2f}s. Clamping to video end.")
                end = video_duration
            
            if start < video_duration and end > start:
                bounded_ranges.append((start, end))
        
        if len(bounded_ranges) != len(non_silent_ranges):
            print(f"Removed {len(non_silent_ranges) - len(bounded_ranges)} segments that were outside video bounds")
        
        print(f"Cutting out silent parts using {len(bounded_ranges)} valid segments...")
        video_clips = [video.subclip(start, end) for start, end in bounded_ranges]
        if not video_clips:
            print("No non-silent parts detected. Check your silence threshold.")
            return
        
        print(f"Concatenating {len(video_clips)} video segments...")
        final_video = concatenate_videoclips(video_clips)
        temp_concat_audio = os.path.join(temp_dir, "concat_audio.wav")
        print("Processing concatenated audio...")
        
        if hasattr(final_video.audio, 'write_audiofile'):
            if not hasattr(final_video.audio, 'fps') or final_video.audio.fps is None:
                if hasattr(video_clips[0].audio, 'fps') and video_clips[0].audio.fps is not None:
                    final_video.audio.fps = video_clips[0].audio.fps
                else:
                    final_video.audio.fps = 44100
            
            final_video.audio.write_audiofile(temp_concat_audio, codec='pcm_s16le', verbose=False, logger=None)
        else:
            temp_video_path = os.path.join(temp_dir, "temp_concat.mp4")
            final_video.write_videofile(temp_video_path, codec="libx264", audio_codec="aac", 
                                        verbose=False, logger=None, threads=threads, 
                                        preset='ultrafast' if fast_mode else 'medium')
            video_with_audio = VideoFileClip(temp_video_path)
            video_with_audio.audio.write_audiofile(temp_concat_audio, codec='pcm_s16le', verbose=False, logger=None)
        
        print("Transcribing audio for subtitles...")
        try:
            transcription = transcribe_audio(temp_concat_audio, use_gpu=use_gpu)
            
            if not transcription:
                print("Warning: No transcription generated. Creating video without subtitles.")
                final_video_with_subs = final_video
            else:
                print("Adding subtitles...")
                subtitle_clips = create_subtitle_clips(
                    transcription, 
                    final_video.w, 
                    final_video.h
                )
                
                if subtitle_clips:
                    final_video_with_subs = CompositeVideoClip([final_video] + subtitle_clips)
                else:
                    print("Warning: Failed to create subtitle clips. Creating video without subtitles.")
                    final_video_with_subs = final_video
        except Exception as e:
            print(f"Error during transcription process: {e}")
            print("Creating video without subtitles.")
            final_video_with_subs = final_video       

        print(f"Writing final video to: {output_video}")
        try:
            ffmpeg_params = []
            if fast_mode:
                base_params = [
                    '-preset', 'ultrafast',
                    '-tune', 'fastdecode',
                    '-crf', '23',
                    '-b:a', '128k'
                ]
                
                if sys.platform.startswith('win') and use_gpu and torch.cuda.is_available():
                    cuda_params = [
                        '-hwaccel', 'cuda',
                        '-hwaccel_output_format', 'cuda',
                        '-c:v', 'h264_nvenc'
                    ]
                    ffmpeg_params = base_params + cuda_params
                    print("Using NVIDIA hardware acceleration for encoding")
                elif sys.platform == 'darwin':
                    mac_params = [
                        '-c:v', 'h264_videotoolbox'
                    ]
                    ffmpeg_params = base_params + mac_params
                    print("Using macOS hardware acceleration for encoding")
                elif sys.platform.startswith('linux') and use_gpu:
                    try:
                        vaapi_check = subprocess.run(['vainfo'], capture_output=True, text=True)
                        if vaapi_check.returncode == 0:
                            vaapi_params = [
                                '-vaapi_device', '/dev/dri/renderD128',
                                '-hwaccel', 'vaapi', 
                                '-c:v', 'h264_vaapi'
                            ]
                            ffmpeg_params = base_params + vaapi_params
                            print("Using VAAPI hardware acceleration for encoding")
                        else:
                            ffmpeg_params = base_params
                            print("Hardware acceleration not available, using software encoding")
                    except:
                        ffmpeg_params = base_params
                        print("VAAPI not found, using software encoding")
                else:
                    ffmpeg_params = base_params
                    print("Using software encoding")
            else:
                ffmpeg_params = [
                    '-preset', 'slow',
                    '-crf', '18',
                    '-b:a', '192k'
                ]
            
            final_video_with_subs.write_videofile(
                output_video,
                codec="libx264",
                audio_codec="aac",
                threads=threads,  
                ffmpeg_params=ffmpeg_params,
                verbose=False,
                logger=None
            )
            print("Successfully created video with subtitles!")
        except Exception as e:
            print(f"Error writing final video: {e}")
            
            try:
                print("Attempting to write video without subtitles...")
                final_video.write_videofile(
                    output_video,
                    codec="libx264",
                    audio_codec="aac",
                    threads=threads,
                    ffmpeg_params=ffmpeg_params,
                    verbose=False,
                    logger=None
                )
                print("Successfully created video without subtitles.")
            except Exception as e2:
                print(f"Critical error: Could not write video at all: {e2}")
                return
    
    except Exception as e:
        print(f"Error processing video: {e}")
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                print("Cleaning up temporary files...")
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
        
        print("Processing complete.")

if __name__ == "__main__":
    import argparse
    import multiprocessing
    
    cpu_count = multiprocessing.cpu_count()
    
    parser = argparse.ArgumentParser(description="Process videos for social media by removing silence and adding subtitles")
    parser.add_argument("input_video", help="Path to the input video file")
    parser.add_argument("--output", "-o", help="Path to the output video file")
    parser.add_argument("--silence-length", "-sl", type=int, default=700, 
                        help="Minimum silence length in milliseconds to be removed (default: 700)")
    parser.add_argument("--silence-threshold", "-st", type=int, default=-35, 
                        help="Audio level (in dB) below which is considered silence (default: -35)")
    parser.add_argument("--context", "-c", type=int, default=300,
                        help="Milliseconds of context to add before each speech segment (default: 300)")
    parser.add_argument("--pause", "-p", type=int, default=500,
                        help="Milliseconds of silence to keep at the end of each segment (default: 500)")
    parser.add_argument("--no-gpu", action="store_true", 
                        help="Disable GPU usage even if available")
    parser.add_argument("--threads", "-t", type=int, default=cpu_count,
                        help=f"Number of threads to use for video processing (default: {cpu_count})")
    parser.add_argument("--high-quality", action="store_true",
                        help="Use higher quality (slower) encoding")
    
    args = parser.parse_args()
    
    use_gpu = True
    if args.no_gpu:
        use_gpu = False
    
    import time
    start_time = time.time()
    
    print(f"Processing with {args.threads} threads, {'GPU' if use_gpu else 'CPU'} transcription, " +
          f"and {'high quality' if args.high_quality else 'fast'} encoding...")
    
    process_video(
        args.input_video, 
        args.output, 
        min_silence_len=args.silence_length, 
        silence_thresh=args.silence_threshold,
        context_ms=args.context,
        pause_ms=args.pause,
        use_gpu=use_gpu,
        threads=args.threads,
        fast_mode=not args.high_quality
    )
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal processing time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")