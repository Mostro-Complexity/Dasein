from lark import Lark
from lark import Transformer
import uuid


class Nonterminal(object):
    def __init__(self, code, place, type):
        self.code = code
        self.place = place
        self.type = type

    def __repr__(self) -> str:
        return "Nonterminal(code={:s}, place={:s}, type={:s})".format(str(self.code), str(self.place), self.type)


class TreeToJson(Transformer):
    def start(self, items):
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
        return items

    def typename(self, items):
        return items

    def basic_expression(self, items):
        return items

    def basic_varbody(self, items):
        return items[0]

    def literal_string(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def literal_signed_float(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def literal_signed_int(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def literal_int(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def literal_float(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def literal_int(self, items):
        return Nonterminal(code=[], place=items[0].value, type="const")

    def add_expression(self, items):
        id = uuid.uuid4()
        code = []
        code.extend(items[0].code)
        code.extend(items[1].code)
        code.append("{:s} := {:s} + {:s}".format(str(id), items[0].place, items[1].place))
        return Nonterminal(code=code, place=str(id), type="var")

    def single_executable_stmt(self, items):
        id = uuid.uuid4()
        code = []
        code.append("{:s} := {:s}".format(str(id), items[1].place))
        return Nonterminal(code=code, place=str(id), type="var")

    def null(self, _): return None
    def true(self, _): return True
    def false(self, _): return False


json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
text = '''intern student: struct {
    grade: int32
    age: uint8
    name: string
}

foo: (a: int64, b: string) -> student {
    c := "aaaabbbccc"
    d := 123 + 12
    e := -12
}

foo1: (a: int64) -> student {
    fff := "asdfads"
    e := -12
}
'''
tree = json_parser.parse(text)
print(tree.pretty())
print(TreeToJson().transform(tree))
