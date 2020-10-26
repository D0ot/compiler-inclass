import sys
from copy import copy

from PySide2.QtCore import *
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import *
from PySide2.QtUiTools import *
from graphviz import Digraph

class Token:
    '''Token is represented as a string internally'''
    TypeTerminal = 0
    TypeNonTerminal = 1
    def __init__(self, t:str, token_type:int):
        self.val = t
        self.type = token_type
    
    def isTerminal(self):
        return self.type == Token.TypeTerminal
    
    def isNonTerminal(self):
        return self.type == Token.TypeNonTerminal
    
    def __str__(self) -> str:
        string_table = ["Term", "NonT"]
        return "({}, \'{}\')".format(string_table[self.type], self.val)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Token):
            raise TypeError("compare between different types{}".format(type(other)))
        else:
            return self.val == other.val and self.type == other.type
    def __hash__(self) -> int:
        return hash(self.val)

class TokenTable:
    def error(self, st:str):
        sys.stderr.write("TokenTable Error : {}".format(st))

    def __init__(self):
        self.tokens = {}

    def AddToken(self, token:Token):
        ''' Overwrites may occur '''
        if token.val in self.tokens and self.tokens[token.val].type == Token.TypeNonTerminal:
            return self.tokens[token.val]
        else:
            self.tokens[token.val] = token
            return token
    
    def getToken(self, t:str) -> Token:
        if t in self.tokens:
            return self.tokens[t]
        else:
            return None
    
    def terminalCount(self):
        cnt = 0
        for v in self.tokens.values():
            if v.isTerminal():
                cnt += 1
        return cnt


    def nonTerminalCount(self):
        cnt = 0
        for v in self.tokens.values():
            if v.isNonTerminal():
                cnt += 1
        return cnt


    def isTerminal(self, t:str):
        return t in self.tokens and self.tokens[t].type == Token.TypeTerminal

    def isNonTerminal(self, t:str):
        return t in self.tokens and self.tokens[t].type == Token.TypeNonTerminal
    
    def inTable(self, t:str):
        return t in self.tokens
    
    def __str__(self) -> str:
        return str(self.tokens)

    def __repr__(self) -> str:
        return self.__str__()
class Production:
    def error(self, st:str):
        sys.stderr.write("Production error : {}".format(st))

    def __init__(self, p:str, ttab:TokenTable):
        self.status = True
        arrow_index = p.find("->")
        if arrow_index == -1:
            self.status = False
            self.error("1")
            return
        left_part = p[:arrow_index]
        if len(left_part) == 0:
            self.status = False
            self.error("2")
            return
        right_part = p[arrow_index+2:]

        left_parts = left_part.strip().split(' ')
        if(len(left_parts) != 1):
            self.status = False
            self.error("3")
            return
        
        left_token = Token(left_parts[0], Token.TypeNonTerminal)
        ttab.AddToken(left_token)
        self.left = left_token.val

        right_parts = right_part.strip().split('|')
        if len(right_parts) == 0:
            self.status = False
            self.error("4")
            return

        self.rights = []
        for x in right_parts:
            ts = x.split(' ')
            tmp = []
            for y in ts:
                if(y == ""):
                    continue
                tmp_token = Token(y.strip(), Token.TypeTerminal)
                ttab.AddToken(tmp_token)
                tmp.append(tmp_token.val)
            self.rights.append(tmp) 
    
    def __str__(self) -> str:
        outstr = ""
        outstr += self.left + " -> "
        for x in self.rights:
            for y in x:
                outstr += y + " "
            outstr = outstr + "| "
        return outstr[:-2]

    def __repr__(self) -> str:
        return self.__str__()

