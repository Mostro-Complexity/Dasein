from lark import Lark
from lark.tree import Tree
from lark.lexer import Token
from llvmlite import ir
from typing import TypeVar, Dict, Set, Any, Tuple, List, Union, Optional
from addict import Dict as NamedDict


FORWARD_METHOD_TITLE = "{:s}_forward"
BACKWARD_METHOD_TITLE = "{:s}_backward"


class Variable(object):
    def __init__(self, name: str, type: Union[ir.DoubleType, ir.FloatType, ir.HalfType, ir.IntType]) -> None:
        self.name = name
        self.type = type
        self.arg = None


class Function(ir.Function):
    def __init__(self, module, ftype, name) -> None:
        super().__init__(module, ftype, name)
        self.block = self.append_basic_block(name="{:s}_entry".format(name))
        self.builder = ir.IRBuilder(self.block)


class ContextStack(object):
    def __init__(self, arr: Optional[List[Union[Dict, NamedDict]]] = None) -> None:
        if arr is None:
            self._stack = []
        else:
            self._stack = arr

    def push(self) -> Dict:
        self._stack.append(self._stack[-1].copy())
        return self._stack[-1]

    def pop(self) -> Union[Dict, NamedDict]:
        self._stack.pop()
        return self._stack[-1]

    def top(self) -> Union[Dict, NamedDict]:
        return self._stack[-1]


class RecursiveTransformerWithContext(object):
    """Top-down ASTree visitor, recursive.

    Visiting a node calls its methods (provided by the user via inheritance) according to ``tree.data``
    """

    def transform(self, tree: Tree[TypeVar('_Leaf_T')]) -> Tree[TypeVar('_Leaf_T')]:
        "Visit the tree, starting at the root, and ending at the leaves"

        if isinstance(tree, Tree):
            self._call_userfunc(tree)

        return tree

    def __default__(self, children):
        """Default function that is called if there is no attribute matching ``data``

        Can be overridden. Defaults to creating a new copy of the tree node (i.e. ``return Tree(data, children, meta)``)
        """
        return children

    def _call_userfunc(self, tree):
        if isinstance(tree.data, Token):
            return getattr(self, tree.data.value, self.__default__)(tree.children)
        elif isinstance(tree.data, str):
            return getattr(self, tree.data, self.__default__)(tree)


