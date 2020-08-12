#!/usr/bin/python
# -*- coding: utf-8 -*-

# @file make_release.py
# @author William R. Otte <wotte@dre.vanderbilt.edu>
#
# Packaging script for ACE/TAO

from __future__ import with_statement
from __future__ import print_function
from time import strftime
import re
import subprocess
import shlex
import multiprocessing
import sys

# Python Version Wrappers

if sys.version_info < (3, 0):
    input = raw_input

def binary_str_write (stream, what):
    if isinstance (what, str) and str is not bytes:
        what = what.encode ('ascii')
    stream.write (what)

class ArgParser:
    '''Wrapper for either optparse or argparse
    '''

    use_argparse = sys.version_info >= (3, 2)

    def __init__ (self, optparse_usage_string):
        if self.use_argparse:
            from argparse import ArgumentParser
            self.real_parser = ArgumentParser ()
        else:
            from optparse import OptionParser
            self.real_parser = OptionParser (optparse_usage_string)

    def add_option(self, *args, **kwargs):
        if self.use_argparse:
            self.real_parser.add_argument (*args, **kwargs)
        else:
            self.real_parser.add_option (*args, **kwargs)

    def parse_args (self):
        if self.use_argparse:
            options = self.real_parser.parse_args ()
        else:
            options, arguments = self.real_parser.parse_args ()
            if arguments:
                self.real_parser.error ("Extranous arguments: " + ' '.join(arguments))
        return options

##################################################
#### Global variables
##################################################
""" Options from the command line """
opts=None

""" Absolute path from the git workspace to be used for the
release"""
doc_root=None

""" A dict containing version information used for the release.
This dict contains entries of the form
COMPONENT_version
COMPONENT_micro
COMPONENT_minor
COMPONENT_major
COMPONENT_code """
comp_versions = {}
old_comp_versions = {}

release_date = strftime (# ie: Mon Jan 23 00:35:37 CST 2006
                              "%a %b %d %H:%M:%S %Z %Y")
cpu_count = multiprocessing.cpu_count()

# Packaging configuration

""" This is a regex that detects files that SHOULD NOT have line endings
converted to CRLF when being put into a ZIP file """
bin_regex = re.compile ("\.(mak|mdp|ide|exe|ico|gz|zip|xls|sxd|gif|vcp|vcproj|vcw|sln|dfm|jpg|png|vsd|bz2|pdf|ppt|graffle|pptx|odt|sh)$")

##################################################
#### Utility Methods
##################################################

def parse_args ():
    parser = ArgParser ("usage %prog [options]")

    parser.add_option ("--major", dest="release_type", action="store_const",
                       help="Create a major release.", default=None, const="major")
    parser.add_option ("--minor", dest="release_type", action="store_const",
                       help="Create a minor release.", default=None, const="minor")
    parser.add_option ("--micro", dest="release_type", action="store_const",
                       help="Create a micro release.", default=None, const="micro")

    parser.add_option ("--tag", dest="tag", action="store_true",
                       help="Tag the repositorie with all needed tags", default=False)
    parser.add_option ("--update", dest="update", action="store_true",
                       help="Update the version numbers", default=False)
    parser.add_option ("--push", dest="push", action="store_true",
                       help="Push all changes to remote", default=False)

    parser.add_option ("--kit", dest="action", action="store_const",
                       help="Create kits. DO NOT USE WITH --tag", default=None, const="kit")
    parser.add_option ("--dest", dest="package_dir", action="store",
                       help="Specify destination for the created packages.", default=None)

    parser.add_option ("--root", dest="repo_root", action="store",
                       help="Specify an alternate repository root",
                       default="https://github.com/DOCGroup/ACE_TAO.git")

    parser.add_option ("--mpc_root", dest="mpc_root", action="store",
                       help="Specify an alternate MPC repository root",
                       default="https://github.com/DOCGroup/MPC.git")

    parser.add_option ("-n", dest="take_action", action="store_false",
                       help="Take no action", default=True)
    parser.add_option ("--verbose", dest="verbose", action="store_true",
                       help="Print out actions as they are being performed",
                       default=False)

    options = parser.parse_args ()

    if not options.action and options.release_type is None:
        parser.error ("A release type (--major, --minor, or --micro) must be specified")

    if options.tag:
        if options.update is False:
            print ("Warning: You are tagging a release, but not requesting a version increment")

        if options.push is False:
            print ("Warning: You are tagging a release, but not requesting a push to remote")

    return options


