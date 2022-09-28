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
        context, _ = self._call_forwardfunc(context, tree)

        for child in tree.children:
            if isinstance(child, Tree):
                context, _ = self.transform(context, child)

        context, _ = self._call_backwardfunc(context, tree)
        return context, tree

    def __default__(self, context, children):
        """Default function that is called if there is no attribute matching ``data``

        Can be overridden. Defaults to creating a new copy of the tree node (i.e. ``return Tree(data, children, meta)``)
        """
        assert tree.data.value != "func_definition"
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


class IRTransformer(RecursiveTransformerWithContext):

    # def start(self, context, items):
    #     return context, items

    # def string(self, context, s):
    #     return context, s

    # def number(self, context, n):
    #     (n,) = n
    #     return context, float(n)

    # def list(self, context, items):
    #     return context, list(items)

    # def dict(self, context, items):
    #     return context, dict(items)

    # def claim(self, context, items):
    #     return context, items

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

    # def literal_signed_float(self, context, items):
    #     return context, items

    # def literal_signed_int(self, context, items):
    #     return context, items

    # def literal_int(self, context, items):
    #     return context, items

    # def literal_float(self, context, items):
    #     return context, items

    # def literal_int(self, context, items):
    #     return context, items

    # def int64(self, context, items):
    #     return context, items

    # def int32(self, context, items):
    #     return context, items

    # def string(self, context, items):
    #     return context, items

    def definition_forward(self, context, items):
        return context, items

    def definition_backward(self, context, items):
        return context, items

    def type_claim_forward(self, context, items):
        return context, items

    def type_claim_backward(self, context, items):
        return context, items

    def param_claim_forward(self, context, items):
        return context, items

    def param_claim_backward(self, context, items):
        return context, items

    def add_forward(self, context, items):
        return context, items

    def add_backward(self, context, items):
        return context, items

    def sub_forward(self, context, items):
        return context, items

    def sub_backward(self, context, items):
        return context, items

    def mul_forward(self, context, items):
        return context, items

    def div_forward(self, context, items):
        return context, items

    def div_backward(self, context, items):
        return context, items
    # def single_statement(self, context, items):
    #     return context, items

    def func_input_params_forward(self, context, items):
        return context, items

    def func_input_params_backward(self, context, items):
        func_input_params = []
        for i in items:  # extremely inefficient
            if i.children[1].data == 'int64':
                func_input_params.append(ir.IntType(64))
            elif i.children[1].data == 'float64':
                func_input_params.append(ir.DoubleType())
            elif i.children[1].data == 'float32':
                func_input_params.append(ir.FloatType())
            elif i.children[1].data == 'int32':
                func_input_params.append(ir.IntType(32))
        context.func_input_params = tuple(func_input_params)
        return context, items

    def func_output_params_forward(self, context, items):
        return context, items

    def func_output_params_backward(self, context, items):
        # context.func_output_params = items.value
        double = ir.DoubleType()
        ftype = ir.FunctionType(double, context.func_input_params)
        context.func = ir.Function(context.module, ftype, name=context.func_name)
        context.block = context.func.append_basic_block(name="{:s}_entry".format(context.func_name))
        context.builder = ir.IRBuilder(context.block)
        return context, items

    def func_definition_forward(self, context, items):
        context.func_name = items[0].children[0].value
        return context, items

    def func_definition_backward(self, context, items):
        return context, items

    def statements_forward(self, context, items):
        return context, items

    def statements_backward(self, context, items):
        a, b = context.func.args
        a = context.builder.sitofp(a, ir.DoubleType())
        b = context.builder.sitofp(b, ir.DoubleType())
        context.builder.ret(context.builder.fadd(a, b, name="res"))
        return context, items

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False


json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
text = '''
func main(a: float64, b: float32) -> (int64, bool) {
    c := "aaaabbbccc"
    d := 123 + 12 * 99 - 1
    e := -12
}

func foo1(a: int64, b: float32) -> float64 {
    fff := "asdfads"
    e := -12
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
context = NamedDict(module=ir.Module(name=__file__))
print(IRTransformer().transform(context, tree))
print(context.module)
