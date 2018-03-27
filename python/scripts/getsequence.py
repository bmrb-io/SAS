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

from __future__ import absolute_import

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

# files are in ${ENTRYDIR}/bmr${ID}/clean/bmr${ID}_[3|21].str
#
ENTRYROOT = "/share/subedit/entries"
ENTRYDIR = os.path.join( ENTRYROOT, "bmr%s/clean" )
ENTRYFILE2 = "bmr%s_21.str"
ENTRYFILE3 = "bmr%s_3.str"

# this goes into ${ENTRYDIR}/bmr${ID}/clean/bmr${ID}.%s.fasta
# the last %s here is "prot", "dna", or "rna", dep. on type
#
SEQFILE = "bmr%s.%s.fasta"

# fasta header for blast
#
HEADER = ">gnl|mdb|bmrb%s:%s %s"

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
            self._data[self._entityid]["name"] = val.strip()

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

# wrapper that does cvs rm with unlink
#
def unlink( filename, verbose = False ) :
    if verbose : sys.stdout.write( "unlink( %s )\n" % (filename,) )

    here = os.getcwd()
    (where,name) = os.path.split( filename )
    os.chdir( where )
    cmd = ["cvs", "rm", name]
    if verbose : pprint.pprint( cmd )
    os.unlink( filename )
    p = subprocess.Popen( cmd )
    p.wait()

    if verbose : 
        sys.stdout.write( "returned %d\n" % (p.returncode,) )

    os.chdir( here )
    return p.returncode

#
#
def fix_sequence( seq, verbose = False ) :
    """upcase, replace "(ABC)" with "X", (re-)wrap at 80 chars"""
    if verbose : sys.stdout.write( "fix_sequence( %s )\n" % (seq,) )
    if (seq is None) or (seq in (".","?",)) : return ""
    rc = re.sub( r"\s+", "", seq )
    rc = re.sub( r"(\(.+\))", "X", rc )
    rc = rc.upper()
    rc = "\n".join( rc[i:i+80] for i in xrange( 0, len( rc ), 80 ) )
    if verbose : sys.stdout.write( "fix_sequence()=%s\n" % (rc,) )
    return rc

# return values are dict { "err" : message } or { "upd" : N, "del" : M }
#
def update( bmrbid, verbose = False ) :
    """read and udpate one BMRB entry"""
    if verbose : sys.stdout.write( "update( %s )\n" % (bmrbid,) )
    global ENTRYDIR   # = "/share/subedit/entries/bmr%s/clean"
    global ENTRYFILE2 # = "bmr%s_21.str"
    global ENTRYFILE3 # = "bmr%s_3.str"
    global SEQFILE    #= "bmr%s.%s.fasta"
    global HEADER     #= ">gnl|mdb|bmrb%s:%s %s"

    infile = os.path.join( (ENTRYDIR % (bmrbid,)), (ENTRYFILE3 % (bmrbid,)) )
    if not os.path.exists( infile ) :
        infile = os.path.join( (ENTRYDIR % (bmrbid,)), (ENTRYFILE2 % (bmrbid,)) )

# nag
#
        if os.path.exists( infile ) :
            sys.stderr.write( "No 3.1 file for %s, using 2.1: %s\n" % (bmrbid,infile,) )
        else :

# not released yet ?
#
            if verbose :
                sys.stdout.write( "no STAR file %s for %s\n" % (infile,bmrbid,) )
            return { "err" : "File not found" }

    data = StarParser.parse_file( filename = infile, verbose = verbose )
    if data is None :
        sys.stderr.write( "Errors parsing %s\n" % (infile,) )
        return { "err" : "Parse error" }

    if verbose :
        sys.stdout.write( "Data:\n" )
        pprint.pprint( data )
