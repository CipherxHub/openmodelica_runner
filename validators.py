"""
validators.py
-------------
Input validation logic for the OpenModelica Simulation Runner GUI.

Keeping validation separate from the UI and from SimulationRunner follows
the Single-Responsibility Principle and makes unit-testing straightforward.
"""

from pathlib import Path


class SimulationInputValidator:
    """
    Validates the three user-facing inputs before launching a simulation.

    Constraints enforced
    --------------------
    * Executable path must be a non-empty string pointing to an existing file.
    * 0 ≤ start_time < stop_time < 5  (as per task specification).

    Usage
    -----
    >>> v = SimulationInputValidator()
    >>> v.validate("", 0, 0)
    ['Executable path must not be empty.',
     'Stop time must be greater than start time.',
     'Stop time must be less than 5.']
    """

    TIME_MAX_EXCLUSIVE: int = 5   # stop time must be < this value

    def validate(
        self,
        executable: str,
        start_time: int,
        stop_time: int,
    ) -> list[str]:
        """
        Run all validation rules and return a list of human-readable errors.

        Parameters
        ----------
        executable : str
            Path to the compiled OM binary.
        start_time : int
            Requested simulation start time.
        stop_time : int
            Requested simulation stop time.

        Returns
        -------
        list[str]
            Empty list means all inputs are valid.
        """
        errors: list[str] = []
        errors.extend(self._validate_executable(executable))
        errors.extend(self._validate_times(start_time, stop_time))
        return errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_executable(path: str) -> list[str]:
        errors: list[str] = []
        if not path:
            errors.append("Executable path must not be empty.")
            return errors   # no point checking further

        resolved = Path(path)
        if not resolved.exists():
            errors.append(f"Executable not found: '{path}'.")
        elif not resolved.is_file():
            errors.append(f"Path is not a file: '{path}'.")
        return errors

    def _validate_times(self, start: int, stop: int) -> list[str]:
        errors: list[str] = []
        if start < 0:
            errors.append("Start time must be ≥ 0.")
        if stop <= start:
            errors.append("Stop time must be greater than start time.")
        if stop >= self.TIME_MAX_EXCLUSIVE:
            errors.append(
                f"Stop time must be less than {self.TIME_MAX_EXCLUSIVE}."
            )
        return errors
