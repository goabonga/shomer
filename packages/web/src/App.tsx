// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>

/**
 * App shell: client-side routing over the server-rendered Jinja shell.
 *
 * The server serves the same HTML shell for every route (see shomer-ssr's
 * catch-all); React Router decides which page to render. AppRoutes is
 * exported separately so tests can drive it through a MemoryRouter.
 */

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { type AppConfig, readConfig } from "./config";
import { Home } from "./pages/Home";

export function AppRoutes({ config }: { config: AppConfig }) {
  return (
    <Routes>
      <Route path="/" element={<Home config={config} />} />
      <Route path="*" element={<Home config={config} />} />
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AppRoutes config={readConfig()} />
    </BrowserRouter>
  );
}
