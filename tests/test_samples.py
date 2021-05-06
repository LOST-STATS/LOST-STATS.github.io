import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from urllib import parse

import mistune

from lostutils.constants import PYTHON_DOCKER_IMAGE, R_DOCKER_IMAGE


@dataclass(frozen=True)
class CodeBlock:
    """
    A code block that is found amongst the markdown

    Args:
        language: The language indicated by the code block
        code: The actual content of the code block
        location: Which file did we find the code block in?
    """

    language: str
    code: str
    options: Dict[str, str]
    location: Path

    def __repr__(self) -> str:
        """Modify the repr so that only the first several characters of code are printed"""
        if len(self.code) > 50:
            code = f"{self.code[:47]}..."
        else:
            code = self.code
        return f'CodeBlock(language="{self.language}", code="{code}", location={self.location})'


@dataclass(frozen=True)
class Outcome:
    """
    The outcome of running a particular code block

    Args:
        block: The CodeBlock object we ran the test on
        stdout: The standard out of the test
        returncode: The return code from running the test
    """

    block: CodeBlock
    stdout: str
    returncode: int


def get_top_level_block_codes(mark: str, location: Path) -> List[CodeBlock]:
    """
    Search for code blocks in the markdown `mark`.

    Some notes on processing:
        * Code blocks are denoted by top-level blocks marked out with ```
        * The language is specified as ```language_name on the first fence
        * If a code block is separated by text, you can join them by giving them
          the same name, specifically like ```python?example=name

    Args:
        mark: The markdown string we'll search for.
        location: The path to the file we are reading

    Returns:
        The list of code blocks. May not be in the order they are found in the file
    """
    markdown = mistune.create_markdown(renderer=mistune.AstRenderer())
    ast = markdown(mark)

    named_blocks = defaultdict(list)
    unnamed_blocks = []
    for elt in ast:
        if elt.get("type") == "block_code":
            # N.B. mistune 2.0.0a5 creates an `info` key with value None if the
            #      info parameter doesn't exist. Thus we can't use `.get()` directly
            language = elt.get("info") or ""
            language = language.lower()

            language, _, options = language.partition("?")
            if options:
                doptions = parse.parse_qs(options)
                name = doptions.get("example", [""])[0]
            else:
                doptions = {}
                name = ""

            block = CodeBlock(
                code=elt.get("text"),
                language=language,
                options=doptions,
                location=location,
            )
            if name:
                named_blocks[name].append(block)
            else:
                unnamed_blocks.append(block)

    for block_of_blocks in named_blocks.values():
        unnamed_blocks.append(
            CodeBlock(
                code="\n\n".join(block.code for block in block_of_blocks),
                language=block_of_blocks[0].language,
                location=location,
                options=block_of_blocks[0].options,
            )
        )

    return unnamed_blocks


def _expand_paths(paths: List[Path]) -> List[Path]:
    all_paths: List[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            all_paths.append(path)
        elif path.is_dir():
            all_paths.extend(path.glob("**/*.md"))

    return all_paths


def pytest_generate_tests(metafunc):
    base_paths = list(map(Path, metafunc.config.getoption("mdpath")))
    base_paths = base_paths or [Path(__file__).parent.parent]

    base_exclude_paths = list(map(Path, metafunc.config.getoption("xmdpath")))

    languages = [
        language.strip().lower() for language in metafunc.config.getoption("language")
    ]

    # Expand and exclude paths on command line
    all_paths = _expand_paths(base_paths)
    exclude_paths = _expand_paths(base_exclude_paths)
    all_paths = sorted(set(all_paths) - set(exclude_paths))

    # Retrieve the blocks from the code
    all_blocks: List[CodeBlock] = []
    for filename in all_paths:
        with open(filename, "rt") as infile:
            text = infile.read()
        blocks = get_top_level_block_codes(text, filename)
        all_blocks.extend(blocks)

    # Skip the blocks labeled `skip`
    # TODO(khw): Is there some way to explicitly call out the `skip` in pytest output?
    run_blocks = [
        block
        for block in all_blocks
        if block.options.get("skip", ["false"])[0].lower() != "true"
    ]

    if "python_code_block" in metafunc.fixturenames:
        if (not languages) or ("python" in languages):
            metafunc.parametrize(
                "python_code_block",
                [block for block in run_blocks if block.language.startswith("py")],
            )
        else:
            metafunc.parametrize(
                "python_code_block",
                [CodeBlock(language="python", code="1 + 1", options={}, location="")],
            )

    if "r_code_block" in metafunc.fixturenames:
        if (not languages) or ("r" in languages):
            metafunc.parametrize(
                "r_code_block", [block for block in run_blocks if block.language == "r"]
            )
        else:
            metafunc.parametrize(
                "r_code_block",
                [CodeBlock(language="r", code="1 + 1", options={}, location="")],
            )


def run_docker_python(block: CodeBlock) -> Outcome:
    process = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            PYTHON_DOCKER_IMAGE,
            "python",
            "-c",
            block.code,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return Outcome(block=block, stdout=process.stdout, returncode=process.returncode)


def run_docker_r(block: CodeBlock) -> Outcome:
    process = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            R_DOCKER_IMAGE,
            "R",
            "-e",
            block.code,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return Outcome(block=block, stdout=process.stdout, returncode=process.returncode)


def test_python_code_block(python_code_block: CodeBlock):
    outcome = run_docker_python(python_code_block)
    assert outcome.returncode == 0, str(python_code_block)


def test_r_code_block(r_code_block: CodeBlock):
    outcome = run_docker_r(r_code_block)
    assert outcome.returncode == 0, str(r_code_block)
