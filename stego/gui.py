import os
import tkinter as tk
from tkinter import filedialog, messagebox

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.io import wavfile

from . import config
from .metrics import calculate_metrics
from .steganography import LSBSteganography


class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio LSB Steganography")
        self.root.geometry("900x700")

        self.fs = None
        self.audio_data = None
        self.modified_audio_data = None

        self._setup_ui()

    def _setup_ui(self):
        # File
        frame_top = tk.Frame(self.root, pady=10)
        frame_top.pack()
        tk.Button(frame_top, text="Load WAV file", command=self.load_wav, width=20).grid(row=0, column=0, padx=5)
        self.lbl_file = tk.Label(frame_top, text="No file loaded")
        self.lbl_file.grid(row=0, column=1, padx=5)

        tk.Label(frame_top, text="Bits per sample:").grid(row=0, column=2, padx=(20, 5))
        self.lsb_var = tk.IntVar(value=config.LSB_COUNT)
        tk.OptionMenu(frame_top, self.lsb_var, 1, 2, 4).grid(row=0, column=3)

        # Message
        frame_text = tk.LabelFrame(self.root, text="Message", padx=10, pady=10)
        frame_text.pack(fill="x", padx=10)

        self.txt_message = tk.Text(frame_text, height=4)
        self.txt_message.pack(fill="x")

        btn_frame = tk.Frame(frame_text)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Encode", command=self.encode, bg="#ddffdd").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Decode", command=self.decode, bg="#ffdddd").pack(side="left", padx=5)

        # Results
        frame_metrics = tk.LabelFrame(self.root, text="Results", padx=10, pady=10)
        frame_metrics.pack(fill="x", padx=10, pady=5)

        self.lbl_metrics = tk.Label(frame_metrics, text="PSNR: - | SNR: -", font=("Arial", 12, "bold"))
        self.lbl_metrics.pack(side="left", padx=10)
        tk.Button(frame_metrics, text="Save WAV", command=self.save_wav).pack(side="right", padx=10)

        # Plots
        self.frame_plot = tk.Frame(self.root)
        self.frame_plot.pack(fill="both", expand=True, padx=10, pady=10)

    def load_wav(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if not path:
            return
        try:
            self.fs, self.audio_data = wavfile.read(path)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid file: {e}")
            return
        self.lbl_file.config(text=os.path.basename(path))
        self.modified_audio_data = None
        self.plot_waveform(self.audio_data, "Original signal")
        messagebox.showinfo("Info", f"Loaded: {self.fs} Hz, shape: {self.audio_data.shape}")

    def encode(self):
        if self.audio_data is None:
            return
        text = self.txt_message.get("1.0", tk.END).strip()
        if not text:
            return

        config.LSB_COUNT = self.lsb_var.get()
        try:
            self.modified_audio_data = LSBSteganography.embed_message(self.audio_data, text)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        psnr, snr = calculate_metrics(self.audio_data, self.modified_audio_data)
        self.lbl_metrics.config(text=f"PSNR: {psnr:.2f} dB | SNR: {snr:.2f} dB")
        messagebox.showinfo("Done", "Message encoded.")

        diff = self.audio_data.astype(np.float64) - self.modified_audio_data.astype(np.float64)
        self.plot_waveform(diff, "LSB noise (difference)", is_diff=True)

    def decode(self):
        if self.audio_data is None:
            return
        config.LSB_COUNT = self.lsb_var.get()
        try:
            decoded = LSBSteganography.extract_message(self.audio_data)
        except ValueError as e:
            messagebox.showerror("Error", f"Could not read a message: {e}")
            return
        self.txt_message.delete("1.0", tk.END)
        self.txt_message.insert("1.0", decoded)
        messagebox.showinfo("Done", "Message decoded.")

    def save_wav(self):
        if self.modified_audio_data is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if path:
            wavfile.write(path, self.fs, self.modified_audio_data)

    def plot_waveform(self, data, title, is_diff=False):
        for widget in self.frame_plot.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        plot_data = data[:, 0] if data.ndim > 1 else data

        if is_diff:
            ax.plot(plot_data, color="red", linewidth=0.5)
        else:
            ax.specgram(plot_data, Fs=self.fs, NFFT=1024, noverlap=512, cmap="inferno")
            ax.set_ylabel("Hz")
            ax.set_xlabel("Time [s]")

        ax.set_title(title)
        canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


def main():
    root = tk.Tk()
    StegoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
