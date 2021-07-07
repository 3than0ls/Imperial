import ast
import builtins
import math

from simpleeval import SimpleEval

math_funcs = [
    "acos",
    "acosh",
    "asin",
    "asinh",
    "atan",
    "atan2",
    "atanh",
    "ceil",
    "cos",
    "cosh",
    "degrees",
    "factorial",
    "floor",
    "hypot",
    "log",
    "log10",
    "pow",
    "radians",
    "sin",
    "sinh",
    "sqrt",
    "tan",
    "tanh",
]
math_funcs = {func: getattr(math, func) for func in math_funcs}
builtin_funcs = ["abs"]
builtin_funcs = {func: getattr(builtins, func) for func in builtin_funcs}  # type: ignore

funcs = {**math_funcs, **builtin_funcs}
symbols = {symbol: getattr(math, symbol) for symbol in ["e", "pi"]}


def simple_eval():
    seval = SimpleEval()

    # remove some ops that we won't use, and add ^ as a power operator
    remove_ops = [ast.Is, ast.IsNot, ast.NotIn, ast.FloorDiv]
    for op in remove_ops:
        del seval.operators[op]

    # remove the default functions, because they're not too relevant, and replace them with ones we want
    seval.functions = {**funcs, **symbols}

    remove_nodes = [ast.Slice, ast.IfExp, ast.JoinedStr, ast.Subscript, ast.Index]
    seval.nodes = {
        node_hash: node
        for node_hash, node in seval.nodes.items()
        if node_hash not in remove_nodes
    }
    return seval