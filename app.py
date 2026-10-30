import sys
import random
import csv
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

try:
    import serial
except ImportError:
    serial = None

class MatrixScanner(GridLayout):
    """ Grille d'imagerie géophysique 12x12 isolée et épurée """
    def __init__(self, **kwargs):
        super(MatrixScanner, self).__init__(**kwargs)
        self.cols = 12
        self.rows = 12
        self.spacing = 3  # Espacement net entre les voxels
        self.cells = []
        for i in range(144):
            lbl = Label(text="", size_hint=(1, 1))
            with lbl.canvas.before:
                Color(rgb=get_color_from_hex('#1E293B')) # Couleur de base : Slate 800
                lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
            lbl.bind(pos=self._update_rect, size=self._update_rect)
            self.add_widget(lbl)
            self.cells.append(lbl)

    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(rgb=getattr(instance, 'cell_color', get_color_from_hex('#1E293B')))
            instance.rect = Rectangle(pos=instance.pos, size=instance.size)

    def update_voxel(self, x, y, signal, metal):
        index = (x * 12) + y
        if index < len(self.cells):
            cell = self.cells[index]
            if signal < 40:
                cell.cell_color = get_color_from_hex('#1E293B')
            elif metal == "GOLD/COPPER":
                cell.cell_color = get_color_from_hex('#F59E0B') # Ambre / Or
            elif metal == "IRON/FERROUS":
                cell.cell_color = get_color_from_hex('#64748B') # Gris Métal (Fer)
            else:
                cell.cell_color = get_color_from_hex('#3B82F6') # Bleu (Anomalie sol)
            cell.canvas.before.clear()
            with cell.canvas.before:
                Color(rgb=cell.cell_color)
                cell.rect = Rectangle(pos=cell.pos, size=cell.size)