class IRTransformer(RecursiveTransformerWithContext):
    def __init__(self) -> None:
        super().__init__()
        self.stack = ContextStack([NamedDict()])
        self.symbol_stack = ContextStack([dict()])
        self.module = ir.Module(name=__file__)

    def start(self, items):
        for i in items:
            getattr(self, i.data, self.__default__)(i.children)
        return items

    # def string(self, context, s):
    #     return context, s

    # def number(self, context, n):
    #     (n,) = n
    #     return context, float(n)

    # def list(self, context, items):
    #     return context, list(items)

    # def dict(self, context, items):
    #     return context, dict(items)

    def claim(self, items):
        getattr(self, items[0].data.value, self.__default__)(items[0].children)
        return items

    def definition(self, items):
        ''' -> func_definition
        '''
        getattr(self, items[0].data.value, self.__default__)(items[0].children)
        return items

    # def type_claim(self, context, items):
    #     return context, items

    # def typename(self, context, items):
    #     return context, items
    def varname(self, items) -> Token:
        self.stack.top()[items[0].value] = None
        return items[0]

    # def literal_string(self, context, items):
    #     return context, items

    def literal_signed_float(self, items) -> ir.Constant:
        return self._estimate_float_bits(float(items[0].value))

    def literal_signed_int(self, items) -> ir.Constant:
        return self._estimate_int_bits(int(items[0].value))

    def _estimate_int_bits(self, val: int) -> ir.Constant:
        if -2**31 <= val and val < 2**31:
            return ir.Constant(ir.IntType(32), val)
        else:
            return ir.Constant(ir.IntType(64), val)

    def _estimate_float_bits(self, val: float) -> ir.Constant:
        if -3.4E+38 <= val and val < 3.4E+38:
            return ir.Constant(ir.FloatType(), val)
        else:
            return ir.Constant(ir.DoubleType(), val)

    def atom(self, items):
        ''' -> Union[literal_string, literal_signed_float, literal_signed_int]
        '''
        return getattr(self, items[0].data.value, self.__default__)(items[0].children)

    def bool(self, items, is_output=False) -> Union[ir.IntType, ir.PointerType]:
        symbol_context = self.symbol_stack.top()
        if is_output:
            symbol_context[varname] = Variable(
                name=(varname := items[0].value), type=ir.IntType(8).as_pointer()
            )
        else:
            symbol_context[varname] = Variable(
                name=(varname := items[0].children[0].value), type=ir.IntType(64)
            )
        return symbol_context[varname]

    def int64(self, items, is_output=False) -> Union[ir.IntType, ir.PointerType]:
        symbol_context = self.symbol_stack.top()
        if is_output:
            symbol_context[varname] = Variable(
                name=(varname := items[0].value), type=ir.IntType(64).as_pointer()
            )
        else:
            symbol_context[varname] = Variable(
                name=(varname := items[0].children[0].value), type=ir.IntType(64)
            )
        return symbol_context[varname]

    def int32(self, items, is_output=False) -> Union[ir.IntType, ir.PointerType]:
        symbol_context = self.symbol_stack.top()
        if is_output:
            symbol_context[varname] = Variable(
                name=(varname := items[0].value), type=ir.IntType(32).as_pointer()
            )
        else:
            symbol_context[(varname := items[0].children[0].value)] = Variable(
                name=varname, type=ir.IntType(32)
            )
        return symbol_context[varname]

    def float32(self, items, is_output=False) -> Union[ir.FloatType, ir.PointerType]:
        symbol_context = self.symbol_stack.top()
        if is_output:
            symbol_context[varname] = Variable(
                name=(varname := items[0].value), type=ir.DoubleType().as_pointer()
            )
        else:
            symbol_context[varname] = Variable(
                name=(varname := items[0].children[0].value), type=ir.DoubleType()
            )
        return symbol_context[varname]

    def float64(self, items, is_output=False) -> Union[ir.FloatType, ir.PointerType]:
        symbol_context = self.symbol_stack.top()
        if is_output:
            symbol_context[varname] = Variable(
                name=(varname := items[0].value), type=ir.DoubleType().as_pointer()
            )
        else:
            symbol_context[varname] = Variable(
                name=(varname := items[0].children[0].value), type=ir.DoubleType()
            )
        return symbol_context[varname]

    # def string(self, context, items):
    #     return context, items

    def type_claim(self, items):
        return items

    def param_claim(self, items, is_output):
        return getattr(self, items[1].data, self.__default__)(items, is_output=is_output)

    def add(self, items):
        items = self._op(items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(items, items[0].constant + items[1].constant)
        else:
            return self._calc(
                items,
                lambda builder, a, b: builder.fadd(a, b, name="add")
            )

    def sub(self, items):
        items = self._op(items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(items, items[0].constant - items[1].constant)
        else:
            return self._calc(
                items,
                lambda builder, a, b: builder.fsub(a, b, name="sub")
            )

    def mul(self, items):
        items = self._op(items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(items, items[0].constant * items[1].constant)
        else:
            return self._calc(
                items,
                lambda builder, a, b: builder.fmul(a, b, name="mul")
            )

    def div(self, items):
        items = self._op(items)
        if isinstance(items[0], ir.Constant) and isinstance(items[1], ir.Constant):
            return self._literal_calc(items, items[0].constant / items[1].constant)
        else:
            return self._calc(
                items,
                lambda builder, a, b: builder.fdiv(a, b, name="div")
            )

    def _literal_calc(self, items: List, result: Union[int, float]) -> List:
        if isinstance(items[0].type, ir.DoubleType) or isinstance(items[1].type, ir.DoubleType):
            return ir.Constant(ir.DoubleType(), result)
        if isinstance(items[0].type, ir.FloatType) or isinstance(items[1].type, ir.FloatType):
            return self._estimate_float_bits(result)
        return self._estimate_int_bits(result)

    def _calc(self, items, calc_handler):
        symbol_ctx = self.symbol_stack.top()
        a: ir.Argument = symbol_ctx[items[0].value].arg
        b: ir.Argument = symbol_ctx[items[1].value].arg
        builder: ir.IRBuilder = self.stack.top().func.builder
        if isinstance(a.type, ir.DoubleType) or isinstance(b.type, ir.DoubleType):
            if not isinstance(a.type, ir.DoubleType):
                a = builder.sitofp(a, ir.DoubleType())
            if not isinstance(b.type, ir.DoubleType):
                b = builder.sitofp(b, ir.DoubleType())
            return calc_handler(builder, a, b)
        if isinstance(a.type, ir.FloatType) or isinstance(b.type, ir.FloatType):
            if not isinstance(a.type, ir.FloatType):
                a = builder.sitofp(a, ir.FloatType())
            if not isinstance(b.type, ir.FloatType):
                b = builder.sitofp(b, ir.FloatType())
            return calc_handler(symbol_ctx, a, b)
        return calc_handler(symbol_ctx, a, b)

    def _op(self, items):
        atomic = []
        for op in items:
            if isinstance(op, Token):
                a = getattr(self, items[1].data, self.__default__)(items[1].children)
            else:
                a = getattr(self, op.data, self.__default__)(op.children)
            atomic.append(a)
        return atomic

    def assignment_statement(self, items):
        out = getattr(self, items[1].data, self.__default__)(items[1].children)
        cur_func = self.stack.top().func
        s_ptr = cur_func.builder.alloca(out.type)
        cur_func.builder.store(out, s_ptr)
        return s_ptr

    def return_clause(self, items):
        return getattr(self, items[0].data, self.__default__)(items[0].children)

    def func_input_params(self, items):
        (context := self.stack.top()).func_params = []
        for i in items:
            param = getattr(self, i.data.value, self.__default__)(i.children, False)
            context.func_params.append(param)
        return items

    def func_output_params(self, items):
        context = self.stack.top()
        for i in items:  # List[Union[float32, float64, int32, int64]]
            param = getattr(self, i.children[0].value, self.__default__)(i.children, True)
            context.func_params.append(param)
        context.ftype = ir.FunctionType(ir.IntType(8), [param.type for param in context.func_params])
        return items

    def func_definition(self, items):
        func_name = items[0].children[0].value
        self.stack.top().func_name = func_name
        for i in items[1:]:  # func_input_params -> func_output_params -> statements
            getattr(self, i.data.value, self.__default__)(i.children)
        return items

    def statements(self, items):
        context = self.stack.push()
        context.func = Function(self.module, context.ftype, context.func_name)
        self.symbol_stack.top()[context.func_name] = context.func
        self.symbol_stack.push()
        for arg, var in zip(context.func.args, context.func_params):
            var.arg = arg

        for i in items:  # List[single_statement]
            if not isinstance(i, Token):
                getattr(self, i.data, self.__default__)(i.children)

        self.stack.pop()
        self.symbol_stack.pop()
        return items

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False


json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
text = '''
func main(a: float64, b: float32) -> (float32, int32) {
    d := 123 + 12 * 99 - 1
    e := -12.5
    return e, d
}

func foo1(a: int64, b: float32) -> float64 {
    e := -12.4
    return e
}

func foo2(a: float32, b: float32) -> float32 {
    return a + b
}

func foo3(a: int64, b: float32) -> float32 {
    return a + b
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
transformer = IRTransformer()
transformer.transform(tree)
print(transformer.module)
