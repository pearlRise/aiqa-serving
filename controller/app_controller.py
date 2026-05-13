import atexit
import time
from PySide6.QtCore import QObject, QTimer, QEvent, QThread, Signal
from PySide6.QtWidgets import QApplication
from core.ollama_manager import ServerManager
from controller.chat_controller import ChatController
from view.components.ui_main_window import MainWindow

class ModelWorker(QThread):
    finished = Signal()

    def __init__(self, ollama_manager, action, model_name):
        super().__init__()
        self.ollama = ollama_manager
        self.action = action
        self.model_name = model_name

    def run(self):
        if self.action == 'load':
            self.ollama.load_model(self.model_name)
        elif self.action == 'unload':
            self.ollama.unload_model(self.model_name)
        self.finished.emit()

class AppController(QObject):
    def __init__(self):
        super().__init__()
        self.window = MainWindow()
        self.ollama = ServerManager()
        atexit.register(self.ollama.stop_server)
        
        self.chat_logic = ChatController(self.ollama)
        self.model_worker = None
        
        self.is_server_starting = False
        self.is_server_stopping = False
        self.current_engine = "MLX"
        self.mlx_active_model = None

        self._connect_signals()
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_ollama_status)
        self.status_timer.start(2000)

        self.window.chat_view.scroll.viewport().installEventFilter(self)
        self.window.selection_view.scroll.viewport().installEventFilter(self)
        self.window.template_view.scroll.viewport().installEventFilter(self)
        
        QTimer.singleShot(100, self.check_ollama_status)

    def _connect_signals(self):
        self.window.chat_view.send_btn.clicked.connect(self.handle_send_message)
        self.window.chat_view.input_field.returnPressed.connect(self.handle_send_message)
        
        self.chat_logic.thinking_started.connect(lambda: self.window.chat_view.add_chat_bubble("{...}", is_me=False, sender_name="Gemma"))
        self.chat_logic.chunk_delivered.connect(self.window.chat_view.update_last_bubble_stream)
        
        self.window.home_view.serve_requested.connect(self.toggle_ollama_serve)
        self.window.home_view.chat_requested.connect(self.window.slide_to_chat)
        self.window.home_view.selection_requested.connect(self.slide_to_selection)
        self.window.home_view.template_requested.connect(self.window.slide_to_template)
        self.window.home_view.engine_toggle_btn.clicked.connect(self.toggle_engine)
        
        self.window.selection_view.model_selected.connect(self.handle_model_selection)
        
        self.window.close_requested = self.handle_close_event

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if obj == self.window.chat_view.scroll.viewport() and self.window.is_chat_active and event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                self.window.slide_to_home()
                return True
            elif hasattr(self.window, 'selection_view') and obj == self.window.selection_view.scroll.viewport() and self.window.is_selection_active and event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                self.window.slide_to_home()
                return True
            elif hasattr(self.window, 'template_view') and obj == self.window.template_view.scroll.viewport() and self.window.is_template_active and event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                self.window.slide_to_home()
                return True
        return super().eventFilter(obj, event)

    def handle_send_message(self):
        text = self.window.chat_view.input_field.toPlainText().strip()
        if text:
            self.window.chat_view.add_chat_bubble(text, is_me=True)
            self.chat_logic.process_message(text)
            self.window.chat_view.input_field.clear()

    def handle_model_selection(self, model_name):
        if model_name in ["Create Model", "Model Configuration"]:
            return
            
        if self.current_engine == "Ollama":
            if self.model_worker and self.model_worker.isRunning():
                return

            action = None
            model_to_act_on = None

            if model_name == "Unselected":
                if self.ollama.active_model:
                    action = 'unload'
                    model_to_act_on = self.ollama.active_model
            else:
                if self.ollama.active_model == model_name:
                    action = 'unload'
                    model_to_act_on = model_name
                else:
                    action = 'load'
                    model_to_act_on = model_name
            
            if not action:
                return

            self.window.home_view.update_model_status("Loading")
            QApplication.processEvents()

            self.model_worker = ModelWorker(self.ollama, action, model_to_act_on)
            self.model_worker.finished.connect(self._on_model_op_finished)
            self.model_worker.start()
        else:
            if model_name == "Unselected":
                self.mlx_active_model = None
            else:
                if getattr(self, 'mlx_active_model', None) == model_name: self.mlx_active_model = None
                else: self.mlx_active_model = model_name
            active = self.mlx_active_model
            
            self.window.selection_view.set_active_model(active if active else "Unselected")
            self.window.home_view.update_model_status(active)
            self.check_ollama_status()

    def _on_model_op_finished(self):
        active = self.ollama.active_model
        self.window.selection_view.set_active_model(active if active else "Unselected")
        self.window.home_view.update_model_status(active)
        self.check_ollama_status()

        if self.model_worker:
            self.model_worker.deleteLater()
            self.model_worker = None

    def slide_to_selection(self):
        if self.window.is_chat_active or self.window.is_selection_active: return
        
        if self.current_engine == "Ollama":
            if not self.ollama.is_running(): return
            self.window.selection_view.update_model_list(self.ollama.get_local_models(), self.ollama.active_model, "Ollama")
        else:
            mlx_dummies = [{"name": "mlx-community/Llama-3-8B", "size": 0}]
            self.window.selection_view.update_model_list(mlx_dummies, getattr(self, 'mlx_active_model', None), "MLX")
        self.window.slide_to_selection()

    def toggle_ollama_serve(self):
        if self.current_engine == "Ollama":
            if not self.ollama.is_running():
                self.is_server_starting, self.is_server_stopping = True, False
                self.update_server_ui("loading")
                QApplication.processEvents()
                self.ollama.start_server()
            else:
                self.is_server_starting, self.is_server_stopping = False, True
                self.update_server_ui("loading")
                QApplication.processEvents()
                self.ollama.stop_server()
                for _ in range(15):
                    if not self.ollama.is_running(): break
                    QApplication.processEvents(); time.sleep(0.2)
                self.is_server_stopping = False
                self.check_ollama_status()
        elif self.current_engine == "MLX":
            if not getattr(self, 'mlx_active_model', None):
                return
            print("MLX Serve mode: Logic not yet implemented.")

    def check_ollama_status(self):
        if self.current_engine == "MLX":
            self.update_server_ui("stopped")
            self.window.home_view.update_model_status(None)
            return

        if self.ollama.is_running():
            self.is_server_starting = False
            self.update_server_ui("loading" if self.is_server_stopping else "running")
            if not self.is_server_stopping: self.window.home_view.update_model_status(self.ollama.active_model)
        else:
            self.ollama.active_model = None
            if self.is_server_starting:
                if self.ollama.process and self.ollama.process.poll() is not None:
                    self.is_server_starting = False; self.update_server_ui("stopped"); self.window.home_view.update_model_status(None)
                else: self.update_server_ui("loading")
            else:
                self.is_server_stopping = False; self.update_server_ui("stopped"); self.window.home_view.update_model_status(None)

    def update_server_ui(self, status):
        has_model = (self.ollama.active_model is not None) if self.current_engine == "Ollama" else (getattr(self, 'mlx_active_model', None) is not None)
        self.window.home_view.update_dashboard_state(self.current_engine, status, has_model)

    def toggle_engine(self):
        if self.ollama.is_running() or self.is_server_starting or self.ollama.process is not None:
            self.is_server_starting, self.is_server_stopping = False, True
            self.update_server_ui("loading"); QApplication.processEvents()
            if self.ollama.active_model: self.ollama.unload_model(self.ollama.active_model); self.ollama.active_model = None; self.window.home_view.update_model_status(None); QApplication.processEvents()
            self.ollama.stop_server()
            for _ in range(15):
                if not self.ollama.is_running() and self.ollama.process is None: break
                QApplication.processEvents(); time.sleep(0.2)
            self.is_server_stopping = False; self.check_ollama_status()
            
        self.current_engine = "MLX" if self.current_engine == "Ollama" else "Ollama"
        style = "background-color: #FF9500;" if self.current_engine == "MLX" else "background-color: #007AFF;"
        hover = "background-color: #CC7700;" if self.current_engine == "MLX" else "background-color: #0051A8;"
        self.window.home_view.engine_toggle_btn.setText(self.current_engine)
        self.window.home_view.engine_toggle_btn.setStyleSheet(f"QPushButton {{ {style} color: white; border-radius: 16px; font-weight: bold; font-size: 13px; border: none; }} QPushButton:hover {{ {hover} }}")
        self.check_ollama_status()

    def handle_close_event(self, event):
        self.update_server_ui("loading"); QApplication.processEvents()
        self.ollama.stop_server()
        for _ in range(15):
            if not self.ollama.is_running(): break
            QApplication.processEvents(); time.sleep(0.2)
        event.accept()