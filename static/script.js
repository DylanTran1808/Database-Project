console.log("✅ Script loaded");

async function loadMenu() {
  try {
    console.log("Fetching /menu...");
    const res = await fetch('/menu');
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    console.log("Menu data:", data);

    const menuDiv = document.getElementById('menu');
    menuDiv.innerHTML = '<h2>Menu Loaded!</h2>';

    const sections = ['pizzas', 'drinks', 'desserts'];
    sections.forEach(section => {
      const title = document.createElement('h2');
      title.textContent = section;
      menuDiv.appendChild(title);

      data[section].forEach(item => {
        const div = document.createElement('div');
        div.textContent = `${item.name} - $${item.price.toFixed(2)}`;
        div.onclick = () => addToBasket(item);
        menuDiv.appendChild(div);
      });
    });
  } catch (err) {
    console.error("❌ Error loading menu:", err);
  }
}

const basket = [];

function addToBasket(item) {
  basket.push(item);
  console.log("Basket:", basket);
  renderBasket();
}

function renderBasket() {
  const ul = document.getElementById('basket-items');
  const total = document.getElementById('total');
  ul.innerHTML = '';
  let sum = 0;
  basket.forEach(item => {
    const li = document.createElement('li');
    li.textContent = `${item.name} - $${item.price.toFixed(2)}`;
    ul.appendChild(li);
    sum += item.price;
  });
  total.textContent = `Total: $${sum.toFixed(2)}`;
}

window.onload = loadMenu;

