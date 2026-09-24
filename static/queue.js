// The PDF list on the stamp page (R32), as plain functions over arrays.
//
// Kept apart from the page so the rules can be tested without a browser:
// tests/test_queue_js.py runs the user's own examples through them with node.
// Anything with a `.name` works, so a File in the page and a plain object in
// the test are the same to these functions.
//
// Same name means same file. That is the rule the server's repeated-upload
// check (R18) uses too, and that check stays as the backstop.

(function (exports) {
  // Add `incoming` to `current`, first-chosen first. A name already on the
  // list, or twice in `incoming`, is skipped and reported, never added again.
  function merge(current, incoming) {
    const have = new Set(current.map(f => f.name));
    const list = current.slice();
    const skipped = [];
    for (const f of incoming) {
      if (have.has(f.name)) { skipped.push(f.name); continue; }
      have.add(f.name);
      list.push(f);
    }
    return { list, skipped };
  }

  // `current` without the file called `name`.
  function remove(current, name) {
    return current.filter(f => f.name !== name);
  }

  exports.merge = merge;
  exports.remove = remove;
})(typeof module !== 'undefined' ? module.exports : (window.PdfQueue = {}));
