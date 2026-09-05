// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Chris <goabonga@pm.me>

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { AppRoutes } from "../src/App";

const config = { appName: "Shomer", version: "0.0.0", issuer: "" };

describe("AppRoutes", () => {
  it("renders the home page at /", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppRoutes config={config} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Shomer" })).toBeDefined();
  });

  it("renders the home page for an unknown route", () => {
    render(
      <MemoryRouter initialEntries={["/nowhere"]}>
        <AppRoutes config={config} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Shomer" })).toBeDefined();
  });
});
