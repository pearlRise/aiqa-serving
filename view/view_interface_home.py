from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QGraphicsOpacityEffect, QPushButton)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, Signal
from PySide6.QtGui import QFont
from view.view_components import SmoothScrollArea, GlassFrame, IndicatorInfoCell, MenuListItem

# 4.1 메인 홈 인터페이스 레이아웃 관리
class HomeView(QWidget):
    chat_requested = Signal()
    serve_requested = Signal()
    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.container.setObjectName("MainBody")
        
        # 자신(self)의 바탕 레이아웃을 만들고 컨테이너를 꽉 채워 넣음
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.addWidget(self.container)
        
        self.container.setStyleSheet("""
            #MainBody { 
                background-color: #000000; 
                border: 1px solid #222; 
                border-radius: 48px; 
            }
        """)        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 21) 
        self.main_layout.setSpacing(0)

        self.top_bar = QFrame(self.container)
        self.top_bar.setFixedHeight(48)
        self.top_bar.setStyleSheet("QFrame { background-color: #212121; border: none; border-top-left-radius: 47px; border-top-right-radius: 47px; }")
        self.main_layout.addWidget(self.top_bar)

        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: transparent; width: 8px; 
                margin: 24px 0px 24px 0px; 
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(0, 0, 0, 0.3); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px; background: none;
            }
        """)

        self.scroll_effect = QGraphicsOpacityEffect(self.scroll.verticalScrollBar())
        self.scroll.verticalScrollBar().setGraphicsEffect(self.scroll_effect)
        self.scroll_effect.setOpacity(0.0)
        
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.hide_scrollbar)
        
        self.scrollbar_anim = QPropertyAnimation(self.scroll_effect, b"opacity")
        self.scrollbar_anim.setDuration(300)
        self.scrollbar_anim.setStartValue(1.0)
        self.scrollbar_anim.setEndValue(0.0)
        
        self.scroll.verticalScrollBar().valueChanged.connect(self.show_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.show_scrollbar)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 30, 8, 30)
        self.scroll_layout.setSpacing(20) 
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # 4.2 사용자 환영 문구 및 배너 영역
        self.banner = GlassFrame(radius=16)
        self.banner.setFixedHeight(80)
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(20, 0, 20, 0)
        
        banner_icon = QLabel("🌟")
        banner_icon.setStyleSheet("background: transparent; border: none; font-size: 28px;")
        
        banner_text_layout = QVBoxLayout()
        banner_text_layout.setAlignment(Qt.AlignVCenter)
        banner_title = QLabel("Welcome, Jihwan!")
        banner_title.setStyleSheet("color: #1A1A1A; font-weight: bold; font-size: 16px; background: transparent; border: none;")
        banner_sub = QLabel("Ollama Control Center")
        banner_sub.setStyleSheet("color: #4A5568; font-size: 12px; background: transparent; border: none;")
        banner_text_layout.addWidget(banner_title)
        banner_text_layout.addWidget(banner_sub)
        
        banner_layout.addWidget(banner_icon)
        banner_layout.addSpacing(10)
        banner_layout.addLayout(banner_text_layout)
        banner_layout.addStretch()
        
        self.scroll_layout.addWidget(self.banner)

        # 4.3 서버 상태 및 시스템 정보 대시보드
        self.indicator_dashboard = GlassFrame(radius=20)
        self.indicator_dashboard.setMinimumHeight(220)

        self.dashboard_layout = QGridLayout(self.indicator_dashboard)
        self.dashboard_layout.setContentsMargins(15, 15, 15, 15)
        self.dashboard_layout.setSpacing(0) 

        indicators_data = [
            ("⌛️", "Server", "Loading"),
            ("⚡", "Memory", "Loading"),
            ("🧠", "Model", "Loading"),
            ("🌡️", "System", "Loading")
        ]
        
        for idx, (icon, title, value) in enumerate(indicators_data):
            row, col = idx // 2, idx % 2
            
            cell = IndicatorInfoCell()
            cell.setFixedHeight(95)
            
            line_color = "rgba(0, 0, 0, 0.12)"
            border_style = "border: none; border-radius: 0px;"
            if col == 0: 
                border_style += f"border-right: 1px solid {line_color};"
            if row == 0: 
                border_style += f"border-bottom: 1px solid {line_color};"
            
            cell.setStyleSheet(f"IndicatorInfoCell {{ background: transparent; {border_style} }}")
            
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 10, 0, 10) 
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setSpacing(4)
            
            icon_label = QLabel(icon)
            icon_font = QFont("Apple Color Emoji", 19)
            icon_label.setFont(icon_font)
            icon_label.setFixedHeight(28) 
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("background: transparent; border: none;")
            
            val_label = QLabel(value)
            val_label.setStyleSheet("color: #1A1A1A; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            val_label.setAlignment(Qt.AlignCenter)
            
            if title == "Server":
                self.server_icon_label = icon_label
                self.server_status_label = val_label
            
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #666666; font-size: 11px; background: transparent; border: none;")
            title_label.setAlignment(Qt.AlignCenter)
            
            cell_layout.addWidget(icon_label)
            cell_layout.addWidget(val_label)
            cell_layout.addWidget(title_label)
            
            self.dashboard_layout.addWidget(cell, row, col)
        
        self.scroll_layout.addWidget(self.indicator_dashboard)
        
        # 4.4 주요 기능 접근 메뉴 리스트
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setSpacing(12)
        
        menus = [
            ("🚀", "Ollama Serve", "백그라운드 서버 구동 및 중지"),
            ("💬", "Ollama Chat", "현재 활성화된 모델과 대화하기"),
            ("🌐", "Choose Model", "생성된 모델을 활성화하기"),
            ("🔨", "Create Model", "새로운 커스텀 모델 빌드"),
            ("📝", "Edit Prompt", "모델의 시스템 프롬프트 편집하기"),
            ("⚙️", "Settings", "앱 기본 테마 및 경로 설정"),
        ]
        
        for icon, title, sub in menus:
            item = MenuListItem(icon, title, sub)

            if title == "Ollama Serve":
                item.clicked.connect(lambda _: self.serve_requested.emit())

            if title == "Ollama Chat":
                item.clicked.connect(lambda _: self.chat_requested.emit())

            self.menu_layout.addWidget(item)
            
        self.scroll_layout.addLayout(self.menu_layout)

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

        # 4.5 다이내믹 아일랜드 UI 구성 (각 화면마다 개별 배치)
        self.island = QFrame(self.container)
        self.island.setFixedSize(120, 26)
        self.island.setStyleSheet("background-color: black; border-radius: 13px;")
        self.island.raise_()

        self.exclaim_btn = QPushButton("!", self.container)
        self.exclaim_btn.setFixedSize(26, 26)
        self.exclaim_btn.setStyleSheet("""
            QPushButton { background-color: #007AFF; font-size: 15px; border: none; border-radius: 13px; color: white; padding: 0px; }
            QPushButton:pressed { background-color: #0051A8; }
        """)
        
        self.question_btn = QPushButton("?", self.container)
        self.question_btn.setFixedSize(26, 26)
        self.question_btn.setStyleSheet("""
            QPushButton { background-color: #007AFF; font-size: 15px; border: none; border-radius: 13px; color: white; padding-bottom: 3px; }
            QPushButton:pressed { background-color: #0051A8; }
        """)

        self.exclaim_btn.raise_()
        self.question_btn.raise_()

    # 4.6 창 크기 변경에 따른 아일랜드 위치 재조정
    def resizeEvent(self, event):
        super().resizeEvent(event)
        island_x = (self.width() - 120) // 2
        if hasattr(self, 'island'):
            self.island.move(island_x, 10)
        if hasattr(self, 'exclaim_btn'):
            self.exclaim_btn.move(island_x - 31, 10)
        if hasattr(self, 'question_btn'):
            self.question_btn.move(island_x + 125, 10)

    def show_scrollbar(self, *args):
        if self.scrollbar_anim.state() == QPropertyAnimation.Running:
            self.scrollbar_anim.stop()
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim.start()

    # 4.5 서버 상태에 따른 대시보드 UI 실시간 업데이트
    def update_server_status(self, status):
        if not hasattr(self, 'server_status_label'): 
            return
            
        if status == "running":
            self.server_status_label.setText("Running")
            self.server_status_label.setStyleSheet("color: #1A1A1A; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🟢")
        elif status == "stopped":
            self.server_status_label.setText("Stopped")
            self.server_status_label.setStyleSheet("color: #FF3B30; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🔴")
        elif status == "loading":
            self.server_status_label.setText("Loading")
            self.server_status_label.setStyleSheet("color: #E6A23C; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("⌛️")
