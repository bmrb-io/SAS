#!/usr/bin/python -u
#
# ***************************************************************************
# Scanner flex specification
# ***************************************************************************
# Lex Definitions for a STAR File
#
# PLY specification that, while not compatible with flex/jflex, 
#  is hopefully easier to deal with than the hand-written regex lexer
#

"""
PLY lexer for STAR-ish input

The *-ish* above refers to

  * incompatibilities between Python regular expressions PLY is built on and STAR specifications,
    both 1994 and 2012 extensions. This affects character handling: unicode, whitespace, newline.
  * Lack of support for STAR-2012 extensions: triple-quoted values are supported, but lists, tables,
    and ref-tables (references) are not.

The lexer is fastest when you feed it one line at a time. They must be whole lines, or 
semicolon-delimited values may not be recognized properly. When parsing a ``file`` the scanner
will buffer lines of input. Setting buffer size to 0 makes it buffer one line at a time.

STAR references:

  1. Hall, S. R., "The STAR File: A New Format for Electronic Data Transfer and Archiving",
     J. Chem. Inf. Comput. Sci. 31, 326-333(1991).

  2. Hall, S. R. and Spadaccini, N., "The STAR File: Detailed Specifications",
     J. Chem. Inf. Comput. Sci. 34, 505-508 (1994).

  3. Hall, S. R. and Cook, A. P. F., "STAR Dictionary Definition Language: Initial Specification",
     J. Chem. Inf. Comput. Sci. 35, 819-825 (1995).

  4. Allen, F. H., Barnard, J. M., Cook, A. P. F., and Hall, S. R., "The Molecular Information File
     (MIF): Core Specifications of a New Standard Format for Chemical Data,"
     J. Chem. Inf. Comput. Sci. 35, 412-427 (1995).

  5. Spadaccini, N. and Hall, S. R., "Extensions to the STAR File Syntax"
     J. Chem. Inf. Model., 52 (8), 1901-1906 (2012)
     DOI: 10.1021/ci300074v

"""

from __future__ import absolute_import

import sys
import os
import re
import ply.lex as lex
import collections
import types
import pprint

_UP = os.path.join( os.path.split( __file__ )[0], ".." )
sys.path.append( os.path.realpath( _UP ) )
import sas

################################################################
# PLY lexer for STAR-ish input
# read the fine comments below
#
# this can be used as either a generator or a filter (both classmethods): see __main__
# make sure you feed it complete lines: can't detect delimiting semicolons otherwise.
#
class StarLexer( object ) :
    """
    STAR lexer

    The lexer is an iterator/generator that parse a buffer and returns PLY ``LexToken`` objects.
    See ``__main__`` for example of either usage.

    Methods prefixed with ``t_`` are how PLY defines lexer tokens. Read PLY manual for details.
    """

# lexical states

    states = (
        ( "YYSINGLE", "exclusive" ),
        ( "YYTSINGLE", "exclusive" ),
        ( "YYDOUBLE", "exclusive" ),
        ( "YYTDOUBLE", "exclusive" ),
        ( "YYSEMI", "exclusive" ),
    )

# tokens

    tokens = (
        "NL",
        "SPACE",
        "ESQUOTE",
        "SQUOTE",
        "TSQUOTE",
        "EDQUOTE",
        "DQUOTE",
        "TDQUOTE",
        "SEMICOLON",

# STAR

        "COMMENT",
        "GLOBALSTART",
        "DATASTART",
        "SAVESTART",
        "SAVEEND",
        "LOOPSTART",
        "STOP",
        "SINGLESTART",
        "SINGLEEND",
        "TSINGLESTART",
        "TSINGLEEND",
        "DOUBLESTART",
        "DOUBLEEND",
        "TDOUBLESTART",
        "TDOUBLEEND",
        "SEMISTART",
        "SEMIEND",
        "FRAMECODE",
        "TAGNAME",
        "CHARACTERS",
    )

# this is for lookahead/behind
#
    whitespace_pattern = re.compile( r"\s" )
    newline_pattern = re.compile( r"\n" )

# token regexps
#  method-tokens are applied in order 
#  except for the exceptions

    #
    #
    def t_ANY_error( self, t ) :
        return t

