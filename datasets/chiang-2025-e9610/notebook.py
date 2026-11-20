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
        r"""
        # Chiang et al. (2025): simulated chromatin snapshots to Arrow

        Convert the eight XYZ snapshots in [Edinburgh DataShare ds/7942](https://doi.org/10.7488/ds/7942)
        accompanying **“Bridging-Induced Phase Separation and Loop Extrusion Drive
        Noise in Chromatin Transcription”** ([paper DOI](https://doi.org/10.1103/bjq4-xnsy)).
        Each output is one structure in Apache Arrow IPC format, readable by uchimata.

        These are coarse-grained simulated polymers, not structures of reference-genome
        loci. Coordinates are copied unchanged; their units are not specified by the deposit.
        """
    )
    return


@app.cell
def _():
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    OUT_DIR = BASE_DIR / "out"
    DATA_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    # Set to a small integer to try only the first N structures; None converts all eight.
    MAX_STRUCTURES = None
    return BASE_DIR, DATA_DIR, MAX_STRUCTURES, OUT_DIR


@app.cell
def _(DATA_DIR, mo):
    # Immutable DataShare bitstream URLs avoid downloading the 119 MB code archive
    # or the movies. Expected byte sizes also catch incomplete cached downloads.
    DOWNLOADS = {
        "README": (
            "https://datashare.ed.ac.uk/bitstreams/e1f94d44-d8b4-4843-bbb6-e207ab6c7d43/download",
            3_408,
        ),
        "fig1.tar.gz": (
            "https://datashare.ed.ac.uk/bitstreams/0b2c8886-fd79-41a4-9ee0-e30ca0821c5b/download",
            24_239,
        ),
        "sfig1.tar.gz": (
            "https://datashare.ed.ac.uk/bitstreams/032e3164-9eee-4cfd-ad27-ff136bd8e29f/download",
            38_309,
        ),
        "sfig4.tar.gz": (
            "https://datashare.ed.ac.uk/bitstreams/b6a19665-a77e-42a8-9c3a-2de508d45871/download",
            20_185,
        ),
        "sfig10.tar.gz": (
            "https://datashare.ed.ac.uk/bitstreams/31f17730-a6c4-4699-b03b-ff6d12f30940/download",
            57_776,
        ),
    }
    ARCHIVES = tuple(name for name in DOWNLOADS if name.endswith(".tar.gz"))

    mo.md(
        f"""
        ## Download the source files

        Four figure archives plus the deposit README are downloaded to `{DATA_DIR.name}/`.
        Existing files with the expected sizes are reused. The total download is about
        141 KiB. The other figure archives contain plotting data, not XYZ snapshots;
        `code.tar.gz` and `movies.tar.gz` are not needed.
        """
    )
    return ARCHIVES, DOWNLOADS


@app.cell
def _():
    import os
    import shutil
    from urllib.request import Request, urlopen

    def download_file(url, destination, expected_size):
        """Download atomically, or reuse a complete file already in data/."""
        if destination.exists():
            actual_size = destination.stat().st_size
            if actual_size != expected_size:
                raise ValueError(
                    f"Cached {destination} has {actual_size} bytes; expected {expected_size}. "
                    "Delete it and run this cell again."
                )
            return "cached"

        request = Request(url, headers={"User-Agent": "chiang-2025-arrow-converter/1.0"})
        temporary = destination.with_suffix(destination.suffix + ".part")
        try:
            with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            actual_size = temporary.stat().st_size
            if actual_size != expected_size:
                raise ValueError(
                    f"Downloaded {destination.name} has {actual_size} bytes; "
                    f"expected {expected_size}."
                )
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return "downloaded"

    return (download_file,)


