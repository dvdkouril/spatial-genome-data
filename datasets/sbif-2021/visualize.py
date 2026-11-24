# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "chromospyce",
#     "marimo",
#     "pyarrow",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    from pathlib import Path

    import chromospyce
    import marimo as mo
    import pyarrow as pa

    return Path, chromospyce, mo, pa


@app.cell
def _(Path, chromospyce, mo):
    # Show the structure via chromospyce widget
    _file_as_bytes = Path("out/dros.3.arrow").read_bytes()
    _vc = {"color": "#6600ff", "scale": 0.01, "links": True, "mark": "sphere"}
    mo.ui.anywidget(chromospyce.Widget(structure=_file_as_bytes, viewconfig=_vc))
    return


@app.cell
def _(chromospyce, mo, pa):
    # Same structure, re-encoded from the Arrow file format to the stream format
    with pa.ipc.open_file("out/dros.3.arrow") as _arrow_file:
        _table = _arrow_file.read_all()

    _output_stream = pa.BufferOutputStream()
    with pa.ipc.new_stream(_output_stream, _table.schema) as _writer:
        _writer.write_table(_table)

    _vc = {"color": "lightgreen", "scale": 0.01, "links": True, "mark": "sphere"}
    mo.ui.anywidget(
        chromospyce.Widget(
            structure=_output_stream.getvalue().to_pybytes(), viewconfig=_vc
        )
    )
    return


if __name__ == "__main__":
    app.run()
