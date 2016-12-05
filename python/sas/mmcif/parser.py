#!/usr/bin/python -u

from __future__ import absolute_import

import sys
import os
import pprint

_UP = os.path.join( os.path.split( __file__ )[0], "../.." )
sys.path.append( os.path.realpath( _UP ) )
import sas

# this parser returns a data item (tag/value pair) in one callback (loop values are matched w/ headers)
# in mmcif loop terminators are implicit, so the parser fakes endLoop()s.
# there are no saveframes so start/endSaveframe() never fire.
# no _parse_save() methid here either.
#
class CifParser( object ) :

    """
    Parser for ``ContentHandler`` interface, see ``handlers.py`` for details.

    This is mmCIF so it never calls ``startSaveframe()``/``endSaveframe()``. They don't need to be
    implemented.

    Loop ends are implicit in mmCIF, but we still generate ``endLoop()`` calls. Note, however,
    that a comment after a loop will fire before the ``endLoop()`` as there's no way to tell
    whether it belongs inside the loop or out.
    """

    #
    #
    def __init__( self, lex, ch, eh, verbose = False ) :
        """
        constructor

        ``lex``: ``sas.StarLexer``
        ``ch`` : ``sas.ContentHandler``
        ``eh`` : ``sas.ErrorHandler``
        ``verbose`` flag is optional
        """

        assert isinstance( lex, sas.StarLexer )
        assert isinstance( ch, sas.ContentHandler )
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

        returns ``SansParser`` instance
        """
        parser = cls( lex = lexer, ch = content_handler, eh = error_handler, verbose = verbose )
        assert isinstance( parser, CifParser )
        parser._parse_file()
        return parser

    # read a delimited value
    # returns a pair: val, stop where stop is the "stop parsing" sign
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
                        if val.endswith( "\n" ) :
                            val = val.rstrip( "\n" )
                        break

                for pat in sas.KEYWORDS :
                    m = pat.search( token.value.strip() )
                    if m :
                        if self._eh.warning( line = token.lineno, msg = "keyword in value: %s" \
                                % (m.group( 1 ),) ) :
                            stop = True
                        break
                val += token.value

            else :
                self._eh.fatalError( line = token.lineno, msg = "EOF in delimited value: %s" % (rc,) )
                stop = True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            stop = True

        return (val, stop)

    # top-level parse does not return anything
    #
    def _parse_file( self ) :
        """Top (file) level parse"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler )
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
                self._ch.endData( line = token.lineno, name = self._data_name )
                return

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return

    # returns a stop sign: if true: stop parsing
    #
    def _parse_data( self ) :
        """Parse data block"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_data()\n" )

        need_value = False
        last_tag = None

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return True
                    continue

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
                    last_tag = (token.value,token.lineno)
                    need_value = True
                    continue

                if token.type in ("CHARACTERS","FRAMECODE") :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here: %s" \
                                % (token.value,) ) :
                            return True
                    assert isinstance( last_tag, tuple )
                    if self._ch.data( tag = last_tag[0], tagline = last_tag[1], val = token.value,
                            valline = token.lineno, delim = sas.TOKENS[token.type], inloop = False ) :
                        return True
                    need_value = False
                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if not need_value :
                        if self._eh.error( line = token.lineno, msg = "value not expected here (found delimiter)" ) :
                            return True
                    assert isinstance( last_tag, tuple )
                    (val, stop) = self._read_value( token.type )
                    if stop : return True

                    if self._ch.data( tag = last_tag[0], tagline = last_tag[1], val = val,
                            valline = token.lineno, delim = sas.TOKENS[token.type], inloop = False ) :
                        return True
                    need_value = False
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in data block: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                if need_value :
                    self._eh.fatalError( line = token.lineno, msg = "premature EOF, expected value" )
                    return True
                    
                    self._ch.endData( line = token.lineno, name = self._data_name )
                    return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

    # returns a stop sign: if true: stop parsing
    #
    def _parse_loop( self ) :
        """Parse loop"""
        assert isinstance( self._lexer, sas.StarLexer )
        assert isinstance( self._ch, sas.ContentHandler )
        assert isinstance( self._eh, sas.ErrorHandler )

        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._parse_loop()\n" )

        reading_tags = True
        reading_vals = False
        tags = []
        tag_idx = -1
        numvals = 0

        try :
            for token in self._lexer :

                if token.type in ("NL", "SPACE" ) : continue

                if token.type == "COMMENT" :
                    if self._ch.comment( line = token.lineno, text = token.value ) :
                        return True
                    continue

# exit points: the loop ends with another loop or a tag or eof after values
#
                if token.type == "LOOPSTART" :
                    if reading_tags :
                        if len( tags ) < 1 :
                            if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                                return True
                        if self._eh.error( line = token.lineno, msg = "found loop_, expected value" ) :
                            return True
                    else :
                        if (numvals % len( tags )) != 0 :
                            if self._eh.error( line = token.lineno, msg = "Loop count error" ) :
                                return True
                    if self._ch.endLoop( line = token.lineno ) :
                        return True
# ugh
#
                    if token.lexer.lexpos > 4 : token.lexer.lexpos -= 5
                    else : raise sas.SasException( line = token.lineno, msg = "can't push back 'loop_'!" )
                    return False

                if token.type == "TAGNAME" :
                    if reading_vals :
                        if (numvals % len( tags )) != 0 :
                            if self._eh.error( line = token.lineno, msg = "Loop count error" ) :
                                return True
                        if self._ch.endLoop( line = token.lineno ) :
                            return True
                        if token.lexer.lexpos >= len( token.value ) :
                            token.lexer.lexpos -= len( token.value )
                        else :
                            raise sas.SasException( line = token.lineno, msg = "can't push back '%s'!" \
                                % (token.value,) )

                        return False

# else collect tags
#
                    tags.append( (token.value,token.lineno) )
                    continue

                if token.type in ("CHARACTERS","FRAMECODE") :
                    if reading_tags :
                        reading_tags = False
                        reading_vals = True

                    if len( tags ) < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True
                        else :
                            tags.append( "LOOP_WITH_NO_TAGS" )

                    numvals += 1
                    tag_idx += 1
                    if tag_idx >= len( tags ) :
                        tag_idx = 0
                    
                    if self._ch.data( tag = tags[tag_idx][0], tagline = tags[tag_idx][1], val = token.value,
                            valline = token.lineno, delim = sas.TOKENS[token.type], inloop = True ) :
                        return True
                    continue

                if token.type in ("SINGLESTART","TSINGLESTART","DOUBLESTART","TDOUBLESTART","SEMISTART") :
                    if reading_tags :
                        reading_tags = False
                        reading_vals = True

                    if len( tags ) < 1 :
                        if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                            return True
                        else :
                            tags.append( "LOOP_WITH_NO_TAGS" )

                    numvals += 1
                    tag_idx += 1
                    if tag_idx >= len( tags ) :
                        tag_idx = 0

                    (val, stop) = self._read_value( token.type )
                    if stop : return True

                    if self._ch.data( tag = tags[tag_idx][0], tagline = tags[tag_idx][1], val = val,
                            valline = token.lineno, delim = sas.TOKENS[token.type], inloop = True ) :
                        return True
                    continue

                if self._eh.error( line = token.lineno, msg = "invalid token in loop: %s : %s" \
                        % (token.type, token.value,) ) :
                    return True

            else :
                if len( tags ) < 1 :
                    if self._eh.error( line = token.lineno, msg = "Loop with no tags" ) :
                        return True
                if numvals < 1 :
                    if self._eh.error( line = token.lineno, msg = "Loop with no values" ) :
                        return True                           
                if (numvals % len( tags )) != 0 :
                    if self._eh.error( line = token.lineno, msg = "Loop count error" ) :
                        return True
                if self._ch.endLoop( line = token.lineno ) :
                    return True
                self._ch.endData( line = token.lineno, name = self._data_name )
                return True

        except sas.SasException, e :
            self._eh.fatalError( line = e._line, msg = "Lexer error: " + str( e._msg ) )
            return True

###################################################################################################
# test handler
#
class Ch( sas.ContentHandler ) :
    def __init__( self, verbose = False ) :
        self._verbose = bool( verbose )
    def startData( self, line, name ) :
        if self._verbose : sys.stdout.write( "Start data block %s in line %d\n" % (name, line,) )
        return False
    def endData( self, line, name ) :
        if self._verbose : sys.stdout.write( "End data block %s in line %d\n" % (name, line,) )
    def startLoop( self, line ) :
        if self._verbose : sys.stdout.write( "Start loop in line %d\n" % (line,) )
        return False
    def endLoop( self, line ) :
        if self._verbose : sys.stdout.write( "End loop in line %d\n" % (line,) )
    def comment( self, line, text ) :
        if self._verbose : sys.stdout.write( "Comment %s in line %d\n" % (text, line,) )
        return False
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if self._verbose :
            sys.stdout.write( "data item %s in line %d:%d, delim=%s, inloop=%s - " \
                % (tag, tagline, valline, str( delim ), str( inloop ),) )
            sys.stdout.write( val )
            sys.stdout.write( "\n" )
        return False

#
#
if __name__ == "__main__" :

    e = sas.ErrorHandler()
    c = Ch( verbose = True )
    l = sas.StarLexer( fp = sys.stdin, bufsize = 0 ) #, verbose = True )
    with sas.timer( "CIF" ) :
        p = CifParser.parse( lexer = l, content_handler = c, error_handler = e, verbose = False )
