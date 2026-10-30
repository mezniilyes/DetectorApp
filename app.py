import sys
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

try:
    import serial
except ImportError:
    serial = None

class MatrixScanner(GridLayout):
    """ Grille d'imagerie thermique géophysique 12x12 """
    def __init__(self, **kwargs):
        super(MatrixScanner, self).__init__(**kwargs)
        self.cols = 12
        self.rows = 12
        self.spacing = 2
        self.cells = []
        
        for i in range(144):
            lbl = Label(text="", size_hint=(1, 1))
            with lbl.canvas.before:
                Color(rgb=get_color_from_hex('#1A202C')) # Couleur terre neutre
                lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
            lbl.bind(pos=self._update_rect, size=self._update_rect)
            self.add_widget(lbl)
            self.cells.append(lbl)

    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(rgb=getattr(instance, 'cell_color', get_color_from_hex('#1A202C')))
            instance.rect = Rectangle(pos=instance.pos, size=instance.size)

    def update_voxel(self, x, y, signal, metal):
        index = (x * 12) + y
        if index < len(self.cells):
            cell = self.cells[index]
            if signal < 40:
                cell.cell_color = get_color_from_hex('#1A202C') # Vide
            elif metal == "GOLD/COPPER":
                cell.cell_color = get_color_from_hex('#D69E2E') # Doré Brillant (Or)
            elif metal == "IRON/FERROUS":
                cell.cell_color = get_color_from_hex('#E53E3E') # Rouge Industriel (Fer)
            else:
                cell.cell_color = get_color_from_hex('#3182CE') # Bleu Minéral
            cell.canvas.before.clear()
            with cell.canvas.before:
                Color(rgb=cell.cell_color)
                instance_rect = Rectangle(pos=cell.pos, size=cell.size)

