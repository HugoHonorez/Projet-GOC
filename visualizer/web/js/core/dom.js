const SVG_NS = "http://www.w3.org/2000/svg";

function apply(node, attrs, parent, text) {
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== undefined && value !== null && value !== false) node.setAttribute(key, value);
  }
  if (text !== undefined) node.textContent = text;
  if (parent) parent.appendChild(node);
  return node;
}

export function svg(tag, attrs = {}, parent = null, text) {
  return apply(document.createElementNS(SVG_NS, tag), attrs, parent, text);
}

export function html(tag, attrs = {}, parent = null, text) {
  return apply(document.createElement(tag), attrs, parent, text);
}

export function clear(node) {
  node.replaceChildren();
  return node;
}

export function tooltip(node, text) {
  svg("title", {}, node, text);
  return node;
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
