"""
tests/test_simulation_runner.py
--------------------------------
Unit tests for SimulationRunner and SimulationInputValidator.

Run with:
    pytest tests/ -v
"""

import sys
import os

# Make app/ importable when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from simulation_runner import SimulationRunner
from validators import SimulationInputValidator


# ======================================================================
# SimulationRunner Tests
# ======================================================================


class TestSimulationRunnerBuildCommand:
    """Tests for SimulationRunner.build_command()"""

    def test_basic_command_structure(self, tmp_path):
        exe = tmp_path / "TwoConnectedTanks"
        exe.touch()
        runner = SimulationRunner(str(exe), 0, 3)
        cmd = runner.build_command()
        assert cmd[0] == str(exe.resolve())
        assert "-override" in cmd
        assert "startTime=0,stopTime=3" in cmd

    def test_extra_flags_appended(self, tmp_path):
        exe = tmp_path / "model"
        exe.touch()
        runner = SimulationRunner(str(exe), 1, 4, extra_flags=["-lv", "LOG_NLS"])
        cmd = runner.build_command()
        assert "-lv" in cmd
        assert "LOG_NLS" in cmd

    def test_start_stop_reflected_in_override(self, tmp_path):
        exe = tmp_path / "model"
        exe.touch()
        runner = SimulationRunner(str(exe), 2, 4)
        cmd = runner.build_command()
        override_val = cmd[cmd.index("-override") + 1]
        assert "startTime=2" in override_val
        assert "stopTime=4" in override_val


class TestSimulationRunnerExecute:
    """Tests for SimulationRunner.execute()"""

    def test_raises_file_not_found_for_missing_exe(self):
        runner = SimulationRunner("/nonexistent/binary", 0, 1)
        with pytest.raises(FileNotFoundError):
            runner.execute(lambda line: None)

    def test_output_streamed_to_callback(self, tmp_path):
        exe = tmp_path / "fake_model"
        # Create a shell script that prints a line and exits 0
        exe.write_text("#!/bin/sh\necho 'simulation ok'\n")
        exe.chmod(0o755)

        lines = []
        runner = SimulationRunner(str(exe), 0, 1)
        rc = runner.execute(lines.append)
        assert rc == 0
        assert any("simulation ok" in line for line in lines)

    def test_nonzero_exit_propagated(self, tmp_path):
        exe = tmp_path / "bad_model"
        exe.write_text("#!/bin/sh\nexit 42\n")
        exe.chmod(0o755)

        runner = SimulationRunner(str(exe), 0, 1)
        rc = runner.execute(lambda _: None)
        assert rc == 42


# ======================================================================
# SimulationInputValidator Tests
# ======================================================================


class TestSimulationInputValidator:
    """Tests for SimulationInputValidator.validate()"""

    def setup_method(self):
        self.v = SimulationInputValidator()

    def test_empty_executable_returns_error(self):
        errors = self.v.validate("", 0, 1)
        assert any("empty" in e.lower() for e in errors)

    def test_nonexistent_executable_returns_error(self):
        errors = self.v.validate("/no/such/file", 0, 1)
        assert any("not found" in e.lower() for e in errors)

    def test_start_equals_stop_invalid(self, tmp_path):
        exe = tmp_path / "m"
        exe.touch()
        errors = self.v.validate(str(exe), 2, 2)
        assert any("greater" in e.lower() for e in errors)

    def test_stop_gte_5_invalid(self, tmp_path):
        exe = tmp_path / "m"
        exe.touch()
        errors = self.v.validate(str(exe), 0, 5)
        assert any("less than 5" in e.lower() for e in errors)

    def test_valid_inputs_no_errors(self, tmp_path):
        exe = tmp_path / "m"
        exe.touch()
        errors = self.v.validate(str(exe), 0, 4)
        assert errors == []

    def test_negative_start_invalid(self, tmp_path):
        exe = tmp_path / "m"
        exe.touch()
        errors = self.v.validate(str(exe), -1, 3)
        assert any("≥ 0" in e or ">= 0" in e.lower() or "0" in e for e in errors)
