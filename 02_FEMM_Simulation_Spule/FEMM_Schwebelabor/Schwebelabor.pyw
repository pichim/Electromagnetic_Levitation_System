"""Windows-Start ohne Konsolenfenster. Zum Starten doppelklicken."""
from pathlib import Path
import ctypes
import os
import runpy
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent


def notice(message):
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, message, "FEMM Schwebelabor", 0x10)


def main():
    # Auch ein Aufruf mit python.exe wird an denselben Interpreter ohne
    # Konsole übergeben. Kein zweiter Python-Interpreter aus dem PATH nötig.
    if os.name == "nt" and Path(sys.executable).name.lower() != "pythonw.exe":
        interpreter = Path(sys.executable).with_name("pythonw.exe")
        if not interpreter.is_file():
            notice("pythonw.exe fehlt neben dem verwendeten Python-Interpreter.")
            return
        subprocess.Popen([str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]],
                         cwd=str(ROOT), creationflags=subprocess.CREATE_NO_WINDOW)
        return
    if not (ROOT/"app.py").is_file():
        notice("Alle Dateien aus dem ZIP entpacken. Schwebelabor.pyw muss neben app.py liegen.")
        return
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    log_path = ROOT/"schwebelabor_start.log"
    try:
        log = log_path.open("a", encoding="utf-8", buffering=1)
    except OSError:
        log = open(os.devnull, "w", encoding="utf-8")
    previous_stdout, previous_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = log
    try:
        runpy.run_path(str(ROOT/"app.py"), run_name="__main__")
    except SystemExit as error:
        if error.code not in (None, 0): traceback.print_exc()
    except Exception:
        traceback.print_exc()
        notice("Das Programm konnte nicht gestartet werden.\n"
               "Details stehen in schwebelabor_start.log im Programmordner.")
    finally:
        sys.stdout, sys.stderr = previous_stdout, previous_stderr
        log.close()


if __name__ == "__main__":
    main()
