# MIg Stage 0 - Intérprete
# Ejecuta el AST y corre código Misty de verdad

from mig_stage0_lexer import Lexer
from mig_stage0_parser import (
    Parser, Program, VarDecl, ConstDecl, FuncDecl, ReturnStmt,
    IfStmt, WhileStmt, ForInStmt, UseStmt, StructDecl, TryCatch,
    ThrowStmt, ExprStmt, AssignExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberExpr, IndexExpr, ArrayExpr, StructInit,
    Identifier, NumberLit, StringLit, DictExpr, SelfExpr
)

# ─────────────────────────────────────────
#  VALORES EN RUNTIME
# ─────────────────────────────────────────

class MistyStruct:
    """Una instancia de un struct de Misty"""
    def __init__(self, type_name, fields: dict, methods: dict):
        self.type_name = type_name
        self.fields    = fields
        self.methods   = methods  # nombre -> MistyFunction

    def __repr__(self):
        fields_str = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
        return f"{self.type_name} {{ {fields_str} }}"

class MistyDict:
    """Un diccionario de Misty"""
    def __init__(self, data: dict):
        self.data = data

    def __repr__(self):
        return str(self.data)

class MistyFunction:
    """Una función definida en Misty"""
    def __init__(self, name, params, body, closure):
        self.name    = name
        self.params  = params
        self.body    = body
        self.closure = closure  # entorno donde fue definida

    def __repr__(self):
        return f"<func {self.name}>"

class ReturnException(Exception):
    """Señal de return dentro de una función"""
    def __init__(self, value):
        self.value = value

class ThrowException(Exception):
    """Señal de throw en Misty"""
    def __init__(self, value):
        self.value = value


# ─────────────────────────────────────────
#  ENTORNO (scope de variables)
# ─────────────────────────────────────────

class Environment:
    def __init__(self, parent=None):
        self.vars   = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"[MIg] undefined variable '{name}'")

    def set(self, name, value):
        """Asigna en el scope donde existe, o en el actual"""
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent and self.parent.has(name):
            self.parent.set(name, value)
            return
        self.vars[name] = value

    def define(self, name, value):
        """Define siempre en el scope actual"""
        self.vars[name] = value

    def has(self, name):
        if name in self.vars:
            return True
        if self.parent:
            return self.parent.has(name)
        return False


# ─────────────────────────────────────────
#  INTÉRPRETE
# ─────────────────────────────────────────

