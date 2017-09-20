#!/usr/bin/python -u
#
# quick STAR syntax & keyword check
#

from __future__ import absolute_import

import sys
import os
import collections
import sas

if (sys.version_info[0] == 2) and (sys.version_info[1] > 6) :
    sys.path = list( collections.OrderedDict.fromkeys( sys.path ) )

#
#
class QuickCheck( sas.ContentHandler, sas.ErrorHandler ) :
    """
    Parse STAR file to make sure it's valid.

    An optional parameter is a list of valid tags, if not NULL
    also check the tags in the file.

    Uses ```sas.ContentHandler``` so it should work on any
    kind of STAR file.
    """

    def __init__( self, dictionary, *args, **kwargs ) :
        super( self.__class__, self ).__init__( *args, **kwargs )
        if dictionary is not None :
            assert isinstance( dictionary, collections.Iterable )
        self._dict = dictionary
        self._errs = False

    def fatalError( self, line, msg ) :
        sys.stderr.write("critical parse error in line %s: %s\n" % (line, msg))
        self._errs = True
    def error( self, line, msg ) :
        sys.stderr.write("parse error in line %s : %s\n" % (line, msg))
        self._errs = True
        return True

    # treat warnings as non-errors, for now
    #
    def warning( self, line, msg ) :
        sys.stderr.write("parser warning in line %s : %s\n" % (line, msg))
        return False


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

    # check tag
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        if self._dict is not None :
            if not tag in self._dict :
                sys.stderr.write("invalid tag in line %s : %s\n" % (tagline, tag))
                self._errs = True
        return False

#
#
#
if __name__ == "__main__" :

    infile = None
    dictfile = None
    if len( sys.argv ) > 0 :
        infile = sys.argv[1]
    if len( sys.argv ) > 1 :
        dictfile = sys.argv[2]

    taglist = set()
    if dictfile is not None :
        with open( dictfile, "rU" ) as f :
            for line in f :
                tag = line.strip()
                if (tag[0] == "'") and (tag[-1] == "'" ) :
                    tag = tag.strip( "'" )
                elif (tag[0] == '"') and (tag[-1] == '"' ) :
                    tag = tag.strip( '"' )
                if tag != "" :
                    taglist.add( tag )
    if len( taglist ) < 1 :
        taglist = None

    h = QuickCheck( dictionary = taglist )
    if infile is not None :
        with open( infile, "rU" ) as f :
            lex =  sas.StarLexer( fp = f, bufsize = 0 )
            p = sas.SansParser.parse( lexer = lex, content_handler = h, error_handler = h )
    else :
        lex =  sas.StarLexer( fp = sys.stdin, bufsize = 0 )
        p = sas.SansParser.parse( lexer = lex, content_handler = h, error_handler = h )

    if h._errs :
        sys.stderr.write( "%s check failed!\n" % ((infile is None and "stdin" or infile),) )

#
# eof
#
