from os import ttyname
import sys
from typing import ItemsView, Type
from copy import copy


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
    
    def getToken(self, t:str):
        if t in self.tokens:
            return self.tokens[t]
        else:
            return None

    def isTerminal(self, t:str):
        return t in self.tokens and self.tokens[t].type == Token.TypeTerminal
    def isNonTerminal(self, t:str):
        return t in self.tokens and self.tokens[t].type == Token.TypeNonTerminal
    
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
    
    def closureExtendable(self) -> bool:
        return self.pos < len(self.right_tokens) and self.right_tokens[self.pos].isNonTerminal()

    def closureGoable(self) -> bool:
        return self.pos != len(self.right_tokens)

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

    first_sets = {}
    nullable = {}

    def __init__(self, productions, ttab:TokenTable, eplision):
        self.eplision = eplision

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
    ''' productions are special, indexed by string '''
    productions = {}

    ttab = TokenTable()
    items = {}
    closures = {}


    def __init__(self, pstr: list, eplision_str, argument_str, guard_str):

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
        
    
    def analyze(self, sentence : str):
        return False
    
    def generateItems(self):
        non_terminals = []
        for x in self.ttab.tokens.keys():
            if self.ttab.tokens[x].type == Token.TypeTerminal:
                non_terminals.append(self.ttab.tokens[x])
        
        for x in self.ttab.tokens.keys():
            token:Token = self.ttab.getToken(x)
            if token.type == Token.TypeNonTerminal:
                prod:Production = self.productions[token.val]

                tmp = []
                for right_strs in prod.rights:
                    str_cnt = len(right_strs)
                    i = 0
                    while i <= str_cnt:
                        for c in non_terminals:
                            right_tokens = [self.ttab.getToken(x) for x in right_strs]
                            item = Item(self.ttab.getToken(prod.left), right_tokens, i, c)
                            tmp.append(item)
                        i = i + 1
                self.items[self.ttab.getToken(prod.left)] = tmp
    
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
                colsure_tmp = closureHelper(frozenset(ret_tmp[x]))
                jmp_tmp[x] = colsure_tmp
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

        closure_hash = [first_closure.__hash__()]

        while len(closure_stack) != 0:
            cur = closure_stack.pop()
            closure_go_dict = GoHelper(cur)
            state = closures_storage.index(cur)
            if not state in closures_jump_table.keys():
                closures_jump_table[state] = {}
            
            for k in closure_go_dict.keys():
                if not closure_go_dict[k] in closures_unique:
                    closures_storage.append(closure_go_dict[k])
                    closures_unique.add(closure_go_dict[k])
                    closure_stack.append(closure_go_dict[k])
                    closure_hash.append(closure_go_dict[k].__hash__())
                
                next_state = closures_storage.index(closure_go_dict[k])
                closures_jump_table[state][k] = next_state
        
        self.closures_storage = closures_storage
        self.closures_jump_table = closures_jump_table

    def __str__(self) -> str:
        return str(self.productions) + ", " + str(self.ttab) + str(self.items)
    
    def __repr__(self) -> str:
        return self.__str()

if __name__ == "__main__":
    f = open("/home/doot/projects/compiler/lab3/testcase/case2.txt", "r")
    plist = f.readlines()
    lra = LRAnalyzer(plist, "?", "START", "END")

    for x in lra.first_sets.first_sets:
        print(x, lra.first_sets.first_sets[x])
    
    for x in lra.first_sets.nullable:
        print(x, lra.first_sets.nullable[x])
    
    # print items
    '''for x in lra.items:
        for y in lra.items[x]:
            print(y)'''
    
    for x in lra.productions:
        print(lra.productions[x])
    
