import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import time
import subprocess
import multiprocessing

class CaptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ParsonLabs Caption - Remove Silence & Add Subtitles")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        try:
            self.root.iconbitmap("Assets/parsonlabs.ico")
        except:
            pass
        
        self.create_file_section()
        
        self.create_parameters_section()
        
        self.create_processing_options()
        
        self.create_log_section()
        
        self.create_action_buttons()
        
        self.processing = False
        
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_file_section(self):
        file_frame = ttk.LabelFrame(self.root, text="Video Files")
        file_frame.pack(fill="x", expand=False, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Input Video:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Browse...", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(file_frame, text="Output Video:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Browse...", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        file_frame.columnconfigure(1, weight=1)
    
    def create_parameters_section(self):
        params_frame = ttk.LabelFrame(self.root, text="Silence Detection Parameters")
        params_frame.pack(fill="x", expand=False, padx=10, pady=5)
        
        ttk.Label(params_frame, text="Silence Length (ms):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.silence_length = tk.IntVar(value=700)
        ttk.Spinbox(params_frame, from_=100, to=5000, increment=100, textvariable=self.silence_length, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(params_frame, text="Minimum silence duration to remove").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(params_frame, text="Silence Threshold (dB):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.silence_thresh = tk.IntVar(value=-35)
        ttk.Spinbox(params_frame, from_=-60, to=-10, increment=5, textvariable=self.silence_thresh, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(params_frame, text="Audio level below which is considered silence").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(params_frame, text="Context (ms):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.context = tk.IntVar(value=300)
        ttk.Spinbox(params_frame, from_=0, to=1000, increment=50, textvariable=self.context, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(params_frame, text="Milliseconds of context to keep before speech").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        
        ttk.Label(params_frame, text="Pause (ms):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.pause = tk.IntVar(value=500)
        ttk.Spinbox(params_frame, from_=0, to=1000, increment=50, textvariable=self.pause, width=10).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(params_frame, text="Milliseconds of silence to keep after speech").grid(row=3, column=2, sticky="w", padx=5, pady=5)
    
    def create_processing_options(self):
        options_frame = ttk.LabelFrame(self.root, text="Processing Options")
        options_frame.pack(fill="x", expand=False, padx=10, pady=5)
        
        self.use_gpu = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Use GPU (if available)", variable=self.use_gpu).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.high_quality = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="High Quality (slower)", variable=self.high_quality).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(options_frame, text="Threads:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.threads = tk.IntVar(value=multiprocessing.cpu_count())
        ttk.Spinbox(options_frame, from_=1, to=32, textvariable=self.threads, width=5).grid(row=1, column=1, sticky="w", padx=5, pady=5)
    
    def create_log_section(self):
        log_frame = ttk.LabelFrame(self.root, text="Processing Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(log_frame, orient="horizontal", length=100, mode="indeterminate", variable=self.progress_var)
        self.progress.pack(fill="x", padx=5, pady=5)
    
    def create_action_buttons(self):
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", expand=False, padx=10, pady=10)
        
        ttk.Label(button_frame, text="Presets:").pack(side=tk.LEFT, padx=5)
        self.preset = tk.StringVar(value="Default")
        preset_combo = ttk.Combobox(button_frame, textvariable=self.preset, width=15, state="readonly")
        preset_combo["values"] = ("Default", "Aggressive", "Conservative", "Smooth")
        preset_combo.pack(side=tk.LEFT, padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)
        
        self.process_btn = ttk.Button(button_frame, text="Process Video", command=self.process_video, style="Accent.TButton")
        self.process_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_processing, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Help", command=self.show_help).pack(side=tk.RIGHT, padx=5)
    
    def browse_input(self):
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.wmv"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Select Input Video", filetypes=filetypes)
        if file_path:
            self.input_path.set(file_path)
            
            if not self.output_path.get():
                filename, ext = os.path.splitext(file_path)
                self.output_path.set(f"{filename}_processed{ext}")
    
    def browse_output(self):
        filetypes = [
            ("MP4 Video", "*.mp4"),
            ("AVI Video", "*.avi"),
            ("MOV Video", "*.mov"),
            ("MKV Video", "*.mkv"),
            ("All files", "*.*")
        ]
        file_path = filedialog.asksaveasfilename(title="Save Output Video", filetypes=filetypes, defaultextension=".mp4")
        if file_path:
            self.output_path.set(file_path)
    
    def apply_preset(self, event=None):
        preset = self.preset.get()
        
        if preset == "Default":
            self.silence_length.set(700)
            self.silence_thresh.set(-35)
            self.context.set(300)
            self.pause.set(500)
        elif preset == "Aggressive":
            self.silence_length.set(500)
            self.silence_thresh.set(-30)
            self.context.set(200)
            self.pause.set(300)
        elif preset == "Conservative":
            self.silence_length.set(1500)
            self.silence_thresh.set(-40)
            self.context.set(400)
            self.pause.set(600)
        elif preset == "Smooth":
            self.silence_length.set(1000)
            self.silence_thresh.set(-35)
            self.context.set(500)
            self.pause.set(700)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def process_video(self):
        if not self.input_path.get():
            tk.messagebox.showerror("Error", "Please select an input video file.")
            return
        
        if not os.path.exists(self.input_path.get()):
            tk.messagebox.showerror("Error", f"Input file not found: {self.input_path.get()}")
            return
        
        if not self.output_path.get():
            tk.messagebox.showerror("Error", "Please specify an output video file.")
            return
        
        self.process_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.processing = True
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.progress.start(10)
        
        self.process_thread = threading.Thread(target=self.run_processing)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def run_processing(self):
        try:
            cmd = [
                sys.executable, 
                "main.py",
                self.input_path.get(),
                "--output", self.output_path.get(),
                "--silence-length", str(self.silence_length.get()),
                "--silence-threshold", str(self.silence_thresh.get()),
                "--context", str(self.context.get()),
                "--pause", str(self.pause.get()),
                "--threads", str(self.threads.get())
            ]
            
            if not self.use_gpu.get():
                cmd.append("--no-gpu")
            
            if self.high_quality.get():
                cmd.append("--high-quality")
            
            self.log(f"Starting processing with command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in iter(self.process.stdout.readline, ""):
                if not self.processing:
                    break
                self.log(line.strip())
            
            self.process.wait()
            
            if self.processing:
                if self.process.returncode == 0:
                    self.log("Processing completed successfully!")
                    self.log(f"Output saved to: {self.output_path.get()}")
                    tk.messagebox.showinfo("Success", "Video processing completed successfully!")
                else:
                    self.log(f"Processing failed with return code {self.process.returncode}")
                    tk.messagebox.showerror("Error", f"Processing failed with return code {self.process.returncode}")
            else:
                self.log("Processing canceled by user.")
        
        except Exception as e:
            self.log(f"Error: {str(e)}")
            tk.messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.process_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress.stop()
            self.processing = False
    
    def cancel_processing(self):
        if not self.processing:
            return
        
        self.processing = False
        self.log("Canceling processing...")
        
        if hasattr(self, 'process') and self.process:
            self.process.terminate()
            time.sleep(0.5)
            if self.process.poll() is None:
                if sys.platform.startswith('win'):
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    import signal
                    os.kill(self.process.pid, signal.SIGKILL)
    
    def show_help(self):
        help_text = """
ParsonLabs Video Help

This tool removes silent parts from videos and adds subtitles automatically.

Parameters:
- Silence Length: Minimum silence duration to be removed (ms)
- Silence Threshold: Audio level (dB) below which is considered silence
- Context: Milliseconds of context to keep before speech segments
- Pause: Milliseconds of silence to keep at the end of speech segments

Presets:
- Default: Balanced settings for most videos
- Aggressive: Removes more silence, creates shorter videos
- Conservative: Only removes obvious long pauses
- Smooth: Creates smoother transitions with more context

Options:
- Use GPU: Enable GPU acceleration for faster processing
- High Quality: Create higher quality output (slower processing)
- Threads: Number of CPU threads to use (higher = faster)

For more details, visit the project page at:
https://github.com/ParsonLabs/caption
"""
        help_window = tk.Toplevel(self.root)
        help_window.title("ParsonLabs Video Help")
        help_window.geometry("600x500")
        help_window.minsize(400, 300)
        
        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)
        
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    try:
        import sv_ttk
        root = tk.Tk()
        sv_ttk.set_theme("dark")
    except ImportError:
        root = tk.Tk()
        if sys.platform.startswith('win'):
            try:
                from tkinter import filedialog
                root.tk.call('source', 'azure.tcl')
                root.tk.call('set_theme', 'dark')
            except:
                pass
    
    app = CaptionGUI(root)
    root.mainloop()