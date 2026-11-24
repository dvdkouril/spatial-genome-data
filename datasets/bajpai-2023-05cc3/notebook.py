# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pyarrow",
# ]
# ///

import marimo

app = marimo.App()


@app.cell
def _():
    import hashlib
    import shutil
    from pathlib import Path
    from urllib.request import urlopen
    from zipfile import ZipFile

    import marimo as mo
    import numpy as np
    import pyarrow as pa

    return Path, ZipFile, hashlib, mo, np, pa, shutil, urlopen


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # Bajpai & Safran chromosome-mixing models

        Convert the three LAMMPS configurations deposited with **“Mesoscale,
        long-time mixing of chromosomes and its connection to polymer dynamics”**
        ([paper](https://doi.org/10.1371/journal.pcbi.1011142),
        [data](https://zenodo.org/record/7557330)) to Arrow IPC files.

        Each configuration is one 3D structure, not a trajectory. The generic
        homopolymer and two *Drosophila* block-copolymer configurations each
        contain 35,240 chromatin beads. Coordinates remain in the published,
        dimensionless LAMMPS `lj` units.
        """
    )
    return


@app.cell
def _(Path):
    NOTEBOOK_DIR = Path(__file__).resolve().parent
    DATA_DIR = NOTEBOOK_DIR / "data"
    OUT_DIR = NOTEBOOK_DIR / "out"
    DATA_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    # Set to a small integer to convert only the first N structures.
    MAX_STRUCTURES = None
    BEAD_SIZE_BP = 5_000

    DOWNLOAD_URL = (
        "https://zenodo.org/api/records/7557330/files/"
        "Supporting_data.zip/content"
    )
    EXPECTED_ARCHIVE_SIZE = 269_924_705
    EXPECTED_ARCHIVE_MD5 = "f1c6f88d695facbb1904cfdaecb30322"

    return (
        BEAD_SIZE_BP,
        DATA_DIR,
        DOWNLOAD_URL,
        EXPECTED_ARCHIVE_MD5,
        EXPECTED_ARCHIVE_SIZE,
        MAX_STRUCTURES,
        OUT_DIR,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Download and unpack the model files

        `Supporting_data.zip` is 269,924,705 bytes (257 MiB). Download it only
        if absent and check its published size and MD5. Only the three small
        `.data` configurations and their three input scripts are unpacked; the
        six simulation videos remain in the archive. Existing extracted files
        with the expected sizes are reused.
        """
    )
    return


@app.cell
def _(
    DATA_DIR,
    DOWNLOAD_URL,
    EXPECTED_ARCHIVE_MD5,
    EXPECTED_ARCHIVE_SIZE,
    Path,
    ZipFile,
    hashlib,
    shutil,
    urlopen,
):
    archive_path = DATA_DIR / "Supporting_data.zip"

    def file_md5(path):
        digest = hashlib.md5()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    if not archive_path.exists():
        partial_path = archive_path.with_suffix(".zip.part")
        print("Downloading Supporting_data.zip (269,924,705 bytes) ...")
        with urlopen(DOWNLOAD_URL) as response, partial_path.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        partial_path.replace(archive_path)
    else:
        print(f"Reusing {archive_path}")

    assert archive_path.stat().st_size == EXPECTED_ARCHIVE_SIZE, (
        "Unexpected archive size; delete the partial or corrupt file and retry"
    )
    assert file_md5(archive_path) == EXPECTED_ARCHIVE_MD5, (
        "Archive checksum mismatch; delete the corrupt file and retry"
    )

    with ZipFile(archive_path) as archive:
        model_files = [
            item
            for item in archive.infolist()
            if item.filename.endswith((".data", ".in"))
        ]
        assert len(model_files) == 6
        for item in model_files:
            destination = DATA_DIR / item.filename
            assert destination.resolve().is_relative_to(DATA_DIR.resolve())
            if not (
                destination.exists()
                and destination.stat().st_size == item.file_size
            ):
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)

    input_root = (
        DATA_DIR / "Supporting_data" / "LAMMPS_script_chromsomes_mixing"
    )
    print(f"Extracted {len(model_files)} model/script files under {input_root}")
    return archive_path, input_root


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Interpret atom IDs as 5 kb model bins

        The paper specifies **5 kb per bead**. In both block-copolymer models,
        atom-ID ranges correspond to Chr2 (1–12,100), Chr3 (12,101–25,860),
        Chr4 (25,861–26,760), and ChrX (26,761–35,240). The generic model has
        four equal, synthetic chains (`chr1`–`chr4`), each with 8,810 beads.
        `coord` is therefore the zero-based start of each modeled 5 kb bin;
        these are model-grid positions, not alignments to a named assembly.

        Atoms are shuffled in the text files, so sort by atom ID. The parser
        also verifies that every chain bond joins consecutive IDs. In the lamin
        setup, exclude only type 11 (19,600 lamina particles); type-12 LAD
        beads are chromatin and are retained. Atom-ID ranges, not molecule IDs,
        determine chromosome membership because LADs have a separate molecule
        ID in that file.
        """
    )
    return


@app.cell
def _(input_root):
    generic_chromosomes = (
        ("chr1", 1, 8_810),
        ("chr2", 8_811, 17_620),
        ("chr3", 17_621, 26_430),
        ("chr4", 26_431, 35_240),
    )
    drosophila_chromosomes = (
        ("chr2", 1, 12_100),
        ("chr3", 12_101, 25_860),
        ("chr4", 25_861, 26_760),
        ("chrX", 26_761, 35_240),
    )

    STRUCTURES = [
        {
            "name": "generic_homopolymer",
            "path": input_root
            / "Generic_model"
            / "system_initial_4chrom_homopolymer.data",
            "chromosomes": generic_chromosomes,
            "excluded_types": frozenset(),
            "allowed_chromatin_types": frozenset({1, 2, 3, 4}),
        },
        {
            "name": "block_copolymer_without_lamin",
            "path": input_root
            / "Block_copolymer_model"
            / "Without_lamin"
            / "system_initial_euhet.data",
            "chromosomes": drosophila_chromosomes,
            "excluded_types": frozenset(),
            "allowed_chromatin_types": frozenset({1, 2}),
        },
        {
            "name": "block_copolymer_with_lamin",
            "path": input_root
            / "Block_copolymer_model"
            / "With_lamin"
            / "system_added_lamin.data",
            "chromosomes": drosophila_chromosomes,
            "excluded_types": frozenset({11}),
            "allowed_chromatin_types": frozenset({1, 2, 12}),
        },
    ]
    return STRUCTURES, drosophila_chromosomes, generic_chromosomes


@app.cell
def _(np, pa):
    def read_lammps_full(path):
        """Read Atoms and Bonds sections from an atom_style full data file."""
        atoms = []
        bonds = []
        section = None
        section_headers = {
            "Masses",
            "Pair Coeffs",
            "Bond Coeffs",
            "Angle Coeffs",
            "Atoms",
            "Velocities",
            "Bonds",
            "Angles",
            "Dihedrals",
            "Impropers",
        }
        with path.open(encoding="utf-8") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.split("#", 1)[0].strip()
                if not line:
                    continue
                if line in section_headers:
                    section = line
                    continue
                fields = line.split()
                if section == "Atoms":
                    if len(fields) != 10:
                        raise ValueError(
                            f"{path}:{line_number}: expected 10 atom_style full "
                            f"fields (including image flags), found {len(fields)}"
                        )
                    atoms.append(
                        (
                            int(fields[0]),
                            int(fields[1]),
                            int(fields[2]),
                            float(fields[4]),
                            float(fields[5]),
                            float(fields[6]),
                        )
                    )
                elif section == "Bonds":
                    if len(fields) != 4:
                        raise ValueError(
                            f"{path}:{line_number}: malformed bond row"
                        )
                    bonds.append((int(fields[2]), int(fields[3])))
        return sorted(atoms), bonds

    def convert_structure(spec, out_dir, bead_size_bp):
        atoms, bonds = read_lammps_full(spec["path"])
        chromatin = [
            atom for atom in atoms if atom[2] not in spec["excluded_types"]
        ]
        excluded_count = len(atoms) - len(chromatin)

        unexpected_types = {atom[2] for atom in chromatin} - spec[
            "allowed_chromatin_types"
        ]
        assert not unexpected_types, f"Unexpected atom types: {unexpected_types}"

        expected_atoms = {
            atom_id
            for _, first, last in spec["chromosomes"]
            for atom_id in range(first, last + 1)
        }
        observed_ids = [atom[0] for atom in chromatin]
        assert len(observed_ids) == len(set(observed_ids)), "Duplicate atom IDs"
        assert set(observed_ids) == expected_atoms, (
            "Chromatin atom IDs do not match the documented chromosome ranges"
        )

        expected_bonds = {
            (atom_id, atom_id + 1)
            for _, first, last in spec["chromosomes"]
            for atom_id in range(first, last)
        }
        observed_bonds = {tuple(sorted(bond)) for bond in bonds}
        assert len(observed_bonds) == len(bonds), "Duplicate bonds"
        assert observed_bonds == expected_bonds, (
            "Bond topology is not four sequential chromosome chains"
        )

        ordered_atoms = []
        chromosome_values = []
        coord_values = np.empty(len(chromatin), dtype=np.int64)
        chromosome_counts = {}
        offset = 0
        for chromosome, first, last in spec["chromosomes"]:
            group = [atom for atom in chromatin if first <= atom[0] <= last]
            assert [atom[0] for atom in group] == list(range(first, last + 1))
            ordered_atoms.extend(group)
            chromosome_values.extend([chromosome] * len(group))
            count = last - first + 1
            coord_values[offset : offset + count] = (
                np.arange(count, dtype=np.int64) * bead_size_bp
            )
            chromosome_counts[chromosome] = count
            offset += count
        assert len(ordered_atoms) == len(chromatin)

        schema = pa.schema(
            [
                pa.field("x", pa.float64()),
                pa.field("y", pa.float64()),
                pa.field("z", pa.float64()),
                pa.field("chr", pa.string()),
                pa.field("coord", pa.int64()),
            ],
            metadata={
                b"source": spec["name"].encode(),
                b"coordinate_units": b"dimensionless LAMMPS lj (sigma)",
                b"genomic_coordinates": (
                    b"zero-based modeled 5 kb bin starts; no assembly alignment"
                ),
            },
        )
        table = pa.Table.from_arrays(
            [
                np.asarray([atom[3] for atom in ordered_atoms], dtype=np.float64),
                np.asarray([atom[4] for atom in ordered_atoms], dtype=np.float64),
                np.asarray([atom[5] for atom in ordered_atoms], dtype=np.float64),
                pa.array(chromosome_values, type=pa.string()),
                pa.array(coord_values, type=pa.int64()),
            ],
            schema=schema,
        )

        output_path = out_dir / f"{spec['name']}.arrow"
        with pa.OSFile(str(output_path), "wb") as sink:
            with pa.ipc.new_file(sink, table.schema) as writer:
                writer.write_table(table)

        # Read the finished IPC file back and check its shape, schema and values.
        with pa.ipc.open_file(str(output_path)) as reader:
            written = reader.read_all()
        assert written.schema == table.schema
        assert written.num_rows == len(chromatin)
        for column in ("x", "y", "z"):
            assert np.isfinite(written[column].to_numpy()).all()

        summary = {
            "structure": spec["name"],
            "file": output_path.name,
            "rows": written.num_rows,
            "chromosome_counts": chromosome_counts,
            "excluded_lamina_beads": excluded_count,
            **{
                f"{column}_range": [
                    float(written[column].to_numpy().min()),
                    float(written[column].to_numpy().max()),
                ]
                for column in ("x", "y", "z")
            },
        }
        return output_path, summary

    return convert_structure, read_lammps_full


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Write and verify Arrow IPC

        Each structure becomes one file in `out/`, with columns `x`, `y`, `z`
        (float64), `chr` (string), and `coord` (int64), in chromosome/atom-ID
        order. Finished files are read back to check their schemas and values.
        """
    )
    return


