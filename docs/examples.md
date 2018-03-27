#Usage examples

Scripts in ``python/scripts`` directory:

##quickcheck.py

Read an input file or ``stdin``. Will generate parse errors and/or warnings
if the input has problems. Files in ``testfiles`` directory can be used as
example input.

When reading a file, the 2nd command line argument can be a list of valid
STAR tags. If present, ``quickcheck`` will also generate "invalid tag"
errors if it finds any tags in the input that are not in the list. An
example list is ``testfiles/taglist.csv``.

##getsequence.py

This script is used at BMRB to generate FASTA sequence databases from 
BMRB entries. Much of the code in there is BMRB-specific (file paths etc.)
but teh code handler class is a good example of using the parser to extract
specific tag/values from a BMRB entry.
