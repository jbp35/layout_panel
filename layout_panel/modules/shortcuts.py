from qgis.PyQt.QtCore import QEvent, QObject, Qt
from qgis.PyQt.QtGui import QAction, QKeySequence
from qgis.gui import QgsGui

try:
    from qgis.PyQt.QtCore import QKeyCombination  # Qt6 only
except ImportError:
    QKeyCombination = None


def registerShortcut(action, name, default_shortcut):
    """Register an action in the QGIS shortcut manager (Settings > Keyboard Shortcuts),
    which applies the user's shortcut if they changed it"""
    action.setObjectName(name)
    QgsGui.shortcutsManager().registerAction(action, default_shortcut)


def unregisterShortcut(action):
    QgsGui.shortcutsManager().unregisterAction(action)


def keySequence(event):
    """Key sequence of a key event (keypad Enter counts as Return)"""
    key = Qt.Key(event.key())
    if key == Qt.Key.Key_Enter:
        key = Qt.Key.Key_Return
    modifiers = event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier
    if QKeyCombination is None:
        return QKeySequence(int(modifiers) | int(key))  # Qt5
    return QKeySequence(QKeyCombination(modifiers, key))


class PanelShortcuts(QObject):
    """Keyboard shortcuts of the layout list.

    They are registered in the QGIS shortcut manager so users can change
    them, but they only work while the layout list has the focus. Several
    defaults are also QGIS shortcuts (Ctrl+D removes the current layer), so
    the list claims them first instead of letting QGIS run its own action.
    """

    # (name, text, default shortcut, method of the panel called when triggered)
    SHORTCUTS = [
        ('mActionLayoutPanelNewLayout', 'New Print Layout', 'Ctrl+N', 'newLayout'),
        ('mActionLayoutPanelOpenLayout', 'Open Layout', 'Return', 'openLayout'),
        ('mActionLayoutPanelRenameLayout', 'Rename Layout', 'F2', 'renameLayout'),
        ('mActionLayoutPanelDuplicateLayout', 'Duplicate Layouts', 'Ctrl+D', 'duplicateLayouts'),
        ('mActionLayoutPanelRemoveLayout', 'Remove Layouts...', 'Del', 'removeLayouts'),
        ('mActionLayoutPanelRemoveLayoutNoConfirm', 'Remove Layouts Without Confirmation', 'Shift+Del',
         'removeLayoutsWithoutConfirmation'),
        ('mActionLayoutPanelCopyToClipboard', 'Copy Layout to Clipboard', 'Ctrl+C', 'copyToClipboard'),
    ]

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.actions = []
        for name, text, default_shortcut, method in self.SHORTCUTS:
            # the action is not added to any widget, so QGIS never triggers it globally
            action = QAction(f'Layout Panel: {text}', self)
            action.triggered.connect(getattr(panel, method))
            registerShortcut(action, name, default_shortcut)
            self.actions.append(action)
        panel.listWidget.installEventFilter(self)

    def actionFor(self, event):
        sequence = keySequence(event)
        for action in self.actions:
            if not action.shortcut().isEmpty() and action.shortcut().matches(sequence) == QKeySequence.SequenceMatch.ExactMatch:
                return action
        return None

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.ShortcutOverride and self.actionFor(event):
            # take the key before QGIS shortcuts do; it then arrives as a KeyPress
            event.accept()
            return True
        if event.type() == QEvent.Type.KeyPress and not self.panel.listWidget.state() == self.panel.listWidget.State.EditingState:
            action = self.actionFor(event)
            if action:
                action.trigger()
                return True
        return False

    def cleanup(self):
        self.panel.listWidget.removeEventFilter(self)
        for action in self.actions:
            unregisterShortcut(action)
        self.actions = []
