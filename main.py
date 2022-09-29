from reprlib import recursive_repr
from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from lark.visitors import Transformer
from llvmlite import ir
from typing import TypeVar, Dict, Set, Any, Tuple, List, Union
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

    def literal_signed_float(self, context, items):  # TODO: 确定具体类型
        return context, self._estimate_float_bits(float(items[0].value))

    def literal_signed_int(self, context, items):  # TODO: 确定具体类型，以及混合类型的运算
        return context, self._estimate_int_bits(int(items[0].value))

    def _estimate_int_bits(self, val: int):
        if -2**31 <= val and val < 2**31:
            return ir.Constant(ir.IntType(32), val)
        else:
            return ir.Constant(ir.IntType(64), val)

    def _estimate_float_bits(self, val: float):
        if -3.4E+38 <= val and val < 3.4E+38:
            return ir.Constant(ir.FloatType(), val)
        else:
            return ir.Constant(ir.DoubleType(), val)

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
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(context, items, items[0].constant + items[1].constant)
        else:
            return context, context.builder.fadd(*items, name="add")

    def sub(self, context, items):
        context, items = self._op(context, items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(context, items, items[0].constant - items[1].constant)
        else:
            return context, context.builder.fsub(*items, name="sub")

    def mul(self, context, items):
        context, items = self._op(context, items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(context, items, items[0].constant * items[1].constant)
        else:
            return context, context.builder.fmul(*items, name="mul")

    def div(self, context, items):
        context, items = self._op(context, items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(context, items, items[0].constant / items[1].constant)
        else:
            return context, context.builder.fdiv(*items, name="div")

    def _literal_calc(self, context: NamedDict, items: List, result: Union[int, float]) -> Tuple[NamedDict, List]:
        if isinstance(items[0].type, ir.DoubleType) or isinstance(items[1].type, ir.DoubleType):
            return context, ir.Constant(ir.DoubleType(), result)
        if isinstance(items[0].type, ir.FloatType) or isinstance(items[1].type, ir.FloatType):
            return context, self._estimate_float_bits(result)
        return context, self._estimate_int_bits(result)

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
        s_ptr = context.builder.alloca(out.type)
        context.builder.store(out, s_ptr)
        return context, s_ptr

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
    d := 123.4 + 12 * 99.8 - 1
    e := -12.5
}

func foo1(a: int64, b: float32) -> float64 {
    e := -12
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
context = NamedDict(module=ir.Module(name=__file__))
context, _ = IRTransformer().transform(context, tree)
print(context.module)
