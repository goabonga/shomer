// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>

/**
 * Home route.
 */

import { useEffect } from "react";
import type { AppConfig } from "../config";

export function Home({ config }: { config: AppConfig }) {
  useEffect(() => {
    document.title = config.appName;
  }, [config.appName]);

  return (
    <main>
      <h1>{config.appName}</h1>
      <p>OAuth2 / OpenID Connect authorization platform.</p>
      {config.issuer ? (
        <p>
          Issuer: <code>{config.issuer}</code>
        </p>
      ) : null}
    </main>
  );
}
