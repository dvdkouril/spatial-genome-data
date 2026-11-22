# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "marimo>=0.14.0",
#   "numpy>=2.0",
#   "pyarrow>=18.0",
# ]
# ///

import marimo

__generated_with = "0.14.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # Wu et al. (2025): single-cell Micro-C 3D genomes

        Convert the diploid GM12878 models in [GSE192759](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE192759)
        to one Apache Arrow IPC file per model. The associated paper is
        **Single-cell Micro-C profiles 3D genome structures at high resolution and
        characterizes multi-enhancer hubs**
        ([doi:10.1038/s41588-025-02247-6](https://doi.org/10.1038/s41588-025-02247-6)).
        GEO reports human hg38 data from 352 single-cell samples and 5, 10, and 20 kb models.

        **Size warning:** the supplementary tar.gz is 102,110,011,821 bytes
        (95.1 GiB). The archive has not been fully listed, so the total model count is
        unknown without reading all of it. Start with a small `MAX_STRUCTURES` below.
        """
    )
    return


@app.cell
def _():
    import contextlib
    import gzip
    import json
    import math
    import os
    import shutil
    import tarfile
    import urllib.request
    from pathlib import Path, PurePosixPath

    import numpy as np
    import pyarrow as pa
    import pyarrow.compute as pc

    # None means every .3dg model in archive order. Use 1 or 2 for a quick test.
    MAX_STRUCTURES = None
    OVERWRITE = False
    CHUNK_ROWS = 100_000

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    MEMBER_DIR = DATA_DIR / "members"
    OUT_DIR = BASE_DIR / "out"
    ARCHIVE_NAME = "GSE192759_5kb_10kb_20kb_3dg_files.tar.gz"
    ARCHIVE_URL = (
        "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE192nnn/"
        f"GSE192759/suppl/{ARCHIVE_NAME}"
    )
    LOCAL_ARCHIVE = DATA_DIR / ARCHIVE_NAME
    ARCHIVE_BYTES = 102_110_011_821
    MAX_MEMBER_BYTES = 5 * 1024**3

    DATA_DIR.mkdir(exist_ok=True)
    MEMBER_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    return (
        ARCHIVE_BYTES,
        ARCHIVE_NAME,
        ARCHIVE_URL,
        CHUNK_ROWS,
        DATA_DIR,
        LOCAL_ARCHIVE,
        MAX_MEMBER_BYTES,
        MAX_STRUCTURES,
        MEMBER_DIR,
        OUT_DIR,
        OVERWRITE,
        Path,
        PurePosixPath,
        contextlib,
        gzip,
        json,
        math,
        np,
        os,
        pa,
        pc,
        shutil,
        tarfile,
        urllib,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Acquire the archive members

        If `data/GSE192759_5kb_10kb_20kb_3dg_files.tar.gz` exists, the notebook reads
        that local file. Otherwise it opens an HTTPS stream and stops after
        `MAX_STRUCTURES`; it does **not** first download the whole 95.1 GiB archive.
        Selected inner gzip members are cached in `data/members/`, and existing members
        and Arrow outputs are reused. For an unrestricted run (`MAX_STRUCTURES = None`),
        a local archive is strongly recommended: streaming the remote source reads the
        entire 95.1 GiB and the Arrow outputs can require substantially more disk space.
        """
    )
    return


@app.cell
def _():
    @contextlib.contextmanager
    def open_archive():
        """Open the local archive or a bounded-by-MAX_STRUCTURES remote stream."""
        if LOCAL_ARCHIVE.exists():
            print(f"Reading local archive: {LOCAL_ARCHIVE}")
            with LOCAL_ARCHIVE.open("rb") as raw:
                with tarfile.open(fileobj=raw, mode="r|gz") as archive:
                    yield archive, "local archive"
            return

        print(f"Streaming {ARCHIVE_URL}")
        print(f"Remote archive size: {ARCHIVE_BYTES:,} bytes (95.1 GiB)")
        request = urllib.request.Request(
            ARCHIVE_URL, headers={"User-Agent": "wu-2025-arrow-converter/1.0"}
        )
        response = urllib.request.urlopen(request, timeout=120)
        try:
            with tarfile.open(fileobj=response, mode="r|gz") as archive:
                yield archive, "remote stream"
        finally:
            # With a finite MAX_STRUCTURES this closes the connection before the
            # rest of the very large archive is transferred.
            response.close()

    def cache_member(archive, member, destination):
        """Copy one nested, still-gzipped text member without unpacking the tar."""
        if destination.exists():
            print(f"  Using cached member ({destination.stat().st_size:,} bytes)")
            return
        if member.size > MAX_MEMBER_BYTES:
            raise ValueError(f"Refusing unexpected >5 GiB member: {member.name}")
        source = archive.extractfile(member)
        if source is None:
            raise OSError(f"Cannot read archive member: {member.name}")
        temporary = destination.with_name(destination.name + ".part")
        try:
            with source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            if temporary.stat().st_size != member.size:
                raise OSError(f"Incomplete download of {member.name}")
            os.replace(temporary, destination)
            print(f"  Cached {member.size:,} compressed bytes")
        finally:
            temporary.unlink(missing_ok=True)

    def read_3dg_metadata(path):
        chromosomes = {}
        unit = None
        other_headers = []
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.startswith("#"):
                    break
                header = line[1:].strip()
                if header.startswith("chromosome:"):
                    chrom, length = header.split(":", 1)[1].strip().rsplit(None, 1)
                    chromosomes[chrom] = int(length)
                elif header.startswith("unit:"):
                    unit = header.split(":", 1)[1].strip()
                else:
                    other_headers.append(header)
        return chromosomes, unit, other_headers

    def resolution_from_name(name):
        for token in name.split("_"):
            if token.endswith("kb") and token[:-2].isdigit():
                return int(token[:-2]) * 1000
        return None

    def write_3dg_arrow(source, destination, member_name):
        """Stream fixed-width text rows into chunked Arrow IPC record batches."""
        chromosomes, unit, other_headers = read_3dg_metadata(source)
        resolution = resolution_from_name(member_name)
        metadata = {
            b"source": ARCHIVE_URL.encode(),
            b"source_member": member_name.encode(),
            b"assembly": b"hg38",
            b"doi": b"10.1038/s41588-025-02247-6",
            b"coordinate_system": b"0-based genomic bin start, as published",
            b"haplotypes": (
                b"source labels retained in chr (a/b or (mat)/(pat))"
            ),
            b"chromosome_lengths": json.dumps(chromosomes).encode(),
        }
        if unit is not None:
            metadata[b"unit"] = unit.encode()
        if resolution is not None:
            metadata[b"resolution_bp"] = str(resolution).encode()
        if other_headers:
            metadata[b"other_headers"] = json.dumps(other_headers).encode()

        schema = pa.schema(
            [
                pa.field("x", pa.float64()),
                pa.field("y", pa.float64()),
                pa.field("z", pa.float64()),
                pa.field("chr", pa.string()),
                pa.field("coord", pa.int64()),
            ],
            metadata=metadata,
        )
        xs, ys, zs, chroms, coords = [], [], [], [], []
        rows = 0
        temporary = destination.with_name(destination.name + ".part")

        def write_chunk(writer):
            if not xs:
                return
            batch = pa.RecordBatch.from_arrays(
                [
                    pa.array(xs, type=pa.float64()),
                    pa.array(ys, type=pa.float64()),
                    pa.array(zs, type=pa.float64()),
                    pa.array(chroms, type=pa.string()),
                    pa.array(coords, type=pa.int64()),
                ],
                schema=schema,
            )
            writer.write_batch(batch)
            xs.clear()
            ys.clear()
            zs.clear()
            chroms.clear()
            coords.clear()

        try:
            with gzip.open(source, "rt", encoding="utf-8", newline="") as handle:
                with pa.OSFile(str(temporary), "wb") as sink:
                    with pa.ipc.new_file(sink, schema) as writer:
                        for line_number, line in enumerate(handle, start=1):
                            if not line.strip() or line.startswith("#"):
                                continue
                            fields = line.rstrip("\r\n").split("\t")
                            if len(fields) != 5:
                                raise ValueError(
                                    f"{member_name}:{line_number}: expected 5 tab-delimited "
                                    f"fields, found {len(fields)}"
                                )
                            chroms.append(fields[0])
                            coords.append(int(fields[1]))
                            xs.append(float(fields[2]))
                            ys.append(float(fields[3]))
                            zs.append(float(fields[4]))
                            rows += 1
                            if len(xs) >= CHUNK_ROWS:
                                write_chunk(writer)
                        write_chunk(writer)
            if rows == 0:
                raise ValueError(f"No coordinates in {member_name}")
            os.replace(temporary, destination)
            print(f"  Wrote {destination.name}: {rows:,} rows")
            return rows
        finally:
            temporary.unlink(missing_ok=True)

    def convert_structures():
        results = []
        seen_names = set()
        with open_archive() as (archive, source_kind):
            for member in archive:
                if not member.isfile() or not member.name.endswith(".3dg.txt.gz"):
                    continue
                if MAX_STRUCTURES is not None and len(results) >= MAX_STRUCTURES:
                    break
                name = PurePosixPath(member.name).name
                if name in seen_names:
                    raise ValueError(f"Duplicate member basename would overwrite output: {name}")
                seen_names.add(name)
                member_path = MEMBER_DIR / name
                output_name = name[: -len(".3dg.txt.gz")] + ".arrow"
                output_path = OUT_DIR / output_name
                print(f"[{len(results) + 1}] {name} ({member.size:,} compressed bytes)")
                if output_path.exists() and not OVERWRITE:
                    print(f"  Keeping existing {output_path.name}")
                    status = "existing"
                else:
                    cache_member(archive, member, member_path)
                    write_3dg_arrow(member_path, output_path, name)
                    status = "converted"
                results.append(
                    {"member": name, "path": output_path, "status": status}
                )
        if not results:
            raise RuntimeError("No .3dg.txt.gz structures found")
        print(f"Finished {len(results)} structure(s) from {source_kind}.")
        return results

    return (convert_structures,)


@app.cell
def _(convert_structures):
    conversion_results = convert_structures()
    return (conversion_results,)


@app.cell
def _(mo):
    mo.md(
        """
        ## Arrow mapping and validation

        Input columns are `chromosome`, `bin start`, `x`, `y`, `z`; output columns are
        `x`, `y`, `z` (`float64`), `chr` (`string`), and `coord` (`int64`). The original
        haplotype label (`chr1a`/`chr1b` or `chr1(mat)`/`chr1(pat)`) stays in `chr` so
        homologous bins remain distinct. Neither coordinates nor genomic positions are
        rescaled, and absent genomic bins are not imputed. When present, source `#unit`
        and chromosome-length headers are stored with the assembly and resolution in
        Arrow schema metadata. `.clean.3dg.txt.gz` files are converted too: they are
        published coordinate models, not discarded duplicates. The inspected `.clean`
        model has fewer bins, no headers/`#unit`, and a different coordinate scale from
        its corresponding uncleaned model.
        """
    )
    return


@app.cell
def _(conversion_results):
    def inspect_arrow(result):
        path = result["path"]
        with pa.ipc.open_file(path) as reader:
            table = reader.read_all()
        arrays = [
            table[column].combine_chunks().to_numpy(zero_copy_only=False)
            for column in ("x", "y", "z")
        ]
        ranges = []
        nonfinite = []
        for values in arrays:
            mask = np.isfinite(values)
            ranges.append(
                (float(values[mask].min()), float(values[mask].max()))
                if mask.any()
                else (None, None)
            )
            nonfinite.append(int((~mask).sum()))
        schema_metadata = table.schema.metadata or {}
        return {
            "structure": path.stem,
            "status": result["status"],
            "rows": table.num_rows,
            "columns": table.column_names,
            "chromosomes": pc.count_distinct(table["chr"]).as_py(),
            "null_chr": table["chr"].null_count,
            "null_coord": table["coord"].null_count,
            "unit": schema_metadata.get(b"unit", b"").decode(),
            "resolution_bp": schema_metadata.get(b"resolution_bp", b"").decode(),
            "xyz_ranges": ranges,
            "nonfinite_xyz": nonfinite,
            "first_rows": table.slice(0, 3).to_pylist(),
            "bytes": path.stat().st_size,
        }

    validation_results = [inspect_arrow(result) for result in conversion_results]
    for summary in validation_results:
        print(
            f"{summary['structure']}: {summary['rows']:,} rows, "
            f"{summary['chromosomes']} chromosomes, {summary['bytes']:,} bytes, "
            f"unit={summary['unit'] or 'not recorded'}"
        )
        print(f"  x/y/z ranges: {summary['xyz_ranges']}")
        print(f"  columns: {summary['columns']}")
        print(
            f"  null chr/coord: {summary['null_chr']}/{summary['null_coord']}; "
            f"non-finite x/y/z: {summary['nonfinite_xyz']}"
        )
        print(f"  first rows: {summary['first_rows']}")
    return (validation_results,)


@app.cell
def _(mo, validation_results):
    mo.md(
        "### Converted in this run\n\n"
        + "\n".join(
            f"- `{item['structure']}` — **{item['rows']:,} rows**, "
            f"{item['chromosomes']} haplotype-tagged chromosomes, "
            f"resolution {item['resolution_bp'] or 'unknown'} bp, "
            f"`unit={item['unit'] or 'not recorded'}`"
            for item in validation_results
        )
        + "\n\nA full remote run is intentionally expensive. Review a small run first, "
        "then obtain the local archive and set `MAX_STRUCTURES = None` for all models."
    )
    return


if __name__ == "__main__":
    app.run()
