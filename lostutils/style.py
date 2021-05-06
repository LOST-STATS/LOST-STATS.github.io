import subprocess
from pathlib import Path
from typing import List, Union

import black

from .constants import R_DOCKER_IMAGE


def format_str(
    src_string: str, parameters: str, r_docker_image: str = R_DOCKER_IMAGE
) -> str:
    parameters = parameters.strip().lower()
    if parameters.startswith("py"):
        return "\n".join(
            [
                "```" + parameters,
                black.format_str(src_string, mode=black.Mode()).rstrip(),
                "```",
            ]
        )

    if parameters.startswith("r"):
        # Should do something here
        proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                r_docker_image,
                "Rscript",
                "--vanilla",
                "-e",
                'styler::style_text(readr::read_file(file("stdin")))',
            ],
            input=src_string.encode("utf8"),
            capture_output=True,
        )
        return "\n".join(
            ["```" + parameters, proc.stdout.decode("utf8").rstrip(), "```"]
        )

    return "\n".join(["```" + parameters, src_string, "```"])


def format_file(
    filename: Union[str, Path], r_docker_image: str = R_DOCKER_IMAGE
) -> str:
    filename = Path(filename)
    with open(filename, "rt") as infile:
        is_in_fence = False
        fence_parameters = None
        fenced_lines = []

        final_lines = []

        for line in infile:
            line = line.rstrip()
            if line.startswith("```"):
                if is_in_fence:
                    # End the fence
                    final_lines.append(
                        format_str(
                            "\n".join(fenced_lines),
                            fence_parameters,
                            r_docker_image=r_docker_image,
                        )
                    )
                    is_in_fence = False
                    fenced_lines = []
                    fence_parameters = None

                else:
                    is_in_fence = True
                    fence_parameters = line.strip()[3:]

            elif is_in_fence:
                fenced_lines.append(line)

            else:
                final_lines.append(line.rstrip())

    # Merge lines together and remove extra whitespace
    output = "\n".join(final_lines).rstrip()

    # Make sure the file ends in a newline
    output += "\n"
    return output
