(function () {
  const STORAGE = {
    apiBase: "mynfit.apiBase",
    profile: "mynfit.profile",
    product: "mynfit.product",
    size: "mynfit.selectedSize",
  };

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
        brand: params.get("brand"),
        category: params.get("category"),
        name: params.get("name") || "",
      };
    }
    return read(STORAGE.product, {
      brand: "H&M",
      category: "Top",
      name: "H&M Top",
    });
  }
  function openProduct(product, destination) {
    write(STORAGE.product, product);
    location.href =
      (destination || "../mynfit_product_detail_page/code.html") +
      "?brand=" +
      encodeURIComponent(product.brand) +
      "&category=" +
      encodeURIComponent(product.category) +
      "&name=" +
      encodeURIComponent(product.name || "");
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
    setProduct: (product) => write(STORAGE.product, product),
    openProduct,
    getProfile: () => read(STORAGE.profile, null),
    setProfile: (profile) => write(STORAGE.profile, profile),
    profileIsValid,
    getSelectedSize: () => read(STORAGE.size, null),
    setSelectedSize: (size) => write(STORAGE.size, size),
    categoryFrom,
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
          brand: name.replace(/\s+(Collection|Premium|Women)$/i, ""),
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
