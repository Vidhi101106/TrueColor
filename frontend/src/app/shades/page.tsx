"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

type Product = {
  brand: string;
  product_line: string;
  shade_name: string;
  price_cad: number | null;
  price_reference_url: string | null;
  product_url: string;
  delta_e: number;
  swatch_hex: string | null;
  swatch_estimated: boolean;
};
type AnalysisResult = {
  undertone: string;
  pantone_family: string;
  products?: Product[];
};

export default function ShadesPage() {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [brand, setBrand] = useState("all");
  const [sort, setSort] = useState("match");
  const [maxPrice, setMaxPrice] = useState("all");

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("analysisResult");
      if (saved) setAnalysis(JSON.parse(saved) as AnalysisResult);
    } catch { /* display the retry link below */ }
  }, []);

  const products = useMemo(() => analysis?.products || [], [analysis]);
  const brands = useMemo(() => [...new Set(products.map(p => p.brand))].sort(), [products]);
  const filtered = useMemo(() => {
    const selection = products.filter(p => {
      if (brand !== "all" && p.brand !== brand) return false;
      if (maxPrice !== "all" && (p.price_cad === null || p.price_cad > Number(maxPrice))) return false;
      return true;
    });
    return selection.sort((a, b) => {
      if (sort === "low") return (a.price_cad ?? Infinity) - (b.price_cad ?? Infinity) || a.delta_e - b.delta_e;
      if (sort === "high") return (b.price_cad ?? -1) - (a.price_cad ?? -1) || a.delta_e - b.delta_e;
      return a.delta_e - b.delta_e;
    });
  }, [products, brand, sort, maxPrice]);

  if (!analysis) {
    return <main className="min-h-screen tc-bg p-10 text-center"><h1 className="tc-title">No analysis yet</h1><p className="mt-3">Upload a photo first.</p><Link className="tc-btn tc-btn-primary inline-block mt-6" href="/capture">Analyze a photo</Link></main>;
  }

  return (
    <main className="min-h-screen tc-bg">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <Link href="/results" className="text-pink-600">← Back to your analysis</Link>
        <h1 className="tc-title text-center mt-8">Your foundation shortlist</h1>
        <p className="text-center text-zinc-600 mt-2">Compare suggested shades across brands and budgets</p>
        <div className="tc-card mt-8 p-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="text-sm font-bold">Brand
              <select aria-label="Filter brand" value={brand} onChange={e => setBrand(e.target.value)} className="mt-2 w-full rounded-xl border border-pink-200 bg-white p-3">
                <option value="all">All brands</option>
                {brands.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </label>
            <label className="text-sm font-bold">Budget (CAD)
              <select aria-label="Filter maximum price" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} className="mt-2 w-full rounded-xl border border-pink-200 bg-white p-3">
                <option value="all">Any price</option>
                <option value="10">Under $10</option>
                <option value="15">Under $15</option>
                <option value="20">Under $20</option>
                <option value="40">Under $40</option>
                <option value="60">Under $60</option>
              </select>
            </label>
            <label className="text-sm font-bold">Sort results
              <select aria-label="Sort results" value={sort} onChange={e => setSort(e.target.value)} className="mt-2 w-full rounded-xl border border-pink-200 bg-white p-3">
                <option value="match">Closest colour first</option>
                <option value="low">Price: low to high</option>
                <option value="high">Price: high to low</option>
              </select>
            </label>
          </div>
          <p className="mt-3 text-xs text-zinc-500">Prices are CAD reference examples, not live quotes. Fenty uses its regular (pre-sale) reference price; current retailer discounts may be lower. Products without a reference price are excluded from budget filters.</p>
        </div>
        <p className="mt-6 text-sm font-semibold text-zinc-700">{filtered.length} suggested shades</p>
        {products.length === 0 && <p className="mt-4 text-zinc-700">No structured recommendations are available yet. Re-run your photo analysis after updating the backend.</p>}
        {products.length > 0 && filtered.length === 0 && <p className="mt-4 text-zinc-700">No shades match these filters. Try another brand or budget.</p>}
        <div className="grid gap-4 mt-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p, i) => (
            <article key={p.brand + p.shade_name + i} className="tc-card p-5">
              <div className="flex justify-between items-center">
                <strong className="text-pink-700">{p.brand}</strong>
                <span className="text-sm text-zinc-600">{p.price_cad === null ? "Price unavailable" : "$" + p.price_cad.toFixed(2) + " CAD"}</span>
              </div>
              <p className="text-xs text-zinc-500 mt-1">{p.product_line}</p>
              <div className="flex gap-3 items-center mt-5">
                <div aria-label="Approximate shade swatch" className="w-14 h-14 rounded-xl border border-zinc-200" style={{backgroundColor: p.swatch_hex || "#dedede"}} />
                <div>
                  <h2 className="text-lg font-bold">{p.shade_name}</h2>
                  <p className="text-xs text-zinc-500">Approx. colour distance: {p.delta_e.toFixed(1)}</p>
                </div>
              </div>
              {p.product_url && <a className="text-sm text-pink-700 underline mt-5 inline-block" href={p.product_url} target="_blank" rel="noopener noreferrer">View product ↗</a>}
              {p.price_reference_url && p.price_reference_url !== p.product_url && <a className="block text-xs text-zinc-500 underline mt-2" href={p.price_reference_url} target="_blank" rel="noopener noreferrer">Price reference</a>}
            </article>
          ))}
        </div>
        <p className="mt-8 text-xs text-zinc-600">Results are approximate suggestions based on photographed colour and uncalibrated digital shade estimates. Lighting, white balance, oxidation and real product texture matter. Always test the product in person before purchasing.</p>
        <div className="text-center mt-8"><Link href="/capture" className="tc-btn tc-btn-primary inline-block">Try another photo</Link></div>
      </div>
    </main>
  );
}
