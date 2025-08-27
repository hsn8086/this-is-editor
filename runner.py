from collections import namedtuple
from pathlib import Path
import subprocess
import tempfile
import threading
import psutil
import time
from hashlib import sha256
from subprocess import Popen


# Define namedtuples
Result = namedtuple("Result", ["output", "type", "time", "memory"])
RunProcessResult = namedtuple(
    "RunProcessResult", ["stdout", "stderr", "time", "memory", "status"]
)


def write_thread(p: Popen, inp: str):
    p.stdin.write(inp)
    p.stdin.flush()
    p.stdin.close()


def run_p(
    cmd: list,
    inp: str = "",
    *,
    memory_limit: int = 256,
    timeout: int = 1,
    cwd: Path | None = None,
):
    # print(f"Running command: {' '.join(cmd)}")
    print(cmd, cwd)
    with Popen(
        cmd, text=True, stdin=-1, stdout=-1, stderr=-1, cwd=cwd
    ) as p:  # set stdin to -1 for input and stdout stderr to -1 for capture output.
        print(cmd)
        try:
            child_process = psutil.Process(
                p.pid
            )  # use psutil tu monitoring process status
            start = time.monotonic()
            threading.Thread(target=write_thread, args=(p, inp)).start()
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

                mem_use = child_process.memory_full_info().uss / (1024**2)
                max_memory = max(max_memory, mem_use)
                if mem_use > memory_limit:  # check memory
                    child_process.kill()
                    child_process.terminate()
                    return RunProcessResult(
                        status="memory_limit_exceeded",
                        stdout=p.stdout.read(),
                        stderr=p.stderr.read(),
                        time=time.monotonic() - start,
                        memory=max_memory,
                    )

                if time.monotonic() - start >= timeout:  # check timeout
                    child_process.kill()
                    child_process.terminate()
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
            p.terminate()
            p.wait()  # 等待子进程完全退出


def run(
    file_path: Path,
    inp: str,
    cmd: str,
    *,
    memory_limit: int = 256,
    timeout: int = 1,
):
    try:
        rst = run_p(
            cmd.format(file_name=str(file_path)).split(),
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


def compile_c_cpp_builder(
    std: str = "c++", lang="c++", flags: str = ["-O2", "-Wall", "-Wextra"]
):
    def compile_func(file_path: Path):
        output_file = file_path.stem + ".out"
        cmd = [
            "g++",
            f"-x{lang}",
            file_path.name,
            "-o",
            output_file,
            "-std=" + std,
        ] + flags
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(file_path).parent
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
):
    cmd = "{file_name}"
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
):
    cmd = f"{version} {{file_name}}"
    return run(file_path, inp, cmd, memory_limit=memory_limit, timeout=timeout)
