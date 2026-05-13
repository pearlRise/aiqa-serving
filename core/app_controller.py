import os
import atexit
import time
from PySide6.QtCore import QObject, QTimer, QEvent, QThread, Signal
from PySide6.QtWidgets import QApplication
from core.ollama_manager import ServerManager
from core.chat_controller import ChatController
from view.components.ui_main_window import MainWindow

class ModelWorker(QThread):
    finished = Signal()
    status_flag = Signal(str, str, str)

    def __init__(self, ollama_manager, action, target_model, current_model=None):
        super().__init__()
        self.ollama = ollama_manager
        self.action = action
        self.target_model = target_model
        self.current_model = current_model
        self.is_cancelled = False

    def run(self):
        try:
            if self.action == 'switch':
                if self.current_model:
                    self.status_flag.emit("model_worker", "start", "Unloading...")
                    self.ollama.unload_model(self.current_model)
                if not self.is_cancelled:
                    self.status_flag.emit("model_worker", "start", "Loading...")
                    self.ollama.load_model(self.target_model)
                if self.is_cancelled:
                    self.ollama.unload_model(self.target_model)
                    self.status_flag.emit("model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("model_worker", "end", "Loaded")

            elif self.action == 'load':
                self.status_flag.emit("model_worker", "start", "Loading...")
                self.ollama.load_model(self.target_model)
                if self.is_cancelled:
                    self.ollama.unload_model(self.target_model)
                    self.status_flag.emit("model_worker", "end", "Cancelled")
                else:
                    self.status_flag.emit("model_worker", "end", "Loaded")

            elif self.action == 'unload':
                self.status_flag.emit("model_worker", "start", "Unloading...")
                self.ollama.unload_model(self.target_model if self.target_model else self.current_model)
                self.status_flag.emit("model_worker", "end", "Unloaded")
        except Exception as e:
            self.status_flag.emit("model_worker", "exception", "Exception")
            
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
        self.window.dynamic_island.left_btn.clicked.connect(self.handle_back_requested)
        
        self.chat_logic.thinking_started.connect(lambda: self.window.chat_view.add_chat_bubble("{...}", is_me=False, sender_name="Gemma"))
        self.chat_logic.chunk_delivered.connect(self.window.chat_view.update_last_bubble_stream)
        self.chat_logic.status_flag.connect(self.handle_task_status)
        
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
        
    def handle_task_status(self, task_id, flag_type, text):
        if flag_type == "start":
            self.window.dynamic_island.show_progress(task_id, text)
        elif flag_type in ["end", "exception"]:
            self.window.dynamic_island.hide_progress(task_id, end_text=text, fill_bar=True)

    def handle_back_requested(self):
        if self.window.is_selection_active:
            self.cancel_model_loading()
            
    def cancel_model_loading(self):
        if self.model_worker and self.model_worker.isRunning():
            self.model_worker.is_cancelled = True
            self.handle_task_status("model_worker", "start", "Cancelling...")

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
                self.cancel_model_loading()
                return

            action = None
            target_model = None
            current_model = self.ollama.active_model

            if model_name == "Unload":
                if current_model:
                    action = 'unload'
                    target_model = current_model
            else:
                if current_model == model_name:
                    action = 'unload'
                    target_model = model_name
                elif current_model:
                    action = 'switch'
                    target_model = model_name
                else:
                    action = 'load'
                    target_model = model_name
            
            if not action:
                return

            self.window.home_view.update_model_status(target_model if target_model else "Unload", is_loading=True)
            self.window.selection_view.set_active_model(target_model if target_model else "Unload", is_loading=True)
            
            self.model_worker = ModelWorker(self.ollama, action, target_model, current_model)
            self.model_worker.status_flag.connect(self.handle_task_status)
            self.model_worker.finished.connect(self._on_model_op_finished)
            self.model_worker.start()
        else:
            if model_name == "Unload":
                self.mlx_active_model = None
            else:
                if getattr(self, 'mlx_active_model', None) == model_name: self.mlx_active_model = None
                else: self.mlx_active_model = model_name
            active = self.mlx_active_model
            
            self.window.selection_view.set_active_model(active if active else "Unload", is_loading=False)
            self.window.home_view.update_model_status(active, is_loading=False)
            self.check_ollama_status()

    def _on_model_op_finished(self):
        active = self.ollama.active_model
        self.window.selection_view.set_active_model(active if active else "Unload", is_loading=False)
        self.window.home_view.update_model_status(active, is_loading=False)
        self.check_ollama_status()

        if self.model_worker:
            self.model_worker.deleteLater()
            self.model_worker = None

    def slide_to_selection(self):
        if self.window.is_chat_active or self.window.is_selection_active: return
        
        if self.current_engine == "Ollama":
            if not self.ollama.is_running(): return
            is_loading = self.model_worker is not None and self.model_worker.isRunning()
            active_mod = self.model_worker.target_model if is_loading else self.ollama.active_model
            self.window.selection_view.update_model_list(self.ollama.get_local_models(), active_mod, "Ollama", is_loading=is_loading)
        else:
            mlx_models = self.get_local_mlx_models()
            self.window.selection_view.update_model_list(mlx_models, getattr(self, 'mlx_active_model', None), "MLX", is_loading=False)
        self.window.slide_to_selection()

    def get_local_mlx_models(self):
        models = []
        mlx_dir = "models/mlx"
        if os.path.exists(mlx_dir):
            for entry in os.listdir(mlx_dir):
                full_path = os.path.join(mlx_dir, entry)
                if os.path.isdir(full_path):
                    size = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, _, filenames in os.walk(full_path) for f in filenames if not os.path.islink(os.path.join(dirpath, f)))
                    models.append({"name": entry, "size": size})
        return models

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
        self.current_engine = "MLX" if self.current_engine == "Ollama" else "Ollama"
        style = "background-color: #FF9500;" if self.current_engine == "MLX" else "background-color: #007AFF;"
        hover = "background-color: #CC7700;" if self.current_engine == "MLX" else "background-color: #0051A8;"
        self.window.home_view.engine_toggle_btn.setText(self.current_engine)
        self.window.home_view.engine_toggle_btn.setStyleSheet(f"QPushButton {{ {style} color: white; border-radius: 16px; font-weight: bold; font-size: 13px; border: none; }} QPushButton:hover {{ {hover} }}")
        self.check_ollama_status()

    def handle_close_event(self, event):
        if self.model_worker and self.model_worker.isRunning():
            self.model_worker.is_cancelled = True
        self.update_server_ui("loading"); QApplication.processEvents()
        self.ollama.stop_server()
        for _ in range(15):
            if not self.ollama.is_running(): break
            QApplication.processEvents(); time.sleep(0.2)
        event.accept()