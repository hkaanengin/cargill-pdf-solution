"""R32: the PDF list on the stamp page, run through node.

`static/queue.js` holds the list's rules as plain functions, so they are
tested here with the user's own examples rather than in a browser. What the
page does with them (drawing rows, the remove buttons, the file input) is
still checked by hand.

Skipped when node is not installed. It is a dev tool, like pytest, and never
part of the image.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

QUEUE_JS = Path(__file__).resolve().parent.parent / "static" / "queue.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def js(expr: str):
    """Evaluate `expr` with `merge`/`remove` from queue.js in scope, as JSON."""
    script = (
        f"const {{ merge, remove }} = require({json.dumps(str(QUEUE_JS))});\n"
        f"const files = names => names.map(name => ({{ name }}));\n"
        f"const names = list => list.map(f => f.name);\n"
        f"process.stdout.write(JSON.stringify({expr}));"
    )
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_a_second_batch_is_added_not_swapped_in():
    # The user's example: 1-2-3, then 4-5-6, gives 1-2-3-4-5-6.
    r = js("(() => { const r = merge(files(['1.pdf','2.pdf','3.pdf']), files(['4.pdf','5.pdf','6.pdf']));"
           " return { list: names(r.list), skipped: r.skipped }; })()")
    assert r == {"list": ["1.pdf", "2.pdf", "3.pdf", "4.pdf", "5.pdf", "6.pdf"], "skipped": []}


def test_names_already_on_the_list_are_skipped_and_reported():
    # The user's example: 1-2-3, then 2-3-4, gives 1-2-3-4, and 2 and 3 are named.
    r = js("(() => { const r = merge(files(['1.pdf','2.pdf','3.pdf']), files(['2.pdf','3.pdf','4.pdf']));"
           " return { list: names(r.list), skipped: r.skipped }; })()")
    assert r == {"list": ["1.pdf", "2.pdf", "3.pdf", "4.pdf"], "skipped": ["2.pdf", "3.pdf"]}


def test_a_name_twice_in_one_pick_is_added_once():
    r = js("(() => { const r = merge([], files(['a.pdf','a.pdf'])); return { list: names(r.list), skipped: r.skipped }; })()")
    assert r == {"list": ["a.pdf"], "skipped": ["a.pdf"]}


def test_merge_does_not_change_the_list_it_was_given():
    assert js("(() => { const cur = files(['1.pdf']); merge(cur, files(['2.pdf'])); return names(cur); })()") == ["1.pdf"]


def test_remove_takes_one_file_off_and_keeps_the_order():
    assert js("names(remove(files(['1.pdf','2.pdf','3.pdf']), '2.pdf'))") == ["1.pdf", "3.pdf"]


def test_a_removed_file_can_be_added_again():
    r = js("(() => { const after = remove(files(['1.pdf','2.pdf']), '2.pdf');"
           " const r = merge(after, files(['2.pdf'])); return { list: names(r.list), skipped: r.skipped }; })()")
    assert r == {"list": ["1.pdf", "2.pdf"], "skipped": []}
