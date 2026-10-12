import fs from "node:fs";
import path from "node:path";
const lock = JSON.parse(fs.readFileSync("package-lock.json", "utf8"));
let out =
  "Noriwake — third-party npm notices\nGenerated from package-lock.json; includes build tooling as well as runtime packages.\nOriginal Noriwake application code and artwork are not covered by these third-party licenses.\n\n";
for (const [dir, meta] of Object.entries(lock.packages).sort()) {
  if (!dir || !fs.existsSync(dir)) continue;
  const pkg = JSON.parse(
    fs.readFileSync(path.join(dir, "package.json"), "utf8"),
  );
  out += `\n${"=".repeat(72)}\n${pkg.name} ${pkg.version}\nDeclared license: ${pkg.license || "See license text"}\n`;
  const files = fs
    .readdirSync(dir)
    .filter(
      (n) =>
        /^(licen[sc]e|copying|notice)(\.|$)/i.test(n) &&
        fs.statSync(path.join(dir, n)).isFile(),
    );
  for (const f of files)
    out += `\n--- ${f} ---\n${fs.readFileSync(path.join(dir, f), "utf8")}\n`;
  if (!files.length)
    out +=
      "No standalone license file in installed package; consult package source before redistribution.\n";
}
fs.mkdirSync("public", { recursive: true });
fs.writeFileSync("public/THIRD_PARTY_NOTICES.txt", out);
