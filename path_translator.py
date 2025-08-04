r"""
Script Name: Path Translator
Written By: Kieran Hanrahan

Script Version: 2.0.0
Flame Version: 2025

URL: http://www.github.com/khanrahan/path-translator

Creation Date: 02.10.24
Update Date: 02.27.24

Description:

    Take a path, either Windows or POSIX, and extract part of the path using tokens.
    Useful for converting windows paths to POSIX for Flame, or even paths from other
    machines that just have different mount points.

    Example paths this was tested on below.

    windows path no trailing slash
    J:\dir\dir\dir\dir\_dir\000000

    frankenstein path with posix slashes and windows mount
    J:/dir/dir/dir/dir/dir/dir/dir-dir/file_file_file_file-file_v000.mov

Menus:

    Right-click selected folders in the Media Hub --> Navigate... --> Path Translator

To Install:

    For all users, copy this file to:
    /opt/Autodesk/shared/python

    For a specific user, copy this file to:
    /opt/Autodesk/user/<user name>/python
"""

import os
import re
import xml.etree.ElementTree as ETree
from functools import partial

import flame
from PySide6 import QtCore, QtGui, QtWidgets

TITLE = 'Path Translator'
VERSION_INFO = (2, 0, 0)
VERSION = '.'.join([str(num) for num in VERSION_INFO])
TITLE_VERSION = f'{TITLE} v{VERSION}'
MESSAGE_PREFIX = '[PYTHON]'

SETTINGS_FOLDER = '~/.config/path-translator'
XML = 'path_translator.xml'


