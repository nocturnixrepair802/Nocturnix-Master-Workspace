/*
=========================================================
Nocturnix Business Portal

Client-Side Module Router
=========================================================
*/

const routes = {
  "/dashboard": {
    title: "Dashboard",
    modulePath:
      "modules/dashboard/index.html",
    styles: [],
    scripts: [],
  },

  "/customers": {
    title: "Customers",
    modulePath:
      "modules/customers/index.html",
    styles: [
      "modules/customers/customers.css",
    ],
    scripts: [],
  },

  "/repairs": {
    title: "Repair Operations",
    modulePath:
      "modules/repair-operations/index.html",
    styles: [
      "modules/repair-operations/css/repair-operations.css",
      "modules/repair-operations/css/repair-intake.css",
      "modules/repair-operations/css/repair-list.css",
      "modules/repair-operations/css/repair-queue.css",
      "modules/repair-operations/css/repair-toolbar.css",
      "modules/repair-operations/css/repair-details.css",
    ],
    scripts: [
      "modules/repair-operations/js/repair-operations.js",
    ],
  },
};

const defaultRoute = "/dashboard";

const loadedStyles = new Set();

const loadedScripts = new Map();


function normalizePath(pathname) {
  if (!pathname || pathname === "/") {
    return defaultRoute;
  }

  const normalized =
    pathname.replace(/\/+$/, "");

  return normalized || defaultRoute;
}


function getRoute(pathname) {
  const normalized =
    normalizePath(pathname);

  return (
    routes[normalized] ||
    routes[defaultRoute]
  );
}


function getWorkspace() {
  const workspace =
    document.querySelector(
      ".workspace"
    );

  if (!workspace) {
    throw new Error(
      "Nocturnix portal workspace was not found."
    );
  }

  return workspace;
}


function setActiveNavigation(pathname) {
  const normalized =
    normalizePath(pathname);

  document
    .querySelectorAll("[data-route]")
    .forEach((link) => {
      const route =
        normalizePath(
          link.getAttribute(
            "data-route"
          )
        );

      const active =
        route === normalized;

      link.classList.toggle(
        "active",
        active
      );

      if (active) {
        link.setAttribute(
          "aria-current",
          "page"
        );
      } else {
        link.removeAttribute(
          "aria-current"
        );
      }
    });
}


function setDocumentTitle(route) {
  document.title =
    `${route.title} | ` +
    "Nocturnix Business Portal";
}


function extractModuleContent(html) {
  const parser = new DOMParser();

  const parsedDocument =
    parser.parseFromString(
      html,
      "text/html"
    );

  const moduleWorkspace =
    parsedDocument.querySelector(
      "main.workspace"
    );

  if (moduleWorkspace) {
    return moduleWorkspace.innerHTML;
  }

  return parsedDocument.body.innerHTML;
}


function loadStyle(url) {
  if (loadedStyles.has(url)) {
    return;
  }

  const link =
    document.createElement("link");

  link.rel = "stylesheet";
  link.href = url;

  link.dataset.nocturnixModuleStyle =
    url;

  document.head.appendChild(link);

  loadedStyles.add(url);
}


function loadStyles(styles = []) {
  styles.forEach(
    (styleUrl) => {
      loadStyle(styleUrl);
    }
  );
}


function loadScript(url) {
  if (loadedScripts.has(url)) {
    return loadedScripts.get(url);
  }

  const promise =
    new Promise(
      (resolve, reject) => {
        const script =
          document.createElement(
            "script"
          );

        script.src = url;
        script.async = false;

        script.dataset.nocturnixModuleScript =
          url;

        script.addEventListener(
          "load",
          () => resolve()
        );

        script.addEventListener(
          "error",
          () => {
            loadedScripts.delete(
              url
            );

            reject(
              new Error(
                `Unable to load module script: ${url}`
              )
            );
          }
        );

        document.body.appendChild(
          script
        );
      }
    );

  loadedScripts.set(
    url,
    promise
  );

  return promise;
}


async function loadScripts(
  scripts = []
) {
  for (const scriptUrl of scripts) {
    await loadScript(
      scriptUrl
    );
  }
}


async function loadModule(pathname) {
  const normalized =
    normalizePath(pathname);

  const route =
    getRoute(normalized);

  const workspace =
    getWorkspace();

  workspace.innerHTML = `
    <section class="portal-loading">
      <h2>
        Loading ${route.title}...
      </h2>
    </section>
  `;

  try {
    loadStyles(
      route.styles
    );

    const response =
      await fetch(
        route.modulePath,
        {
          cache: "no-store",
        }
      );

    if (!response.ok) {
      throw new Error(
        "Module request failed: " +
          response.status
      );
    }

    const html =
      await response.text();

    workspace.innerHTML =
      extractModuleContent(
        html
      );

    await loadScripts(
      route.scripts
    );

    setActiveNavigation(
      normalized
    );

    setDocumentTitle(
      route
    );

    document.dispatchEvent(
      new CustomEvent(
        "nocturnix:module-loaded",
        {
          detail: {
            path: normalized,
            route,
            workspace,
          },
        }
      )
    );
  } catch (error) {
    console.error(
      "Module load failed:",
      error
    );

    workspace.innerHTML = `
      <section class="portal-error">
        <h2>
          Module unavailable
        </h2>

        <p>
          Nocturnix could not load
          ${route.title}.
        </p>
      </section>
    `;
  }
}


function navigate(pathname) {
  const normalized =
    normalizePath(pathname);

  if (
    window.location.pathname !==
    normalized
  ) {
    window.history.pushState(
      {},
      "",
      normalized
    );
  }

  loadModule(
    normalized
  );
}


function handleNavigation(event) {
  const link =
    event.target.closest(
      "[data-route]"
    );

  if (!link) {
    return;
  }

  const route =
    link.getAttribute(
      "data-route"
    );

  if (!route) {
    return;
  }

  event.preventDefault();

  navigate(
    route
  );
}


function initializeRouter() {
  document.addEventListener(
    "click",
    handleNavigation
  );

  window.addEventListener(
    "popstate",
    () => {
      loadModule(
        window.location.pathname
      );
    }
  );

  let initialPath =
    normalizePath(
      window.location.pathname
    );

  if (!routes[initialPath]) {
    initialPath =
      defaultRoute;

    window.history.replaceState(
      {},
      "",
      initialPath
    );
  }

  loadModule(
    initialPath
  );
}


document.addEventListener(
  "DOMContentLoaded",
  initializeRouter
);