def ex (command):
    from os import system
    global opts
    vprint ("Executing " + command)

    if not opts.take_action:
        print ("Executing " + command)
        return

    status = system(command)
    if status != 0:
        print ("ERROR: Nonzero return value from " + command)
        raise Exception

def ex_failureok (command):
    from os import system
    global opts
    vprint ("Executing " + command)

    if not opts.take_action:
        print ("Executing " + command)
        return

    status = system(command)
    if status != 0:
        print ("WARNING: Nonzero return value from " + command)

###
# Checks that the users environment is sane.
#
def check_environment ():
    from os import getenv

    global doc_root, opts

    doc_root = getenv ("DOC_ROOT")
    if doc_root is None:
        print ("ERROR: Environment DOC_ROOT must be defined.")
        return False

    return True

def vprint (*args, **kwargs):
    """ Prints the supplied message if verbose is enabled"""
    global opts

    if opts.verbose:
        print (*args, **kwargs)

def get_tag (verdict, component):
    return "ACE+TAO-%d_%d_%d" % (
        verdict[component + '_major'], verdict[component + '_minor'], verdict[component + '_micro'])

def get_path (component=None, subpath=''):
  rv = doc_root + '/ACE_TAO/'
  if component is not None:
    rv += component + '/' + subpath
  return rv

##################################################
#### Tagging methods
##################################################
def commit (files):
    """ Commits the supplied list of files to the repository. """
    global comp_versions

    version = get_tag(comp_versions, 'ACE')
    root_path = get_path()
    files = [i[len(root_path):] if i.startswith(root_path) else i for i in files]

    print ("Committing the following files for " + version + ':', " ".join (files))

    if opts.take_action:
        for file in files:
            print ("Adding file " + file + " to commit")
            ex ("cd $DOC_ROOT/ACE_TAO && git add " + file)

        ex ("cd $DOC_ROOT/ACE_TAO && git commit -m\"" + version + "\"")

#        print "Checked in files, resuling in revision ", rev.number

def check_workspace ():
    """ Checks that the DOC and MPC repositories are up to date.  """
    global opts, doc_root
    try:
        ex ("cd $DOC_ROOT/ACE_TAO && git pull -p")
        print ("Successfully updated ACE/TAO working copy")
    except:
        print ("Unable to update ACE/TAO workspace at " + doc_root)
        raise

    try:
        ex ("cd $DOC_ROOT/MPC && git pull -p")
        print ("Successfully updated MPC working copy to revision ")
    except:
        print ("Unable to update the MPC workspace at " + doc_root + "/ACE/MPC")
        raise

    vprint ("Repos root URL = " + opts.repo_root + "\n")
    vprint ("Repos MPC root URL = " + opts.mpc_root + "\n")

