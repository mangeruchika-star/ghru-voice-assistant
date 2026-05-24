import os
import sys
import yaml
from argparse import ArgumentParser

from .render import loaded, render_template


def main():
    parser = ArgumentParser(
        description="A small utility to render template files. Rendering can be performed based on data stored in a YAML configuration file."
    )
    parser.add_argument(
        "templateFile",
        action="store",
        nargs="?",
        help="A template file to be rendered. If you want to render multiple templates at once, use the `--config` option.",
    )
    parser.add_argument(
        "-c",
        "--context",
        action="store",
        dest="contextFile",
        help="YAML file containing template context.",
    )
    parser.add_argument(
        "-C",
        "--config",
        action="store",
        dest="configFiles",
        nargs="*",
        default=[],
        help="YAML configuration files. Should contain YAML documents with a 'template_file', 'output_file', and 'context' key. Multiple documents in a single file are supported and option can be used multiple time sto pass multiple files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        dest="outputFile",
        default="/dev/stdout",
        help="Send rendered output to OUTPUTFILE.",
    )

    parser.add_argument(
        "-x",
        "--overwrite",
        action="store_true",
        dest="overwrite",
        default=False,
        help="Overwrite output files.",
    )
    parser.add_argument(
        "-n",
        "--no-overwrite",
        action="store_false",
        dest="overwrite",
        default=True,
        help="Do not overwrite output files.",
    )
    parser.add_argument(
        "-e",
        "--engine",
        action="store",
        default="jinja",
        help="The template engine to use.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        default=False,
        help="List available engines.",
    )

    args = parser.parse_args()

    if args.list:
        fmt = "{:>10} {:<20}"
        print(fmt.format("engine", "available?"))
        print("=" * 25)
        default_engine = parser.get_default("engine")
        for key in loaded:
            is_default = " (default)" if key == default_engine else ""
            print(fmt.format(key, "yes" if loaded[key] else "no") + is_default)
        sys.exit(0)

    # check that the engine is supported
    if args.engine not in loaded:
        print(
            "'"
            + args.engine
            + "' engine is not recognized. Did you spell it correctly?"
        )
        sys.exit(1)

    # check that the engine loaded
    if not loaded[args.engine]:
        print(
            "'"
            + args.engine
            + "' engine did not load. Make sure that it is installed and available?"
        )
        sys.exit(1)

    # generate configurations for command line arguments
    configs = []
    if args.templateFile:
        configs.append(
            {
                "template_file": args.templateFile,
                "output_file": args.outputFile,
                "source": f"Auto-generated for template file '{args.templateFile}'",
            }
        )
        if args.contextFile:
            if not os.path.isfile(args.contextFile):
                raise IOError("file '" + args.contextFile + "' does not exist")
            with open(args.contextFile) as f:
                ctx = yaml.safe_load(f)
                configs[-1]["context"] = ctx

    # read config files
    for configFile in args.configFiles:
        if os.path.isfile(configFile):
            with open(configFile) as f:
                # each YAML config file may contain multiple documents
                configGenerator = yaml.safe_load_all(f)
                for c in configGenerator:
                    c.update({"source": configFile})
                    configs.append(c)
        else:
            raise IOError("file '" + configFile + "' does not exist")

    for config in configs:
        # get template file
        templateFile = config.get("template_file", None)
        if templateFile is None:
            print(
                f"Error: config in '{config['source']}' does not contain 'template_file' key.",
                file=sys.stderr,
            )
            sys.exit(1)
        # get the context  that will be rendered
        ctx = config.get("context", config.get("data", {}))
        # get output filename
        outputFile = config.get("output_file", None)
        if outputFile is None:
            print(
                f"Error: config in '{config['source']}' does not contain 'output_file' key.",
                file=sys.stderr,
            )
            sys.exit(1)

        # render 10
        try:
            render_template(templateFile, ctx, outputFile, args.engine, args.overwrite)
        except (IOError, FileExistsError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
