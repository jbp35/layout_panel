from qgis.PyQt import sip
from qgis.PyQt.QtCore import QObject, Qt, pyqtSlot


class SignalRelay(QObject):
    """Call a Python callback when any watched Qt signal is emitted.

    Layouts and their items are owned and deleted by QGIS, so the plugin
    must not keep references to them to disconnect later: touching a
    deleted C++ object crashes QGIS. Instead every signal is connected to
    this QObject, and deleting the relay makes Qt drop all its connections.
    """

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback

    @pyqtSlot()
    def relay(self):
        self.callback()

    def watch(self, signal):
        """Connect the signal, at most once"""
        try:
            signal.connect(self.relay, Qt.ConnectionType.UniqueConnection)
        except TypeError:
            # PyQt raises when the unique connection already exists
            pass

    def delete(self):
        """Disconnect everything"""
        if not sip.isdeleted(self):
            sip.delete(self)
