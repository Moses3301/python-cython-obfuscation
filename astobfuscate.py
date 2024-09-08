import ast
from ast import *
import astor.code_gen
import random
import os
import sys
import copy


def random_string(minlength, maxlength):
    """
    Horrifying variable names consisting entirely of lookalikes:
    Digit ones, lowercase els, digit zeroes, uppercase ohs
    """
    return random.choice('lO') + ''.join(random.choice('lO10') for _ in range(random.randint(minlength, maxlength)))


def import_node(name, newname, froms=None):
    if froms:
        froms = [Str(from_name) for from_name in froms]
    else:
        froms = []
    """Import module obfuscation"""
    # import sys -> sys = __import__('sys', globals(), locals(), [], 0)
    return Assign(
        targets=[Name(id=newname, ctx=Store())],
        value=Call(func=Name(id='__import__', ctx=Load()),
                   args=[Str(s=name),
                         Call(func=Name(id='globals', ctx=Load()), args=[],
                              keywords=[], starargs=None, kwargs=None),
                         Call(func=Name(id='locals', ctx=Load()), args=[],
                              keywords=[], starargs=None, kwargs=None),
                         List(elts=froms, ctx=Load()), Num(n=0)],
                   keywords=[], starargs=None, kwargs=None))


def obfuscate_binary(operator, newname):
    arg1 = random_string(20, 20)
    arg2 = random_string(20, 20)
    return Assign(targets=[Name(id=newname, ctx=Store())],
                  value=Lambda(args=arguments(args=[arg(arg=arg1, annotation=None), arg(arg=arg2, annotation=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                               body=BinOp(left=Name(id=arg1, ctx=Load()), op=operator(), right=Name(id=arg2, ctx=Load()))))


def obfuscate_string(s):
    """Various String Obfuscation routines."""
    # Vars we might use
    var1 = random_string(20, 20)
    var2 = random_string(20, 20)

    random_bytes = os.urandom(len(s))

    # For xor combining two bytestrings
    pair1 = random_bytes
    pair2 = bytes([
        x ^ y for x, y in zip(random_bytes, s.encode('utf-8'))
    ])

    # Divisor for filtering into an empty list
    random_divisor = random.randint(2, 6)

    chars = list(filter(lambda x: ord(x) % random_divisor == 0, [chr(x) for x in range(0, 126)]))

    list_of_chars = ''.join([random.choice(chars) for _ in range(15)])



    table0 = [
        # '' -> ''
        lambda: Str(s=''),
        # Filter out all characters whose ascii values aren't divisible by a certain value, leaving an empty string
        lambda: Call(func=Attribute(value=Str(s=''), attr='join', ctx=Load()), args=[Call(func=Name(id='filter', ctx=Load()), args=[Lambda(args=arguments(args=[arg(arg=var1, annotation=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=Compare(left=BinOp(left=Call(func=Name(id='ord', ctx=Load()), args=[Name(id=var1, ctx=Load())], keywords=[]), op=Mod(), right=Num(n=random_divisor)), ops=[NotEq()], comparators=[Num(n=0)])), Bytes(s=list_of_chars)], keywords=[])], keywords=[])
    ]

    table1 = [
        # 'a' -> 'a'
        lambda x: Str(s=chr(x)),
        # 'a' -> chr(0x61)
        lambda x: Call(func=Name(id='chr', ctx=Load()), args=[Num(n=x)],
                       keywords=[], starargs=None, kwargs=None),
    ]

    table = [
        # 'abc' -> 'a' + 'bc'
        lambda x: BinOp(left=Str(s=x[:len(x)//2]),
                        op=Add(),
                        right=Str(s=x[len(x)//2:])),
        # 'abc' -> 'cba'[::-1]
        lambda x: Subscript(value=Str(s=x[::-1]),
                            slice=Slice(lower=None, upper=None,
                                        step=Num(n=-1)),
                            ctx=Load()),
        # xor two bytestrings together in a list comprehension
        lambda x: Call(func=Attribute(value=Str(s=''), attr='join', ctx=Load()), args=[GeneratorExp(elt=Call(func=Name(id='chr', ctx=Load()), args=[BinOp(left=Name(id=var1, ctx=Load()), op=BitXor(), right=Name(id=var2, ctx=Load()))], keywords=[]), generators=[comprehension(target=Tuple(elts=[Name(id=var2, ctx=Store()), Name(id=var1, ctx=Store())], ctx=Store()), iter=Call(func=Name(id='zip', ctx=Load()), args=[Bytes(s=pair1), Bytes(s=pair2)], keywords=[]), ifs=[], is_async=0)])], keywords=[])
    ]
    # Make it much more likely for it to be a bitwise xor. They are much more difficult to understand.
    table.extend([table[2]] * 2)
    if not len(s):
        return random.choice(table0)()

    if len(s) == 1:
        return random.choice(table1)(ord(s))

    return random.choice(table)(s)


class Obfuscator(ast.NodeTransformer):
    def __init__(self, passes=1):
        ast.NodeTransformer.__init__(self)

        # imported modules
        self.imports = {}

        # Import values from modules
        self.from_imports = {}

        # The names of the imported values
        self.import_aliases = {}

        # global values (can be renamed)
        self.globs = {}

        # local variables
        self.locs = []

        # Obfuscated operators
        self.binary_operators = {}

        self.unary_operators = {}

        # List of classes
        self.classes = []

        # inside a function
        self.indef = False

        # Inside a class
        self.inclass = False

        # Number of passes to perform
        self.passes = passes

        # Whether we've renamed variables yet.
        self.renamed = False

    def obfuscate_global(self, name):
        newname = random_string(20, 20)
        self.globs[name] = newname
        return newname

    def obfuscate_local(self, name):
        # Rename the variable in the closest-in local namespace
        newname = random_string(20, 20)
        self.locs[0][name] = newname
        return newname

    def get_name(self, name):
        found_local = False

        # Loop through and try to find a local var in the closest containing namespace
        for local_namespace in self.locs:
            if name in local_namespace:
                name = local_namespace[name]
                found_local = True
                break

        # Otherwise fall back to global variables
        if not found_local:
            name = self.globs.get(name, name)

        return name

    def visit_Import(self, node):
        # Add a plain import
        newname = self.obfuscate_global(node.names[0].name)
        self.imports[node.names[0].name] = newname

    def visit_ImportFrom(self, node):
        # Add the module and all the aliases we're importing from it to their respective places
        module_name = self.obfuscate_global(node.module)
        self.from_imports[module_name] = {}
        self.import_aliases[node.module] = module_name
        for alias in node.names:
            self.from_imports[module_name][alias.name] = self.obfuscate_global(alias.name)

    def visit_Str(self, node):
        return obfuscate_string(node.s)

    def visit_NameConstant(self, node):
        # Don't mess with None
        if node.value is None:
            return node

        # Replace with a x % y == 0
        divisor = random.randint(2, 16)
        multiplicand = random.randint(4, 8)

        value = divisor * multiplicand

        if not node.value:
            # Make it not divisible, and therefore False
            value += random.randint(1, divisor - 1)
        return Compare(left=BinOp(left=Num(n=value), op=Mod(), right=Num(n=divisor)), ops=[Eq()], comparators=[Num(n=0)])

    def visit_Num(self, node):
        obfus_type = random.randint(1, 3)

        if type(node.n) == float:
            # Obfuscate with integer ratio
            left, right = node.n.as_integer_ratio()
            return BinOp(left=Num(left), op=Div(), right=Num(right))

        if obfus_type == 1:
            # 7 to (2 * 3) + 1 or likewise with another divisor
            d = random.randint(2, 16)
            return BinOp(left=BinOp(left=Num(node.n // d), op=Mult(),
                                    right=Num(n=d)),
                         op=Add(), right=Num(node.n % d))
        elif obfus_type == 2 and node.n:
            # 8 to 2 ^ 10
            random_num = random.getrandbits(node.n.bit_length())
            return BinOp(left=Num(node.n ^ random_num), op=BitXor(), right=Num(random_num))

        else:
            return node

    def visit_ClassDef(self, node):
        self.classes.append(node.name)

        # Don't obfuscate our class names or args.
        self.inclass = True
        node.body = [self.visit(x) for x in node.body if x]
        self.inclass = False

        return node

    def visit_Attribute(self, node):
        # Replace with a call to getattr()
        if isinstance(node.value, Name) and isinstance(node.value.ctx, Load):
            node.value = self.visit(node.value)
            return Call(func=Name(id='getattr', ctx=Load()), args=[
                Name(id=node.value.id, ctx=Load()), Str(s=node.attr)],
                keywords=[], starargs=None, kwargs=None)
        # Visit the value
        node.value = self.visit(node.value)
        return node

    def visit_BinOp(self, node):
        """
        Use a few equivalent arithmetic tricks to obfuscate certain operators, including +, -, |, &, ^, and ~
        """
        expandable = True
        is_int = True

        for candidate_node in ast.walk(node):
            if isinstance(candidate_node, Call):
                expandable = False

        if type(node.left) != Num or type(node.right) != Num or type(node.left.n) != int or type(node.right.n) != int:
            is_int = False

        left_visited = self.visit(copy.deepcopy(node.left))

        right_visited = self.visit(copy.deepcopy(node.right))

        if type(node.op) == Add and random.randint(1, 10) == 1 and expandable and is_int:
            # Obfuscate using Mixed Binary Arithmetic
            # Only if we can guarantee it's an int
            # x + y -> (x & y) + (x | y)
            # x + y -> (x ^ y) + 2 * (x & y)
            return random.choice([
                                  BinOp(left=BinOp(left=left_visited, op=BitXor(), right=right_visited), op=Add(), right=BinOp(left=Num(n=2), op=Mult(), right=BinOp(left=left_visited, op=BitAnd(), right=right_visited))),

                                  BinOp(left=BinOp(left=left_visited, op=BitAnd(), right=right_visited), op=Add(), right=BinOp(left=left_visited, op=BitOr(), right=right_visited))
            ])

        elif type(node.op) == Sub and random.randint(1, 10) == 1 and expandable and is_int:
            # Sub replacements
            # Same as addition, just with negative right hand side
            # x - y -> (x & ~y + 1) + (x | ~y + 1)
            # x - y -> (x ^ ~y + 1) + 2 * (x & ~y + 1)
            return random.choice([
                                  BinOp(left=BinOp(left=Num(n=2), op=Mult(), right=BinOp(left=left_visited, op=BitOr(), right=BinOp(left=UnaryOp(op=Invert(), operand=right_visited), op=Add(), right=Num(n=1)))), op=Sub(), right=BinOp(left=left_visited, op=BitXor(), right=BinOp(left=UnaryOp(op=Invert(), operand=right_visited), op=Add(), right=Num(n=1)))),

                                  BinOp(left=BinOp(left=left_visited, op=BitOr(), right=BinOp(left=UnaryOp(op=Invert(), operand=right_visited), op=Add(), right=Num(n=1))), op=Add(), right=BinOp(left=left_visited, op=BitAnd(), right=BinOp(left=UnaryOp(op=Invert(), operand=right_visited), op=Add(), right=Num(n=1))))
            ])

        elif type(node.op) == BitOr and random.randint(1, 10) == 1 and expandable:
            # BitOr replacements:
            # x | y -> (x ^ y) | (x & y)
            # Or using NAND logic:
            # x | y -> ~(~(x & x) & ~(y & y))
            return random.choice([
                                  BinOp(left=BinOp(left=left_visited, op=BitXor(), right=right_visited), op=BitOr(), right=BinOp(left=left_visited, op=BitAnd(), right=right_visited)),

                                  UnaryOp(op=Invert(), operand=BinOp(left=UnaryOp(op=Invert(), operand=BinOp(left=left_visited, op=BitAnd(), right=right_visited)), op=BitAnd(), right=UnaryOp(op=Invert(), operand=BinOp(left=right_visited, op=BitAnd(), right=right_visited))))
            ])

        elif type(node.op) == BitAnd and random.randint(1, 10) == 1 and expandable:
            # BitAnd replacements:
            # x & y -> (x | y) - (x ^ y)
            # Or using NAND logic:
            # x & y -> ~(~(x & y) & ~(x & y))
            return random.choice([
                                  BinOp(left=BinOp(left=left_visited, op=BitOr(), right=right_visited), op=Sub(), right=BinOp(left=left_visited, op=BitXor(), right=right_visited)),

                                  UnaryOp(op=Invert(), operand=BinOp(left=UnaryOp(op=Invert(), operand=BinOp(left=left_visited, op=BitAnd(), right=right_visited)), op=And(), right=UnaryOp(op=Invert(), operand=BinOp(left=left_visited, op=BitAnd(), right=right_visited))))
            ])

        elif type(node.op) == BitXor and random.randint(1, 10) == 1 and expandable:
            # BitXor replacements:
            # x ^ y -> x - y + 2 * (~x & y)
            # x ^ y -> ~(x & y) & ~(~x & ~y)
            # x ^ y -> (~x & y) | (x & ~y)
            return random.choice([
                                  BinOp(left=BinOp(left=left_visited, op=Sub(), right=right_visited), op=Add(), right=BinOp(left=Num(n=2), op=Mult(), right=BinOp(left=UnaryOp(op=Invert(), operand=left_visited), op=BitAnd(), right=right_visited))),

                                  BinOp(left=UnaryOp(op=Invert(), operand=BinOp(left=left_visited, op=BitAnd(), right=right_visited)), op=BitAnd(), right=UnaryOp(op=Invert(), operand=BinOp(left=UnaryOp(op=Invert(), operand=left_visited), op=BitAnd(), right=UnaryOp(op=Invert(), operand=right_visited)))),

                                  BinOp(left=BinOp(left=UnaryOp(op=Invert(), operand=left_visited), op=BitAnd(), right=right_visited), op=BitOr(), right=BinOp(left=left_visited, op=BitAnd(), right=UnaryOp(op=Invert(), operand=right_visited)))
            ])

        # Make a lambda expression for the operator, and have a 1/4 chance of using it
        # This lambda definition will be stuck right at the top of the file in the visit_Module() function
        try:
            if type(node.op) not in self.binary_operators:
                newname = random_string(20, 20)
                self.binary_operators[type(node.op)] = newname
            if random.randint(1, 4) == 1:
                name = self.binary_operators[type(node.op)]
                return Call(func=Name(self.globs.get(name, name), ctx=Load()), args=[left_visited, right_visited], keywords=[])
            else:
                node.left = left_visited
                node.right = right_visited
                return node
        except:
            node.left = left_visited
            node.right = right_visited
            return node

    def visit_UnaryOp(self, node):
        node.operand = self.visit(node.operand)

        # Basically the same as BinOp
        try:
            if type(node.op) not in self.unary_operators:
                newname = random_string(20, 20)
                self.unary_operators[type(node.op)] = newname
            if random.randint(1, 2) == 1:
                name = self.unary_operators[type(node.op)]
                return Call(func=Name(self.get_name(name), ctx=Load()), args=[node.operand], keywords=[])
            else:
                return node
        except:
            return node

    def visit_AugAssign(self, node):

        if type(node.target) == Name:
            # Just replace the name with a non-augmented assignment
            # x += 3
            # x = x + 3
            return self.visit(Assign(targets=[Name(node.target.id, ctx=Store())],
                              value=BinOp(left=Name(node.target.id, ctx=Load()), op=node.op, right=node.value)))
        elif type(node.target) == Attribute and type(node.target.value) == Name:
            # Replace a attribute with a non-augmented assignment
            # name.attr /= 3
            # name.attr = name.attr / 3
            attribute = node.target

            # Grab versions of our attribute with both store and reload contexts.
            storeattribute = copy.deepcopy(attribute)

            loadattribute = copy.deepcopy(attribute)

            storeattribute.ctx = Store()

            loadattribute.ctx = Load()

            storeattribute.value.ctx = Load()

            loadattribute.value.ctx = Load()

            return self.visit(Assign(targets=[storeattribute],
                                     value=BinOp(left=loadattribute, op=node.op, right=node.value)))
        else:
            # I don't wont to go through all the possible cases, leave as-is
            node.value = self.visit(node.value)

            return node

    def visit_Assign(self, node):
        node.value = self.visit(node.value)

        # Visit the targets if they're not attributes
        # Visiting an attribute will result in trying to assign to a function call
        node.targets = [self.visit(x) if type(x) != Attribute else x for x in node.targets]

        return node

    def visit_FunctionDef(self, node):
        # Test to see if there's a keyword-only argument specifying that we shouldn't
        # Obfuscate the name and arguments
        no_obfuscate = 'ast_no_obfuscate' in [arg.arg for arg in node.args.kwonlyargs]

        # If we're already in a function definition make sure we don't close out of it
        if self.indef == True:
            already_indef = True
        else:
            already_indef = False
        self.indef = True

        # Add a new local namespace for this function
        self.locs.insert(0, {})

        # If we haven't already renamed stuff, do that
        if not self.renamed:
            # In a class or not, if the no_obfuscate flag is there, remove it and simply keep the name and args as-is
            if no_obfuscate:
                self.globs[node.name] = node.name
                # Purge the undesirable flag for no obfuscation
                node.args.kwonlyargs = list(filter(lambda arg: arg.arg != 'ast_no_obfuscate', node.args.kwonlyargs))

            # If we're not in a class and allowed to obfuscate, do both name and args
            elif not self.inclass:
                    node.name = self.obfuscate_global(node.name)
                    for arg in node.args.args:
                        arg.arg = self.obfuscate_local(arg.arg)

            # If we're in a class, only rename args
            elif self.inclass:
                for arg in node.args.args:
                    arg.arg = self.obfuscate_local(arg.arg)

        # Visit the function body, possibly recursing into another definition
        node.body = [self.visit(x) for x in node.body]

        # Handle nested function defs
        if not already_indef:
            self.indef = False

        # Remove our function namespace
        self.locs.pop(0)
        return node

    def visit_Lambda(self, node):
        # Test to see if there's a keyword-only argument specifying that we shouldn't
        # Obfuscate the name and arguments
        no_obfuscate = 'ast_no_obfuscate' in [arg.arg for arg in node.args.kwonlyargs]

        # If we're already in a function definition make sure we don't close out of it
        if self.indef == True:
            already_indef = True
        else:
            already_indef = False
        self.indef = True

        # Add a new local namespace for this function
        self.locs.insert(0, {})

        # If we haven't already renamed stuff, do that
        if not self.renamed:
            for arg in node.args.args:
                arg.arg = self.obfuscate_local(arg.arg)

        # Visit the function body, possibly recursing into another definition
        node.body = self.visit(node.body)

        # Handle nested function defs
        if not already_indef:
            self.indef = False

        # Remove our function namespace
        self.locs.pop(0)
        return node

    def visit_Name(self, node):
        # obfuscate known globals and locals
        if not self.renamed and not self.inclass and isinstance(node.ctx, Store):
            if not self.indef and node.id not in self.globs:
                node.id = self.obfuscate_global(node.id)
            if self.indef and node.id not in self.locs[0]:
                node.id = self.obfuscate_local(node.id)

        node.id = self.get_name(node.id)

        return node

    def visit_Module(self, node):

        # Run our obfuscation layers times
        for i in range(self.passes):
            node.body = [y for y in (self.visit(x) for x in node.body) if y]
            self.renamed = True

        # Add imports
        for name, newname in self.imports.items():
            node.body.insert(0, import_node(name, newname))

        # Add imports with specific names import
        # E.G:
        # from math import log, sqrt
        for name, newname in self.import_aliases.items():
            for alias in self.from_imports[newname].keys():
                node.body.insert(0, Assign(targets=[Name(id=self.from_imports[newname][alias], ctx=Store())],
                                           value=Attribute(
                                               value=Name(id=newname, ctx=Load()),
                                               attr=alias
                                           )))
            node.body.insert(0, import_node(name, newname, self.from_imports[newname].keys()))

        node.body = [self.visit(x) for x in node.body]

        # Add lambdas for each obfuscated operator
        for operator, newname in self.binary_operators.items():
            node.body.insert(0, obfuscate_binary(operator, newname))

        for operator, newname in self.unary_operators.items():
            arg1 = random_string(20, 20)
            node.body.insert(0, Assign(targets=[Name(id=newname, ctx=Store())],
                                       value=Lambda(args=arguments(args=[arg(arg=arg1, annotation=None)], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                                                    body=UnaryOp(operand=Name(arg1, ctx=Load()), op=operator()))))

        return node


class GlobalsEnforcer(ast.NodeTransformer):
    def __init__(self, globs):
        ast.NodeTransformer.__init__(self)
        self.globs = {}

    def visit_Name(self, node):
        node.id = self.globs.get(node.id, node.id)
        return node


if __name__ == '__main__':
    if len(sys.argv) < 3:
        exit(0)

    if len(sys.argv) == 4:
        passes = int(sys.argv[3])
    else:
        passes = 1

    if sys.argv[1] == '-':
        root = ast.parse(sys.stdin.read())
    else:
        root = ast.parse(open(sys.argv[1], 'rb').read())

    if sys.argv[2] == '-':
        file_obj = sys.stdin
    else:
        file_obj = open(sys.argv[2], 'w')

    # obfuscate the AST
    obf = Obfuscator(passes=passes)
    root = obf.visit(root)

    # resolve all global names
    root = GlobalsEnforcer(obf.globs).visit(root)

    file_obj.write(astor.code_gen.to_source(root, indent_with=' '))

    file_obj.close()