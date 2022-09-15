from lark import Lark
from lark import Transformer


class TreeToJson(Transformer):
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
    d := 123
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
