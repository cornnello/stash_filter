#!/usr/bin/env python3
from pathlib import Path
from typing import Optional, List
from subprocess import Popen, PIPE
import logging
import os
import re
import click


logger = logging.getLogger(__name__)


def get_stash_files(
    remote_url: str,
    password: Optional[str] = None,
    excluded_regions: Optional[List[str]] = None,
):
    """User rclone ls to get the available versions for each title"""
    if password is not None:
        os.putenv("RCLONE_CONFIG_PASS", password)

    if excluded_regions is None:
        excluded_regions = [
            "JP",
            "KR",
            "GB",
            "DE",
            "HK",
            "RU",
            "CN",
            "DE",
            "PL",
            "AU", 
            "FR",
        ]  # default regions to exclude

    logger.info("Fetching remote filelist")
    # ls_content = os.popen(f'rclone ls "{remote_url}"', ).read()

    # force encoding to fix errors on windows
    with Popen(['rclone', 'ls', remote_url], stdout=PIPE) as proc:
        output, _ = proc.communicate()  # read from stdout
    ls_content = output.decode('utf-8')

    logger.info("Processing filelist")
    # filter lines
    lines = [line for line in ls_content.split("\n") if len(line.strip()) > 0]

    # parse the filenames and get the files, titleid, regions and
    file_vers = [
        {
            "filename": re.sub(r"^\s*[0-9]+ (.*)$", r"\1", line),
            "folder": str(
                Path(re.sub(r"^\s*[0-9]+ (.*)$", r"\1", line)).parent
            ),  # get the base folder
            "formatted": (
                # check to see that the file at least has a properly formatted ver and titleid
                (re.match(r"^.*\[v([0-9]+)\].*$", line) is not None)
                and (re.match(r"^.*\[([a-zA-Z0-9]{16})\].*$", line) is not None)
            ),
            "version": re.sub(r"^.*\[v([0-9]+)\].*$", r"\1", line),
            "titleid": re.sub(
                r"^.*\[((01|05)[A-Fa-f0-9]{14})\].*$", r"\1", line
            ).lower(),  # for consistency with tinfoil
            "region": re.sub(r"^.*\[([A-Z]{2})\].*$", r"\1", line)
            if re.match(r"^.*\[([A-Z]{2})\].*$", line) is not None
            else "",
        }
        for line in lines
    ]
    rest_files = set(
        x["filename"] for x in file_vers if not x["formatted"]
    )  # keep improperly formatted files regardless
    file_vers = [
        x for x in file_vers if x["formatted"]
    ]  # only use the rest for trimming

    # group by titleid, region and folder
    versions = {}
    for title in file_vers:
        cur_value = versions.get(
            (title["titleid"], title["region"], title["folder"]), []
        )  # get current_list of vals
        cur_value += [(title["version"], title["filename"])]
        versions[(title["titleid"], title["region"], title["folder"])] = cur_value
    versions = {
        k: sorted(vers, key=lambda x: int(x[0]), reverse=True)
        for k, vers in versions.items()
    }

    # select all the file s to keep (from those that have a version id)
    kept_files = set()  # list of all files to copy
    for (titleid, region, folder), ver_list in versions.items():
        if region not in excluded_regions:
            # only keep the highest version of everything
            kept_files.add(ver_list[0][1])  # add the latest version

    # unset the password
    if password is not None:
        os.unsetenv("RCLONE_CONFIG_PASS")

    return kept_files | rest_files


def output_files(dest_file: str, all_files: List[str], is_filter: bool):
    """Output to the filelist to the destination"""
    all_files = list(all_files)
    if is_filter:
        all_files = [re.sub(r"(\[|\]|\{|\}|\*|\?)", r"\\\1", f)for f in all_files]  # escape special chars
        filter_list = ["+ " + f for f in all_files] + ["- **"]  # add file + "- **""
    else:
        filter_list = all_files  # just the file names

    # get the filter portion
    filter_text = "\n".join(
        ["# START STASH FILTER"] + filter_list + ["# END STASH FILTER"]
    )

    existing_text = ""
    if dest_file != "-" and Path(dest_file).exists():
        click.echo(f"Destination file {dest_file} already exists. Overwritting...")
        with open(dest_file, "r", encoding="utf-8") as f:
            existing_text = f.read()  # get the current content

    # replace the filter block with the new one, or append
    re_pattrn = r"(.*)# START STASH FILTER\n.*# END STASH FILTER(.*)"
    if re.match(re_pattrn, existing_text, flags=re.DOTALL) is not None:
        filter_text = re.sub(
            re_pattrn, rf"\1{filter_text}\2", existing_text, flags=re.DOTALL
        )
    else:
        filter_text = existing_text + "\n" + filter_text  # append it

    # write to file or stdout
    if dest_file == "-":
        print(filter_text)
    # or file
    else:
        with open(dest_file, "w", encoding="utf-8") as f:
            f.write(filter_text)


@click.command(
    name="stash_filter",
    short_help="generates a filter file for the stash",
    help="""
    Takes the remote at SRC and generates a filtered rules file to use with rclone 
    at DEST_FILE (can be - for stdout). SRC should be rclone URL such as `stash:dir` or simply `stash`.
    All files that have the usual format `[titleid]*[region]?*[version]` are filtered
    so that if the same titleid occurs multiple time in a folder, only the most
    recent version is used. All the othe files are kept.

    The generated portion of the output file is padded by comments.

        \b
        ...untouched
        # START STASH FILTER
        ...
        actual rules
        ...
        # END STASH FILTE
        ..untouched

    If the file already exists, only that portion is overwritten so you can
    safely prepend and append rules. 
    """,
)
@click.option(
    "pass_prompt",
    "-p",
    "--password",
    is_flag=True,
    default=False,
    help="Whether to prompt for rclone password (default: get from RCLONE_CONFIG_PASS)",
)
@click.option(
    "is_filter",
    "-f",
    "--filter",
    is_flag=True,
    default=False,
    help="Create a filter file (default: creates a normal file list)",
)
@click.option(
    "exclude",
    "-e",
    "--exclude",
    multiple=True,
    type=click.STRING,
    default=None,
    metavar="REGION",
    help="Exclude REGION from files (defaults to all but US). Can be repeated to add multiple regions.",
)
@click.argument("src", metavar="SRC", required=True)
@click.argument(
    "dest_file",
    metavar="DEST_FILE",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, writable=True, allow_dash=True),
)
def stash_filter(
    pass_prompt: bool, src: str, is_filter: bool, dest_file: str, exclude: List[str]
):
    if len(exclude) == 0:
        exclude = None  # default
    password = os.environ.get("RCLONE_CONFIG_PASS", None)
    if pass_prompt:
        # prompt if option selected
        password = click.prompt("Rclone password", hide_input=True)

    # get the files
    if dest_file != "-":
        click.echo("Filtering files")  # do not output info when outputting to stdout
    files = get_stash_files(src, password=password, excluded_regions=exclude)

    # output them
    if dest_file != "-":
        click.echo("Outputting files")
    output_files(dest_file, files, is_filter=is_filter)

    if dest_file != "-":
        click.echo('Done!')


if __name__ == "__main__":
    stash_filter()  # run the command