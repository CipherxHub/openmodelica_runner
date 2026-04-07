"""
OpenModelica Simulation Runner
================================
A PyQt6 desktop application to launch OpenModelica compiled executables
with configurable start and stop time parameters.

Author: CipherxHub / Himalaya Yadav
License: MIT
"""

import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QGroupBox, QSpinBox, QStatusBar, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QTextCursor

from simulation_runner import SimulationRunner
from validators import SimulationInputValidator


class SimulationWorker(QThread):
    """
    Worker thread to run the simulation executable without blocking the GUI.

    Signals:
        output_received (str): Emitted when stdout/stderr data arrives.
        finished (int): Emitted when the process ends; carries return code.
        error_occurred (str): Emitted on process launch failure.
    """

    output_received = pyqtSignal(str)
    finished = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, runner: SimulationRunner) -> None:
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        """Execute the simulation and relay output back to the main thread."""
        try:
            return_code = self._runner.execute(self._emit_output)
            self.finished.emit(return_code)
        except (FileNotFoundError, PermissionError, OSError) as exc:
            self.error_occurred.emit(str(exc))

    def _emit_output(self, line: str) -> None:
        self.output_received.emit(line)


class ExecutableSelector(QWidget):
    """
    Composite widget: a read-only line edit + Browse button for picking an
    executable from the filesystem.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select the compiled OpenModelica executable…")
        self.path_edit.setReadOnly(False)
        self.path_edit.setObjectName("pathEdit")

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.setFixedWidth(90)
        self.browse_btn.clicked.connect(self._browse)

        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_btn)

    def _browse(self) -> None:
        """Open a file dialog and populate the path field."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenModelica Executable",
            str(Path.home()),
            "Executables (*.exe *.sh *);;All Files (*)"
        )
        if path:
            self.path_edit.setText(path)

    @property
    def executable_path(self) -> str:
        return self.path_edit.text().strip()


class OutputConsole(QTextEdit):
    """
    A read-only console widget that displays simulation output with
    colour-coded lines (stdout vs error vs info).
    """

    INFO_COLOR = "#00d4ff"
    SUCCESS_COLOR = "#00ff9f"
    ERROR_COLOR = "#ff2d78"
    DEFAULT_COLOR = "#c8c8c8"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("outputConsole")
        self.setFont(QFont("Courier New", 10))

    def append_info(self, text: str) -> None:
        self._append_colored(text, self.INFO_COLOR)

    def append_success(self, text: str) -> None:
        self._append_colored(text, self.SUCCESS_COLOR)

    def append_error(self, text: str) -> None:
        self._append_colored(text, self.ERROR_COLOR)

    def append_output(self, text: str) -> None:
        self._append_colored(text, self.DEFAULT_COLOR)

    def _append_colored(self, text: str, color: str) -> None:
        self.setTextColor(QColor(color))
        self.append(text)
        self.moveCursor(QTextCursor.MoveOperation.End)


