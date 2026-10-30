// rastreador-importacao/frontend/src/formato.test.ts
import { describe, expect, it } from "vitest";
import { data, dinheiro, normalizarDecimal } from "./formato";

describe("formato", () => {
  it("data não sofre deslocamento de fuso", () => {
    expect(data("2026-06-01")).toBe("01/06/2026");
    expect(data(null)).toBe("—");
  });

  it("dinheiro em BRL", () => {
    expect(dinheiro("98765.43").replace(/\s/g, " ")).toBe("R$ 98.765,43");
    expect(dinheiro(null)).toBe("—");
  });

  it("normaliza decimal digitado à brasileira", () => {
    expect(normalizarDecimal("1.234,56")).toBe("1234.56");
    expect(normalizarDecimal("1234.56")).toBe("1234.56");
    expect(normalizarDecimal(" 10,5 ")).toBe("10.5");
  });
});