class Item:
    def __init__(self, left_token, right_tokens, pos, preview_token):
        self.left_token = left_token
        self.pos = pos
        self.right_tokens = right_tokens
        self.preview_token = preview_token
    
    # used to calculate closure
    def closureExtendable(self) -> bool:
        return self.pos < len(self.right_tokens) and self.right_tokens[self.pos].isNonTerminal()

    # used to calculate GO(...) function
    def closureGoable(self) -> bool:
        return self.pos != len(self.right_tokens)
    
    def canShift(self) -> bool:
        return self.pos < len(self.right_tokens) and self.right_tokens[self.pos].isTerminal()
    
    def canReduce(self) -> bool:
        return self.pos == len(self.right_tokens)
    
    def __str__(self) -> str:
        outstr = "[ {} -> ".format(self.left_token.val)
        i = 0
        once_flag = True
        while i < len(self.right_tokens):
            if i == self.pos and once_flag:
                outstr += "• "
                once_flag = False
            else:
                outstr += self.right_tokens[i].val + " "
                i = i + 1
        if once_flag:
            outstr = outstr[:-1] + " •"
        outstr += ", {} ]".format(self.preview_token.val)
        return outstr

    def __repr__(self) -> str:
        return self.__str__()
    
    def __hash__(self) -> int:
        return hash(self.__str__())
    
    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Item):
            raise TypeError("compare different types")
        return self.__repr__() == o.__repr__()
    

class FirstSets:


    def __init__(self, productions, ttab:TokenTable, eplision):
        self.eplision = eplision
        self.first_sets = {}
        self.nullable = {}

        tokens = ttab.tokens
        for x in tokens.keys():
            token = tokens[x]
            self.nullable[token] = False

            if token.isTerminal():
                self.first_sets[token] = {token}
            else:
                self.first_sets[token] = set()
        
        self.nullable[eplision] = True
        self.first_sets[eplision] = set()


        changed_in_this_iter = True
        while(changed_in_this_iter):
            changed_in_this_iter = False

            for prod in productions:
                for candi_strs in productions[prod].rights:

                    left_token = ttab.getToken(productions[prod].left)
                    old_len = len(self.first_sets[left_token])
                    old_nullable = self.nullable[left_token]
                    
                    candi_tokens = [ttab.getToken(x) for x in candi_strs]

                    i = 0
                    while i < len(candi_tokens) and self.nullable[candi_tokens[i]]:
                        self.first_sets[left_token] = self.first_sets[left_token].union(self.first_sets[candi_tokens[i]])
                        i = i + 1

                    if i < len(candi_tokens):
                        self.first_sets[left_token] = self.first_sets[left_token].union(self.first_sets[candi_tokens[i]])
                    else:
                        self.nullable[left_token] = True
                    
                    if old_len != len(self.first_sets[left_token]) or old_nullable != self.nullable[left_token]:
                        changed_in_this_iter = True

        for x in self.first_sets:
            if eplision in self.first_sets[x]:
                self.first_sets[x].remove(eplision)
                

    def queryFirst(self, token):
        if token in self.first_sets:
            return self.first_sets[token]
        else:
            raise ValueError("queryFirst not found")

    def queryNullable(self, token):
        if token in self.nullable:
            return self.nullable[token]
        else:
            raise ValueError("queryNullable not found")
    
    def queryFirstOfSentence(self, tokens):
        ret = set()
        for x in tokens:
            ret = ret.union(self.queryFirst(x))
            if not self.queryNullable(x):
                break
        return ret
    
    def __str__(self) -> str:
        return str(self.first_sets) + str(self.nullable)


