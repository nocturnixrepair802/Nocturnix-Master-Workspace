async function loadPage(page) {
  const response = await fetch(page);

  const html = await response.text();

  document.getElementById("app").innerHTML = html;
}
