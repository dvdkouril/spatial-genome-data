# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "pyarrow", "numpy"]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md(
        """
        # Lampbrush chromosome polymer models → Arrow

        Convert the four Plotly models from Lagunov *et al.*, **The 3D genomics
        of lampbrush chromosomes highlights the role of active transcription in
        chromatin organization** (2026), DOI
        [10.1093/nar/gkag316](https://doi.org/10.1093/nar/gkag316).

        The models cover chicken chr1:55–64 Mb at the lampbrush chromosome (LBC)
        and post-LBC (`_late`) stages. `Spatial` is the native 3D conformation;
        `Flat` is a conformation after simulated flattening for microscopy.
        """
    )
    return (mo,)


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import pyarrow as pa

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    OUT_DIR = BASE_DIR / "out"
    BASE_URL = "https://genedev.bionet.nsc.ru/ftp/by_User/tlagunov/LBCs/htmls"

    # None converts the complete four-file deposit. Set to 1 or 2 for a quick run.
    MAX_STRUCTURES = None
    MAX_DOWNLOAD_BYTES = 5 * 1024**3
    SOURCE_FILES = (
        ("Flat_chr1_55000000-64000000.html", 55_299_512),
        ("Flat_chr1_55000000-64000000_late.html", 25_231_031),
        ("Spatial_chr1_55000000-64000000.html", 55_408_619),
        ("Spatial_chr1_55000000-64000000_late.html", 25_268_296),
    )

    DATA_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    return (
        BASE_URL,
        DATA_DIR,
        MAX_DOWNLOAD_BYTES,
        MAX_STRUCTURES,
        OUT_DIR,
        SOURCE_FILES,
        np,
        pa,
    )


@app.cell
def _(BASE_URL, DATA_DIR, MAX_DOWNLOAD_BYTES, MAX_STRUCTURES, SOURCE_FILES):
    import urllib.request

    if MAX_STRUCTURES is not None and MAX_STRUCTURES < 0:
        raise ValueError("MAX_STRUCTURES must be None or a non-negative integer")

    selected_sources = SOURCE_FILES[:MAX_STRUCTURES]
    expected_total = sum(size for _, size in selected_sources)
    print(
        f"Selected {len(selected_sources)} of {len(SOURCE_FILES)} structures; "
        f"expected download: {expected_total / 1024**2:.1f} MiB"
    )

    def download_file(filename, expected_size):
        if expected_size > MAX_DOWNLOAD_BYTES:
            raise ValueError(f"Refusing to download {filename}: larger than 5 GiB")
        destination = DATA_DIR / filename
        if destination.exists() and destination.stat().st_size == expected_size:
            print(f"Already downloaded: {filename} ({expected_size:,} bytes)")
            return destination

        url = f"{BASE_URL}/{filename}"
        request = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "lbc-arrow-converter/1.0"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                remote_size = response.headers.get("Content-Length")
            if remote_size is not None and int(remote_size) != expected_size:
                raise ValueError(
                    f"Remote size changed for {filename}: {remote_size} vs {expected_size}"
                )
        except urllib.error.URLError as error:
            # The checked-in expected size is still a guard if HEAD is unsupported.
            print(f"HEAD request failed for {filename}; trying GET: {error}")

        partial = destination.with_suffix(destination.suffix + ".part")
        for attempt in range(1, 4):
            try:
                request = urllib.request.Request(
                    url, headers={"User-Agent": "lbc-arrow-converter/1.0"}
                )
                with urllib.request.urlopen(request, timeout=120) as response:
                    with partial.open("wb") as output:
                        while chunk := response.read(1024**2):
                            output.write(chunk)
                actual_size = partial.stat().st_size
                if actual_size != expected_size:
                    raise IOError(
                        f"Incomplete download of {filename}: "
                        f"{actual_size:,} of {expected_size:,} bytes"
                    )
                partial.replace(destination)
                print(f"Downloaded: {filename} ({actual_size:,} bytes)")
                return destination
            except Exception:
                if attempt == 3:
                    raise
                print(f"Download attempt {attempt} failed for {filename}; retrying")
        raise AssertionError("unreachable")

    downloaded_files = [
        download_file(filename, expected_size)
        for filename, expected_size in selected_sources
    ]
    return (downloaded_files,)


@app.cell
def _(mo):
    mo.md("""
    ## Extract the genomic trace

    The final `Plotly.newPlot` call contains the model; earlier occurrences are
    inside the embedded Plotly library. Decode its JSON arguments and select the
    trace named `3D structure`. The DAPI/BAC/mRNA traces are styled copies of the
    same coordinates. SMC and RNA-polymerase overlays are not genomic polymer
    traces and are omitted.

    Hover labels such as `chr1: 55,001,126` provide `chr` and `coord`. The trace
    contains two sister-chromatid chains: labels ascend in the first half and
    descend in the second. Both chains and the original point order are retained.
    """)
    return