def update_version_files (component):
    """ Updates the version files for a given component.  This includes
    Version.h, the PRF, and the VERSION.txt file."""

    global comp_versions, opts, release_date

    vprint ("Updating version files for " + component)

    retval = []

    ## Update component/VERSION.txt
    path = get_path(component, "VERSION.txt")
    with open (path, "r+") as version_file:
        new_version = re.sub (component + " version .*",
                              "%s version %s, released %s" % (component,
                                                              comp_versions[component + "_version"],
                                                              release_date),
                              version_file.read ())
        if opts.take_action:
            version_file.seek (0)
            version_file.truncate (0)
            version_file.write (new_version)
        else:
            print ("New version file for " + component)
            print (new_version)

        vprint ("Updating Version.h for " + component)

    retval.append(path)

    ## Update component/component/Version.h
    version_header = """
// -*- C++ -*-
// This is file was automatically generated by $ACE_ROOT/bin/make_release.py

#define %s_MAJOR_VERSION %s
#define %s_MINOR_VERSION %s
#define %s_MICRO_VERSION %s
#define %s_BETA_VERSION %s
#define %s_VERSION \"%s\"
#define %s_VERSION_CODE %s
#define %s_MAKE_VERSION_CODE(a,b,c) (((a) << 16) + ((b) << 8) + (c))
""" % (component, comp_versions[component + "_major"],
       component, comp_versions[component + "_minor"],
       component, comp_versions[component + "_micro"],
       component, comp_versions[component + "_micro"],
       component, comp_versions[component + "_version"],
       component, comp_versions[component + "_code"],
       component)

    path = get_path(component, component.lower () + "/Version.h")
    if opts.take_action:
        with open (path, 'r+') as version_h:
            version_h.write (version_header)
    else:
        print ("New Version.h for " + component)
        print (version_header)

    retval.append(path)

    # Update component/PROBLEM-REPORT-FORM
    vprint ("Updating PRF for " + component)

    version_string = re.compile ("^\s*(\w+) +VERSION ?:")
    path = get_path(component, "PROBLEM-REPORT-FORM")

    with open (path, 'r+') as prf:
        new_prf = ""
        for line in prf.readlines ():
            match = None
            match = version_string.search (line)
            if match is not None:
                vprint ("Found PRF Version for " + match.group (1))
                line = re.sub ("(\d\.)+\d?",
                               comp_versions[match.group(1) + "_version"],
                               line)

            new_prf += line

        if opts.take_action:
            prf.seek (0)
            prf.truncate (0)
            prf.writelines (new_prf)
        else:
            print ("New PRF for " + component)
            print ("".join (new_prf))

    retval.append(path)

    return retval


def update_spec_file ():
    path = get_path('ACE', "rpmbuild/ace-tao.spec")
    with open (path, 'r+') as spec_file:
        new_spec = ""
        for line in spec_file.readlines ():
            if line.find ("define ACEVER ") is not -1:
                line = "%define ACEVER  " + comp_versions["ACE_version"] + "\n"
            if line.find ("define TAOVER ") is not -1:
                line = "%define TAOVER  " + comp_versions["TAO_version"] + "\n"
            if line.find ("define is_major_ver") is not -1:
                if opts.release_type == "micro":
                    line = "%define is_major_ver 0\n"
                else:
                    line = "%define is_major_ver 1\n"

            new_spec += line

        if opts.take_action:
            spec_file.seek (0)
            spec_file.truncate (0)
            spec_file.writelines (new_spec)
        else:
            print ("New spec file:")
            print ("".join (new_spec))

    return [path]

def update_debianbuild ():
    """ Updates ACE_ROOT/debian directory.
    - renames all files with version numbers in name; if file contains
      lintian overrides, update version numbers inside file
    - updates version numbers inside file debian/control
    Currently ONLY ACE is handled here """

    global comp_versions

    from os import listdir

    prev_ace_ver = None

    path = get_path('ACE', 'debian/control')

    mask = re.compile ("(libace|libACE|libkokyu|libKokyu|libnetsvcs)([^\s,:]*-)(\d+\.\d+\.\d+)([^\s,:]*)")

    def update_ver (match):
        return match.group (1) + match.group (2) + comp_versions["ACE_version"] + match.group (4)

    # update debian/control
    with open (path, 'r+') as control_file:
        new_ctrl = ""
        for line in control_file.readlines ():
            if re.search ("^(Package|Depends|Suggests):", line) is not None:
                line = mask.sub (update_ver, line)
            elif re.search ('^Replaces:', line) is not None:
                line = line.replace (old_comp_versions["ACE_version"], comp_versions["ACE_version"])

            new_ctrl += line

        if opts.take_action:
            control_file.seek (0)
            control_file.truncate (0)
            control_file.writelines (new_ctrl)
        else:
            print ("New control file:")
            print ("".join (new_ctrl))

    return [path]

