# MIg Stage 0 - Parser
# Takes tokens from the Lexer and builds the AST

from mig_stage0_lexer import Lexer, TokenType, Token

# ─────────────────────────────────────────
#  NODOS DEL AST
# ─────────────────────────────────────────

class Node:
    pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f"Program({self.statements})"

class VarDecl(Node):
    def __init__(self, name, type_hint, value):
        self.name      = name
        self.type_hint = type_hint  # opcional
        self.value     = value
    def __repr__(self):
        return f"VarDecl({self.name}, type={self.type_hint}, value={self.value})"

class ConstDecl(Node):
    def __init__(self, name, value):
        self.name  = name
        self.value = value
    def __repr__(self):
        return f"ConstDecl({self.name}, value={self.value})"

class FuncDecl(Node):
    def __init__(self, name, params, body):
        self.name   = name
        self.params = params
        self.body   = body
    def __repr__(self):
        return f"FuncDecl({self.name}, params={self.params}, body={self.body})"

class ReturnStmt(Node):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Return({self.value})"

class IfStmt(Node):
    def __init__(self, condition, then_body, else_body):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
    def __repr__(self):
        return f"If({self.condition}, then={self.then_body}, else={self.else_body})"

class WhileStmt(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body
    def __repr__(self):
        return f"While({self.condition}, body={self.body})"

class ForInStmt(Node):
    def __init__(self, var, iterable, body):
        self.var      = var
        self.iterable = iterable
        self.body     = body
    def __repr__(self):
        return f"ForIn({self.var} in {self.iterable}, body={self.body})"

class UseStmt(Node):
    def __init__(self, module):
        self.module = module
    def __repr__(self):
        return f"Use({self.module})"

class ThrowStmt(Node):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Throw({self.value})"

class TryCatch(Node):
    def __init__(self, try_body, catch_var, catch_body):
        self.try_body   = try_body
        self.catch_var  = catch_var
        self.catch_body = catch_body
    def __repr__(self):
        return f"TryCatch(catch_var={self.catch_var})"

class StructDecl(Node):
    def __init__(self, name, fields, methods):
        self.name    = name
        self.fields  = fields   # lista de (nombre, tipo)
        self.methods = methods  # lista de FuncDecl
    def __repr__(self):
        return f"StructDecl({self.name}, fields={self.fields}, methods={[m.name for m in self.methods]})"

class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return f"ExprStmt({self.expr})"

class AssignExpr(Node):
    def __init__(self, target, value):
        self.target = target
        self.value  = value
    def __repr__(self):
        return f"Assign({self.target} = {self.value})"

class BinaryExpr(Node):
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right
    def __repr__(self):
        return f"Binary({self.left} {self.op} {self.right})"

class UnaryExpr(Node):
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand
    def __repr__(self):
        return f"Unary({self.op}{self.operand})"

class CallExpr(Node):
    def __init__(self, callee, args):
        self.callee = callee
        self.args   = args
    def __repr__(self):
        return f"Call({self.callee}, args={self.args})"

class MemberExpr(Node):
    def __init__(self, obj, member):
        self.obj    = obj
        self.member = member
    def __repr__(self):
        return f"Member({self.obj}.{self.member})"

class IndexExpr(Node):
    def __init__(self, obj, index):
        self.obj   = obj
        self.index = index
    def __repr__(self):
        return f"Index({self.obj}[{self.index}])"

class ArrayExpr(Node):
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return f"Array({self.elements})"

class StructInit(Node):
    def __init__(self, name, fields):
        self.name   = name
        self.fields = fields  # dict nombre -> valor
    def __repr__(self):
        return f"StructInit({self.name}, {self.fields})"

class Identifier(Node):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Ident({self.name})"

class NumberLit(Node):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Num({self.value})"

class StringLit(Node):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Str({repr(self.value)})"

class DictExpr(Node):
    def __init__(self, pairs):
        self.pairs = pairs  # lista de (key_expr, value_expr)
    def __repr__(self):
        return f"Dict({self.pairs})"

class SelfExpr(Node):
    def __repr__(self):
        return "Self"


# ─────────────────────────────────────────
#  PARSER
# ─────────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def error(self, msg):
        tok = self.current()
        raise SyntaxError(f"[MIg Parser] línea {tok.line}: {msg} (got {tok.type})")

    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def check(self, *types):
        return self.current().type in types

    def match(self, *types):
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, type, msg=None):
        if self.current().type == type:
            return self.advance()
        self.error(msg or f"se esperaba {type}")

    # ── programa ──────────────────────────
    def parse(self):
        stmts = []
        while not self.check(TokenType.EOF):
            stmts.append(self.parse_statement())
        return Program(stmts)

    # ── statements ────────────────────────
    def parse_statement(self):
        t = self.current().type

        if t == TokenType.VAR:
            return self.parse_var()
        if t == TokenType.CONST:
            return self.parse_const()
        if t == TokenType.FUNC:
            return self.parse_func()
        if t == TokenType.RETURN:
            return self.parse_return()
        if t == TokenType.IF:
            return self.parse_if()
        if t == TokenType.WHILE:
            return self.parse_while()
        if t == TokenType.FOR:
            return self.parse_for()
        if t == TokenType.USE:
            return self.parse_use()
        if t == TokenType.STRUCT:
            return self.parse_struct()
        if t == TokenType.TRY:
            return self.parse_try()
        if t == TokenType.THROW:
            return self.parse_throw()

        return self.parse_expr_stmt()

    def parse_var(self):
        self.expect(TokenType.VAR)
        name = self.expect(TokenType.IDENTIFIER).value
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQUALS, "se esperaba '=' en declaración de variable")
        value = self.parse_expr()
        return VarDecl(name, type_hint, value)

    def parse_const(self):
        self.expect(TokenType.CONST)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQUALS, "se esperaba '=' en declaración de constante")
        value = self.parse_expr()
        return ConstDecl(name, value)

    def parse_func(self):
        self.expect(TokenType.FUNC)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return FuncDecl(name, params, body)

    def parse_return(self):
        self.expect(TokenType.RETURN)
        value = self.parse_expr()
        return ReturnStmt(value)

    def parse_if(self):
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expr()
        self.expect(TokenType.RPAREN)
        then_body = self.parse_block()
        else_body = None
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                else_body = [self.parse_if()]
            else:
                else_body = self.parse_block()
        return IfStmt(condition, then_body, else_body)

    def parse_while(self):
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expr()
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return WhileStmt(condition, body)

    def parse_for(self):
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IN)
        iterable = self.parse_expr()
        body = self.parse_block()
        return ForInStmt(var, iterable, body)

    def parse_use(self):
        self.expect(TokenType.USE)
        module = self.expect(TokenType.IDENTIFIER).value
        return UseStmt(module)

    def parse_struct(self):
        self.expect(TokenType.STRUCT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACE)
        fields  = []
        methods = []
        while not self.check(TokenType.RBRACE):
            if self.check(TokenType.FUNC):
                methods.append(self.parse_func())
            else:
                fname = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.COLON)
                ftype = self.expect(TokenType.IDENTIFIER).value
                fields.append((fname, ftype))
        self.expect(TokenType.RBRACE)
        return StructDecl(name, fields, methods)

    def parse_try(self):
        self.expect(TokenType.TRY)
        try_body = self.parse_block()
        self.expect(TokenType.CATCH)
        self.expect(TokenType.LPAREN)
        catch_var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.RPAREN)
        catch_body = self.parse_block()
        return TryCatch(try_body, catch_var, catch_body)

    def parse_throw(self):
        self.expect(TokenType.THROW)
        value = self.parse_expr()
        return ThrowStmt(value)

    def parse_block(self):
        self.expect(TokenType.LBRACE)
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return stmts

    def parse_expr_stmt(self):
        expr = self.parse_expr()
        return ExprStmt(expr)

    # ── expresiones ───────────────────────
    def parse_expr(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_or()
        if self.match(TokenType.EQUALS):
            value = self.parse_assignment()
            return AssignExpr(left, value)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinaryExpr(left, "||", right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.match(TokenType.AND):
            right = self.parse_equality()
            left = BinaryExpr(left, "&&", right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while True:
            if self.match(TokenType.EQEQ):
                left = BinaryExpr(left, "==", self.parse_comparison())
            elif self.match(TokenType.BANGEQ):
                left = BinaryExpr(left, "!=", self.parse_comparison())
            else:
                break
        return left

    def parse_comparison(self):
        left = self.parse_addition()
        while True:
            if self.match(TokenType.LT):
                left = BinaryExpr(left, "<", self.parse_addition())
            elif self.match(TokenType.GT):
                left = BinaryExpr(left, ">", self.parse_addition())
            elif self.match(TokenType.LTEQ):
                left = BinaryExpr(left, "<=", self.parse_addition())
            elif self.match(TokenType.GTEQ):
                left = BinaryExpr(left, ">=", self.parse_addition())
            else:
                break
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while True:
            if self.match(TokenType.PLUS):
                left = BinaryExpr(left, "+", self.parse_multiplication())
            elif self.match(TokenType.MINUS):
                left = BinaryExpr(left, "-", self.parse_multiplication())
            else:
                break
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while True:
            if self.match(TokenType.STAR):
                left = BinaryExpr(left, "*", self.parse_unary())
            elif self.match(TokenType.SLASH):
                left = BinaryExpr(left, "/", self.parse_unary())
            else:
                break
        return left

    def parse_unary(self):
        if self.match(TokenType.BANG):
            return UnaryExpr("!", self.parse_unary())
        if self.match(TokenType.MINUS):
            return UnaryExpr("-", self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.match(TokenType.DOT):
                member = self.expect(TokenType.IDENTIFIER).value
                if self.check(TokenType.LPAREN):
                    self.advance()
                    args = self.parse_args()
                    self.expect(TokenType.RPAREN)
                    expr = CallExpr(MemberExpr(expr, member), args)
                else:
                    expr = MemberExpr(expr, member)
            elif self.check(TokenType.LPAREN):
                self.advance()
                args = self.parse_args()
                self.expect(TokenType.RPAREN)
                expr = CallExpr(expr, args)
            elif self.match(TokenType.LBRACKET):
                index = self.parse_expr()
                self.expect(TokenType.RBRACKET)
                expr = IndexExpr(expr, index)
            elif self.match(TokenType.PLUSPLUS):
                expr = UnaryExpr("++", expr)
            elif self.match(TokenType.MINUSMINUS):
                expr = UnaryExpr("--", expr)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.current()

        if tok.type == TokenType.NUMBER:
            self.advance()
            return NumberLit(tok.value)

        if tok.type == TokenType.STRING:
            self.advance()
            return StringLit(tok.value)

        if tok.type == TokenType.LBRACKET:
            return self.parse_array()

        if tok.type == TokenType.LBRACE:
            return self.parse_dict()

        if tok.type == TokenType.SELF:
            self.advance()
            return SelfExpr()

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            # struct init: Nombre { campo: valor }
            # solo si el siguiente token es { y el de después es IDENTIFIER seguido de COLON
            if self.check(TokenType.LBRACE):
                next1 = self.peek(1)
                next2 = self.peek(2)
                if next1.type == TokenType.IDENTIFIER and next2.type == TokenType.COLON:
                    return self.parse_struct_init(tok.value)
            return Identifier(tok.value)

        self.error(f"expresión inesperada '{tok.value}'")

    def parse_dict(self):
        self.expect(TokenType.LBRACE)
        pairs = []
        if not self.check(TokenType.RBRACE):
            key = self.parse_expr()
            self.expect(TokenType.COLON)
            val = self.parse_expr()
            pairs.append((key, val))
            while self.match(TokenType.COMMA):
                if self.check(TokenType.RBRACE):
                    break
                key = self.parse_expr()
                self.expect(TokenType.COLON)
                val = self.parse_expr()
                pairs.append((key, val))
        self.expect(TokenType.RBRACE)
        return DictExpr(pairs)

    def parse_array(self):
        self.expect(TokenType.LBRACKET)
        elements = []
        if not self.check(TokenType.RBRACKET):
            elements.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                elements.append(self.parse_expr())
        self.expect(TokenType.RBRACKET)
        return ArrayExpr(elements)

    def parse_struct_init(self, name):
        self.expect(TokenType.LBRACE)
        fields = {}
        while not self.check(TokenType.RBRACE):
            fname = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.COLON)
            fval = self.parse_expr()
            fields[fname] = fval
        self.expect(TokenType.RBRACE)
        return StructInit(name, fields)

    def parse_args(self):
        args = []
        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                args.append(self.parse_expr())
        return args


# ─────────────────────────────────────────
#  PRETTY PRINT DEL AST
# ─────────────────────────────────────────

def print_ast(node, indent=0):
    pad = "  " * indent
    if isinstance(node, Program):
        print(f"{pad}Program")
        for s in node.statements:
            print_ast(s, indent + 1)
    elif isinstance(node, FuncDecl):
        print(f"{pad}FuncDecl: {node.name}({', '.join(node.params)})")
        for s in node.body:
            print_ast(s, indent + 1)
    elif isinstance(node, VarDecl):
        t = f": {node.type_hint}" if node.type_hint else ""
        print(f"{pad}VarDecl: {node.name}{t}")
        print_ast(node.value, indent + 1)
    elif isinstance(node, ConstDecl):
        print(f"{pad}ConstDecl: {node.name}")
        print_ast(node.value, indent + 1)
    elif isinstance(node, ReturnStmt):
        print(f"{pad}Return")
        print_ast(node.value, indent + 1)
    elif isinstance(node, IfStmt):
        print(f"{pad}If")
        print(f"{pad}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{pad}  then:")
        for s in node.then_body:
            print_ast(s, indent + 2)
        if node.else_body:
            print(f"{pad}  else:")
            for s in node.else_body:
                print_ast(s, indent + 2)
    elif isinstance(node, WhileStmt):
        print(f"{pad}While")
        print_ast(node.condition, indent + 1)
        for s in node.body:
            print_ast(s, indent + 1)
    elif isinstance(node, ForInStmt):
        print(f"{pad}ForIn: {node.var} in")
        print_ast(node.iterable, indent + 1)
        for s in node.body:
            print_ast(s, indent + 1)
    elif isinstance(node, UseStmt):
        print(f"{pad}Use: {node.module}")
    elif isinstance(node, StructDecl):
        print(f"{pad}StructDecl: {node.name}")
        for fname, ftype in node.fields:
            print(f"{pad}  {fname}: {ftype}")
    elif isinstance(node, TryCatch):
        print(f"{pad}TryCatch (catch: {node.catch_var})")
        print(f"{pad}  try:")
        for s in node.try_body:
            print_ast(s, indent + 2)
        print(f"{pad}  catch:")
        for s in node.catch_body:
            print_ast(s, indent + 2)
    elif isinstance(node, ThrowStmt):
        print(f"{pad}Throw")
        print_ast(node.value, indent + 1)
    elif isinstance(node, ExprStmt):
        print_ast(node.expr, indent)
    elif isinstance(node, AssignExpr):
        print(f"{pad}Assign")
        print_ast(node.target, indent + 1)
        print_ast(node.value, indent + 1)
    elif isinstance(node, BinaryExpr):
        print(f"{pad}Binary: {node.op}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, UnaryExpr):
        print(f"{pad}Unary: {node.op}")
        print_ast(node.operand, indent + 1)
    elif isinstance(node, CallExpr):
        print(f"{pad}Call:")
        print_ast(node.callee, indent + 1)
        for a in node.args:
            print_ast(a, indent + 1)
    elif isinstance(node, MemberExpr):
        print(f"{pad}Member: .{node.member}")
        print_ast(node.obj, indent + 1)
    elif isinstance(node, IndexExpr):
        print(f"{pad}Index")
        print_ast(node.obj, indent + 1)
        print_ast(node.index, indent + 1)
    elif isinstance(node, ArrayExpr):
        print(f"{pad}Array[{len(node.elements)}]")
        for e in node.elements:
            print_ast(e, indent + 1)
    elif isinstance(node, StructInit):
        print(f"{pad}StructInit: {node.name}")
        for k, v in node.fields.items():
            print(f"{pad}  {k}:")
            print_ast(v, indent + 2)
    elif isinstance(node, Identifier):
        print(f"{pad}Ident: {node.name}")
    elif isinstance(node, NumberLit):
        print(f"{pad}Num: {node.value}")
    elif isinstance(node, StringLit):
        print(f"{pad}Str: {repr(node.value)}")
    else:
        print(f"{pad}{repr(node)}")


# ─────────────────────────────────────────
#  PRUEBA
# ─────────────────────────────────────────

if __name__ == "__main__":
    codigo_misty = """
use math

struct Persona {
    name: string
    age: int
}

func greet(person) {
    print("Hello " + persona.name)
}

func main() {
    var user = Person {
        name: "Misty"
        age: 20
    }

    greet(user)

    const MAX = 100
    var lista = [1, 2, 3, 4, 5]

    for item in lista {
        print(item)
    }

    if (user.age > 18) {
        print("is an adult")
    } else {
        print("is a minor")
    }

    try {
        var resultado = dividir(10, 0)
    } catch (err) {
        print(err)
    }
}
"""
    print("=== MIg Stage 0 - Parser ===")
    print("Misty source:")
    print(codigo_misty)
    print("Generated AST:")
    print("─" * 40)

    lexer  = Lexer(codigo_misty)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast    = parser.parse()
    print_ast(ast)
