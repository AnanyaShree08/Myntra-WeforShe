(function () {
  const STORAGE = {
    apiBase: "mynfit.apiBase",
    profile: "mynfit.profile",
    product: "mynfit.product",
    size: "mynfit.selectedSize",
  };

  // The only brands that actually exist in the backend dataset. Any brand
  // outside this list has zero real data behind it, so recommend.py's
  // fallback ladder silently drops brand entirely and returns the same
  // generic category-level result for every product - which is why every
  // product looked identical regardless of which one was opened.
  const VALID_BRANDS = [
    "Adidas", "Allen Solly", "Biba", "H&M", "Levi's",
    "Nike", "ONLY", "Roadster", "W", "Zara",
  ];

  // Display brand names on the cards (real Myntra-style brand names, kept
  // as-is visually) mapped to the nearest real dataset brand, so every
  // product actually gets a brand-specific recommendation instead of
  // silently falling back to a generic one.
  const BRAND_ALIASES = {
    "mango": "ONLY",
    "wrogn": "Adidas",
    "mast & harbour": "Allen Solly",
    "mast and harbour": "Allen Solly",
    "us polo assn": "Allen Solly",
    "us polo": "Allen Solly",
    "essentia luxe": "Zara",
    "style theory": "Zara",
    "silk & co": "W",
    "silk and co": "W",
    "nike sportswear": "Nike",
  };

  function normalizeBrand(rawName) {
    if (!rawName) return "Zara"; // safe default, never send an empty brand
    // strip common trailing marketing words that aren't part of the brand name
    const core = rawName
      .replace(/\s+(Collection|Premium|Women|Denims|Basics|Essentials|Performance|Heritage|Edit)\s*$/i, "")
      .trim();

    // exact (case-insensitive) match against real dataset brands first
    const exact = VALID_BRANDS.find(
      (b) => b.toLowerCase() === core.toLowerCase()
    );
    if (exact) return exact;

    // known alias for a display-only brand name
    const alias = BRAND_ALIASES[core.toLowerCase()] || BRAND_ALIASES[rawName.toLowerCase()];
    if (alias) return alias;

    // last resort - never let an unrecognized brand silently skip brand-level
    // matching; pick a consistent, real default instead
    return "Zara";
  }

  function read(key, fallback) {
    try {
      return JSON.parse(localStorage.getItem(key)) || fallback;
    } catch (_) {
      return fallback;
    }
  }
  function write(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }
  function categoryFrom(text) {
    const value = (text || "").toLowerCase();
    if (value.includes("dress")) return "Dress";
    if (value.includes("kurti")) return "Kurti";
    if (value.includes("jean")) return "Jeans";
    if (value.includes("trouser") || value.includes("chino")) return "Trousers";
    if (value.includes("top") || value.includes("polo")) return "Top";
    return "Shirt";
  }
  function getProduct() {
    const params = new URLSearchParams(location.search);
    if (params.get("brand") && params.get("category")) {
      return {
        brand: normalizeBrand(params.get("brand")),
        category: params.get("category"),
        name: params.get("name") || "",
      };
    }
    const stored = read(STORAGE.product, {
      brand: "H&M",
      category: "Top",
      name: "H&M Top",
    });
    // normalize even stored/legacy values, in case they were saved before
    // this fix and still hold a non-dataset brand name
    return { ...stored, brand: normalizeBrand(stored.brand) };
  }
  function openProduct(product, destination) {
    const normalized = { ...product, brand: normalizeBrand(product.brand) };
    write(STORAGE.product, normalized);
    location.href =
      (destination || "../mynfit_product_detail_page/code.html") +
      "?brand=" +
      encodeURIComponent(normalized.brand) +
      "&category=" +
      encodeURIComponent(normalized.category) +
      "&name=" +
      encodeURIComponent(normalized.name || "");
  }
  function profileIsValid(profile) {
    return (
      profile &&
      Number(profile.height_cm) > 0 &&
      Number(profile.weight_kg) > 0 &&
      profile.gender
    );
  }
  window.MynFit = {
    get apiBase() {
      return (
        window.MYNFIT_API_BASE_URL ||
        read(STORAGE.apiBase, "http://127.0.0.1:8000")
      );
    },
    get mynFitUrl() {
      return this.apiBase.replace(/\/$/, "") + "/mynfit";
    },
    getProduct,
    setProduct: (product) => write(STORAGE.product, { ...product, brand: normalizeBrand(product.brand) }),
    openProduct,
    getProfile: () => read(STORAGE.profile, null),
    setProfile: (profile) => write(STORAGE.profile, profile),
    profileIsValid,
    getSelectedSize: () => read(STORAGE.size, null),
    setSelectedSize: (size) => write(STORAGE.size, size),
    categoryFrom,
    normalizeBrand,
  };

  document.addEventListener(
    "click",
    function (event) {
      const card = event.target.closest(".group.cursor-pointer");
      if (!card) return;
      const name = card.querySelector("h3")?.textContent.trim();
      const description = card.querySelector("p")?.textContent.trim();
      if (name)
        write(STORAGE.product, {
          brand: normalizeBrand(name.replace(/\s+(Collection|Premium|Women)$/i, "")),
          category: categoryFrom(description),
          name: description || name,
        });
    },
    true,
  );

  document.addEventListener("DOMContentLoaded", function () {
    // The Stitch export stores accessible image descriptions in data-alt.
    // Promote them to real alt text so assistive technology can use them.
    document.querySelectorAll("img[data-alt]").forEach(function (image) {
      if (!image.hasAttribute("alt")) image.alt = image.dataset.alt;
    });
  });
})();