def get_and_update_versions ():
    """ Gets current version information for each component,
    updates the version files, creates changelog entries,
    and commit the changes into the repository."""
    global comp_versions, opts

    try:
        get_comp_versions ("ACE")
        get_comp_versions ("TAO")

        if opts.update:
            files = []
            files += update_version_files ("ACE")
            files += update_version_files ("TAO")
            if opts.tag:
              files += create_changelog ("ACE")
              files += create_changelog ("TAO")
            files += update_spec_file ()
            files += update_debianbuild ()

            commit (files)

    except:
        print ("Fatal error in get_and_update_versions.")
        raise

def create_changelog (component):
    """ Creates a changelog entry for the supplied component that includes
    the version number being released"""
    vprint ("Creating ChangeLog entry for " + component)

    global old_comp_versions, comp_versions, opts

    old_tag = get_tag (old_comp_versions, 'ACE')

    # Generate changelogs per component
    path = get_path(component, "ChangeLogs/" + component + "-" + comp_versions[component + "_version_"])
    ex ("cd $DOC_ROOT/ACE_TAO && git log " + old_tag + "..HEAD " + component + " > " + path)

    return [path]

def get_comp_versions (component):
    """ Extracts the current version number from the VERSION.txt
    file and increments it appropriately for the release type
    requested."""
    vprint ("Detecting current version for " + component)

    regex = re.compile ("version (\d+)(?:\.(\d+)(?:\.(\d+))?)?")
    major = component + "_major"
    minor = component + "_minor"
    micro = component + "_micro"


    version = (None, None, None)
    with open (doc_root + "/ACE_TAO/" + component + "/VERSION.txt") as version_file:
        for line in version_file:
            match = regex.search (line)
            if match is not None:
                version = match.groups(default=0)

                vprint ("Detected version %s.%s.%s" % version)

                comp_versions[major] = int (version[0])
                comp_versions[minor] = int (version[1])
                comp_versions[micro] = int (version[2])

                break

            print ("FATAL ERROR: Unable to locate current version for " + component)
            raise Exception

    # Also store the current release (old from now)
    old_comp_versions[major] = comp_versions[major]
    old_comp_versions[minor] = comp_versions[minor]
    old_comp_versions[micro] = comp_versions[micro]

    if opts.update:
        if opts.release_type == "major":
            comp_versions[major] += 1
            comp_versions[minor] = 0
            comp_versions[micro] = 0
        elif opts.release_type == "minor":
            comp_versions[minor] += 1
            comp_versions[micro] = 0
        elif opts.release_type == "micro":
            comp_versions[micro] += 1

    #if opts.release_type == "micro":
    comp_versions [component + "_version"] = \
        str (comp_versions[major])  + '.' + \
        str (comp_versions[minor])  + '.' + \
        str (comp_versions[micro])
    comp_versions [component + "_version_"] = \
        str (comp_versions[major])  + '_' + \
        str (comp_versions[minor])  + '_' + \
        str (comp_versions[micro])

    comp_versions [component + "_code"] = \
        str((comp_versions[major] << 16) + \
            (comp_versions[minor] << 8) + \
            comp_versions[micro])

    old_comp_versions[component + "_version"] = \
        str (old_comp_versions[major])  + '.' + \
        str (old_comp_versions[minor])  + '.' + \
        str (old_comp_versions[micro])
    old_comp_versions[component + "_version_"] = \
        str (old_comp_versions[major])  + '_' + \
        str (old_comp_versions[minor])  + '_' + \
        str (old_comp_versions[micro])

    if opts.update:
      vprint ("Updating from version %s to version %s" %
                  (old_comp_versions [component + "_version"], comp_versions [component + "_version"]))
    else:
      vprint ("Found version %s" %
                  (comp_versions [component + "_version"]))

    # else:
    #     comp_versions [component + "_version"] = \
    #                   str (comp_versions[major])  + '.' + \
    #                   str (comp_versions[minor])


def update_latest_tag (product, which, branch):
    """ Update one of the Latest_* tags externals to point the new release """
    global opts
    tagname = "Latest_" + which

    # Remove tag locally
    vprint ("Removing tag %s" % (tagname))
    ex_failureok ("cd $DOC_ROOT/" + product + " && git tag -d " + tagname)

    vprint ("Placing tag %s" % (tagname))
    ex ("cd $DOC_ROOT/" + product + " && git tag -a " + tagname + " -m\"" + tagname + "\"")


