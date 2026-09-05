// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>

import { beforeEach, describe, expect, it } from "vitest";
import { readConfig } from "../src/config";

function mountConfig(text: string): void {
  document.body.innerHTML = `<script id="app-config">${text}</script>`;
}

describe("readConfig", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("falls back to the defaults when the tag is absent", () => {
    expect(readConfig()).toEqual({ appName: "Shomer", version: "dev", issuer: "" });
  });

  it("reads the issuer the server resolved", () => {
    mountConfig(JSON.stringify({ issuer: "https://id.example.test" }));
    expect(readConfig().issuer).toBe("https://id.example.test");
  });

  it("reads the server-provided values", () => {
    mountConfig(JSON.stringify({ appName: "Shomer", version: "1.2.3" }));
    expect(readConfig().version).toBe("1.2.3");
  });

  it("falls back on malformed JSON rather than throwing", () => {
    mountConfig("{not json");
    expect(readConfig().version).toBe("dev");
  });

  it("ignores non-string values instead of rendering them", () => {
    mountConfig(JSON.stringify({ version: null }));
    expect(readConfig().version).toBe("dev");
  });

  it("ignores a payload that is not an object", () => {
    mountConfig(JSON.stringify(["nope"]));
    expect(readConfig()).toEqual({ appName: "Shomer", version: "dev", issuer: "" });
  });
});