@app.cell
def _(
    BEAD_SIZE_BP,
    MAX_STRUCTURES,
    OUT_DIR,
    STRUCTURES,
    convert_structure,
):
    selected_structures = (
        STRUCTURES
        if MAX_STRUCTURES is None
        else STRUCTURES[:MAX_STRUCTURES]
    )
    conversion_summaries = []
    for spec in selected_structures:
        output_path, summary = convert_structure(spec, OUT_DIR, BEAD_SIZE_BP)
        conversion_summaries.append(summary)
        print(
            f"Wrote {output_path.name}: {summary['rows']:,} chromatin beads "
            f"({summary['excluded_lamina_beads']:,} lamina beads excluded)"
        )
    return conversion_summaries, selected_structures


@app.cell(hide_code=True)
def _(conversion_summaries, mo):
    lines = [
        "### Conversion summary",
        "",
        "| Structure | Rows | x range | y range | z range |",
        "|---|---:|---|---|---|",
    ]
    for _summary in conversion_summaries:
        ranges = [
            f"{_summary[f'{axis}_range'][0]:.3f} … "
            f"{_summary[f'{axis}_range'][1]:.3f}"
            for axis in ("x", "y", "z")
        ]
        lines.append(
            f"| {_summary['structure']} | {_summary['rows']:,} | "
            + " | ".join(ranges)
            + " |"
        )
    mo.md("\n".join(lines))
    return


if __name__ == "__main__":
    app.run()
