#+
# This script is meant to be run from within Blender 2.64, via
# a command line like
#
#     blender -b dummy.blend -P batch_collada_import.py -- infile.dae outfile.blend
#
# where infile.dae is the name of the Collada file to import, and
# outfile.blend is the name to give the output .blend file. Note the
# “--” is mandatory, to allow the script to ignore the part of the
# command line that is processed by Blender.
#
# Alternatively, the input file can be a .zip file, as downloaded from
# the Google/Trimble 3D Warehouse. In this case, the .dae file is
# found within the models subdirectory in the zip archive, which will
# be automatically extracted to a temporary location for importing.
#
# The dummy.blend file must be a valid .blend file, and is initially
# loaded by Blender, but is otherwise ignored; it is only required
# because the -b option has to have an argument.
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import bpy
import sys
import os
import subprocess
import tempfile
import getopt

#+
# Miscellaneous useful stuff
#-

def delete_dir(dir) :
    """deletes dir and all its contents."""
    if os.path.isdir(dir) :
        for parent, dirs, files in os.walk(dir, topdown = False) :
            for item in files :
                os.remove(os.path.join(parent, item))
            #end for
            for item in dirs :
                item = os.path.join(parent, item)
                (os.rmdir, os.remove)[os.path.islink(item)](item)
            #end for
        #end for
        os.rmdir(dir)
    #end if
#end delete_dir

def runcmd(args) :
    """runs a command and checks its return status."""
    status = subprocess.Popen(args = args).wait()
    if status != 0 :
        raise RuntimeError("status %s from cmd %s" % (status, repr(args)))
    #end if
#end runcmd

#+
# Mainline
#-

def parse_command_line() :
    global infile, outfile, rescale
    opts, args = getopt.getopt \
      (
        sys.argv[min(i for i in range(0, len(sys.argv)) if sys.argv[i] == "--") + 1:],
        "",
        ["scale="],
      )
    if len(args) != 2 :
        raise getopt.GetoptError("need exactly 2 args, the input and output filenames")
    #end if
    infile, outfile = args
    rescale = None
    for keyword, value in opts :
        if keyword == "--scale" :
            rescale = float(value)
            if rescale == 0 :
                raise getopt.GetoptError("invalid --scale value")
            #end if
        #end if
    #end for
#end parse_command_line

parse_command_line()
tmpdir = None
if not outfile.endswith(".blend") :
    raise getopt.GetoptError("output filename must end with .blend")
#end if
if infile.endswith(".zip") :
    tmpdir = tempfile.mkdtemp(prefix = "blenddae")
    runcmd(args = ("unzip", infile, "-d", tmpdir))
    modelsdir = os.path.join(tmpdir, "models")
    if not os.path.isdir(modelsdir) :
        raise RuntimeError("no models subdir present in %s" % infile)
    #end if
    use_infile = None
    for item in os.listdir(modelsdir) :
        if item.endswith(".dae") :
            modelfile = os.path.join(modelsdir, item)
            if os.path.isfile(modelfile) :
                if use_infile != None :
                    raise RuntimeError("multiple .dae files present in %s" % infile)
                #end if
                use_infile = modelfile
            #end if
        #end if
        if use_infile == None :
            raise RuntimeError("no models/*.dae file found in in %s" % infile)
        #end if
    #end for
elif infile.endswith(".dae") :
    use_infile = infile
else :
    raise getopt.GetoptError("input filename must end with .dae or .zip")
#end if

if not hasattr(bpy.utils, "collada_import") :
    raise RuntimeError("Your version of Blender does not include the necessary bpy.utils.collada_import routine")
#end if

bpy.ops.wm.read_homefile()
#bpy.ops.wm.collada_import(filepath = use_infile)
  # WON'T WORK: fails with “RuntimeError: Operator bpy.ops.wm.collada_import.poll() failed, context is incorrect” on this line
bpy.utils.collada_import(use_infile)
  # requires my custom Blender patch to add this API routine
if rescale != None :
    # bpy.ops.transform.resize(value = (rescale, rescale, rescale))
        # WON'T WORK: will fail with “RuntimeError: Operator bpy.ops.transform.resize.poll() failed, context is incorrect”
    pass
#end if
for image in bpy.data.images :
    image.pack()
#end for
bpy.ops.wm.save_as_mainfile(filepath = outfile)
if tmpdir != None :
    delete_dir(tmpdir)
#end if
