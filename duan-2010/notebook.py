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
    import pyarrow.csv
    import pyarrow.parquet as pq

    input_file = "41586_2010_BFnature08973_MOESM239_ESM.pdb"
    return Path, input_file, np, pa, pq


@app.cell
def _(np, pa):
    def model_lines_to_coord_arrays(lines):
        x_arr, y_arr, z_arr, chr_arr, coord_arr = [], [], [], [], []
        l_num = 0
        for line in lines.split("\n"):
            line_annot = line[0:6].strip()
            l_num += 1
            if line_annot == "HETATM" or line_annot == "ATOM":
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                chrom = line[21:22]
                coord = l_num  # for now just generating global fake coordinate
                x_arr.append(x)
                y_arr.append(y)
                z_arr.append(z)
                chr_arr.append(chrom)
                coord_arr.append(coord)
                if l_num <= 1:
                    print(f"x: {x}, y: {y}, z: {z}, chr: {chrom}")
        return [x_arr, y_arr, z_arr, chr_arr, coord_arr]

    def arrays_to_table(x_arr, y_arr, z_arr, chrom_arr, coord_arr):
        return pa.Table.from_arrays(
            [
                np.array(x_arr),
                np.array(y_arr),
                np.array(z_arr),
                np.array(chrom_arr),
                np.array(coord_arr),
            ],
            ["x", "y", "z", "chr", "coord"],
        )

    def write_to_file(outfile_path, table):
        with pa.OSFile(outfile_path, "wb") as sink:
            with pa.ipc.RecordBatchFileWriter(sink, table.schema) as writer:
                writer.write_table(table)

    return arrays_to_table, model_lines_to_coord_arrays, write_to_file


@app.cell
def _(
    Path,
    arrays_to_table,
    input_file,
    model_lines_to_coord_arrays,
    pa,
    pq,
    write_to_file,
):
    Path("out").mkdir(parents=True, exist_ok=True)

    outputs_list_file = "out/out_file.txt"
    with open(outputs_list_file, "w") as _outputs_file:
        with open(f"./{input_file}", "r") as _file:
            _lines = _file.read()

        _table = arrays_to_table(*model_lines_to_coord_arrays(_lines))

        _outputpath_parquet = "out/yeast_model.parquet"
        print("Writing: " + _outputpath_parquet)
        pq.write_table(_table, _outputpath_parquet, compression=None)

        _outputpath_arrow = "out/yeast_model.arrow"
        print("Writing: " + _outputpath_arrow)
        write_to_file(_outputpath_arrow, _table)

        pa.csv.write_csv(
            _table,
            "out/yeast_model.csv",
            write_options=pa.csv.WriteOptions(include_header=True),
        )

        _outputs_file.write("yeast_model\n")
    return


if __name__ == "__main__":
    app.run()