@app.cell
def _():
    import json
    import re

    LABEL_PATTERN = re.compile(
        r"^\s*([^:\s]+)\s*:\s*(\d+|\d{1,3}(?:,\d{3})+)\s*$"
    )

    def extract_genomic_trace(path):
        html = path.read_text(encoding="utf-8")
        marker = "Plotly.newPlot("
        call_start = html.rfind(marker)
        if call_start < 0:
            raise ValueError(f"No Plotly.newPlot call in {path.name}")

        decoder = json.JSONDecoder()
        position = call_start + len(marker)

        def next_json(position):
            while html[position].isspace() or html[position] == ",":
                position += 1
            return decoder.raw_decode(html, position)

        _, position = next_json(position)  # Plotly div id
        traces, position = next_json(position)
        matching = [trace for trace in traces if trace.get("name") == "3D structure"]
        if len(matching) != 1:
            raise ValueError(
                f"Expected one '3D structure' trace in {path.name}, found {len(matching)}"
            )
        trace = matching[0]
        n_rows = len(trace["x"])
        if any(len(trace[axis]) != n_rows for axis in ("x", "y", "z")):
            raise ValueError(f"Coordinate arrays have different lengths in {path.name}")
        labels = trace.get("hovertext", [])
        if len(labels) != n_rows:
            raise ValueError(f"Missing genomic hover labels in {path.name}")

        chromosomes, genomic_starts = [], []
        for index, label in enumerate(labels):
            match = LABEL_PATTERN.fullmatch(label)
            if match is None:
                raise ValueError(f"Unrecognized label at row {index} in {path.name}: {label!r}")
            chromosomes.append(match.group(1))
            genomic_starts.append(int(match.group(2).replace(",", "")))
        return trace, chromosomes, genomic_starts

    return (extract_genomic_trace,)


@app.cell
def _(OUT_DIR, downloaded_files, extract_genomic_trace, np, pa):

    def write_structure(source_path):
        trace, chromosomes, genomic_starts = extract_genomic_trace(source_path)
        xyz = {
            axis: np.asarray(trace[axis], dtype=np.float64) for axis in ("x", "y", "z")
        }
        n_rows = len(genomic_starts)
        if any(values.shape != (n_rows,) for values in xyz.values()):
            raise ValueError(f"Invalid coordinate shape in {source_path.name}")
        if not all(np.isfinite(values).all() for values in xyz.values()):
            raise ValueError(f"Non-finite coordinates in {source_path.name}")

        table = pa.Table.from_arrays(
            [
                pa.array(xyz["x"], type=pa.float64()),
                pa.array(xyz["y"], type=pa.float64()),
                pa.array(xyz["z"], type=pa.float64()),
                pa.array(chromosomes, type=pa.string()),
                pa.array(genomic_starts, type=pa.int64()),
            ],
            names=["x", "y", "z", "chr", "coord"],
        )
        destination = OUT_DIR / f"{source_path.stem}.arrow"
        temporary = destination.with_suffix(".arrow.tmp")
        with temporary.open("wb") as sink:
            with pa.ipc.new_file(sink, table.schema) as writer:
                writer.write_table(table)
        temporary.replace(destination)
        print(f"Wrote {destination.name}: {table.num_rows:,} rows")
        return destination

    written_files = [write_structure(path) for path in downloaded_files]
    return (written_files,)


@app.cell
def _(mo, np, pa, written_files):

    verification = []
    for path in written_files:
        with pa.ipc.open_file(str(path)) as reader:
            table = reader.read_all()
        coordinates = table.select(["x", "y", "z"]).to_pydict()
        genomic_starts = table["coord"].to_pylist()
        record = {
            "file": path.name,
            "rows": table.num_rows,
            "distinct_genomic_positions": len(set(genomic_starts)),
            "coord_min_bp": min(genomic_starts),
            "coord_max_bp": max(genomic_starts),
        }
        for axis in ("x", "y", "z"):
            record[f"{axis}_range"] = (
                f"{np.min(coordinates[axis]):.3f} … {np.max(coordinates[axis]):.3f}"
            )
        verification.append(record)
        print(f"\n{path.name}: {table.schema}")
        print(f"First three rows: {table.slice(0, 3).to_pylist()}")

    if verification:
        columns = list(verification[0])
        lines = [
            "## Arrow output check",
            "",
            "Coordinates below are in the published model units (nm).",
            "",
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        lines.extend(
            "| " + " | ".join(str(record[column]) for column in columns) + " |"
            for record in verification
        )
        summary_markdown = "\n".join(lines)
    else:
        summary_markdown = (
            "No structures selected; set `MAX_STRUCTURES` to `None` or a positive integer."
        )
    mo.md(summary_markdown)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Conversion notes

    - Arrow files are written with `pyarrow.ipc.new_file`; coordinates are float64,
      `chr` is string, and `coord` is int64. No coordinate transformation is applied.
    - Repeated `coord` values are intentional: each file contains two sister
      chromatids. The halfway row separates the chains; do not deduplicate by locus.
    - Bead spacing is variable (hundreds to thousands of bp), not a fixed resolution.
    - The paper uses the chicken T2T assembly ASM2420605v2, although the HTML itself
      does not state the assembly. The model methods describe lengths in nm.
    - `Flat` and `Spatial` are alternative states/views of a simulated conformation,
      not independent biological replicates.
    """)
    return


if __name__ == "__main__":
    app.run()