def push_latest_tag (product, which, branch):
    """ Update one of the Latest_* tags externals to point the new release """
    global opts
    tagname = "Latest_" + which

    if opts.push:
        # Remove tag in the remote origin
        ex_failureok ("cd $DOC_ROOT/" + product + " && git push origin :refs/tags/" + tagname)

        vprint ("Pushing tag %s" % (tagname))
        ex ("cd $DOC_ROOT/" + product + " && git push origin " + tagname)

def tag ():
    """ Tags the DOC and MPC repositories for the version and push that remote """
    global comp_versions, opts

    tagname = get_tag(comp_versions, 'ACE')

    if opts.tag:
        if opts.take_action:
            vprint ("Placing tag %s on ACE_TAO" % (tagname))
            ex ("cd $DOC_ROOT/ACE_TAO && git tag -a " + tagname + " -m\"" + tagname + "\"")

            vprint ("Placing tag %s on MPC" % (tagname))
            ex ("cd $DOC_ROOT/MPC && git tag -a " + tagname + " -m\"" + tagname + "\"")

            # Update latest tag
            if opts.release_type == "major":
                update_latest_tag ("ACE_TAO", "Major", tagname)
                update_latest_tag ("ACE_TAO", "Minor", tagname)
                update_latest_tag ("ACE_TAO", "Beta", tagname)
                update_latest_tag ("ACE_TAO", "Micro", tagname)
                update_latest_tag ("MPC", "ACETAO_Major", tagname)
                update_latest_tag ("MPC", "ACETAO_Minor", tagname)
                update_latest_tag ("MPC", "ACETAO_Micro", tagname)
            elif opts.release_type == "minor":
                update_latest_tag ("ACE_TAO", "Minor", tagname)
                update_latest_tag ("ACE_TAO", "Beta", tagname)
                update_latest_tag ("ACE_TAO", "Micro", tagname)
                update_latest_tag ("MPC", "ACETAO_Minor", tagname)
                update_latest_tag ("MPC", "ACETAO_Micro", tagname)
            elif opts.release_type == "micro":
                update_latest_tag ("ACE_TAO", "Beta", tagname)
                update_latest_tag ("ACE_TAO", "Micro", tagname)
                update_latest_tag ("MPC", "ACETAO_Micro", tagname)
        else:
            vprint ("Placing tag %s on ACE_TAO" % (tagname))
            vprint ("Placing tag %s on MPC" % (tagname))
            print ("Creating tags:\n")
            print ("Placing tag " + tagname + "\n")

def push ():
    """ Tags the DOC and MPC repositories for the version and push that remote """
    global comp_versions, opts

    tagname = "ACE+TAO-%d_%d_%d" % (comp_versions["ACE_major"],
                                    comp_versions["ACE_minor"],
                                    comp_versions["ACE_micro"])

    if opts.push:
        if opts.take_action:
            vprint ("Pushing ACE_TAO master to origin")
            ex ("cd $DOC_ROOT/ACE_TAO && git push origin master")

            vprint ("Pushing tag %s on ACE_TAO" % (tagname))
            ex ("cd $DOC_ROOT/ACE_TAO && git push origin tag " + tagname)

            vprint ("Pushing tag %s on MPC" % (tagname))
            ex ("cd $DOC_ROOT/MPC && git push origin tag " + tagname)

            # Update latest tag
            if opts.release_type == "major":
                push_latest_tag ("ACE_TAO", "Major", tagname)
                push_latest_tag ("ACE_TAO", "Minor", tagname)
                push_latest_tag ("ACE_TAO", "Beta", tagname)
                push_latest_tag ("ACE_TAO", "Micro", tagname)
                push_latest_tag ("MPC", "ACETAO_Major", tagname)
                push_latest_tag ("MPC", "ACETAO_Minor", tagname)
                push_latest_tag ("MPC", "ACETAO_Micro", tagname)
            elif opts.release_type == "minor":
                push_latest_tag ("ACE_TAO", "Minor", tagname)
                push_latest_tag ("ACE_TAO", "Beta", tagname)
                push_latest_tag ("ACE_TAO", "Micro", tagname)
                push_latest_tag ("MPC", "ACETAO_Minor", tagname)
                push_latest_tag ("MPC", "ACETAO_Micro", tagname)
            elif opts.release_type == "micro":
                push_latest_tag ("ACE_TAO", "Beta", tagname)
                push_latest_tag ("ACE_TAO", "Micro", tagname)
                push_latest_tag ("MPC", "ACETAO_Micro", tagname)
        else:
            vprint ("Pushing tag %s on ACE_TAO" % (tagname))
            vprint ("Pushing tag %s on MPC" % (tagname))
            print ("Pushing tags:\n")
            print ("Pushing tag " + tagname + "\n")