class Interpreter:
    def __init__(self):
        self.globals      = Environment()
        self.struct_defs  = {}  # nombre -> lista de (campo, tipo)
        self._setup_builtins()

    # ── builtins de Misty ─────────────────
    def _setup_builtins(self):
        # print
        def misty_print(*args):
            print(*[self._to_str(a) for a in args])
            return None

        # len
        def misty_len(obj):
            if isinstance(obj, list):
                return len(obj)
            if isinstance(obj, str):
                return len(obj)
            raise TypeError(f"[MIg] len() does not apply to {type(obj)}")

        # push (modifica el array y regresa nada)
        def misty_push(arr, val):
            if not isinstance(arr, list):
                raise TypeError("[MIg] push() requires an array")
            arr.append(val)
            return None

        # pop
        def misty_pop(arr):
            if not isinstance(arr, list):
                raise TypeError("[MIg] pop() requires an array")
            return arr.pop()

        # str / int / float conversions
        def misty_str(val):
            return self._to_str(val)

        def misty_int(val):
            return int(val)

        def misty_float(val):
            return float(val)

        # input
        def misty_input(prompt=""):
            return input(prompt)

        self.globals.define("print",  misty_print)
        self.globals.define("len",    misty_len)
        self.globals.define("push",   misty_push)
        self.globals.define("pop",    misty_pop)
        self.globals.define("str",    misty_str)
        self.globals.define("int",    misty_int)
        self.globals.define("float",  misty_float)
        self.globals.define("input",  misty_input)
        self.globals.define("true",   True)
        self.globals.define("false",  False)
        self.globals.define("null",   None)

        # math module
        import math as _math
        math_struct = MistyDict({
            "sqrt":  lambda x: _math.sqrt(x),
            "pow":   lambda x, y: _math.pow(x, y),
            "abs":   lambda x: abs(x),
            "floor": lambda x: _math.floor(x),
            "ceil":  lambda x: _math.ceil(x),
            "pi":    _math.pi,
        })
        self.globals.define("math", math_struct)

    def _to_str(self, val):
        if val is True:  return "true"
        if val is False: return "false"
        if val is None:  return "null"
        if isinstance(val, MistyStruct): return repr(val)
        if isinstance(val, MistyDict):   return str(val.data)
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        return str(val)

    # ── ejecutar programa ─────────────────
    def run(self, program: Program):
        for stmt in program.statements:
            self.exec_stmt(stmt, self.globals)
        # call main() if it exists
        if self.globals.has("main"):
            main_fn = self.globals.get("main")
            self.call_function(main_fn, [])

    # ── ejecutar statement ────────────────
    def exec_stmt(self, node, env: Environment):
        if isinstance(node, VarDecl):
            value = self.eval_expr(node.value, env)
            env.define(node.name, value)

        elif isinstance(node, ConstDecl):
            value = self.eval_expr(node.value, env)
            env.define(node.name, value)

        elif isinstance(node, FuncDecl):
            fn = MistyFunction(node.name, node.params, node.body, env)
            env.define(node.name, fn)

        elif isinstance(node, StructDecl):
            self.struct_defs[node.name] = {
                "fields":  node.fields,
                "methods": {m.name: m for m in node.methods}
            }

        elif isinstance(node, UseStmt):
            # por ahora solo registramos el módulo
            pass

        elif isinstance(node, ReturnStmt):
            value = self.eval_expr(node.value, env)
            raise ReturnException(value)

        elif isinstance(node, ThrowStmt):
            value = self.eval_expr(node.value, env)
            raise ThrowException(value)

        elif isinstance(node, IfStmt):
            condition = self.eval_expr(node.condition, env)
            if self._truthy(condition):
                self.exec_block(node.then_body, Environment(env))
            elif node.else_body:
                self.exec_block(node.else_body, Environment(env))

        elif isinstance(node, WhileStmt):
            while self._truthy(self.eval_expr(node.condition, env)):
                self.exec_block(node.body, Environment(env))

        elif isinstance(node, ForInStmt):
            iterable = self.eval_expr(node.iterable, env)
            if not isinstance(iterable, list):
                raise TypeError(f"[MIg] for..in requires an array")
            for item in iterable:
                loop_env = Environment(env)
                loop_env.define(node.var, item)
                self.exec_block(node.body, loop_env)

        elif isinstance(node, TryCatch):
            try:
                self.exec_block(node.try_body, Environment(env))
            except ThrowException as e:
                catch_env = Environment(env)
                catch_env.define(node.catch_var, e.value)
                self.exec_block(node.catch_body, catch_env)

        elif isinstance(node, ExprStmt):
            self.eval_expr(node.expr, env)

        else:
            raise RuntimeError(f"[MIg] unknown statement: {type(node)}")

    def exec_block(self, stmts, env: Environment):
        for stmt in stmts:
            self.exec_stmt(stmt, env)

    # ── evaluar expresión ─────────────────
    def eval_expr(self, node, env: Environment):
        if isinstance(node, NumberLit):
            return node.value

        if isinstance(node, StringLit):
            return node.value

        if isinstance(node, Identifier):
            return env.get(node.name)

        if isinstance(node, ArrayExpr):
            return [self.eval_expr(e, env) for e in node.elements]

        if isinstance(node, DictExpr):
            data = {}
            for k, v in node.pairs:
                key = self.eval_expr(k, env)
                val = self.eval_expr(v, env)
                data[key] = val
            return MistyDict(data)

        if isinstance(node, SelfExpr):
            return env.get("self")

        if isinstance(node, StructInit):
            if node.name not in self.struct_defs:
                raise NameError(f"[MIg] undefined struct '{node.name}'")
            defn    = self.struct_defs[node.name]
            fields  = {k: self.eval_expr(v, env) for k, v in node.fields.items()}
            methods = {
                name: MistyFunction(name, fn.params, fn.body, env)
                for name, fn in defn["methods"].items()
            }
            return MistyStruct(node.name, fields, methods)

        if isinstance(node, MemberExpr):
            obj = self.eval_expr(node.obj, env)

            # struct — campos y métodos
            if isinstance(obj, MistyStruct):
                if node.member in obj.fields:
                    return obj.fields[node.member]
                if node.member in obj.methods:
                    fn = obj.methods[node.member]
                    # bind self
                    def bound_method(fn=fn, obj=obj):
                        return lambda *args: self._call_method(fn, obj, list(args))
                    return bound_method()
                raise AttributeError(f"[MIg] '{obj.type_name}' does not have field '{node.member}'")

            # dict — métodos
            if isinstance(obj, MistyDict):
                if node.member == "get":
                    return lambda k: obj.data.get(k)
                if node.member == "set":
                    return lambda k, v: obj.data.update({k: v})
                if node.member == "has":
                    return lambda k: k in obj.data
                if node.member == "keys":
                    return lambda: list(obj.data.keys())
                if node.member == "values":
                    return lambda: list(obj.data.values())
                if node.member == "len":
                    return lambda: len(obj.data)
                # acceso directo a valores internos (para math.pi etc)
                if node.member in obj.data:
                    val = obj.data[node.member]
                    return val
                raise AttributeError(f"[MIg] dict does not have method '{node.member}'")

            # string — métodos
            if isinstance(obj, str):
                if node.member == "len":
                    return lambda: len(obj)
                if node.member == "upper":
                    return lambda: obj.upper()
                if node.member == "lower":
                    return lambda: obj.lower()
                if node.member == "split":
                    return lambda sep=" ": obj.split(sep)
                if node.member == "contains":
                    return lambda s: s in obj
                if node.member == "replace":
                    return lambda a, b: obj.replace(a, b)
                if node.member == "trim":
                    return lambda: obj.strip()
                if node.member == "starts_with":
                    return lambda s: obj.startswith(s)
                if node.member == "ends_with":
                    return lambda s: obj.endswith(s)
                raise AttributeError(f"[MIg] string does not have method '{node.member}'")

            # array — métodos
            if isinstance(obj, list):
                if node.member == "len":
                    return lambda: len(obj)
                if node.member == "push":
                    return lambda val: obj.append(val)
                if node.member == "pop":
                    return lambda: obj.pop()
                if node.member == "contains":
                    return lambda val: val in obj
                if node.member == "join":
                    return lambda sep="": sep.join(self._to_str(x) for x in obj)
                if node.member == "reverse":
                    return lambda: obj.reverse()
                raise AttributeError(f"[MIg] array does not have method '{node.member}'")

            # dict nativo Python (usado por mig_interpreter.mi internamente)
            if isinstance(obj, dict):
                if node.member == "has":
                    return lambda k, o=obj: k in o
                if node.member == "keys":
                    return lambda o=obj: list(o.keys())
                if node.member == "values":
                    return lambda o=obj: list(o.values())
                if node.member == "len":
                    return lambda o=obj: len(o)
                if node.member in obj:
                    return obj[node.member]
                return None

            raise AttributeError(f"[MIg] cannot access .{node.member} on {type(obj)}")


        if isinstance(node, IndexExpr):
            obj   = self.eval_expr(node.obj, env)
            index = self.eval_expr(node.index, env)
            if isinstance(obj, list):
                return obj[int(index)]
            if isinstance(obj, str):
                return obj[int(index)]
            if isinstance(obj, MistyDict):
                if index not in obj.data:
                    raise KeyError(f"[MIg] key '{index}' not found in dict")
                return obj.data[index]
            # dict nativo de Python (usado internamente en Stage 1)
            return obj[index]

        if isinstance(node, AssignExpr):
            value = self.eval_expr(node.value, env)
            if isinstance(node.target, Identifier):
                env.set(node.target.name, value)
            elif isinstance(node.target, MemberExpr):
                obj = self.eval_expr(node.target.obj, env)
                if isinstance(obj, MistyStruct):
                    obj.fields[node.target.member] = value
                else:
                    raise AttributeError(f"[MIg] cannot assign to .{node.target.member}")
            elif isinstance(node.target, IndexExpr):
                obj   = self.eval_expr(node.target.obj, env)
                index = self.eval_expr(node.target.index, env)
                if isinstance(obj, list):
                    obj[int(index)] = value
                elif isinstance(obj, MistyDict):
                    obj.data[index] = value
                else:
                    obj[index] = value
            return value

        if isinstance(node, UnaryExpr):
            if node.op == "-":
                return -self.eval_expr(node.operand, env)
            if node.op == "!":
                return not self._truthy(self.eval_expr(node.operand, env))
            if node.op == "++":
                val = self.eval_expr(node.operand, env) + 1
                if isinstance(node.operand, Identifier):
                    env.set(node.operand.name, val)
                return val
            if node.op == "--":
                val = self.eval_expr(node.operand, env) - 1
                if isinstance(node.operand, Identifier):
                    env.set(node.operand.name, val)
                return val

        if isinstance(node, BinaryExpr):
            return self.eval_binary(node, env)

        if isinstance(node, CallExpr):
            return self.eval_call(node, env)

        raise RuntimeError(f"[MIg] unknown expression: {type(node)}")

    # ── operaciones binarias ──────────────
    def eval_binary(self, node: BinaryExpr, env):
        left  = self.eval_expr(node.left, env)
        right = self.eval_expr(node.right, env)
        op    = node.op

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return self._to_str(left) + self._to_str(right)
            return left + right
        if op == "-":  return left - right
        if op == "*":  return left * right
        if op == "/":
            if right == 0:
                raise ThrowException("Error: division by zero")
            return left / right
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == "<":  return left < right
        if op == ">":  return left > right
        if op == "<=": return left <= right
        if op == ">=": return left >= right
        if op == "&&": return self._truthy(left) and self._truthy(right)
        if op == "||": return self._truthy(left) or self._truthy(right)

        raise RuntimeError(f"[MIg] unknown operator: {op}")

    # ── llamadas a funciones ──────────────
    def eval_call(self, node: CallExpr, env):
        callee = self.eval_expr(node.callee, env)
        args   = [self.eval_expr(a, env) for a in node.args]

        # builtin de Python (lambda o función)
        if callable(callee) and not isinstance(callee, MistyFunction):
            return callee(*args)

        if isinstance(callee, MistyFunction):
            return self.call_function(callee, args)

        raise TypeError(f"[MIg] '{callee}' is not a function")

    def call_function(self, fn: MistyFunction, args):
        if len(args) != len(fn.params):
            raise TypeError(
                f"[MIg] {fn.name}() expected {len(fn.params)} args, got {len(args)}"
            )
        fn_env = Environment(fn.closure)
        for param, arg in zip(fn.params, args):
            fn_env.define(param, arg)
        try:
            self.exec_block(fn.body, fn_env)
        except ReturnException as r:
            return r.value
        return None

    def _call_method(self, fn: MistyFunction, instance: MistyStruct, args):
        fn_env = Environment(fn.closure)
        fn_env.define("self", instance)
        for param, arg in zip(fn.params, args):
            fn_env.define(param, arg)
        try:
            self.exec_block(fn.body, fn_env)
        except ReturnException as r:
            return r.value
        return None

    def _truthy(self, val):
        if val is None or val is False:
            return False
        if isinstance(val, (int, float)) and val == 0:
            return False
        return True


