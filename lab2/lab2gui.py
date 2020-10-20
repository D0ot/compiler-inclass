import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QIODevice
import subprocess





def parseTheOutput(output_str):
    
    def parseProduction(opstr):
        pro_start = "PRODUCTIONS_START#"
        pro_end = "PRODUCTIONS_END#"
        start_index = opstr.index(pro_start)
        end_index = opstr.index(pro_end)
        i = start_index + 1
        productions = []
        while(i != end_index):
            productions = productions + [opstr[i]]
            i = i + 1
        return productions


    def parseFirst(opstr):
        fst_start = "FIRST_START#"
        fst_end = "FIRST_END#"
        start_index = opstr.index(fst_start)
        end_index = opstr.index(fst_end)
        i = start_index + 1
        first = {}
        while(i != end_index):
            tmp = opstr[i].split(":")
            if(len(tmp) == 2):
                first[tmp[0]] = tmp[1][:-1]
            i = i + 1
        return first
    
    def parseFollow(opstr):
        fol_start = "FOLLOW_START#"
        fol_end = "FOLLOW_END#"
        start_index = opstr.index(fol_start)
        end_index = opstr.index(fol_end)
        i = start_index + 1
        follow = {}
        while(i != end_index):
            tmp = opstr[i].split(":")
            if(len(tmp) == 2 and tmp[1] != ""):
                follow[tmp[0]] = tmp[1][:-1]
            i = i + 1
        return follow
    
    def parseNul(opstr):
        nul_start = "NULLABLE_START#"
        nul_end = "NULLABLE_END#"
        start_index = opstr.index(nul_start)
        end_index = opstr.index(nul_end)
        i = start_index + 1
        nullable = {}
        while(i != end_index):
            tmp = opstr[i].split(":")
            if(len(tmp) == 2):
                nullable[tmp[0]] = tmp[1]
            i = i + 1
        return nullable 

    
    def parseTab(opstr):
        tab_start = "TABLE_START#"
        tab_end = "TABLE_END#"
        start_index = opstr.index(tab_start)
        end_index = opstr.index(tab_end)
        i = start_index + 1
        table = []
        while(i != end_index):
            table = table + [opstr[i]]
            i = i + 1
        return table

    
    def parseProcess(opstr):
        proc_start = "PROCESS_START#"
        proc_end = "PROCESS_END#"
        start_index = opstr.index(proc_start)
        end_index = opstr.index(proc_end)
        i = start_index + 1
        stack = []
        input_str = []
        accord_action = []
        while(i != end_index):
            three_str = opstr[i].strip().split("\t")
            stack = stack + [three_str[0]]
            input_str = input_str + [three_str[1]]
            accord_action = accord_action + [three_str[2]]
            i = i + 1
        return (stack, input_str, accord_action)

    tmp_lines = output_str.split("\n")

    

    return (parseProduction(tmp_lines)
    ,parseFirst(tmp_lines)
    ,parseFollow(tmp_lines)
    ,parseNul(tmp_lines)
    ,parseTab(tmp_lines)
    ,parseProcess(tmp_lines))



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
            backend_stdin = backend_stdin + x + "\n"
        backend_stdin = backend_stdin + window.sentence_lineedit.text().strip()
        proc = subprocess.Popen('../build/lab2/lab2',stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        print("###")
        print(backend_stdin)
        print("###")
        proc.stdin.write(backend_stdin.encode())
        proc.stdin.close()
        proc.wait()
        result = proc.stdout.read().decode()
        #print(result)
        parseTheOutput(result)

    window.llanalysis_button.clicked.connect(llanalysis_clicked)
    window.show()
    sys.exit(app.exec_())