class MainWindow(QMainWindow):
    """
    Primary application window for the OpenModelica Simulation Runner.

    Layout:
        ┌─────────────────────────────────────┐
        │  Header                             │
        ├─────────────────────────────────────┤
        │  Simulation Parameters (GroupBox)   │
        │    • Executable path + Browse       │
        │    • Start Time (SpinBox)           │
        │    • Stop  Time (SpinBox)           │
        │    • [Run Simulation] button        │
        ├─────────────────────────────────────┤
        │  Output Console                     │
        ├─────────────────────────────────────┤
        │  Status Bar                         │
        └─────────────────────────────────────┘
    """

    APP_TITLE = "OpenModelica Simulation Runner"
    MIN_WIDTH = 780
    MIN_HEIGHT = 580

    def __init__(self) -> None:
        super().__init__()
        self._worker: SimulationWorker | None = None
        self._validator = SimulationInputValidator()
        self._build_ui()
        self._apply_stylesheet()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle(self.APP_TITLE)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(14)
        root_layout.setContentsMargins(20, 16, 20, 16)

        root_layout.addWidget(self._make_header())
        root_layout.addWidget(self._make_params_group())
        root_layout.addWidget(self._make_console_group())

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready — select an executable and set time bounds.")

    def _make_header(self) -> QLabel:
        header = QLabel("⚙  OpenModelica Simulation Runner")
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return header

    def _make_params_group(self) -> QGroupBox:
        group = QGroupBox("Simulation Parameters")
        group.setObjectName("paramsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        # -- Row 1: Executable --
        layout.addWidget(QLabel("Application (Executable)"))
        self._exec_selector = ExecutableSelector()
        layout.addWidget(self._exec_selector)

        # -- Row 2: Time inputs --
        time_row = QHBoxLayout()
        time_row.setSpacing(20)

        start_col = QVBoxLayout()
        start_col.addWidget(QLabel("Start Time  (0 ≤ start < stop < 5)"))
        self._start_spin = QSpinBox()
        self._start_spin.setRange(0, 4)
        self._start_spin.setValue(0)
        self._start_spin.setObjectName("spinBox")
        start_col.addWidget(self._start_spin)

        stop_col = QVBoxLayout()
        stop_col.addWidget(QLabel("Stop Time  (start < stop < 5)"))
        self._stop_spin = QSpinBox()
        self._stop_spin.setRange(1, 4)
        self._stop_spin.setValue(1)
        self._stop_spin.setObjectName("spinBox")
        stop_col.addWidget(self._stop_spin)

        time_row.addLayout(start_col)
        time_row.addLayout(stop_col)
        time_row.addStretch()
        layout.addLayout(time_row)

        # -- Row 3: Action buttons --
        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Run Simulation")
        self._run_btn.setObjectName("runBtn")
        self._run_btn.setFixedHeight(42)
        self._run_btn.clicked.connect(self._on_run_clicked)

        self._clear_btn = QPushButton("Clear Output")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setFixedHeight(42)
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return group

    def _make_console_group(self) -> QGroupBox:
        group = QGroupBox("Simulation Output")
        group.setObjectName("consoleGroup")
        layout = QVBoxLayout(group)
        self._console = OutputConsole()
        self._console.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._console)
        return group

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def _on_run_clicked(self) -> None:
        """Validate inputs, build a SimulationRunner, launch worker thread."""
        executable = self._exec_selector.executable_path
        start = self._start_spin.value()
        stop = self._stop_spin.value()

        errors = self._validator.validate(executable, start, stop)
        if errors:
            QMessageBox.warning(self, "Input Error", "\n".join(errors))
            return

        self._run_btn.setEnabled(False)
        self._status_bar.showMessage("Running simulation…")
        self._console.append_info(
            f"[INFO] Launching: {executable}  | startTime={start}  stopTime={stop}"
        )

        runner = SimulationRunner(executable, start, stop)
        self._worker = SimulationWorker(runner)
        self._worker.output_received.connect(self._console.append_output)
        self._worker.finished.connect(self._on_simulation_finished)
        self._worker.error_occurred.connect(self._on_simulation_error)
        self._worker.start()

    def _on_clear_clicked(self) -> None:
        self._console.clear()
        self._status_bar.showMessage("Output cleared.")

    def _on_simulation_finished(self, return_code: int) -> None:
        self._run_btn.setEnabled(True)
        if return_code == 0:
            self._console.append_success("[SUCCESS] Simulation completed (exit 0).")
            self._status_bar.showMessage("Simulation finished successfully.")
        else:
            self._console.append_error(
                f"[WARN] Simulation exited with code {return_code}."
            )
            self._status_bar.showMessage(f"Simulation ended — exit code {return_code}.")

    def _on_simulation_error(self, message: str) -> None:
        self._run_btn.setEnabled(True)
        self._console.append_error(f"[ERROR] {message}")
        self._status_bar.showMessage("Simulation failed to start.")
        QMessageBox.critical(self, "Launch Error", message)

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #e6edf3;
            }
            QLabel {
                color: #8b949e;
                font-size: 12px;
            }
            #headerLabel {
                color: #58a6ff;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 0;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 13px;
                font-weight: bold;
                color: #8b949e;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QLineEdit, #pathEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px 10px;
                color: #e6edf3;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
            }
            QSpinBox#spinBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px 10px;
                color: #e6edf3;
                font-size: 13px;
                min-width: 100px;
            }
            QSpinBox#spinBox:focus {
                border-color: #58a6ff;
            }
            QPushButton#runBtn {
                background-color: #238636;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 24px;
                min-width: 180px;
            }
            QPushButton#runBtn:hover { background-color: #2ea043; }
            QPushButton#runBtn:pressed { background-color: #1a7f37; }
            QPushButton#runBtn:disabled { background-color: #21262d; color: #484f58; }
            QPushButton#browseBtn, QPushButton#clearBtn {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                font-size: 12px;
                padding: 0 14px;
            }
            QPushButton#browseBtn:hover, QPushButton#clearBtn:hover {
                background-color: #30363d;
            }
            QTextEdit#outputConsole {
                background-color: #010409;
                border: 1px solid #21262d;
                border-radius: 4px;
                padding: 8px;
                font-family: "Courier New", monospace;
                font-size: 11px;
            }
            QStatusBar {
                background-color: #161b22;
                color: #8b949e;
                font-size: 11px;
                border-top: 1px solid #21262d;
            }
            QScrollBar:vertical {
                background: #0d1117;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                border-radius: 4px;
            }
        """)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("OpenModelica Simulation Runner")
    app.setOrganizationName("CipherxHub")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
