# from llvmlite import ir

# # Create some useful types
# double = ir.DoubleType()
# fnty = ir.FunctionType(double, (double, double))

# # Create an empty module...
# module = ir.Module(name=__file__)
# # and declare a function named "fpadd" inside it
# func = ir.Function(module, fnty, name="fpadd")

# # Now implement the function
# block = func.append_basic_block(name="entry")
# builder = ir.IRBuilder(block)
# a, b = func.args
# result = builder.fadd(a, b, name="res")
# builder.ret(result)

# # Print the module IR
# print(module)


class Object:
    def __init__(self) -> None:
        self._before_func_flag = True
        self._after_func_flag = False

    def before(func):
        print(1)

        def warp(self, *args, **kwargs):
            if self._before_func_flag:
                return func(self, *args, **kwargs)

        return warp

    def after(func):
        print(2)

        def warp(self, *args, **kwargs):
            if self._after_func_flag:
                return func(self, *args, **kwargs)

        return warp

    @before
    def myfunc(self):
        print("Hellow Before")

    @after
    def myfunc(self):
        print("Hellow After")


oo = Object()
a = oo.myfunc()
oo._before_func_flage = False
oo._after_func_flag = True
b = oo.myfunc()