# ─────────────────────────────────────────
#  MIg — punto de entrada
# ─────────────────────────────────────────

def run_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    run_source(source)

def run_source(source: str):
    lexer    = Lexer(source)
    tokens   = lexer.tokenize()
    parser   = Parser(tokens)
    ast      = parser.parse()
    interp   = Interpreter()
    interp.run(ast)


# ─────────────────────────────────────────
#  PRUEBA — primer programa Misty real
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        codigo = """
use math

struct Circulo {
    radio: float

    func area() {
        return math.pi * self.radio * self.radio
    }

    func describir() {
        print("Circle with radius " + str(self.radio))
        print("Area: " + str(self.area()))
    }
}

func main() {
    print("=== Misty v0.2 ===")

    var c = Circulo { radio: 5 }
    c.describir()

    var data = {"name": "Misty", "version": 2, "language": "Misty"}
    print("Name: " + data["name"])
    print("Language: " + data["language"])

    var greeting = "hello world from misty"
    print(greeting.upper())
    print("Contains misty: " + str(greeting.contains("misty")))
    print("Replaced: " + greeting.replace("misty", "Misty"))

    var nums = [3, 1, 4, 1, 5, 9, 2, 6]
    print("Array tiene 8 elementos: " + str(nums.len()))
    print("Contiene 9: " + str(nums.contains(9)))
    print("Joined: " + nums.join(", "))

    print("sqrt(144) = " + str(math.sqrt(144)))
    print("pow(2, 10) = " + str(math.pow(2, 10)))
    print("pi = " + str(math.pi))

    print("=== All features working ===")
}
"""
        run_source(codigo)
