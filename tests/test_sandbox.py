from typing import Any
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sandbox.isolate import IsolateCodeSandbox
from sandbox.schema import (
    SandboxSubmission,
    SandboxSubmissionLanguage,
    SandboxSubmissionStatus,
)


@pytest.fixture
def sandbox_submission():
    return SandboxSubmission(
        id=1234567,
        language=SandboxSubmissionLanguage(
            source_file="main.py",
            compile_cmd="python -m py_compile main.py",
            run_cmd="python main.py",
        ),
        source_code="print('hello')",
        stdin="",
        expected_output="hello\n",
        cpu_time_limit=1,
        cpu_extra_time=1,
        wall_time_limit=2,
        stack_limit=64 * 1024,
        memory_limit=128 * 1024,
        max_file_size=1024,
        max_processes_and_or_threads=1,
        limit_per_process_and_thread_cpu_time_usages=False,
        limit_per_process_and_thread_memory_usages=False,
    )


class TestSandbox:
    def test_process_and_execute_runs_pipeline_on_success(
        self, sandbox_submission: SandboxSubmission
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        sandbox.initialize_workdirs = MagicMock()
        sandbox.compile_code = MagicMock(return_value=True)
        sandbox.run_code = MagicMock()
        sandbox.verify_result = MagicMock()
        sandbox.do_cleanup = MagicMock()

        sandbox.process_and_execute()

        sandbox.initialize_workdirs.assert_called_once_with()
        sandbox.compile_code.assert_called_once_with()
        sandbox.run_code.assert_called_once_with()
        sandbox.verify_result.assert_called_once_with()
        sandbox.do_cleanup.assert_called_once_with()

    def test_process_and_execute_marks_compilation_error(
        self, sandbox_submission: SandboxSubmission
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        sandbox.initialize_workdirs = MagicMock()
        sandbox.compile_code = MagicMock(return_value=False)
        sandbox.run_code = MagicMock()
        sandbox.verify_result = MagicMock()
        sandbox.do_cleanup = MagicMock()

        sandbox.process_and_execute()

        assert sandbox.submission.status == SandboxSubmissionStatus.comerr
        sandbox.run_code.assert_not_called()
        sandbox.verify_result.assert_not_called()
        sandbox.do_cleanup.assert_called_once_with()

    def test_get_metadata_parses_metadata_file(
        self, sandbox_submission: SandboxSubmission, tmp_path: Path
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        sandbox.metadata_file = tmp_path / "metadata.txt"
        sandbox.metadata_file.write_text(
            "time:0.01\nstatus:RE\nmessage:boom\nexitcode:1\n", encoding="utf-8"
        )

        metadata = sandbox.get_metadata()

        assert metadata == {
            "time": "0.01",
            "status": "RE",
            "message": "boom",
            "exitcode": "1",
        }

    def test_verify_result_updates_submission_fields(
        self, sandbox_submission: SandboxSubmission, tmp_path: Path
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        sandbox.stdout_file = tmp_path / "stdout.txt"
        sandbox.stderr_file = tmp_path / "stderr.txt"
        sandbox.metadata_file = tmp_path / "metadata.txt"

        sandbox.stdout_file.write_text("hello\n", encoding="utf-8")
        sandbox.stderr_file.write_text("", encoding="utf-8")
        sandbox.metadata_file.write_text(
            "\n".join(
                [
                    "time:0.12",
                    "time-wall:0.20",
                    "cg-mem:512",
                    "exitcode:0",
                    "exitsig:0",
                    "message:ok",
                    "status:",
                ]
            ),
            encoding="utf-8",
        )
        sandbox.extract_status = MagicMock(return_value=SandboxSubmissionStatus.acc)

        sandbox.verify_result()

        assert sandbox.submission.stdout == "hello\n"
        assert sandbox.submission.stderr == ""
        assert sandbox.submission.time == 0.12
        assert sandbox.submission.wall_time == 0.2
        assert sandbox.submission.memory == 512
        assert sandbox.submission.exit_code == 0
        assert sandbox.submission.exit_signal == 0
        assert sandbox.submission.message == "ok"
        assert sandbox.submission.status == SandboxSubmissionStatus.acc
        sandbox.extract_status.assert_called_once_with("", 0)

    @pytest.mark.parametrize(
        ("status", "exit_signal", "expected_status"),
        [
            ("TO", 0, SandboxSubmissionStatus.tle),
            ("SG", 11, SandboxSubmissionStatus.sigsegv),
            ("SG", 25, SandboxSubmissionStatus.sigxfsz),
            ("SG", 8, SandboxSubmissionStatus.sigfpe),
            ("SG", 6, SandboxSubmissionStatus.sigabrt),
            ("SG", 9, SandboxSubmissionStatus.mle),
            ("SG", 1, SandboxSubmissionStatus.other),
        ],
    )
    def test_extract_status_handles_timeout_and_signals(
        self,
        sandbox_submission: SandboxSubmission,
        status: str,
        exit_signal: int,
        expected_status: Any,
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        assert sandbox.extract_status(status, exit_signal) == expected_status

    def test_extract_status_handles_runtime_errors(
        self, sandbox_submission: SandboxSubmission
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)

        sandbox.submission.stderr = "RecursionError: maximum recursion depth exceeded"
        assert sandbox.extract_status("RE", 0) == SandboxSubmissionStatus.rf

        sandbox.submission.stderr = "ValueError: bad input"
        assert sandbox.extract_status("RE", 0) == SandboxSubmissionStatus.nzec

    @pytest.mark.parametrize(
        ("message", "expected_status"),
        [
            (
                "execve(/box/run.sh): Exec format error",
                SandboxSubmissionStatus.exeerr,
            ),
            (
                "execve(/box/run.sh): No such file or directory",
                SandboxSubmissionStatus.exeerr,
            ),
            (
                "execve(/box/run.sh): Permission denied",
                SandboxSubmissionStatus.exeerr,
            ),
            ("sandbox broke unexpectedly", SandboxSubmissionStatus.boxerr),
        ],
    )
    def test_extract_status_handles_box_errors(
        self,
        sandbox_submission: SandboxSubmission,
        message: str,
        expected_status: str,
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)
        sandbox.submission.message = message

        assert sandbox.extract_status("XX", 0) == expected_status

    def test_extract_status_handles_output_comparison(
        self, sandbox_submission: SandboxSubmission
    ):
        sandbox = IsolateCodeSandbox(sandbox_submission)

        sandbox.submission.expected_output = None
        assert sandbox.extract_status("", 0) == SandboxSubmissionStatus.acc

        sandbox.submission.expected_output = "hello\n"
        sandbox.submission.stdout = "hello\n"
        assert sandbox.extract_status("", 0) == SandboxSubmissionStatus.acc

        sandbox.submission.stdout = "goodbye\n"
        assert sandbox.extract_status("", 0) == SandboxSubmissionStatus.wans
