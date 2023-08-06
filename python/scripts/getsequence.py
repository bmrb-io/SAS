#!/usr/bin/python -u
#
# Extract residue sequences from BMRB entries
# and save them in SEQFILE(s) in FASTA format.
#
# Prefer v.3.1 over v.2.1 files and canonical over "non-canonical" sequence.
#
# Replace PDB-style "(CompID)", if any, with "X".
#
# FASTA comment is for BLAST search database:
#  gnl|mdb|bmrb<ID>:<Entity ID> <molecule name>
#
# Entity IDs are "faked" for 2.1 entries: we just count
# entity saveframes. For 3.1 it's value of  _Entity.ID
#
# Molecule name is _Entity.Name for 3.1 files and the name
# of the entity saveframe for 2.1 files.
#

import os
import sys
import re
import pprint
import subprocess
import argparse
import glob

_UP = os.path.realpath( os.path.join( os.path.split( __file__ )[0], ".." ) )
sys.path.append( _UP )
import sas

#
#
#
class Getsequence( object ) :

# files are in ${ENTRYDIR}/bmr${ID}/clean/bmr${ID}_[3|21].str
#
    ENTRYDIR = "/projects/BRMB/private/entrydirs/macromolecules"
    CLEANDIR = "%s/clean"
    ENTRYFILE2 = "bmr%s_21.str"
    ENTRYFILE3 = "bmr%s_3.str"

# this goes into ${ENTRYDIR}/bmr${ID}/clean/bmr${ID}.%s.fasta
# the last %s here is "prot", "dna", or "rna", dep. on type
#
    SEQFILE = "bmr%s.%s.fasta"

# fasta header for blast
#
    HEADER = ">gnl|mdb|bmrb%s:%s %s"

    #
    #
    @classmethod
    def runall( cls ) :
        obj = cls()
        for d in glob.glob( os.path.join( cls.ENTRYDIR, "bmr*" ) ) :
            m = cls._pat.search( d )
            if not m :
#            sys.stderr.write( "%s does not match pattern\n" % (d,) )
                continue

            obj.getsequence( m.group( 1 ) )

        return obj

    #
    #
    def init( self ) :
        _pat = re.compile( r"bmr(\d+)$" )
        _seqs = {}

# these are sequence files
        _updated = 0
        _deleted = 0

# and these are entries
        _errors = 0
        _total = 0

    #
    #
    @property
    def sequences( self ) :
        return self._seqs

    #
    #
    def getsequence( self, bmrbid ) :
        self._total += 1
        entryfile = os.path.join( self.CLEANDIR % (bmrbid,), self.ENTRYFILE3 % (bmrbid,) )
        if not os.path.exists( entryfile ) :
            entryfile = os.path.join( self.CLEANDIR % (bmrbid,), self.ENTRYFILE2 % (bmrbid,) )

# not released?
#
        if not os.path.exists( entryfile ) :
            return

        self.parse( entryfile, bmrbid )

# got sequences ?
#
        for i in ("dna", "prot", "rna") :
            outfile = os.path.join( self.CLEANDIR % (bmrbid,), self.SEQFILE % (bmrbid,i,) )
            if os.path.exists( outfile ) :
                if len( self._seqs[i] ) < 1 :

#FIXME: check 4 errs
                    self.unlink( outfile )
                    continue

            self.update( self._seqs[i], outfile )

    #
    #
    def parse( self, entryfile, bmrbid ) :

        self._seqs.clear()
        data = StarParser.parse_file( entryfile )
        if data is None :
            self._errors += 1
            return

        self._seqs["rna"] = []
        self._seqs["dna"] = []
        self._seqs["prot"] = []

        for eid in sorted( data.keys() ) :
            if not "type" in data[eid].keys() : 
#ERR: no molecule type
                continue
            if data[eid]["type"] is None : 
#ERR: null molecule type
                continue
            if data[eid]["type"] in (".","?") : 
#ERR: ditto
                continue

            restype = None
            if (data[eid]["type"].lower() == "protein") \
            or (data[eid]["type"][:11].lower() == "polypeptide") :
                restype = "prot"

            elif (data[eid]["type"].lower() == "rna") \
            or (data[eid]["type"].lower() == "polyribonucleotide") :
                restype = "rna"

            elif (data[eid]["type"].lower() == "dna") \
            or (data[eid]["type"].lower() == "polydeoxyribonucleotide") :
                restype = "dna"

            if not restype in ("dna","prot","rna") :
# skip
                continue

            seq = ""
            if "seq_can" in data[eid].keys() :
                seq = self.fix_sequence( data[eid]["seq_can"], kind = restype )
            if seq == "" :
                if "seq" in data[eid].keys() :
                    seq = self.fix_sequence( data[eid]["seq"], kind = restype )

            if seq == "" : 
#ERR(?) no sequence
                continue

            name = ""
            if "name" in data[eid].keys() :
                if data[eid]["name"] is not None :
                    if not data[eid]["name"] in (".","?") :
                        name = data[eid]["name"]
# types
#
            seqstr = HEADER % (bmrbid,eid,name,)
            seqstr += "\n"
            seqstr += seq

            if restype == "prot" :
                self._seqs["prot"].append( seqstr )

            elif restype == "rna" :
                self._seqs["rna"].append( seqstr )

            elif restype == "dna" :
                self._seqs["dna"].append( seqstr )

            return

    #
    #
    def fix_sequence( self, seq, kind = "prot" ) :
        """upcase, replace "(ABC)" with "X", (re-)wrap at 80 chars"""

        if not kind in ("dna", "prot", "rna") : return ""
        if (seq is None) or (seq in (".","?",)) : return ""
        rc = re.sub( r"\s+", "", seq )
        rc = re.sub( r"(\(.+\))", "X", rc )
        rc = rc.upper()

