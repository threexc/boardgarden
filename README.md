# boardgarden

tgamblin's boardfarm repo, built for testing RISC-V development boards with [Labgrid](https://github.com/labgrid-project/labgrid) and [Forgejo](https://forgejo.org/) Actions

## Usage

### boards

This entire subdirectory is meant to be used with
[uv](https://docs.astral.sh/uv/) for installing and managing Python projects. It
includes a `common` module, which the `pyproject.toml` files are used to help
install in the virtualenv. This allows re-use of various Labgrid strategy
functions and pytest fixtures across multiple boards, since the fundamental
actions used (such as setting a TFTP server's IP address on the U-Boot prompt)
are more or less the same.

Assuming you have `uv` installed, you can set up the Python virtual environment
with all of the necessary modules by doing:

1. `cd boards`
2. `uv sync`

Using the board configurations will depend on how you have structured your
Labgrid deployment (see the [docs](https://labgrid.readthedocs.io/en/latest/)
for more details). Assuming that you have created a place called
`bf-muse-pi-pro` and exported the corresponding resources in
`boards/muse-pi-pro/exporter.yaml` with an appropriate matching pattern, you
should be able to invoke the labgrid CLI using `uv run`, e.g.:

1. `uv run labgrid-client -p bf-muse-pi-pro acquire`
2. `uv run labgrid-client -p bf-muse-pi-pro -s tftp con`

Or, if you want to run the test suite, you can do:

1. `uv run labgrid-client -p bf-muse-pi-pro acquire`
2. `uv run pytest -vvv --html=report.html --self-contained-html muse-pi-pro/pytest/`
