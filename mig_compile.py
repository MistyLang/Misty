# mig_compile.py
# MIg Stage 2 - Compiles .my to native executable via C
# file.my -> file.c -> gcc -> executable

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

from mig_stage0_lexer import Lexer
from mig_stage0_parser import (
    Parser, Program, VarDecl, ConstDecl, FuncDecl, ReturnStmt,
    IfStmt, WhileStmt, ForInStmt, UseStmt, StructDecl, TryCatch,
    ThrowStmt, ExprStmt, AssignExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberExpr, IndexExpr, ArrayExpr, StructInit,
    Identifier, NumberLit, StringLit, DictExpr, SelfExpr
)

# ─────────────────────────────────────────
#  GENERADOR DE CÓDIGO C
# ─────────────────────────────────────────

class CGen:
    def __init__(self):
        self.output       = []
        self.indent_level = 0
        self.struct_defs  = {}
        self.tmp_count    = 0

    def tmp(self):
        self.tmp_count += 1
        return f"_tmp{self.tmp_count}"

    def indent(self):
        return "    " * self.indent_level

    def emit(self, line):
        self.output.append(self.indent() + line)

    def emit_raw(self, line):
        self.output.append(line)

    # ── programa completo ─────────────────
    def generate(self, program: Program) -> str:
        # header C
        self.emit_raw('#include <stdio.h>')
        self.emit_raw('#include <stdlib.h>')
        self.emit_raw('#include <string.h>')
        self.emit_raw('#include <math.h>')
        self.emit_raw('')
        self.emit_raw('// ── runtime de Misty ──────────────────')
        self.emit_raw('')

        # runtime helpers
        self.emit_runtime()

        # forward declarations
        self.emit_raw('// ── forward declarations ──────────────')
        for stmt in program.statements:
            if isinstance(stmt, FuncDecl):
                params = ', '.join(f'MistyVal {p}' for p in stmt.params)
                self.emit_raw(f'MistyVal misty_{stmt.name}({params});')
            if isinstance(stmt, StructDecl):
                self.struct_defs[stmt.name] = stmt
        self.emit_raw('')

        # struct definitions
        self.emit_raw('// ── structs ───────────────────────────')
        for stmt in program.statements:
            if isinstance(stmt, StructDecl):
                self.gen_struct_def(stmt)
        self.emit_raw('')

        # funciones y statements globales
        self.emit_raw('// ── funciones ─────────────────────────')
        for stmt in program.statements:
            if isinstance(stmt, FuncDecl):
                self.gen_func(stmt)

        # main de C
        self.emit_raw('int main() {')
        self.indent_level = 1
        # statements globales que no son funcs ni structs
        for stmt in program.statements:
            if not isinstance(stmt, (FuncDecl, StructDecl, UseStmt)):
                self.gen_stmt(stmt)
        # llamar main de Misty si existe
        self.emit('misty_main();')
        self.emit('return 0;')
        self.indent_level = 0
        self.emit_raw('}')

        return '\n'.join(self.output)

    # ── runtime ───────────────────────────
    def emit_runtime(self):
        runtime = r"""
// Tipo universal de Misty
typedef enum { MISTY_NULL, MISTY_INT, MISTY_FLOAT, MISTY_STRING, MISTY_BOOL } MistyType;

typedef struct MistyVal {
    MistyType type;
    union {
        long long   ival;
        double      fval;
        char*       sval;
        int         bval;
    };
} MistyVal;

// Constructores
MistyVal misty_null()              { MistyVal v; v.type=MISTY_NULL;   v.ival=0;  return v; }
MistyVal misty_int(long long i)    { MistyVal v; v.type=MISTY_INT;    v.ival=i;  return v; }
MistyVal misty_float(double f)     { MistyVal v; v.type=MISTY_FLOAT;  v.fval=f;  return v; }
MistyVal misty_bool(int b)         { MistyVal v; v.type=MISTY_BOOL;   v.bval=b;  return v; }
MistyVal misty_str(const char* s)  {
    MistyVal v; v.type=MISTY_STRING;
    v.sval = (char*)malloc(strlen(s)+1);
    strcpy(v.sval, s);
    return v;
}

// Conversión a string
char* misty_to_str(MistyVal v) {
    char* buf = (char*)malloc(256);
    if (v.type == MISTY_INT)         sprintf(buf, "%lld", v.ival);
    else if (v.type == MISTY_FLOAT)  sprintf(buf, "%g",   v.fval);
    else if (v.type == MISTY_STRING) return v.sval;
    else if (v.type == MISTY_BOOL)   sprintf(buf, "%s", v.bval ? "true" : "false");
    else                             sprintf(buf, "null");
    return buf;
}

// Concatenación de strings
MistyVal misty_concat(MistyVal a, MistyVal b) {
    char* sa = misty_to_str(a);
    char* sb = misty_to_str(b);
    char* result = (char*)malloc(strlen(sa)+strlen(sb)+1);
    strcpy(result, sa);
    strcat(result, sb);
    MistyVal v; v.type=MISTY_STRING; v.sval=result;
    return v;
}

// Aritmética
MistyVal misty_add(MistyVal a, MistyVal b) {
    if (a.type==MISTY_STRING || b.type==MISTY_STRING) return misty_concat(a,b);
    if (a.type==MISTY_FLOAT || b.type==MISTY_FLOAT)
        return misty_float((a.type==MISTY_FLOAT?a.fval:a.ival)+(b.type==MISTY_FLOAT?b.fval:b.ival));
    return misty_int(a.ival + b.ival);
}
MistyVal misty_sub(MistyVal a, MistyVal b) {
    if (a.type==MISTY_FLOAT||b.type==MISTY_FLOAT)
        return misty_float((a.type==MISTY_FLOAT?a.fval:a.ival)-(b.type==MISTY_FLOAT?b.fval:b.ival));
    return misty_int(a.ival - b.ival);
}
MistyVal misty_mul(MistyVal a, MistyVal b) {
    if (a.type==MISTY_FLOAT||b.type==MISTY_FLOAT)
        return misty_float((a.type==MISTY_FLOAT?a.fval:a.ival)*(b.type==MISTY_FLOAT?b.fval:b.ival));
    return misty_int(a.ival * b.ival);
}
MistyVal misty_div(MistyVal a, MistyVal b) {
    double da = a.type==MISTY_FLOAT?a.fval:a.ival;
    double db = b.type==MISTY_FLOAT?b.fval:b.ival;
    return misty_float(da / db);
}

// Comparaciones
int misty_eq(MistyVal a, MistyVal b) {
    if (a.type==MISTY_INT   && b.type==MISTY_INT)    return a.ival==b.ival;
    if (a.type==MISTY_FLOAT || b.type==MISTY_FLOAT) {
        double da=a.type==MISTY_FLOAT?a.fval:a.ival;
        double db=b.type==MISTY_FLOAT?b.fval:b.ival;
        return da==db;
    }
    if (a.type==MISTY_STRING && b.type==MISTY_STRING) return strcmp(a.sval,b.sval)==0;
    if (a.type==MISTY_BOOL   && b.type==MISTY_BOOL)   return a.bval==b.bval;
    if (a.type==MISTY_NULL   && b.type==MISTY_NULL)   return 1;
    return 0;
}
int misty_lt(MistyVal a, MistyVal b) {
    if (a.type==MISTY_FLOAT||b.type==MISTY_FLOAT)
        return (a.type==MISTY_FLOAT?a.fval:a.ival)<(b.type==MISTY_FLOAT?b.fval:b.ival);
    return a.ival < b.ival;
}
int misty_gt(MistyVal a, MistyVal b) { return misty_lt(b,a); }
int misty_truthy(MistyVal v) {
    if (v.type==MISTY_NULL)  return 0;
    if (v.type==MISTY_BOOL)  return v.bval;
    if (v.type==MISTY_INT)   return v.ival != 0;
    if (v.type==MISTY_FLOAT) return v.fval != 0.0;
    if (v.type==MISTY_STRING)return strlen(v.sval) > 0;
    return 0;
}

// print builtin
void misty_print(MistyVal v) {
    printf("%s\n", misty_to_str(v));
}

"""
        for line in runtime.split('\n'):
            self.emit_raw(line)

    # ── struct definition ─────────────────
    def gen_struct_def(self, node: StructDecl):
        self.emit_raw(f'typedef struct {{')
        for fname, ftype in node.fields:
            self.emit_raw(f'    MistyVal {fname};')
        self.emit_raw(f'}} Misty_{node.name};')
        self.emit_raw('')

    # ── función ───────────────────────────
    def gen_func(self, node: FuncDecl):
        params = ', '.join(f'MistyVal {p}' for p in node.params)
        self.emit_raw(f'MistyVal misty_{node.name}({params}) {{')
        self.indent_level = 1
        for stmt in node.body:
            self.gen_stmt(stmt)
        self.emit('return misty_null();')
        self.indent_level = 0
        self.emit_raw('}')
        self.emit_raw('')

    # ── statements ────────────────────────
    def gen_stmt(self, node):
        if isinstance(node, VarDecl) or isinstance(node, ConstDecl):
            name  = node.name if isinstance(node, VarDecl) else node.name
            value = node.value if isinstance(node, VarDecl) else node.value
            expr  = self.gen_expr(value)
            self.emit(f'MistyVal {name} = {expr};')

        elif isinstance(node, ReturnStmt):
            expr = self.gen_expr(node.value)
            self.emit(f'return {expr};')

        elif isinstance(node, ExprStmt):
            expr = self.gen_expr(node.expr)
            self.emit(f'{expr};')

        elif isinstance(node, IfStmt):
            cond = self.gen_expr(node.condition)
            self.emit(f'if (misty_truthy({cond})) {{')
            self.indent_level += 1
            for s in node.then_body:
                self.gen_stmt(s)
            self.indent_level -= 1
            if node.else_body:
                self.emit('} else {')
                self.indent_level += 1
                for s in node.else_body:
                    self.gen_stmt(s)
                self.indent_level -= 1
            self.emit('}')

        elif isinstance(node, WhileStmt):
            cond = self.gen_expr(node.condition)
            self.emit(f'while (misty_truthy({cond})) {{')
            self.indent_level += 1
            for s in node.body:
                self.gen_stmt(s)
            self.indent_level -= 1
            self.emit('}')

        elif isinstance(node, AssignExpr):
            target = self.gen_expr(node.target)
            value  = self.gen_expr(node.value)
            self.emit(f'{target} = {value};')

        elif isinstance(node, UseStmt):
            pass  # ignorar use statements

        elif isinstance(node, StructDecl):
            pass  # ya procesado arriba

        elif isinstance(node, ThrowStmt):
            msg = self.gen_expr(node.value)
            self.emit(f'fprintf(stderr, "Error: %s\\n", misty_to_str({msg}));')
            self.emit('exit(1);')

        elif isinstance(node, TryCatch):
            # try/catch simple — por ahora ejecuta el bloque directo
            for s in node.try_body:
                self.gen_stmt(s)

        else:
            self.emit(f'/* unhandled: {type(node).__name__} */')

    # ── expresiones ───────────────────────
    def gen_expr(self, node) -> str:
        if isinstance(node, NumberLit):
            if isinstance(node.value, float):
                return f'misty_float({node.value})'
            return f'misty_int({node.value})'

        if isinstance(node, StringLit):
            escaped = node.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'misty_str("{escaped}")'

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, BinaryExpr):
            return self.gen_binary(node)

        if isinstance(node, UnaryExpr):
            return self.gen_unary(node)

        if isinstance(node, CallExpr):
            return self.gen_call(node)

        if isinstance(node, MemberExpr):
            obj = self.gen_expr(node.obj)
            return f'{obj}.{node.member}'

        if isinstance(node, AssignExpr):
            target = self.gen_expr(node.target)
            value  = self.gen_expr(node.value)
            return f'({target} = {value})'

        if isinstance(node, StructInit):
            tmp = self.tmp()
            self.emit(f'Misty_{node.name} {tmp};')
            for fname, fval in node.fields.items():
                expr = self.gen_expr(fval)
                self.emit(f'{tmp}.{fname} = {expr};')
            return tmp

        return 'misty_null()'

    def gen_binary(self, node: BinaryExpr) -> str:
        l = self.gen_expr(node.left)
        r = self.gen_expr(node.right)
        op = node.op
        if op == '+':  return f'misty_add({l},{r})'
        if op == '-':  return f'misty_sub({l},{r})'
        if op == '*':  return f'misty_mul({l},{r})'
        if op == '/':  return f'misty_div({l},{r})'
        if op == '==': return f'misty_bool(misty_eq({l},{r}))'
        if op == '!=': return f'misty_bool(!misty_eq({l},{r}))'
        if op == '<':  return f'misty_bool(misty_lt({l},{r}))'
        if op == '>':  return f'misty_bool(misty_gt({l},{r}))'
        if op == '<=': return f'misty_bool(!misty_gt({l},{r}))'
        if op == '>=': return f'misty_bool(!misty_lt({l},{r}))'
        if op == '&&': return f'misty_bool(misty_truthy({l})&&misty_truthy({r}))'
        if op == '||': return f'misty_bool(misty_truthy({l})||misty_truthy({r}))'
        return 'misty_null()'

    def gen_unary(self, node: UnaryExpr) -> str:
        operand = self.gen_expr(node.operand)
        if node.op == '-':  return f'misty_sub(misty_int(0),{operand})'
        if node.op == '!':  return f'misty_bool(!misty_truthy({operand}))'
        if node.op == '++': return f'({operand}.ival++, {operand})'
        if node.op == '--': return f'({operand}.ival--, {operand})'
        return operand

    def gen_call(self, node: CallExpr) -> str:
        args = [self.gen_expr(a) for a in node.args]

        # print builtin
        if isinstance(node.callee, Identifier) and node.callee.name == 'print':
            if args:
                return f'(misty_print({args[0]}), misty_null())'
            return 'misty_null()'

        # str builtin
        if isinstance(node.callee, Identifier) and node.callee.name == 'str':
            if args:
                return f'misty_str(misty_to_str({args[0]}))'
            return 'misty_str("")'

        # llamada normal a función
        if isinstance(node.callee, Identifier):
            args_str = ', '.join(args)
            return f'misty_{node.callee.name}({args_str})'

        # método de struct
        if isinstance(node.callee, MemberExpr):
            obj    = self.gen_expr(node.callee.obj)
            member = node.callee.member
            args_str = ', '.join(args)
            return f'misty_{member}({args_str})'

        return 'misty_null()'


# ─────────────────────────────────────────
#  COMPILAR
# ─────────────────────────────────────────

def compile_file(source_path: str):
    base     = os.path.splitext(source_path)[0]
    c_path   = base + '.c'
    exe_path = base

    # leer fuente
    with open(source_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # lexer + parser
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast    = parser.parse()

    # generar C
    gen    = CGen()
    c_code = gen.generate(ast)

    # escribir .c
    with open(c_path, 'w', encoding='utf-8') as f:
        f.write(c_code)

    print(f'[MIg] Generated: {c_path}')

    # compilar con gcc
    result = subprocess.run(
        ['gcc', '-o', exe_path, c_path, '-lm'],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f'[MIg] gcc error:\n{result.stderr}')
        return False

    print(f'[MIg] Compiled:  {exe_path}')
    print(f'[MIg] Run with:  ./{os.path.basename(exe_path)}')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 mig_compile.py <file.my>')
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f'[MIg] File not found: {path}')
        sys.exit(1)

    success = compile_file(path)
    sys.exit(0 if success else 1)
