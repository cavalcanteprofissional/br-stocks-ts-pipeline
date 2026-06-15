const DATA_URL = "/br-stocks-ts-pipeline/landing_data.json";

let cache = null;

export async function loadData() {
  if (cache) return cache;
  const res = await fetch(DATA_URL);
  if (!res.ok) throw new Error(`Failed to load data: ${res.status}`);
  cache = await res.json();
  return cache;
}
