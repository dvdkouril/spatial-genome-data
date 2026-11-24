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
        "GSM2219497_Cell_1",
        "GSM2219498_Cell_2",
        "GSM2219499_Cell_3",
        "GSM2219500_Cell_4",
        "GSM2219501_Cell_5",
        "GSM2219502_Cell_6",
        "GSM2219503_Cell_7",
        "GSM2219504_Cell_8",
    ]
    return (keys,)


@app.cell
def _(np, pa):
    def separate_into_models(filepath):
        models_lines = {}
        with open(filepath, "r") as file:
            for line in file:
                line_annot = line[0:6].strip()
                if line_annot == "MODEL":
                    model_num = line.split()[1]
                    models_lines[model_num] = []

        with open(filepath, "r") as file:
            current_model = "0"
            for line in file:
                line_annot = line[0:6].strip()
                if line_annot == "MODEL":
                    model_num = line.split()[1]
                    current_model = model_num
                    continue
                if line_annot == "ENDMDL":
                    continue
                if line_annot == "HETATM":
                    models_lines[current_model].append(line)
        return models_lines

    def model_lines_to_coord_arrays(lines):
        x_arr, y_arr, z_arr, chr_arr, coord_arr = [], [], [], [], []
        for line in lines:
            line_annot = line[0:6]
            if line_annot == "HETATM" or line_annot == "ATOM":
                x_arr.append(float(line[30:38]))
                y_arr.append(float(line[38:46]))
                z_arr.append(float(line[46:54]))
                chr_arr.append(line[17:22])
                coord_arr.append(int(line[80:90]))
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

    return (
        arrays_to_table,
        model_lines_to_coord_arrays,
        separate_into_models,
        write_to_file,
    )


@app.cell
def _(
    Path,
    arrays_to_table,
    keys,
    model_lines_to_coord_arrays,
    pq,
    separate_into_models,
    write_to_file,
):
    basepath = "GSE80280_RAW"
    postfix = "_genome_structure_model.pdb"
    prefix = "Stevens-2017_"

    Path("out").mkdir(parents=True, exist_ok=True)

    outputs_list_file = "out/out_file.txt"
    with open(outputs_list_file, "w") as _outputs_file:
        for _key in keys:
            _filepath = f"{basepath}/{_key}{postfix}"
            print("input: " + _filepath)

            for _n, _model in separate_into_models(_filepath).items():
                _table = arrays_to_table(*model_lines_to_coord_arrays(_model))

                _outputpath_parquet = f"out/{prefix}{_key}_model_{_n}.parquet"
                print("Writing: " + _outputpath_parquet)
                pq.write_table(_table, _outputpath_parquet, compression=None)

                _outputpath_arrow = f"out/{prefix}{_key}_model_{_n}.arrow"
                print("Writing: " + _outputpath_arrow)
                write_to_file(_outputpath_arrow, _table)

                _outputs_file.write(f"{prefix}{_key}_model_{_n}\n")
    return


if __name__ == "__main__":
    app.run()
