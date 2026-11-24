# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "pyarrow", "numpy", "remotezip"]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Minimal-cell chromosome structures to Arrow

        This notebook converts the chromosome configurations deposited for
        **Maytin, Gilbert & Luthey-Schulten, “Chromosome segregation in a
        minimal bacterial cell driven by SMC protein complexes”**
        (*Protein Science*, 2026, [10.1002/pro.70604](https://doi.org/10.1002/pro.70604)).
        The source is [Zenodo record 19959420](https://doi.org/10.5281/zenodo.19959420),
        published under CC BY 4.0.

        The record's 22.85 GB ZIP contains seven 3.08–3.71 GB `tar.gz` run
        archives. We use HTTP range requests and stream each nested archive
        only until the requested chromosome files have been read. The outer
        ZIP, the run archives, LAMMPS trajectories, and ribosome coordinates
        are never saved locally.
        """
    )
    return


@app.cell
def _():
    from pathlib import Path

    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    OUT_DIR = BASE_DIR / "out"
    DATA_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    # For a quick trial, use 2: the first two configurations stored in each
    # archive. None discovers and converts every initial configuration and
    # every dna_<run>_<minute>.bin snapshot in all seven archives.
    MAX_STRUCTURES_PER_RUN = None

    RUN_NAMES = (
        "Mar03_p9",   # N=20 SMC, v=500 bp/s, tau=100 s
        "Mar03_p21",  # N=50, v=200 bp/s, tau=100 s
        "Mar06_1",    # N=50, v=100 bp/s, tau=200 s
        "Mar06_2",    # N=5, v=500 bp/s, tau=400 s
        "Feb16_p12",  # no swelling
        "Feb03_1",    # topoisomerase after SMC looping
        "Feb03_2",    # no topoisomerase
    )
    SOURCE_URL = (
        "https://zenodo.org/api/records/19959420/files/"
        "protein_science_zenodo.zip/content"
    )
    N_PARENT = 54_338
    BP_PER_BEAD = 10
    CHROMOSOME = "JCVI-syn3A"

    return (
        BASE_DIR,
        BP_PER_BEAD,
        CHROMOSOME,
        DATA_DIR,
        MAX_STRUCTURES_PER_RUN,
        N_PARENT,
        OUT_DIR,
        RUN_NAMES,
        SOURCE_URL,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Download and decode selected members

        The simulation scripts (`load_mono_coords:...,row`) and the authors'
        analysis code establish that each `.bin` file is native float64 data
        in `[x1, y1, z1, x2, y2, z2, ...]` order. We explicitly decode it as
        little-endian `<f8` (the format on the machines that produced it).
        Files are cached under `data/<run>/`; existing complete files are
        reused without being extracted again. Output is written atomically to
        `out/*.arrow`. A fresh scan can still transfer compressed bytes while
        skipping through a gzip stream, even for a member already cached.

        Each archive also contains an `x_chain_...bin` initial chromosome.
        Both that input configuration and the time-series `dna_...bin` files
        are converted. Archive members are not in chronological order: with a
        small limit, the time-series example is the first one stored in each
        tar archive, not necessarily minute zero.
        """
    )
    return


@app.cell
def _(
    BP_PER_BEAD,
    CHROMOSOME,
    DATA_DIR,
    N_PARENT,
    OUT_DIR,
):
    import os
    import re
    import shutil
    import tarfile
    from pathlib import PurePosixPath

    import numpy as np
    import pyarrow as pa
    import pyarrow.ipc as ipc

    def genomic_starts(n_beads):
        """Map original and newly replicated beads to 0-based reference starts.

        The first 54,338 beads retain parental bead order. The authors'
        compute_partitioning.py defines N_repl = N - 54,338 and places the
        appended daughter beads symmetrically about 0-based parental index
        27,168. This is the same ordering used by the replication-fork files.
        """
        if not 0 < n_beads <= 2 * N_PARENT:
            raise ValueError(f"Unexpected DNA bead count: {n_beads}")
        indices = np.arange(n_beads, dtype=np.int64)
        n_replicated = n_beads - N_PARENT
        if n_replicated:
            left_start = 27_168 - (n_replicated - 1) // 2
            indices[N_PARENT:] = np.arange(
                left_start, left_start + n_replicated, dtype=np.int64
            )
        return indices * BP_PER_BEAD

    def write_arrow(bin_path, arrow_path):
        values = np.fromfile(bin_path, dtype="<f8")
        if values.size == 0 or values.size % 3:
            raise ValueError(f"Not a nonempty xyz float64 file: {bin_path}")
        xyz = values.reshape(-1, 3)
        if not np.isfinite(xyz).all():
            raise ValueError(f"Non-finite coordinate in {bin_path}")

        table = pa.Table.from_arrays(
            [
                pa.array(xyz[:, 0], type=pa.float64()),
                pa.array(xyz[:, 1], type=pa.float64()),
                pa.array(xyz[:, 2], type=pa.float64()),
                pa.array(np.full(len(xyz), CHROMOSOME), type=pa.string()),
                pa.array(genomic_starts(len(xyz)), type=pa.int64()),
            ],
            names=["x", "y", "z", "chr", "coord"],
        )
        temporary = arrow_path.with_suffix(".tmp")
        try:
            with ipc.new_file(str(temporary), table.schema) as writer:
                writer.write_table(table)
            os.replace(temporary, arrow_path)
        finally:
            temporary.unlink(missing_ok=True)

    def save_member(tar, member, destination, expected_size):
        temporary = destination.with_suffix(destination.suffix + ".part")
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = tar.extractfile(member)
        if source is None:
            raise OSError(f"Cannot read tar member {member.name}")
        try:
            with source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            if temporary.stat().st_size != expected_size:
                raise OSError(f"Short read for {member.name}")
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

    def summarize(path, run, timepoint, status):
        with ipc.open_file(str(path)) as reader:
            table = reader.read_all()
        n = table.num_rows
        row = {
            "file": path.name,
            "run": run,
            "minute": "initial" if timepoint is None else timepoint,
            "rows": n,
            "replicated_beads": max(0, n - N_PARENT),
            "status": status,
            "coord_range": (
                int(table["coord"].to_numpy().min()),
                int(table["coord"].to_numpy().max()),
            ),
        }
        for axis in ("x", "y", "z"):
            values = table[axis].to_numpy(zero_copy_only=False)
            row[f"{axis}_range"] = (float(values.min()), float(values.max()))
        return row

    def process_run(remote_zip, run, limit):
        """Stream one nested tar.gz and return summaries of selected structures."""
        archive_name = f"protein_science_zenodo/runs/{run}.tar.gz"
        dna_pattern = re.compile(rf"dna_{re.escape(run)}_(\d+)\.bin")
        initial_pattern = re.compile(
            r"x_chain_Syn3A_chromosome_init_rep\d+\.bin"
        )
        results = []
        entered_coords = False

        with remote_zip.open(archive_name) as compressed:
            with tarfile.open(fileobj=compressed, mode="r|gz") as tar:
                for member in tar:
                    in_coords = "/coords/" in member.name
                    if in_coords:
                        entered_coords = True
                    elif entered_coords and limit is None:
                        # tar stores this directory contiguously. Do not stream
                        # the much larger LAMMPS files that follow it.
                        break
                    if limit is not None and len(results) >= limit:
                        break
                    if not member.isfile() or not in_coords:
                        continue

                    basename = PurePosixPath(member.name).name
                    match = dna_pattern.fullmatch(basename)
                    if match:
                        timepoint = int(match.group(1))
                        output_name = f"{run}_minute_{timepoint:03d}.arrow"
                    elif initial_pattern.fullmatch(basename):
                        timepoint = None
                        output_name = f"{run}_initial.arrow"
                    else:
                        continue  # ribosomes and unrelated coordinate files

                    destination = DATA_DIR / run / basename
                    arrow_path = OUT_DIR / output_name
                    if arrow_path.exists():
                        try:
                            results.append(
                                summarize(arrow_path, run, timepoint, "existing Arrow")
                            )
                            continue
                        except Exception:
                            arrow_path.unlink()  # replace a partial/corrupt output

                    if destination.exists() and destination.stat().st_size != member.size:
                        destination.unlink()
                    if destination.exists():
                        status = "cached binary"
                    else:
                        print(f"Downloading {member.name} ({member.size:,} bytes)")
                        save_member(tar, member, destination, member.size)
                        status = "downloaded"
                    write_arrow(destination, arrow_path)
                    results.append(summarize(arrow_path, run, timepoint, status))
                    print(f"Wrote {arrow_path.name}: {member.size // 24:,} beads")

        if not results and limit != 0:
            raise RuntimeError(f"No selected chromosome structures found in {archive_name}")
        return results

    return np, process_run


@app.cell
def _(mo):
    mo.md(
        """
        ## Genomic coordinates and Arrow schema

        Coordinates are retained exactly as published (simulation length units
        are ångströms). Each parental bead represents 10 bp: bead `i` receives
        `coord = 10*i`, for `i = 0..54337`, and all rows receive
        `chr = "JCVI-syn3A"`. Appended replicated beads share the reference
        starts of their parental copies. This follows the midpoint formula in
        the deposited `analysis/compute_partitioning.py`; at full replication
        the appended 54,338 beads therefore run again from 0 to 543,370 bp.
        `coord` is a **reference-genome start**, not a unique bead identifier,
        so duplicated loci intentionally have the same value.

        Each structure becomes one Arrow IPC file with `x`, `y`, `z`
        (`float64`), `chr` (`string`), and `coord` (`int64`). IPC files are
        opened again below to calculate the validation summary.
        """
    )
    return


@app.cell
def _(MAX_STRUCTURES_PER_RUN, RUN_NAMES, SOURCE_URL, mo, process_run):
    from remotezip import RemoteZip

    results = []
    with RemoteZip(SOURCE_URL) as remote_zip:
        for run_name in RUN_NAMES:
            print(f"Processing {run_name}")
            results.extend(
                process_run(remote_zip, run_name, MAX_STRUCTURES_PER_RUN)
            )
    print(f"Available Arrow outputs from this selection: {len(results)}")
    return (results,)


@app.cell
def _(mo, np, results):
    if not results:
        summary = mo.md("No structures selected.")
    else:
        xyz = np.array(
            [[row[f"{axis}_range"] for axis in "xyz"] for row in results],
            dtype=float,
        )
        lines = [
            f"**{len(results)} Arrow files**, "
            f"{sum(row['rows'] for row in results):,} rows in total.  ",
            f"Global x/y/z minima: **{xyz[:, :, 0].min(axis=0).round(3)}**; "
            f"global maxima: **{xyz[:, :, 1].max(axis=0).round(3)}**.  ",
            "`chr` and `coord` are filled in every file.",
            "",
            "| Arrow file | minute | rows | replicated beads | status |",
            "|---|---:|---:|---:|---|",
        ]
        lines.extend(
            f"| {row['file']} | {row['minute']} | {row['rows']:,} | "
            f"{row['replicated_beads']:,} | {row['status']} |"
            for row in results
        )
        summary = mo.md("\n".join(lines))
        print("\n".join(lines[:3]))
        for row in results:
            print(
                row["file"], row["rows"],
                {axis: row[f"{axis}_range"] for axis in "xyz"},
                row["coord_range"],
            )
    summary
    return


if __name__ == "__main__":
    app.run()
