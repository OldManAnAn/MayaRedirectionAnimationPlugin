"""Send a Python file to a running Maya commandPort."""
from pathlib import Path
import socket
import sys

HOST = "127.0.0.1"
PORT = 7001

def run_in_maya(script_path: str) -> None:
    path = Path(script_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    source = path.read_text(encoding="utf-8")
    command = "exec(" + repr(source) + ", globals())"
    with socket.create_connection((HOST, PORT), timeout=3) as connection:
        connection.sendall(command.encode("utf-8"))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法: python run_to_maya.py <maya_script.py>")
    try:
        run_in_maya(sys.argv[1])
    except ConnectionRefusedError:
        raise SystemExit("无法连接 Maya，请先在 Maya Script Editor 开启 commandPort。")
    print(f"已发送到 Maya: {Path(sys.argv[1]).resolve()}")
