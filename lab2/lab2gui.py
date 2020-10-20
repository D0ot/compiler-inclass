import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QIODevice
import subprocess


if __name__ == "__main__":
    app = QApplication(sys.argv)

    ui_file_name = "lab2.ui"
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        print("Cannot open {}: {}".format(ui_file_name, ui_file.errorString()))
        sys.exit(-1)
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    if not window:
        print(loader.errorString())
        sys.exit(-1)
    
    def llanalysis_clicked():
        print("llanalysis_clicked")
        raw_str = window.input_text_box.toPlainText().strip()
        raw_str = raw_str.replace(" ", "")
        str_list = raw_str.split('\n')
        backend_stdin = str(len(str_list)) + "\n"
        for x in str_list:
            backend_stdin = backend_stdin + "\n" + x 
        
        proc = subprocess.Popen('../build/lab2/lab2',stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        print(backend_stdin)
        proc.stdin.write(backend_stdin.encode())
        proc.stdin.close()
        proc.wait()
        result = proc.stdout.read()
        print(result.decode())

    window.llanalysis_button.clicked.connect(llanalysis_clicked)

    window.show()
    sys.exit(app.exec_())



