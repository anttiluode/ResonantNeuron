import os
import glob
import json
import threading
import numpy as np
import soundfile as sf
import scipy.linalg as la
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class HolographicCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Holographic Koopman Compressor")
        self.root.geometry("500x350")
        
        self.input_folder = tk.StringVar()
        self.output_file = tk.StringVar(value="hologram_master.wav")
        
        # GUI Setup
        tk.Label(root, text="Koopman Holographic Multiplexer", font=("Courier", 14, "bold")).pack(pady=10)
        
        # Input Folder
        frame_in = tk.Frame(root)
        frame_in.pack(pady=5, fill="x", padx=20)
        tk.Label(frame_in, text="Input Folder (WAVs):").pack(anchor="w")
        tk.Entry(frame_in, textvariable=self.input_folder, width=40).pack(side="left", padx=5)
        tk.Button(frame_in, text="Browse", command=self.browse_input).pack(side="left")
        
        # Parameters
        frame_params = tk.Frame(root)
        frame_params.pack(pady=15, fill="x", padx=20)
        tk.Label(frame_params, text="Takens Delay (τ):").grid(row=0, column=0, sticky="w")
        self.tau_var = tk.IntVar(value=4)
        tk.Entry(frame_params, textvariable=self.tau_var, width=8).grid(row=0, column=1, padx=5)
        
        tk.Label(frame_params, text="Phase Space Dim (d):").grid(row=1, column=0, sticky="w")
        self.dim_var = tk.IntVar(value=8)
        tk.Entry(frame_params, textvariable=self.dim_var, width=8).grid(row=1, column=1, padx=5)

        # Output File
        frame_out = tk.Frame(root)
        frame_out.pack(pady=5, fill="x", padx=20)
        tk.Label(frame_out, text="Output Master Wave:").pack(anchor="w")
        tk.Entry(frame_out, textvariable=self.output_file, width=40).pack(side="left", padx=5)
        tk.Button(frame_out, text="Browse", command=self.browse_output).pack(side="left")
        
        # Progress & Run
        self.progress = ttk.Progressbar(root, orient="horizontal", length=460, mode="determinate")
        self.progress.pack(pady=15)
        
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(root, textvariable=self.status_var, font=("Courier", 9)).pack()
        
        self.run_btn = tk.Button(root, text="COMPRESS TO HOLOGRAM", command=self.start_compression, bg="#333", fg="white", font=("Courier", 10, "bold"))
        self.run_btn.pack(pady=5)

    def browse_input(self):
        folder = filedialog.askdirectory()
        if folder: self.input_folder.set(folder)

    def browse_output(self):
        file = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if file: self.output_file.set(file)

    def start_compression(self):
        if not self.input_folder.get():
            messagebox.showerror("Error", "Select an input folder first.")
            return
        
        self.run_btn.config(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self.process_hologram, daemon=True).start()

    def process_hologram(self):
        try:
            folder = self.input_folder.get()
            wav_files = glob.glob(os.path.join(folder, "*.wav"))
            if not wav_files:
                raise Exception("No WAV files found in folder.")
            
            tau = self.tau_var.get()
            dim = self.dim_var.get()
            
            self.status_var.set(f"Found {len(wav_files)} files. Reading lengths...")
            
            # 1. Read all files and find max length to align the phase space
            audio_data = []
            max_len = 0
            sr_master = None
            
            for f in wav_files:
                x, sr = sf.read(f)
                if len(x.shape) > 1: x = x.mean(axis=1) # Force Mono
                if sr_master is None: sr_master = sr
                audio_data.append((os.path.basename(f), x))
                if len(x) > max_len: max_len = len(x)

            # The 1D Master Wave that will hold the compressed static
            hologram_master = np.zeros(max_len)
            time_vector = np.arange(max_len) / sr_master
            
            address_book = {} # Stores the keys to un-compress later
            
            base_carrier_freq = 1000 # Start addressing at 1kHz

            for idx, (filename, x) in enumerate(audio_data):
                self.status_var.set(f"Embedding {filename} ({idx+1}/{len(wav_files)})...")
                
                # Pad to max length with zeros
                x_padded = np.pad(x, (0, max_len - len(x)))
                
                # Takens Delay Embedding
                v = np.zeros((dim, max_len))
                for d in range(dim):
                    shift = d * tau
                    if shift < max_len:
                        v[d, shift:] = x_padded[:max_len - shift]
                
                # Extract Koopman Basis (W) via SVD
                U, _, _ = la.svd(v, full_matrices=False)
                W = U # The spatial topological structure
                
                # Extract Koopman Modes (y)
                y = W.T @ v 
                
                # --- THE HOLOGRAPHIC MODE ADDRESSING ---
                # We multiply each mode by a unique carrier frequency. 
                # This mathematically lifts the mode into an independent topological space.
                addressed_modes = np.zeros(max_len)
                file_addresses = []
                
                for mode_idx in range(dim):
                    # Unique frequency key for this specific mode of this specific file
                    freq_key = base_carrier_freq + (idx * 1000) + (mode_idx * 50)
                    file_addresses.append(freq_key)
                    
                    # Apply the "Reference Beam" twist
                    carrier = np.cos(2 * np.pi * freq_key * time_vector)
                    addressed_modes += y[mode_idx] * carrier
                
                # Add this file's addressed static to the master hologram
                hologram_master += addressed_modes
                
                # Save the structural keys needed to reverse the math later
                address_book[filename] = {
                    "W_matrix": W.tolist(),
                    "frequency_addresses": file_addresses
                }
                
                self.progress["value"] = ((idx + 1) / len(wav_files)) * 100
                self.root.update_idletasks()

            # Normalize the master wave to prevent audio clipping
            hologram_master = hologram_master / np.max(np.abs(hologram_master))
            
            self.status_var.set("Saving Hologram Master and Keys...")
            
            # Save the Audio
            out_wav = self.output_file.get()
            sf.write(out_wav, hologram_master, sr_master)
            
            # Save the Keys
            out_json = out_wav.replace(".wav", "_keys.json")
            with open(out_json, "w") as jf:
                json.dump(address_book, jf, indent=2)

            self.status_var.set("Complete. Hologram generated.")
            messagebox.showinfo("Success", f"Compressed {len(wav_files)} files into 1 wave.\nSaved to:\n{out_wav}\n{out_json}")
            
        except Exception as e:
            messagebox.showerror("Math Error", str(e))
            self.status_var.set("Error occurred.")
        finally:
            self.run_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = HolographicCompressorApp(root)
    root.mainloop()