#!/usr/bin/python -u
#
# Interfaces for sas parsers.
#
# Except for EOF and fatalError callbacks,
# - callbacks can return True to stop the parser.
# - callbacks must return False to keep the parser going.
#
# MOst content handler callbacks below simply raise "Abstract method called".
#
from __future__ import absolute_import
import sys
import abc

# fatal error terminates parsing, but error and warning don't have to.
# override them to return False and keep going (use at own risk!)
#
class ErrorHandler :
    """
    Error handlers are common to all parser versions.

    These aren't defined as abstract methods so you can use the implementation.

    Non-fatal error and warning callbacks may return ``False`` to continue parsing
    (use at own risk, of course).
    """
    __metaclass__ = abc.ABCMeta
    def fatalError( self, line, msg ) :
        sys.stderr.write("critical parse error in line %s: %s\n" % (line, msg))
    def error( self, line, msg ) :
        sys.stderr.write("parse error in line %s : %s\n" % (line, msg))
        return True
    def warning( self, line, msg ) :
        sys.stderr.write("parser warning in line %s : %s\n" % (line, msg))
        return False

#
# This content handler defines single callback for a data item tag/value pair.
# Data item in a loop will have "inloop" flag set to True.
#
class ContentHandler :
    """
    In this interface a data item (tag/value pair) is returned in one callback.

    Loop items have ``inloop`` flag set to ``True``

    This is convenient in many cases, but can be inefficient on files with large
    semicolon- or triple-quote-delimited text values
    """

    __metaclass__ = abc.ABCMeta

    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def startGlobal( self, line ) :
        raise Exception( "Abstract method called" )
    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def endGlobal( self, line ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startData( self, line, name ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endData( self, line, name ) :
        raise Exception( "Abstract method called" )

    # not abstract because saveframes don't exist in mmcif
    #
    def startSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )
    # not abstract because saveframes don't exist in mmcif
    #
    def endSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def comment( self, line, text ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def data( self, tag, tagline, val, valline, delim, inloop ) :
        raise Exception( "Abstract method called" )

#
# This content handler has separate callbacks for tag and value
#
class ContentHandler2 :
    """
    This interface defines separate callbacks for tag ("data name") and value.

    Loops are parsed "as is" i.e. the parser will first return all tags then all values.

    This is convenient for e.g. database insertions.

    Can be inefficient on files with large semicolon- or triple-quote-delimited text values,
    about as fast as ``ContentHandler``.
    """
    __metaclass__ = abc.ABCMeta

    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def startGlobal( self, line ) :
        raise Exception( "Abstract method called" )
    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def endGlobal( self, line ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startData( self, line, name ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endData( self, line, name ) :
        raise Exception( "Abstract method called" )

    # not abstract because saveframes don't exist in mmcif
    #
    def startSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )
    # not abstract because saveframes don't exist in mmcif
    #
    def endSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def comment( self, line, text ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def tag( self, line, tag ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def value( self, line, val, delim ) :
        raise Exception( "Abstract method called" )

#
# This content handler is the closest to SAX
#
class SasContentHandler :
    """
    This interface defines callbacks for ```startValue```,```endValue```, and ```characters```.

    This is closest to SAX, the leanest, and also least validating.

    The extra function calls make this slower than the others in general, but on files with
    BLOB/CLOBs it is the fastest as well as leanest.
    """
    __metaclass__ = abc.ABCMeta

    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def startGlobal( self, line ) :
        raise Exception( "Abstract method called" )
    # not abstract because global blocks aren't used in mmcif or nmr-star
    #
    def endGlobal( self, line ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startData( self, line, name ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endData( self, line, name ) :
        raise Exception( "Abstract method called" )

    # not abstract because saveframes don't exist in mmcif
    #
    def startSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )
    # not abstract because saveframes don't exist in mmcif
    #
    def endSaveframe( self, line, name ) :
        raise Exception( "Abstract method called" )

    @abc.abstractmethod
    def startLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endLoop( self, line ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def comment( self, line, text ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def tag( self, line, tag ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def startValue( self, line, delim ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def endValue( self, line, delim ) :
        raise Exception( "Abstract method called" )
    @abc.abstractmethod
    def characters( self, line, val ) :
        raise Exception( "Abstract method called" )
