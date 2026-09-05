#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>
//
// Build the shomer-ssr frontend assets and sync them into the downstream
// Python package. Outputs land directly under
// packages/ssr/src/shomer_ssr/{static,templates}/ — that's the only place
// Python at runtime will read them from. Run with `--watch` for an
// incremental esbuild loop; without the flag for a one-shot release build
// called via multicz's post_bump.
//
//   src/main.tsx          ──> esbuild bundle ──> static/main.js
//   src/styles.css        ──> esbuild bundle ──> static/main.css
//   src/templates/*.html  ──> verbatim copy   ──> templates/
//
// Templates get an "AUTO-GENERATED" comment prepended so a Python dev who
// opens packages/ssr/src/shomer_ssr/templates/index.html knows to fix it
// upstream in web instead.

import * as esbuild from "esbuild";
import { mkdirSync, readdirSync, readFileSync, rmSync, watch, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const SRC = join(ROOT, "src");

// OUTPUT_STATIC / OUTPUT_TEMPLATES let a dev stack redirect the build at a
// path the ssr process also watches. Unset (a plain checkout, or CI), we
// write into packages/ssr/src/shomer_ssr/, which multicz then tracks as
// part of the ssr release.
const OUT_STATIC =
  process.env.OUTPUT_STATIC || resolve(ROOT, "..", "ssr", "src", "shomer_ssr", "static");
const OUT_TEMPLATES =
  process.env.OUTPUT_TEMPLATES || resolve(ROOT, "..", "ssr", "src", "shomer_ssr", "templates");

const WATCH = process.argv.includes("--watch");

const AUTO_GEN_COMMENT_HTML = (sourcePath) =>
  `<!-- AUTO-GENERATED from packages/web/src/templates/${sourcePath} - DO NOT EDIT -->\n`;

function ensureDir(dir) {
  mkdirSync(dir, { recursive: true });
}

// Minify in every mode so the dev bundle matches what production ships —
// same byte stream, same parser behaviour, fewer "works in dev, breaks in
// prod" surprises.
//
// In watch mode we emit `sourcemap: "external"`: esbuild writes a sibling
// main.js.map but does NOT append the `//# sourceMappingURL=` comment, so
// main.js stays byte-identical between dev and prod and no trailing dev
// artefact rides into a release commit. The ssr server detects the .map at
// request time and answers with a `SourceMap:` response header, which
// DevTools honours exactly like the inline comment would.
const jsConfig = {
  entryPoints: [join(SRC, "main.tsx")],
  bundle: true,
  minify: true,
  sourcemap: WATCH ? "external" : false,
  format: "iife",
  target: "es2022",
  // React 19 automatic runtime — esbuild injects the jsx-runtime imports,
  // so components don't need `import React`.
  jsx: "automatic",
  outfile: join(OUT_STATIC, "main.js"),
  logLevel: "info",
};

const cssConfig = {
  entryPoints: [join(SRC, "styles.css")],
  bundle: true,
  minify: true,
  sourcemap: WATCH ? "external" : false,
  outfile: join(OUT_STATIC, "main.css"),
  logLevel: "info",
};

function buildTemplates() {
  // Wipe the *contents* of the destination so deleted source templates
  // disappear too — but never the directory itself: under a dev stack
  // OUT_TEMPLATES may be a bind-mount point, and the kernel refuses to
  // remove one from inside the container regardless of UID. Unlinking each
  // .html file works on both layouts.
  ensureDir(OUT_TEMPLATES);
  for (const entry of readdirSync(OUT_TEMPLATES, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.endsWith(".html")) {
      rmSync(join(OUT_TEMPLATES, entry.name), { force: true });
    }
  }

  const srcDir = join(SRC, "templates");
  for (const entry of readdirSync(srcDir, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith(".html")) continue;
    const body = readFileSync(join(srcDir, entry.name), "utf8");
    writeFileSync(join(OUT_TEMPLATES, entry.name), AUTO_GEN_COMMENT_HTML(entry.name) + body);
    console.log(`templates/${entry.name} -> ${OUT_TEMPLATES}/${entry.name}`);
  }
}

ensureDir(OUT_STATIC);

if (WATCH) {
  // esbuild's context API rebuilds JS + CSS incrementally — it watches
  // every transitive import and only re-bundles what's dirty. Templates
  // aren't bundled (they're copied verbatim with a header), so fs.watch
  // covers them.
  const jsCtx = await esbuild.context(jsConfig);
  const cssCtx = await esbuild.context(cssConfig);
  await jsCtx.watch();
  await cssCtx.watch();

  buildTemplates();
  watch(join(SRC, "templates"), { recursive: false }, (_event, filename) => {
    if (!filename || !filename.endsWith(".html")) return;
    try {
      buildTemplates();
    } catch (err) {
      console.error("template rebuild failed:", err);
    }
  });

  console.log("watch mode — esbuild + fs.watch active. Ctrl-C to stop.");
  await new Promise(() => {});
} else {
  await Promise.all([esbuild.build(jsConfig), esbuild.build(cssConfig)]);
  buildTemplates();
  console.log("done.");
}
