import re
from functools import reduce
lineCount=1
symbolTable={}
numTable={}
flag=''
entryNumber=0
dataTypes={'int':4,'float':8,'double':16,'char':1,'long':8,'ptr':4}
addr=1000
g=open("Output.xls","w")
class Token(object):
    """ A simple Token structure. Token type, value and position.
    """
    def __init__(self, type, val, pos,lineno):
        self.type = type
        self.val = val
        self.pos = pos
        self.lineno=lineno
        
    def __str__(self):
        return '%s(%s) at %s in %s' % (self.type, self.val, self.pos,self.lineno)


class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos

#Lexer

class Lexer(object):
    """ A simple regex-based lexer/tokenizer.
    """
    def __init__(self, rules, skip_whitespace=True):
        """ Create a lexer.

            rules:
                A list of rules. Each rule is a regex, type
                pair, where regex is the regular expression used
                to recognize the token and type is the type
                of the token to return when it's recognized.

            skip_whitespace:
                If True, whitespace (\s+) will be skipped and not
                reported by the lexer. Otherwise, you have to
                specify your rules for whitespace, or it will be
                flagged as an error.
        """
        self.rules = []
        for regex, type in rules:
            self.rules.append((re.compile(regex), type))
        self.skip_whitespace = skip_whitespace
        self.re_ws_skip = re.compile('[^ \t\v\f\r]')
        

    def input(self, buf):
        """ Initialize the lexer with a buffer as input.
        """
        self.buf = buf
        self.pos = 0
    
    def tableEntry(self,tok):
        global symbolTable
        global numTable
        global dataTypes
        global addr
        global flag
        global entryNumber
        if (tok.val not in symbolTable.keys()):
            if(tok.type == 'IDENTIFIER' ):
                #print(dataTypes[flag],tok.type,tok.val,addr)
                #addr = hex(addr)
                
                symbolTable[tok.val] = (hex(addr),flag,dataTypes[flag])
                #addr=int(str(addr),16)
                addr += dataTypes[flag]
           
           
            if(tok.type=='ARRAY' or tok.type=='PTRARRAY'):
                pat='\[(\d+)\]'
                m=re.findall(pat,tok.val)
                m=list(map(int,m))
                m=reduce(lambda x,y:x*y,m)
                symbolTable[tok.val.split('[')[0]] = (hex(addr),flag,dataTypes[flag]*m)
                addr = addr + m*dataTypes[flag]
                
            
                 
        if(tok.val not in numTable.keys()):
            if(tok.type=='1002'):
                numTable[tok.val]=(entryNumber,tok.val,tok.type,'int')
                entryNumber+=1
            elif(tok.type=='1003'):
                numTable[tok.val]=(entryNumber,tok.val,tok.type,'float')
                entryNumber+=1
            elif(tok.type=='1004'):
                numTable[tok.val]=(entryNumber,ord(tok.val[1:2]),tok.type,'char')
                entryNumber+=1

    def token(self):
        """ Return the next token (a Token object) found in the
            input buffer. None is returned if the end of the
            buffer was reached.
            In case of a lexing error (the current chunk of the
            buffer matches no rule), a LexerError is raised with
            the position of the error.
        """
        if self.pos >= len(self.buf):
            return None
        if self.skip_whitespace:
            m = self.re_ws_skip.search(self.buf, self.pos)
            if m:
                self.pos = m.start()
            else:
                return None
            
        global g
        for regex, type in self.rules:
            m = regex.match(self.buf, self.pos)
            global lineCount
           
            if m:
                if(type=='NEWLINE'):
                    lineCount+=1
                tok = Token(type, m.group(), self.pos,lineCount)
                self.pos = m.end()
                global flag
                if(tok.type=='DATATYPE'):
                    flag=tok.val
                if(tok.type=='PTR'):
                    flag='ptr'
                self.tableEntry(tok)
                if(tok.type=='MLINECOMMENTS'):
                    n=len(tok.val.split('\n'))
                    lineCount+=n
                if(tok.type=='SLINECOMMENT'):
                    lineCount+=1
                if(tok.type!='DATATYPE'and tok.type!='NEWLINE'and tok.type!='MLINECOMMENTS'and tok.type!='SLINECOMMENT'
                   and tok.type!='PTR'):
                    if(tok.type=='IDENTIFIER'):
                        value=(symbolTable[tok.val][0],int(symbolTable[tok.val][0],16))
                    elif(tok.type=='1002' or tok.type=='1003'):
                        value=tok.val
                    elif(tok.type=='1004'):
                        value=ord(tok.val[1:2])
                    elif(tok.type=='ARRAY'or tok.type=='PTRARRAY'):
                        value=(symbolTable[tok.val.split('[')[0]][0],int(symbolTable[tok.val.split('[')[0]][0],16))
                        if(flag=='ptr'):
                            tok.type='PTRARRAY'
                    else:
                        value='--'
                    print(tok.lineno,"\t\t",tok.val,"\t\t",tok.type,"\t\t",value,file=g)
                return tok

        # if we're here, no rule matched
        raise LexerError(self.pos)

    def tokens(self):
        """ Returns an iterator to the tokens found in the buffer.
        """
        while 1:
            tok = self.token()
            if tok is None: break
            yield tok
