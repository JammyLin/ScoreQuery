import sys
from PyQt5.QtWidgets import QApplication, QStyleFactory
from QueryWindow import QueryWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("fusion"))
    window = QueryWindow()
    window.show()
    sys.exit(app.exec_())
