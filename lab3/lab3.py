import sys

class TokenTable:
    def __init__(self):
        self.nonterminal = {}
        self.terminal = {}

    def AddToken(self, token:Token):
        ''' Overwrite may occurs '''
        if self.isTerminal(token.t):
            del self.terminal[token.t]
        
        if self.isNonTerminal(token.t):
            del self.nonterminal[token.t]

        if token.type == Token.TypeNonTerminal:
            self.nonterminal[token.val] = token
        else:
            self.terminal[token.val] = token

    
    def getToken(self, t:str):
        if self.isTerminal(t):
            return self.terminal[t]
        if self.isNonTerminal(t):
            return self.nonterminal[t]
        return None
    
    def isTerminal(self, t:str):
        return t in self.terminal:

    def isNonTerminal(self, t:str):
        return t in self.nonterminal:

    def getTerminal(self):
        return self.terminal
    
    def getNonTerminal(self):
        return self.nonterminal
            
class Token:
    '''Token is represented as a string internally'''
    TypeTerminal = 0
    TypeNonTerminal = 1
    def __init__(self, t:str, token_type:int):
        self.val = t
        self.type = token_type

class Production:
    def error(self, st:str):
        sys.stderr.writable("Production error : {}".format(st))

    def __init__(self, p:str):
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
        right_part = p[arrow_index+1:]
        if len(right_part) == 0:
            self.status = False
            self.error("3")
            return
        left_parts = left_part.split(' ')
        
        if(len(left_parts) != 1):
            self.status = False
            self.error("4")
            return

        self.left_str = left_part[0]
        self.candidates = right_part.split('|')
    pass
        


if __name__ == "__main__":

    pass