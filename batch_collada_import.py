#+
# This script is meant to be run from within Blender 2.64, via
# a command line like
#
#     blender -b -P batch_collada_import.py -- infile.dae outfile.blend
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
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import bpy
import sys
import os
import subprocess
import shutil
import tempfile
import getopt

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
    subprocess.check_call(args = ("unzip", infile, "-d", tmpdir))
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
    #end for
    if use_infile == None :
        raise RuntimeError("no .dae file found in in %s" % infile)
    #end if
elif infile.endswith(".dae") :
    use_infile = infile
else :
    raise getopt.GetoptError("input filename must end with .dae or .zip")
#end if

bpy.ops.wm.read_homefile()
bpy.ops.wm.collada_import(filepath = use_infile)
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
    shutil.rmtree(tmpdir)
#end if
