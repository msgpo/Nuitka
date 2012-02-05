#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Optimizations of builtins to builtin calls.

"""
from .OptimizeBase import makeRaiseExceptionReplacementExpressionFromInstance

from nuitka.nodes import Nodes

from nuitka.nodes.BuiltinRangeNode import CPythonExpressionBuiltinRange

from nuitka.nodes.ParameterSpec import ParameterSpec, TooManyArguments

from nuitka.Utils import getPythonVersion

import sys

class BuiltinParameterSpec( ParameterSpec ):
    def __init__( self, name, arg_names, default_count, list_star_arg = None, dict_star_arg = None ):
        self.name = name
        self.builtin = __builtins__[ name ]

        ParameterSpec.__init__(
            self,
            normal_args    = arg_names,
            list_star_arg  = list_star_arg,
            dict_star_arg  = dict_star_arg,
            default_count  = default_count
        )

    def __repr__( self ):
        return "<BuiltinParameterSpec %s>" % self.name

    def getName( self ):
        return self.name

    def simulateCall( self, given_values ):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=W0142,W0703

        try:
            given_normal_args = given_values[ : len( self.normal_args ) ]

            if self.list_star_arg:
                given_list_star_args = given_values[ len( self.normal_args ) ]
            else:
                given_list_star_args = None

            if self.dict_star_arg:
                given_dict_star_args = given_values[ -1 ]
            else:
                given_dict_star_args = None

            arg_dict = {}

            for arg_name, given_value in zip( self.normal_args, given_normal_args ):
                assert type( given_value ) not in ( tuple, list ), ( "do not like a tuple %s" % ( given_value, ))

                if given_value is not None:
                    arg_dict[ arg_name ] = given_value.getConstant()

            if given_dict_star_args:
                for given_dict_star_arg in given_dict_star_args:
                    arg_name = given_dict_star_arg.getKey()
                    arg_value = given_dict_star_arg.getValue()

                    arg_dict[ arg_name.getConstant() ] = arg_value.getConstant()

        except Exception as e:
            sys.exit( "Fatal problem: %r" % e )

        if given_list_star_args:
            return self.builtin( *( value.getConstant() for value in given_list_star_args ), **arg_dict )
        else:
            return self.builtin( **arg_dict )

class BuiltinParameterSpecNoKeywords( BuiltinParameterSpec ):

    def allowsKeywords( self ):
        return False

    def simulateCall( self, given_values ):
        # Using star dict call for simulation and catch any exception as really fatal,
        # pylint: disable=W0142,W0703

        try:
            if self.list_star_arg:
                given_list_star_arg = given_values[ len( self.normal_args ) ]
            else:
                given_list_star_arg = None

            arg_list = []
            refuse_more = False

            for _arg_name, given_value in zip( self.normal_args, given_values ):
                assert type( given_value ) not in ( tuple, list ), ( "do not like tuple %s" % ( given_value, ))

                if given_value is not None:
                    if not refuse_more:
                        arg_list.append( given_value.getConstant() )
                    else:
                        assert False
                else:
                    refuse_more = True

            if given_list_star_arg is not None:
                arg_list += [ value.getConstant() for value in given_list_star_arg ]
        except Exception as e:
            sys.exit( e )

        return self.builtin( *arg_list )


class BuiltinParameterSpecExceptions( BuiltinParameterSpec ):
    def allowsKeywords( self ):
        return False

    def getKeywordRefusalText( self ):
        return "exceptions.%s does not take keyword arguments" % self.name

    def __init__( self, name, default_count ):
        BuiltinParameterSpec.__init__(
            self,
            name          = name,
            arg_names     = (),
            default_count = default_count,
            list_star_arg = "args"
        )

    def getCallableName( self ):
        return "exceptions." + self.getName()

builtin_int_spec = BuiltinParameterSpec( "int", ( "x", "base" ), 2 )
# This builtin is only available for Python2
if getPythonVersion() < 300:
    builtin_long_spec = BuiltinParameterSpec( "long", ( "x", "base" ), 2 )

builtin_bool_spec = BuiltinParameterSpec( "bool", ( "x", ), 1 )
builtin_float_spec = BuiltinParameterSpec( "float", ( "x", ), 1 )
builtin_str_spec = BuiltinParameterSpec( "str", ( "object", ), 1 )
builtin_len_spec = BuiltinParameterSpecNoKeywords( "len", ( "object", ), 0 )
builtin_dict_spec = BuiltinParameterSpec( "dict", (), 2, "list_args", "dict_args" )
builtin_len_spec = BuiltinParameterSpecNoKeywords( "len", ( "object", ), 0 )
builtin_tuple_spec = BuiltinParameterSpec( "tuple", ( "sequence", ), 1 )
builtin_list_spec = BuiltinParameterSpec( "list", ( "sequence", ), 1 )
builtin_import_spec = BuiltinParameterSpec( "__import__", ( "name", "globals", "locals", "fromlist", "level" ), 1 )
builtin_chr_spec = BuiltinParameterSpecNoKeywords( "chr", ( "i", ), 1 )
builtin_ord_spec = BuiltinParameterSpecNoKeywords( "ord", ( "c", ), 1 )
builtin_bin_spec = BuiltinParameterSpecNoKeywords( "bin", ( "number", ), 1 )
builtin_oct_spec = BuiltinParameterSpecNoKeywords( "oct", ( "number", ), 1 )
builtin_hex_spec = BuiltinParameterSpecNoKeywords( "hex", ( "number", ), 1 )
builtin_range_spec = BuiltinParameterSpecNoKeywords( "range", ( "start", "stop", "step" ), 2 )
builtin_repr_spec = BuiltinParameterSpecNoKeywords( "repr", ( "object", ), 1 )
builtin_execfile_spec = BuiltinParameterSpecNoKeywords( "repr", ( "filename", "globals", "locals" ), 1 )

# TODO: This should be separate
builtin_table = {
    "range" : ( CPythonExpressionBuiltinRange, builtin_range_spec )
}

def extractBuiltinArgs( node, builtin_spec, builtin_class ):
    # TODO: These could be handled too.
    if node.getStarListArg() is not None or node.getStarDictArg() is not None:
        return None

    try:
        args = builtin_spec.matchCallSpec(
            name      = builtin_spec.getName(),
            call_spec = node
        )

        # Using list reference for passing the arguments without names, pylint: disable=W0142
        return builtin_class(
            *args,
            source_ref = node.getSourceReference()
        )
    except TooManyArguments as e:
        return Nodes.CPythonExpressionFunctionCall(
            called_expression = makeRaiseExceptionReplacementExpressionFromInstance(
                expression     = node,
                exception      = e.getRealException()
            ),
            positional_args   = node.getPositionalArguments(),
            list_star_arg     = node.getStarListArg(),
            dict_star_arg     = node.getStarDictArg(),
            pairs             = node.getNamedArgumentPairs(),
            source_ref        = node.getSourceReference()
        )

def makeBuiltinCallNode( node ):
    builtin_name = node.getCalled().getBuiltinName()

    if builtin_name not in builtin_table:
        return None

    builtin_maker, builtin_spec = builtin_table[ builtin_name ]

    return extractBuiltinArgs(
        builtin_spec  = builtin_spec,
        builtin_class = builtin_maker,
        node          = node
    )