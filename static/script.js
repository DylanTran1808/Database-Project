document.addEventListener("DOMContentLoaded", async () => {
  const homeBtn = document.getElementById("home-btn");
  if (homeBtn) {
    homeBtn.addEventListener("click", () => {
      window.location.href = "/";  // redirect to home route
    });
  }
  const menuContainer = document.getElementById("menu-container");
  const basketList = document.getElementById("basket");
  const checkoutBtn = document.getElementById("checkout-btn");
  const totalText = document.getElementById("total");

  let basket = [];

  // --- Load menu from backend ---
  try {
    const res = await fetch("/menu/get_menu");
    const data = await res.json();
    console.log("Menu loaded:", data);

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
  } catch (err) {
    console.error("Failed to load menu:", err);
  }

  // --- Basket functions ---
  function addToBasket(item) {
    basket.push(item);
    renderBasket();
  }

  function renderBasket() {
    basketList.innerHTML = "";
    let total = 0;
    basket.forEach(it => {
      const li = document.createElement("li");
      li.textContent = `${it.name} x1 - $${it.price.toFixed(2)}`;
      basketList.appendChild(li);
      total += it.price;
    });
    totalText.textContent = `Total: $${total.toFixed(2)}`;
  }

  // --- Checkout button ---
  checkoutBtn.addEventListener("click", async () => {
    console.log("Checkout clicked. Basket:", basket);
    if (basket.length === 0) return alert("Your basket is empty!");

    const customer_id = 1; // example

    try {
      // --- Step 1: Get order summary ---
      const summaryRes = await fetch("/order/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id,
          items: basket.map(it => ({
            type: it.type,
            name: it.name, // send name only
            quantity: 1
          }))
        })
      });

      if (!summaryRes.ok) throw new Error(`Summary request failed: ${summaryRes.status}`);

      const summary = await summaryRes.json();
      console.log("Order summary received:", summary);

      if (!summary.items || summary.items.length === 0) {
        return alert("No items found in order summary. Please check the basket.");
      }

      // --- Step 2: Show summary and ask for delivery person ---
      let summaryText = "Order Summary:\n";
      summary.items.forEach(it => {
        summaryText += `${it.name} x${it.quantity} - $${it.price.toFixed(2)}\n`;
      });
      summaryText += `Total: $${summary.total.toFixed(2)}\nDiscount: $${summary.discount.toFixed(2)}\nFinal: $${summary.final_total.toFixed(2)}`;
      const delivery_person_id = prompt(summaryText + "\nEnter delivery person ID:");
      if (!delivery_person_id) return alert("Order cancelled!");

      // --- Step 3: Confirm order ---
      const confirmRes = await fetch("/order/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id,
          items: summary.items,
          discount: summary.discount,
          delivery_person_id
        })
      });

      if (!confirmRes.ok) throw new Error(`Confirm request failed: ${confirmRes.status}`);

      const result = await confirmRes.json();
      console.log("Order confirmed:", result);

      alert(`✅ Order placed! Order ID: ${result.order_id}, Final Total: $${result.final_total.toFixed(2)}`);

      // Clear basket
      basket = [];
      renderBasket();

    } catch (err) {
      console.error("Error during checkout:", err);
      alert("An error occurred during checkout. See console for details.");
    }
  });
});
