console.log("hi.");

const listFileIn = Deno.args[0];
const outMdPath = Deno.args[1];

const header = "|filename|R2 URL|chspace.xyz|\n|---|---|---|\n";
const baseBucketURL = "https://pub-5c3f8ce35c924114a178c6e929fc3ac7.r2.dev";
let content = header;

const generatedFiles = await Deno.readTextFile(listFileIn);

for (const file of generatedFiles.split("\n")) {
  if (file === "") {
    continue;
  }
  const arrowURL = `${baseBucketURL}/${file}.arrow`;
  const parquetURL = `${baseBucketURL}/${file}.parquet`;
  const csvURL = `${baseBucketURL}/${file}.csv`;
  const chspaceURL = `https://chspace.xyz/?source=${arrowURL}`;
  const line =
    `|${file}|[.arrow](${arrowURL}) / [.parquet](${parquetURL}) / [.csv](${csvURL})|[open](${chspaceURL})|\n`;
  content = content + line;
}

await Deno.writeTextFile(outMdPath, content);
