from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint
from view.window.home_view import HomeView
from view.window.chat_view import ChatView
from view.window.selection_view import SelectionView
from view.window.template_view import TemplateView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(305, 655)
        self.resize(305, 655)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QWidget(self)
        self.setCentralWidget(self.container)

        self.home_view = HomeView()
        self.home_view.setParent(self.container)
        self.chat_view = ChatView()
        self.chat_view.setParent(self.container)
        self.selection_view = SelectionView()
        self.selection_view.setParent(self.container)
        self.template_view = TemplateView()
        self.template_view.setParent(self.container)

        self.old_pos = None
        self.logical_pos = None
        self.is_chat_active = False
        self.is_selection_active = False
        self.is_template_active = False
        self.resizing = False
        self.resize_margin = 10
        self.anim_group = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self.container.resize(w, h)
        self.home_view.resize(w, h)
        self.chat_view.resize(w, h)
        self.selection_view.resize(w, h)
        self.template_view.resize(w, h)

        if self.is_chat_active:
            self.home_view.move(-w, 0); self.chat_view.move(0, 0); self.selection_view.move(w, 0); self.template_view.move(w, 0)
        elif self.is_selection_active:
            self.home_view.move(-w, 0); self.selection_view.move(0, 0); self.chat_view.move(w, 0); self.template_view.move(w, 0)
        elif self.is_template_active:
            self.home_view.move(-w, 0); self.template_view.move(0, 0); self.chat_view.move(w, 0); self.selection_view.move(w, 0)
        else:
            self.home_view.move(0, 0); self.chat_view.move(w, 0); self.selection_view.move(w, 0); self.template_view.move(w, 0)

    def slide_to_chat(self):
        if self.is_chat_active: return
        self.is_chat_active = True
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        
        anim_home = QPropertyAnimation(self.home_view, b"pos"); anim_home.setEndValue(QPoint(-w, 0)); anim_home.setEasingCurve(QEasingCurve.InOutQuart); anim_home.setDuration(450)
        anim_chat = QPropertyAnimation(self.chat_view, b"pos"); anim_chat.setEndValue(QPoint(0, 0)); anim_chat.setEasingCurve(QEasingCurve.InOutQuart); anim_chat.setDuration(450)
        self.anim_group.addAnimation(anim_home); self.anim_group.addAnimation(anim_chat); self.anim_group.start()

    def slide_to_home(self):
        if not (self.is_chat_active or self.is_selection_active or self.is_template_active): return
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        anim_home = QPropertyAnimation(self.home_view, b"pos"); anim_home.setEndValue(QPoint(0, 0)); anim_home.setEasingCurve(QEasingCurve.InOutQuart); anim_home.setDuration(450)
        self.anim_group.addAnimation(anim_home)

        if self.is_chat_active:
            self.is_chat_active = False
            anim_chat = QPropertyAnimation(self.chat_view, b"pos"); anim_chat.setEndValue(QPoint(w, 0)); anim_chat.setEasingCurve(QEasingCurve.InOutQuart); anim_chat.setDuration(450); self.anim_group.addAnimation(anim_chat)
        if self.is_selection_active:
            self.is_selection_active = False
            anim_sel = QPropertyAnimation(self.selection_view, b"pos"); anim_sel.setEndValue(QPoint(w, 0)); anim_sel.setEasingCurve(QEasingCurve.InOutQuart); anim_sel.setDuration(450); self.anim_group.addAnimation(anim_sel)
        if self.is_template_active:
            self.is_template_active = False
            anim_tpl = QPropertyAnimation(self.template_view, b"pos"); anim_tpl.setEndValue(QPoint(w, 0)); anim_tpl.setEasingCurve(QEasingCurve.InOutQuart); anim_tpl.setDuration(450); self.anim_group.addAnimation(anim_tpl)
        self.anim_group.start()

    def slide_to_selection(self):
        self.is_selection_active = True
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        anim_home = QPropertyAnimation(self.home_view, b"pos"); anim_home.setEndValue(QPoint(-w, 0)); anim_home.setEasingCurve(QEasingCurve.InOutQuart); anim_home.setDuration(450)
        anim_sel = QPropertyAnimation(self.selection_view, b"pos"); anim_sel.setEndValue(QPoint(0, 0)); anim_sel.setEasingCurve(QEasingCurve.InOutQuart); anim_sel.setDuration(450)
        self.anim_group.addAnimation(anim_home); self.anim_group.addAnimation(anim_sel); self.anim_group.start()

    def slide_to_template(self):
        self.is_template_active = True
        self.anim_group = QParallelAnimationGroup()
        w = self.width()
        anim_home = QPropertyAnimation(self.home_view, b"pos"); anim_home.setEndValue(QPoint(-w, 0)); anim_home.setEasingCurve(QEasingCurve.InOutQuart); anim_home.setDuration(450)
        anim_tpl = QPropertyAnimation(self.template_view, b"pos"); anim_tpl.setEndValue(QPoint(0, 0)); anim_tpl.setEasingCurve(QEasingCurve.InOutQuart); anim_tpl.setDuration(450)
        self.anim_group.addAnimation(anim_home); self.anim_group.addAnimation(anim_tpl); self.anim_group.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if pos.x() > self.width() - self.resize_margin or pos.y() > self.height() - self.resize_margin: self.resizing = True
            else: self.old_pos = event.globalPosition().toPoint()
            self.logical_pos = self.pos()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        is_right = pos.x() > self.width() - self.resize_margin
        is_bottom = pos.y() > self.height() - self.resize_margin
        if is_right and is_bottom: self.setCursor(Qt.SizeFDiagCursor)
        elif is_right: self.setCursor(Qt.SizeHorCursor)
        elif is_bottom: self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)
            
        if self.resizing:
            self.resize(max(self.minimumWidth(), pos.x()), max(self.minimumHeight(), pos.y()))
        elif self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.logical_pos += delta
            new_pos = QPoint(self.logical_pos)
            screen_rect = self.screen().availableGeometry()
            snap_dist = 20
            if abs(new_pos.x() - screen_rect.left()) < snap_dist: new_pos.setX(screen_rect.left())
            elif abs(new_pos.x() + self.width() - screen_rect.right()) < snap_dist: new_pos.setX(screen_rect.right() - self.width() + 1)
            if abs(new_pos.y() - screen_rect.top()) < snap_dist: new_pos.setY(screen_rect.top())
            elif abs(new_pos.y() + self.height() - screen_rect.bottom()) < snap_dist: new_pos.setY(screen_rect.bottom() - self.height() + 1)
            self.move(new_pos); self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.resizing = False; self.old_pos = None; self.logical_pos = None

    def closeEvent(self, event):
        if hasattr(self, 'close_requested'): self.close_requested(event)
        else: event.accept()