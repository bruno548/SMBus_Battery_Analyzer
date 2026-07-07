import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import json
import time

class BatteryAnalyzer:

    def __init__(self, root):
        self.root = root
        self.root.title("SMBus Battery Analyzer - Expert Diagnostic PRO")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#1e1e1e")

        self.serial_conn = None
        self.connected = False
        self.data = {}

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_ui()

    def create_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#2b2b2b", background="#2b2b2b", foreground="white")

        top_frame = tk.Frame(self.root, bg="#2b2b2b", height=70)
        top_frame.pack(fill="x")

        title = tk.Label(top_frame, text="SMBus Battery Analyzer PRO+", font=("Segoe UI", 22, "bold"), fg="white", bg="#2b2b2b")
        title.pack(side="left", padx=20, pady=15)

        conn_frame = tk.Frame(self.root, bg="#252526", height=80)
        conn_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(conn_frame, text="Serial Port", fg="white", bg="#252526", font=("Segoe UI", 10)).place(x=20, y=10)
        self.port_combo = ttk.Combobox(conn_frame, width=18, font=("Segoe UI", 11))
        self.port_combo.place(x=20, y=35)

        refresh_btn = tk.Button(conn_frame, text="Refresh", command=self.refresh_ports, bg="#3c3c3c", fg="white", relief="flat", font=("Segoe UI", 10), width=10)
        refresh_btn.place(x=220, y=33)

        self.connect_btn = tk.Button(conn_frame, text="Connect", command=self.toggle_connection, bg="#007acc", fg="white", relief="flat", font=("Segoe UI", 10, "bold"), width=12)
        self.connect_btn.place(x=330, y=33)

        self.status_label = tk.Label(conn_frame, text="DISCONNECTED", fg="#ff5555", bg="#252526", font=("Segoe UI", 11, "bold"))
        self.status_label.place(x=480, y=36)

        # PAINEL DO MEIO: INFO & DIAGNÓSTICO PROFISSIONAL DE ERROS
        middle_frame = tk.Frame(self.root, bg="#1e1e1e")
        middle_frame.pack(fill="x", padx=15, pady=5)

        info_frame = tk.Frame(middle_frame, bg="#252526", width=400, height=200)
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        info_frame.pack_propagate(False)

        self.manufacturer_label = tk.Label(info_frame, text="Manufacturer: ---", font=("Segoe UI", 12, "bold"), fg="#00d7ff", bg="#252526")
        self.manufacturer_label.pack(anchor="w", padx=20, pady=(15, 2))
        self.device_label = tk.Label(info_frame, text="Device: ---", font=("Segoe UI", 11), fg="white", bg="#252526")
        self.device_label.pack(anchor="w", padx=20, pady=1)
        self.chem_label = tk.Label(info_frame, text="Chemistry: ---", font=("Segoe UI", 11), fg="white", bg="#252526")
        self.chem_label.pack(anchor="w", padx=20, pady=1)
        self.health_label = tk.Label(info_frame, text="BATTERY STATUS: ---", font=("Segoe UI", 13, "bold"), fg="#00cc66", bg="#252526")
        self.health_label.pack(anchor="w", padx=20, pady=(10, 10))

        diag_frame = tk.Frame(middle_frame, bg="#252526", height=200)
        diag_frame.pack(side="right", fill="both", expand=True)
        
        tk.Label(diag_frame, text="SMBus REGISTERS & HARDWARE FAULTS (REAL-TIME)", font=("Segoe UI", 12, "bold"), fg="#ffaa00", bg="#252526").pack(anchor="w", padx=20, pady=(15, 5))
        
        self.chg_req_label = tk.Label(diag_frame, text="Firmware Targets: ---", font=("Segoe UI", 10), fg="#bbbbbb", bg="#252526")
        self.chg_req_label.pack(anchor="w", padx=20, pady=1)

        self.smbus_err_label = tk.Label(diag_frame, text="Protocol Error: None", font=("Segoe UI", 10, "bold"), fg="#00ff88", bg="#252526")
        self.smbus_err_label.pack(anchor="w", padx=20, pady=1)

        self.safety_flags_label = tk.Label(diag_frame, text="BMS Hardware Protections: None Active", font=("Segoe UI", 10), fg="white", bg="#252526")
        self.safety_flags_label.pack(anchor="w", padx=20, pady=1)

        self.lock_status_label = tk.Label(diag_frame, text="Permanent Failure (PF): CLEAR", font=("Segoe UI", 11, "bold"), fg="#00ff88", bg="#252526")
        self.lock_status_label.pack(anchor="w", padx=20, pady=2)

        # GRID PRINCIPAL DE METRICAS
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        for i in range(3):
            main_frame.grid_columnconfigure(i, weight=1)
            main_frame.grid_rowconfigure(i, weight=1)

        self.cards = {}
        metrics = [
            ("Charge Level (SoC)", "soc", "%"),
            ("Voltage", "v", "mV"),
            ("Current", "i", "mA"),
            ("Remaining Capacity", "rc", "mAh"),
            ("Full Capacity", "fc", "mAh"),
            ("Design Capacity", "dc", "mAh"),
            ("Temperature", "t", "°C"),
            ("Cycle Count", "cy", ""),
            ("Battery Health (SoH)", "h", "%"),
        ]

        row, col = 0, 0
        for title, key, unit in metrics:
            card = self.create_card(main_frame, title, unit)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            self.cards[key] = card
            col += 1
            if col > 2:
                col = 0
                row += 1

        self.refresh_ports()

    def create_card(self, parent, title, unit):
        frame = tk.Frame(parent, bg="#2d2d30", width=260, height=120, bd=0, relief="flat")
        frame.pack_propagate(False)
        tk.Label(frame, text=title, font=("Segoe UI", 11), fg="#bbbbbb", bg="#2d2d30").pack(pady=(12, 2))
        value_label = tk.Label(frame, text="---", font=("Consolas", 22, "bold"), fg="white", bg="#2d2d30")
        value_label.pack()
        tk.Label(frame, text=unit, font=("Segoe UI", 9), fg="#888888", bg="#2d2d30").pack()
        frame.value_label = value_label
        return frame

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo["values"] = [port.device for port in ports]
        if ports: self.port_combo.current(0)

    def toggle_connection(self):
        if not self.connected: self.connect_serial()
        else: self.disconnect_serial()

    def connect_serial(self):
        port = self.port_combo.get()
        if not port: return
        try:
            self.serial_conn = serial.Serial(port, 115200, timeout=1)
            self.serial_conn.reset_input_buffer()
            self.connected = True
            self.status_label.config(text="CONNECTED", fg="#00ff88")
            self.connect_btn.config(text="Disconnect", bg="#cc4444")
            threading.Thread(target=self.read_serial, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def disconnect_serial(self):
        self.connected = False
        if self.serial_conn:
            try: self.serial_conn.close()
            except: pass
        self.status_label.config(text="DISCONNECTED", fg="#ff5555")
        self.connect_btn.config(text="Connect", bg="#007acc")
        self.root.after(0, self.clear_ui)

    def read_serial(self):
        buffer = ""
        while self.connected:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    raw_data = self.serial_conn.read(self.serial_conn.in_waiting).decode(errors="ignore")
                    buffer += raw_data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("{") and line.endswith("}"):
                            try:
                                parsed = json.loads(line)
                                if "v" in parsed:
                                    self.data = parsed
                                    self.root.after(0, self.update_ui)
                            except: pass
            except: pass
            time.sleep(0.02)

    def update_ui(self):
        if not self.data:
            return

        # 1. Atualizar Cards Padrões
        for key, card in self.cards.items():
            value = self.data.get(key, "---")

            if key == "t" and value != "---":
                try: value = (float(value) / 10.0) - 273.15 # Decikelvin para Celsius
                except: value = "---"

            if isinstance(value, float):
                value = f"{value:.1f}"
            elif isinstance(value, int) and key == "i":
                if value > 32767: value -= 65536 # Trata corrente negativa

            card.value_label.config(text=str(value))

        # Atualiza Strings de Informação Estáticas
        self.manufacturer_label.config(text=f"Manufacturer: {self.data.get('mf', '---')}")
        self.device_label.config(text=f"Device: {self.data.get('dev', '---')}")
        self.chem_label.config(text=f"Chemistry: {self.data.get('chem', '---')}")

        # Saúde Geral baseada no SoH
        try:
            health = float(self.data.get("h", 0))
            if health >= 80: self.health_label.config(text="BATTERY STATUS: GOOD", fg="#00cc66")
            elif health >= 60: self.health_label.config(text="BATTERY STATUS: ATTENTION", fg="#ffaa00")
            else: self.health_label.config(text="BATTERY STATUS: REPLACE", fg="#ff4444")
        except: pass

        # ============================================================
        # DIAGNÓSTICO PROFISSIONAL SEGURO (PADRÃO SMBus UNIVERSAL)
        # ============================================================
        cv = self.data.get("cv", "---")
        cc = self.data.get("cc", "---")
        bs = self.data.get("bs", 0)
        current_real = self.data.get("i", 0)
        cycles = self.data.get("cy", 0)

        if isinstance(current_real, int) and current_real > 32767:
            current_real -= 65536

        if cv != "---" and cc != "---":
            self.chg_req_label.config(text=f"Firmware Targets: {cv} mV / {cc} mA")
            
            active_alarms = []
            protocol_error = "None"
            
            if isinstance(bs, int):
                # 1. Alertas de proteção universais do padrão SMBus
                if bs & (1 << 15): active_alarms.append("OVER_CHARGED")
                if bs & (1 << 14): active_alarms.append("TERMINATE_CHARGE")
                if bs & (1 << 12): active_alarms.append("OVER_TEMP")
                if bs & (1 << 11): active_alarms.append("TERMINATE_DISCHARGE")
                
                # 2. Erros de execução internos da própria BMS (4 bits inferiores)
                err_code = bs & 0x000F
                errors_map = {
                    1: "BMS Busy", 
                    2: "Rejected Command", 
                    3: "Unsupported Command", 
                    4: "Access Denied (Sealed/Locked)", 
                    5: "Data Overflow"
                }
                if err_code in errors_map:
                    protocol_error = errors_map[err_code]

            # Atualiza o label do erro de protocolo na interface
            if protocol_error != "None":
                self.smbus_err_label.config(text=f"Protocol Error: {protocol_error}", fg="#ff4444")
            else:
                self.smbus_err_label.config(text="Protocol Error: None (Bus Clean)", fg="#00ff88")

            # INTERPRETAÇÃO COMBINADA DO ESTADO DA BATERIA
            # Caso 1: Bateria Nova de estoque com proteção física armada (Subtensão)
            if cc > 0 and current_real == 0 and isinstance(cycles, int) and cycles <= 5:
                self.lock_status_label.config(text="Permanent Failure: CELL UNDERVOLTAGE / HW TRIP", fg="#ff4444")
                self.safety_flags_label.config(text=f"Status: Alarms={active_alarms if active_alarms else 'BMS Safety Open'}")
            
            # Caso 2: Alvos zerados voluntariamente (Bateria cheia ou em standby)
            elif cv == 0 or cc == 0:
                self.lock_status_label.config(text="Permanent Failure: OPERATIONAL (STANDBY / FULL)", fg="#00ff88")
                self.safety_flags_label.config(text=f"Status: {', '.join(active_alarms) if active_alarms else 'Normal Cutoff'}")
            
            # Caso 3: Erro explícito de Access Denied na BMS
            elif "Access Denied" in protocol_error:
                self.lock_status_label.config(text="Permanent Failure: FIRMWARE LOCKOUT / SEALED", fg="#ffaa00")
                self.safety_flags_label.config(text="Status: Hardware memory locked by safety fuse.")
            
            # Caso 4: Operação Padrão
            else:
                self.lock_status_label.config(text="Permanent Failure: OPERATIONAL (CLEAR)", fg="#00ff88")
                
                # Correção da Sintaxe: Isolando o join de forma limpa
                if active_alarms:
                    alarms_str = f" ({', '.join(active_alarms)})"
                else:
                    alarms_str = ""
                    
                self.safety_flags_label.config(text=f"Status: Requesting Charge{alarms_str}")

    def clear_ui(self):
        self.data = {}
        for card in self.cards.values(): card.value_label.config(text="---")
        self.manufacturer_label.config(text="Manufacturer: ---")
        self.device_label.config(text="Device: ---")
        self.chem_label.config(text="Chemistry: ---")
        self.lock_status_label.config(text="Permanent Failure (PF): CLEAR", fg="#00ff88")
        self.safety_flags_label.config(text="BMS Hardware Protections: None Active", fg="white")
        self.smbus_err_label.config(text="Protocol Error: None", fg="#00ff88")

    def on_closing(self):
        self.disconnect_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BatteryAnalyzer(root)
    root.mainloop()