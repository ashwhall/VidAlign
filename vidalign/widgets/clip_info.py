from PySide6 import QtCore
from PySide6.QtWidgets import (QErrorMessage, QFrame, QHBoxLayout, QLabel,
                               QSizePolicy, QStyle, QVBoxLayout)

from vidalign.constants import COLOURS
from vidalign.widgets.modules import StyledButton
from vidalign.widgets.text_field_dialog import TextFieldDialog


def err_dlg(msg):
    error_dialog = QErrorMessage()
    error_dialog.showMessage(msg)
    error_dialog.exec()
    return


class ClipInfo(QFrame):
    new_clip = QtCore.Signal()
    rename_clip = QtCore.Signal()
    delete_clip = QtCore.Signal()

    set_clip_start = QtCore.Signal()
    set_clip_end = QtCore.Signal()
    set_clip_duration = QtCore.Signal(int)

    jump_clip_start = QtCore.Signal()
    jump_clip_end = QtCore.Signal()

    def __init__(self, clip):
        super().__init__()

        self.clip = clip

        self.layout = QHBoxLayout()

        self.layout.addLayout(self.make_left_layout())
        self.layout.addLayout(self.make_middle_layout())
        self.layout.addLayout(self.make_righter_layout())
        self.layout.addLayout(self.make_right_layout())

        self.update_ui()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(90)

        self.setObjectName('clipInfo')
        self.setStyleSheet(f"""
            QFrame#clipInfo {{
                border: 2px solid {COLOURS['neutral']};
                border-radius: 5px;
            }}
        """)

        self.setLayout(self.layout)

    def prompt_clip_duration(self):
        if self.clip.start_frame is None:
            return err_dlg('Cannot set duration without a start frame.')

        # A wrapper function to set the clip duration
        def set_signal(duration):
            try:
                duration = int(duration)
            except ValueError:
                return err_dlg('Duration must be an integer.')
            if duration < 1:
                return err_dlg('Duration must be at least 1 frame.')
            self.set_clip_duration.emit(duration)

        dialog = TextFieldDialog(
            'Clip Duration (frames)', str(self.clip.duration))
        dialog.submitted.connect(set_signal)
        dialog.exec()

    def make_left_layout(self):
        layout = QVBoxLayout()

        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label)

        new_button = StyledButton('New Clip', StyledButton.Style.POSITIVE)
        new_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_button.setMinimumWidth(120)
        new_button.clicked.connect(self.new_clip.emit)
        layout.addWidget(new_button)

        return layout

    def make_middle_layout(self):
        layout = QVBoxLayout()

        layout.addLayout(self.make_set_jump_buttons(
            'Start', self.set_clip_start, self.jump_clip_start))
        layout.addLayout(self.make_set_jump_buttons(
            'End', self.set_clip_end, self.jump_clip_end))

        return layout

    def make_righter_layout(self):
        layout = QVBoxLayout()

        set_button = StyledButton('Set Duration')
        set_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        set_button.setMinimumWidth(120)
        set_button.clicked.connect(self.prompt_clip_duration)
        layout.addWidget(set_button)

        return layout

    def make_right_layout(self):
        layout = QVBoxLayout()

        delete_button = StyledButton(
            'Delete Clip', StyledButton.Style.NEGATIVE)
        delete_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Expanding)
        delete_button.setMinimumWidth(120)
        delete_button.clicked.connect(self.delete_clip.emit)
        layout.addWidget(delete_button)

        rename_button = StyledButton('Rename Clip')
        rename_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Expanding)
        rename_button.setMinimumWidth(120)
        rename_button.clicked.connect(self.rename_clip.emit)
        layout.addWidget(rename_button)

        return layout

    def make_set_jump_buttons(self, label_txt, set_signal, jump_signal):
        layout = QHBoxLayout()

        label = QLabel(f'{label_txt}:')
        layout.addWidget(label)

        set_button = StyledButton(None)
        set_button.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogApplyButton
        ))
        set_button.setToolTip(f'Set {label_txt} frame')
        set_button.setFixedSize(64, 32)
        set_button.clicked.connect(set_signal)
        layout.addWidget(set_button)

        jump_button = StyledButton(None)
        jump_button.setIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_ArrowRight
        ))
        jump_button.setToolTip(f'Jump to {label_txt} frame')
        jump_button.setFixedSize(64, 32)
        jump_button.clicked.connect(jump_signal)
        layout.addWidget(jump_button)

        return layout

    def update_ui(self):
        if self.clip is not None:
            self.label.setText(f'Selected: {self.clip.name}')
        else:
            self.label.setText('No clip selected')

    def set_clip(self, clip):
        self.clip = clip
        self.update_ui()
