import pyautogui
import pyaudio
import audioop
import threading
import time
import win32api
import configparser
import random
import numpy as np
import cv2
import dearpygui.dearpygui as dpg
from windowcapture import WindowCapture
import random

class FishermanBot:
    def __init__(self, bobber, bar, region=None, settings_file='settings.ini'):
        # Inicialização do bot com configurações básicas
        # bobber: imagem da boia de pesca
        # bar: imagem da barra do minigame
        # region: região da tela para captura
        # settings_file: arquivo de configurações
        
        self.bobber = bobber
        self.bar = bar
        self.region = region
        self.settings_file = settings_file
        self.parser = configparser.ConfigParser()
        self.parser.read(self.settings_file)

        # Carrega configurações do arquivo .ini
        self.debug_mode = self.parser.getboolean('Settings', 'debug')
        self.max_volume = self.parser.getint('Settings', 'Volume_Threshold')
        self.detection_threshold = self.parser.getfloat('Settings', 'detection_threshold')

        # Define área de rastreamento na tela
        screen_area = self.parser.get('Settings', 'tracking_zone').strip('()')
        cordies = screen_area.split(',')
        self.screen_area = tuple(map(int, cordies))

        # Variáveis de estado do bot
        self.coords = []  # Coordenadas dos pontos de pesca
        self.total = 0    # Volume total do áudio
        self.STATE = "IDLE"  # Estado atual do bot
        self.stop_button = False  # Controle de parada
        self.state_left = win32api.GetKeyState(0x01)  # Estado do botão esquerdo do mouse
        self.state_right = win32api.GetKeyState(0x02) # Estado do botão direito do mouse
        self.fish_count = 0      # Contador de peixes pescados
        self.bait_counter = 0    # Contador de iscas usadas
        self.food_timer = 0      # Temporizador para comer
        self.minigame_counter = 0  # Contador de minigames
        self.bait_item_coords = None  # Coordenadas do item de isca
        self.use_button_coords = None  # Coordenadas do botão de usar
        self.bait_amount = self.parser.getint('Settings', 'bait_amount')  # Quantidade de iscas
        self.bait_counter = 0  # Contador de iscas usadas
        self.last_minigame_time = time.time()  # Armazena o tempo da última entrada no minigame
        self.check_interval = 600  # 10 minutos em segundos
        self.use_bait_boolean = True # Verifica quer usar iscas ou não
        # Inicializa captura da janela do Albion
        self.wincap = WindowCapture('Albion Online Client')

    def check_volume(self):
        # Monitora o volume do áudio para detectar quando um peixe morde a isca
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True, frames_per_buffer=1024)
        while not self.stop_button:
            self.total = 0
            for _ in range(2):
                data = stream.read(1024)
                reading = audioop.max(data, 2)
                self.total += reading
                if self.total > self.max_volume and self.STATE not in ["MINIGAME", "DELAY", "LANCANDO", "COMENDO", "ISCA"]:
                    self.do_minigame()

    def get_new_spot(self):
        # Seleciona aleatoriamente um novo ponto de pesca
        return random.choice(self.coords)



    def cast_hook(self):
        # Função para lançar a linha de pesca
        # Gerencia o ciclo de lançamento e espera
        while not self.stop_button:
            if self.STATE in ["LANCANDO", "INICIADO"]:
                time.sleep(random.uniform(1.2, 3.0))
                if self.fish_count % 10 == 0 and self.use_bait_boolean == True :  # A cada 10 peixes, usa isca
                    # Verifica se há iscas suficientes antes de usar
                    if self.bait_counter < self.bait_amound:
                        self.log_info("Sem iscas suficientes para usar.")
                    else:
                        self.use_bait()  # Chama a função para usar iscas
                        time.sleep(0.2)
                # Processo de lançamento da linha
                pyautogui.mouseUp()
                x, y = self.get_new_spot()
                pyautogui.moveTo(x, y, tween=pyautogui.linear, duration=0.2)
                time.sleep(0.2)
                pyautogui.mouseDown()
                time.sleep(random.uniform(0.3, 0.9))
                pyautogui.mouseUp()
                self.log_info(f"STATE {self.STATE}")
                time.sleep(2.5)
                self.STATE = "LANCAR"
            elif self.STATE == "LANCAR":
                time.sleep(20)
                if self.STATE == "LANCAR":
                    self.log_info("Parece estar preso no lançamento. Relançando.")
                    pyautogui.press('s')
                    self.STATE = "LANCANDO"

    def eat_food(self):
        # Função para gerenciar o consumo de comida
        # Executa a cada 30 minutos (1800 segundos)
        while not self.stop_button:
            time.sleep(1800)
            self.STATE = "COMENDO"
            if self.STATE == "COMENDO":
                self.log_info("EATING FOOD")
                pyautogui.press('2')
                self.STATE = "LANCANDO"

    def use_bait(self):
        
        """
        Função para usar iscas no jogo.
        Abre o menu, seleciona o primeiro item e clica no botão de usar.
        """
        self.STATE = "ISCA"  # Muda o estado para "ISCA" (usando isca)
        self.log_info(f"STATE {self.STATE}")  # Registra o estado atual no log

        if self.bait_counter >= self.bait_amound:
            self.log_info("Sem iscas suficientes para usar.")
            self.STATE = "LANCANDO"  # Muda o estado para "LANCANDO" (lançando)
            return

       
        # Seleciona o item de isca
        if self.bait_item_coords:
            pyautogui.press('i')  # Exemplo: 'i' para inventário
            time.sleep(0.5)  # Aguarda o menu abrir
            pyautogui.moveTo(self.bait_item_coords[0], self.bait_item_coords[1], duration=0.2)
            pyautogui.click()
            time.sleep(0.5)  # Aguarda a seleção
            
            
        # Clica no botão de usar
        if self.use_button_coords:
            pyautogui.moveTo(self.use_button_coords[0], self.use_button_coords[1])
            pyautogui.click()
            time.sleep(0.2)  # Aguarda a ação ser concluída
            self.bait_counter += 1  # Incrementa o contador de iscas usadas
            self.log_info(f"isca usada, restam {self.bait_amount - self.bait_counter}")

        # Fecha o menu
        pyautogui.press('i')  # Exemplo: 'i' para inventário
        time.sleep(0.2)  # Aguarda o menu fechar
        pyautogui.press('s')  # interrompe todas as ações
        self.STATE = "LANCANDO"  # Muda o estado para "LANCANDO" (lançando)

    def do_minigame(self):
        # Executa o minigame de pesca quando um peixe é fisgado
        # Controla o mouse baseado na posição da boia

        # Verifica se o bot não está em estados de lançamento, iniciado ou comendo
        if self.STATE not in ["LANCANDO", "INICIADO", "COMENDO", " ISCA"]:
            self.STATE = "MINIGAME"  # Muda o estado para "MINIGAME" (resolvendo)
            self.log_info(f"STATE {self.STATE}")  # Registra o estado atual no log
            pyautogui.mouseDown()  # Simula o pressionamento do botão do mouse
            pyautogui.mouseUp()    # Simula o soltar do botão do mouse
            time.sleep(0.2)        # Aguarda 200 milissegundos para estabilizar

            # Chama a função detect_bobber para verificar a posição da boia
            valid, location, size = self.detect_bobber()
            
            # Se a boia for detectada com sucesso
            if valid == True:
                self.last_minigame_time = time.time()  # Atualiza o timestamp
                self.fish_count += 1  # Incrementa o contador de peixes pescados
               
                
                while True:  # Loop contínuo para monitorar a boia
                    valid, location, size = self.detect_bobber()  # Verifica novamente a boia
                    
                    # min_limit = int(size[1] * 0.3)
                    # max_limit = int(size[1] * 0.7)

                    # Se a boia ainda for válida
                    if valid == True:
                        # Se a posição da boia estiver na metade esquerda da barra
                        if location <= int(size[1] / 2):
                            pyautogui.mouseDown()  # Pressiona o botão do mouse (captura)
                        # Se a posição da boia estiver na metade direita da barra
                        elif location >= int(size[1] / 2):
                            pyautogui.mouseUp()  # Solta o botão do mouse (libera)
                    else:
                        # Se a boia não for mais detectada e não estiver em estado de lançamento
                        if self.STATE != "LANCANDO":
                            self.STATE = "LANCANDO"  # Muda o estado para "LANCANDO"
                            time.sleep(0.3) # Aguarda 300 milissegundos
                            pyautogui.mouseUp()  # Solta o botão do mouse
                            break  # Sai do loop
            else:
                self.STATE = "LANCANDO"  # Se a boia não for detectada, muda o estado para "LANCANDO"
    
    def monitor_bot(self):
        """
        Monitora o comportamento do bot e para se necessário.
        """
        while not self.stop_button:
            current_time = time.time()
            if current_time - self.last_minigame_time > self.check_interval:
                self.log_info("O bot não entrou no minigame em 10 minutos. Parando o bot.")
                self.stop_bot()  # Chama a função para parar o bot
            time.sleep(60)  # Verifica a cada 60 segundos



    def generate_coords(self):
        # Gera coordenadas para pontos de pesca
        # Usuário define os pontos pressionando espaço
        amount_of_coords = dpg.get_value("Amount Of Spots")
        if amount_of_coords == 0:
            amount_of_coords = 1
        for n in range(amount_of_coords):
            self.log_info(f"[spot: {n + 1}] | Press Spacebar over the spot you want")
            time.sleep(1)
            while True:
                if win32api.GetKeyState(0x20) < 0:
                    x, y = pyautogui.position()
                    self.coords.append([x, y])
                    self.log_info(f"Position: {n + 1} Saved. | {x, y}")
                    break
                time.sleep(0.001)

    def grab_screen(self):
        # Define a área de rastreamento na tela
        # Usuário seleciona dois pontos para definir a região
        image_coords = []
        while True:
            if win32api.GetKeyState(0x20) < 0:
                x, y = pyautogui.position()
                image_coords.append([x, y])
                if len(image_coords) == 2:
                    break
            time.sleep(0.001)
        start_point, end_point = image_coords
        self.screen_area = start_point[0], start_point[1], end_point[0], end_point[1]
        self.log_info(f"área atualizada {self.screen_area}")

    def detect_minigame(self, screenshot, bar):
        # Detecta se o minigame está ativo
        # Usa template matching para encontrar a barra do minigame
        result = cv2.matchTemplate(screenshot, bar, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val >= self.detection_threshold:
            return True
        return False

    
    def set_bait_item_coords(self):
        """
        Permite ao usuário definir as coordenadas do item de isca.
        """
        self.log_info("Pressione Espaço sobre o item de isca.")
        while True:
            if win32api.GetKeyState(0x20) < 0:  # 0x20 é a tecla espaço
                self.bait_item_coords = pyautogui.position()
                self.log_info(f"Coordenadas do item de isca salvas: {self.bait_item_coords}")
                break
            time.sleep(0.001)

    def set_use_button_coords(self):
        """
        Permite ao usuário definir as coordenadas do botão de usar.
        """
        self.log_info("Pressione Espaço sobre o botão de usar.")
        while True:
            if win32api.GetKeyState(0x20) < 0:  # 0x20 é a tecla espaço
                self.use_button_coords = pyautogui.position()
                self.log_info(f"Coordenadas do botão de usar salvas: {self.use_button_coords}")
                break
            time.sleep(0.001)




    def detect_bobber(self):
        # Detecta a posição da boia na tela
        # Retorna se é válido, localização e tamanho
        screenshot = self.wincap.get_screenshot(region=self.region)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        bobber = cv2.imread(self.bobber)
        bar = cv2.imread(self.bar)
        result = cv2.matchTemplate(screenshot, bobber, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return [self.detect_minigame(screenshot, bar), max_loc[0] + bobber.shape[1] // 2, screenshot.shape]
    
    def log_info(self, message):
        # Função para logging de mensagens na interface
        current_logs = dpg.get_value("LogWindow")
        updated_logs = f"{current_logs}\n{message}" if current_logs else message
        dpg.set_value("LogWindow", updated_logs)

    def save_settings(self):
        # Salva as configurações no arquivo .ini
        with open(self.settings_file, 'w') as configfile:
            self.parser.set('Settings', 'Volume_Threshold', str(self.max_volume))
            self.parser.set('Settings', 'tracking_zone', str(self.screen_area))
            self.parser.set('Settings', 'detection_threshold', str(self.detection_threshold))
            self.parser.set('Settings', 'bait_amount', str(self.bait_amound))
            self.parser.set('Settings', 'use_bait_boolean', str(self.use_bait_boolean))
            self.parser.write(configfile)
        self.log_info("Saved New Settings to settings.ini")

    def start_bot(self):
        # Inicia o bot e suas threads
        self.log_info("Bot started successfully.")
        self.stop_button = False
        time.sleep(3)
        threading.Thread(target=self.eat_food).start()
        threading.Thread(target=self.check_volume).start()
        threading.Thread(target=self.cast_hook).start()
        time.sleep(2)
        pyautogui.press('s')
        time.sleep(2)
        self.STATE = "INICIADO"

    def stop_bot(self):
        # Para a execução do bot
        self.log_info("Bot stopped.")
        self.stop_button = True
        self.STATE = "STOPPED"

    def update_use_bait_boolean(self, sender, app_data):
        """
        Atualiza a variável use_bait_boolean com o valor do checkbox.
        """
        self.use_bait_boolean = app_data  # app_data será True ou False
        self.log_info(f"Bait boolean set to: {self.use_bait_boolean}")

        # Mostra ou oculta os botões de coordenadas do item e uso da isca
        if self.use_bait_boolean:
            dpg.show_item("bait_use")
            # dpg.show_item(self.set_bait_amount)
            # dpg.show_item(self.bait_item_button)
            # dpg.show_item(self.use_button_button)
            dpg.configure_item("bait", height=150)
        else:
            dpg.hide_item("bait_use")
            dpg.configure_item("bait", height=50)
            # dpg.hide_item(self.set_bait_amount)
            # dpg.hide_item(self.bait_item_button)
            # dpg.hide_item(self.use_button_button)



    def init_gui(self):
        """
        Inicializa a interface gráfica com todos os controles.
        """
        dpg.create_context()
        dpg.create_viewport(title="Fisherman", width=700, height=500)

        with dpg.window(label="Fisherman Window", width=684, height=460):
            with dpg.group():
                # Controles da interface
                dpg.add_input_int(label="Amount Of Spots", tag="Amount Of Spots", 
                                  max_value=10, min_value=1, default_value=1, width=120)
                dpg.add_input_int(label="Set Volume Threshold", tag="Set Volume Threshold", 
                                  max_value=100000, min_value=0, default_value=self.max_volume, width=120)
                dpg.add_input_float(label="Set Detection Threshold", tag="Set Detection Threshold", 
                                    min_value=0.1, max_value=1.0, default_value=self.detection_threshold, width=120)
                
                
                
            with dpg.group(tag="baits", horizontal=True):

                with dpg.child_window(tag="bait", width=520, height=150):
                    
                    dpg.add_checkbox(label="Use Bait", default_value=self.use_bait_boolean, callback=self.update_use_bait_boolean)
                    with dpg.child_window(tag="bait_use", width=400, height=100):
                        self.set_bait_amount = dpg.add_input_int(label="Set Bait Amount", width=80, max_value=100, min_value=0, default_value=self.bait_amount)
                        self.bait_item_button = dpg.add_button(label="Set Bait Item Location", callback=self.set_bait_item_coords)
                        self.use_button_button = dpg.add_button(label="Set Use Button Location", callback=self.set_use_button_coords)


            # Botões de controle
            dpg.add_button(label="Set Fishing Spots", callback=self.generate_coords)
            dpg.add_button(label="Set Tracking Zone", callback=self.grab_screen)
            dpg.add_button(label="Start Bot", callback=self.start_bot)
            dpg.add_button(label="Stop Bot", callback=self.stop_bot)
            dpg.add_button(label="Save Settings", callback=self.save_settings)

            

            # Área de logs
            dpg.add_text("Log Messages:")
            dpg.add_input_text(multiline=True, readonly=True, 
                               width=650, height=150, tag="LogWindow", 
                               default_value="")

        # Inicializa a interface
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
