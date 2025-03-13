---
title: Create a Conda Package (Python)
parent: Other
has_children: false
nav_order: 1
---

# Create a Conda Package (Python)

*Warning* This is a page aimed at git experts at the moment. We welcome suggestions for pushing its difficulty down.

Sometimes there are packages that are available in the Python ecosystem generally but which have not yet been incorporated into the [conda-forge](https://conda-forge.org/) package repository for Anaconda. This page shows you the correct way to install that package into your environment in the interim and how to get that package added to the conda-forge repository.

## Installing the package locally

First, create a temporary directory where we'll do all of our work. In the following snippet we call that directory `TMP_DIR`.

Second, identify the package you'd like to install that is currently available via `pip`. In what follows, we'll use `linearmodels` as an example.

```bash
PACKAGE=linearmodels
TMP_DIR="~/tmp/{PACKAGE}_build"

# Create the temporary directory
mkdir -p $TMP_DIR && cd $TMP_DIR

# Conda boilerplate
conda skeleton pypi $PACKAGE
conda build -c conda-forge $PACKAGE

# Install the package
conda install --use-local -c conda-forge linearmodels
```


## Setting up an Anaconda feedstock for your package

The above solves the problem for you locally, but not for the broader community! In this section, we'll describe generic instructions for creating an Anaconda _feedstock_ for a Python 3 package. There are detailed instructions [here](https://github.com/conda-forge/staged-recipes/), but we found them a bit confusing for relatively simple packages.

First, an overview of the steps:
1. Fork the [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes/) repo on GitHub.
1. Create the skeleton recipe for your package.
1. Edit the skeleton recipe.
1. Create a PR for your recipe.
1. Work with conda-forge maintainers until your recipe is merged.

### Forking the conda-forge/staged-recipes repo

On GitHub, go to [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes/) and fork the repository. If you already have a fork, I recommend _deleting_ your fork and reforking. This repository is highly volatile.

### Creating the skeleton recipe

As above, we'll assume you're working with the `linearmodels` package. We'll also assume you're working in `REPO_DIR` as defined below. You'll need to run the below scripts.

```bash
REPO_DIR=~/repo
GITHUB_USER=khwilson
PACKAGE=linearmodels
LOCAL_REPO_DIR="${REPO_DIR}/staged-recipes"

# Make sure your REPO_DIR exists
mkdir -p $REPO_DIR && cd $REPO_DIR

# Pull your fork
git clone "https://github.com/${GITHUB_USER}/staged-recipes.git"
cd $LOCAL_REPO_DIR

# Create the skeleton recipe
cd "recipes"
conda skeleton pypi $PACKAGE
```

You should now see a file in "${PACKAGE}/meta.yaml". This is your skeleton recipe.

### Edit the recipe

You'll need to make several changes to the skeleton. These can be divided into:
1. Make the recipe py3k only.
1. If your recipe involves Cython, adding some build requirements.
1. Getting the license setup.
1. Other "about" metadata.
1. Add your name to the list of maintainers.

#### Make the recipe py3k only

In the `build` section, add a key `skip: True  # [py2k]`

#### If your recipe involves Cython

In the `requirements` section:
* Add a `build` section that looks like this:
```yaml
{% raw %}
build:
  - {{ compiler('c') }}
  - {{ compiler('cxx') }}
{% endraw %}
```
* In the `host` section, change the line involving `pip` to `pip >=10`.
* In the `run` section, remove any references to Cython and pip.

#### Getting the license setup

This is probably the most annoying part. Find your packages online home. Copy the LICENSE file to your recipe's directory. Then in the `about` section, add the line `license_file: NAME_OF_LICENSE_FILE`, where `NAME_OF_LICENSE_FILE` is the file you saved the license to.

Also, you'll need to describe the license by type. Sometimes, conda can figure
this out for you. However, sometimes you'll need to figure it out. To do so,
you can typically dump large parts of the text into Google and it will tell you
the name. In the worst case, you may need to physically search [this
page](https://opensource.org/licenses/alphabetical). Once you've found the
license, add `license: SPDX_SHORT_CODE` to the `about` block.

N.B. You may also need to add a `license_family` to the `about` block. However, the errors should tell you how to do this. :-)

#### Other `about` metatdata

There are some other stubs in the `about` section that conda should have setup for you, specifically around docs. If you can find these online, then add them here.

#### Add your name to the list of maintainers

Finally, at the bottom of the `meta.yaml` file, you will need a section that looks like:

```yaml
extra:
  recipe-maintainers:
    - khwilson
```

Here you should obviously replace `khwilson` with your own GitHub username.

This completes the main part of recipe editing.

### Create a PR for your recipe

Before creating a PR for your recipe, you probably want to test your recipe locally. To do so, you'll need to have docker installed. Then run the following:

```bash
cd $LOCAL_REPO_DIR

# Remove extra recipes
rm -rf recipes/example recipes/spyrmsd
```

Then in the `.circleci/build_steps.sh` file, comment out the line that starts `git ls-tree --name-only main -- .`.

Then you should be able to run `./.circleci/run_docker_build.sh`. You'll probably see some errors which you'll need to fix.

Once these errors are sorted out, you can push your recipe to GitHub and create a PR. Make sure to name the PR something memorable, e.g., `Adding linearmodels recipe`.
