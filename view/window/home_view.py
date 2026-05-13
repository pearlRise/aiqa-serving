from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QFont
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_glass_frame import GlassFrame
from view.components.ui_round_button import SmoothRoundButton
from view.components.ui_indicator import IndicatorInfoCell
from view.components.ui_menu_button import MenuButton
from view.configuration.app_texts import BANNER_GREETING, BANNER_SUBTITLE, ENGINE_TITLE, ENGINE_SUBTITLE

MENUS = [
    ("💬", "LLM Chat", "현재 활성화된 모델과 대화하기", "chat"),
    ("📝", "Edit Prompt", "시스템 프롬프트 편집하기", None),
    ("⚙️", "Settings", "앱 기본 테마 및 경로 설정", None),
    ("🧩", "Template View", "더미 템플릿 화면으로 이동", "template"),
]

class HomeView(QWidget):
    chat_requested = Signal()
    serve_requested = Signal()
    selection_requested = Signal()
    template_requested = Signal()
    def __init__(self):
        super().__init__()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 48, 0, 21) 
        self.main_layout.setSpacing(0)

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 12, 8, 30)
        self.scroll_layout.setSpacing(12) 
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.banner = GlassFrame(radius=16)
        self.banner.setFixedHeight(128)
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(20, 0, 20, 0)
        
        banner_icon = QLabel("🌟")
        banner_icon.setStyleSheet("background: transparent; border: none; font-size: 28px;")
        
        banner_text_layout = QVBoxLayout()
        banner_text_layout.setAlignment(Qt.AlignVCenter)
        banner_title = QLabel(BANNER_GREETING)
        banner_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        banner_sub = QLabel(BANNER_SUBTITLE)
        banner_sub.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none;")
        banner_text_layout.addWidget(banner_title)
        banner_text_layout.addWidget(banner_sub)
        
        banner_layout.addWidget(banner_icon)
        banner_layout.addSpacing(10)
        banner_layout.addLayout(banner_text_layout)
        banner_layout.addStretch()
        
        self.scroll_layout.addWidget(self.banner)

        self.indicator_dashboard = GlassFrame(radius=16)
        self.indicator_dashboard.setFixedHeight(64)

        self.dashboard_layout = QHBoxLayout(self.indicator_dashboard)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_layout.setSpacing(0) 

        indicators_data = [
            ("⌛️", "Server", "Loading"),
            ("🤖", "Model", "Loading")
        ]
        
        for idx, (icon, title, value) in enumerate(indicators_data):
            cell = IndicatorInfoCell()
            
            line_color = "rgba(255, 255, 255, 0.1)"
            border_style = "border: none; border-radius: 0px;"
            if idx == 0: 
                border_style += f"border-right: 1px solid {line_color};"
            
            cell.setStyleSheet(f"IndicatorInfoCell {{ background: transparent; {border_style} }}")
            
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0) 
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setSpacing(8)
            
            icon_label = QLabel(icon)
            icon_font = QFont("Apple Color Emoji", 19)
            icon_label.setFont(icon_font)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("background: transparent; border: none;")
            
            text_layout = QVBoxLayout()
            text_layout.setAlignment(Qt.AlignCenter)
            text_layout.setSpacing(2)
            
            val_label = QLabel(value)
            val_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            val_label.setAlignment(Qt.AlignLeft)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #8E8E93; font-size: 11px; background: transparent; border: none;")
            title_label.setAlignment(Qt.AlignLeft)
            
            if title == "Server":
                self.server_cell = cell
                self.server_icon_label = icon_label
                self.server_status_label = val_label
            elif title == "Model":
                self.model_cell = cell
                self.model_icon_label = icon_label
                self.model_status_label = val_label
            
            text_layout.addWidget(val_label)
            text_layout.addWidget(title_label)
            
            cell_layout.addWidget(icon_label)
            cell_layout.addLayout(text_layout)
            
            self.dashboard_layout.addWidget(cell)
        
        self.scroll_layout.addWidget(self.indicator_dashboard)

        self.server_cell.clicked.connect(lambda: self.serve_requested.emit())
        self.model_cell.clicked.connect(lambda: self.selection_requested.emit())
        
        self.server_cell_effect = QGraphicsOpacityEffect()
        self.server_cell.setGraphicsEffect(self.server_cell_effect)
        
        self.model_cell_effect = QGraphicsOpacityEffect()
        self.model_cell.setGraphicsEffect(self.model_cell_effect)

        self.engine_frame = GlassFrame(radius=16)
        self.engine_frame.setFixedHeight(64)
        engine_layout = QHBoxLayout(self.engine_frame)
        engine_layout.setContentsMargins(20, 0, 20, 0)
        
        engine_title_layout = QVBoxLayout()
        engine_title_layout.setAlignment(Qt.AlignVCenter)
        self.engine_title = QLabel(ENGINE_TITLE)
        self.engine_title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 15px; background: transparent; border: none;")
        self.engine_sub = QLabel(ENGINE_SUBTITLE)
        self.engine_sub.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none;")
        engine_title_layout.addWidget(self.engine_title)
        engine_title_layout.addWidget(self.engine_sub)
        
        self.engine_toggle_btn = QPushButton("MLX")
        self.engine_toggle_btn.setFixedSize(80, 32)
        self.engine_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.engine_toggle_btn.setStyleSheet("""
            QPushButton { background-color: #FF9500; color: white; border-radius: 16px; font-weight: bold; font-size: 13px; border: none; }
            QPushButton:hover { background-color: #CC7700; }
        """)
        
        engine_layout.addLayout(engine_title_layout)
        engine_layout.addStretch()
        engine_layout.addWidget(self.engine_toggle_btn)
        
        self.scroll_layout.addWidget(self.engine_frame)
        
        self._build_menus()

        self.current_server_status = "stopped"
        self.update_dashboard_state("MLX", "stopped", False)

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

    def _build_menus(self):
        for icon, title, sub, action in MENUS:
            item = MenuButton(icon, title, sub)
            if action == "chat":
                item.clicked.connect(lambda _: self.chat_requested.emit())
            elif action == "template":
                item.clicked.connect(lambda _: self.template_requested.emit())
            self.scroll_layout.addWidget(item)

    def update_dashboard_state(self, engine_name, status, has_model):
        self.current_server_status = status
        if not hasattr(self, 'server_status_label'): 
            return
            
        if status == "running":
            self.server_status_label.setText("Running")
            self.server_status_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🟢")
        elif status == "stopped":
            self.server_status_label.setText("Stopped")
            self.server_status_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🔴")
        elif status == "loading":
            self.server_status_label.setText("Loading")
            self.server_status_label.setStyleSheet("color: #E6A23C; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("⌛️")
            
        if engine_name == "Ollama":
            is_running = (status == "running")
            if hasattr(self, 'model_cell'):
                self.model_cell.setEnabled(is_running)
                self.model_cell_effect.setOpacity(1.0 if is_running else 0.4)
            if hasattr(self, 'server_cell'):
                self.server_cell.setEnabled(True)
                self.server_cell_effect.setOpacity(1.0)
        else:
            if hasattr(self, 'model_cell'):
                self.model_cell.setEnabled(True)
                self.model_cell_effect.setOpacity(1.0)
            if hasattr(self, 'server_cell'):
                self.server_cell.setEnabled(has_model)
                self.server_cell_effect.setOpacity(1.0 if has_model else 0.4)

    def update_model_status(self, model_name):
        if not hasattr(self, 'model_status_label'): return
        if model_name:
            self.model_status_label.setText(model_name)
            self.model_status_label.setStyleSheet("color: #E6A23C; font-weight: bold; font-size: 14px; background: transparent; border: none;")
        else:
            self.model_status_label.setText("Unselected")
            self.model_status_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px; background: transparent; border: none;")
