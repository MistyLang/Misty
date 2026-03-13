# MIg Stage 0 - Lexer
# First step of the MIg compiler
# Converts .my source code into tokens

from enum import Enum, auto

# ─────────────────────────────────────────
#  TIPOS DE TOKENS
# ─────────────────────────────────────────
class TokenType(Enum):
    # Literals
    NUMBER      = auto()
    STRING      = auto()
    IDENTIFIER  = auto()

    # Keywords
    VAR         = auto()
    CONST       = auto()
    FUNC        = auto()
    RETURN      = auto()
    IF          = auto()
    ELSE        = auto()
    WHILE       = auto()
    FOR         = auto()
    IN          = auto()
    USE         = auto()
    STRUCT      = auto()
    TRY         = auto()
    CATCH       = auto()
    THROW       = auto()
    SELF        = auto()

    # Operators
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    EQUALS      = auto()   # =
    EQEQ        = auto()   # ==
    BANGEQ      = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LTEQ        = auto()   # <=
    GTEQ        = auto()   # >=
    PLUSPLUS    = auto()   # ++
    MINUSMINUS  = auto()   # --
    BANG        = auto()   # !
    AND         = auto()   # &&
    OR          = auto()   # ||

    # Delimiters
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    COMMA       = auto()   # ,
    DOT         = auto()   # .
    COLON       = auto()   # :

    # Special
    EOF         = auto()
    NEWLINE     = auto()


# Reserved keywords
KEYWORDS = {
    "var":    TokenType.VAR,
    "const":  TokenType.CONST,
    "func":   TokenType.FUNC,
    "return": TokenType.RETURN,
    "if":     TokenType.IF,
    "else":   TokenType.ELSE,
    "while":  TokenType.WHILE,
    "for":    TokenType.FOR,
    "in":     TokenType.IN,
    "use":    TokenType.USE,
    "struct": TokenType.STRUCT,
    "try":    TokenType.TRY,
    "catch":  TokenType.CATCH,
    "throw":  TokenType.THROW,
    "self":   TokenType.SELF,
}


# ─────────────────────────────────────────
#  TOKEN
# ─────────────────────────────────────────
class Token:
    def __init__(self, type: TokenType, value, line: int):
        self.type  = type
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"


# ─────────────────────────────────────────
#  LEXER
# ─────────────────────────────────────────
class Lexer:
    def __init__(self, source: str):
        self.source  = source
        self.pos     = 0
        self.line    = 1
        self.tokens  = []

    def error(self, msg):
        raise SyntaxError(f"[MIg Lexer] línea {self.line}: {msg}")

    def peek(self, offset=0):
        idx = self.pos + offset
        if idx >= len(self.source):
            return '\0'
        return self.source[idx]

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def match(self, expected):
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.pos += 1
            return True
        return False

    def add_token(self, type: TokenType, value=None):
        self.tokens.append(Token(type, value, self.line))

    # ── escaneo principal ──────────────────
    def tokenize(self):
        while self.pos < len(self.source):
            self.scan_token()
        self.add_token(TokenType.EOF)
        return self.tokens

    def scan_token(self):
        ch = self.advance()

        # Espacios y tabs — ignorar
        if ch in (' ', '\t', '\r'):
            return

        # Saltos de línea
        if ch == '\n':
            return  # ya incrementado en advance()

        # Comentarios // 
        if ch == '/' and self.peek() == '/':
            while self.peek() != '\n' and self.peek() != '\0':
                self.advance()
            return

        # Strings
        if ch == '"':
            self.read_string()
            return

        # Números
        if ch.isdigit():
            self.read_number(ch)
            return

        # Identificadores y keywords
        if ch.isalpha() or ch == '_':
            self.read_identifier(ch)
            return

        # Operators y delimitadores
        match ch:
            case '+':
                if self.match('+'):
                    self.add_token(TokenType.PLUSPLUS)
                else:
                    self.add_token(TokenType.PLUS)
            case '-':
                if self.match('-'):
                    self.add_token(TokenType.MINUSMINUS)
                else:
                    self.add_token(TokenType.MINUS)
            case '*': self.add_token(TokenType.STAR)
            case '/': self.add_token(TokenType.SLASH)
            case '=':
                if self.match('='):
                    self.add_token(TokenType.EQEQ)
                else:
                    self.add_token(TokenType.EQUALS)
            case '!':
                if self.match('='):
                    self.add_token(TokenType.BANGEQ)
                else:
                    self.add_token(TokenType.BANG)
            case '<':
                if self.match('='):
                    self.add_token(TokenType.LTEQ)
                else:
                    self.add_token(TokenType.LT)
            case '>':
                if self.match('='):
                    self.add_token(TokenType.GTEQ)
                else:
                    self.add_token(TokenType.GT)
            case '&':
                if self.match('&'):
                    self.add_token(TokenType.AND)
                else:
                    self.error(f"carácter inesperado '&'")
            case '|':
                if self.match('|'):
                    self.add_token(TokenType.OR)
                else:
                    self.error(f"carácter inesperado '|'")
            case '(': self.add_token(TokenType.LPAREN)
            case ')': self.add_token(TokenType.RPAREN)
            case '{': self.add_token(TokenType.LBRACE)
            case '}': self.add_token(TokenType.RBRACE)
            case '[': self.add_token(TokenType.LBRACKET)
            case ']': self.add_token(TokenType.RBRACKET)
            case ',': self.add_token(TokenType.COMMA)
            case '.': self.add_token(TokenType.DOT)
            case ':': self.add_token(TokenType.COLON)
            case _:
                self.error(f"carácter desconocido '{ch}'")

    # ── helpers ────────────────────────────
    def read_string(self):
        result = ""
        while self.peek() != '"' and self.peek() != '\0':
            if self.peek() == '\n':
                self.error("string sin cerrar")
            if self.peek() == '\\':
                self.advance()  # consume backslash
                esc = self.advance()
                if esc == 'n':  result += '\n'
                elif esc == 't': result += '\t'
                elif esc == '"': result += '"'
                elif esc == '\\': result += '\\'
                elif esc == '0': result += '\0'
                else: result += '\\' + esc
            else:
                result += self.advance()
        if self.peek() == '\0':
            self.error("string sin cerrar al final del archivo")
        self.advance()  # close quote
        self.add_token(TokenType.STRING, result)

    def read_number(self, first_ch):
        num = first_ch
        while self.peek().isdigit():
            num += self.advance()
        if self.peek() == '.' and self.source[self.pos + 1].isdigit():
            num += self.advance()  # decimal point
            while self.peek().isdigit():
                num += self.advance()
            self.add_token(TokenType.NUMBER, float(num))
        else:
            self.add_token(TokenType.NUMBER, int(num))

    def read_identifier(self, first_ch):
        ident = first_ch
        while self.peek().isalnum() or self.peek() == '_':
            ident += self.advance()
        token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        self.add_token(token_type, ident)


# ─────────────────────────────────────────
#  PRUEBA
# ─────────────────────────────────────────
if __name__ == "__main__":
    codigo_misty = """
func main() {
    var name = "Misty"
    const VERSION = 1
    print(nombre)
    if (VERSION == 1) {
        print("Misty v1")
    }
}
"""
    print("=== MIg Stage 0 - Lexer ===")
    print("Misty source:")
    print(codigo_misty)
    print("Generated tokens:")
    lexer = Lexer(codigo_misty)
    tokens = lexer.tokenize()
    for token in tokens:
        print(f"  {token}")
