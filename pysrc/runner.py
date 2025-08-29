import platform
import shlex
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple, TypeVar

import psutil
from loguru import logger

T = TypeVar("T")


# Define namedtuples
class Result(NamedTuple):
    output: str
    type: str
    time: float
    memory: float


class RunProcessResult(NamedTuple):
    stdout: str
    stderr: str
    time: float
    memory: float
    status: str | None


def try_r(func: Callable[..., T], *args: any, default: T = None) -> T:
    """
    Executes a function with the provided arguments and returns its result.
    If an exception occurs during execution, returns a default value.
    Args:
        func (Callable[..., T]): The function to execute.
        *args (any): Arguments to pass to the function.
        default (T, optional): The value to return if an exception occurs.
            Defaults to None.
    Returns:
        T: The result of the function execution,
            or the default value if an exception occurs.
    """

    try:
        return func(*args)
    except Exception:
        return default


def run_p(
    cmd: list,
    inp: str = "",
    *,
    memory_limit: int = 256,
    timeout: int = 1,
    cwd: Path | None = None,
) -> RunProcessResult:
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
        shell=True if platform.system() == "Windows" else False,
    ) as p:  # set stdin to -1 for input and stdout stderr to -1 for capture output.
        try:
            child_process = p

            start = time.monotonic()
            p.stdin.write(inp)
            p.stdin.flush()
            p.stdin.close()
            max_memory = 0

            while True:
                state = p.poll()  # check process state
                if state is not None:
                    return RunProcessResult(
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=time.monotonic() - start,
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
                        time=time.monotonic() - start,
                        memory=max_memory,
                    )

                if time.monotonic() - start >= timeout:  # check timeout
                    try_r(child_process.kill)
                    try_r(child_process.terminate)
                    return RunProcessResult(
                        status="timeout",
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=time.monotonic() - start,
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
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    r_cmd = []
    for c in cmd:
        c: str

        r_cmd.append(
            c.format(
                file=str(file_path),
                fileWithoutExt=str(file_path.with_suffix("")),
                fileName=file_path.name,
                fileStem=file_path.stem,
                fileExt=file_path.suffix,
                fileParent=str(file_path.parent),
                fileParentName=file_path.parent.name,
                executable=executable,
            )
        )
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
    except Exception as e:
        return Result(output=str(e), type="runtime_error", time=0, memory=0)
    if status == "timeout":
        return Result(output=stdout, type="timeout", time=time, memory=memory)
    elif status == "memory_limit_exceeded":
        return Result(
            output=stdout, type="memory_limit_exceeded", time=time, memory=memory
        )

    if stderr:
        return Result(output=stderr, type="runtime_error", time=time, memory=memory)
    return Result(output=stdout, type="success", time=time, memory=memory)


def compile(file_path: Path, cmd: list | str, *, executable: str = "") -> None:
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    r_cmd = []
    for c in cmd:
        c: str

        r_cmd.append(
            c.format(
                file=str(file_path),
                fileWithoutExt=str(file_path.with_suffix("")),
                fileName=file_path.name,
                fileStem=file_path.stem,
                fileExt=file_path.suffix,
                fileParent=str(file_path.parent),
                fileParentName=file_path.parent.name,
                executable=executable,
            )
        )
    logger.debug(f"Compile command: {' '.join(r_cmd)}")
    try:
        subprocess.run(
            r_cmd,
            check=True,
            cwd=file_path.parent,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=True if platform.system() == "Windows" else False,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr) from e


def compile_c_cpp_builder(
    std: str = "c++", lang: str = "c++", flags: str = ["-O2", "-Wall", "-Wextra"]
) -> Callable[[Path], Path]:
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
    cmd = [version, "{file_name}"]
    return run(file_path, inp, cmd, memory_limit=memory_limit, timeout=timeout)