#Rules:

rules = [
    (r'\n','NEWLINE'),
    #('\#(.)*?[<"](.)*?[>"]','PREPROCESSOR'),
    ('\#include','PREPROCESSOR'),
    ('\#define','MACRO'),
    ('<=','LE'),
    ('>=','GE'),
    ('>','GT'),
    ('!=','NE'),
    ('<','LT'),
    ('\/\/(.)*?\n','SLINECOMMENT'),
    ('\"([^\\\n]|(\\.))*?\"','STRCONST'),
    
    ('(.)*?\.[hc]','HEADER'),
    (r'\d+\.(\d+)','1003'),
    (r'\d+','1002'),
    ('/\*(.|\n)*?\*/','MLINECOMMENTS'),
    
    (r'\bint(\s)*\*\b','PTR'),
    (r'\bfloat(\s)*\*\b','PTR'),
    (r'\bdouble(\s)*\*\b','PTR'),
    (r'\blong(\s)*\*\b','PTR'),
    (r'\bchar(\s)*\*\b','PTR'),
    
    (r'\bint\b','DATATYPE'),
    (r'\bfloat\b','DATATYPE'),
    (r'\bdouble\b','DATATYPE'),
    (r'\blong\b','DATATYPE'),
    (r'\bchar\b','DATATYPE'),
    #(r'\bmain\b','FUNCTION'),
    (r'\bvoid\b','RESERVEWORD'),
    #(r'\bprintf\b','RESERVEWORD'),
    (r'\bvoid\b','RESERVEWORD'),
    (r'\bif\b','RESERVEWORD'),
    
    (r'\bauto\b','RESERVEWORD'),
    (r'\bbreak\b','RESERVEWORD'),
    (r'\bcase\b','RESERVEWORD'),
    (r'\bconst\b','RESERVEWORD'),
    (r'\bcontinue\b','RESERVEWORD'),
    (r'\bdefault\b','RESERVEWORD'),
    (r'\bdo\b','RESERVEWORD'),
    (r'\bdouble\b','RESERVEWORD'),
    (r'\belse\b','RESERVEWORD'),
    (r'\benum\b','RESERVEWORD'),
    (r'\bextern\b','RESERVEWORD'),
    (r'\bfor\b','RESERVEWORD'),
    (r'\bgoto\b','RESERVEWORD'),
    (r'\bregister\b','RESERVEWORD'),
    (r'\breturn\b','RESERVEWORD'),
    (r'\bshort\b','RESERVEWORD'),
    (r'\bsigned\b','RESERVEWORD'),
    (r'\bsizeof\b','RESERVEWORD'),
    (r'\bstatic\b','RESERVEWORD'),
    (r'\bstruct\b','RESERVEWORD'),
    (r'\bswitch\b','RESERVEWORD'),
    (r'\btypedef\b','RESERVEWORD'),
    (r'\bunion\b','RESERVEWORD'),
    (r'\bvoid\b','RESERVEWORD'),
    (r'\bvolatile\b','RESERVEWORD'),
    (r'\bwhile\b','RESERVEWORD'),
    
    
    
    
    
    
    
    ('->','ARROW'),
    ('\?','CONDOP'),
    ('[a-zA-Z_]\w*\((.)*?\)',    'FUNCTION'),
     ('[a-zA-Z_]\w*\*(\[(.)*?\])+',    'PTRARRAY'),
    ('[a-zA-Z_]\w*(\[(.)*?\])+',    'ARRAY'),
    #('\*(\s)*[a-zA-Z_]\w*',    'POINTER'),
    ('[a-zA-Z_]\w*',    'IDENTIFIER'),
    ('\+=','PLUSEQUALS'),
    ('-=','MINUSQUALS'),
    ('\*=','TIMESEQUALS'),
    ('\/=','DIVIDEEQUALS'),
    ('%=','MODEQUALS'),
    ('<<=','LSHIFTEQUALS'),
    ('>>=','RSHIFTEQUALS'),
    ('&=','ANDEQUALS'),
    ('\|=','OREQUALS'),
    ('^=','XOREQUALS'),
    ('\+\+','POSTINCREMENT'),
    ('\-\-','POSTDECREMENT'),
    ('\+',              'PLUS'),
    ('\-',              'MINUS'),
    ('\*',              'MULTIPLY'),
    ('\/',              'DIVIDE'),
    ('\(',              'LPAREN'),
    ('\)',              'RPAREN'),
    ('==','EQ'),
    ('=',               'EQUALS'),
    ('%',                'MOD'),
    ('\[','LBRACKET'),
    ('\]','RBRACKET'),
    ('\{','LBRACE'),
    ('\}','RBRACE'),
    (',','COMMA'),
    ('\.','PERIOD'),
    (';','SEMICOLON'),
    (':','COLON'),
    ('\|' ,'OR'),
    ('&','AND'),
    ('~','NOT'),
    ('\^','XOR'),
    ('<<','LSHIFT'),
    ('>>','RSHIFT'),
    ('\|\|','SHTCKTOR'),
    ('&&','SHTCKTAND'),
    ('!','LNOT'),
    
    
    (r'(L)?\'([^\\\n]|(\\.))*?\'','1004')
    
]



