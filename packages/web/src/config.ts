// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>

/**
 * Runtime config handed from the server to the React app.
 *
 * shomer-ssr renders `{{ config | tojson }}` into a
 * `<script id="app-config">` tag (see src/templates/index.html); the app
 * reads it at mount time. Keeping the server as the single source of
 * truth means no config is duplicated in the bundle.
 */

export interface AppConfig {
  appName: string;
  version: string;
  /**
   * Origin the tokens will claim to come from. The server owns it — a
   * second copy compiled into this bundle drifts the first time one
   * deployment is reconfigured.
   */
  issuer: string;
}

const DEFAULT_CONFIG: AppConfig = {
  appName: "Shomer",
  version: "dev",
  issuer: "",
};

/**
 * Keep only the keys AppConfig declares, and only when they are strings.
 *
 * Spreading the parsed JSON straight over the defaults would trust the
 * payload's shape: a parsed array or string spreads to numeric or index
 * keys, and `{"version": null}` would overwrite the default with null,
 * rendering the literal "null" rather than falling back. Both parse fine,
 * so a try/catch never sees them.
 */
function coerce(parsed: unknown): Partial<AppConfig> {
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return {};
  }
  const source = parsed as Record<string, unknown>;
  const out: Partial<AppConfig> = {};
  for (const key of Object.keys(DEFAULT_CONFIG) as (keyof AppConfig)[]) {
    const value = source[key];
    if (typeof value === "string") out[key] = value;
  }
  return out;
}

export function readConfig(): AppConfig {
  if (typeof document === "undefined") return DEFAULT_CONFIG;
  const el = document.getElementById("app-config");
  if (!el?.textContent) return DEFAULT_CONFIG;
  try {
    return { ...DEFAULT_CONFIG, ...coerce(JSON.parse(el.textContent)) };
  } catch {
    return DEFAULT_CONFIG;
  }
}
