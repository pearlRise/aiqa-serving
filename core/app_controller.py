#============================================================
# - subject: app_controller.py
# - created: 2026-05-13
# - updated: 2026-05-14
# - summary: Orchestrates UI events and LLM manager logic.
# - caution: Ensure safe QThread and Ollama process exits.
#============================================================
import os
import atexit
import time
from PySide6.QtCore import QObject, QTimer, QEvent, QThread, Signal
from PySide6.QtWidgets import QApplication
from core.ollama.ollama_manager import ServerManager
from core.mlx.mlx_manager import MlxManager
from core.chat_controller import ChatController
from view.components.ui_main_window import MainWindow
from core.ollama.ollama_model_worker import OllamaModelWorker
from core.mlx.mlx_model_worker import MlxModelWorker

# UI와 비즈니스 로직(Ollama/MLX)을 중재하는 메인 컨트롤러
class AppController(QObject):
    # 앱 초기화 및 시그널 연결, 상태 모니터링 타이머 시작
    def __init__(self):
        super().__init__()
        self.window = MainWindow()
        self.ollama = ServerManager()
        self.mlx = MlxManager()
        atexit.register(self.ollama.stop_server)
        
        self.chat_logic = ChatController(self.ollama, self.mlx)
        self.model_worker = None
        
        self.is_server_starting = False
        self.is_server_stopping = False
        # 현재 활성화된 LLM 엔진 상태 (상태 추적 핵심 변수)
        self.current_engine = "MLX"
        # 현재 로드된 MLX 모델의 이름 (상태 추적 핵심 변수)
        self.mlx_active_model = None

        self._connect_signals()
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_ollama_status)
        self.status_timer.start(2000)

        self.window.chat_view.scroll.viewport().installEventFilter(self)
        self.window.selection_view.scroll.viewport().installEventFilter(self)
        self.window.template_view.scroll.viewport().installEventFilter(self)
        
        QTimer.singleShot(100, self.check_ollama_status)

    # UI 이벤트와 컨트롤러 내부 비즈니스 로직을 시그널로 연결
    def _connect_signals(self):
        self.window.chat_view.send_btn.clicked.connect(self.handle_send_message)
        self.window.chat_view.input_field.returnPressed.connect(self.handle_send_message)
        self.window.dynamic_island.left_btn.clicked.connect(self.handle_back_requested)
        
        self.chat_logic.thinking_started.connect(lambda: self.window.chat_view.add_chat_bubble("Thinking...", is_me=False, sender_name="Gemma"))
        self.chat_logic.chunk_delivered.connect(self.window.chat_view.update_last_bubble_stream)
        self.chat_logic.status_flag.connect(self.handle_task_status)
        
        self.window.home_view.serve_requested.connect(self.toggle_ollama_serve)
        self.window.home_view.chat_requested.connect(self.window.slide_to_chat)
        self.window.home_view.selection_requested.connect(self.slide_to_selection)
        self.window.home_view.template_requested.connect(self.window.slide_to_template)
        self.window.home_view.engine_toggle_btn.clicked.connect(self.toggle_engine)
        
        self.window.selection_view.model_selected.connect(self.handle_model_selection)
        
        self.window.close_requested = self.handle_close_event

    # 마우스 휠 이벤트를 가로채서 특정 조건 시 홈 화면으로 슬라이드 복귀
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if event.angleDelta().x() > 40 and abs(event.angleDelta().y()) < 20:
                if (obj == self.window.chat_view.scroll.viewport() and self.window.is_chat_active) or \
                   (obj == self.window.selection_view.scroll.viewport() and self.window.is_selection_active) or \
                   (obj == self.window.template_view.scroll.viewport() and self.window.is_template_active):
                    self.window.slide_to_home()
                    return True
        return super().eventFilter(obj, event)
        
    # 다이내믹 아일랜드에 백그라운드 작업 진행 상태를 표시하거나 숨김
    def handle_task_status(self, task_id, flag_type, text):
        if flag_type == "start":
            self.window.dynamic_island.show_progress(task_id, text)
        elif flag_type in ["end", "exception"]:
            self.window.dynamic_island.hide_progress(task_id, end_text=text, fill_bar=True)
            
        if task_id == "chat_worker":
            if flag_type == "start":
                self.window.chat_view.set_send_button_state("stop")
            elif flag_type in ["end", "exception"]:
                self.window.chat_view.set_send_button_state("send")

    # 다이내믹 아일랜드 뒤로가기 버튼 클릭 시 모델 로딩 취소 처리
    def handle_back_requested(self):
        if self.window.is_selection_active:
            self.cancel_model_loading()
            
    # 진행 중인 모델 로딩 워커(Ollama 또는 MLX) 작업을 강제로 취소
    def cancel_model_loading(self):
        if self.model_worker and self.model_worker.isRunning():
            self.model_worker.is_cancelled = True
            task_id = "mlx_model_worker" if isinstance(self.model_worker, MlxModelWorker) else "ollama_model_worker"
            self.handle_task_status(task_id, "start", "Cancelling...")

    # 채팅 입력 메시지를 뷰에 추가하고 LLM 엔진(워커)으로 텍스트 전달
    def handle_send_message(self):
        if self.chat_logic.worker and self.chat_logic.worker.isRunning():
            sender = self.sender()
            if sender == self.window.chat_view.send_btn:
                self.chat_logic.cancel_generation()
            return

        text = self.window.chat_view.input_field.toPlainText().strip()
        if text:
            self.window.chat_view.add_chat_bubble(text, is_me=True)
            self.chat_logic.process_message(text, self.current_engine)
            self.window.chat_view.input_field.clear()

    # 사용자가 선택한 모델에 따라 로드/언로드 워커를 조건부 실행
    def handle_model_selection(self, model_name):
        """
        POLICY - Asynchronous Model Transition
        1. Policy Description
            - Manages the switching of LLM models safely without blocking the UI.
            - Coordinates load, unload, and switch actions based on the current engine state.
        2. Policy Constraints
            - Existing QThread workers must be canceled before starting a new operation.
            - To prevent Out-Of-Memory (OOM) errors, the currently active model must always be unloaded before a new model is loaded.
        """
        if model_name in ["Create Model", "Model Configuration"]:
            return
            
        # 1. Ollama 엔진일 경우 작업 결정 및 워커 실행
        if self.current_engine == "Ollama":
            if self.model_worker and self.model_worker.isRunning():
                self.cancel_model_loading()
                return

            action = None
            target_model = None
            current_model = self.ollama.active_model

            # 1.1 선택된 모델과 현재 모델 비교하여 액션 할당
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
            
            self.model_worker = OllamaModelWorker(self.ollama, action, target_model, current_model)
            self.model_worker.status_flag.connect(self.handle_task_status)
            self.model_worker.finished.connect(self._on_model_op_finished)
            self.model_worker.start()
        else:
            # 2. MLX 엔진일 경우 작업 결정 및 워커 실행
            if self.model_worker and self.model_worker.isRunning():
                self.cancel_model_loading()
                return

            action = None
            target_model = None
            current_model = self.mlx_active_model

            # 2.1 선택된 모델과 현재 모델 비교하여 액션 할당
            if model_name == "Unload":
                if current_model:
                    action = 'unload'
            else:
                if current_model == model_name:
                    action = 'unload'
                else:
                    action = 'load'
                    target_model = model_name
            
            if not action:
                return

            self.window.home_view.update_model_status(target_model if target_model else "Unload", is_loading=True)
            self.window.selection_view.set_active_model(target_model if target_model else "Unload", is_loading=True)
            
            self.model_worker = MlxModelWorker(self.mlx, action, target_model)
            self.model_worker.status_flag.connect(self.handle_task_status)
            self.model_worker.finished.connect(self._on_mlx_model_op_finished)
            self.model_worker.start()

    # MLX 모델 로드/언로드 워커 종료 시 UI 상태 갱신 및 메모리 정리
    def _on_mlx_model_op_finished(self):
        active = self.mlx.active_model
        self.mlx_active_model = active
        self.window.selection_view.set_active_model(active if active else "Unload", is_loading=False)
        self.window.home_view.update_model_status(active, is_loading=False)
        self.check_ollama_status()

        if self.model_worker:
            self.model_worker.deleteLater()
            self.model_worker = None

    # Ollama 모델 로드/언로드 워커 종료 시 UI 상태 갱신 및 메모리 정리
    def _on_model_op_finished(self):
        active = self.ollama.active_model
        self.window.selection_view.set_active_model(active if active else "Unload", is_loading=False)
        self.window.home_view.update_model_status(active, is_loading=False)
        self.check_ollama_status()

        if self.model_worker:
            self.model_worker.deleteLater()
            self.model_worker = None

    # 모델 선택 화면으로 이동 전, 엔진별 로컬 모델 목록을 UI에 갱신
    def slide_to_selection(self):
        if self.window.is_chat_active or self.window.is_selection_active: return
        
        if self.current_engine == "Ollama":
            if not self.ollama.is_running(): return
            is_loading = self.model_worker is not None and self.model_worker.isRunning()
            active_mod = self.model_worker.target_model if is_loading else self.ollama.active_model
            self.window.selection_view.update_model_list(self.ollama.get_local_models(), active_mod, "Ollama", is_loading=is_loading)
        else:
            mlx_models = self.get_local_mlx_models()
            self.window.selection_view.update_model_list(mlx_models, self.mlx_active_model, "MLX", is_loading=False)
        self.window.slide_to_selection()

    # 로컬 디렉토리에서 폴더 용량을 계산해 MLX 모델 목록 객체로 반환
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

    # Ollama 서버 시작/중지 토글 로직
    def toggle_ollama_serve(self):
        """
        POLICY - Server Lifecycle Management
        1. Policy Description
            - Controls the starting and stopping of the local Ollama server process.
        2. Policy Constraints
            - The server process may not terminate immediately upon a stop request.
            - Must use `QApplication.processEvents()` while polling (up to 3 seconds) to prevent main thread UI freezing during termination.
        """
        if self.current_engine == "Ollama":
            if not self.ollama.is_running():
                # 1. 서버 실행: 프로세스 생성 및 로딩 상태 UI 반영
                self.is_server_starting, self.is_server_stopping = True, False
                self.update_server_ui("loading")
                QApplication.processEvents()
                self.ollama.start_server()
            else:
                # 2. 서버 중지: 프로세스 종료 및 UI 갱신 (대기 포함)
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
            if not self.mlx_active_model:
                return
            self.handle_model_selection("Unload")
            self.check_ollama_status()

    # 주기적으로 엔진 상태(Ollama 프로세스 등)를 확인하여 UI 반영
    def check_ollama_status(self):
        if self.current_engine == "MLX":
            if self.model_worker and self.model_worker.isRunning() and isinstance(self.model_worker, MlxModelWorker):
                self.update_server_ui("loading")
            else:
                self.update_server_ui("running" if self.mlx_active_model else "stopped")
            self.window.home_view.update_model_status(self.mlx_active_model)
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

    # 현재 엔진 상태에 맞춰 홈 화면 대시보드의 상태 UI 갱신
    def update_server_ui(self, status):
        has_model = (self.ollama.active_model is not None) if self.current_engine == "Ollama" else (self.mlx_active_model is not None)
        self.window.home_view.update_dashboard_state(self.current_engine, status, has_model)

    # Ollama와 MLX 엔진 간 전환 토글 및 스타일 업데이트
    def toggle_engine(self):
        self.current_engine = "MLX" if self.current_engine == "Ollama" else "Ollama"
        style = "background-color: #FF9500;" if self.current_engine == "MLX" else "background-color: #007AFF;"
        hover = "background-color: #CC7700;" if self.current_engine == "MLX" else "background-color: #0051A8;"
        self.window.home_view.engine_toggle_btn.setText(self.current_engine)
        self.window.home_view.engine_toggle_btn.setStyleSheet(f"QPushButton {{ {style} color: white; border-radius: 16px; font-weight: bold; font-size: 13px; border: none; }} QPushButton:hover {{ {hover} }}")
        self.check_ollama_status()

    # 앱 닫기 이벤트 시 워커 취소 및 Ollama 서버 안전 종료 보장
    def handle_close_event(self, event):
        if self.model_worker and self.model_worker.isRunning():
            self.model_worker.is_cancelled = True
        self.update_server_ui("loading"); QApplication.processEvents()
        self.ollama.stop_server()
        for _ in range(15):
            if not self.ollama.is_running(): break
            QApplication.processEvents(); time.sleep(0.2)
        event.accept()