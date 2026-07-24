(() => {
  const rootId = 'nocturnix-widget-root';
  if (document.getElementById(rootId)) return;
  const root = document.createElement('div'); root.id = rootId; document.body.appendChild(root);
  const css = document.createElement('link'); css.rel='stylesheet'; css.href='/static/widget.css'; document.head.appendChild(css);
  const script = document.createElement('script'); script.src='/static/widget.js'; script.defer=true; document.head.appendChild(script);
})();
