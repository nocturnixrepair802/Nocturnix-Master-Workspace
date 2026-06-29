/*
=========================================================
Nocturnix Business Portal

Router

Version 0.5.0 Alpha
=========================================================
*/

async function loadModule(moduleName) {
  const workspace = document.getElementById("module-container");

  try {
    const response = await fetch(`modules/${moduleName}/index.html`);

    const html = await response.text();

    workspace.innerHTML = html;
  } catch (error) {
    workspace.innerHTML = `
            <h1>Module Error</h1>
            <p>Unable to load ${moduleName}</p>
        `;

    console.error(error);
  }
}