@app.cell
def _(DATA_DIR, DOWNLOADS, download_file):
    download_status = []
    for filename, (url, expected_size) in DOWNLOADS.items():
        status = download_file(url, DATA_DIR / filename, expected_size)
        download_status.append({"file": filename, "bytes": expected_size, "status": status})
    download_status
    return (download_status,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Discover and interpret the snapshots

        The XYZ header gives the total particle count and timestep. Every following row is
        `element x y z`. The deposit README defines **H** (inert chromatin), **He**
        (transcription-unit chromatin), and **B** (loop-extrusion anchor) as chromatin;
        **Li**, **Be**, and **C** are TF particles, patches, or cores. Chromatin is the
        leading block and TF particles form the suffix, so conversion stops at the first
        TF particle and checks that no chromatin occurs later.

        The source row order is retained as zero-based `bead_index`. Original H/He/B symbols
        are retained in `bead_type`. `chr` and `coord` are deliberately omitted: there is no
        chromosome, assembly, base-pair position, or bead-to-bp resolution to put in them.
        Timestep and provenance are stored as Arrow schema metadata.
        """
    )
    return


@app.cell
def _():
    import io
    import math
    import re
    import tarfile

    import pyarrow as pa

    CHROMATIN_TYPES = frozenset({"H", "He", "B"})
    TF_TYPES = frozenset({"Li", "Be", "C"})

    def discover_snapshots(data_dir, archive_names):
        snapshots = []
        for archive_name in archive_names:
            with tarfile.open(data_dir / archive_name, mode="r:gz") as archive:
                for member in archive.getmembers():
                    if member.isfile() and member.name.endswith(".xyz"):
                        snapshots.append((archive_name, member.name))
        return sorted(snapshots)

    def read_xyz(archive_path, member_name):
        with tarfile.open(archive_path, mode="r:gz") as archive:
            extracted = archive.extractfile(member_name)
            if extracted is None:
                raise ValueError(f"Cannot read {member_name} from {archive_path}")
            with io.TextIOWrapper(extracted, encoding="utf-8") as stream:
                total_atoms = int(stream.readline().strip())
                timestep_line = stream.readline().strip()
                match = re.fullmatch(r"Atoms\. Timestep:\s*(\d+)", timestep_line)
                if match is None:
                    raise ValueError(f"Unexpected XYZ timestep line: {timestep_line!r}")
                timestep = int(match.group(1))

                atoms = []
                for row_number in range(total_atoms):
                    line = stream.readline()
                    fields = line.split()
                    if len(fields) != 4:
                        raise ValueError(
                            f"Bad atom row {row_number + 1} in {member_name}: {line!r}"
                        )
                    bead_type = fields[0]
                    if bead_type not in CHROMATIN_TYPES | TF_TYPES:
                        raise ValueError(f"Unknown bead type {bead_type!r} in {member_name}")
                    xyz = tuple(float(value) for value in fields[1:])
                    if not all(math.isfinite(value) for value in xyz):
                        raise ValueError(f"Non-finite coordinate in {member_name}")
                    atoms.append((bead_type, *xyz))
                if stream.read().strip():
                    raise ValueError(f"Extra rows after declared atom count in {member_name}")

        first_tf = next(
            (index for index, atom in enumerate(atoms) if atom[0] in TF_TYPES),
            len(atoms),
        )
        chromatin = atoms[:first_tf]
        if any(atom[0] in CHROMATIN_TYPES for atom in atoms[first_tf:]):
            raise ValueError(f"Chromatin is not one leading block in {member_name}")
        if not chromatin:
            raise ValueError(f"No chromatin beads in {member_name}")
        return timestep, total_atoms, chromatin, len(atoms) - len(chromatin)

    def convert_snapshot(data_dir, out_dir, archive_name, member_name):
        timestep, total_atoms, chromatin, tf_count = read_xyz(
            data_dir / archive_name, member_name
        )
        name = Path(member_name).stem
        metadata = {
            b"paper_doi": b"10.1103/bjq4-xnsy",
            b"dataset_doi": b"10.7488/ds/7942",
            b"source_archive": archive_name.encode(),
            b"source_member": member_name.encode(),
            b"timestep": str(timestep).encode(),
            b"total_particle_count": str(total_atoms).encode(),
            b"chromatin_bead_count": str(len(chromatin)).encode(),
            b"excluded_tf_particle_count": str(tf_count).encode(),
            b"coordinate_units": b"unspecified in source deposit",
            b"bead_index": b"zero-based index within the leading chromatin block",
        }
        schema = pa.schema(
            [
                pa.field("x", pa.float64(), nullable=False),
                pa.field("y", pa.float64(), nullable=False),
                pa.field("z", pa.float64(), nullable=False),
                pa.field("bead_type", pa.string(), nullable=False),
                pa.field("bead_index", pa.int64(), nullable=False),
            ],
            metadata=metadata,
        )
        table = pa.Table.from_arrays(
            [
                pa.array([atom[axis] for atom in chromatin], type=pa.float64())
                for axis in (1, 2, 3)
            ]
            + [
                pa.array([atom[0] for atom in chromatin], type=pa.string()),
                pa.array(range(len(chromatin)), type=pa.int64()),
            ],
            schema=schema,
        )

        destination = out_dir / f"{name}.arrow"
        temporary = destination.with_suffix(".arrow.tmp")
        try:
            with pa.ipc.new_file(temporary, table.schema) as writer:
                writer.write_table(table)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return {
            "structure": name,
            "source": f"{archive_name}:{member_name}",
            "timestep": timestep,
            "all_particles": total_atoms,
            "chromatin_rows": len(chromatin),
            "excluded_tf_particles": tf_count,
            "arrow_file": destination,
        }

    return CHROMATIN_TYPES, TF_TYPES, convert_snapshot, discover_snapshots, pa, read_xyz


@app.cell
def _(ARCHIVES, DATA_DIR, MAX_STRUCTURES, OUT_DIR, convert_snapshot, discover_snapshots):
    if MAX_STRUCTURES is not None and (
        not isinstance(MAX_STRUCTURES, int) or MAX_STRUCTURES < 0
    ):
        raise ValueError("MAX_STRUCTURES must be None or a non-negative integer")
    snapshots = discover_snapshots(DATA_DIR, ARCHIVES)
    selected_snapshots = (
        snapshots if MAX_STRUCTURES is None else snapshots[:MAX_STRUCTURES]
    )
    output_names = [Path(member).stem for _, member in selected_snapshots]
    if len(output_names) != len(set(output_names)):
        raise ValueError("Snapshot names collide; choose unique Arrow output names")

    conversions = [
        convert_snapshot(DATA_DIR, OUT_DIR, archive_name, member_name)
        for archive_name, member_name in selected_snapshots
    ]
    conversions
    return conversions, selected_snapshots, snapshots


@app.cell
def _(MAX_STRUCTURES, conversions, mo, snapshots):
    mo.vstack(
        [
            mo.md(
                f"Discovered **{len(snapshots)}** XYZ structures; converted "
                f"**{len(conversions)}** (MAX_STRUCTURES={MAX_STRUCTURES!r})."
            ),
            mo.ui.table(
                [
                    {key: str(value) for key, value in record.items()}
                    for record in conversions
                ]
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Validate the Arrow files

        Read every result back with Arrow IPC, check its required coordinate types and row
        count, and calculate coordinate ranges. Only chromatin rows should remain. The source
        files are not modified, and extracting tar members to disk is unnecessary.
        """
    )
    return


