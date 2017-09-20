#!/usr/bin/python -u
#
# NOTE: if you want "installable" egg, edit the sources and comment out every
#   sys.path.append( ... __file__ ...
# before building
#
import setuptools
setuptools.setup( name = "quickcheck", version = "1.0", 
    packages = setuptools.find_packages(),
    py_modules = ["__main__", "sas"] )
