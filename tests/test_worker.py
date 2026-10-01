import threading
import time

from PySide6.QtCore import QObject, QThread, Qt, Slot
from PySide6.QtTest import QTest

from grepzztranslate.config import Config
from grepzztranslate.worker import LookupWorker


def test_background_worker_delivers_on_gui_thread(qt_app, paths):
    main_id = threading.get_ident()
    received = []

    class Receiver(QObject):
        @Slot(list)
        def on_ready(self, warnings):
            received.append((threading.get_ident(), warnings))

    receiver = Receiver(qt_app)
    thread = QThread()
    worker = LookupWorker(paths, Config())
    worker.moveToThread(thread)
    thread.started.connect(worker.initialize)
    worker.ready.connect(receiver.on_ready, Qt.ConnectionType.QueuedConnection)
    thread.start()
    try:
        for _ in range(200):
            qt_app.processEvents()
            time.sleep(0.025)
            if received:
                break
        assert received
        assert received[0][0] == main_id
        assert not received[0][1]
    finally:
        thread.quit()
        thread.wait(5000)
