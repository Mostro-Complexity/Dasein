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


# json_parser = Lark.open('dasein.lark', rel_to=__file__, parser='lalr')
# text = '''student: struct {
#     grade: int32
#     age: uint8
#     name: string
# }'''
# tree = json_parser.parse(text)
# print(tree.pretty())
# print(TreeToJson().transform(tree))

json_parser = Lark.open('expression.lark', rel_to=__file__, parser='lalr')
text = '9-name+3*4.2!= 1 && name>= 8'
tree = json_parser.parse(text)
print(tree.pretty())
print(TreeToJson().transform(tree))