# whitespace and other animals
#
# STAR-94: blank     = ASCII 32 | ASCII 9
#          newline   = ASCII 10
#          non-blank = ASCII 33..126
# STAR-12: space     = U+0020 | U+0009
#          newline   = system-dependent EOL sequence
#          non-blank = anything other than <space>, <newline>, or U+0007
#
# This implementation:
#          blank     = \s
#          newline   = \n
#          non-blank = \S

# STAR-2012 further specifies that any character outside of (U+0007, U+0009, U+000A, U+000D,
#  U+0020..U+D7FF, U+E000..U+FFFD, U+10000..U+10FFF) range is illegal and throws a lexer error.
#  we don't do that unless PLY lexer (python regexp) does.
# furthermore U+0007 is only legal inside quoted strings. we don't do that either.
#

# need lookahead/lookbehind for "\n;", " '", and "' "
#
# \s with unicode flag will match [ \t\n\r\f\v] plus unicode spaces. We need to differentiate
# between space and (system-dependent?) \n for the "\n;". Simple stupid way: define space as
# a token and ignore it in the parser later.
#
    # newlines
    #  error
    #
    def t_YYSINGLE_YYDOUBLE_NL( self, t ) :
        r'\n+'
        t.lexer.lineno += len( t.value )
        raise sas.SasException( msg = "Newline in quoted value", line = t.lexer.lineno )

    #  keep count
    #
    def t_ANY_NL( self, t ) :
        r'\n+'
        t.lexer.lineno += len( t.value )
        return t

    # whitespace
    #  \s matches \n but NL above should trigger first
    #  however, this will catch "  \n  "
    #  "\n" only really matters in "\n;", that's why we need to separate \n's from \s'es
    # this will not match inside quoted values where we don't ignore space
    # 
    def t_SPACE( self, t ) :
        r"\s+"
        for c in t.value :
            if c == "\n" :
                t.lexer.lineno += 1
        return t