##################################################
#### Packaging methods
##################################################
def export_wc (stage_dir):

    global doc_root, comp_versions

    tag = "ACE+TAO-%d_%d_%d" % (comp_versions["ACE_major"],
                                comp_versions["ACE_minor"],
                                comp_versions["ACE_micro"])

    # Clone the ACE repository with the needed tag
    print ("Retrieving ACE with tag " + tag)
    ex ("git clone --depth 1 --branch " + tag + " " + opts.repo_root + " " + stage_dir + "/ACE_TAO")

    # Clone the MPC repository with the needed tag
    print ("Retrieving MPC with tag " + tag)
    ex ("git clone --depth 1 --branch " + tag + " " + opts.mpc_root + " " + stage_dir + "/MPC")

    # Setting up stage_dir
    print ("Moving ACE")
    ex ("mv " + stage_dir + "/ACE_TAO/ACE " + stage_dir + "/ACE_wrappers")
    print ("Moving TAO")
    ex ("mv " + stage_dir + "/ACE_TAO/TAO " + stage_dir + "/ACE_wrappers/TAO")
    print ("Moving MPC")
    ex ("mv " + stage_dir + "/MPC " + stage_dir + "/ACE_wrappers/MPC")

def update_packages (text_files, bin_files, stage_dir, package_dir):
    import os

    print ("Updating packages....")
    os.chdir (stage_dir)

    # -g appends, -q for quiet operation
    zip_base_args = " -gqu "
    # -l causes line ending conversion for windows
    zip_text_args = " -l "
    zip_file = stage_dir + "/zip-archive.zip"

    # -r appends, -f specifies file.
    tar_args = "-uf "
    tar_file = stage_dir + "/tar-archive.tar"

    # Zip binary files
    print ("\tAdding binary files to zip....")
    p = subprocess.Popen (
        shlex.split ("xargs zip " + zip_base_args + zip_file),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    instream, outstream = (p.stdin, p.stdout)

    binary_str_write (instream, bin_files)

    instream.close ()
    outstream.close ()

    # Need to wait for zip process spawned by popen2 to complete
    # before proceeding.
    os.wait ()

    print ("\tAdding text files to zip.....")
    p = subprocess.Popen (
        shlex.split ("xargs zip " + zip_base_args + zip_text_args + zip_file),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    instream, outstream = (p.stdin, p.stdout)

    binary_str_write (instream, text_files)

    instream.close ()
    outstream.close ()

    # Need to wait for zip process spawned by popen2 to complete
    # before proceeding.
    os.wait ()

    # Tar files
    print ("\tAdding to tar file....")
    if not os.path.exists (tar_file):
        open(tar_file, 'w').close ()

    p = subprocess.Popen (
        shlex.split ("xargs tar " + tar_args + tar_file),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    instream, outstream = (p.stdin, p.stdout)
    binary_str_write (instream, ' ' + bin_files + ' ' + text_files)

    instream.close ()

    print (outstream.read ())
    outstream.close ()

    os.wait ()

def move_packages (name, stage_dir, package_dir):
    """ Copies the temporary files from the stage_dir to the package_dir.
        Renames them to name.tar and name.zip, respectively, and compresses
        the tarfile with gzip and bzip2. """
    import shutil, os
    from os.path import join

    print ("Storing packages for ", name)

    # Take care of the zip file
    print ("\tZip file...")
    target_file = join (package_dir, name + ".zip")
    shutil.copy (join (stage_dir, "zip-archive.zip"), target_file)
    ex ("md5sum " + target_file + " > " + target_file + ".md5")


    tar_file = join (stage_dir, "tar-archive.tar")
    target_file = join (package_dir, name + ".tar")

    # bzip
    print ("\tBzip2 file.....")
    shutil.copy (tar_file, target_file)
    ex ("bzip2 " + target_file)
    ex ("md5sum " + target_file + ".bz2 > " + target_file + ".bz2.md5")

    print ("\tgzip file.....")
    shutil.copy (tar_file, target_file)
    ex ("gzip " + target_file)
    ex ("md5sum " + target_file + ".gz > " + target_file + ".gz.md5")

def create_file_lists (base_dir, prefix, exclude):
    """ Creates two lists of files:  files that need CR->CRLF
    conversions (useful for zip files) and those that don't,
    excluding filies/directories found in exclude. """
    import os

    text_files = list ()
    bin_files = list ()

    for root, dirs, files in os.walk (base_dir, topdown=True):
#        print "root", root

        relroot = root.replace (base_dir, "")

#        print "relroot", relroot

        if len(relroot) and relroot[0] == '/':
            relroot = relroot [1:]

        excluded = False
        for item in exclude:
            dir_item = item + '/'
            if relroot.startswith (dir_item) or relroot.startswith (item):
#                print "excluding", relroot
                excluded = True
#            else:
#                print relroot, "does not start with", dir_item, "or", item

        if excluded:
            continue

        # Remove dirs that are listed in our exclude pattern
        for item in dirs:
#            print "item", item
            # Remove our excludes
            if (item) in exclude:
#                print "Removing " + item + " from consideration...."
                dirs.remove (item)

        # Remove files that are listed in our exclude pattern
        for item in files:
            fullitem = os.path.join (relroot, item)
            if fullitem in exclude or item in exclude:
#                print "Removing " + fullitem + " from consideration...."
                continue
            else:
                if bin_regex.search (fullitem) is not None:
                    bin_files.append ('"' + os.path.join (prefix, fullitem) + '"')
                else:
                    text_files.append ('"' + os.path.join (prefix, fullitem) + '"')

    return (text_files, bin_files)

def write_file_lists (comp, text, bin):
    with open (comp + ".files", 'w') as outfile:
        outfile.write ("\n".join (text))
        outfile.write (".............\nbin files\n.............\n")
        outfile.write ("\n".join (bin))

def package (stage_dir, package_dir, decorator):
    """ Packages ACE, ACE+TAO releases of current
        staged tree, with decorator appended to the name of the archive. """
    from os.path import join
    from os import remove
    from os import chdir

    chdir (stage_dir)

    text_files = list ()
    bin_files = list ()

    # Erase our old temp files
    try:
#        print "removing files", join (stage_dir, "zip-archive.zip"), join (stage_dir, "tar-archive.tar")
        remove (join (stage_dir, "zip-archive.zip"))
        remove (join (stage_dir, "tar-archive.tar"))
    except:
        print ("error removing files", join (stage_dir, "zip-archive.zip"), join (stage_dir, "tar-archive.tar"))
        pass # swallow any errors

    text_files, bin_files = create_file_lists (join (stage_dir, "ACE_wrappers"),
                                               "ACE_wrappers", ["TAO", ".gitignore", ".git"])

#    write_file_lists ("fACE" + decorator, text_files, bin_files)
    update_packages ("\n".join (text_files),
                     "\n".join (bin_files),
                     stage_dir,
                     package_dir)

    move_packages ("ACE" + decorator, stage_dir, package_dir)

    text_files = list ()
    bin_files = list ()

    # for TAO:
    text_files, bin_files = create_file_lists (join (stage_dir, "ACE_wrappers/TAO"),
                                                     "ACE_wrappers/TAO", [".gitignore", ".git"])

#    write_file_lists ("fTAO" + decorator, text_files, bin_files)
    update_packages ("\n".join (text_files),
                     "\n".join (bin_files),
                     stage_dir,
                     package_dir)

    move_packages ("ACE+TAO" + decorator, stage_dir, package_dir)

def generate_workspaces (stage_dir):
    """ Generates workspaces in the given stage_dir """
    print ("Generating workspaces...")
    global opts
    import os

    # Make sure we are in the right directory...
    os.chdir (os.path.join (stage_dir, "ACE_wrappers"))

    # Set up our environment
    os.putenv ("ACE_ROOT", os.path.join (stage_dir, "ACE_wrappers"))
    os.putenv ("MPC_ROOT", os.path.join (stage_dir, "ACE_wrappers", "MPC"))
    os.putenv ("TAO_ROOT", os.path.join (stage_dir, "ACE_wrappers", "TAO"))
    os.putenv ("CIAO_ROOT", "")
    os.putenv ("DANCE_ROOT", "")
    os.putenv ("DDS_ROOT", "")

    # Create option strings
    mpc_command = os.path.join (stage_dir, "ACE_wrappers", "bin", "mwc.pl")
    exclude_option = ' -exclude TAO/TAO_*.mwc '
    workers_option = ' -workers ' + str(cpu_count)
    mpc_option = ' -recurse -hierarchy -relative ACE_ROOT=' + stage_dir + '/ACE_wrappers '
    mpc_option += ' -relative TAO_ROOT=' + stage_dir + '/ACE_wrappers/TAO '
    msvc_exclude_option = ' '
    vs2017_option = ' -name_modifier *_vs2017 '
    vs2019_option = ' -name_modifier *_vs2019 '

    redirect_option = str ()
    if not opts.verbose:
        redirect_option = " >> ../mpc.log 2>&1"

    print ("\tGenerating GNUmakefiles....")
    ex (mpc_command + " -type gnuace " + \
        exclude_option + workers_option + mpc_option + redirect_option)

    print ("\tGenerating VS2017 solutions...")
    ex (mpc_command + " -type vs2017 "  + \
        msvc_exclude_option + mpc_option + workers_option + vs2017_option + redirect_option)

    print ("\tGenerating VS2019 solutions...")
    ex (mpc_command + " -type vs2019 " + \
        msvc_exclude_option + mpc_option + workers_option + vs2019_option + redirect_option)

    print ("\tCorrecting permissions for all generated files...")
    regex = [
        '*.vc[p,w]',
        '*.bmak',
        '*.vcproj',
        '*.sln',
        '*.vcxproj',
        '*.filters',
        'GNUmake*',
    ]
    ex ("find ./ " + ' -or '.join(["-name '%s'" % (i,) for i in regex]) + " | xargs chmod 0644")

def create_kit ():
    """ Creates kits """
    import os
    from os.path import join
    # Get version numbers for this working copy, note this will
    # not update the numbers.
    print ("Getting current version information....")

    get_comp_versions ("ACE")
    get_comp_versions ("TAO")

    print ("Creating working directories....")
    stage_dir, package_dir = make_working_directories ()

    print ("Exporting working copy...")
    export_wc (stage_dir)

    ### make source only packages
    package (stage_dir, package_dir, "-src")

    generate_workspaces (stage_dir)

    ### create standard packages.
    package (stage_dir, package_dir, "")

def make_working_directories ():
    """ Creates directories that we will be working in.
    In particular, we will have DOC_ROOT/stage-PID and
    DOC_ROOT/packages-PID """
    global doc_root
    import os.path, os

    stage_dir = os.path.join (doc_root, "stage-" + str (os.getpid ()))
    package_dir = os.path.join (doc_root, "package-" + str (os.getpid ()))

    os.mkdir (stage_dir)
    os.mkdir (package_dir)

    return (stage_dir, package_dir)

def main ():
    global opts

    if opts.action == "kit":
        print ("Creating a kit.")
        input ("Press enter to continue")

        create_kit ()

    else:
        print ("Making a " + opts.release_type + " release.")
        input ("Press enter to continue")

        get_and_update_versions ()
        tag ()
        push ()

if __name__ == "__main__":
    opts = parse_args ()

    if check_environment() is not True:
        exit (1)

    main ()
