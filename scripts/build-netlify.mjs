import { cp, mkdir, rm, copyFile } from "node:fs/promises";
import { resolve } from "node:path";

const source = resolve("src/trademate/static");
const output = resolve("netlify-build");

await rm(output, { recursive: true, force: true });
await mkdir(resolve(output, "static"), { recursive: true });
for (const file of ["index.html", "manifest.webmanifest", "service-worker.js"]) {
  await copyFile(resolve(source, file), resolve(output, file));
}
await cp(source, resolve(output, "static"), {
  recursive: true,
  filter: (path) => !["index.html", "manifest.webmanifest", "service-worker.js"].includes(path.split(/[\\/]/).at(-1)),
});
