#! /usr/bin/env python3


import os


loaded = dict()

try:
    import _ctemplate

except ImportError:
    loaded["ctemplate"] = False

try:
    import mako.template

    loaded["mako"] = True
except ImportError:
    loaded["mako"] = False

try:
    import jinja2

    loaded["jinja"] = True
except ImportError:
    loaded["jinja"] = False

try:
    import tempita

    loaded["Tempita"] = True
except ImportError:
    loaded["Tempita"] = False







try:
    import pystache

    loaded["mustache"] = True
except ImportError:
    loaded["mustache"] = False


def render_template(templateFile, data, outputFile, engine, overwrite=True):
    """Renders a template from a templateFile with data to an outputFile"""
    # read template file into a string. some engines requires this.
    if not os.path.isfile(templateFile):
        raise IOError("file '" + templateFile + "' does not exist")
    templateText = ""
    with open(templateFile) as f:
        templateText = f.read()

    # make sure we are not going to overwrite template file
    if outputFile == templateFile:
        raise IOError(
            "Output file (%s) would overwrite template file (%s)"
            % (outputFile, templateFile)
        )

    # check if we are going to overwrite existing file
    if outputFile != "/dev/stdout" and not overwrite and os.path.isfile(outputFile):
        raise FileExistsError(
            "output file '"
            + outputFile
            + "' exists, please delete, move, or rerun with --overwrite option"
        )

    # render
    with open(outputFile, "w") as f:
        if engine == "ctemplate":
            f.write(_ctemplate.compile_template(templateText, data))

        if engine == "mako":
            t = mako.template.Template(filename=templateFile)
            f.write(t.render(**data))

        if engine == "jinja":
            t = jinja2.Template(templateText)
            f.write(t.render(**data))

        if engine == "Tempita":
            t = tempita.Template(templateText)
            f.write(t.substitute(**data))
        if engine == "mustache":
            f.write(pystache.render(templateText, data))