class ProfessionalDetectorApp(App):
    def build(self):
        self.title = "PRO-GEORADAR 3D ANALYSIS SYSTEM"
        self.cur_x, self.cur_y = 0, 0
        
        # Liaison Série Bluetooth HC-05
        self.ser = None
        if serial:
            try: self.ser = serial.Serial('COM3', 115200, timeout=0.02)
            except: print("Déploiement en mode Simulation Graphique.")

        # Layout Principal (Style cockpit)
        root = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        with root.canvas.before:
            Color(rgb=get_color_from_hex('#0F172A')) # Fond Noir Espace/Militaire
            self.rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda ins, val: setattr(self.rect, 'pos', val) or setattr(self.rect, 'size', ins.size))

        # ==========================================
        # PANNEAU GAUCHE : PARAMÈTRES ET GRAPHES PRO
        # ==========================================
        left_panel = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=12)
        
        # Statut du système
        left_panel.add_widget(Label(text="[b]SYSTEM DISCOVERY PRO[/b]", font_size='16sp', color=get_color_from_hex('#38BDF8'), markup=True, size_hint_y=0.05))
        
        # Jauges d'analyse sol
        self.lbl_status = Label(text="STATUT : RECHERCHE...", font_size='14sp', color=get_color_from_hex('#94A3B8'), size_hint_y=0.05)
        left_panel.add_widget(self.lbl_status)
        
        # Bloc d'analyse environnementale de la Terre
        env_box = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.3)
        self.lbl_temp = Label(text="🌡️ TEMPÉRATURE SOL : -- °C", font_size='13sp', halign='left')
        self.lbl_moist = Label(text="💧 HUMIDITÉ TERRE : -- %", font_size='13sp', halign='left')
        self.progress_moist = ProgressBar(max=4096, value=0, size_hint_y=0.2)
        env_box.add_widget(self.lbl_temp)
        env_box.add_widget(self.lbl_moist)
        env_box.add_widget(self.progress_moist)
        left_panel.add_widget(env_box)

        # Indicateurs numériques géants de la cible
        target_box = BoxLayout(orientation='vertical', padding=10, spacing=5, size_hint_y=0.6)
        self.lbl_signal = Label(text="0000\n[size=12]SIGNAL INDUCTION (LSB)[/size]", font_size='32sp', color=get_color_from_hex('#10B981'), markup=True)
        self.lbl_depth = Label(text="-- cm\n[size=12]PROFONDEUR ESTIMÉE[/size]", font_size='28sp', color=get_color_from_hex('#F59E0B'), markup=True)
        self.lbl_metal = Label(text="[b]SOL NEUTRE[/b]", font_size='22sp', color=get_color_from_hex('#EF4444'), markup=True)
        
        target_box.add_widget(self.lbl_signal)
        target_box.add_widget(self.lbl_depth)
        target_box.add_widget(self.lbl_metal)
        left_panel.add_widget(target_box)

        root.add_widget(left_panel)

        # ==========================================
        # PANNEAU DROIT : CARTOGRAPHIE 3D THERMIQUE
        # ==========================================
        right_panel = BoxLayout(orientation='vertical', size_hint=(0.6, 1))
        right_panel.add_widget(Label(text="[b]IMAGERIE DU SOUS-SOL EN TEMPS RÉEL (3D RENDER)[/b]", font_size='14sp', color=get_color_from_hex('#38BDF8'), markup=True, size_hint_y=0.05))
        
        self.matrix_view = MatrixScanner(size_hint=(1, 0.95))
        right_panel.add_widget(self.matrix_view)
        
        root.add_widget(right_panel)

        # Cadencement de lecture ultra-rapide (20ms pour coller à la vitesse du STM32)
        Clock.schedule_interval(self.update_telemetry, 0.02)
        return root

    def update_telemetry(self, dt):
        if self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line.startswith("$PI_DATA"):
                    tokens = line.split(',')
                    sig = int(tokens[1])
                    depth = int(tokens[2])
                    metal = tokens[3]
                    moist = int(tokens[4])
                    temp = float(tokens[5])

                    # Actualisation instantanée du dashboard pro
                    self.lbl_signal.text = f"{sig}\n[size=12]SIGNAL INDUCTION (LSB)[/size]"
                    self.lbl_depth.text = f"{depth} cm\n[size=12]PROFONDEUR ESTIMÉE[/size]"
                    self.lbl_temp.text = f"🌡️ TEMPÉRATURE SOL : {temp} °C"
                    self.lbl_moist.text = f"💧 HUMIDITÉ TERRE : {int((moist/4096)*100)} %"
                    self.progress_moist.value = moist
                    self.lbl_status.text = "STATUT : ADQUISITION ACTIVE"

                    if sig > 35:
                        self.lbl_metal.text = f"[b][COLOR=D69E2E]{metal}[/color][/b]"
                    else:
                        self.lbl_metal.text = "[COLOR=64748B]SOL NEUTRE[/color]"

                    # Dessin du point géophysique
                    self.matrix_view.update_voxel(self.cur_x, self.cur_y, sig, metal)
                    
                    # Balayage matriciel automatique
                    self.cur_y += 1
                    if self.cur_y >= 12:
                        self.cur_y = 0
                        self.cur_x += 1
                        if self.cur_x >= 12: self.cur_x = 0
            except: pass
        else:
            # Mode démo si le STM32 n'est pas branché (simulation graphique pour tester l'interface)
            sim_sig = random.randint(0, 500) if random.random() > 0.8 else 10
            sim_metal = "GOLD/COPPER" if sim_sig > 300 else "IRON/FERROUS"
            self.matrix_view.update_voxel(self.cur_x, self.cur_y, sim_sig, sim_metal)
            self.cur_y += 1
            if self.cur_y >= 12:
                self.cur_y = 0
                self.cur_x += 1
                if self.cur_x >= 12: self.cur_x = 0

if __name__ == '__main__':
    ProfessionalDetectorApp().run()
