"""Provides utilities for running code.

It includes functions for executing Python and C/C++ code,
monitoring memory and time usage, and handling compilation errors.
"""

import platform
import shlex
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple, TypeVar

import psutil
from loguru import logger

from .utils import formatter as fmt

T = TypeVar("T")


# Define namedtuples
class Result(NamedTuple):
    """Represents the result of running code.

    Attributes:
        output (str): The output from the process.
        type (str): The result type (e.g., 'success', 'timeout').
        time (float): Execution time in seconds.
        memory (float): Peak memory usage in MB.

    """

    output: str
    type: str
    time: float
    memory: float


class RunProcessResult(NamedTuple):
    """Represents the result of running a process.

    Attributes:
        stdout (str): Standard output.
        stderr (str): Standard error.
        time (float): Execution time in seconds.
        memory (float): Peak memory usage in MB.
        status (str | None): Status string or None.

    """

    stdout: str
    stderr: str
    time: float
    memory: float
    status: str | None


def try_r(func: Callable[..., T], *args: any, default: T = None) -> T:
    """Execute a function and return its result, or a default value on exception.

    Args:
        func (Callable[..., T]): Function to execute.
        *args (any): Arguments for the function.
        default (T, optional): Value to return if an exception occurs.

    Returns:
        T: Result of the function or the default value.

    """
    try:
        return func(*args)
    except Exception:  # noqa: BLE001
        return default


def get_time(child_process: psutil.Popen) -> float:
    """Get the elapsed time of a child process.

    Args:
        child_process (psutil.Process): The child process to monitor.

    Returns:
        float: The elapsed time in seconds.

    """
    try:
        cpu_times = child_process.cpu_times()
        return (
            cpu_times.children_user
            + cpu_times.children_system
            + cpu_times.user
            + cpu_times.system
        )
    except psutil.NoSuchProcess:
        return 0.0


def run_p(
    cmd: list,
    inp: str = "",
    *,
    memory_limit: int = 256,
    timeout: int = 1,
    cwd: Path | None = None,
) -> RunProcessResult:
    """Run a process with resource limits and capture output.

    Args:
        cmd (list): Command to execute.
        inp (str): Input to pass to stdin.
        memory_limit (int): Memory limit in MB.
        timeout (int): Timeout in seconds.
        cwd (Path | None): Working directory.

    Returns:
        RunProcessResult: Result of the process execution.

    """
    logger.debug(f"Run command: {' '.join(cmd)}")
    logger.debug(f"Working directory: {cwd}")
    with psutil.Popen(
        cmd,
        text=True,
        stdin=-1,
        stdout=-1,
        stderr=-1,
        cwd=cwd,
        creationflags=subprocess.CREATE_NO_WINDOW
        if platform.system() == "Windows"
        else 0,
        shell=platform.system() == "Windows",
    ) as p:  # set stdin to -1 for input and stdout stderr to -1 for capture output.
        try:
            child_process = p

            start = time.monotonic()
            p.stdin.write(inp)
            p.stdin.flush()
            p.stdin.close()
            max_memory = 0
            cpu_time = 0
            while True:
                state = p.poll()  # check process state
                cpu_time = max(get_time(child_process), cpu_time)
                if state is not None:
                    return RunProcessResult(
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=cpu_time,
                        memory=max_memory,
                        status=None,
                    )
                mem_use = 0
                if mem := try_r(child_process.memory_full_info):
                    mem_use = mem.uss / (1024**2)

                max_memory = max(max_memory, mem_use)
                if mem_use > memory_limit:  # check memory
                    try_r(child_process.kill)
                    try_r(child_process.terminate)
                    return RunProcessResult(
                        status="memory_limit_exceeded",
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=cpu_time,
                        memory=max_memory,
                    )

                if (
                    time.monotonic() - start >= timeout * 2 or cpu_time >= timeout
                ):  # check timeout
                    try_r(child_process.kill)
                    try_r(child_process.terminate)
                    return RunProcessResult(
                        status="timeout",
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=cpu_time,
                        memory=max_memory,
                    )
        finally:
            p.stdin.close()
            p.stdout.close()
            p.stderr.close()
            try_r(child_process.kill)
            try_r(child_process.terminate)
            p.wait()  # wait for process to terminate


