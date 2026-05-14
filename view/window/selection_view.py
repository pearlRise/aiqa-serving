#============================================================
# - subject: selection_view.py
# - created: 2026-05-11
# - updated: 2026-05-14
# - summary: View for selecting and managing MLX/Ollama models.
# - caution: None.
#============================================================
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel
)
from PySide6.QtCore import Qt, Signal
from view.components.ui_scroll_area import SmoothScrollArea
from view.components.ui_menu_button import MenuButton
from data.view.app_texts import NO_MODELS_MSG, UNKNOWN_MODEL_NAME, UNKNOWN_MODEL_SIZE

class SelectionView(QWidget):
    model_selected = Signal(str)

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
        self.scroll_layout.setContentsMargins(16, 24, 8, 30)
        self.scroll_layout.setSpacing(12) 
        self.scroll_layout.setAlignment(Qt.AlignTop)
        

        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll, 1)

    def update_model_list(self, models, active_model=None, engine="Ollama", is_loading=False):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        none_item = MenuButton("🚫", "Unload", "Unload active model")
        if not active_model or active_model == "Unload":
            none_item.set_active(True, is_loading)
        none_item.clicked.connect(lambda checked=False: self.model_selected.emit("Unload"))
        self.scroll_layout.addWidget(none_item)

        if engine == "Ollama":
            create_item = MenuButton("➕", "Create Model", "Build a new modelfile")
            create_item.clicked.connect(lambda checked=False: self.model_selected.emit("Create Model"))
            self.scroll_layout.addWidget(create_item)
        elif engine == "MLX":
            config_item = MenuButton("⚙️", "Model Configuration", "Configure model parameters")
            config_item.clicked.connect(lambda checked=False: self.model_selected.emit("Model Configuration"))
            self.scroll_layout.addWidget(config_item)

        if not models:
            info_label = QLabel(NO_MODELS_MSG)
            info_label.setStyleSheet("color: #8E8E93; font-size: 12px; background: transparent; border: none; padding: 20px;")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setWordWrap(True)
            self.scroll_layout.addWidget(info_label)
        else:
            def sort_key(m):
                size_bytes = m.get('size', 0)
                size_gb = round(size_bytes / (1024**3), 2)
                return (-size_gb, m.get('name', '').lower())
                
            for model in sorted(models, key=sort_key):
                model_name = model.get('name', UNKNOWN_MODEL_NAME)
                model_size = model.get('size', 0)

                if model_size > 0:
                    size_gb = round(model_size / (1024**3), 2)
                    subtitle = f"Size: {size_gb} GB"
                else:
                    subtitle = UNKNOWN_MODEL_SIZE

                item = MenuButton("🤖", model_name, subtitle)
                if active_model == model_name:
                    item.set_active(True, is_loading)
                item.clicked.connect(lambda checked=False, m=model_name: self.model_selected.emit(m))
                self.scroll_layout.addWidget(item)

    def set_active_model(self, active_model_name, is_loading=False):
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, MenuButton):
                if widget.title_label.text() in ["Create Model", "Model Configuration"]:
                    continue
                is_active = (widget.title_label.text() == active_model_name)
                widget.set_active(is_active, is_loading)