class LRAnalyzer:

    class ActionType:
        Shift = 0
        Reduce = 1

    ''' productions are special, indexed by string '''

    def __init__(self, pstr: list, eplision_str, argument_str, guard_str):

        self.productions = {}
        self.items = {}
        self.ttab = TokenTable()
        self.eplision = Token(eplision_str, Token.TypeTerminal)

        orginal_first_prod = Production(pstr[0], self.ttab)
        arguemnted_first_str = argument_str + " -> " + orginal_first_prod.left
        argumented_pstr = [arguemnted_first_str] + pstr


        for x in argumented_pstr:
            prod = Production(x, self.ttab)
            self.productions[prod.left] = prod
        
        self.eplision_token = self.ttab.getToken(eplision_str)
        self.argument_token = self.ttab.getToken(argument_str)
        self.orginal_start_token = self.ttab.getToken(self.productions[self.argument_token.val].rights[0][0])
        self.first_sets = FirstSets(self.productions, self.ttab, self.eplision)

        self.guard_token = Token(guard_str, Token.TypeTerminal)
        self.ttab.AddToken(self.guard_token)

        self.first_sets.first_sets[self.guard_token] = {self.guard_token}
        self.first_sets.nullable[self.guard_token] = False

        self.generateClosureSet()
        conflict_list = self.generateAction()
        if len(conflict_list) != 0:
            self.lr_check = False
        else:
            self.lr_check = True
        self.conflict_list = conflict_list

    def checkLR(self):
        return self.lr_check
    
    def stateCount(self):
        return len(self.closures_storage)

    def terminalCount(self):
        return self.ttab.terminalCount()

    def nonTerminalCount(self):
        return self.ttab.nonTerminalCount()
    
    def getTerminal(self):
        return list(filter(lambda t : t.isTerminal(), self.ttab.tokens.values()))
    
    def getNonTerminal(self):
        return list(filter(lambda t : t.isNonTerminal(), self.ttab.tokens.values()))

    def analyze(self, sentence : list, prority_resolver = None) -> tuple:
        def value_zero(actions_list):
            return 0
        
        if prority_resolver == None:
            prority_resolver = value_zero


        sentence = sentence + [self.guard_token]
        sentence_len = len(sentence)
        sentence_pos = 0

        analyze_status = False
        output_list = []

        def append_output_list(s_stack, t_stack, remaining_sentence, info):
            output_list.append((copy(s_stack),copy(t_stack), copy(remaining_sentence), info))
            print(output_list[-1])

        state_stack = [0]
        token_stack = [self.guard_token]

        def auto_append(info):
            append_output_list(state_stack, token_stack, sentence[sentence_pos:], info)
        
        while len(state_stack) != 0 and len(token_stack) != 0 and sentence_pos < sentence_len:

            cur_token:Token = sentence[sentence_pos]
            cur_state = state_stack[-1]
            actions_list = self.action_table[cur_state][cur_token]
            if len(actions_list) == 0:
                analyze_status = False
                break

            (action_type, item) = actions_list[prority_resolver(actions_list)]

            if action_type == LRAnalyzer.ActionType.Shift:
                auto_append(str(item) + ", Shift")
                next_state = self.closures_jump_table[cur_state][cur_token]
                state_stack.append(next_state)
                token_stack.append(cur_token)
                sentence_pos += 1
            elif action_type == LRAnalyzer.ActionType.Reduce:
                item:Item

                auto_append(str(item) + ", Reduce")
                if item.right_tokens[0] != self.eplision:
                    pop_len = len(item.right_tokens)
                    token_stack = token_stack[:-pop_len]
                    state_stack = state_stack[:-pop_len]

                    if item.left_token == self.argument_token:
                        analyze_status = True
                        break
                token_stack.append(item.left_token)
                state_stack.append(self.closures_jump_table[state_stack[-1]][item.left_token])
            else:
                raise Exception("Unexpected LRAnalyze.ActionType Value: {}".find(action_type))
        
        auto_append("Analyze End")
        # output_list is (list of int, list of token, str)
        return (analyze_status, output_list)
    
    # generate the closures set and the states transition table
    def generateClosureSet(self):
        def closureHelper(iset:frozenset):
            item_stack = []
            item_stack.extend(iset)
            ret_set = set()
            ret_set.update(iset)
            while len(item_stack) != 0:
                item:Item = item_stack.pop()
                if item.closureExtendable():
                    next_token = item.right_tokens[item.pos]
                    prod:Production = self.productions[next_token.val]
                    sentence = item.right_tokens[item.pos + 1:]
                    sentence.append(item.preview_token)
                    sts_fst = self.first_sets.queryFirstOfSentence(sentence)

                    for candi_strs in prod.rights:
                        candi_tokens = [self.ttab.getToken(x) for x in candi_strs]
                        for preview_token in sts_fst:
                            new_item = Item(next_token, candi_tokens, 0, preview_token)
                            if(candi_tokens[0] == self.eplision_token) :
                                new_item.pos = 1
                            if new_item in ret_set:
                                continue
                            else:
                                ret_set.update([new_item])
                                item_stack.append(new_item)
            return frozenset(ret_set)
        
        def GoHelper(iset:frozenset):

            ret_tmp = {}

            def goHelperStub(item:Item) -> Item:
                new_item = copy(item)
                new_item.pos = new_item.pos + 1
                return new_item

            for item in iset:
                item : Item
                
                if item.closureGoable():
                    new_item = goHelperStub(item)
                    next_token = item.right_tokens[item.pos]
                    if not next_token in ret_tmp.keys():
                        ret_tmp[next_token] = []
                    ret_tmp[next_token].append(new_item)

            jmp_tmp = {}
            for x in ret_tmp:
                jmp_tmp[x] = closureHelper(frozenset(ret_tmp[x]))
            return jmp_tmp
        
        start_item = Item(self.argument_token, [self.orginal_start_token], 0, self.guard_token)
        start_set = frozenset([start_item])
        first_closure = closureHelper(start_set)

        
        # used to temporary sotrage
        closure_stack = [first_closure]

        # to check if the set is unique in list named closure_stack
        closures_unique = set()
        closures_unique.add(first_closure)

        # it is a dict of dicts
        # can be used like : closures_jump_table[state][token]
        closures_jump_table = {}

        closures_storage = [first_closure]
        
        goto_table = {}
        while len(closure_stack) != 0:
            cur = closure_stack.pop()
            closure_go_dict = GoHelper(cur)
            state = closures_storage.index(cur)
            if not state in closures_jump_table.keys():
                closures_jump_table[state] = {}
                goto_table[state] = {}
            
            for k in closure_go_dict.keys():
                if not closure_go_dict[k] in closures_unique:
                    closures_storage.append(closure_go_dict[k])
                    closures_unique.add(closure_go_dict[k])
                    closure_stack.append(closure_go_dict[k])
                
                next_state = closures_storage.index(closure_go_dict[k])
                closures_jump_table[state][k] = next_state
                if k.isNonTerminal():
                    goto_table[state][k] = next_state
        
        self.closures_storage = closures_storage
        self.closures_jump_table = closures_jump_table
        self.goto_table = goto_table

    
    # return true if the grammar satisify the LR(1)
    # action table will be a dict of dicts of list
    # return type : (LR(1) check result, list of indics of closures which conflict)
    def generateAction(self) -> tuple:
        action = {}
        terminals_tmp = []
        for k in self.ttab.tokens:
            if self.ttab.getToken(k).isTerminal():
                terminals_tmp.append(self.ttab.getToken(k))

        closures_num = len(self.closures_storage)
        state = 0
        while state < closures_num:
            action[state] = {}
            for terminal in terminals_tmp:
                action[state][terminal] = []
            
            cur_closure = self.closures_storage[state]

            for item in cur_closure:
                item:Item
                if item.canShift():
                    action[state][item.right_tokens[item.pos]].append((LRAnalyzer.ActionType.Shift, item))
                elif item.canReduce():
                    action[state][item.preview_token].append((LRAnalyzer.ActionType.Reduce, item))

            state += 1
        self.action_table = action

        # check conflicts in action table

        conflicts_list = []
        state = 0
        while state < closures_num:
            for terminal in action[state]:
                action_list = action[state][terminal]
                reduce_cnt = 0
                shift_cnt = 0
                for (action_type, item) in action_list:
                    if action_type == LRAnalyzer.ActionType.Reduce:
                        reduce_cnt += 1
                    if action_type == LRAnalyzer.ActionType.Shift:
                        shift_cnt += 1
                
                if (reduce_cnt > 1) or (reduce_cnt > 0 and shift_cnt > 0):
                    conflicts_list.append((state, terminal))
            state += 1


        return conflicts_list 
    
    def getSentenceByStr(self, s:str):
        ret_tokens = []
        ret_status = True
        for single_str in s.strip().split(' '):
            if len(single_str) == 0:
                continue
            if not self.ttab.inTable(single_str):
                ret_status = False
                break
            ret_tokens.append(self.ttab.getToken(single_str))
        return (ret_status, ret_tokens)

        
    def getClosures(self) -> list:
        return self.closures_storage
    
    def getJumpTable(self) -> dict:
        return self.closures_jump_table
    
    def getGOTO(self) -> dict:
        return self.goto_table
    
    def getAction(self) -> dict:
        return self.action_table
    
    def debug_log(self):
        
        print("CLOSURES_JUMP_TABLE_START")
        l = list(self.closures_jump_table.keys())
        l.sort()
        for x in l:
            print(x, self.closures_jump_table[x])
        print("CLOSURES_JUMP_TABLE_END")


        print("ACTION_START")
        for s in self.action_table:
            for t in self.action_table[s]:
                print("{} -- {} -- {}".format(s, t, self.action_table[s][t]))
        print("ACTION_END")

        print("CONFLICTS_START")
        for x in self.conflict_list:
            print(x)
        print("CONFLICTS_END")

    def __str__(self) -> str:
        return str(self.productions) + ", " + str(self.ttab) + str(self.items)
    
    def __repr__(self) -> str:
        return self.__str()

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        ui_file_name = "lab3.ui"
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly):
            print("Cannot open {}: {}".format(ui_file_name, ui_file.errorString()))
            sys.exit(-1)
        loader = QUiLoader()
        window = loader.load(ui_file)
        ui_file.close()
        self.setCentralWidget(window)

        self.textedit_focus_status = False
        self.button:QPushButton = window.analysis
        self.button.clicked.connect(self.button_clicked)
        self.textedit:QTextEdit = window.productions
        self.lineedit:QLineEdit = window.sentence
        self.label:QLabel = window.check_status
        self.sentence_status_label:QLabel = window.sentence_status
        
        self.tabwidget:QTabWidget = window.tabwidget

    @Slot()
    def button_clicked(self):
        pstrs = self.textedit.toPlainText().strip().split("\n")
        senstr = self.lineedit.text().strip()
        lra = LRAnalyzer(pstrs, "?", "START", "#")
        lra.debug_log()

        if lra.checkLR():
            self.label.setText("LR(1) check passed")
        else:
            self.label.setText("LR(1) check failed, but still can be used to parse")
        
        (sentence_status, sentence) = lra.getSentenceByStr(senstr)

        if not sentence_status:
            self.sentence_status_label.setText("Unexpected tokens in the Sentence")
            return
        
        analyze_status, out_list = lra.analyze(sentence)

        if analyze_status:
            self.sentence_status_label.setText("Sentence Accepted")
        else: 
            self.sentence_status_label.setText("Sentence Not Accepted")

        # left to right is:
        # PROCESS, ACTION GOTO, DFA

        self.tabwidget.clear()

        process_tab = QTableWidget(len(out_list), 4)
        i = 0
        for (s,t,r,info) in out_list:
            s_item = QTableWidgetItem(str(s))
            process_tab.setItem(i, 0, s_item)
            
            t_str = [x.val for x in t]
            t_item = QTableWidgetItem(str(t_str))
            process_tab.setItem(i, 1, t_item)
            r_str = [x.val for x in r]
            r_item = QTableWidgetItem(str(r_str))
            process_tab.setItem(i, 2, r_item)

            i_item = QTableWidgetItem(str(info))
            process_tab.setItem(i, 3, i_item)
            i += 1
        process_tab.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        print(out_list)
        process_tab.setHorizontalHeaderLabels(["States", "Tokens", "Inputs", "Actions"])
        self.tabwidget.addTab(process_tab,"PROCESS")

        states_num = lra.stateCount()
        nterm_num = lra.nonTerminalCount()
        term_num = lra.terminalCount()

        nterms = [x.val for x in lra.getNonTerminal()]
        nterms.sort()
        terms = [x.val for x in lra.getTerminal()]
        terms.sort()

        action_tab = QTableWidget(states_num, term_num)

        print(terms)
        print(nterms)
        print(term_num)
        i = 0
        while i < states_num:
            j = 0
            while j < term_num:
                action = lra.action_table[i][lra.ttab.getToken(terms[j])]
                if len(action) == 0:
                    pass
                else:
                    item_str = ""
                    tmp_str_tab = ["Shift", "Reduce"]
                    t,p = action[0]
                    if lra.ttab.getToken(terms[j]) in lra.closures_jump_table[i]:
                        item_str = item_str + str(lra.closures_jump_table[i][lra.ttab.getToken(terms[j])])
                    tmp_action = [(tmp_str_tab[t], p) for (t,p) in action]
                    item = QTableWidgetItem(item_str + str(tmp_action))
                    action_tab.setItem(i,j, item)
                j += 1
            i = i + 1
        
        action_tab.setHorizontalHeaderLabels(terms)
        self.tabwidget.addTab(action_tab, "ACTION")


        goto_tab = QTableWidget(states_num, nterm_num)

        i = 0
        while i < states_num:
            j = 0
            while j < nterm_num:
                if lra.ttab.getToken(nterms[j]) in lra.closures_jump_table[i]:
                    print("in")
                    item = QTableWidgetItem(str(lra.closures_jump_table[i][lra.ttab.getToken(nterms[j])]))
                    goto_tab.setItem(i, j, item)
                else:
                    pass
                j = j + 1
            i = i + 1
        
        goto_tab.setHorizontalHeaderLabels(nterms)
        self.tabwidget.addTab(goto_tab, "GOTO")


        dfa_tab = QLabel()

        graph = Digraph("DFA", format="png")

        final_state = set()
        render_tuple = []
        for state in lra.closures_jump_table:
            flag = True 
            for token in lra.closures_jump_table[state]:
                flag = False 
                next_state = lra.closures_jump_table[state][token]
                tmp_tuple = (state, next_state, token.val)
                render_tuple.append(tmp_tuple)
            if flag:
                final_state.add(state)

        graph.attr("node", shape="doublecircle")
        graph.node("0")
        for (x,y,t) in render_tuple:
            if y in final_state:
                graph.attr("node", shape="doublecircle")
                graph.node(str(y))
            graph.attr("node", shape= "circle")
            graph.edge(str(x), str(y), label=t)
        graph.render()


        pic = QPixmap("./DFA.gv.png")
        dfa_tab.setPixmap(pic)
        scroll_area = QScrollArea()
        scroll_area.setWidget(dfa_tab)
        self.tabwidget.addTab(scroll_area, "DFA")


if __name__ == "__main__":
    
    '''
    f = open("/home/doot/projects/compiler/lab3/testcase/case3.txt", "r")
    plist = f.readlines()
    f.close()
    lra = LRAnalyzer(plist, "?", "START", "END")
    lra.debug_log()
    sentence = lra.getSentenceByStr("i * i + i + i + i")

    (status, out_str) = lra.analyze(sentence)
    print(status)
    for x in out_str:
        print(x)

    '''
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


    
    
