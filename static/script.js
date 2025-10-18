document.addEventListener("DOMContentLoaded", async () => {
  const menuContainer = document.getElementById("menu-container");
  const basketList = document.getElementById("basket");
  const checkoutBtn = document.getElementById("checkout-btn");
  const totalText = document.getElementById("total");

  let basket = [];

  // Load menu
  const res = await fetch("/menu");
  const data = await res.json();
  console.log("Menu Loaded!");

  const allItems = [
    ...data.pizzas.map(p => ({ ...p, type: "pizza" })),
    ...data.drinks.map(p => ({ ...p, type: "drink" })),
    ...data.desserts.map(p => ({ ...p, type: "dessert" }))
  ];

  allItems.forEach(item => {
    const card = document.createElement("div");
    card.className = "menu-card";
    card.innerHTML = `
      <h3>${item.name}</h3>
      <p>$${item.price.toFixed(2)}</p>
      <small>${item.type.toUpperCase()}</small>
    `;
    card.addEventListener("click", () => addToBasket(item));
    menuContainer.appendChild(card);
  });

  function addToBasket(item) {
    basket.push(item);
    renderBasket();
  }

  function renderBasket() {
    basketList.innerHTML = "";
    let total = 0;
    basket.forEach(it => {
      const li = document.createElement("li");
      li.textContent = `${it.name} - $${it.price.toFixed(2)}`;
      basketList.appendChild(li);
      total += it.price;
    });
    totalText.textContent = `Total: $${total.toFixed(2)}`;
  }

  checkoutBtn.addEventListener("click", async () => {
    if (basket.length === 0) return alert("Your basket is empty!");

    // Example customer id (you’ll replace this dynamically)
    const customer_id = 1;

    const payload = {
      customer_id,
      items: basket.map(it => ({
        type: it.type,
        id: it.product_id || 1, // you can fix this once you know product_id
        quantity: 1
      }))
    };

    const response = await fetch("/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    alert(`✅ Order placed! Total: $${result.total.toFixed(2)} (Discount: $${result.discount.toFixed(2)})`);
    basket = [];
    renderBasket();
  });
});


