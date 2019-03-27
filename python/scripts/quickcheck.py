#!/usr/bin/python -u
#
# quick STAR syntax & keyword check
#

from __future__ import absolute_import

import sys
import os
import collections

_UP = os.path.join( os.path.split( __file__ )[0], ".." )
sys.path.append( os.path.realpath( _UP ) )
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

    @classmethod
    def check_nmr_star( cls, fp, dictionary = None, verbose = False ) :
        chk = cls( dictionary )
        lex =  sas.StarLexer( fp, bufsize = 0, verbose = verbose )
        p = sas.SansParser.parse( lexer = lex, content_handler = chk, error_handler = chk, verbose = verbose )
        return (not chk._errs)

    @classmethod
    def check_nmr_star_file( cls, filename, dictionary = None, verbose = False ) :
        rc = False
        with open( filename, "rU" ) as fp :
            rc = cls.check_nmr_star( fp, dictionary, verbose )
        return rc

# TODO: add methods to check mmCIF and DDL if anyone ever needs them
#

    #
    #
    def __init__( self, dictionary ) :
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
    if len( sys.argv ) > 1 :
        infile = sys.argv[1]
    if len( sys.argv ) > 2 :
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

    if infile is None :
        rc = QuickCheck.check_nmr_star( fp = sys.stdin, dictionary = taglist, verbose = False ) # True )
    else :
        rc = QuickCheck.check_nmr_star_file( filename = infile, dictionary = taglist, verbose = False ) # = True )
    if not rc :
        sys.stderr.write( "%s check failed!\n" % ((infile is None and "stdin" or infile),) )

#
# eof
#
