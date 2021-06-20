import ast
import math
import builtins

from simpleeval import SimpleEval, safe_power, safe_mult

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
    "e",
    "factorial",
    "floor",
    "hypot",
    "log",
    "log10",
    "pi",
    "pow",
    "radians",
    "sin",
    "sinh",
    "sqrt",
    "tan",
    "tanh",
]
math_funcs = {func: getattr(math, func) for func in math_funcs}
builtin_funcs = ["abs", "round"]
builtin_funcs = {func: getattr(builtins, func) for func in builtin_funcs}  # type: ignore


def simple_eval():
    seval = SimpleEval()

    # remove some ops that we won't use, and add ^ as a power operator
    remove_ops = [ast.Is, ast.IsNot, ast.NotIn, ast.FloorDiv]
    add_ops = {ast.BitXor: safe_power, "x": safe_mult}
    for op in remove_ops:
        del seval.operators[op]
    seval.operators.update(add_ops)
    # pprint.PrettyPrinter(indent=3).pprint(seval.operators)

    # remove the default functions, because they're not too relevant, and replace them with ones we want
    funcs = {**math_funcs, **builtin_funcs, "foo": lambda: "bar"}
    seval.functions = funcs
    # pprint.PrettyPrinter(indent=3).pprint(seval.functions)

    remove_nodes = [ast.Slice, ast.IfExp, ast.JoinedStr, ast.Subscript, ast.Index]
    seval.nodes = {
        node_hash: node
        for node_hash, node in seval.nodes.items()
        if node_hash not in remove_nodes
    }
    # pprint.PrettyPrinter(indent=3).pprint(seval.nodes)
    return seval


def can_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