class UltimateRefinedApp(App):
    def build(self):
        self.title = "GEORADAR PI-3D INDUSTRIAL MONITOR"
        self.cur_x, self.cur_y = 0, 0
        
        # Initialisation du Datalogger
        self.log_filename = f"scan_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(self.log_filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Grid_X", "Grid_Y", "Signal_LSB", "Depth_CM", "Metal_Type", "Sensitivity", "Pulse_Width", "Soil_Moisture", "Temperature"])

        self.ser = None
        if serial:
            try: self.ser = serial.Serial('COM3', 115200, timeout=0.02)
            except: print("Mode Simulation Graphique Actif.")

        # Conteneur principal (Structure Cockpit Sombre)
        root = BoxLayout(orientation='horizontal', padding=15, spacing=15)
        with root.canvas.before:
            Color(rgb=get_color_from_hex('#090D16')) # Fond Noir Profond de sécurité (900)
            self.rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda ins, val: setattr(self.rect, 'pos', val) or setattr(self.rect, 'size', ins.size))

        # =====================================================================
        # PANNEAU GAUCHE : SENSORS & TARGET TELEMETRY (Alignement strict)
        # =====================================================================
        left_panel = BoxLayout(orientation='vertical', size_hint=(0.38, 1), spacing=12)
        
        # Titre de l'application
        left_panel.add_widget(Label(text="[b]GEORADAR TELEMETRY v1.0[/b]", font_size='15sp', color=get_color_from_hex('#38BDF8'), halign='left', markup=True, size_hint_y=0.06))

        
        # 1. BLOC IDENTIFICATION DU MÉTAL (Grand affichage centralisé)
        metal_box = BoxLayout(orientation='vertical', padding=8, size_hint_y=0.25)
        self.lbl_metal = Label(text="[b][COLOR=64748B]SOL NEUTRE[/COLOR][/b]", font_size='22sp', markup=True, halign='center', valign='middle')
        self.lbl_vdi = Label(text="INDICE VDI : 00", font_size='13sp', color=get_color_from_hex('#94A3B8'))
        metal_box.add_widget(self.lbl_metal)
        metal_box.add_widget(self.lbl_vdi)
        left_panel.add_widget(metal_box)

        # 2. BLOC MESURES DE LA CIBLE (Signal et Profondeur alignés côte à côte)
        metrics_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.22)
        
        # Sous-bloc Signal
        sig_sub = BoxLayout(orientation='vertical', padding=4)
        self.lbl_signal = Label(text="0000", font_size='26sp', color=get_color_from_hex('#10B981'))
        sig_sub.add_widget(self.lbl_signal)
        sig_sub.add_widget(Label(text="SIGNAL (LSB)", font_size='11sp', color=get_color_from_hex('#64748B')))
        metrics_box.add_widget(sig_sub)
        
        # Sous-bloc Profondeur
        depth_sub = BoxLayout(orientation='vertical', padding=4)
        self.lbl_depth = Label(text="-- cm", font_size='26sp', color=get_color_from_hex('#F59E0B'))
        depth_sub.add_widget(self.lbl_depth)
        depth_sub.add_widget(Label(text="PROFONDEUR", font_size='11sp', color=get_color_from_hex('#64748B')))
        metrics_box.add_widget(depth_sub)
        
        left_panel.add_widget(metrics_box)

        # 3. BLOC ANALYSE GEOLOGIQUE & REGULATEURS (Tableau de bord aligné)
        data_panel = BoxLayout(orientation='vertical', spacing=6, padding=5, size_hint_y=0.47)
        
        self.lbl_sens_pot = Label(text="🎛️ SEUIL SENSIVITÉ  : -- LSB", font_size='11.5sp', halign='left', color=get_color_from_hex('#E2E8F0'))
        self.lbl_pulse_pot = Label(text="⚡ LARGEUR IMPULSION : -- µs", font_size='11.5sp', halign='left', color=get_color_from_hex('#E2E8F0'))
        self.lbl_temp = Label(text="🌡️ TEMPÉRATURE SOL : -- °C", font_size='11.5sp', halign='left', color=get_color_from_hex('#94A3B8'))
        self.lbl_moist = Label(text="💧 HUMIDITÉ TERRE  : -- %", font_size='11.5sp', halign='left', color=get_color_from_hex('#94A3B8'))
        self.progress_moist = ProgressBar(max=4096, value=0, size_hint_y=0.1)
        
        # Forcer l'alignement du texte à gauche pour un look pro
        for lbl in [self.lbl_sens_pot, self.lbl_pulse_pot, self.lbl_temp, self.lbl_moist]:
              lbl.bind(size=lbl.setter('text_size'))


            data_panel.add_widget(lbl)
        data_panel.add_widget(self.progress_moist)
        
        left_panel.add_widget(data_panel)
        root.add_widget(left_panel)

        # =====================================================================
        # PANNEAU DROIT : SCANNER MATRICIEL 3D/2D
        # =====================================================================
        right_panel = BoxLayout(orientation='vertical', size_hint=(0.62, 1))
        right_panel.add_widget(Label(text="[b]CARTOGRAPHIE DU SOUS-SOL (GRID 12x12 RENDER)[/b]", font_size='13sp', color=get_color_from_hex('#38BDF8'), markup=True, size_hint_y=0.06))
        
        self.matrix_view = MatrixScanner(size_hint=(1, 0.94))
        right_panel.add_widget(self.matrix_view)
        
        root.add_widget(right_panel)

        Clock.schedule_interval(self.update_telemetry, 0.02)
        return root

    def log_to_file(self, sig, depth, metal, sens, pulse, moist, temp):
        with open(self.log_filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime('%H:%M:%S.%f')[:-3], self.cur_x, self.cur_y, sig, depth, metal, sens, pulse, moist, temp])

    def update_telemetry(self, dt):
        if self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line.startswith("$PI_DATA"):
                    tokens = line.split(',')
                    sig = int(tokens[1])
                    depth = int(tokens[2])
                    metal = tokens[3]
                    sens_val = int(tokens[4])
                    pulse_val = int(tokens[5])
                    
                    moist_val = random.randint(1100, 2400) # Simulation ou lecture sonde
                    temp_val = 26.2
                    vdi_index = int((sig / 4096.0) * 99) if sig > sens_val else 0

                    # Rafraîchissement des mesures alignées
                    self.lbl_vdi.text = f"INDICE VDI : {vdi_index:02d}"
                    self.lbl_signal.text = f"{sig}"
                    self.lbl_depth.text = f"{depth} cm"
                    self.lbl_sens_pot.text = f"🎛️ SEUIL SENSIVITÉ  : {sens_val} LSB"
                    self.lbl_pulse_pot.text = f"⚡ LARGEUR IMPULSION : {pulse_val} µs"
                    self.lbl_temp.text = f"🌡️ TEMPÉRATURE SOL : {temp_val} °C"
                    self.lbl_moist.text = f"💧 HUMIDITÉ TERRE  : {int((moist_val/4096)*100)} %"
                    self.progress_moist.value = moist_val

                    # Affichage raffiné des noms de métaux traduit en français
                    if sig > sens_val:
                        if metal == "GOLD/COPPER":
                            self.lbl_metal.text = "[b][COLOR=F59E0B]OR / METAUX PRECIEUX[/COLOR][/b]"
                        else:
                            self.lbl_metal.text = "[b][COLOR=EF4444]FER / MATERIAU FERREUX[/COLOR][/b]"
                    else:
                        self.lbl_metal.text = "[b][COLOR=64748B]SOL NEUTRE[/COLOR][/b]"

                    self.matrix_view.update_voxel(self.cur_x, self.cur_y, sig, metal)
                    self.log_to_file(sig, depth, metal, sens_val, pulse_val, moist_val, temp_val)
                    
                    self.cur_y += 1
                    if self.cur_y >= 12:
                        self.cur_y = 0
                        self.cur_x += 1
                        if self.cur_x >= 12: self.cur_x = 0
            except Exception as e:
                pass

if __name__ == '__main__':
    UltimateRefinedApp().run()