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
class SasParser( sas.ParserBase ) :

    """
    Parser for ``SasContentHandler`` interface, see ``handlers.py`` for details.
    """

    # top-level parse does not return anything
    #
    def _parse_file( self ) :
        """Top (file) level parse"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.SasContentHandler )
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

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return

    # returns a stop sign: if true: stop parsing
    #
    def _parse_data( self ) :
        """Parse data block"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.SasContentHandler )
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

            return False

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

    # returns a stop sign: if true: stop parsing
    #
    def _parse_save( self, name ) :
        """Parse saveframe"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.SasContentHandler )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_save(%s)\n" % (name,) )

        need_value = False
        last_delimiter = None

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

# fake start & end of value
#
                if token.type == "CHARACTERS" :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here: %s" \
                                % (token.value,) ) :
                            return True

                    if last_delimiter is None :
                        if self._ch.startValue( line = token.lineno, delim = None ) :
                            return True

# check for keywords inside quoted multi-line values
#
                    if last_delimiter in ( ";", "'''", '"""' ) :
                        for pat in sas.KEYWORDS :
                            m = pat.search( token.value.strip() )
                            if m :
                                if self._eh.warning( line = token.lineno, msg = "keyword in value: %s" \
                                        % (m.group( 1 ),) ) :
                                    return True

                    if self._ch.characters( line = token.lineno, val = token.value ) :
                        return True

                    if last_delimiter is None :
                        if self._ch.endValue( line = token.lineno, delim = None ) :
                            return True
                        need_value = False

                    continue

                if token.type == "FRAMECODE" :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "framecode not expected here: %s" \
                                % (token.value,) ) :
                            return True

                    if self._ch.startValue( line = token.lineno, delim = sas.TOKENS[token.type] ) :
                        return True

                    if self._ch.characters( line = token.lineno, val = token.value ) :
                        return True

                    if self._ch.endValue( line = token.lineno, delim = sas.TOKENS[token.type] ) :
                        return True
                    need_value = False

                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here (found delimiter %s)" \
                                % (sas.TOKENS[token.type],) ) :
                            return True
                    if last_delimiter is not None :
                        if self._eh.error( line = token.lineno, msg = "found opening %s inside quoted value" \
                                % (sas.TOKENS[token.type],) ) :
                            return True

                    last_delimiter = sas.TOKENS[token.type]
                    if self._ch.startValue( line = token.lineno, delim = last_delimiter ) :
                        return True

                    continue

                if token.type in ("SINGLEEND","TSINGLEEND","DOUBLEEND","TDOUBLEEND","SEMIEND") :
                    if last_delimiter is None :
                        if self._eh.error( line = token.lineno, msg = "closing %s not expected here (not reading value)" \
                                % (sas.TOKENS[token.type],) ) :
                            return True
                    if last_delimiter != sas.TOKENS[token.type] :
                        if self._eh.error( line = token.lineno, msg = "closing %s not expected here (need %s)" \
                                % (sas.TOKENS[token.type],last_delimiter,) ) :
                            return True
                    if self._ch.endValue( line = token.lineno, delim = last_delimiter ) :
                        return True
                    last_delimiter = None
                    need_value = False

                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in saveframe: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                if last_delimiter is not None :
                    self._eh.fatalError( line = ln, msg = "EOF in value: no closing `%s`" \
                            % (last_delimiter,) )
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
        assert isinstance( self._ch, sas.SasContentHandler )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_loop()\n" )

        need_tag = True
        numtags = 0
        numvals = 0
        last_delimiter = None

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

# fake start & end of value
#
                if token.type == "CHARACTERS" :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True

                    if last_delimiter is None :
                        if self._ch.startValue( line = token.lineno, delim = None ) :
                            return True

                    if self._ch.characters( line = token.lineno, val = token.value ) :
                        return True

                    if last_delimiter is None :
                        if self._ch.endValue( line = token.lineno, delim = None ) :
                            return True
                        numvals += 1

                    continue

                if token.type == "FRAMECODE" :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True

                    if self._ch.startValue( line = token.lineno, delim = sas.TOKENS[token.type] ) :
                        return True

                    if self._ch.characters( line = token.lineno, val = token.value ) :
                        return True

                    if self._ch.endValue( line = token.lineno, delim = sas.TOKENS[token.type] ) :
                        return True

                    numvals += 1

                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True

                    if last_delimiter is not None :
                        if self._eh.error( line = token.lineno, msg = "found opening %s inside quoted value" \
                                % (sas.TOKENS[token.type],) ) :
                            return True

                    last_delimiter = sas.TOKENS[token.type]
                    if self._ch.startValue( line = token.lineno, delim = last_delimiter ) :
                        return True

                    continue

                if token.type in ("SINGLEEND","TSINGLEEND","DOUBLEEND","TDOUBLEEND","SEMIEND") :
                    if need_tag :
                        need_tag = False
                    if numtags < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True

                    if last_delimiter is None :
                        if self._eh.error( line = token.lineno, msg = "closing %s not expected here (not reading value)" \
                                % (sas.TOKENS[token.type],) ) :
                            return True
                    if last_delimiter != sas.TOKENS[token.type] :
                        if self._eh.error( line = token.lineno, msg = "closing %s not expected here (need %s)" \
                                % (sas.TOKENS[token.type],last_delimiter,) ) :
                            return True
                    if self._ch.endValue( line = token.lineno, delim = last_delimiter ) :
                        return True
                    last_delimiter = None
                    numvals += 1

                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in loop: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                ln = -1
                if "token" in locals() :
                    ln = token.lineno
                if last_delimiter is not None :
                    self._eh.fatalError( line = ln, msg = "EOF in value: no closing `%s`" \
                            % (last_delimiter,) )
                    return True

                self._eh.fatalError( line = ln, msg = "EOF in loop (no closing stop_)" )
                return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

###################################################################################################
# test handler
#
class Ch( sas.SasContentHandler ) :
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
    def startValue( self, line, delim ) :
        if self._verbose :
            sys.stdout.write( "start value in line %d" % (line,) )
            if delim is None : sys.stdout.write( "\n" )
            else : sys.stdout.write( " delimited with %s\n" % (delim,) )
        return False
    def endValue( self, line, delim ) :
        if self._verbose :
            sys.stdout.write( "end value in line %d" % (line,) )
            if delim is None : sys.stdout.write( "\n" )
            else : sys.stdout.write( " delimited with %s\n" % (delim,) )
        return False
    def characters( self, line, val ) :
        if self._verbose :
            sys.stdout.write( "characters in line " + str( line ) )
            sys.stdout.write( " >>> " )
            sys.stdout.write( val )
            sys.stdout.write( " <<<\n" )

#
#
if __name__ == "__main__" :

    e = sas.ErrorHandler()
    c = Ch( verbose = False )
    l = sas.StarLexer( fp = sys.stdin, bufsize = 0, verbose = False )
    with sas.timer( "SAS" ) :
        p = SasParser.parse( lexer = l, content_handler = c, error_handler = e, verbose = False )