@app.cell
def _(conversions, pa):
    import numpy as np

    validation = []
    for record in conversions:
        path = record["arrow_file"]
        with pa.ipc.open_file(path) as reader:
            table = reader.read_all()
        for column in ("x", "y", "z"):
            if table.schema.field(column).type != pa.float64():
                raise TypeError(f"{path.name}: {column} is not float64")
        if table.num_rows != record["chromatin_rows"]:
            raise ValueError(f"{path.name}: row count does not match conversion")
        if "chr" in table.column_names or "coord" in table.column_names:
            raise ValueError(f"{path.name}: genomic columns should be absent")
        if table.schema.metadata[b"timestep"] != str(record["timestep"]).encode():
            raise ValueError(f"{path.name}: timestep metadata does not match source")

        ranges = {}
        for column in ("x", "y", "z"):
            values = table[column].to_numpy(zero_copy_only=False)
            if not np.isfinite(values).all():
                raise ValueError(f"{path.name}: non-finite {column} coordinates")
            ranges[column] = (float(values.min()), float(values.max()))
        validation.append(
            {
                "file": path.name,
                "rows": table.num_rows,
                "columns": ", ".join(table.column_names),
                "x_range": ranges["x"],
                "y_range": ranges["y"],
                "z_range": ranges["z"],
                "timestep": record["timestep"],
            }
        )
    validation
    return np, validation


@app.cell
def _(mo, validation):
    mo.vstack(
        [
            mo.md(
                f"Validated **{len(validation)}** Arrow files containing "
                f"**{sum(row['rows'] for row in validation):,}** chromatin beads in total."
            ),
            mo.ui.table(validation),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
