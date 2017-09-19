#!/usr/bin/python -u

from __future__ import absolute_import

import sys
import os
#import pprint

_UP = os.path.join( os.path.split( __file__ )[0], "../.." )
sys.path.append( os.path.realpath( _UP ) )
import sas

# this parser returns data name(s) (tags)  and data value(s) in separate callbacks
#
class Parser( object ) :

    """
    Parser for ``ContentHandler2`` interface, see ``handlers.py`` for details.
    """

    #
    #
    def __init__( self, lex, ch, eh, verbose = False ) :
        """
        constructor

        ``lex``: ``sas.StarLexer``
        ``ch`` : ``sas.ContentHandler2``
        ``eh`` : ``sas.ErrorHandler``
        ``verbose`` flag is optional
        """

        assert isinstance( lex, sas.StarLexer )
        assert isinstance( ch, sas.ContentHandler2 )
        assert isinstance( eh, sas.ErrorHandler )
        self._lexer = lex
        self._ch = ch
        self._eh = eh
        self._verbose = bool( verbose )
        self._data_name = "__FILE__"

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

        other parameters are the same as for the contructor

        returns ``Parser`` instance
        """
        parser = cls( lex = lexer, ch = content_handler, eh = error_handler, verbose = verbose )
        assert isinstance( parser, Parser )
        parser._parse_file()
        return parser

    # top-level parse does not return anything
    #
    def _parse_file( self ) :
        """Top (file) level parse"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler2 )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_file()\n" )

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return
                    continue

                if token.type == "DATASTART" :
                    if self._ch.startData( line = token.lineno, name = token.value ) :
                        return
                    self._data_name = token.value
                    if self._parse_data() :
                        return
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token at file level: %s : %s" \
                        % (token.type, token.value,) ) :
                    return

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                self._ch.endData( line = ln, name = self._data_name )
                return

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return

    # returns a stop sign: if true: stop parsing
    #
    def _parse_data( self ) :
        """Parse data block"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler2 )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_data()\n" )

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return True
                    continue

                if token.type == "SAVESTART" :
                    if self._ch.startSaveframe( line = token.lineno, name = token.value ) :
                        return True
                    if self._parse_save( name = token.value ) :
                        return True
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in data block: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                self._ch.endData( line = ln, name = self._data_name )
                return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

    # read a delimited value
    # returns a pair: val, stop where stop is the sopt parsing sign
    #
    def _read_value( self, delimiter ) :
        assert isinstance( self._lexer, sas.StarLexer )
        assert delimiter in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART")

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._read_value(%s)\n" % (delimiter,) )

        stop = False
        val = ""
        try :
            for token in self._lexer :

                if delimiter in ("SINGLESTART","DOUBLESTART") :
                    if token.type == "NL" :
                        if self._eh.error( line = token.lineno, msg = "newline in quoted value: %s" % (val,) ) :
                            stop = True
                            break
                        val += "\n"
                        continue

                if delimiter == "SINGLESTART" :
                    if token.type == "SINGLEEND" :
                        break

                if delimiter == "DOUBLESTART" :
                    if token.type == "DOUBLEEND" :
                        break

                if delimiter == "TSINGLESTART" :
                    if token.type == "TSINGLEEND" :
                        break

                if delimiter == "TDOUBLESTART" :
                    if token.type == "TDOUBLEEND" :
                        break

# assume that trailing \n is a part of the "\n;" delimiter and strip it off
#
                if delimiter == "SEMISTART" :
                    if token.type == "SEMIEND" :
                        if val.endswith( "\n" ) : val = val.rstrip( "\n" )
                        break

                if not delimiter in ("SINGLESTART","DOUBLESTART") :
                    for pat in sas.KEYWORDS :
                        m = pat.search( token.value.strip() )
                        if m :
                            if self._eh.warning( line = token.lineno, msg = "keyword in value: %s" \
                                    % (m.group( 1 ),) ) :
                                stop = True
                            break

                val += token.value

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                self._eh.fatalError( line = ln, msg = "EOF in delimited value" )
                stop = True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            stop = True

        return (val, stop)

    # returns a stop sign: if true: stop parsing
    #
    def _parse_save( self, name ) :
        """Parse saveframe"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler2 )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_save(%s)\n" % (name,) )

        need_value = False

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return True
                    continue

