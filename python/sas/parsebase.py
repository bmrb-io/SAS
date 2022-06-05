#!/usr/bin/python3 -u
#
#
from __future__ import absolute_import

import sys
import os
import abc
#import pprint

_UP = os.path.join( os.path.split( __file__ )[0], ".." )
sys.path.append( os.path.realpath( _UP ) )
import sas

# base interface for SAS parsers
#
class ParserBase( object, metaclass = abc.ABCMeta ) :

    """
    Parser for STAR file.
    """

    #
    #
    def __init__( self, lex, ch, eh, verbose = False ) :
        """
        constructor

        ``lex``: ``sas.StarLexer``
        ``ch`` : ``sas.ContentHandlerBase``
        ``eh`` : ``sas.ErrorHandler``
        ``verbose`` flag is optional
        """

        assert isinstance( lex, sas.StarLexer )
        assert isinstance( ch, sas.ContentHandlerBase )
        assert isinstance( eh, sas.ErrorHandler )
        self._lexer = lex
        self._ch = ch
        self._eh = eh
        self._verbose = bool( verbose )
        self._data_name = "__FILE__"
        self._save_name = "__UNNAMED__"

    #
    #
    @property
    def verbose( self ) :
        """verbose flag"""
        return bool( self._verbose )
    @verbose.setter
    def verbose( self, flag ) :
        self._verbose = bool( flag )

    # main
    #
    @classmethod
    def parse( cls, lexer, content_handler, error_handler, verbose = False ) :
        """
        Main method

        parameters are the same as for the contructor

        returns parser instance
        """
        parser = cls( lex = lexer, ch = content_handler, eh = error_handler, verbose = verbose )
        assert isinstance( parser, ParserBase )
        parser._parse_file()
        return parser

    @abc.abstractmethod
    def _parse_file() :
        raise Exception( "Abstract method called" )

###################################################################################################
# just to make sure it fails
#
class Ch( sas.ContentHandler2 ) :
    def __init__( self, verbose = False ) :
        self._verbose = bool( verbose )
    def startData( self, line, name ) :
        return False
    def endData( self, line, name ) :
        pass
    def startSaveframe( self, line, name ) :
        return False
    def endSaveframe( self, line, name ) :
        return False
    def startLoop( self, line ) :
        return False
    def endLoop( self, line ) :
        return False
    def comment( self, line, text ) :
        return False
    def tag( self, line, tag ) :
        return False
    def value( self, line, val, delim ) :
        return False

#
#
if __name__ == "__main__" :

    e = sas.ErrorHandler()
    c = Ch()
    l = sas.StarLexer( fp = sys.stdin, bufsize = 0, verbose = False )
    p = ParserBase.parse( lexer = l, content_handler = c, error_handler = e, verbose = False )
