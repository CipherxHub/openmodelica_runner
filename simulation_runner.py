"""
simulation_runner.py
--------------------
Encapsulates the logic for launching a compiled OpenModelica executable
with start/stop time arguments via the OMC simulation flag ``-override``.

Reference:
    https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/
    simulationflags.html#simflag-override
"""

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Optional


class SimulationRunner:
    """
    Responsible for constructing the CLI command and running the
    OpenModelica compiled executable in a subprocess.

    Parameters
    ----------
    executable : str
        Absolute or relative path to the compiled OM executable.
    start_time : int
        Simulation start time (0 ≤ start_time < stop_time < 5).
    stop_time : int
        Simulation stop time (start_time < stop_time < 5).
    extra_flags : list[str] | None
        Optional additional simulation flags forwarded verbatim.

    Example
    -------
    >>> runner = SimulationRunner("/path/to/TwoConnectedTanks", 0, 3)
    >>> runner.execute(print)
    """

    _OVERRIDE_FLAG = "-override"

    def __init__(
        self,
        executable: str,
        start_time: int,
        stop_time: int,
        extra_flags: Optional[list[str]] = None,
    ) -> None:
        self.executable = Path(executable).resolve()
        self.start_time = start_time
        self.stop_time = stop_time
        self.extra_flags: list[str] = extra_flags or []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_command(self) -> list[str]:
        """
        Construct the full command list to be passed to ``subprocess``.

        Returns
        -------
        list[str]
            E.g. ["/path/to/TwoConnectedTanks",
                  "-override", "startTime=0,stopTime=3"]
        """
        override_value = (
            f"startTime={self.start_time},stopTime={self.stop_time}"
        )
        cmd: list[str] = [
            str(self.executable),
            self._OVERRIDE_FLAG,
            override_value,
        ]
        cmd.extend(self.extra_flags)
        return cmd

    def execute(self, output_callback: Callable[[str], None]) -> int:
        """
        Launch the executable and stream each output line to *output_callback*.

        Parameters
        ----------
        output_callback : Callable[[str], None]
            Called with each decoded line from stdout / stderr.

        Returns
        -------
        int
            Process return code (0 = success).

        Raises
        ------
        FileNotFoundError
            If the executable path does not exist.
        PermissionError
            If the executable is not marked as executable on POSIX.
        OSError
            For other OS-level launch failures.
        """
        if not self.executable.exists():
            raise FileNotFoundError(
                f"Executable not found: {self.executable}"
            )

        cmd = self.build_command()
        output_callback(f"$ {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,      # merge stderr → stdout
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Stream output line by line
        assert process.stdout is not None
        for line in process.stdout:
            output_callback(line.rstrip())

        process.wait()
        return process.returncode

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"SimulationRunner(executable={self.executable!r}, "
            f"start_time={self.start_time}, stop_time={self.stop_time})"
        )
