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
        "GSM3271347_gm12878_01",
        "GSM3271347_rep1_gm12878_01",
        "GSM3271347_rep2_gm12878_01",
        "GSM3271348_gm12878_02",
        "GSM3271348_rep1_gm12878_02",
        "GSM3271348_rep2_gm12878_02",
        "GSM3271349_gm12878_03",
        "GSM3271349_rep1_gm12878_03",
        "GSM3271349_rep2_gm12878_03",
        "GSM3271350_gm12878_04",
        "GSM3271350_rep1_gm12878_04",
        "GSM3271350_rep2_gm12878_04",
        "GSM3271351_gm12878_05",
        "GSM3271351_rep1_gm12878_05",
        "GSM3271351_rep2_gm12878_05",
        "GSM3271352_gm12878_06",
        "GSM3271352_rep1_gm12878_06",
        "GSM3271352_rep2_gm12878_06",
        "GSM3271353_gm12878_07",
        "GSM3271353_rep1_gm12878_07",
        "GSM3271353_rep2_gm12878_07",
        "GSM3271355_gm12878_09",
        "GSM3271355_rep1_gm12878_09",
        "GSM3271355_rep2_gm12878_09",
        "GSM3271356_gm12878_10",
        "GSM3271356_rep1_gm12878_10",
        "GSM3271356_rep2_gm12878_10",
        "GSM3271358_gm12878_11",
        "GSM3271358_rep1_gm12878_11",
        "GSM3271358_rep2_gm12878_11",
        "GSM3271360_gm12878_12",
        "GSM3271360_rep1_gm12878_12",
        "GSM3271360_rep2_gm12878_12",
        "GSM3271362_gm12878_13",
        "GSM3271362_rep1_gm12878_13",
        "GSM3271362_rep2_gm12878_13",
        "GSM3271364_gm12878_14",
        "GSM3271364_rep1_gm12878_14",
        "GSM3271364_rep2_gm12878_14",
        "GSM3271366_gm12878_15",
        "GSM3271366_rep1_gm12878_15",
        "GSM3271366_rep2_gm12878_15",
        "GSM3271368_gm12878_16",
        "GSM3271368_rep1_gm12878_16",
        "GSM3271368_rep2_gm12878_16",
        "GSM3271370_gm12878_17",
        "GSM3271370_rep1_gm12878_17",
        "GSM3271370_rep2_gm12878_17",
        "GSM3271372_pbmc_01",
        "GSM3271372_rep1_pbmc_01",
        "GSM3271372_rep2_pbmc_01",
        "GSM3271374_pbmc_02",
        "GSM3271374_rep1_pbmc_02",
        "GSM3271374_rep2_pbmc_02",
        "GSM3271376_pbmc_03",
        "GSM3271376_rep1_pbmc_03",
        "GSM3271376_rep2_pbmc_03",
        "GSM3271378_pbmc_04",
        "GSM3271378_rep1_pbmc_04",
        "GSM3271378_rep2_pbmc_04",
        "GSM3271380_pbmc_05",
        "GSM3271380_rep1_pbmc_05",
        "GSM3271380_rep2_pbmc_05",
        "GSM3271382_pbmc_06",
        "GSM3271382_rep1_pbmc_06",
        "GSM3271382_rep2_pbmc_06",
        "GSM3271384_pbmc_07",
        "GSM3271384_rep1_pbmc_07",
        "GSM3271384_rep2_pbmc_07",
        "GSM3271386_pbmc_08",
        "GSM3271386_rep1_pbmc_08",
        "GSM3271386_rep2_pbmc_08",
        "GSM3271388_pbmc_09",
        "GSM3271388_rep1_pbmc_09",
        "GSM3271388_rep2_pbmc_09",
        "GSM3271390_pbmc_10",
        "GSM3271390_rep1_pbmc_10",
        "GSM3271390_rep2_pbmc_10",
        "GSM3271392_pbmc_11",
        "GSM3271392_rep1_pbmc_11",
        "GSM3271392_rep2_pbmc_11",
        "GSM3271394_pbmc_12",
        "GSM3271394_rep1_pbmc_12",
        "GSM3271394_rep2_pbmc_12",
        "GSM3271396_pbmc_13",
        "GSM3271396_rep1_pbmc_13",
        "GSM3271396_rep2_pbmc_13",
        "GSM3271398_pbmc_14",
        "GSM3271398_rep1_pbmc_14",
        "GSM3271398_rep2_pbmc_14",
        "GSM3271400_pbmc_15",
        "GSM3271400_rep1_pbmc_15",
        "GSM3271400_rep2_pbmc_15",
        "GSM3271402_pbmc_16",
        "GSM3271402_rep1_pbmc_16",
        "GSM3271402_rep2_pbmc_16",
        "GSM3271404_pbmc_17",
        "GSM3271404_rep1_pbmc_17",
        "GSM3271404_rep2_pbmc_17",
        "GSM3271406_pbmc_18",
        "GSM3271406_rep1_pbmc_18",
        "GSM3271406_rep2_pbmc_18",
    ]
    return (keys,)


@app.cell
def _(np, pa):
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

    return arrays_to_table, write_to_file


@app.cell
def _(Path, arrays_to_table, keys, pq, write_to_file):
    basepath = "GSE117876_RAW/selected"
    postfix = ".impute.3dg.txt"
    prefix = "Tan-2018_"

    Path("out").mkdir(parents=True, exist_ok=True)

    outputs_list_file = "out/out_file.txt"
    with open(outputs_list_file, "w") as _outputs_file:
        for _key in keys:
            _filepath = f"{basepath}/{_key}{postfix}"
            print("input: " + _filepath)
            _x, _y, _z, _chr, _coord = [], [], [], [], []
            with open(_filepath, "r") as _file:
                for _line in _file:
                    _tokens = _line.strip().split("\t")
                    _x.append(float(_tokens[2]))
                    _y.append(float(_tokens[3]))
                    _z.append(float(_tokens[4]))
                    _chr.append(_tokens[0])
                    _coord.append(int(_tokens[1]))
            _table = arrays_to_table(_x, _y, _z, _chr, _coord)

            _outputpath_parquet = f"out/{prefix}{_key}.parquet"
            print("Writing: " + _outputpath_parquet)
            pq.write_table(_table, _outputpath_parquet, compression=None)

            _outputpath_arrow = f"out/{prefix}{_key}.arrow"
            print("Writing: " + _outputpath_arrow)
            write_to_file(_outputpath_arrow, _table)

            _outputs_file.write(f"{prefix}{_key}\n")
    return


if __name__ == "__main__":
    app.run()
