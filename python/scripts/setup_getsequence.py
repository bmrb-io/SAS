#!/usr/bin/python -u
#
# NOTE: if you want "installable" egg, edit the sources and comment out every
#   sys.path.append( ... __file__ ...
# before building
#
import setuptools
setuptools.setup( name = "getsequence", 
        version = "1.0", 
        package_dir = { "" : ".", "sas" : "../sas" }, 
        packages = setuptools.find_packages(".."), 
        py_modules = ["getsequence", "sas"],
        entry_points= {
            'setuptools.installation': [
                'eggsecutable = getsequence:main',
            ] 
        }
    )
