import sys
from typing import Type


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
        outstr += self.left.val + " -> "
        for x in self.rights:
            for y in x:
                outstr += y.val + " "
            outstr = outstr + "| "
        return outstr[:-2]

    def __repr__(self) -> str:
        return self.__str__()

class Item:
    def __init__(self, left_token, right_tokens, pos, next_token):
        self.left_token = left_token
        self.pos = pos
        self.right_tokens = right_tokens
        self.next_token = next_token
    
    def __str__(self) -> str:
        outstr = "[ {} -> ".format(self.left_token.val)
        i = 0
        once_flag = True
        while i < len(self.right_tokens):
            if i == self.pos and once_flag:
                outstr += "*"
                once_flag = False
            else:
                outstr += self.right_tokens[i].val + " "
                i = i + 1
        if once_flag:
            outstr = outstr[:-1] + "*"
        outstr += ", {} ]".format(self.next_token.val)
        return outstr

    def __repr__(self) -> str:
        return self.__str__()
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
                for right_strs in productions[prod].rights:

                    left_token = ttab.getToken(productions[prod].left)
                    old_len = len(self.first_sets[left_token])
                    old_nullable = self.nullable[left_token]
                    
                    rights = [ttab.getToken(x) for x in right_strs]

                    i = 0
                    while i < len(rights):
                        if not self.nullable[rights[i]]:
                            break
                        self.first_sets[left_token] = self.first_sets[left_token].union(self.first_sets[rights[i]])
                        i = i + 1

                    if i < len(rights):
                        self.first_sets[left_token] = self.first_sets[left_token].union(self.first_sets[rights[i]])
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
    
    def __str__(self) -> str:
        return str(self.first_sets) + str(self.nullable)


class LRAnalyzer:
    productions = {}
    ttab = TokenTable()
    items = {}

    def __init__(self, pstr: list, eplision_str):

        self.eplision = Token(eplision_str, Token.TypeTerminal)

        flag = True
        for x in pstr:
            prod = Production(x, self.ttab)
            self.productions[prod.left] = prod
            if flag:
                self.start_token = prod.left
                flag = False
        
        self.first_sets = FirstSets(self.productions, self.ttab, self.eplision)
        #self.generateItems()
        
    
    def analyze(self, sentence : str):
        return False
    
    def generateItems(self):
        non_terminals = []
        for x in self.ttab.tokens.keys():
            if self.ttab.tokens[x].type == Token.TypeTerminal:
                non_terminals.append(self.ttab.tokens[x])
        
        for x in self.ttab.tokens.keys():
            token:Token = self.ttab.tokens[x]
            if token.type == Token.TypeNonTerminal:
                prod:Production = self.productions[token]

                tmp = []
                for y in prod.rights:
                    token_cnt = len(y)
                    i = 0
                    while i <= token_cnt:
                        for c in non_terminals:
                            item = Item(prod.left, y, i, c)
                            tmp.append(item)
                        i = i + 1
                self.items[prod.left] = tmp
    
    def generateClosureSet(self, item:Item):
        pass

        
    def __str__(self) -> str:
        return str(self.productions) + ", " + str(self.ttab) + str(self.items)
    
    def __repr__(self) -> str:
        return self.__str()

if __name__ == "__main__":
    f = open("/home/doot/projects/compiler/lab3/testcase/case1.txt", "r")
    plist = f.readlines()
    lra = LRAnalyzer(plist, "?")

    for x in lra.first_sets.first_sets:
        print(x, lra.first_sets.first_sets[x])
    
    for x in lra.first_sets.nullable:
        print(x, lra.first_sets.nullable[x])