lx = Lexer(rules, skip_whitespace=True)
f=open('test.c')
inp=f.read()
f.close()
lx.input(inp)
staticTable=[]
try:
    print("\nOutput Table\nLine NO\t\t","Lexeme\t\t","Token\t\t","Specifier",file=g)
    for tok in lx.tokens():
        #print(tok)
        if(tok.type!='IDENTIFIER'and tok.type!='DATATYPE'and tok.type!='ARRAY'and tok.type!='STRCONST'and tok.type!='NEWLINE'and tok.type!='MLINECOMMENTS'
           and tok.type!='1002'and tok.type!='1003'and tok.type!='FUNCTION'and tok.type!='1004'):
            staticTable.append((tok.val,tok.type))
except LexerError as err:
    print('LexerError at position %s' % err.pos)
    
    

    

symbolTable=sorted(symbolTable.items(),key = lambda item:item[1][0])
numTable = sorted(numTable.items(),key = lambda item:item[1][0])




print("\nSymbolTable\n",file=g)
print("Address\t","\tSymbol","\t\tType\t","\tSize",file=g)
for i in symbolTable:
    print(i[1][0],"(",int(i[1][0],16),")\t\t",i[0],"\t\t",i[1][1],"\t\t",i[1][2],file=g)
        

print("\nNumTable\n",file=g)
print("Number\t","\tToken","\t\tType\t","\tValue",file=g)
for i in numTable:
    print(i[0],"\t\t",i[1][2],"\t\t",i[1][3],"\t\t",i[1][1],file=g)
    
print("\nStaticTable\n",file=g)
print("Token\t","\tType",file=g)
for i in staticTable:
    print(i[0],"\t\t",i[1],file=g)



g.close()

############