def run(
    file_path: Path,
    inp: str,
    cmd: list | str,
    *,
    executable: str = "",
    memory_limit: int = 256,
    timeout: int = 1,
) -> Result:
    """Run code with the given command and input.

    Args:
        file_path (Path): Path to the code file.
        inp (str): Input for the code.
        cmd (list | str): Command to execute.
        executable (str): Executable name.
        memory_limit (int): Memory limit in MB.
        timeout (int): Timeout in seconds.

    Returns:
        Result: Result of code execution.

    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    r_cmd = []
    for c in cmd:
        c: str

        r_cmd.append(fmt(c, file_path=file_path, executable=executable))
    try:
        rst = run_p(
            r_cmd,
            inp=inp,
            timeout=timeout,
            memory_limit=memory_limit,
            cwd=file_path.parent,
        )
        stdout = rst.stdout
        stderr = rst.stderr
        time = rst.time
        memory = rst.memory
        status = rst.status
    except (subprocess.CalledProcessError, OSError) as e:
        return Result(output=str(e), type="runtime_error", time=0, memory=0)
    if status == "timeout":
        return Result(output=stdout, type="timeout", time=time, memory=memory)
    if status == "memory_limit_exceeded":
        return Result(
            output=stdout,
            type="memory_limit_exceeded",
            time=time,
            memory=memory,
        )

    if stderr:
        return Result(output=stderr, type="runtime_error", time=time, memory=memory)
    return Result(output=stdout, type="success", time=time, memory=memory)


def run_compilation(file_path: Path, cmd: list | str, *, executable: str = "") -> None:
    """Compile code using the given command.

    Args:
        file_path (Path): Path to the code file.
        cmd (list | str): Compilation command.
        executable (str): Executable name.

    Raises:
        RuntimeError: If compilation fails.

    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    r_cmd = []
    for c in cmd:
        c: str

        r_cmd.append(fmt(c, file_path=file_path, executable=executable))
    logger.debug(f"Compile command: {' '.join(r_cmd)}")
    try:
        subprocess.run(
            r_cmd,
            check=True,
            cwd=file_path.parent,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=platform.system() == "Windows",
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr) from e


def compile_c_cpp_builder(
    std: str = "c++",
    lang: str = "c++",
    flags: list | None = None,
) -> Callable[[Path], Path]:
    """Return a function to compile C/C++ files with given options.

    Args:
        std (str): Standard version (e.g., 'c++').
        lang (str): Language ('c++' or 'c').
        flags (list[str] | None): Compilation flags.

    Returns:
        Callable[[Path], Path]: Compilation function.

    """
    if flags is None:
        flags = ["-O2", "-Wall", "-Wextra"]

    def compile_func(file_path: Path) -> Path:
        output_file = file_path.stem + ".out"
        cmd = [
            "g++",
            f"-x{lang}",
            file_path.name,
            "-o",
            output_file,
            "-std=" + std,
            *flags,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(file_path).parent,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            check=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return Path(file_path).parent / output_file

    return compile_func


def run_c_cpp(
    file_path: Path,
    inp: str,
    memory_limit: int = 256,
    timeout: int = 1,
) -> Result:
    """Run a compiled C/C++ binary.

    Args:
        file_path (Path): Path to the binary.
        inp (str): Input for the program.
        memory_limit (int): Memory limit in MB.
        timeout (int): Timeout in seconds.

    Returns:
        Result: Result of execution.

    """
    cmd = ["{file_name}"]
    return run(
        file_path,
        inp,
        cmd,
        memory_limit=memory_limit,
        timeout=timeout,
    )


def run_python(
    file_path: Path,
    inp: str,
    memory_limit: int = 256,
    timeout: int = 1,
    *,
    version: str = "python3.10",
) -> Result:
    """Run a Python file with the specified version.

    Args:
        file_path (Path): Path to the Python file.
        inp (str): Input for the program.
        memory_limit (int): Memory limit in MB.
        timeout (int): Timeout in seconds.
        version (str): Python interpreter version.

    Returns:
        Result: Result of execution.

    """
    cmd = [version, "{file_name}"]
    return run(file_path, inp, cmd, memory_limit=memory_limit, timeout=timeout)
