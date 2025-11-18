from PyQt6.QtCore import QObject, pyqtSignal

class _AppSignals(QObject):
    """Sinais globais da aplicação."""
    documentos_atualizados = pyqtSignal()
    layout_update_requested = pyqtSignal()

signals = _AppSignals()