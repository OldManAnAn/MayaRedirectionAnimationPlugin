import socket
import sys
from pathlib import Path


def run_in_maya(script_path):
    path = Path(script_path).resolve()
    code = path.read_text(encoding="utf-8")

    # Maya commandPort evaluates a complete newline-terminated command.
    command = "exec(" + repr(code) + ")\n"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 7001))
        sock.sendall(command.encode("utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python run_to_maya.py your_script.py")
        sys.exit(1)

    run_in_maya(sys.argv[1])
    print("脚本已发送到 Maya")
