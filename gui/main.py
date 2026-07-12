import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow, ORG_NAME, APP_NAME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(f"{APP_NAME} - Compilateur Quantique")
    app.setOrganizationName(ORG_NAME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
