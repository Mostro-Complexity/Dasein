from reprlib import recursive_repr
from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from lark.visitors import Transformer
from llvmlite import ir
from typing import TypeVar, Dict, Set, Any
from addict import Dict as NamedDict
from enum import Enum


FORWARD_METHOD_TITLE = "{:s}_forward"
BACKWARD_METHOD_TITLE = "{:s}_backward"


class RecursiveTransformerWithContext(object):
    """Top-down ASTree visitor, recursive.

    Visiting a node calls its methods (provided by the user via inheritance) according to ``tree.data``
    """

    def transform(self, context: NamedDict, tree: Tree[TypeVar('_Leaf_T')]) -> Tree[TypeVar('_Leaf_T')]:
        "Visit the tree, starting at the root, and ending at the leaves"

        if isinstance(tree, Tree):
            context, _ = self._call_userfunc(context, tree)

        return context, tree

    def __default__(self, context, children):
        """Default function that is called if there is no attribute matching ``data``

        Can be overridden. Defaults to creating a new copy of the tree node (i.e. ``return Tree(data, children, meta)``)
        """
        return context, children

    def _call_forwardfunc(self, context, tree):
        if isinstance(tree.data, Token):
            return getattr(self,  FORWARD_METHOD_TITLE.format(tree.data.value), self.__default__)(context, tree.children)
        elif isinstance(tree.data, str):
            return getattr(self, tree.data, self.__default__)(context, tree)

    def _call_backwardfunc(self, context, tree):
        if isinstance(tree.data, Token):
            return getattr(self, BACKWARD_METHOD_TITLE.format(tree.data.value), self.__default__)(context, tree.children)
        elif isinstance(tree.data, str):
            return getattr(self, tree.data, self.__default__)(context, tree)

    def _call_userfunc(self, context, tree):
        if isinstance(tree.data, Token):
            return getattr(self, tree.data.value, self.__default__)(context, tree.children)
        elif isinstance(tree.data, str):
            return getattr(self, tree.data, self.__default__)(context, tree)


class IRTransformer(RecursiveTransformerWithContext):

    def start(self, context, items):
        for i in items:
            context, _ = getattr(self, i.data, self.__default__)(context, i.children)
        return context, items

    # def string(self, context, s):
    #     return context, s

    # def number(self, context, n):
    #     (n,) = n
    #     return context, float(n)

    # def list(self, context, items):
    #     return context, list(items)

    # def dict(self, context, items):
    #     return context, dict(items)

    def claim(self, context, items):
        context, _ = getattr(self, items[0].data.value, self.__default__)(context, items[0].children)
        return context, items

    def definition(self, context, items):
        context, _ = getattr(self, items[0].data.value, self.__default__)(context, items[0].children)
        return context, items

    # def type_claim(self, context, items):
    #     return context, items

    # def typename(self, context, items):
    #     return context, items

    # def sum(self, context, items):
    #     return context, items

    # def atom(self, context, items):
    #     return context, items[0]

    # def literal_string(self, context, items):
    #     return context, items

    def literal_signed_float(self, context, items):
        return context, ir.Constant(ir.DoubleType(), items[0].value)

    def literal_signed_int(self, context, items):
        return context, ir.Constant(ir.IntType(64), items[0].value)

    # def literal_int(self, context, items):
    #     return context, items

    # def literal_float(self, context, items):
    #     return context, items

    # def literal_int(self, context, items):
    #     return context, items

    def int64(self, context, items):
        return context, ir.IntType(64)

    def int32(self, context, items):
        return context, ir.IntType(32)

    def float32(self, context, items):
        return context, ir.FloatType()

    def float64(self, context, items):
        return context, ir.DoubleType()

    # def string(self, context, items):
    #     return context, items

    def type_claim(self, context, items):
        return context, items

    def type_claim(self, context, items):
        return context, items

    def param_claim(self, context, items):
        return context, items

    def param_claim(self, context, items):
        return context, items

    def add(self, context, items):
        context, items = self._op(context, items)
        return context, context.builder.fadd(*items, name="add")

    def sub(self, context, items):
        context, items = self._op(context, items)
        return context, context.builder.fsub(*items, name="sub")

    def mul(self, context, items):
        context, items = self._op(context, items)
        return context, context.builder.fmul(*items, name="mul")

    def div(self, context, items):
        context, items = self._op(context, items)
        return context, context.builder.fdiv(*items, name="div")

    def _op(self, context, items):
        atomic = []
        for op in items:
            if isinstance(op, Token):
                context, a = getattr(self, items[1].data, self.__default__)(context, items[1].children)
            else:
                context, a = getattr(self, op.data, self.__default__)(context, op.children)
            atomic.append(a)
        return context, atomic

    def single_statement(self, context, items):
        context, out = getattr(self, items[1].data, self.__default__)(context, items[1].children)
        return context, out

    def func_input_params(self, context, items):
        func_input_params = []
        for i in items:
            context, param = getattr(self, i.children[1].data, self.__default__)(context, i.children)
            func_input_params.append(param)
        context.func_input_params = tuple(func_input_params)
        return context, items

    def func_output_params(self, context, items):
        double = ir.DoubleType()
        ftype = ir.FunctionType(double, context.func_input_params)
        context.func = ir.Function(context.module, ftype, name=context.func_name)
        context.block = context.func.append_basic_block(name="{:s}_entry".format(context.func_name))
        context.builder = ir.IRBuilder(context.block)
        return context, items

    def func_definition(self, context, items):
        context.func_name = items[0].children[0].value
        for i in items[1:]:
            context, _ = getattr(self, i.data.value, self.__default__)(context, i.children)

        return context, items

    def statements(self, context, items):
        for i in items:
            if not isinstance(i, Token):
                context, _ = getattr(self, i.data.value, self.__default__)(context, i.children)
        # a, b = context.func.args
        # a = context.builder.sitofp(a, ir.DoubleType())
        # b = context.builder.sitofp(b, ir.DoubleType())
        # context.builder.ret(context.builder.fadd(a, b, name="res"))
        return context, items

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False


json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
text = '''
func main(a: float64, b: float32) -> (int64, bool) {
    d := 123 + 12 * 99 - 1
    e := -12
}

func foo1(a: int64, b: float32) -> float64 {
    e := -12
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
context = NamedDict(module=ir.Module(name=__file__))
print(IRTransformer().transform(context, tree))
print(context.module)