# exit point
#
                if token.type == "SAVEEND" :
                    if need_value :
                        if self._eh.error( line = token.lineno, msg = "found save_, expected value" ) :
                            return True
                    if self._ch.endSaveframe( line = token.lineno, name = name ) :
                        return True
                    return False

                if token.type == "LOOPSTART" :
                    if need_value :
                        if self._eh.error( line = token.lineno, msg = "found loop_, expected value" ) :
                            return True
                    if self._ch.startLoop( line = token.lineno ) :
                        return True
                    if self._parse_loop() :
                        return True
                    continue

                if token.type == "TAGNAME" :
                    if need_value :
                        if self._eh.error( line = token.lineno, msg = "found tag: %s, expected value" \
                                % (token.value,) ) :
                            return True
                        if self._ch.tag( line = token.lineno, tag = token.value ) :
                            return True
                    need_value = True
                    continue

                if token.type in ("CHARACTERS","FRAMECODE") :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here: %s" \
                                % (token.value,) ) :
                            return True
                    if self._ch.value( line = token.lineno, val = token.value, delim = sas.TOKENS[token.type] ) :
                        return True
                    need_value = False
                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here (found delimiter)" ) :
                            return True
                    (val, stop) = self._read_value( token.type )
                    if stop :
                        return True
                    if self._ch.value( line = token.lineno, val = val, delim = sas.TOKENS[token.type] ) :
                        return True
                    need_value = False
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in saveframe: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                if need_value :
                    self._eh.fatalError( line = ln, msg = "EOF in saveframe: %s (expected value)" \
                        % (name,) )
                    return True
                self._eh.fatalError( line = ln, msg = "EOF in saveframe: %s (no closing save_)" % (name,) )
                return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

    # returns a stop sign: if true: stop parsing
    #
    def _parse_loop( self ) :
        """Parse loop"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler2 )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_loop()\n" )

        need_tag = True
        numtags = 0
        numvals = 0

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return True
                    continue

# exit point
#
                if token.type == "STOP" :
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True
                    if numvals < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no values" ) :
                            return True
                    if (numvals % numtags) != 0 :
                        if self._eh.error( line = token.lineno, msg = "Loop count error" ) :
                            return True

                    if self._ch.endLoop( line = token.lineno ) :
                        return True
                    return False

                if token.type == "TAGNAME" :
                    if not need_tag :
                        if self._eh.error( line = token.lineno, msg = "tag not expected here: %s" \
                                % (token.value,) ) :
                            return True
                    numtags += 1
                    if self._ch.tag( line = token.lineno, tag = token.value ) :
                        return True
                    continue

                if token.type in ("CHARACTERS","FRAMECODE") :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True
                    numvals += 1
                    if self._ch.value( line = token.lineno, val = token.value, delim = sas.TOKENS[token.type] ) :
                        return True
                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True
                    numvals += 1
                    (val, stop) = self._read_value( token.type )
                    if stop : return True

                    if self._ch.value( line = token.lineno, val = val, delim = sas.TOKENS[token.type] ) :
                        return True
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in loop: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                if numtags < 1 :
                    self._eh.fatalRrror( line = ln, msg = "EOF in loop (no tags)" )
                    return True
                if numvals < 1 :
                    self._eh.fatalError( line = ln, msg = "EOF in loop (no values)" )
                    return True

                if (numvals % numtags ) != 0 :
                    self._eh.error( line = ln, msg = "Loop count error" )

                self._eh.fatalError( line = ln, msg = "EOF in loop (no closing stop_)" )
                return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

###################################################################################################
# test handler
#
class Ch( sas.ContentHandler2 ) :
    def __init__( self, verbose = False ) :
        self._verbose = bool( verbose )
    def startData( self, line, name ) :
        if self._verbose : sys.stdout.write( "Start data block %s in line %d\n" % (name, line,) )
        return False
    def endData( self, line, name ) :
        if self._verbose : sys.stdout.write( "End data block %s in line %d\n" % (name, line,) )
    def startSaveframe( self, line, name ) :
        if self._verbose : sys.stdout.write( "Start saveframe %s in line %d\n" % (name, line,) )
        return False
    def endSaveframe( self, line, name ) :
        if self._verbose : sys.stdout.write( "End saveframe %s in line %d\n" % (name, line,) )
        return False
    def startLoop( self, line ) :
        if self._verbose : sys.stdout.write( "Start loop in line %d\n" % (line,) )
        return False
    def endLoop( self, line ) :
        if self._verbose : sys.stdout.write( "End loop in line %d\n" % (line,) )
    def comment( self, line, text ) :
        if self._verbose : sys.stdout.write( "Comment %s in line %d\n" % (text, line,) )
        return False
    def tag( self, line, tag ) :
        if self._verbose :
            sys.stdout.write( "tag %s in line %d\n" % (tag, line,) )
    def value( self, line, val, delim ) :
        if self._verbose :
            sys.stdout.write( "value in line " + str( line ) )
            if delim is not None : sys.stdout.write( "delimited with " + str( delim ) )
            sys.stdout.write( " >>> " )
            sys.stdout.write( val )
            sys.stdout.write( " <<<\n" )

#
#
if __name__ == "__main__" :

    e = sas.ErrorHandler()
    c = Ch( verbose = False )
    l = sas.StarLexer( fp = sys.stdin, bufsize = 0, verbose = False )
    with sas.timer( "SANS2" ) :
        p = Parser.parse( lexer = l, content_handler = c, error_handler = e, verbose = False )

