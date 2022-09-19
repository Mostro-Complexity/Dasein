from lark import Lark
from lark import Transformer
import uuid


class Token(object):
    def __init__(self, value, type) -> None:
        self.value = value
        self.type = type

    def __repr__(self) -> str:
        return "Token(value={:s}, type={:s})".format(self.value, self.type)


class Variable(object):
    def __init__(self, code, place=None, type="NA"):
        self.code = code
        self.place = place
        self.type = type

    def __repr__(self) -> str:
        return "Variable(code={:s}, place={:s}, type={:s})".format(str(self.code), str(self.place), self.type)


class Parameter(object):
    def __init__(self, place=None, type="NA") -> None:
        self.place = place
        self.type = type

    def __repr__(self) -> str:
        return "Parameter(place={:s}, type={:s})".format(str(self.place), self.type)


class Function(object):
    def __init__(self, name, place=None, inputs=None, outputs=None, code=None) -> None:
        self.place = place
        self.inputs = inputs
        self.outputs = outputs
        self.name = name
        self.code = code

    def __repr__(self) -> str:
        if isinstance(self.outputs, Token):
            return "Function(name={:s}, place={:s}, inputs={:s}, outputs={:s})".format(
                self.name,
                str(self.place),
                ", ".join([str(i) for i in self.inputs]),
                str(self.outputs)
            )
        else:
            return "Function(name={:s}, place={:s}, inputs={:s}, outputs={:s})".format(
                self.name,
                str(self.place),
                ", ".join([str(i) for i in self.inputs]),
                ", ".join([str(i) for i in self.outputs])
            )


class LexTransformer(Transformer):
    def __init__(self, visit_tokens: bool = True, out_path: str = None) -> None:
        super().__init__(visit_tokens)
        self.out_path = out_path

    def start(self, items):
        for i in items:
            if isinstance(i, Function) and i.name == "main" and self.out_path is not None:
                with open(self.out_path, mode='w', encoding='utf-8') as f:
                    f.write('\n'.join(i.code))
        return items

    def string(self, s):
        return s

    def number(self, n):
        (n,) = n
        return float(n)

    def list(self, items):
        return list(items)

    def dict(self, items):
        return dict(items)

    def claim(self, items):
        return items[0]

    def type_claim(self, items):
        return items

    def typename(self, items):
        return Token(value=items[0].value, type="typename")

    def sum(self, items):
        return items

    def atom(self, items):
        return items[0]

    def literal_string(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def literal_signed_float(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def literal_signed_int(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def literal_int(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def literal_float(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def literal_int(self, items):
        return Variable(code=[], place=items[0].value, type="const")

    def int64(self, items):
        return Token(value="int64", type="basic_definition")

    def int32(self, items):
        return Token(value="int32", type="basic_defination")

    def string(self, items):
        return Token(value="string", type="basic_defination")

    def definition(self, items):
        return items[0]

    def type_claim(self, items):
        return items

    def param_claim(self, items):
        id = uuid.uuid4()
        return Parameter(place=str(id), type=items[1].value)

    def add(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[0].code)
        code.extend(items[1].code)
        code.append("{:s} := {:s} + {:s}".format(str(id), items[0].place, items[1].place))
        return Variable(code=code, place=str(id), type="var")

    def sub(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[0].code)
        code.extend(items[1].code)
        code.append("{:s} := {:s} - {:s}".format(str(id), items[0].place, items[1].place))
        return Variable(code=code, place=str(id), type="var")

    def mul(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[0].code)
        code.extend(items[1].code)
        code.append("{:s} := {:s} * {:s}".format(str(id), items[0].place, items[1].place))
        return Variable(code=code, place=str(id), type="var")

    def div(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[0].code)
        code.extend(items[1].code)
        code.append("{:s} := {:s} / {:s}".format(str(id), items[0].place, items[1].place))
        return Variable(code=code, place=str(id), type="var")

    def single_statement(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[1].code)
        code.append("{:s} := {:s}".format(str(id), items[1].place))
        return Variable(code=code, place=str(id), type="var")

    def statements(self, items):
        id = uuid.uuid4()
        code = []
        for i in items:
            if isinstance(i, Variable):
                code.extend(i.code)
        return Variable(code=code, place=str(id), type="executable")

    def func_input_params(self, items):
        return items

    def func_output_params(self, items):
        return items

    def func_definition(self, items):
        if items[0].type == 'func_constraint':
            raise NotImplemented
        else:
            return Function(
                name=items[0].value, place=items[-1].place,
                inputs=items[-3], outputs=items[-2], code=items[-1].code
            )

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False


json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
text = '''intern type student struct {
    grade: int32
    age: uint8
    name: string
}

func main(a: int64, b: string) -> (student, cat) {
    c := "aaaabbbccc"
    d := 123 + 12 * 99 - 1
    e := -12
}

func foo1(a: int64) -> student {
    fff := "asdfads"
    e := -12
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
print(LexTransformer(out_path="output.txt").transform(tree))
