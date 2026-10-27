"""Owner 2026-10-27: copy-ready post page - bold without asterisks, bullets, paragraphs."""

from mcf.report.post_html import to_html


def test_bold_bullets_no_asterisks():
    h = to_html("**Day 3 in the books!**\n\n***GitHub note here.\n\n**Changes before today:**\n\n- **Demoted** X to **Testing**\n- plain\n")
    assert "<b>Day 3 in the books!</b>" in h and "<b>Demoted</b> X to <b>Testing</b>" in h
    assert "*" not in h.split("<body>")[1]
    assert h.count("<li>") == 2 and "<p>GitHub note here.</p>" in h
