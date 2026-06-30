import os
import json
import threading
import numpy as np
import soundfile as sf
import scipy.signal as sp_signal
import scipy.linalg as la
import sounddevice as sd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class HolographicExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Holographic Koopman Extractor")
        self.root.geometry("550x500")
        
        self.master_wav_path = tk.StringVar()
        self.keys_json_path = tk.StringVar()
        self.address_book = {}
        self.audio_data = None
        self.sr_master = None
        
        # --- GUI SETUP ---
        tk.Label(root, text="Holographic Mode Decryptor", font=("Courier", 14, "bold")).pack(pady=10)
        
        # Load Hologram Wave
        frame_wav = tk.Frame(root)
        frame_wav.pack(pady=5, fill="x", padx=20)
        tk.Label(frame_wav, text="1. Hologram (WAV):").pack(anchor="w")
        tk.Entry(frame_wav, textvariable=self.master_wav_path, width=40).pack(side="left", padx=5)
        tk.Button(frame_wav, text="Browse", command=self.browse_wav).pack(side="left")
        
        # Load Keys JSON
        frame_keys = tk.Frame(root)
        frame_keys.pack(pady=5, fill="x", padx=20)
        tk.Label(frame_keys, text="2. Address Book (JSON):").pack(anchor="w")
        tk.Entry(frame_keys, textvariable=self.keys_json_path, width=40).pack(side="left", padx=5)
        tk.Button(frame_keys, text="Browse", command=self.browse_json).pack(side="left")
        
        # Load Button
        tk.Button(root, text="LOAD HOLOGRAM", command=self.load_data, bg="#444", fg="white").pack(pady=10)
        
        # Listbox for embedded files
        tk.Label(root, text="Embedded Files:").pack(anchor="w", padx=20)
        self.file_listbox = tk.Listbox(root, height=8, font=("Courier", 10))
        self.file_listbox.pack(fill="x", padx=20, pady=5)
        
        # Action Buttons
        frame_actions = tk.Frame(root)
        frame_actions.pack(pady=10)
        
        self.play_btn = tk.Button(frame_actions, text="EXTRACT & PLAY", command=lambda: self.process_extraction(play=True), bg="#005500", fg="white", font=("Courier", 10, "bold"), state="disabled")
        self.play_btn.pack(side="left", padx=10)
        
        self.save_btn = tk.Button(frame_actions, text="EXTRACT & SAVE", command=lambda: self.process_extraction(play=False), bg="#000055", fg="white", font=("Courier", 10, "bold"), state="disabled")
        self.save_btn.pack(side="left", padx=10)

        # Status
        self.status_var = tk.StringVar(value="Waiting for files...")
        tk.Label(root, textvariable=self.status_var, font=("Courier", 9)).pack(pady=10)

    def browse_wav(self):
        file = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file: self.master_wav_path.set(file)

    def browse_json(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file: self.keys_json_path.set(file)

    def load_data(self):
        wav_path = self.master_wav_path.get()
        json_path = self.keys_json_path.get()
        
        if not os.path.exists(wav_path) or not os.path.exists(json_path):
            messagebox.showerror("Error", "Please select both the WAV and JSON files.")
            return
            
        try:
            self.status_var.set("Loading master wave into memory...")
            self.root.update()
            
            self.audio_data, self.sr_master = sf.read(wav_path)
            
            with open(json_path, "r") as f:
                self.address_book = json.load(f)
                
            self.file_listbox.delete(0, tk.END)
            for filename in self.address_book.keys():
                self.file_listbox.insert(tk.END, filename)
                
            self.play_btn.config(state="normal")
            self.save_btn.config(state="normal")
            self.status_var.set(f"Loaded successfully. Found {len(self.address_book)} embedded files.")
            
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def process_extraction(self, play=True):
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Select a file from the list first.")
            return
            
        filename = self.file_listbox.get(selection[0])
        
        # Disable UI during heavy math
        self.play_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.status_var.set(f"Decrypting {filename}...")
        
        threading.Thread(target=self._extract_thread, args=(filename, play), daemon=True).start()

    def _extract_thread(self, filename, play):
        try:
            keys = self.address_book[filename]
            W = np.array(keys["W_matrix"])
            freqs = keys["frequency_addresses"]
            dim = len(freqs)
            
            time_vector = np.arange(len(self.audio_data)) / self.sr_master
            
            # Create the Dendritic Low-Pass Filter
            # The multiplexing carrier moves the data to high frequencies.
            # We demodulate it back down, then use a severe low-pass to kill the static.
            nyq = 0.5 * self.sr_master
            # Use a cutoff frequency slightly below the carrier spacing (e.g., 25Hz)
            # This isolates the core Koopman topology from the high-freq noise.
            b, a = sp_signal.butter(4, 30 / nyq, btype='low')
            
            y_recovered = np.zeros((dim, len(self.audio_data)))
            
            for mode_idx in range(dim):
                f = freqs[mode_idx]
                
                # 1. The Reference Beam (Carrier Wave)
                carrier = np.cos(2 * np.pi * f * time_vector)
                
                # 2. Phase Cancellation (Demodulation)
                demodulated = self.audio_data * carrier
                
                # 3. Dendritic Sieve (Low-Pass Filter)
                filtered_mode = sp_signal.filtfilt(b, a, demodulated)
                
                # Multiply by 2 to restore amplitude lost in the cos^2 math expansion
                y_recovered[mode_idx] = filtered_mode * 2.0
                
            # 4. Snap the geometry back together (Inverse Takens mapping)
            v_recovered = W @ y_recovered
            
            # Extract the observable (0th dimension)
            extracted_audio = v_recovered[0, :]
            
            # Normalize to make it audible and prevent blowing out speakers
            extracted_audio = extracted_audio / (np.max(np.abs(extracted_audio)) + 1e-9)
            
            self.status_var.set(f"Successfully extracted {filename}!")
            
            if play:
                sd.play(extracted_audio, self.sr_master)
                # We don't block the thread with sd.wait(), let it play asynchronously
            else:
                out_path = filedialog.asksaveasfilename(
                    initialfile=f"extracted_{filename}", 
                    defaultextension=".wav", 
                    filetypes=[("WAV files", "*.wav")]
                )
                if out_path:
                    sf.write(out_path, extracted_audio, self.sr_master)
                    self.status_var.set(f"Saved to {out_path}")
            
        except Exception as e:
            self.status_var.set("Extraction failed.")
            messagebox.showerror("Math Error", str(e))
        finally:
            self.play_btn.config(state="normal")
            self.save_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = HolographicExtractorApp(root)
    root.mainloop()