class FlameButton(QtWidgets.QPushButton):
    """Custom Qt Flame Button Widget v2.1

    button_name: button text [str]
    connect: execute when clicked [function]
    button_color: (optional) normal, blue [str]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 150 [int]

    Usage:
        button = FlameButton(
            'Button Name', do_something__when_pressed, button_color='blue')
    """
    def __init__(self, button_name, connect, button_color='normal', button_width=150,
                 button_max_width=150):
        super().__init__()

        self.setText(button_name)
        self.setMinimumSize(QtCore.QSize(button_width, 28))
        self.setMaximumSize(QtCore.QSize(button_max_width, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        if button_color == 'normal':
            self.setStyleSheet("""
                QPushButton {
                    color: rgb(154, 154, 154);
                    background-color: rgb(58, 58, 58);
                    border: none;
                    font: 14px 'Discreet'}
                QPushButton:hover {
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:pressed {
                    color: rgb(159, 159, 159);
                    background-color: rgb(66, 66, 66);
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:disabled {
                    color: rgb(116, 116, 116);
                    background-color: rgb(58, 58, 58);
                    border: none}
                QToolTip {
                    color: rgb(170, 170, 170);
                    background-color: rgb(71, 71, 71);
                    border: 10px solid rgb(71, 71, 71)}""")
        elif button_color == 'blue':
            self.setStyleSheet("""
                QPushButton {
                    color: rgb(190, 190, 190);
                    background-color: rgb(0, 110, 175);
                    border: none;
                    font: 12px 'Discreet'}
                QPushButton:hover {
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:pressed {
                    color: rgb(159, 159, 159);
                    border: 1px solid rgb(90, 90, 90)
                QPushButton:disabled {
                    color: rgb(116, 116, 116);
                    background-color: rgb(58, 58, 58);
                    border: none}
                QToolTip {
                    color: rgb(170, 170, 170);
                    background-color: rgb(71, 71, 71);
                    border: 10px solid rgb(71, 71, 71)}""")


class FlameLabel(QtWidgets.QLabel):
    """Custom Qt Flame Label Widget v2.1

    label_name:  text displayed [str]
    label_type:  (optional) select from different styles:
                 normal, underline, background. default is normal [str]
    label_width: (optional) default is 150 [int]

    Usage:
        label = FlameLabel('Label Name', 'normal', 300)
    """
    def __init__(self, label_name, label_type='normal', label_width=150):
        super().__init__()

        self.setText(label_name)
        self.setMinimumSize(label_width, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet("""
                QLabel {
                    color: rgb(154, 154, 154);
                    font: 14px 'Discreet'}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}""")
        elif label_type == 'underline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet("""
                QLabel {
                    color: rgb(154, 154, 154);
                    border-bottom: 1px inset rgb(40, 40, 40);
                    font: 14px 'Discreet'}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}""")
        elif label_type == 'background':
            self.setStyleSheet("""
                QLabel {
                    color: rgb(154, 154, 154);
                    background-color: rgb(30, 30, 30);
                    padding-left: 5px;
                    font: 14px 'Discreet'}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}""")


class FlameLineEdit(QtWidgets.QLineEdit):
    """Custom Qt Flame Line Edit Widget v2.1

    Main window should include this: window.setFocusPolicy(QtCore.Qt.StrongFocus)

    text: text show [str]
    width: (optional) width of widget. default is 150. [int]
    max_width: (optional) maximum width of widget. default is 2000. [int]

    Usage:
        line_edit = FlameLineEdit('Some text here')
    """
    def __init__(self, text, width=150, max_width=2000):
        super().__init__()

        self.setText(text)
        self.setMinimumHeight(28)
        self.setMinimumWidth(width)
        self.setMaximumWidth(max_width)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setStyleSheet("""
            QLineEdit {
                color: rgb(154, 154, 154);
                background-color: rgb(55, 65, 75);
                selection-color: rgb(38, 38, 38);
                selection-background-color: rgb(184, 177, 167);
                border: 1px solid rgb(55, 65, 75);
                padding-left: 5px;
                font: 14px 'Discreet'}
            QLineEdit:focus {background-color: rgb(73, 86, 99)}
            QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}
            QLineEdit:disabled {
                color: rgb(106, 106, 106);
                background-color: rgb(55, 55, 55);
                border: 1px solid rgb(55, 55, 55)}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: none}""")


class FlamePushButton(QtWidgets.QPushButton):
    """Custom Qt Flame Push Button Widget v2.1

    button_name: text displayed on button [str]
    button_checked: True or False [bool]
    connect: execute when button is pressed [function]
    button_width: (optional) default is 150. [int]

    Usage:
        pushbutton = FlamePushButton('Button Name', False)
    """
    def __init__(self, button_name, button_checked, connect=None, button_width=150):
        super().__init__()

        self.setText(button_name)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(button_width, 28)
        self.setMaximumSize(button_width, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.clicked.connect(connect)  # produces error on 2021.1
        self.setStyleSheet("""
            QPushButton {
                color: rgb(154, 154, 154);
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(58, 58, 58),
                    stop: .94 rgb(44, 54, 68));
                text-align: left;
                border-top: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(58, 58, 58),
                    stop: .94 rgb(44, 54, 68));
                border-bottom: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(58, 58, 58),
                    stop: .94 rgb(44, 54, 68));
                border-left: 1px solid rgb(58, 58, 58);
                border-right: 1px solid rgb(44, 54, 68);
                padding-left: 5px; font: 14px 'Discreet'}
            QPushButton:checked {
                color: rgb(217, 217, 217);
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(71, 71, 71),
                    stop: .94 rgb(50, 101, 173));
                text-align: left;
                border-top: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(71, 71, 71),
                    stop: .94 rgb(50, 101, 173));
                border-bottom: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(71, 71, 71),
                    stop: .94 rgb(50, 101, 173));
                border-left: 1px solid rgb(71, 71, 71);
                border-right: 1px solid rgb(50, 101, 173);
                padding-left: 5px;
                font: italic}
            QPushButton:hover {
                border: 1px solid rgb(90, 90, 90)}
            QPushButton:disabled {
                color: #6a6a6a;
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: .93 rgb(58, 58, 58),
                    stop: .94 rgb(50, 50, 50));
                font: light;
                border: none}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: 10px solid rgb(71, 71, 71)}""")


class FlamePushButtonMenu(QtWidgets.QPushButton):
    """Custom Qt Flame Menu Push Button Widget v3.1

    button_name: text displayed on button [str]
    menu_options: list of options show when button is pressed [list]
    menu_width: (optional) width of widget. default is 150. [int]
    max_menu_width: (optional) set maximum width of widget. default is 2000. [int]
    menu_action: (optional) execute when button is changed. [function]

    Usage:
        push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
        menu_push_button = FlamePushButtonMenu(
            'push_button_name', push_button_menu_options)

        or

        push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
        menu_push_button = FlamePushButtonMenu(
            push_button_menu_options[0], push_button_menu_options)

    Notes:
        Started as v2.1
        v3.1 adds a functionionality to set the width of the menu to be the same as the
        button.
    """
    def __init__(self, button_name, menu_options, menu_width=240, max_menu_width=2000,
                 menu_action=None):
        super().__init__()

        self.button_name = button_name
        self.menu_options = menu_options
        self.menu_action = menu_action

        self.setText(button_name)
        self.setMinimumHeight(28)
        self.setMinimumWidth(menu_width)
        self.setMaximumWidth(max_menu_width)  # is max necessary?
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet("""
            QPushButton {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none;
                font: 14px 'Discreet';
                padding-left: 9px;
                text-align: left}
            QPushButton:disabled {
                color: rgb(116, 116, 116);
                background-color: rgb(45, 55, 68);
                border: none}
            QPushButton:hover {
                border: 1px solid rgb(90, 90, 90)}
            QPushButton::menu-indicator {image: none}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: 10px solid rgb(71, 71, 71)}""")

        # Menu
        def match_width():
            """Match menu width to the parent push button width."""
            self.pushbutton_menu.setMinimumWidth(self.size().width())

        self.pushbutton_menu = QtWidgets.QMenu(self)
        self.pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pushbutton_menu.aboutToShow.connect(match_width)
        self.pushbutton_menu.setStyleSheet("""
            QMenu {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none; font: 14px 'Discreet'}
            QMenu::item:selected {
                color: rgb(217, 217, 217);
                background-color: rgb(58, 69, 81)}""")

        self.populate_menu(menu_options)
        self.setMenu(self.pushbutton_menu)

    def create_menu(self, option, menu_action):
        """Create menu item."""
        self.setText(option)

        if menu_action:
            menu_action()

    def populate_menu(self, options):
        """Empty the menu then reassemble the options."""
        self.pushbutton_menu.clear()

        for option in options:
            self.pushbutton_menu.addAction(
                option, partial(self.create_menu, option, self.menu_action))


class FlameMessageWindow(QtWidgets.QDialog):
    """Custom Qt Flame Message Window v2.1

    message_title: text shown in top left of window ie. Confirm Operation [str]
    message_type: confirm, message, error, warning [str] confirm and warning return True
                  or False values
    message: text displayed in body of window [str]
    parent: optional - parent window [object]

    Message Window Types:
        confirm: confirm and cancel button / grey left bar - returns True or False
        message: ok button / blue left bar
        error: ok button / yellow left bar
        warning: confirm and cancel button / red left bar - returns True of False

    Usage:
        FlameMessageWindow('Error', 'error', 'some important message')

        or

        if FlameMessageWindow(
            'Confirm Operation', 'confirm', 'some important message', window):
                do something
    """
    def __init__(self, message_title, message_type, message, parent=None):
        super().__init__()

        self.message_type = message_type

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(QtCore.QSize(500, 330))
        self.setMaximumSize(QtCore.QSize(500, 330))
        self.setStyleSheet('background-color: rgb(36, 36, 36)')

        resolution = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2)
        )

        self.setParent(parent)

        self.grid = QtWidgets.QGridLayout()

        self.main_label = FlameLabel(message_title, 'normal', label_width=500)
        self.main_label.setStyleSheet("""
            color: rgb(154, 154, 154);
            font: 18px 'Discreet'""")

        self.message_text_edit = QtWidgets.QTextEdit(message)
        self.message_text_edit.setDisabled(True)
        self.message_text_edit.setStyleSheet("""
            QTextEdit {
                color: rgb(154, 154, 154);
                background-color: rgb(36, 36, 36);
                selection-color: rgb(190, 190, 190);
                selection-background-color: rgb(36, 36, 36);
                border: none;
                padding-left: 20px;
                padding-right: 20px;
                font: 12px 'Discreet'}""")

        if message_type in ('confirm', 'warning'):
            self.confirm_button = FlameButton(
                'Confirm', self.confirm, button_color='blue', button_width=110)
            self.cancel_button = FlameButton('Cancel', self.cancel, button_width=110)

            self.grid.addWidget(self.main_label, 0, 0)
            self.grid.setRowMinimumHeight(1, 30)
            self.grid.addWidget(self.message_text_edit, 2, 0, 4, 8)
            self.grid.setRowMinimumHeight(9, 30)
            self.grid.addWidget(self.cancel_button, 10, 5)
            self.grid.addWidget(self.confirm_button, 10, 6)
            self.grid.setRowMinimumHeight(11, 30)
        else:
            self.ok_button = FlameButton(
                'Ok', self.confirm, button_color='blue', button_width=110)

            self.grid.addWidget(self.main_label, 0, 0)
            self.grid.setRowMinimumHeight(1, 30)
            self.grid.addWidget(self.message_text_edit, 2, 0, 4, 8)
            self.grid.setRowMinimumHeight(9, 30)
            self.grid.addWidget(self.ok_button, 10, 6)
            self.grid.setRowMinimumHeight(11, 30)

        # Why stripping these?
        message = message.replace('<br>', '')
        message = message.replace('<center>', '')
        message = message.replace('<dd>', '')

        self.setLayout(self.grid)
        self.show()
        self.exec_()

    def __bool__(self):
        return self.confirmed

    def cancel(self):
        self.close()
        self.confirmed = False

    def confirm(self):
        self.close()
        self.confirmed = True

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        if self.message_type == 'confirm':
            line_color = QtGui.QColor(71, 71, 71)
        elif self.message_type == 'message':
            line_color = QtGui.QColor(0, 110, 176)
        elif self.message_type == 'error':
            line_color = QtGui.QColor(200, 172, 30)
        elif self.message_type == 'warning':
            line_color = QtGui.QColor(200, 29, 29)

        painter.setPen(QtGui.QPen(line_color, 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, 330)

        painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, 500, 40)

    def mousePressEvent(self, event):
        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass


class FlameTokenPushButton(QtWidgets.QPushButton):
    """Custom Qt Flame Token Push Button Widget v2.1

    button_name: Text displayed on button [str]
    token_dict: Dictionary defining tokens. {'Token Name': '<Token>'} [dict]
    token_dest: LineEdit that token will be applied to [object]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 300 [int]

    Usage:
        token_dict = {'Token 1': '<Token1>', 'Token2': '<Token2>'}
        token_push_button = FlameTokenPushButton('Add Token', token_dict, token_dest)
    """
    def __init__(self, button_name, token_dict, token_dest, button_width=110,
                 button_max_width=300):
        super().__init__()

        self.setText(button_name)
        self.setMinimumHeight(28)
        self.setMinimumWidth(button_width)
        self.setMaximumWidth(button_max_width)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet("""
            QPushButton {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none;
                font: 14px 'Discreet';
                padding-left: 6px;
                text-align: left}
            QPushButton:hover {
                border: 1px solid rgb(90, 90, 90)}
            QPushButton:disabled {
                color: rgb(106, 106, 106);
                background-color: rgb(45, 55, 68);
                border: none}
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: 10px solid rgb(71, 71, 71)}""")

        def token_action_menu():

            def insert_token(token):
                for key, value in token_dict.items():
                    if key == token:
                        token_name = value
                        token_dest.insert(token_name)

            # the lambda sorts aAbBcC instead of ABCabc
            for key, value in sorted(token_dict.items(), key=lambda v: v[0].upper()):
                del value
                token_menu.addAction(key, partial(insert_token, key))

        token_menu = QtWidgets.QMenu(self)
        token_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        token_menu.setStyleSheet("""
            QMenu {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none; font: 14px 'Discreet'}
            QMenu::item:selected {
                color: rgb(217, 217, 217);
                background-color: rgb(58, 69, 81)}""")

        self.setMenu(token_menu)
        token_action_menu()


class SettingsStore:
    """Store settings as XML.

    The setting XML is structured as below:

    <settings>
        <script_name>Script Name
            <version>X.X.X
                <presets>
                    <preset>
                    </preset>
                </preset>
            </version>
        </script_name>
    </settings>
    """

    def __init__(self, file):
        """Initialize the instance.

        Args:
            file: Filepath of existing or to be created XML file of settings.
        """
        self.file = file
        self.root = None
        self.tree = None
        self.presets = None
        self.load()

    def load(self):
        """Load preset file if preset and store XML tree & root."""
        if os.path.isfile(self.file):
            self.tree = ETree.parse(self.file)
        else:
            self.init_tree()

        self.get_settings_root()
        self.get_settings_presets()

    def reload(self):
        """Reload the file and store root & presets again."""
        self.load()
        self.get_settings_root()
        self.get_settings_presets()

    def init_tree(self):
        """Create a new empty tree if one does not already exists."""
        settings = ETree.Element('settings')

        name = ETree.SubElement(settings, 'script_name')
        name.text = TITLE

        version = ETree.SubElement(name, 'version')
        version.text = VERSION

        presets = ETree.SubElement(version, 'presets')
        self.tree = ETree.ElementTree(settings)

    def get_settings_root(self):
        """Store the root object for the ElementTree of settings."""
        self.root = self.tree.getroot()

    def get_settings_presets(self):
        """Store the element object for the ElementTree of settings."""
        self.presets = self.root.find('script_name/version/presets')

    def get_presets(self):
        """Return a list of preset Element objects."""
        return self.presets.findall('preset')

    def load_preset_by_index_element(self, index, element):
        """Convert None to empty string.

        ElementTree saves empty string as None.
        """
        preset_element = (
            self.presets.findall('preset')[index].find(element).text)

        if preset_element is None:
            preset_element = ''

        return preset_element

    def duplicate_check(self, preset_name):
        """Check that preset to be saved would not be a duplicate."""
        duplicate = False

        for preset in self.get_presets():
            if preset.find('name').text == preset_name:
                duplicate = True

        return duplicate

    def sort(self):
        """Alphabetically sort presets by name attribute."""
        self.presets[:] = sorted(
            self.presets,
            key=lambda preset: preset.find('name').text)

    def get_preset_names(self):
        """Return a list of all the preset names."""
        return [preset.find('name').text for preset in self.get_presets()]

    def add_preset(self, name=None, find=None, replace=None):
        """Add preset Element object to the presets Element Tree."""
        preset = ETree.Element('preset')

        preset_name = ETree.SubElement(preset, 'name')
        preset_name.text = name

        preset_find = ETree.SubElement(preset, 'find')
        preset_find.text = find

        preset_replace = ETree.SubElement(preset, 'replace')
        preset_replace.text = replace

        self.presets.append(preset)

    def overwrite_preset(self, name=None, find=None, replace=None):
        """Replace pattern in presets XML tree then save to XML file."""
        for preset in self.get_presets():
            if preset.find('name').text == name:
                preset.find('find').text = find
                preset.find('replace').text = replace

    def delete(self, preset):
        """Remove preset Element from presets Element Tree."""
        self.presets.remove(preset)

    def save(self):
        """Create folder path if necessary then write out the XML."""
        if not os.path.exists(os.path.dirname(self.file)):
            os.makedirs(os.path.dirname(self.file))

        self.tree.write(
            self.file,
            encoding='UTF-8',
            xml_declaration=True
        )


class SavePresetWindow(QtWidgets.QDialog):
    """View to confirm name of preset before saving."""

    def __init__(self, parent):
        """Initialize the instance.

        Args:
            parent: Pyside object to make this window a child of.
        """
        super().__init__(parent)
        self.dimensions = {'x': 500, 'y': 100}
        self.init_window()

    @property
    def name(self):
        """Get the preset name."""
        return self.line_edit_preset_name.text()

    @name.setter
    def name(self, string):
        """Set the present name."""
        self.line_edit_preset_name.setText(string)

    def init_window(self):
        """Initialize the window."""
        self.setMinimumSize(
                self.dimensions['x'], self.dimensions['y'])

        self.setStyleSheet('background-color: #272727')
        self.setWindowTitle('Save Preset As...')

        # Center Window
        resolution = QtGui.QGuiApplication.primaryScreen().screenGeometry()
        self.move(
            (resolution.width() / 2) - (self.dimensions['x'] / 2),
            (resolution.height() / 2) - (self.dimensions['y'] / 2 + 44))

        # Labels
        self.label_preset_name = FlameLabel('Preset Name', 'normal')

        # Line Edits
        self.line_edit_preset_name = FlameLineEdit('')

        # Buttons
        self.save_btn_cancel = FlameButton(
            'Cancel', self.reject, button_width=110)
        self.save_btn_save = FlameButton(
            'Save', self.accept, button_color='blue', button_width=110)

        # Layout
        self.save_grid = QtWidgets.QGridLayout()
        self.save_grid.setVerticalSpacing(10)
        self.save_grid.setHorizontalSpacing(10)
        self.save_grid.addWidget(self.label_preset_name, 0, 0)
        self.save_grid.addWidget(self.line_edit_preset_name, 0, 1)

        self.save_hbox = QtWidgets.QHBoxLayout()
        self.save_hbox.addStretch(1)
        self.save_hbox.addWidget(self.save_btn_cancel)
        self.save_hbox.addWidget(self.save_btn_save)

        self.save_vbox = QtWidgets.QVBoxLayout()
        self.save_vbox.setContentsMargins(20, 20, 20, 20)
        self.save_vbox.addLayout(self.save_grid)
        self.save_vbox.addSpacing(20)
        self.save_vbox.addLayout(self.save_hbox)

        self.setLayout(self.save_vbox)


class PathTranslator:
    """Convert a path from one system to a valid path on another system.

    Mostly useful to convert windows paths to posix paths, but could also be used for
    posix paths on machines that have different mount points.
    """
    def __init__(self, selection):
        """Create object with necessary attributes."""
        self.message(TITLE_VERSION)
        self.message(f'Script called from {__file__}')

        self.selection = selection

        # Load settings
        self.settings_file = None
        self.get_settings_file()
        self.settings = SettingsStore(self.settings_file)

        # Load starting path
        self.path = None
        self.load_path()

        # Generate dict containing token names, shorthand, and values
        self.tokens_input = None
        self.generate_tokens_input()

        self.tokens_output = None
        self.generate_tokens_output()

        # Load the input pattern
        self.pattern_input = None
        self.load_pattern_input()

        # Translate the input token pattern to a regex
        self.pattern_input_regex = None
        self.generate_pattern_input_regex()

        self.pattern_input_regex_capture = None
        self.capture_pattern_input_regex()

        # Load the output pattern
        self.pattern_output = None
        self.load_pattern_output()

        # Replace tokens to generate new folder name
        self.folder_new = None
        self.generate_folder_new()

        # Starting dimensions
        self.window_x = 1000
        self.window_y = 130
        self.save_window_x = 500
        self.save_window_y = 100

        self.save_window = SavePresetWindow(self.main_window)

        self.main_window()

    @staticmethod
    def message(string):
        """Print message to shell window and append global MESSAGE_PREFIX."""
        print(' '.join([MESSAGE_PREFIX, string]))

    def get_settings_file(self):
        """Generate filepath for settings."""
        user_folder = os.path.expanduser(SETTINGS_FOLDER)
        self.settings_file = os.path.join(user_folder, XML)

    def generate_tokens_input(self):
        """Generate dictionary of input pattern tokens with a list for each.

        Each item has a list with the shorthand token, a token regex, and then the
        default value.  Input tokens use curly braces to follow Flame standard
        convention.

        {name : [ token, pattern_regex, value ], ...}

        name = full name of the token
        token = this is the shorthand used in the pattern. ie, {token}
        pattern_regex = regex to extract the token data from the input path
        value = starting value
        """
        self.tokens_input = {
            'Root':
                ['{root}', r'[A-Z]:\\', ''],
            'Path':
                ['{path}', r'(?P<Path>[a-zA-Z0-9_\.\-\\\/]+)', ''],
        }

    def generate_tokens_output(self):
        """Generate dictionary of output pattern tokens with a list for each.

        Each item has a list with the shorthand token and a method or attribute to
        return a value.  Output tokens use angle brackets to follow Flame standard
        convention.

        {name: [ token, value ], ...}

        name = full name of token
        token = this is the shorthand used in the pattern. ie, <token>
        value = method or attribute to return a value
        """
        self.tokens_output = {
                'Path': ['<path>', self.get_token_output_path]
        }

    def get_token_output_path(self):
        """Return path for the <path> token.

        Converts backslashes on the captured string using the input token path to
        backslashes on the output pattern path.
        """
        try:
            result = self.pattern_input_regex_capture.group('Path').replace('\\', '/')
        except (AttributeError, IndexError):
            result = ''
        return result

    def load_path(self):
        """Load the input path from the clipboard contents or empty str."""
        if self.settings.get_preset_names():
            if self.load_preset_by_index_element(0, 'clipboard_contents') == 'true':
                self.load_path_from_clipboard()
        else:
            self.path = ''

    def load_path_from_clipboard(self):
        """Get clipboard contents."""
        qt_app_instance = QtWidgets.QApplication.instance()
        self.path = qt_app_instance.clipboard().text()  # raw string?

    def load_pattern_input(self):
        """Load the first preset's pattern or use the default pattern."""
        if self.settings.get_preset_names():
            # load output pattern for first element in list of presets
            self.pattern_input = self.settings.load_preset_by_index_element(
                0, 'pattern_input')
        else:
            self.pattern_input = ''

    def generate_pattern_input_regex(self):
        r"""Generate a regex based on the input pattern tokens.

        This regex will be used to find matching folders.  Use the token regex if
        available otherwise just token.

        for example, {path} would become [a-zA-Z0-9+\\
        """
        self.pattern_input_regex = self.pattern_input.replace('\\', '\\\\')  # ugly

        for name, values in self.tokens_input.items():
            del name
            token, pattern_regex, *unused = values
            del unused
            self.pattern_input_regex = self.pattern_input_regex.replace(
                    token, pattern_regex)

    def capture_pattern_input_regex(self):
        """Perform the regex match on the input path.

        Use the input pattern converted to a regex and the input path to create a match
        object.
        """
        self.pattern_input_regex_capture = re.match(
                self.pattern_input_regex, self.path
        )

    def load_pattern_output(self):
        """Load output pattern from settings."""
        if self.settings.get_preset_names():
            # load input pattern for first element in list of presets
            self.pattern_output = self.settings.load_preset_by_index_element(
                0, 'pattern_output')
        else:
            self.pattern_output = ''

    def generate_folder_new(self):
        """Replace output path tokens with values."""
        result = self.pattern_output

        for name, values in self.tokens_output.items():
            del name
            token, value = values
            result = result.replace(token, value())

        if os.path.splitext(result)[1]:
            self.folder_new = os.path.dirname(result)
        else:
            self.folder_new = os.path.join(result, '')

    def preset_save_button(self):
        """Triggered when the Save button the Presets line is pressed."""
        self.save_window.name = self.main_window.preset
        if self.save_window.exec() == QtWidgets.QDialog.Accepted:
            duplicate = self.settings.duplicate_check(self.save_window.name)

            if duplicate and FlameMessageWindow(
                    'Overwrite Existing Preset', 'confirm', 'Are you '
                    + 'sure want to permanently overwrite this preset?' + '<br/>'
                    + 'This operation cannot be undone.'):
                self.settings.overwrite_preset(
                        name=self.save_window.name,
                        pattern_input=self.pattern_input,
                        pattern_output=self.pattern_output,
                )

            if not duplicate:
                self.settings.add_preset(
                        name=self.save_window.name,
                        pattern_input=self.pattern_input,
                        pattern_output=self.pattern_output,
                )
                self.settings.sort()

            try:
                self.settings.save()
                self.message(f'{self.save_window.name} preset saved ' +
                             f'to {self.settings_file}')
            except OSError:  # removed IOError based on linter rule UP024
                FlameMessageWindow(
                    'Error', 'error',
                    f'Check permissions on {self.settings_file}')

            self.main_window.presets = self.settings.get_preset_names()
            self.main_window.preset = self.save_window.name

    def save_preset_window(self):
        """Smaller window with save dialog."""

        def check_preset_folder():
            """Check that destination folder for preset XML file is available."""
            result = False

            if os.path.exists(self.settings_xml_folder):
                result = True
            else:
                try:
                    os.makedirs(self.settings_xml_folder)
                    result = True
                except OSError:
                    FlameMessageWindow(
                        'Error', 'error',
                        f'Could not create {self.settings_xml_folder}')
            return result

        def save_preset():
            """Save new preset to XML file."""
            # is the below taking the name from this window or the previous
            new_preset = ETree.Element('preset', name=self.line_edit_preset_name.text())

            new_clipboard_contents = ETree.SubElement(new_preset, 'clipboard_contents')
            new_clipboard_contents.text = (
                    str(self.btn_path_clipboard.isEnabled()).lower()
            )

            new_pattern = ETree.SubElement(new_preset, 'pattern_input')
            new_pattern.text = self.pattern_input

            new_pattern = ETree.SubElement(new_preset, 'pattern_output')
            new_pattern.text = self.pattern_output

            self.settings_xml_presets.append(new_preset)
            sort_presets()

            if check_preset_folder():
                try:
                    self.settings_xml_tree.write(
                        self.settings_xml_file,
                        encoding='UTF-8',
                        xml_declaration=True
                    )

                    self.message(f'{self.line_edit_preset_name.text()} preset saved' +
                                 f' to {self.settings_xml_file}')
                except OSError as err:
                    raise err
                    FlameMessageWindow(
                        'Error', 'error',
                        f'Check permissions on {self.settings_xml_file}')

        def overwrite_preset():
            """Replace pattern in presets XML tree then save to XML file."""
            preset_name = self.line_edit_preset_name.text()

            for preset in self.settings_xml_presets.findall('preset'):
                if preset.get('name') == preset_name:
                    preset.find('clipboard_contents').text = (
                            str(self.btn_path_clipboard.isEnabled()).lower()
                    )
                    preset.find('pattern_input').text = (self.pattern_input)
                    preset.find('pattern_output').text = (self.pattern_output)

            try:
                self.settings_xml_tree.write(
                        self.settings_xml_file,
                        encoding='UTF-8',
                        xml_declaration=True
                )

                self.message(f'{self.line_edit_preset_name.text()} preset saved to ' +
                             f'{self.settings_xml_file}')
            except OSError:
                FlameMessageWindow(
                    'Error', 'error',
                    f'Check permissions on {self.settings_xml_file}')

        def sort_presets():
            """Alphabetically sort presets by name attribute."""
            self.settings_xml_presets[:] = sorted(
                self.settings_xml_presets,
                key=lambda child: (child.tag, child.get('name')))

        def save_button():
            """Triggered when the Save button at the bottom is pressed."""
            duplicate = self.settings.duplicate_check(self.save_window.name)

            if duplicate and FlameMessageWindow(
                    'Overwrite Existing Preset', 'confirm', 'Are you ' +
                    'sure want to permanently overwrite this preset?' + '<br/>' +
                    'This operation cannot be undone.'):
                overwrite_preset()
                self.btn_preset.populate_menu(
                    [preset.get('name') for preset in
                     self.settings_xml_presets.findall('preset')])
                self.btn_preset.setText(self.line_edit_preset_name.text())
                self.save_window.close()

            if not duplicate:
                save_preset()
                self.btn_preset.populate_menu(
                    [preset.get('name') for preset in
                     self.settings_xml_presets.findall('preset')])
                self.btn_preset.setText(self.line_edit_preset_name.text())
                self.save_window.close()

        def cancel_button():
            """Triggered when the Cancel button at the bottom is pressed."""
            self.save_window.close()

        self.save_window = QtWidgets.QWidget()

        self.save_window.setMinimumSize(self.save_window_x, self.save_window_y)

        self.save_window.setStyleSheet('background-color: #272727')
        self.save_window.setWindowTitle('Save Preset As...')

        # Center Window
        resolution = QtGui.QGuiApplication.primaryScreen().availableGeometry()

        self.save_window.move(
            (resolution.width() / 2) - (self.save_window_x / 2),
            (resolution.height() / 2) - (self.save_window_y / 2 + 44)
        )

        # Buttons
        self.save_btn_save = FlameButton(
            'Save', save_button, button_color='blue', button_width=110)
        self.save_btn_cancel = FlameButton('Cancel', cancel_button, button_width=110)

        # Labels
        self.label_preset_name = FlameLabel('Preset Name', 'normal')
        self.label_preset_pattern_input = FlameLabel('Input Pattern', 'normal')
        self.label_preset_pattern_output = FlameLabel('Output Pattern', 'normal')

        # Line Edits
        self.line_edit_preset_name = FlameLineEdit(self.btn_preset.text())

        # Layout
        self.save_grid = QtWidgets.QGridLayout()
        self.save_grid.setVerticalSpacing(10)
        self.save_grid.setHorizontalSpacing(10)
        self.save_grid.addWidget(self.label_preset_name, 0, 0)
        self.save_grid.addWidget(self.line_edit_preset_name, 0, 1)

        self.save_hbox = QtWidgets.QHBoxLayout()
        self.save_hbox.addStretch(1)
        self.save_hbox.addWidget(self.save_btn_cancel)
        self.save_hbox.addWidget(self.save_btn_save)

        self.save_vbox = QtWidgets.QVBoxLayout()
        self.save_vbox.setContentsMargins(20, 20, 20, 20)
        self.save_vbox.addLayout(self.save_grid)
        self.save_vbox.addSpacing(20)
        self.save_vbox.addLayout(self.save_hbox)

        self.save_window.setLayout(self.save_vbox)

        self.save_window.show()

        return self.window

    def main_window(self):
        """The main GUI window."""
        def get_selected_preset():
            """Get preset that should be displayed or return empty string."""
            try:
                selected_preset = (
                        self.settings_xml_presets.findall('preset')[0].get('name')
                )
            except IndexError:  # if findall() returns empty list
                selected_preset = ''

            return selected_preset

        def get_preset_clipboard_contents_state():
            """Get the intended state of CLipboard button."""
            if self.settings_xml_presets.findall('preset'):
                if self.load_preset_by_index_element(0, 'clipboard_contents') == 'true':
                    state = True
            else:
                state = False

            return state

        def toggle_clipboard_contents():
            """Update UI when Clipboard Contents button is pressed."""
            if self.line_edit_path.isEnabled():
                self.line_edit_path.setEnabled(False)
                self.load_path_from_clipboard()
                self.line_edit_path.setText(self.path)
            else:
                self.line_edit_path.setEnabled(True)

        def update_folder():
            """Update folder when pattern is changed."""
            self.path = self.line_edit_path.text()
            self.pattern_input = self.line_edit_pattern_input.text()
            self.pattern_output = self.line_edit_pattern_output.text()
            self.generate_pattern_input_regex()
            self.capture_pattern_input_regex()
            self.generate_folder_new()
            self.line_edit_folder.setText(self.folder_new)

        def update_pattern():
            """Update pattern when preset is changed."""
            preset_name = self.btn_preset.text()

            if preset_name:  # might be empty str if all presets were deleted
                for preset in self.settings_xml_presets.findall('preset'):
                    if preset.get('name') == preset_name:
                        if preset.find('clipboard_contents').text == 'true':
                            self.load_path_from_clipboard()
                            self.line_edit_path.setText(self.path)
                            self.line_edit_path.setEnabled(False)
                            self.btn_path_clipboard.setChecked(True)
                        else:
                            self.line_edit_path.setEnabled(True)
                            self.btn_path_clipboard.setChecked(False)
                        self.line_edit_pattern_input.setText(
                                preset.find('pattern_input').text)
                        self.line_edit_pattern_output.setText(
                                preset.find('pattern_output').text)
                        break  # should not be any duplicates

        def preset_delete_button():
            """Triggered when the Delete button on the Preset line is pressed."""
            if FlameMessageWindow(
                    'Confirm Operation', 'confirm', 'Are you sure want to'
                    + ' permanently delete this preset?' + '<br/>' + 'This operation'
                    + ' cannot be undone.'):
                preset_name = self.btn_preset.text()

                for preset in self.settings.get_presets():
                    if preset.fine('name').text == preset_name:
                        self.settings.delete(preset)
                        self.message(
                            f'{preset_name} preset deleted from ' +
                            f'{self.settings_file}')

                self.settings.save()

            # Reload presets button
            self.settings.reload()
            self.btn_preset.populate_menu(self.settings.get_preset_names())
            self.btn_preset.setText(get_selected_preset())
            update_pattern()

        def preset_save_button():
            """Triggered when the Save button the Presets line is pressed."""
            self.save_preset_window()

        def okay_button():
            """Triggered when the Okay button at the bottom is pressed."""
            # add try and error msg window if path doesnt exist
            if os.path.exists(self.folder_new):
                flame.mediahub.files.set_path(self.folder_new)
                self.window.close()
                self.message(f'MediaHub path changed to {self.folder_new}')
                self.message('Done!')
            else:
                FlameMessageWindow('Error', 'error',
                        f'{self.folder_new} does not exist.')

        def cancel_button():
            """Triggered when the Cancel button at the bottom is pressed."""
            self.message('Cancelled!')
            self.window.close()

        self.window = QtWidgets.QWidget()

        self.window.setMinimumSize(self.window_x, self.window_y)
        self.window.setStyleSheet('background-color: #272727')
        self.window.setWindowTitle(TITLE_VERSION)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Center Window
        resolution = QtGui.QGuiApplication.primaryScreen().availableGeometry()

        self.window.move(
                (resolution.width() / 2) - (self.window_x / 2),
                (resolution.height() / 2) - (self.window_y / 2 + 44)
        )

        # Labels
        self.label_preset = FlameLabel('Preset', 'normal')
        self.label_path = FlameLabel('Path', 'normal')
        self.label_pattern_input = FlameLabel('Input Pattern', 'normal')
        self.label_pattern_output = FlameLabel('Output Pattern', 'normal')
        self.label_folder = FlameLabel('New Destination', 'normal')

        # Lines
        self.line_edit_path = FlameLineEdit(self.path)
        self.line_edit_path.setEnabled(not get_preset_clipboard_contents_state())
        self.line_edit_path.textChanged.connect(update_folder)

        self.line_edit_pattern_input = FlameLineEdit(self.pattern_input)
        self.line_edit_pattern_input.textChanged.connect(update_folder)

        self.line_edit_pattern_output = FlameLineEdit(self.pattern_output)
        self.line_edit_pattern_output.textChanged.connect(update_folder)

        self.line_edit_folder = FlameLabel(self.folder_new, 'background')

        # Buttons
        self.btn_preset = FlamePushButtonMenu(
            get_selected_preset(),
            self.settings.get_preset_names(),
            menu_action=update_pattern
        )
        self.btn_preset.setMaximumSize(QtCore.QSize(4000, 28))  # span over to Save btn

        self.btn_preset_save = FlameButton(
                'Save', preset_save_button, button_width=110)
        self.btn_preset_delete = FlameButton(
                'Delete', preset_delete_button, button_width=110)
        self.btn_path_clipboard = FlamePushButton(
                'Clipboard Contents',
                get_preset_clipboard_contents_state(),
                button_width=240)
        self.btn_path_clipboard.clicked.connect(toggle_clipboard_contents)
        self.btn_tokens_input = FlameTokenPushButton(
                'Add Token',
                # self.tokens is a dict with a nested set for each key
                # FlameTokenPushButton wants a dict that is only {token_name: token}
                # so need to simplify it with a dict comprehension
                {key: values[0] for key, values in self.tokens_input.items()},
                self.line_edit_pattern_input)
        self.btn_tokens_output = FlameTokenPushButton(
                'Add Token',
                # self.tokens is a dict with a nested set for each key
                # FlameTokenPushButton wants a dict that is only {token_name: token}
                # so need to simplify it with a dict comprehension
                {key: values[0] for key, values in self.tokens_output.items()},
                self.line_edit_pattern_output)
        self.btn_ok = FlameButton(
                'Ok', okay_button, button_color='blue', button_width=110)
        self.btn_cancel = FlameButton('Cancel', cancel_button, button_width=110)

        # Layout
        self.hbox1 = QtWidgets.QHBoxLayout()
        self.hbox1.addStretch()

        self.grid = QtWidgets.QGridLayout()
        self.grid.setVerticalSpacing(10)
        self.grid.setHorizontalSpacing(10)
        self.grid.addWidget(self.label_preset, 0, 0)
        self.grid.addWidget(self.btn_preset, 0, 1)
        self.grid.addWidget(self.btn_preset_save, 0, 2)
        self.grid.addWidget(self.btn_preset_delete, 0, 3)
        self.grid.addWidget(self.label_path, 1, 0)
        self.grid.addWidget(self.line_edit_path, 1, 1)
        self.grid.addWidget(self.btn_path_clipboard, 1, 2, 1, 2)
        self.grid.addWidget(self.label_pattern_input, 2, 0)
        self.grid.addWidget(self.line_edit_pattern_input, 2, 1)
        self.grid.addWidget(self.btn_tokens_input, 2, 2)
        self.grid.addWidget(self.label_pattern_output, 3, 0)
        self.grid.addWidget(self.line_edit_pattern_output, 3, 1)
        self.grid.addWidget(self.btn_tokens_output, 3, 2)
        self.grid.addWidget(self.label_folder, 4, 0)
        self.grid.addWidget(self.line_edit_folder, 4, 1)
        self.grid.addLayout(self.hbox1, 4, 1)

        self.hbox2 = QtWidgets.QHBoxLayout()
        self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.btn_cancel)
        self.hbox2.addWidget(self.btn_ok)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setContentsMargins(20, 20, 20, 20)
        self.vbox.addLayout(self.grid)
        self.vbox.addSpacing(20)
        self.vbox.addLayout(self.hbox2)

        self.window.setLayout(self.vbox)

        self.window.show()

        return self.window


def scope_folders(selection):
    """Determine if selection is a folder in the MediaHub > Files tab."""
    return any(isinstance(item, flame.PyMediaHubFilesFolder) for item in selection)


def get_mediahub_files_custom_ui_actions():
    """Add right click menu items."""
    return [{'name': 'Navigate...',
             'actions': [{'name': 'Path Translator',
                          'isVisible': scope_folders,
                          'execute': PathTranslator,
                          'minimumVersion': '2025.0.0'}]
            }]
