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
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Kitanishi et al. single-cell genome models → Arrow

        Convert the RPR (recurrence plot reconstruction) models deposited at
        [10.5281/zenodo.18498172](https://doi.org/10.5281/zenodo.18498172) for
        **“Recurrence plot reconstruction reveals chromosomal reorganization before
        territory formation”** ([10.1093/nargab/lqag023](https://doi.org/10.1093/nargab/lqag023)).

        The deposit contains 632 mouse embryo models (1-, 2-, 4-, 8-, and 64-cell
        stages) and 15 postnatal-day-0 cortical neuron models. Each CSV is one cell
        and contains both homolog/haplotype copies at 1 Mb genomic resolution.
        """
    )
    return


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import pyarrow as pa

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    OUT_DIR = BASE_DIR / "out"
    DATA_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    # None converts all 647 primary CSVs; use a small integer for a quick trial.
    MAX_STRUCTURES = None
    MAX_DOWNLOAD_BYTES = 5 * 1024**3
    SOURCE_URL = (
        "https://zenodo.org/api/records/18498172/files/"
        "Gotoh-Lab/Kitanishi_2025-v1.0.0.zip/content"
    )
    ZIP_NAME = "Kitanishi_2025-v1.0.0.zip"
    SOURCE_SIZE = 39_400_388
    SOURCE_MD5 = "da9e784936686f4c86a0051bf1607930"
    NESTED_ARCHIVES = (
        "Gotoh-Lab-Kitanishi_2025-b0cc59f/Coordinates/embryo_coordinates.tar.gz",
        "Gotoh-Lab-Kitanishi_2025-b0cc59f/Coordinates/neuron_coordinates.tar.gz",
    )
    BIN_SIZE = 1_000_000
    CHROMOSOMES = {**{i: f"chr{i}" for i in range(1, 20)}, 20: "chrX", 21: "chrY"}
    return (
        BIN_SIZE,
        CHROMOSOMES,
        DATA_DIR,
        MAX_DOWNLOAD_BYTES,
        MAX_STRUCTURES,
        NESTED_ARCHIVES,
        OUT_DIR,
        SOURCE_MD5,
        SOURCE_SIZE,
        SOURCE_URL,
        ZIP_NAME,
        np,
        pa,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Download and verify the deposit

        Zenodo exposes one **39,400,388-byte ZIP**. Its two coordinate tarballs are
        read directly as nested ZIP members, so no duplicate archives or extracted CSV
        trees are needed. Existing downloads are reused only after size and MD5 checks.
        """
    )
    return


@app.cell
def _(DATA_DIR, MAX_DOWNLOAD_BYTES, SOURCE_MD5, SOURCE_SIZE, SOURCE_URL, ZIP_NAME):
    import hashlib
    import os
    import urllib.request

    def file_md5(path):
        digest = hashlib.md5()
        with path.open("rb") as stream:
            while chunk := stream.read(1024**2):
                digest.update(chunk)
        return digest.hexdigest()

    def download_deposit():
        if SOURCE_SIZE > MAX_DOWNLOAD_BYTES:
            raise ValueError("The source ZIP exceeds the 5 GiB download limit")
        destination = DATA_DIR / ZIP_NAME
        if destination.exists():
            actual_size = destination.stat().st_size
            actual_md5 = file_md5(destination)
            if actual_size != SOURCE_SIZE or actual_md5 != SOURCE_MD5:
                raise ValueError(
                    f"Cached {destination} failed verification; delete it and rerun. "
                    f"size={actual_size}, md5={actual_md5}"
                )
            print(f"Using verified cached download: {destination.name}")
            return destination

        temporary = destination.with_suffix(".zip.part")
        for attempt in range(1, 4):
            try:
                request = urllib.request.Request(
                    SOURCE_URL, headers={"User-Agent": "kitanishi-arrow-converter/1.0"}
                )
                digest = hashlib.md5()
                with urllib.request.urlopen(request, timeout=120) as response:
                    declared_size = response.headers.get("Content-Length")
                    if declared_size and int(declared_size) > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Remote file exceeds the 5 GiB download limit")
                    with temporary.open("wb") as output:
                        while chunk := response.read(1024**2):
                            output.write(chunk)
                            digest.update(chunk)
                actual_size = temporary.stat().st_size
                if actual_size != SOURCE_SIZE or digest.hexdigest() != SOURCE_MD5:
                    raise IOError(
                        f"Download verification failed: size={actual_size}, "
                        f"md5={digest.hexdigest()}"
                    )
                os.replace(temporary, destination)
                print(f"Downloaded and verified {destination.name} ({actual_size:,} bytes)")
                return destination
            except Exception:
                temporary.unlink(missing_ok=True)
                if attempt == 3:
                    raise
                print(f"Download attempt {attempt} failed; retrying")
        raise AssertionError("unreachable")

    archive_path = download_deposit()
    return archive_path, file_md5


@app.cell
def _(mo):
    mo.md(
        """
        ## Inventory the primary structures

        Only file members ending in `.csv` are considered. Three duplicates under
        `.ipynb_checkpoints` are excluded. The unsexed path `8cell/cell8_126.csv` is
        deliberately retained; its sex is inferred later from its X/Y-copy layout.
        Output names combine sample kind, stage where applicable, and source CSV stem.
        """
    )
    return


@app.cell
def _(NESTED_ARCHIVES, archive_path):
    import tarfile as _tarfile
    import zipfile as _zipfile
    from collections import Counter
    from pathlib import PurePosixPath

    def describe_member(archive_name, member_name):
        path = PurePosixPath(member_name)
        parts = path.parts
        model_id = path.stem
        kind = "embryo" if "embryo_coordinates" in archive_name else "neuron"
        if kind == "embryo":
            stage = parts[0]
            sex = parts[1] if len(parts) > 2 and parts[1] in {"female", "male"} else None
            output_name = f"embryo__{stage}__{model_id}.arrow"
        else:
            stage = "postnatal_day_0"
            sex_part = next((part for part in parts if part in {"sex0", "sex1"}), None)
            sex = {"sex0": "female", "sex1": "male"}.get(sex_part)
            output_name = f"neuron__{model_id}.arrow"
        return {
            "kind": kind,
            "stage": stage,
            "path_sex": sex,
            "model_id": model_id,
            "archive_name": archive_name,
            "member_name": member_name,
            "output_name": output_name,
        }

    structures = []
    skipped_checkpoints = []
    with _zipfile.ZipFile(archive_path) as outer:
        for archive_name in NESTED_ARCHIVES:
            members = []
            with outer.open(archive_name) as compressed:
                with _tarfile.open(fileobj=compressed, mode="r|gz") as archive:
                    for member in archive:
                        if not member.isfile() or not member.name.endswith(".csv"):
                            continue
                        if ".ipynb_checkpoints" in PurePosixPath(member.name).parts:
                            skipped_checkpoints.append(member.name)
                            continue
                        members.append(member.name)
            structures.extend(
                describe_member(archive_name, member_name)
                for member_name in sorted(members)
            )

    output_names = [item["output_name"] for item in structures]
    if len(output_names) != len(set(output_names)):
        raise ValueError("Output names are not unique")
    inventory_counts = Counter(
        (item["kind"], item["stage"], item["path_sex"] or "not in path")
        for item in structures
    )
    print(f"Discovered {len(structures)} primary structures")
    print(f"Excluded {len(skipped_checkpoints)} notebook-checkpoint duplicates")
    for key, count in sorted(inventory_counts.items()):
        print(f"  {' / '.join(key)}: {count}")
    return describe_member, inventory_counts, skipped_checkpoints, structures


@app.cell
def _(MAX_STRUCTURES, mo, structures):
    if MAX_STRUCTURES is not None and (
        not isinstance(MAX_STRUCTURES, int) or isinstance(MAX_STRUCTURES, bool) or MAX_STRUCTURES < 0
    ):
        raise ValueError("MAX_STRUCTURES must be None or a non-negative integer")
    selected_structures = (
        structures if MAX_STRUCTURES is None else structures[:MAX_STRUCTURES]
    )
    selection_message = (
        f"Selected **{len(selected_structures)} of {len(structures)}** structures "
        f"(`MAX_STRUCTURES={MAX_STRUCTURES!r}`)."
    )
    print(selection_message.replace("**", "").replace("`", ""))
    mo.md(selection_message)
    return selected_structures


@app.cell
def _(mo):
    mo.md(
        """
        ## Decode CSV rows and write Arrow

        Each headerless row is `copy_index, chromosome_code, bin_midpoint, x, y, z`.
        Codes 1–19 map to `chr1`–`chr19`, 20 to `chrX`, and 21 to `chrY`. The MATLAB
        code uses `(j - 0.5) * res`, confirming that positions are bin midpoints:
        Arrow `coord` is therefore **midpoint − 500,000 bp**, the start of the 1 Mb bin.

        Trailing all-zero allocation/padding rows are removed. XYZ values and source row
        order are otherwise unchanged. `copy_index` is retained as an additional int64
        column; model ID, sex, source member, assembly, and processing notes are stored
        in Arrow schema metadata. No maternal/paternal relabeling is applied.
        """
    )
    return


@app.cell
def _(BIN_SIZE, CHROMOSOMES, NESTED_ARCHIVES, OUT_DIR, archive_path, np, pa):
    import io
    import tarfile as _tarfile
    import zipfile as _zipfile

    def infer_sex(copy_index, chromosome_code):
        if np.any(chromosome_code == 21):
            return "male"
        x_copies = set(copy_index[chromosome_code == 20].tolist())
        if x_copies == {0, 1}:
            return "female"
        return "unknown"

    def table_from_csv(stream, structure):
        # Buffer the small member: streaming tar files are not seekable on every Python.
        csv_text = io.StringIO(stream.read().decode("ascii"))
        rows = np.loadtxt(csv_text, delimiter=",", ndmin=2)
        if rows.shape[1] != 6 or rows.shape[0] == 0:
            raise ValueError(f"Unexpected CSV shape {rows.shape} in {structure['member_name']}")
        if not np.isfinite(rows).all():
            raise ValueError(f"Non-finite value in {structure['member_name']}")
        source_row_count = len(rows)

        padding = np.all(rows == 0, axis=1)
        if padding.any():
            first_padding = int(np.flatnonzero(padding)[0])
            if not padding[first_padding:].all():
                raise ValueError(f"Non-trailing all-zero row in {structure['member_name']}")
            rows = rows[:first_padding]
        padding_count = source_row_count - len(rows)
        if not len(rows):
            raise ValueError(f"No genomic beads in {structure['member_name']}")

        integer_columns = rows[:, :3]
        if not np.equal(integer_columns, np.round(integer_columns)).all():
            raise ValueError(f"Non-integer genomic field in {structure['member_name']}")
        copy_index = rows[:, 0].astype(np.int64)
        chromosome_code = rows[:, 1].astype(np.int64)
        midpoint = rows[:, 2].astype(np.int64)
        if not set(copy_index).issubset({0, 1}):
            raise ValueError(f"Unexpected copy index in {structure['member_name']}")
        if not set(chromosome_code).issubset(CHROMOSOMES):
            raise ValueError(f"Unexpected chromosome code in {structure['member_name']}")
        if np.any(midpoint < BIN_SIZE // 2) or np.any(midpoint % BIN_SIZE != BIN_SIZE // 2):
            raise ValueError(f"Position is not a 1 Mb-bin midpoint in {structure['member_name']}")
        bead_keys = set(zip(copy_index.tolist(), chromosome_code.tolist(), midpoint.tolist()))
        if len(bead_keys) != len(rows):
            raise ValueError(f"Duplicate copy/chromosome/bin row in {structure['member_name']}")

        inferred_sex = infer_sex(copy_index, chromosome_code)
        path_sex = structure["path_sex"]
        if path_sex and inferred_sex != "unknown" and path_sex != inferred_sex:
            raise ValueError(
                f"Sex from path ({path_sex}) disagrees with layout ({inferred_sex}) "
                f"in {structure['member_name']}"
            )
        sex = path_sex or inferred_sex
        sex_source = "directory name" if path_sex else "inferred from X/Y-copy layout"
        chromosomes = [CHROMOSOMES[int(code)] for code in chromosome_code]
        genomic_start = midpoint - BIN_SIZE // 2
        metadata = {
            "paper_doi": "10.1093/nargab/lqag023",
            "dataset_doi": "10.5281/zenodo.18498172",
            "source_archive": structure["archive_name"],
            "source_member": structure["member_name"],
            "model_id": structure["model_id"],
            "sample_kind": structure["kind"],
            "developmental_stage": structure["stage"],
            "sex": sex,
            "sex_source": sex_source,
            "organism": "Mus musculus",
            "genome_assembly": "mm10 (paper Methods)",
            "method": "recurrence plot reconstruction from single-cell Hi-C",
            "resolution_bp": str(BIN_SIZE),
            "coord_definition": "1 Mb-bin start; source bin midpoint minus 500000 bp",
            "coordinate_units": "relative/dimensionless; no physical scale in the paper",
            "copy_index": "source homolog/haplotype index (0 or 1); not relabeled",
            "source_row_count": str(source_row_count),
            "filtered_zero_padding_rows": str(padding_count),
        }
        schema = pa.schema(
            [
                pa.field("x", pa.float64(), nullable=False),
                pa.field("y", pa.float64(), nullable=False),
                pa.field("z", pa.float64(), nullable=False),
                pa.field("chr", pa.string(), nullable=False),
                pa.field("coord", pa.int64(), nullable=False),
                pa.field("copy_index", pa.int64(), nullable=False),
            ],
            metadata={key.encode(): value.encode() for key, value in metadata.items()},
        )
        table = pa.Table.from_arrays(
            [
                pa.array(rows[:, axis], type=pa.float64()) for axis in (3, 4, 5)
            ]
            + [
                pa.array(chromosomes, type=pa.string()),
                pa.array(genomic_start, type=pa.int64()),
                pa.array(copy_index, type=pa.int64()),
            ],
            schema=schema,
        )
        return table, sex, sex_source, source_row_count, padding_count

    def convert_selected(selected):
        selected_by_archive = {name: {} for name in NESTED_ARCHIVES}
        for structure in selected:
            selected_by_archive[structure["archive_name"]][structure["member_name"]] = structure
        converted = {}
        with _zipfile.ZipFile(archive_path) as outer:
            for archive_name, selected_members in selected_by_archive.items():
                if not selected_members:
                    continue
                with outer.open(archive_name) as compressed:
                    with _tarfile.open(fileobj=compressed, mode="r|gz") as archive:
                        for member in archive:
                            structure = selected_members.get(member.name)
                            if structure is None:
                                continue
                            stream = archive.extractfile(member)
                            if stream is None:
                                raise IOError(f"Cannot read {member.name}")
                            table, sex, sex_source, source_rows, padding = table_from_csv(
                                stream, structure
                            )
                            destination = OUT_DIR / structure["output_name"]
                            temporary = destination.with_suffix(".arrow.tmp")
                            try:
                                with temporary.open("wb") as sink:
                                    with pa.ipc.new_file(sink, table.schema) as writer:
                                        writer.write_table(table)
                                temporary.replace(destination)
                            finally:
                                temporary.unlink(missing_ok=True)
                            converted[structure["output_name"]] = {
                                "structure": structure,
                                "path": destination,
                                "rows": table.num_rows,
                                "source_rows": source_rows,
                                "padding_rows": padding,
                                "sex": sex,
                                "sex_source": sex_source,
                            }
                            if len(converted) % 50 == 0 or len(converted) == len(selected):
                                print(f"Converted {len(converted)} of {len(selected)} structures")
        if len(converted) != len(selected):
            found = set(converted)
            absent = [s["output_name"] for s in selected if s["output_name"] not in found]
            raise IOError(f"Missing selected archive members: {absent}")
        return [converted[item["output_name"]] for item in selected]

    return convert_selected, infer_sex, table_from_csv


@app.cell
def _(convert_selected, selected_structures):
    conversions = convert_selected(selected_structures)
    return (conversions,)


@app.cell
def _(mo):
    mo.md(
        """
        ## Validate the Arrow IPC files

        Read every result back, check required column types and row counts, and calculate
        coordinate ranges. The grouped summary keeps the full 647-file run manageable.
        The expected complete inventory is 75 1-cell, 109 2-cell, 121 4-cell, 126 8-cell,
        201 64-cell, and 15 neuron models. The paper lists 125 8-cell models; the extra
        archived `cell8_126` is converted rather than silently discarded.
        """
    )
    return


@app.cell
def _(CHROMOSOMES, conversions, np, pa):
    expected_types = {
        "x": pa.float64(),
        "y": pa.float64(),
        "z": pa.float64(),
        "chr": pa.string(),
        "coord": pa.int64(),
        "copy_index": pa.int64(),
    }
    validation = []
    grouped = {}
    for record in conversions:
        path = record["path"]
        with pa.ipc.open_file(str(path)) as reader:
            table = reader.read_all()
        if table.column_names != list(expected_types):
            raise ValueError(f"Unexpected columns in {path.name}: {table.column_names}")
        for name, expected_type in expected_types.items():
            if table.schema.field(name).type != expected_type:
                raise TypeError(f"{path.name}: {name} is not {expected_type}")
        if table.num_rows != record["rows"] or table.num_rows == 0:
            raise ValueError(f"Row-count mismatch in {path.name}")
        if not set(table["chr"].to_pylist()).issubset(set(CHROMOSOMES.values())):
            raise ValueError(f"Unexpected chromosome name in {path.name}")
        starts = table["coord"].to_numpy(zero_copy_only=False)
        if starts.min() < 0 or np.any(starts % 1_000_000 != 0):
            raise ValueError(f"Invalid genomic bin start in {path.name}")

        row = {
            "file": path.name,
            "rows": table.num_rows,
            "sex": record["sex"],
            "sex_source": record["sex_source"],
            "padding_rows": record["padding_rows"],
        }
        for axis in ("x", "y", "z"):
            values = table[axis].to_numpy(zero_copy_only=False)
            if not np.isfinite(values).all():
                raise ValueError(f"Non-finite {axis} in {path.name}")
            row[f"{axis}_min"] = float(values.min())
            row[f"{axis}_max"] = float(values.max())
        validation.append(row)

        group_name = (
            f"{record['structure']['kind']} / {record['structure']['stage']}"
        )
        if group_name not in grouped:
            grouped[group_name] = {
                "group": group_name,
                "structures": 0,
                "rows_min": table.num_rows,
                "rows_max": table.num_rows,
                "total_beads": 0,
                "zero_padding_rows": 0,
                **{f"{axis}_{bound}": row[f"{axis}_{bound}"]
                   for axis in ("x", "y", "z") for bound in ("min", "max")},
            }
        group = grouped[group_name]
        group["structures"] += 1
        group["rows_min"] = min(group["rows_min"], table.num_rows)
        group["rows_max"] = max(group["rows_max"], table.num_rows)
        group["total_beads"] += table.num_rows
        group["zero_padding_rows"] += record["padding_rows"]
        for axis in ("x", "y", "z"):
            group[f"{axis}_min"] = min(group[f"{axis}_min"], row[f"{axis}_min"])
            group[f"{axis}_max"] = max(group[f"{axis}_max"], row[f"{axis}_max"])

    group_summaries = list(grouped.values())
    coordinate_ranges = {
        axis: (
            min(row[f"{axis}_min"] for row in validation),
            max(row[f"{axis}_max"] for row in validation),
        )
        for axis in ("x", "y", "z")
    } if validation else {}
    sample_rows = []
    if conversions:
        with pa.ipc.open_file(str(conversions[0]["path"])) as reader:
            sample_rows = reader.read_all().slice(0, 3).to_pylist()
    return coordinate_ranges, group_summaries, sample_rows, validation


@app.cell
def _(conversions, coordinate_ranges, group_summaries, mo, sample_rows, validation):
    lines = [
        "## Conversion summary",
        "",
        f"Validated **{len(validation)} Arrow files** with "
        f"**{sum(row['rows'] for row in validation):,} genomic beads** in total.",
        "",
        "| Group | Structures | Rows/model | Total beads | Removed padding rows |",
        "|---|---:|---:|---:|---:|",
    ]
    for _row in group_summaries:
        lines.append(
            f"| {_row['group']} | {_row['structures']} | {_row['rows_min']}–{_row['rows_max']} "
            f"| {_row['total_beads']:,} | {_row['zero_padding_rows']} |"
        )
    if coordinate_ranges:
        lines.extend(["", "Global coordinate ranges (published relative units):", ""])
        for _axis, (_minimum, _maximum) in coordinate_ranges.items():
            lines.append(f"- **{_axis}**: {_minimum:.6g} to {_maximum:.6g}")
        lines.extend(["", "First three rows of the first selected output:", "", "```", str(sample_rows), "```"])
    else:
        lines.append("No structures selected; set `MAX_STRUCTURES` to a positive integer or `None`.")
    summary = "\n".join(lines)
    print(summary)
    mo.md(summary)
    return (summary,)


@app.cell
def _(mo):
    mo.md(
        """
        ## Caveats

        - Coordinates are relative RPR embeddings, not physical distances; no rescaling,
          recentering, or other coordinate transformation is performed.
        - The paper identifies **mm10**. `chr` and `coord` are filled for every row.
        - Both homologs remain in one file and share chromosome/position labels. Use
          `copy_index` to separate copies; their original indices are not assigned new
          parental labels by this conversion.
        - Female cells contain two X copies; male cells contain one X and one Y. Do not
          assume two copies of every sex chromosome.
        - The archive's extra `8cell/cell8_126.csv` lacks a sex directory. Its inferred
          sex and that inference's basis are recorded in schema metadata.
        """
    )
    return


if __name__ == "__main__":
    app.run()
