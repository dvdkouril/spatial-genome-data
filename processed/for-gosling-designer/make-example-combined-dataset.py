import marimo

__generated_with = "0.17.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import pyarrow as pa
    import pandas as pd
    return (pa,)


@app.cell
def _():
    modelFileName = "Tan-2018_GSM3271347_gm12878_01.arrow"
    modelPath = "tan-2018/out"
    modelFilePath = f"../../{modelPath}/{modelFileName}"
    modelFilePath
    return modelFileName, modelFilePath


@app.cell
def _(modelFilePath, pa):
    # 1. Read the original spatial model file
    with open(modelFilePath, 'rb') as file:
        content = file.read()
        print(content[0:10])

        # read the ipc
        reader = pa.ipc.open_file(file)
        table = reader.read_all()
        # print(table)

    print(table)
    return (table,)


@app.cell
def _(modelFileName, table):
    # Save as .csv to disk
    newCsvFileName = f"{modelFileName.split(".")[0]}.csv"
    df = table.to_pandas()
    df.to_csv(newCsvFileName)
    return


@app.cell
def _(table):
    table
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
