import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import pyarrow as pa
    import pandas as pd
    import requests
    return pa, requests


@app.cell
def _():
    modelFileName = "Tan-2018_GSM3271347_gm12878_01.arrow"
    modelFileUrl = f"https://pub-5c3f8ce35c924114a178c6e929fc3ac7.r2.dev/{modelFileName}"
    return modelFileName, modelFileUrl


@app.cell
def _(modelFileUrl, pa, requests):
    response = requests.get(modelFileUrl)
    response.raise_for_status()  # raises if status != 200

    data = response.content  # this is bytes

    reader = pa.ipc.RecordBatchFileReader(pa.py_buffer(data))
    table = reader.read_all()

    print(table)
    return (table,)


@app.cell
def _(table):
    modelDF = table.to_pandas()
    return (modelDF,)


@app.cell
def _(modelDF):
    # modelDF["chr"] = modelDF["chr"].spli
    modelDFprocessed = modelDF.copy()
    modelDFprocessed[["chr", "patmat"]] = modelDF["chr"].str.extract(r"(\d+)\((\w+)\)")
    modelDFprocessed["chr"] = "chr" + modelDFprocessed["chr"]
    modelDFprocessed
    return (modelDFprocessed,)


@app.cell
def _(modelDFprocessed, modelFileName):
    # Save as .csv to disk
    newCsvFileName = f"out/{modelFileName.split(".")[0]}.csv"
    modelDFprocessed.to_csv(newCsvFileName, index=False)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
