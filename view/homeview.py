import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QCursor

# 1. 커스텀 부드러운 스크롤 영역 (유지)
class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_val = 0
        self.anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setDuration(400)

    def wheelEvent(self, event):
        if not event.pixelDelta().isNull():
            super().wheelEvent(event)
            self.target_val = self.verticalScrollBar().value()
            return
        
        bar = self.verticalScrollBar()
        if self.anim.state() != QPropertyAnimation.Running:
            self.target_val = bar.value()
            
        step = event.angleDelta().y()
        self.target_val = max(bar.minimum(), min(bar.maximum(), self.target_val - step))
        
        self.anim.setEndValue(self.target_val)
        self.anim.start()

# 2. 글래스모피즘 스타일 프레임들
# 2.1. [수정] 통합 유리판 대시보드 및 배너/메뉴용
class GlassFrame(QFrame):
    def __init__(self, radius=16, parent=None):
        super().__init__(parent)
        # QFrame 대신 GlassFrame으로 셀렉터 변경
        self.setStyleSheet(f"""
            GlassFrame {{
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: {radius}px;
            }}
        """)

# 2.2. [신규] 통합 대시보드 내부의 개별 정보 셀 (배경/테두리 없음, 투명함)
class IndicatorInfoCell(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 배경과 테두리를 명확히 초기화
        self.setStyleSheet("IndicatorInfoCell { background: transparent; border: none; border-radius: 0px; }")

# 3. 메뉴 리스트의 개별 아이템 (유지 - 클릭 유도를 위해 입체감 유지)
class MenuListItem(GlassFrame):
    clicked = Signal(str)

    def __init__(self, icon, title, subtitle):
        super().__init__(radius=16)
        self.setFixedHeight(72)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        self.icon_label = QLabel(icon)
        self.icon_label.setFont(QFont("Apple Color Emoji", 24))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #1A1A1A; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("color: #4A5568; font-size: 12px; background: transparent; border: none;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.9);
                border-radius: 16px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 16px;
            }
        """)
        super().leaveEvent(event)
    
# ★ 마우스 클릭 이벤트 오버라이드
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title_label.text()) # 클릭된 메뉴의 타이틀을 밖으로 쏨
        super().mousePressEvent(event)

# 4. 홈 화면 메인 윈도우
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
                background-color: #BACEE0; 
                border: 1px solid #99AABF; 
                border-radius: 48px; 
            }
        """)        
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 21) 
        self.main_layout.setSpacing(0)
        self.main_layout.addSpacing(21) 

        # 4.1. 커스텀 스크롤 영역
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
        self.scrollbar_anim = None
        
        self.scroll.verticalScrollBar().valueChanged.connect(self.show_scrollbar)
        self.scroll.verticalScrollBar().rangeChanged.connect(self.show_scrollbar)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 30, 8, 30)
        self.scroll_layout.setSpacing(20) 
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # ==========================================
        # 1행: 최상단 배너
        # ==========================================
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

        # ==========================================
        # 2행: 통합된 유리 대시보드 (수정본)
        # ==========================================
        self.indicator_dashboard = GlassFrame(radius=20)
        self.indicator_dashboard.setMinimumHeight(220)

        self.dashboard_layout = QGridLayout(self.indicator_dashboard)
        self.dashboard_layout.setContentsMargins(15, 15, 15, 15)
        self.dashboard_layout.setSpacing(0) 

        indicators_data = [
            ("🟢", "Server", "Running"),
            ("⚡", "Memory", "14.2 GB"),
            ("🧠", "Active", "26B MoE"),
            ("🌡️", "System", "M-Chip 45°C")
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
            # 상하단 여백을 조금 더 주어서 수직 중앙 밸런스를 맞춤
            cell_layout.setContentsMargins(0, 10, 0, 10) 
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setSpacing(4)
            
            # 1. 이모지 라벨
            icon_label = QLabel(icon)
            icon_font = QFont("Apple Color Emoji", 19)
            icon_label.setFont(icon_font)
            icon_label.setFixedHeight(28) 
            icon_label.setAlignment(Qt.AlignCenter) # 중앙 정렬 추가
            icon_label.setStyleSheet("background: transparent; border: none;")
            
            # 2. 수치 데이터 (예: Running, 14.2 GB)
            val_label = QLabel(value)
            val_label.setStyleSheet("color: #1A1A1A; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            val_label.setAlignment(Qt.AlignCenter) # 중앙 정렬 추가
            
            # ★ [신규 추가] 타이틀이 "Server"일 경우, 나중에 상태를 업데이트하기 위해 변수에 저장
            if title == "Server":
                self.server_icon_label = icon_label
                self.server_status_label = val_label
            
            # 3. 설명 텍스트 (예: Server, Memory)
            title_label = QLabel(title)
            title_label.setStyleSheet("color: #666666; font-size: 11px; background: transparent; border: none;")
            title_label.setAlignment(Qt.AlignCenter) # 중앙 정렬 추가
            
            cell_layout.addWidget(icon_label)
            cell_layout.addWidget(val_label)
            cell_layout.addWidget(title_label)
            
            self.dashboard_layout.addWidget(cell, row, col)
        
        self.scroll_layout.addWidget(self.indicator_dashboard)
        
        # ==========================================
        # 3행~: 메뉴 리스트 영역
        # ==========================================
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

    def show_scrollbar(self, *args):
        self.scroll_effect.setOpacity(1.0)
        self.scroll_timer.start(1500)

    def hide_scrollbar(self):
        self.scrollbar_anim = QPropertyAnimation(self.scroll_effect, b"opacity")
        self.scrollbar_anim.setDuration(300)
        self.scrollbar_anim.setStartValue(1.0)
        self.scrollbar_anim.setEndValue(0.0)
        self.scrollbar_anim.start()

    # [신규] 서버 상태에 따라 대시보드 UI를 갱신하는 함수
    def update_server_status(self, is_active):
        # UI 객체가 아직 생성되지 않았을 때를 대비한 안전 장치
        if not hasattr(self, 'server_status_label'): 
            return
            
        if is_active:
            self.server_status_label.setText("Running")
            self.server_status_label.setStyleSheet("color: #1A1A1A; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🟢")
        else:
            self.server_status_label.setText("Stopped")
            # 꺼져있을 때는 직관적으로 알 수 있게 빨간색 텍스트로 변경
            self.server_status_label.setStyleSheet("color: #FF3B30; font-weight: bold; font-size: 14px; background: transparent; border: none;")
            self.server_icon_label.setText("🔴")