# sort 'em out, they may be in any order
#
    rc = { "upd" : 0, "del" : 0 }
    s = {}
    s["rna"] = []
    s["dna"] = []
    s["prot"] = []

    for eid in sorted( data.keys() ) :
        if not "type" in data[eid].keys() : 
            if verbose : sys.stdout.write( "No type in %s\n" % (bmrbid,) )
            continue
        if data[eid]["type"] is None : 
            if verbose : sys.stdout.write( "No type in %s (none)\n" % (bmrbid,) )
            continue
        if data[eid]["type"] in (".","?") : 
            if verbose : sys.stdout.write( "No type in %s (null)\n" % (bmrbid,) )
            continue

        seq = ""
        if "seq_can" in data[eid].keys() :
            seq = fix_sequence( data[eid]["seq_can"], verbose = verbose )
        if seq == "" :
            if "seq" in data[eid].keys() :
                seq = fix_sequence( data[eid]["seq"], verbose = verbose )

        if seq == "" : 
            if verbose : sys.stdout.write( "No sequence in %s\n" % (bmrbid,) )
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

        if (data[eid]["type"].lower() == "protein") \
        or (data[eid]["type"][:11].lower() == "polypeptide") :
            s["prot"].append( seqstr )

        elif (data[eid]["type"].lower() == "rna") \
        or (data[eid]["type"].lower() == "polyribonucleotide") :
            s["rna"].append( seqstr )

        elif (data[eid]["type"].lower() == "dna") \
        or (data[eid]["type"].lower() == "polydeoxyribonucleotide") :
            s["dna"].append( seqstr )

#
#
    if verbose : pprint.pprint( s )
    for t in ("prot","dna","rna") :
        outname = SEQFILE % (bmrbid,t,)
        outfile = os.path.join( (ENTRYDIR % (bmrbid,)), outname )

        newstr = ""
        for seq in s[t] :
            newstr += seq + "\n"

        if os.path.exists( outfile ) :

            if len( newstr ) < 1 : 
                if verbose :
                    sys.stdout.write( "Deleting %s\n" % (outfile,) )
                unlink( outfile )
                rc["del"] += 1
                continue

            oldstr = ""
            with open( outfile, "rU" ) as f :
                oldstr = f.read()

            if oldstr == newstr :
                if verbose :
                    sys.stdout.write( "Not updating %s: not changed\n" % (outfile,) )
                continue

        else :
            if len( newstr ) < 1 : 
                continue

        with open( outfile, "w" ) as f :
            if verbose :
                sys.stdout.write( "Updating %s\n" % (outfile,) )
            f.write( newstr )
            rc["upd"] += 1

    return rc

# because setuptools won't run __main__
#
def main() :

    ap = argparse.ArgumentParser( description = "read residue sequence(s) from NMR-STAR file" )
    ap.add_argument( "-v", "--verbose", help = "print lots of messages to stdout", dest = "verbose",
        action = "store_true", default = False )

    args = ap.parse_args( sys.argv[1:] )

    pat = re.compile( r"bmr(\d+)$" )
    updated = 0
    deleted = 0
    errors = 0
    total = 0
    for d in glob.glob( os.path.join( ENTRYROOT, "*" ) ) :
        m = pat.search( d )
        if not m :
            sys.stderr.write( "%s does not match pattern\n" % (d,) )
            continue
        bmrbid = m.group( 1 )
        total += 1
        ret = update( bmrbid, verbose = args.verbose )
        if "err" in ret.keys() : 
            if ret["err"] != "File not found" : # probably unreleased
                errors += 1
        if "upd" in ret.keys() : updated += ret["upd"]
        if "del" in ret.keys() : deleted += ret["del"]

#        sys.stdout.write( ">%s:\n" % (bmrbid,) )
#        pprint.pprint( ret )

        ret.clear()

    sys.stdout.write( "%d entries processed, %d errors, %d sequence files updated, %d deleted\n" \
            % (total, errors, updated, deleted,) )

#
#
#
if __name__ == "__main__" :

    main()

#
# eof
