# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pyarrow",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq

    return Path, np, pa, pq


@app.cell
def _():
    keys = [
        "dros.3",
        "dros.10",
        "dros.4000",
        "dros.10123",
    ]
    return (keys,)


@app.cell
def _(np, pa, pq):
    def txt_to_coord_arrays(filepath):
        x_arr, y_arr, z_arr = [], [], []
        with open(filepath, "r") as file:
            for line in file:
                tokens = line.split("\t")
                x_arr.append(float(tokens[0]))
                y_arr.append(float(tokens[1]))
                z_arr.append(float(tokens[2]))
        return [x_arr, y_arr, z_arr]

    def arrays_to_table(x_arr, y_arr, z_arr):
        return pa.Table.from_arrays(
            [np.array(x_arr), np.array(y_arr), np.array(z_arr)], ["x", "y", "z"]
        )

    def write_to_file(outfile_path, table):
        with pa.OSFile(outfile_path, "wb") as sink:
            with pa.ipc.RecordBatchFileWriter(sink, table.schema) as writer:
                writer.write_table(table)

    def convert_to_arrow(filepath, outputpath):
        table = arrays_to_table(*txt_to_coord_arrays(filepath))
        write_to_file(outputpath, table)

    def convert_to_parquet(filepath, outputpath):
        table = arrays_to_table(*txt_to_coord_arrays(filepath))
        pq.write_table(table, outputpath, compression=None)

    return convert_to_arrow, convert_to_parquet


@app.cell
def _(Path, convert_to_arrow, convert_to_parquet, keys):
    basepath = "input"
    postfix = ".txt"

    Path("out").mkdir(parents=True, exist_ok=True)

    for _key in keys:
        _filepath = f"{basepath}/{_key}{postfix}"
        print("input: " + _filepath)

        _outfile_path = "out/" + _key + ".arrow"
        print("output: " + _outfile_path)
        convert_to_arrow(_filepath, _outfile_path)

        _outfile_path = "out/" + _key + ".parquet"
        print("output: " + _outfile_path)
        convert_to_parquet(_filepath, _outfile_path)
    print("Done.")
    return


if __name__ == "__main__":
    app.run()
