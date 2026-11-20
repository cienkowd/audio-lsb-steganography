import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

from steganography import LSBSteganography
from metrics import calculate_metrics


class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Steganografia LSB")
        self.root.geometry("900x700")

        self.fs = None
        self.audio_data = None
        self.modified_audio_data = None

        self._setup_ui()

    def _setup_ui(self):
        # Sekcja pliku
        frame_top = tk.Frame(self.root, pady=10)
        frame_top.pack()
        tk.Button(frame_top, text="Wczytaj plik WAV", command=self.load_wav, width=20).grid(row=0, column=0, padx=5)
        self.lbl_file = tk.Label(frame_top, text="Brak pliku")
        self.lbl_file.grid(row=0, column=1, padx=5)

        # Sekcja wiadomości
        frame_text = tk.LabelFrame(self.root, text="Wiadomość", padx=10, pady=10)
        frame_text.pack(fill="x", padx=10)

        self.txt_message = tk.Text(frame_text, height=4)
        self.txt_message.pack(fill="x")

        btn_frame = tk.Frame(frame_text)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Encode", command=self.encode, bg="#ddffdd").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Decode", command=self.decode, bg="#ffdddd").pack(side="left", padx=5)

        # Wyniki
        frame_metrics = tk.LabelFrame(self.root, text="Wyniki", padx=10, pady=10)
        frame_metrics.pack(fill="x", padx=10, pady=5)

        self.lbl_metrics = tk.Label(frame_metrics, text="PSNR: - | SNR: -", font=("Arial", 12, "bold"))
        self.lbl_metrics.pack(side="left", padx=10)
        tk.Button(frame_metrics, text="Zapisz WAV", command=self.save_wav).pack(side="right", padx=10)

        # Wykresy
        self.frame_plot = tk.Frame(self.root)
        self.frame_plot.pack(fill="both", expand=True, padx=10, pady=10)

    def load_wav(self):
        path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if path:
            try:
                self.fs, self.audio_data = wavfile.read(path)
                self.lbl_file.config(text=os.path.basename(path))
                self.modified_audio_data = None

                self.plot_waveform(self.audio_data, "Sygnał oryginalny")
                messagebox.showinfo("Info", f"Wczytano: {self.fs} Hz, shape: {self.audio_data.shape}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Niepoprawny plik: {e}")

    def encode(self):
        if self.audio_data is None:
            return

        text = self.txt_message.get("1.0", tk.END).strip()
        if not text:
            return

        try:
            self.modified_audio_data = LSBSteganography.embed_message(self.audio_data, text)

            psnr, snr = calculate_metrics(self.audio_data, self.modified_audio_data)
            self.lbl_metrics.config(text=f"PSNR: {psnr:.2f} dB | SNR: {snr:.2f} dB")

            messagebox.showinfo("Sukces", "Zakodowano.")

            # Wykres różnicowy
            diff = self.audio_data.astype(np.float64) - self.modified_audio_data.astype(np.float64)
            self.plot_waveform(diff, "Szum LSB (Diff)", is_diff=True)

        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def decode(self):
        if self.audio_data is None:
            return

        try:
            decoded = LSBSteganography.extract_message(self.audio_data)
            self.txt_message.delete("1.0", tk.END)
            self.txt_message.insert("1.0", decoded)
            messagebox.showinfo("Sukces", "Odkodowano.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się odczytać: {e}")

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

        plot_data = data[:, 0] if len(data.shape) > 1 else data

        if is_diff:
            ax.plot(plot_data, color='red', linewidth=0.5)
        else:
            ax.specgram(plot_data, Fs=self.fs, NFFT=1024, noverlap=512, cmap='inferno')
            ax.set_ylabel("Hz")
            ax.set_xlabel("Czas [s]")

        ax.set_title(title)
        canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = StegoApp(root)
    root.mainloop()