import sys
from pathlib import Path
from lineview.cli.main import app as cli_app

def _run_gui(path=None):
    from PySide6.QtWidgets import QApplication
    from lineview.gui.app import LineViewApp
    
    app = QApplication(sys.argv)
    window = LineViewApp()
    if path:
        window.open_file(Path(path))
    window.show()
    sys.exit(app.exec())

def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ["inspect", "measure", "fit", "lines", "compare", "demo", "--help"]:
        # Probably a file path, run GUI
        _run_gui(sys.argv[1])
    elif len(sys.argv) == 1:
        # No args, run GUI
        _run_gui()
    else:
        # Let typer handle it
        cli_app()

if __name__ == "__main__":
    main()