# nucl. acid notation uses N for "any nucleotide, not a gap"
# blast complains about Xes
#
        if kind in ("dna", "rns") : rc = rc.replace( "X", "N" )
        rc = "\n".join( rc[i:i+80] for i in xrange( 0, len( rc ), 80 ) )
        return rc

    # wrapper that does cvs rm with unlink
    # need this becasue a cron job does auto cvs add/cvs commit
    # on all files in entrydir
    #
    def unlink( self, filename ) :

        here = os.getcwd()
        (where,name) = os.path.split( filename )
        os.chdir( where )
        cmd = ["cvs", "rm", name]
        os.unlink( filename )
        p = subprocess.Popen( cmd )
        p.wait()

        os.chdir( here )
        if p.returncode == 0 : self._deleted += 1

        return p.returncode

    #
    #
    def update( self, sequences, outfile ) :
        newstr = ""
        for seq in self._seqs[t] :
            newstr += seq + "\n"
        if len( newstr.strip() ) < 1 :
            if os.path.exists( outfile ) :

#FIXME: check 4 errs
                self.unlink( outfile )
            return

        oldstr = ""
        if os.path.exists( outfile ) :
            with open( outfile, "rU" ) as f :
                oldstr = f.read()

# not updated?
#
        if oldstr == newstr :
            return

# still here?
#
        with open( outfile, "w" ) as f :
            f.write( newstr )
            self._updated += 1


########################################################
#
# STAR parser: extract entity IDs, types and sequence(s)
# 
class StarParser( sas.ContentHandler, sas.ErrorHandler ) :

    _entryid = None
    _entityid = 0
    _sfname = None
    _errs = 0

# data is a dict of { "entity id" : { "type" : [prot|dna|rna], "name" : , "seq" } }
# returned by parse methods
#
    _data = None

    #
    #
    @classmethod
    def parse( cls, fp, verbose = False ) :
        h = cls()
        lex = sas.StarLexer( fp, bufsize = 0 )
        p = sas.SansParser.parse( lexer = lex, content_handler = h, error_handler = h, verbose = verbose )
        if h._errs > 0 : return None
        return h._data

    @classmethod
    def parse_file( cls, filename, verbose = False ) :
        with open( filename, "rU" ) as f :
            return cls.parse( fp = f, verbose = verbose )

    def __init__( self ) :
        self._data = {}

# SAS callbacks
#
    def fatalError( self, line, msg ) :
        sys.stderr.write("critical parse error in line %s: %s\n" % (line, msg))
        self._errs += 1

    def error( self, line, msg ) :
        sys.stderr.write("parse error in line %s : %s\n" % (line, msg))
        self._errs += 1
        return True

    # treat warnings as non-errors and suppress messages
    #
    def warning( self, line, msg ) :
#        sys.stderr.write("parser warning in line %s : %s\n" % (line, msg))
        return False

# unused callbacks
#
    def startData( self, line, name ) :
        return False
    def endData( self, line, name ) :
        pass
    def endSaveframe( self, line, name ) :
        return False
    def startLoop( self, line ) :
        return False
    def endLoop( self, line ) :
        return False
    def comment( self, line, text ) :
        return False

    # need this for 2.1 files
    #
    def startSaveframe( self, line, name ) :
        self._sfname = name
        return False

    #
    #
    def data( self, tag, tagline, val, valline, delim, inloop ) :

# 3.1
# ID comes before Name in properly formatted NMR-STAR file
#
        if tag == "_Entity.ID" :
            self._entityid = val
            if not val in self._data.keys() :
                self._data[val] = {}
        if tag == "_Entity.Name" :
            self._data[self._entityid]["name"] = str( val ).replace( "\n", " " ).strip()

# 2.1 - fake entity IDs
#
        if (tag == "_Saveframe_category") and (val == "monomeric_polymer") :
            e = 1
            for i in self._data :
                if i > e : e = i
            self._entityid = e
            self._data[e] = {}
            if self._sfname is not None : 
                self._data[e]["name"] = self._sfname

# 3.1 or 2.1
#
        if (tag == "_Entity.Polymer_type") or (tag == "_Mol_polymer_class") :
            self._data[self._entityid]["type"] = val

        if (tag == "_Entity.Polymer_seq_one_letter_code_can") or (tag == "_Mol_residue_sequence") :
            self._data[self._entityid]["seq_can"] = val.replace( "\n", "" ).replace( " ", "" )

        if tag == "_Entity.Polymer_seq_one_letter_code" :
            self._data[self._entityid]["seq"] = val.replace( "\n", "" ).replace( " ", "" )

# shortcut: natural source is mandatory & comes after entities -- stop parsing
#
        if tag == "_Entity_natural_src_list.Sf_category" : return True
        if (tag == "_Saveframe_category") and (val == "natural_source") : return True

        return False


#    ap = argparse.ArgumentParser( description = "read residue sequence(s) from NMR-STAR file" )
#    ap.add_argument( "-v", "--verbose", help = "print lots of messages to stdout", dest = "verbose",
#    action = "store_true", default = False )
#    args = ap.parse_args( sys.argv[1:] )


#
#
#
if __name__ == "__main__" :

    obj = Getsequence.runall()
    sys.stdout.write( "%d entries processed, %d errors, %d sequence files updated, %d deleted\n" \
            % (obj._total, obj._errors, obj._updated, obj._deleted,) )

#
# eof
