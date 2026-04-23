import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import pyarrow as pa
    import pyarrow.parquet as pq
    import pandas as pd
    import requests
    from pathlib import Path

    return Path, pa, pq, requests


@app.cell
def _():
    modelFileNames = [
        "Tan-2018_GSM3271347_gm12878_01.arrow",
    ]
    return (modelFileNames,)


@app.cell
def _(pa, requests):
    def fetchFileAsTable(modelFileUrl):
        response = requests.get(modelFileUrl)
        response.raise_for_status()  # raises if status != 200
    
        data = response.content  # this is bytes
    
        reader = pa.ipc.RecordBatchFileReader(pa.py_buffer(data))
        table = reader.read_all()
    
        # print(table)
        return table

    return (fetchFileAsTable,)


@app.cell
def _(pa):
    def write_to_file(outfile_path, table):
        with pa.OSFile(outfile_path, 'wb') as sink:
            with pa.ipc.RecordBatchFileWriter(sink, table.schema) as writer:
                writer.write_table(table)

    return (write_to_file,)


@app.cell
def _(Path, fetchFileAsTable, modelFileNames, pa, pq, write_to_file):
    out_folder = Path("out")
    out_folder.mkdir(parents=True, exist_ok=True)
    outputs = []

    for modelFileName in modelFileNames:
        modelFileUrl = f"https://pub-5c3f8ce35c924114a178c6e929fc3ac7.r2.dev/{modelFileName}"
        table = fetchFileAsTable(modelFileUrl)
        modelDF = table.to_pandas()

        # split the 'chr' column
        modelDFprocessed = modelDF.copy()
        modelDFprocessed["chrOG"] = modelDFprocessed["chr"]
        modelDFprocessed[["chr", "patmat"]] = modelDF["chr"].str.extract(r"([A-Za-z0-9]+)\((\w+)\)")
        modelDFprocessed["chr"] = "chr" + modelDFprocessed["chr"]

        # add index column
        modelDFprocessed.insert(0, 'index', range(len(modelDFprocessed)))

        # recenter
        xyz_cols = ['x', 'y', 'z']
        # modelDFprocessed[xyz_cols] = modelDFprocessed[xyz_cols] - modelDFprocessed[xyz_cols].mean()
        modelDFprocessed[xyz_cols] = modelDFprocessed[xyz_cols] - (modelDFprocessed[xyz_cols].min() + modelDFprocessed[xyz_cols].max()) / 2

        # normalize
        max_dim = (modelDFprocessed[xyz_cols].max() - modelDFprocessed[xyz_cols].min()).max()
        scale_factor = 1 / max_dim
        modelDFprocessed[xyz_cols] = modelDFprocessed[xyz_cols] * scale_factor

        # Save as .csv to disk
        fileKey = f"forGD_{modelFileName.split(".")[0]}"
        newCsvFileName = f"out/{fileKey}.csv"
        modelDFprocessed.to_csv(newCsvFileName, index=False)
    
        # write to outputs array: this will then be used to generate the structures.md table
        outputs.append(f"{fileKey}")

        processed_table = pa.Table.from_pandas(modelDFprocessed)

        # Write also as .parquet and .arrow file: 
        outputpath_parquet = f'out/{fileKey}.parquet'
        pq.write_table(processed_table, outputpath_parquet, compression=None)
    
        outputpath_arrow = f'out/{fileKey}.arrow'
        write_to_file(outputpath_arrow, processed_table)
    return (outputs,)


@app.cell
def _(outputs):
    # Write list of datasets to out_file.txt
    outputs_list_file = "out/out_file.txt"
    with open(outputs_list_file, "w") as outputs_file:
        for key in outputs:
            outputs_file.write(f'{key}\n')
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