##############################################
# single and double quotes: the opening digraph is space+quote, closing is quote+space.
# STAR-2012 allows for escaping quotes with U+07: BEL+quote is not a delimiter and e.g.
# 'd\u+07' onofrio' should be parsed as "d' onofrio".
#
    # escaped single quote
    #
    def t_ANY_ESQUOTE( self, t ) :
        r"\x07'"
        if self._verbose :
            sys.stdout.write( "Escaped single quote in line %d\n" % (t.lexer.lineno,) )
        t.type = "CHARACTERS"
        t.value = t.value.lstrip( "\x07" )
        return t

    # opening triple-quote
    # this should be above single-single-quote so it matches first
    #
    def t_TSQUOTE( self, t ) :
        r"'''"
        if self._verbose :
            sys.stdout.write( "Opening 3xsingle quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.push_state( "YYTSINGLE" )
        t.type = "TSINGLESTART"
        return t

    # closing triple-quote
    # should be above "characters"
    #
    def t_YYTSINGLE_TSQUOTE( self, t ) :
        r"'''"
        if self._verbose :
            sys.stdout.write( "Closing 3xsingle quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.pop_state()
        t.type = "TSINGLEEND"
        return t

    def t_YYTSINGLE_CHARACTERS( self, t ) :
        r"(?:[^']+)|'{1,2}"
        if self._verbose :
            sys.stdout.write( "Line in triple-quotes (%d): |%s|\n" % (t.lexer.lineno,t.value) )
        return t

    # unescaped single quote in YYINITIAL starts YYSINGLE
    #
    def t_SQUOTE( self, t ) :
        r"'"
        if self._verbose :
            sys.stdout.write( "Opening single quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.push_state( "YYSINGLE" )
        t.type = "SINGLESTART"
        return t

    # unescaped single quote in YYSINGLE
    #
    def t_YYSINGLE_SQUOTE( self, t ) :
        r"'"
        if self._verbose :
            sys.stdout.write( "Single quote in line %d\n" % (t.lexer.lineno,) )

# lookahead
#  input reader must split on newlines or this will not work
#
        if t.lexer.lexpos == len( t.lexer.lexdata ) - 1 :
            t.type = "SINGLEEND"
            t.lexer.pop_state()
            return t

#
        m = self.whitespace_pattern.match( t.lexer.lexdata[t.lexer.lexpos] )
        if m :
            t.type = "SINGLEEND"
            t.lexer.pop_state()
            return t

# otherwise it's just a character
        t.type = "CHARACTERS"
        return t

    # single quote in any other state is just a character

    def t_YYDOUBLE_YYSEMI_SQUOTE( self, t ) :
        r"'"
        if self._verbose :
            sys.stdout.write( "Single quote in line %d\n" % (t.lexer.lineno,) )
        t.type = "CHARACTERS"
        return t

    # read chars (anything except U+07 or ')
    #
    def t_YYSINGLE_CHARACTERS( self, t ) :
        r"[^'\x07\n]+"
        if self._verbose :
            sys.stdout.write( "chars in single quotes in line %d: |%s\n" % (t.lexer.lineno,t.value) )
        return t

##################################
# same for doubles

    # escaped double quote
    #
    def t_ANY_EDQUOTE( self, t ) :
        r'\x07"'
        if self._verbose :
            sys.stdout.write( "Escaped double quote in line %d\n" % (t.lexer.lineno,) )
        t.type = "characters"
        t.value = t.value.lstrip( "\x07" )
        return t

    # opening triple-double-quote
    # this should be above single-double-quote so it matches first
    #
    def t_TDQUOTE( self, t ) :
        r'"""'
        if self._verbose :
            sys.stdout.write( "Opening 3xdouble quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.push_state( "YYTDOUBLE" )
        t.type = "TDOUBLESTART"
        return t

    # closing triple-quote
    # should be above "characters"
    #
    def t_YYTDOUBLE_TDQUOTE( self, t ) :
        r'"""'
        if self._verbose :
            sys.stdout.write( "Closing 3xdouble quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.pop_state()
        t.type = "TDOUBLEEND"
        return t

    def t_YYTDOUBLE_CHARACTERS( self, t ) :
        r'(?:[^"]+)|"{1,2}'
        if self._verbose :
            sys.stdout.write( "Line in triple-double-quotes (%d): |%s|\n" % (t.lexer.lineno,t.value) )
        return t

    # unescaped double quote in YYINITIAL
    #
    def t_DQUOTE( self, t ) :
        r'"'
        if self._verbose :
            sys.stdout.write( "Opening double quote in line %d\n" % (t.lexer.lineno,) )
        t.lexer.push_state( "YYDOUBLE" )
        t.type = "DOUBLESTART"
        return t

    # unescaped double quote in YYDOUBLE
    #
    def t_YYDOUBLE_DQUOTE( self, t ) :
        r'"'
        if self._verbose :
            sys.stdout.write( "Double quote in line %d\n" % (t.lexer.lineno,) )

# lookahead
#  input reader must split on newlines or this will not work
#
        if t.lexer.lexpos == len( t.lexer.lexdata ) - 1 :
            t.type = "DOUBLEEND"
            t.lexer.pop_state()
            return t

#
        m = self.whitespace_pattern.match( t.lexer.lexdata[t.lexer.lexpos] )
        if m :
            t.type = "DOUBLEEND"
            t.lexer.pop_state()
            return t

# otherwise it's just a character
        t.type = "CHARACTERS"
        return t

    # double quote in any other state is just a character
    #
    def t_YYSINGLE_YYSEMI_DQUOTE( self, t ) :
        r'"'
        if self._verbose :
            sys.stdout.write( "Double quote in line %d\n" % (t.lexer.lineno,) )
        t.type = "CHARACTERS"
        return t

    # read chars
    #
    def t_YYDOUBLE_CHARACTERS( self, t ) :
        r'[^"\x07\n]+'
        if self._verbose :
            sys.stdout.write( "chars in double quotes in line %d: |%s\n" % (t.lexer.lineno,t.value) )
        return t

#######################################################
# semicolons: both opening and closing digraph is "\n;"
#  technically the "\n" in closing "\n" is part of the delimiter, not part of the value
#
# if input reader splits on newlines, a bare ";" at the start of a chunk is actually a "\n;"
# -- except if it's the very first chunk. the parser above us should throw an error if the
# very first chunk didn't start with data_X or global_, so we should be OK here.
#
    # start YYSEMI state
    #
    def t_SEMICOLON( self, t ) :
        r";"
        if self._verbose :
            sys.stdout.write( "Semicolon in line %d\n" % (t.lexer.lineno,) )
#            print ">>> lexpos=", t.lexer.lexpos, ":", t.lexer.lexdata[t.lexer.lexpos - 2], ":"

# start of chunk or lookbehind
#  lexpos is after the match
#
        if t.lexer.lexpos == 1 :
            t.lexer.push_state( "YYSEMI" )
            t.type = "SEMISTART"
            return t

        if t.lexer.lexpos > 1 :
            m = self.newline_pattern.match( t.lexer.lexdata[t.lexer.lexpos - 2] )
            if m :
                t.lexer.push_state( "YYSEMI" )
                t.type = "SEMISTART"
                return t

# otherwise it's just a character

        t.type = "CHARACTERS"
        return t

    # in YYSEMI state
    #
    def t_YYSEMI_SEMICOLON( self, t ) :
        r";"
        if self._verbose :
            sys.stdout.write( "Semicolon in YYSEMI line %d\n" % (t.lexer.lineno,) )

        if t.lexer.lexpos == 1 :
            t.lexer.pop_state()
            t.type = "SEMIEND"
            return t

        if t.lexer.lexpos > 1 :
            m = self.newline_pattern.match( t.lexer.lexdata[t.lexer.lexpos - 2] )
            if m :
                t.lexer.pop_state()
                t.type = "SEMIEND"
                return t

# otherwise it's just a character

        t.type = "CHARACTERS"
        return t

    # otherwise it's just a character
    #
    def t_YYSINGLE_YYDOUBLE_SEMICOLON( self, t ) :
        r";"
        if self._verbose :
            sys.stdout.write( "Semicolon in quoted value in line %d\n" % (t.lexer.lineno,) )

        t.type = "CHARACTERS"
        return t

    # read entire lines (but NL is triggered separately as '.' doesn't match it)
    #
    def t_YYSEMI_CHARACTERS( self, t ) :
        r".+"
        if self._verbose :
            sys.stdout.write( "Line in semicolons (%d): |%s|\n" % (t.lexer.lineno,t.value) )
        return t

#######################################################
# the easy ones

#######################################################
# we keep comments by popular demand
#
# STAR-94 says '\s#' outside of quoted value is the EOL and everything that follows does not exist
# STAR-2012 says '#' starts a comment and a comment is whitespace.
#   it does not require a space before # !!! (we do)
#
    #  (strip the #)
    #
    def t_COMMENT( self, t ):
        r"\#.*"
        t.value = t.value[1:]
        return t

    #
    #
    def t_GLOBALSTART( self, t ) :
        r"[Gg][Ll][Oo][Bb][Aa][Ll]_"
        if self._verbose :
            sys.stdout.write( "Start global block in line %d\n" % (t.lexer.lineno,) )
        return t

    # strip "data_"
    #
    def t_DATASTART( self, t ) :
        r"[Dd][Aa][Tt][Aa]_\S+"
        if self._verbose :
            sys.stdout.write( "Start data |%s| in line %d\n" % (t.value,t.lexer.lineno,) )
        t.value = t.value[5:]
        return t

    # strip "save_"
    #
    def t_SAVESTART( self, t ) :
        r"save_\S+"
        if self._verbose :
            sys.stdout.write( "Start saveframe |%s| in line %d\n" % (t.value,t.lexer.lineno,) )
        t.value = t.value[5:]
        return t

    #
    #
    def t_SAVEEND( self, t ) :
        r"save_"
        if self._verbose :
            sys.stdout.write( "End saveframe in line %d\n" % (t.lexer.lineno,) )
        return t

    #
    #
    def t_LOOPSTART( self, t ) :
        r"loop_"
        if self._verbose :
            sys.stdout.write( "Start loop in line %d\n" % (t.lexer.lineno,) )
        return t

    #
    #
    def t_STOP( self, t ) :
        r"stop_"
        if self._verbose :
            sys.stdout.write( "End loop in line %d\n" % (t.lexer.lineno,) )
        return t

#######################################################

    # tag
    #
    # STAR is _<non-whitespace> but python's \S != STAR non-whitespace
    #
    # with unicode it may have to be
    #    r"^_[\x33-\x7f]+"
    #
    # PDB regex:
    #    r"^_[_A-Za-z0-9]+[_.A-Za-z0-9%\-\]\[]+"
    #
    # all of the above:
    #    r"_\w[\x33-\x7f\.\w\-\]\[/%]+"
    #
    def t_TAGNAME( self, t ) :
        r"_\S+"
        if self._verbose :
            sys.stdout.write( "Tag in line %d: |%s|\n" % (t.lexer.lineno,t.value) )
        return t

#######################################################
# values

    # strip leading '$'
    #
    def t_FRAMECODE( self, t ) :
        r"$\S+"
        if self._verbose :
            sys.stdout.write( "Framecode value in line %d: |%s|\n" % (t.lexer.lineno,t.value) )
        t.value = t.value.lstrip( "$" )
        return t

    # bareword: as with tagname, python non-whitespace
    #
    def t_CHARACTERS( self, t ) :
        r"\S+"
        if self._verbose :
            sys.stdout.write( "Bareword value in line %d: |%s|\n" % (t.lexer.lineno,t.value) )
        return t

    def t_error( self, v ) :
        raise sas.SasException( line = t.lexer.lineno, msg = v )

#######################################################
# class, generator, iterator, etc.

    #
    #
    def __init__( self, fp = None, bufsize = 65534, verbose = False, **lexer_args ) :
        """
        constructor

        ``fp`` is a ``file`` object (or feed me lines via ``send()``)
        ``bufsize``: read input lines (``fp.readline()``) into a buffer until it's over ``bufsize``,
                     then parse the buffer
        ``lexer_args`` are passed on to PLY lexer
        """

        if verbose : sys.stdout.write( self.__class__.__name__ + ".init()\n" )

        self._fp = fp
        self._bufsize = bufsize
        self._verbose = bool( verbose )
        self.lexer = lex.lex( module = self, **lexer_args )

    # iterator
    #
    def __iter__( self ) :
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".__iter__()\n" )
        return self

    # py3 compat.
    #
    def __next__( self ) :
        return self.next()

    # generator: reads the next chunk of input and feeds it to the lexer
    #
    def _input_reader( self ) :
        """buffering input reader: reads lines until the buffer is greater than _bufsize,
            then yields the buffer."""
        if self._verbose : sys.stdout.write( self.__class__.__name__ + "._input_reader()\n" )
        assert isinstance( self._fp, file )
        buf = ""
        for line in self._fp :
            buf += line
            if len( buf ) >= self._bufsize :
                self.lexer.input( buf )
                yield
                buf = ""

# out of for: last chunk
#
        if len( buf ) > 0 :
            self.lexer.input( buf )
            yield

    #
    #
    def next( self ) :
        """returns the next lexer token"""
        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".next()\n" )


# fisrt chunk of data: if reading from a file we need to fire off the feeder
#
        if self._fp is not None : inp = self._input_reader()

        if (self.lexer.lexdata is None) or (len( self.lexer.lexdata ) < 1) :

# if we're not reading a file, we must be fed via send()
# tell 'em to feed us more input
#
            if self._fp is None : raise StopIteration

# or else bite off a chunk ourselves
#
            else : inp.next()

        rc = self.lexer.token()
        if rc is None :
            if self._fp is None : raise StopIteration
            else : inp.next()
            rc = self.lexer.token()

# if it's none again, we're done
#
            if rc is None : raise StopIteration

        assert hasattr( rc, "lineno" )
        assert hasattr( rc, "type" )
        assert hasattr( rc, "value" )

        return rc

    #
    #
    def send( self, lines ) :
        """feed the next chunk of lines to the lexer.

        NOTE that they must be whole lines, or bad things will happen"""

        if self._verbose : sys.stdout.write( self.__class__.__name__ + ".send()\n" )

        self.lexer.input( lines )

#
#

if __name__ == "__main__" :

#    l = StarLexer( verbose = True )
#    lex.runmain()

    iterator = True
    if len( sys.argv ) > 1 :
        if sys.argv[1] == "send" :
            iterator = False

    if iterator :
        with sas.timer( "lexer (iter)" ) :
            l = StarLexer( fp = sys.stdin, bufsize = 0 ) # , verbose = True )
            for t in l :
#                pprint.pprint( t )
                pass

    else :
        with sas.timer( "lexer (send)" ) :
            l = StarLexer() #  verbose = True )
            for line in sys.stdin :
                l.send( line )
                for t in l :
#                    pprint.pprint( t )
                    pass

