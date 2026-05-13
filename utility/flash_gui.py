import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from serial.tools import list_ports
    from pymcuprog.backend import SessionConfig, Backend
    from pymcuprog.toolconnection import ToolSerialConnection
except ImportError as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependencies",
        f"Required package not found: {e}\n\n"
        "Run setup.sh (Mac) or setup.bat (Windows) to install dependencies."
    )
    sys.exit(1)


UPDI_VID = 0x1A86  # CH340 chip used by the UPDI Friend programmer
UPDI_PID = 0x7523


def get_app_dir():
    """Return directory of the executable or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def is_updi(port):
    return port.vid == UPDI_VID and port.pid == UPDI_PID


def list_ports_labeled():
    """Return (devices, labels) parallel lists. Auto-detected UPDI port is first."""
    ports = list_ports.comports()
    updi   = [p for p in ports if is_updi(p)]
    others = [p for p in ports if not is_updi(p)]
    ordered = updi + others
    devices = [p.device for p in ordered]
    labels  = [
        f"{p.device}  —  {p.description}" + ("  ✓ UPDI programmer" if is_updi(p) else "")
        for p in ordered
    ]
    return devices, labels


class App:
    def __init__(self, root):
        self.root = root
        root.title("Scent Dispenser – Firmware Utility")
        root.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        outer = ttk.Frame(root, padding=14)
        outer.grid(row=0, column=0, sticky='nsew')

        nb = ttk.Notebook(outer)
        nb.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 12))

        flash_frame = ttk.Frame(nb, padding=12)
        nb.add(flash_frame, text='  Flash Firmware  ')
        self._build_flash_tab(flash_frame)

        id_frame = ttk.Frame(nb, padding=12)
        nb.add(id_frame, text='  Set Device ID  ')
        self._build_id_tab(id_frame)

        ttk.Label(outer, text='Output', font=('', 9, 'bold')).grid(
            row=1, column=0, sticky='w', pady=(0, 4))

        self.log = tk.Text(
            outer, height=11, width=62, state='disabled',
            bg='#1e1e2e', fg='#cdd6f4',
            font=('Courier New', 10) if sys.platform == 'win32' else ('Menlo', 11),
            relief='flat', padx=8, pady=8, wrap='word')
        self.log.grid(row=2, column=0, sticky='ew')
        self.log.tag_config('ok',   foreground='#a6e3a1')
        self.log.tag_config('err',  foreground='#f38ba8')
        self.log.tag_config('dim',  foreground='#6c7086')
        self.log.tag_config('warn', foreground='#f9e2af')

        scroll = ttk.Scrollbar(outer, command=self.log.yview)
        scroll.grid(row=2, column=1, sticky='ns')
        self.log.config(yscrollcommand=scroll.set)

        self._busy = False
        self._write("Scent Dispenser Firmware Utility ready.\n", 'dim')
        if sys.platform == 'win32':
            self.root.after(200, self._check_windows_drivers)

    # ── Flash tab ──────────────────────────────────────────────────────────────

    def _build_flash_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text='Firmware file:').grid(row=0, column=0, sticky='w', pady=4)
        self._hex_var = tk.StringVar()
        self._hex_combo = ttk.Combobox(parent, textvariable=self._hex_var,
                                       state='readonly', width=36)
        self._hex_combo.grid(row=0, column=1, sticky='ew', padx=(8, 4))
        ttk.Button(parent, text='↻', width=3,
                   command=self._refresh_hex).grid(row=0, column=2)

        ttk.Label(parent, text='Port:').grid(row=1, column=0, sticky='w', pady=4)
        self._flash_port = tk.StringVar()
        self._flash_port_combo = ttk.Combobox(parent, textvariable=self._flash_port,
                                               state='readonly', width=36)
        self._flash_port_combo.grid(row=1, column=1, sticky='ew', padx=(8, 4))
        ttk.Button(parent, text='↻', width=3,
                   command=self._refresh_flash_ports).grid(row=1, column=2)

        ttk.Label(parent,
                  text='Connect the UPDI programmer (3-pin header) before selecting a port.',
                  foreground='gray', font=('', 9)).grid(
            row=2, column=0, columnspan=3, sticky='w', pady=(2, 10))

        self._flash_btn = ttk.Button(parent, text='Flash Firmware',
                                     command=self._do_flash)
        self._flash_btn.grid(row=3, column=0, columnspan=3, sticky='ew', ipady=5)

        self._refresh_hex()
        self._refresh_flash_ports()

    def _refresh_hex(self):
        d = get_app_dir()
        files = sorted(f for f in os.listdir(d) if f.lower().endswith('.hex'))
        self._hex_combo['values'] = files
        if files:
            # Default to newest-looking file (last alphabetically)
            if not self._hex_var.get() or self._hex_var.get() not in files:
                self._hex_var.set(files[-1])

    def _refresh_flash_ports(self):
        devices, labels = list_ports_labeled()
        self._flash_port_devices = devices
        self._flash_port_combo['values'] = labels
        if devices:
            self._flash_port_combo.current(0)  # UPDI programmer floated to top

    # ── Set Device ID tab ──────────────────────────────────────────────────────

    def _build_id_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text='Port:').grid(row=0, column=0, sticky='w', pady=4)
        self._id_port = tk.StringVar()
        self._id_port_combo = ttk.Combobox(parent, textvariable=self._id_port,
                                            state='readonly', width=36)
        self._id_port_combo.grid(row=0, column=1, sticky='ew', padx=(8, 4))
        ttk.Button(parent, text='↻', width=3,
                   command=self._refresh_id_ports).grid(row=0, column=2)

        ttk.Label(parent, text='Device ID:').grid(row=1, column=0, sticky='w', pady=4)
        self._id_var = tk.StringVar()
        self._id_entry = ttk.Entry(parent, textvariable=self._id_var, width=38)
        self._id_entry.grid(row=1, column=1, sticky='ew', padx=(8, 0), columnspan=2)

        self._char_label = ttk.Label(parent, text='0 / 16', foreground='gray', font=('', 9))
        self._char_label.grid(row=2, column=1, sticky='e', pady=(0, 2))
        self._id_var.trace_add('write', self._update_char_count)

        ttk.Label(parent,
                  text='Connect the UPDI programmer (3-pin header) before selecting a port.',
                  foreground='gray', font=('', 9)).grid(
            row=3, column=0, columnspan=3, sticky='w', pady=(2, 10))

        btn_row = ttk.Frame(parent)
        btn_row.grid(row=4, column=0, columnspan=3, sticky='ew')
        ttk.Button(btn_row, text='Read Current ID',
                   command=self._do_read_id).pack(side='left', padx=(0, 8))
        self._set_id_btn = ttk.Button(btn_row, text='Set Device ID',
                                      command=self._do_set_id)
        self._set_id_btn.pack(side='left')

        self._refresh_id_ports()

    def _refresh_id_ports(self):
        devices, labels = list_ports_labeled()
        self._id_port_devices = devices
        self._id_port_combo['values'] = labels
        if devices:
            self._id_port_combo.current(0)

    def _update_char_count(self, *_):
        n = len(self._id_var.get())
        self._char_label.config(
            text=f'{n} / 16',
            foreground='red' if n > 16 else 'gray')

    # ── Shared helpers ─────────────────────────────────────────────────────────

    def _write(self, msg, tag=''):
        self.log.config(state='normal')
        self.log.insert('end', msg, tag)
        self.log.see('end')
        self.log.config(state='disabled')

    def _log(self, msg, tag=''):
        self.root.after(0, lambda: self._write(msg + '\n', tag))

    def _set_busy(self, busy):
        self._busy = busy
        state = 'disabled' if busy else 'normal'
        self._flash_btn.config(state=state)
        self._set_id_btn.config(state=state)

    def _connect(self, port, erase):
        """Open a pymcuprog session. Returns Backend instance."""
        cfg = SessionConfig("attiny3217")
        cfg.special_options = (
            {"chip-erase-locked-device": True} if erase
            else {"user-row-locked-device": True}
        )
        transport = ToolSerialConnection(serialport=port, timeout=5)
        backend = Backend()
        backend.connect_to_tool(transport)
        backend.start_session(cfg)
        return backend

    # ── Flash firmware ─────────────────────────────────────────────────────────

    def _do_flash(self):
        hex_name = self._hex_var.get()
        idx = self._flash_port_combo.current()
        port = self._flash_port_devices[idx] if idx >= 0 and hasattr(self, '_flash_port_devices') and self._flash_port_devices else None
        if not hex_name:
            messagebox.showerror('Error', 'No firmware file selected.\n'
                                 'Place a .hex file in the same folder as this app.')
            return
        if not port:
            messagebox.showerror('Error', 'No port selected.\nConnect the programmer and click ↻.')
            return

        hex_path = os.path.join(get_app_dir(), hex_name)
        self._set_busy(True)
        self._write('\n', '')

        def run():
            backend = None
            try:
                self._log(f'Flashing {hex_name} → {port}')
                self._log('Connecting to programmer…')
                backend = self._connect(port, erase=True)
                self._log('Connected.')
                self._log('Erasing device…')
                backend.erase()
                self._log('Writing firmware (this takes ~1 minute)…')
                backend.write_hex_to_target(hex_path)
                self._log('Done. Device will restart.', 'ok')
            except Exception as e:
                self._log(f'Error: {e}', 'err')
            finally:
                if backend:
                    try:
                        backend.end_session()
                        backend.disconnect_from_tool()
                    except Exception:
                        pass
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    # ── Read / Set Device ID ───────────────────────────────────────────────────

    def _do_read_id(self):
        idx = self._id_port_combo.current()
        port = self._id_port_devices[idx] if idx >= 0 and hasattr(self, '_id_port_devices') and self._id_port_devices else None
        if not port:
            messagebox.showerror('Error', 'No port selected.')
            return
        self._set_busy(True)
        self._write('\n', '')

        def run():
            backend = None
            try:
                self._log(f'Reading device ID from {port}…')
                backend = self._connect(port, erase=False)
                mem = backend.read_memory(memory_name='user_row', numbytes=16)
                dev_id = mem[0].data.decode('utf-8').strip('\x00')
                self._log(f'Current ID: "{dev_id}"', 'ok')
                self.root.after(0, lambda: self._id_var.set(dev_id))
            except Exception as e:
                self._log(f'Error: {e}', 'err')
            finally:
                if backend:
                    try:
                        backend.end_session()
                        backend.disconnect_from_tool()
                    except Exception:
                        pass
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    def _do_set_id(self):
        idx = self._id_port_combo.current()
        port = self._id_port_devices[idx] if idx >= 0 and hasattr(self, '_id_port_devices') and self._id_port_devices else None
        dev_id = self._id_var.get().strip()
        if not port:
            messagebox.showerror('Error', 'No port selected.')
            return
        if len(dev_id) > 16:
            messagebox.showerror('Error', 'Device ID cannot exceed 16 characters.')
            return
        if not messagebox.askyesno(
                'Confirm', f'Set device ID to "{dev_id}"?'):
            return
        self._set_busy(True)
        self._write('\n', '')

        def run():
            backend = None
            try:
                self._log(f'Setting device ID to "{dev_id}" on {port}…')
                backend = self._connect(port, erase=False)
                data = dev_id.encode('utf-8').ljust(16, b'\x00')[:16]
                backend.write_memory(data, memory_name='user_row')
                self._log(f'Device ID set to "{dev_id}".', 'ok')
            except Exception as e:
                self._log(f'Error: {e}', 'err')
            finally:
                if backend:
                    try:
                        backend.end_session()
                        backend.disconnect_from_tool()
                    except Exception:
                        pass
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=run, daemon=True).start()

    # ── Windows driver check ───────────────────────────────────────────────────

    def _check_windows_drivers(self):
        """Check for CH340 and FTDI drivers via registry (no admin needed)."""
        import subprocess

        drivers = [
            {
                'name':    'CH340  (UPDI programmer)',
                'regkey':  r'HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_1A86&PID_7523',
                'url':     'https://www.wch-ic.com/downloads/CH341SER_ZIP.html',
            },
            {
                'name':    'FTDI   (USB-C log port)',
                'regkey':  r'HKLM\SYSTEM\CurrentControlSet\Enum\USB\VID_0403&PID_6015',
                'url':     'https://ftdichip.com/drivers/vcp-drivers/',
            },
        ]

        missing = []
        for d in drivers:
            result = subprocess.run(
                ['reg', 'query', d['regkey']],
                capture_output=True)
            if result.returncode != 0:
                missing.append(d)

        if missing:
            self._write('\nWindows driver check:\n', 'warn')
            for d in missing:
                self._write(f'  ✗ {d["name"]} — not detected\n', 'warn')
                self._write(f'    Download: {d["url"]}\n', 'dim')
            self._write(
                '  Drivers are needed the first time a device is used.\n'
                '  Installation requires administrator access (a UAC prompt\n'
                '  will appear — click Yes to allow).\n'
                '  If you lack admin rights, ask your IT department.\n\n', 'dim')
        else:
            self._write('\nWindows driver check: both drivers detected.\n', 'ok')


if __name__ == '__main__':
    root = tk.Tk()
    root.minsize(520, 420)
    App(root)
    root.mainloop()
