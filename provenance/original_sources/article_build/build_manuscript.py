"""Build the simulation-validated neural Lyapunov manuscript as a polished DOCX."""

from __future__ import annotations

import csv
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ALIGN_VERTICAL, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import nsdecls, qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUTPUT_DIR = ROOT.parent / "output" / "docx"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTPUT_DIR / "Structure_Preserving_Neural_Lyapunov_Certificates.docx"

NAVY = "0B2545"
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
TEAL = "0B7A75"
MUTED = "5C6673"
LIGHT = "F4F6F9"
LIGHT_BLUE = "E8EEF5"
LIGHT_GOLD = "FFF4DC"
RED = "9B1C1C"
WHITE = "FFFFFF"
BLACK = "000000"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths: list[int], indent=120) -> None:
    if sum(widths) != 9360:
        raise ValueError(f"Table widths must sum to 9360 DXA, got {sum(widths)}")
    table.autofit = False
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), "9360")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:type"), "dxa")
    tbl_ind.set(qn("w:w"), str(indent))
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width / 1440)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:type"), "dxa")
            tc_w.set(qn("w:w"), str(width))
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_run_font(run, name="Calibri", size=None, color=None, bold=None, italic=None) -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_hyperlink(paragraph, text: str, url: str, color=BLUE, underline=True) -> None:
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), color)
    r_pr.append(c)
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        r_pr.append(u)
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Calibri")
    fonts.set(qn("w:hAnsi"), "Calibri")
    r_pr.append(fonts)
    new_run.append(r_pr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def add_field(paragraph, instruction: str) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    r1 = OxmlElement("w:r"); r1.append(begin)
    r2 = OxmlElement("w:r"); r2.append(instr)
    r3 = OxmlElement("w:r"); r3.append(separate); r3.append(text)
    r4 = OxmlElement("w:r"); r4.append(end)
    paragraph._p.extend([r1, r2, r3, r4])


def add_native_equation(doc: Document, expression: str, number: int) -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["Equation"]
    tabs = p.paragraph_format.tab_stops
    tabs.add_tab_stop(Inches(3.25), alignment=1)
    tabs.add_tab_stop(Inches(6.5), alignment=2)
    p.add_run("\t")
    omath = OxmlElement("m:oMath")
    mr = OxmlElement("m:r")
    mrpr = OxmlElement("m:rPr")
    sty = OxmlElement("m:sty")
    sty.set(qn("m:val"), "p")
    mrpr.append(sty)
    mr.append(mrpr)
    mt = OxmlElement("m:t")
    mt.text = expression
    mr.append(mt)
    omath.append(mr)
    p._p.append(omath)
    r = p.add_run(f"\t({number})")
    set_run_font(r, name="Cambria Math", size=10.5, color=BLACK)


def add_paragraph_border(paragraph, color=TEAL, size=18, side="left") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    border = OxmlElement(f"w:{side}")
    border.set(qn("w:val"), "single")
    border.set(qn("w:sz"), str(size))
    border.set(qn("w:space"), "8")
    border.set(qn("w:color"), color)
    p_bdr.append(border)


def shade_paragraph(paragraph, fill=LIGHT) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_callout(doc, label: str, text: str, kind="info") -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["Callout"]
    fill = LIGHT_GOLD if kind == "warning" else LIGHT
    edge = RED if kind == "warning" else TEAL
    shade_paragraph(p, fill)
    add_paragraph_border(p, edge)
    r = p.add_run(label + " ")
    set_run_font(r, bold=True, color=edge)
    r = p.add_run(text)
    set_run_font(r, color=BLACK)


def add_caption(doc, text: str) -> None:
    p = doc.add_paragraph(text, style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_together = True


def add_figure(doc, filename: str, caption: str, alt: str, width=6.45) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(RESULTS / filename), width=Inches(width))
    shape._inline.docPr.set("descr", alt)
    shape._inline.docPr.set("name", alt[:120])
    add_caption(doc, caption)


def create_numbering(doc: Document, bullet=False) -> int:
    numbering = doc.part.numbering_part.element
    abstract_ids = [int(x.get(qn("w:abstractNumId"))) for x in numbering.findall(qn("w:abstractNum"))]
    num_ids = [int(x.get(qn("w:numId"))) for x in numbering.findall(qn("w:num"))]
    abstract_id = max(abstract_ids + [0]) + 1
    num_id = max(num_ids + [0]) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    nsid = OxmlElement("w:nsid"); nsid.set(qn("w:val"), f"{0xA1000000 + abstract_id:08X}"); abstract.append(nsid)
    tmpl = OxmlElement("w:tmpl"); tmpl.set(qn("w:val"), f"{0xB2000000 + abstract_id:08X}"); abstract.append(tmpl)
    multi = OxmlElement("w:multiLevelType"); multi.set(qn("w:val"), "singleLevel"); abstract.append(multi)
    lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start"); start.set(qn("w:val"), "1"); lvl.append(start)
    num_fmt = OxmlElement("w:numFmt"); num_fmt.set(qn("w:val"), "bullet" if bullet else "decimal"); lvl.append(num_fmt)
    lvl_text = OxmlElement("w:lvlText"); lvl_text.set(qn("w:val"), "•" if bullet else "%1."); lvl.append(lvl_text)
    suff = OxmlElement("w:suff"); suff.set(qn("w:val"), "tab"); lvl.append(suff)
    p_pr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab"); tab.set(qn("w:val"), "num"); tab.set(qn("w:pos"), "540"); tabs.append(tab); p_pr.append(tabs)
    ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "280"); p_pr.append(ind)
    lvl.append(p_pr)
    r_pr = OxmlElement("w:rPr"); fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:ascii"), "Calibri"); fonts.set(qn("w:hAnsi"), "Calibri"); r_pr.append(fonts); lvl.append(r_pr)
    abstract.append(lvl)
    numbering.append(abstract)
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId"); abstract_ref.set(qn("w:val"), str(abstract_id)); num.append(abstract_ref)
    numbering.append(num)
    return num_id


def add_list_item(doc, text: str, num_id: int) -> None:
    p = doc.add_paragraph()
    p.style = doc.styles["List Paragraph"]
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.208
    p_pr = p._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), "0")
    num = OxmlElement("w:numId"); num.set(qn("w:val"), str(num_id))
    num_pr.extend([ilvl, num]); p_pr.append(num_pr)
    p.add_run(text)


def add_table(doc, headers, rows, widths, caption, font_size=8.8) -> None:
    p = doc.add_paragraph(caption, style="Table Caption")
    p.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    set_table_geometry(table, widths)
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, header in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_shading(cell, LIGHT_BLUE)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(0)
        run = para.add_run(header)
        set_run_font(run, size=font_size, bold=True, color=NAVY)
    for row_data in rows:
        row = table.add_row()
        for i, value in enumerate(row_data):
            cell = row.cells[i]
            para = cell.paragraphs[0]
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = 1.05
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 or len(value) > 18 else WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(str(value))
            set_run_font(run, size=font_size, color=BLACK)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def setup_styles(doc: Document) -> None:
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"; normal.font.size = Pt(11); normal.font.color.rgb = RGBColor.from_string(BLACK)
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_before = Pt(0); normal.paragraph_format.space_after = Pt(8)
    normal.paragraph_format.line_spacing = 1.333
    for name, size, color, before, after in [
        ("Heading 1",16,BLUE,18,10),("Heading 2",13,BLUE,12,6),("Heading 3",12,DARK_BLUE,8,4)]:
        s = styles[name]
        s.font.name = "Calibri"; s.font.size = Pt(size); s.font.bold = True; s.font.color.rgb = RGBColor.from_string(color)
        s._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); s._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        s.paragraph_format.space_before = Pt(before); s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.keep_with_next = True
    caption = styles["Caption"]
    caption.font.name = "Calibri"; caption.font.size = Pt(9); caption.font.italic = True; caption.font.color.rgb = RGBColor.from_string(MUTED)
    caption.paragraph_format.space_before = Pt(3); caption.paragraph_format.space_after = Pt(8); caption.paragraph_format.line_spacing = 1.0
    for style_name, base in [("Equation","Normal"),("Callout","Normal"),("Table Caption","Caption")]:
        if style_name not in styles:
            styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        styles[style_name].base_style = styles[base]
    eq = styles["Equation"]
    eq.font.name = "Cambria Math"; eq.font.size = Pt(10.5)
    eq.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT; eq.paragraph_format.space_before = Pt(4); eq.paragraph_format.space_after = Pt(6); eq.paragraph_format.keep_together = True
    callout = styles["Callout"]
    callout.paragraph_format.left_indent = Inches(0.12); callout.paragraph_format.right_indent = Inches(0.08)
    callout.paragraph_format.space_before = Pt(6); callout.paragraph_format.space_after = Pt(8); callout.paragraph_format.line_spacing = 1.15
    tc = styles["Table Caption"]
    tc.font.bold = True; tc.font.italic = False; tc.font.color.rgb = RGBColor.from_string(NAVY)
    tc.paragraph_format.space_before = Pt(6); tc.paragraph_format.space_after = Pt(4)
    styles["List Paragraph"].font.name = "Calibri"; styles["List Paragraph"].font.size = Pt(11)


def setup_page(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5); section.page_height = Inches(11)
    section.top_margin = Inches(1); section.bottom_margin = Inches(1); section.left_margin = Inches(1); section.right_margin = Inches(1)
    section.header_distance = Inches(0.492); section.footer_distance = Inches(0.492)
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("STRUCTURE-PRESERVING NEURAL LYAPUNOV CERTIFICATES")
    set_run_font(r, size=8.5, bold=True, color=MUTED)
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("Uyulan  |  ")
    set_run_font(r, size=8.5, color=MUTED)
    add_field(p, "PAGE")
    r = p.add_run(" / ")
    set_run_font(r, size=8.5, color=MUTED)
    add_field(p, "NUMPAGES")


def add_title_block(doc: Document) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(10)
    r = p.add_run("RESEARCH ARTICLE  •  AUGUST 2026")
    set_run_font(r, size=10, bold=True, color=TEAL)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run("Structure-Preserving Neural Lyapunov Certificates for Intelligent Nonlinear Control")
    set_run_font(r, size=24, bold=True, color=NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(18)
    r = p.add_run("A failure-aware and simulation-validated framework for robustness, verification, and compositional scaling")
    set_run_font(r, size=13, italic=True, color=DARK_BLUE)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Çağlar Uyulan")
    set_run_font(r, size=12, bold=True, color=BLACK)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(2)
    r = p.add_run("Department of Mechanical Engineering, Faculty of Engineering and Architecture, İzmir Kâtip Çelebi University, İzmir, Türkiye")
    set_run_font(r, size=9.5, color=MUTED)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(16)
    r = p.add_run("Correspondence: caglar.uyulan@ikcu.edu.tr  |  ORCID: 0000-0002-6423-6720")
    set_run_font(r, size=9.5, color=MUTED)


def add_body(doc, text: str, bold_lead: str | None = None) -> None:
    p = doc.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        set_run_font(r, bold=True, color=NAVY)
        p.add_run(text[len(bold_lead):])
    else:
        p.add_run(text)


def section(doc, title: str, level=1) -> None:
    doc.add_heading(title, level=level)


def read_metrics() -> dict[str, dict[str, str]]:
    with (RESULTS / "model_verification_metrics.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["Row"]: row for row in reader}


def build() -> None:
    metrics = read_metrics()
    base = metrics["Unconstrained_MSE_DNN"]
    prop = metrics["StructurePreserving_PDE_DNN"]
    doc = Document()
    setup_styles(doc)
    setup_page(doc)
    add_title_block(doc)

    section(doc,"Abstract",1)
    add_body(doc,
        "Deep neural networks (DNNs) can represent Lyapunov functions beyond polynomial templates, but approximation accuracy alone does not establish stability. This article synthesizes a failure-aware framework that separates architectural guarantees, orbital-derivative learning, counterexample mining, and post-training verification. The work is grounded in the local manuscript and code base associated with Efficient Computation of Lyapunov Functions Using DNNs, augmented with recent developments in neural certificates through August 2026. A source-fidelity audit first exposes a sign defect: the published four-state example contains even-power dynamics for which the asserted Lyapunov derivative is positive on part of the state space; 19.0952% of 250,000 uniform samples violate decrease, and a negative initial condition exhibits finite escape. A corrected benchmark is then constructed so that its exact quadratic certificate is analytically known while its nonlinear term is energy preserving. The proposed candidate Vθ(x)=ε||x||²+||ϕθ(x)-ϕθ(0)||² enforces Vθ(0)=0 and positive definiteness for every network parameter. MATLAB R2024b experiments compare this architecture with an unconstrained value-regression DNN. On 232,761 dense-grid and Monte Carlo states in [-2,2]², the unconstrained model violates positivity at 5.0662% and decrease at 2.2697% of tested points; the proposed model produces no observed positivity, derivative, or prescribed-decay violations, while maintaining a 5.8997% relative value error. Sixteen closed-loop trajectories show no monotonicity violation over 20,452 integration steps. A sampled robust-stability test remains violation free through uncertainty scale 0.8, consistent with a 0.7978 sufficient bound. Finally, a shared 272-parameter compositional certificate is evaluated without observed violations from 2 to 32 states, whereas a 21-point tensor grid grows from 441 to 2.05×10⁴² points. The analysis is explicit about its epistemic boundary: finite testing is evidence, not a formal proof of uniform decrease; SMT or branch-and-bound verification remains the required publication-grade certification step for safety-critical deployment.")
    p = doc.add_paragraph()
    r = p.add_run("Keywords: "); set_run_font(r,bold=True,color=NAVY)
    p.add_run("Lyapunov stability; deep neural networks; intelligent control; control Lyapunov functions; robustness; counterexample-guided learning; compositional systems; neural verification")

    section(doc,"Research highlights",1)
    highlight_bullet_id = create_numbering(doc, bullet=True)
    for item in [
        "A mathematical and code-level audit identifies a stability-sign error that value regression alone cannot detect.",
        "The neural architecture satisfies the equilibrium and positivity conditions exactly for all trainable weights.",
        "Physics-informed orbital-derivative loss and hard-state recycling remove all observed decay violations on 232,761 validation points.",
        "A robust Lyapunov margin connects model-error bounds to intelligent-controller deployment.",
        "Weight sharing retains 272 parameters while the validated interconnected model scales from 2 to 32 states."
    ]:
        add_list_item(doc,item,highlight_bullet_id)

    add_callout(doc,"Claim discipline.","In this manuscript, “guaranteed” refers only to properties enforced algebraically by the architecture or proved conditionally in the stated theorems. A zero sampled-violation rate is reported as empirical validation, not as a formal certificate over a continuum.","warning")

    section(doc,"1. Introduction",1)
    add_body(doc,
        "Lyapunov theory converts an infinite-horizon question about trajectories into inequalities on a scalar function. For a nonlinear closed loop, this is unusually powerful: stability can be proved without solving the state equations, and the same function can guide controller synthesis, region-of-attraction (ROA) estimation, observer design, robustness analysis, and adaptive laws [1-5]. The price is constructive difficulty. Quadratic functions solve the linear problem through a Lyapunov equation, while nonlinear systems generally require energy insight, sum-of-squares (SOS) templates, numerical PDE solvers, or problem-specific converse constructions [2,6,7].")
    add_body(doc,
        "DNNs offer a flexible alternative because automatic differentiation supplies the orbital derivative and compositional architectures can reuse local structure. Early neural-certificate methods learned ROAs from data [11], jointly searched for controllers and Lyapunov functions with a falsifier [12], and combined neural learners with formal satisfiability-modulo-theories (SMT) verification [13]. More recent work has imposed positive-definite architectures [14], studied unknown dynamics [16], extended certification to networked and discrete-time systems [18,19], and replaced expensive global solvers with bound-propagation and branch-and-bound procedures [20,24]. The field has therefore moved from “fit a Lyapunov-shaped surface” toward “co-design a certificate that a verifier can prove.”")
    add_body(doc,
        "The local baseline article [8] correctly foregrounds compositional structure and the curse of dimensionality. Its associated notebooks, however, primarily minimize mean squared value error against a known analytical candidate. This distinction is decisive: a small value error does not control the sign of the gradient projected onto the vector field. Moreover, the paper and code disagree on part of the four-dimensional dynamics, and the remaining even-power state equation is not globally stabilizing for negative states. Rather than reproducing those results, the present synthesis treats them as a diagnostic starting point and builds a new, auditable pipeline.")
    add_body(doc,"The contributions are:")
    contribution_number_id = create_numbering(doc, bullet=False)
    for item in [
        "a source-fidelity audit that connects equations, notebooks, orbital derivatives, and trajectories before training;",
        "a smooth, structure-preserving neural candidate with exact equilibrium anchoring and a uniform quadratic lower bound;",
        "a normalized Zubov-type PDE residual, prescribed decay loss, and counterexample recycling strategy;",
        "conditional stability, robustness, and compositional scaling results with short proofs;",
        "reproducible MATLAB experiments that report violations, worst margins, trajectory monotonicity, uncertainty tolerance, and dimension scaling; and",
        "a deployment map for CLF-QP safety layers, adaptive neural control, learned observers, and networked intelligent systems."
    ]:
        add_list_item(doc,item,contribution_number_id)

    add_figure(doc,"fig01_method_workflow.png",
        "Figure 1. Structure-preserving synthesis loop. Algebraic positivity is separated from derivative learning; hard states return to the learner, and accepted candidates are passed to empirical and formal verification before control deployment.",
        "Workflow from dynamics and controller through positive neural architecture, physics loss, counterexample mining, verification, and intelligent-control deployment.",5.75)

    section(doc,"2. Stability framework and neural certificates",1)
    section(doc,"2.1 Closed-loop nonlinear system",2)
    add_body(doc,"Consider a continuously differentiable plant with a possibly learned feedback policy κω and an equilibrium shifted to the origin. The closed-loop vector field is")
    add_native_equation(doc,"ẋ = fκ(x) := f(x, κω(x)),     fκ(0)=0,     x∈D⊂ℝⁿ.",1)
    add_body(doc,"Assume fκ is locally Lipschitz on an open set containing the compact verification domain D. A continuously differentiable scalar V is a strict Lyapunov function on D when")
    add_native_equation(doc,"V(0)=0,     V(x)>0,     V̇(x)=∇V(x)ᵀfκ(x)<0     for every x∈D∖{0}.",2)
    add_body(doc,"If a level set is contained in D, it defines a forward-invariant inner estimate of the ROA:")
    add_native_equation(doc,"Ωρ := {x : V(x)≤ρ},     Ωρ⊂D.",3)
    add_body(doc,"The domain qualifier is essential. Neither a plot nor a sample cloud proves global stability, and a trajectory initialized in D need not remain there unless invariance is established. This manuscript therefore reports trajectories only from a sublevel family that remains inside the verified square.")

    section(doc,"2.2 Why regression error is not a certificate",2)
    add_body(doc,"Let V* be a valid certificate and V̂=V*+e. A value bound |e(x)|≤η does not imply a useful gradient bound, because highly oscillatory errors may be uniformly small while ∇e is large. Along the dynamics, V̂̇=V*̇+∇eᵀfκ, so the sign can change wherever the projected gradient error exceeds the nominal decay margin. This is precisely what the numerical comparison in Section 7 demonstrates: the unconstrained DNN has slightly lower value RMSE than the proposed network, yet violates both positivity and derivative conditions.")
    add_callout(doc,"Operational rule.","Every learned Lyapunov function should be evaluated on the quantities used in the theorem - V(0), a positivity margin, the orbital derivative, and an invariant sublevel set - rather than on regression loss alone.")

    section(doc,"2.3 Literature transition: approximation to verification",2)
    add_table(doc,
        ["Method family","Representative mechanism","What is guaranteed","Primary limitation"],
        [
            ["SOS / SDP","Polynomial V and semidefinite constraints","Algebraic certificate when solver assumptions hold","Polynomial dynamics/templates; dimensional growth"],
            ["Value-regression DNN","Fit samples of a known V","Approximation on the sampled distribution","No sign guarantee for V or V̇"],
            ["Positive neural architecture","V lower bounded by a known positive function","V(0)=0 and V>0 by construction","Derivative remains to be verified"],
            ["Learner-falsifier / SMT","Train, search counterexamples, formally discharge constraints","Uniform certificate on the encoded domain","Solver and activation-function scalability"],
            ["Bound propagation / BaB","Optimize verification-friendly bounds and split hard boxes","Post-hoc or training-time certified ROA","Implementation complexity; conservatism"],
            ["Compositional certificate","Combine local ISS/Lyapunov functions","Scalable global result under interconnection conditions","Requires exploitable subsystem structure"]
        ],[1600,2600,2560,2600],"Table 1. Neural Lyapunov synthesis has evolved from fitting to architecture-aware and verifier-aware design [9-24].")

    section(doc,"3. Source-fidelity and stability audit",1)
    section(doc,"3.1 Reconciliation of the paper and repository",2)
    add_body(doc,"The baseline PDF [8], the public DeepDynaSim repository, two TensorFlow notebooks, and two MATLAB scripts were inspected as a single evidence set. The first notebook supervises a scalar network with the analytical value V=0.5x₁⁴+0.5x₂². Its later visualization cell silently changes the vector field, so the displayed orbital derivative is not necessarily associated with the training dynamics. The second notebook uses ẋ₁=-x₁² and ẋ₃=-x₃³, whereas the paper's displayed derivative corresponds to even powers in both nonlinear channels. The provided MATLAB example additionally tests a conservative oscillator with h(x)=2||x||², for which the requested strict inequality cannot hold because the true derivative of x₁²+x₂² is zero.")
    add_table(doc,
        ["Audited item","Observation","Stability consequence","Required correction"],
        [
            ["Equation-level bounds","A vector gradient is compared directly with scalar radial bounds","Condition is dimensionally undefined","Bound V by class-K functions; constrain ∇Vᵀf separately"],
            ["Four-state example","ẋ₁=-x₁² with V containing x₁⁴","Contribution -4x₁⁵ is positive for x₁<0","Use odd dissipative power or restrict and prove invariant domain"],
            ["Paper vs notebook","The x₃ exponent differs","Reproduction does not match the printed model","Version equations and code from one source of truth"],
            ["Regression objective","MSE fits known V values","Low MSE need not preserve V̇<0","Train and verify orbital-derivative margins"],
            ["MATLAB checker","Grid assembled as paired points, not a Cartesian product","Large parts of the square are never checked","Use meshgrid / product sampling and numerical gradients consistently"]
        ],[1700,2600,2500,2560],"Table 2. Failure modes found in the local baseline and its associated repository.",8.5)

    section(doc,"3.2 Analytical failure of the even-power example",2)
    add_body(doc,"For the published candidate V=x₁⁴+x₂²+x₃⁶+x₄² and even-power nonlinear channels, the orbital derivative contains odd powers:")
    add_native_equation(doc,"V̇ = -4x₁⁵ - 2x₂² - 6x₃⁷ - 2x₄².",4)
    add_body(doc,"This expression is not negative definite. With x₂=x₃=x₄=0 and x₁<0, V̇=-4x₁⁵>0. More strongly, ẋ₁=-x₁² has the solution x₁(t)=x₁(0)/(1+x₁(0)t). For x₁(0)=-0.5, the denominator vanishes at t=2, so the state undergoes finite escape rather than convergence. The code-level audit therefore changes the scientific question: the relevant goal is not to approximate this candidate more accurately, but to detect and reject the incompatible dynamics-certificate pair.")
    add_figure(doc,"fig02_source_example_audit.png",
        "Figure 2. Stability audit of the even-power source example. A negative state diverges at the analytical finite-escape time t=2, while the candidate orbital derivative becomes positive; replacing the even power with an odd dissipative power restores convergence in the illustrated scalar channel.",
        "Two plots showing finite escape for xdot equals minus x squared from negative initial state and positive Lyapunov derivative, compared with corrected odd-power dynamics.")

    section(doc,"4. Proposed structure-preserving method",1)
    section(doc,"4.1 Positive-definite neural architecture",2)
    add_body(doc,"Let ϕθ:ℝⁿ→ℝʳ be any continuously differentiable feature network. We define")
    add_native_equation(doc,"Vθ(x) = ε‖x‖₂² + ‖ϕθ(x)-ϕθ(0)‖₂²,     ε>0.",5)
    add_body(doc,"The origin is anchored exactly because both terms vanish at x=0. For x≠0, Vθ(x)≥ε||x||²>0 irrespective of the learned weights. This is a smooth vector-feature specialization of the positive Lyapunov-Net design [14]. It removes two competing loss terms - equilibrium matching and positivity - and leaves the optimizer to shape the derivative. Squared features also preserve differentiability for tanh networks and produce a directly editable analytical expression.")

    section(doc,"4.2 Physics-informed objective",2)
    add_body(doc,"For a desired state penalty q(x)=||x||² and prescribed decay c>0, set rθ=∇Vθᵀfκ+||x||² and mθ=∇Vθᵀfκ+c||x||². Their normalized forms and the empirical MATLAB objective are")
    add_native_equation(doc,"L(θ)=E[r̃θ²] + 8E[[m̃θ]₊²] + 0.05Lₐ,     [a]₊=max(a,0),",6)
    add_native_equation(doc,"r̃θ=rθ/(‖x‖²+0.05),     m̃θ=mθ/(‖x‖²+0.05).",7)
    add_body(doc,"The first term targets a normalized Zubov-type transport equation; the second enforces a nonzero decay margin even when the PDE fit is imperfect. Four anchor values form Lₐ and remove residual trajectory-wise scaling ambiguity. Near-origin Gaussian samples and uniform domain samples are mixed in every mini-batch.")

    section(doc,"4.3 Hard-state recycling",2)
    add_body(doc,"The learner is coupled to a lightweight numerical falsifier. Every 200 iterations, 12,000 fresh states are scored by mθ; the 192 largest margins are retained and resampled in later mini-batches. This does not replace a formal verifier, but it concentrates training on the exact states most likely to falsify the theorem.")
    method_number_id = create_numbering(doc, bullet=False)
    for item in [
        "Initialize the feature network at small weight scale and set ε and c from the desired lower and decay margins.",
        "Sample 704 uniform states, 128 near-origin states, and 192 recycled hard states per iteration.",
        "Compute Vθ, ∇Vθ, rθ, and mθ by automatic differentiation; update θ with Adam and cosine-decayed learning rate.",
        "Every 200 iterations, evaluate a fresh pool, retain the worst mθ states, and continue training.",
        "After training, separate empirical validation, trajectory tests, robustness tests, and formal verification. Reject the candidate if any required gate fails."
    ]:
        add_list_item(doc,item,method_number_id)

    add_figure(doc,"fig03_training_convergence.png",
        "Figure 3. Deterministic training histories (seed 20260826). The structure-preserving loss rapidly reduces the normalized PDE objective, while counterexample recycling keeps the worst mini-batch decay margin nonpositive after the early transient.",
        "Training plots comparing supervised MSE loss with structure-preserving PDE loss, and showing PDE residual and worst decay margin.")

    section(doc,"4.4 Verification hierarchy",2)
    add_body(doc,"A credible neural certificate requires several independent gates. Gate A is algebraic: Eq. (5) enforces Vθ(0)=0 and Vθ≥ε||x||². Gate B is numerical: dense grids, independent Monte Carlo samples, hard-state searches, and trajectory monotonicity expose ordinary implementation defects. Gate C is robust: the margin is recomputed under bounded model perturbations. Gate D is formal: SMT, mixed-integer, interval, or bound-propagation methods must prove the derivative inequality for every state in the selected domain [12,13,19,20,22-24]. Only Gates A-D justify the phrase “formally certified” in a safety-critical setting.")

    section(doc,"5. Theoretical guarantees",1)
    section(doc,"Theorem 1 - Architectural positivity",2)
    add_callout(doc,"Theorem 1.","For any ε>0 and any differentiable feature network ϕθ, Eq. (5) satisfies Vθ(0)=0 and Vθ(x)≥ε||x||² for all x. Hence Vθ is positive definite; if the quadratic term is retained globally, Vθ is radially unbounded.")
    add_body(doc,"Proof. At x=0, both terms in Eq. (5) are zero. For x≠0, the feature norm is nonnegative and ε||x||² is strictly positive. The lower bound tends to infinity with ||x||, which also proves radial unboundedness. □")

    section(doc,"Theorem 2 - Exponential stability on a verified sublevel set",2)
    add_callout(doc,"Theorem 2.","Let Ωρ={x:Vθ(x)≤ρ} be compact and contained in D. Suppose Vθ(x)≤b||x||² and ∇Vθ(x)ᵀfκ(x)≤-c||x||² on Ωρ for b,c>0. Then Ωρ is forward invariant and the origin is exponentially stable for every initial state in Ωρ.")
    add_native_equation(doc,"‖x(t)‖ ≤ √(b/ε) exp[-ct/(2b)] ‖x(0)‖.",8)
    add_body(doc,"Proof. On the boundary Vθ=ρ, the derivative is strictly negative away from the origin, so a trajectory cannot cross outward and Ωρ is invariant. Since ||x||²≥Vθ/b, V̇θ≤-(c/b)Vθ. The comparison lemma gives Vθ(t)≤Vθ(0)e^{-ct/b}; combining Vθ≥ε||x||² and Vθ(0)≤b||x(0)||² yields Eq. (8). □")

    section(doc,"Proposition 1 - Robustness to model error",2)
    add_callout(doc,"Proposition 1.","Let the true field be ftrue=fκ+Δ. If nominal decrease satisfies ∇Vθᵀfκ≤-α||x||², and ||∇Vθ||≤g||x||, ||Δ||≤d||x|| on Ωρ, then V̇θ,true≤-(α-gd)||x||². The same sublevel set is exponentially stable whenever gd<α.")
    add_native_equation(doc,"V̇θ,true = ∇Vθᵀfκ + ∇VθᵀΔ ≤ -(α-gd)‖x‖².",9)
    add_body(doc,"The result follows immediately from Cauchy-Schwarz. It is especially useful in intelligent control: d can combine learned-model error, bounded residual approximation error, and actuator/model mismatch. A safety monitor can therefore compare a live uncertainty estimate against α/g instead of relying on an uncalibrated neural confidence score.")

    section(doc,"Proposition 2 - Exact compositional certificate for the ring benchmark",2)
    add_body(doc,"For m two-state subsystems zi with periodic indexing, define")
    add_native_equation(doc,"żᵢ = Azᵢ + 0.6zᵢ,₁JPzᵢ + κ(zᵢ₋₁-zᵢ),     VΣ=Σᵢ zᵢᵀPzᵢ.",10)
    add_body(doc,"If AᵀP+PA=-I, P≻0, and Jᵀ=-J, then")
    add_native_equation(doc,"V̇Σ = -Σᵢ‖zᵢ‖² - κΣᵢ(zᵢ-zᵢ₋₁)ᵀP(zᵢ-zᵢ₋₁) ≤ -Σᵢ‖zᵢ‖².",11)
    add_body(doc,"Proof. The nonlinear term vanishes because (Pzi)ᵀJ(Pzi)=0. Summing the periodic diffusive terms and pairing adjacent cross-products yields the negative weighted disagreement energy in Eq. (11). □ The learned experiment replaces each exact local quadratic with one shared vθ. The analytic result validates the benchmark; the learned derivative is still reported empirically unless a verifier proves the approximation margin.")

    section(doc,"6. Reproducible numerical study",1)
    section(doc,"6.1 Non-normal nonlinear benchmark",2)
    add_body(doc,"The two-state field is designed to be nonlinear yet analytically auditable:")
    add_native_equation(doc,"f(x)=Ax+0.6x₁JPx,     A=[-1  4; -0.5  -1],     J=[0  -1; 1  0].",12)
    add_native_equation(doc,"P=[17/48  7/24; 7/24  5/3],     λ(P)={0.2922708, 1.7285625}.",13)
    add_body(doc,"The matrix P solves AᵀP+PA=-I with zero residual to MATLAB display precision. Therefore V*(x)=xᵀPx is globally positive definite. The nonlinear term is P-energy preserving, and")
    add_native_equation(doc,"V̇*(x)=xᵀ(AᵀP+PA)x+1.2x₁(Px)ᵀJ(Px)=-‖x‖².",14)
    add_body(doc,"The non-normal A makes the Euclidean quadratic generally unsuitable, while the skew energy injection produces curved trajectories without weakening the exact decay identity. This combination is useful for assessing whether a network learns the stability geometry rather than merely a radial bowl.")

    section(doc,"6.2 Training and verification protocol",2)
    add_table(doc,
        ["Setting","Unconstrained baseline","Proposed certificate"],
        [
            ["Architecture","2-32-32-1 tanh","2-24-8 tanh features; Eq. (5)"],
            ["Trainable objective","MSE to exact V* values","Normalized PDE + decay hinge + anchors"],
            ["Training points","24,000 uniform","Fresh uniform + near-origin + hard points"],
            ["Iterations / batch","1,400 / 512","2,200 / 1,024"],
            ["Optimizer","Adam; cosine schedule","Adam; cosine schedule"],
            ["Domain","[-2,2]²","[-2,2]²"],
            ["ε / c","not applicable","0.02 / 0.15"],
            ["Independent validation","181×181 grid + 200,000 random","same states and metrics"]
        ],[2300,3530,3530],"Table 3. Deterministic training configuration in MATLAB R2024b (random seed 20260826).",8.7)
    add_body(doc,"All plots are generated by article_build/simulate_neural_lyapunov.m. Dense-grid and Monte Carlo samples are combined only for post-training reporting; none is reused as an optimizer batch. ODE45 uses relative tolerance 10⁻⁹ and absolute tolerance 10⁻¹¹. The 16 trajectory initial states lie on radius 1.1 and remain inside [-2,2]².")

    section(doc,"7. Results",1)
    section(doc,"7.1 Certificate quality versus value fit",2)
    add_table(doc,
        ["Metric","MSE DNN","Proposed DNN","Interpretation"],
        [
            ["Training time (s)",f"{float(base['TrainingTime_s']):.3f}",f"{float(prop['TrainingTime_s']):.3f}","Derivative learning costs more"],
            ["Relative L2 value error",f"{100*float(base['RelativeL2ValueError']):.4f}%",f"{100*float(prop['RelativeL2ValueError']):.4f}%","Nearly equal value fidelity"],
            ["|V(0)|",f"{float(base['AbsV0']):.6f}",f"{float(prop['AbsV0']):.6f}","Origin exact only by architecture"],
            ["Positivity violation rate",f"{100*float(base['PositiveDefiniteViolationRate']):.4f}%",f"{100*float(prop['PositiveDefiniteViolationRate']):.4f}%","Algebraic lower bound succeeds"],
            ["Derivative violation rate",f"{100*float(base['DerivativeViolationRate']):.4f}%",f"{100*float(prop['DerivativeViolationRate']):.4f}%","MSE does not preserve gradients"],
            ["Decay-margin violation rate",f"{100*float(base['DecayMarginViolationRate']):.4f}%",f"{100*float(prop['DecayMarginViolationRate']):.4f}%","Tested with c=0.15"],
            ["Maximum decay margin",f"{float(base['MaximumDecayMargin']):.4f}",f"{float(prop['MaximumDecayMargin']):.3e}","Negative is required"],
            ["PDE residual RMSE",f"{float(base['PDERMSE']):.4f}",f"{float(prop['PDERMSE']):.4f}","Physics loss reduces transport error"]
        ],[2400,1500,1500,3960],"Table 4. Post-training validation on 232,761 states. Zero means no observed violation, not a formal continuum proof.",8.45)
    add_body(doc,"The key comparison is intentionally uncomfortable: the baseline has a slightly smaller value error (5.7263% versus 5.8997%) but fails every certificate-specific gate. Its output at the equilibrium is 0.2550, its minimum tested value is -0.2587, and 2.2697% of tested points have a nonnegative orbital derivative. By contrast, the structure-preserving model has Vθ(0)=0 exactly, a minimum tested off-origin value of 6.80×10⁻⁶, and a worst decay margin of -1.15×10⁻⁵.")
    add_figure(doc,"fig04_learned_certificate_fields.png",
        "Figure 4. Exact and learned Lyapunov fields on [-2,2]². The structure-preserving network reproduces the tilted energy geometry; its prescribed-decay margin remains negative on the plotted grid. Black points are the final recycled hard states.",
        "Four contour plots of exact Lyapunov function, learned neural function, approximation error, and negative decay margin with hard samples.")

    section(doc,"7.2 Trajectory consistency",2)
    add_body(doc,"Sixteen trajectories generate 20,452 accepted ODE time steps. No increase larger than 2×10⁻⁶ is detected; the actual maximum step increase is 7.80×10⁻¹⁴. At t=12, the largest final state norm is 1.93×10⁻⁵ and the median is 8.70×10⁻⁶. These trajectory checks are weaker than derivative verification, but they independently catch sign errors, dimension swaps, and mismatched dynamics such as those observed in the source audit.")
    add_figure(doc,"fig05_trajectories_and_decay.png",
        "Figure 5. Closed-loop trajectories from radius 1.1 remain inside the verified square and cross learned level sets inward. The selected certificate traces decrease monotonically over twelve seconds.",
        "Phase portrait with sixteen convergent trajectories inside the verified square and semilog decay curves of the learned certificate.")

    section(doc,"7.3 Robustness margin",2)
    add_body(doc,"The perturbed model fδ=f+δBx uses B=[[0.20,0.15],[-0.10,0.25]]. On 80,000 independent samples, the learned nominal decay rate is α̂=0.8500 and the sampled gradient gain is ĝ=3.6395. Proposition 1 gives the sampled sufficient scale δ<0.7978 after including ||B||₂. The empirical sweep reports zero violations through δ=0.8 and first detects violations at δ=0.9. Agreement between the sufficient estimate and the falsification threshold is reassuring, but both remain sample-dependent because ĝ and α̂ were not obtained with certified global bounds.")
    add_figure(doc,"fig06_robustness_sweep.png",
        "Figure 6. Robustness sweep for Δf=δBx. The vertical line is the sampled sufficient bound 0.7978; no decay-margin violations are observed through δ=0.8, while the worst margin turns positive at δ=0.9.",
        "Two robustness plots showing decay violation rate and worst Lyapunov margin versus uncertainty scale.")

    section(doc,"7.4 Compositional scaling",2)
    add_body(doc,"A single local feature network is shared across m periodic subsystems, so the learned parameter count remains 272 for every dimension. Each dimension is tested on 12,000 independently sampled full states with κ=0.08. No learned or exact decay-condition violation is observed from n=2 through n=32. Measured evaluation time per sample increases from 0.0123 ms to 0.0225 ms. In contrast, a modest tensor grid with 21 values per coordinate grows to 2.05×10⁴² points at n=32.")
    add_table(doc,
        ["n","Subsystems","Parameters","Time/sample (ms)","Observed violations","21ⁿ grid points"],
        [
            ["2","1","272","0.01234","0 / 12,000","4.41×10²"],
            ["4","2","272","0.01005","0 / 12,000","1.94481×10⁵"],
            ["8","4","272","0.01200","0 / 12,000","3.78229×10¹⁰"],
            ["16","8","272","0.01411","0 / 12,000","1.43057×10²¹"],
            ["32","16","272","0.02248","0 / 12,000","2.04653×10⁴²"]
        ],[780,1250,1250,1800,2200,2080],"Table 5. Weight-shared compositional evaluation. Timings are wall-clock measurements, not asymptotic complexity claims.",8.5)
    add_figure(doc,"fig07_compositional_scaling.png",
        "Figure 7. Shared compositional certificate from 2 to 32 states. The left panel contrasts near-linear evaluation cost with exponential tensor-grid cardinality. The right panel plots a 1/12,000 visualization floor for zero observed violations; every reported count is 0/12,000.",
        "Scaling plots comparing neural evaluation time with exponential tensor-grid size and zero sampled violation counts through 32 states.")

    section(doc,"8. Applications in intelligent control",1)
    section(doc,"8.1 Neural policy with a CLF-QP safety layer",2)
    add_body(doc,"A learned policy uNN can be treated as a performance proposal rather than a final actuator command. For control-affine dynamics ẋ=f(x)+g(x)u, the online filter solves")
    add_native_equation(doc,"u*=argminᵤ ‖u-uNN(x)‖²  subject to  ∇Vθᵀ(f+gu)≤-c‖x‖²+s,",15)
    add_body(doc,"with a heavily penalized slack s≥0 and actuator constraints. When the certificate is valid and the constraint is feasible, the filter makes the smallest intervention consistent with the Lyapunov decrease condition. Barrier constraints can be added to separate asymptotic regulation from state safety [17,29]. The derivative margin in this paper is exactly the quantity an implementation would monitor.")

    section(doc,"8.2 Robust adaptive neural control",2)
    add_body(doc,"Adaptive neural controllers typically approximate unknown nonlinearities and use a Lyapunov function containing tracking error and weight-estimation energy. Reconstruction error prevents exact cancellation, so robust terms or ultimate-boundedness arguments are required. The local variable-stiffness-actuator study [25] is an instructive example: an RBF network models lumped uncertainty, while an additional robust term protects stability against approximation error. Proposition 1 provides an analogous certificate-centric interpretation. Online estimates of model residuals should be converted into d, then compared with α/g; the network should not be trusted solely because its prediction error is small.")

    section(doc,"8.3 Output feedback, observers, and state uncertainty",2)
    add_body(doc,"In practice Vθ is evaluated on an estimated state x̂. Output-feedback certificates therefore need a joint plant-observer Lyapunov argument or an explicit Lipschitz error allowance. Recent verifier-aware frameworks have synthesized neural observers and controllers together [20]. A conservative deployment alternative is to reserve part of the nominal decay margin for ||x-x̂||, measurement noise, and sample-and-hold error. If this reserve is exhausted, the controller should switch to a known recovery policy.")

    section(doc,"8.4 Networked MIMO systems",2)
    add_body(doc,"The compositional experiment illustrates a path around the state-space grid explosion. Shared local certificates suit platoons, robot formations, power networks, and modular mechatronic systems when subsystem physics and coupling graphs repeat. The decisive theorem is not universal approximation; it is an ISS or dissipativity condition that permits local certificates to compose [4,5,18]. In MIMO control, this structure can be aligned with decentralized controllers, graph neural policies, and small-gain matrices. A monolithic DNN should be the exception when physically meaningful decomposition is available.")

    section(doc,"8.5 Digital twins, anomaly detection, and fault tolerance",2)
    add_body(doc,"A neural Lyapunov residual can serve as a health signal in a digital twin. If rθ(x)=∇Vθᵀfmodel(x)+q(x) is near zero during nominal operation but the measured finite-difference energy change becomes positive, the discrepancy indicates modeling error, actuator degradation, or a distribution shift relevant to stability. Because the signal is tied to an energy balance, it is more actionable than a generic reconstruction loss. Fault logic should nevertheless use persistence, confidence bounds, and a recovery controller to avoid reacting to differentiation noise.")

    section(doc,"9. Limitations and research agenda",1)
    limitation_bullet_id = create_numbering(doc, bullet=True)
    for item in [
        "Formal derivative proof is not completed here. The next step is to export the tanh network and dynamics to an interval or branch-and-bound verifier, or to retrain with verifier-friendly activations and certified bounds [20,24].",
        "The benchmark has known smooth dynamics and an analytical reference certificate. Unknown systems require uncertainty sets learned from data, and Proposition 1 must use certified model-error bounds rather than sample maxima [15,16,21].",
        "Only one principal nonlinear benchmark and one repeated subsystem family are studied. Comparisons with SOS, rational CLFs, and formal neural baselines on standard robot tasks are needed before claiming state-of-the-art performance.",
        "Floating-point automatic differentiation and ODE integration are checked numerically, not with interval arithmetic. Reproducibility across hardware, precisions, and random seeds should be reported.",
        "The compositional test shares one local network and uses diffusive ring coupling. Heterogeneous subsystems require local ISS gains and a verified gain operator; zero sampled violations do not establish a general small-gain result.",
        "Hardware experiments, actuator saturation, delays, measurement noise, hybrid modes, and discrete implementation are outside the present scope. Each can invalidate a continuous-time certificate if omitted."
    ]:
        add_list_item(doc,item,limitation_bullet_id)
    add_body(doc,"The emerging verifier-aware literature suggests a concrete research program: train against certified bounds rather than point margins; adaptively partition hard regions; exploit compositional ISS structure; co-design policies, observers, and certificates; and expose numerical proof artifacts as first-class experimental outputs. The 2026 CT-BaB result [24] is particularly relevant because it closes part of the training-verification gap by using branch-and-bound partitions during training.")

    section(doc,"10. Conclusions",1)
    add_body(doc,"DNNs are useful in Lyapunov analysis only when their flexibility is disciplined by stability theory. The local baseline's strongest idea - compositional approximation - survives this audit, but value-supervised experiments do not by themselves validate a certificate, and an incompatible vector field cannot be repaired by a better regressor. The proposed workflow makes four distinctions explicit: positivity can be guaranteed architecturally; decrease must be trained and checked on the vector field; robustness needs a quantitative margin; and formal certification is separate from empirical falsification.")
    add_body(doc,"The deterministic MATLAB study supports those distinctions. At essentially equal value error, the unconstrained DNN violates certificate conditions, while the structure-preserving network exhibits no sampled positivity, decrease, or prescribed-margin violation on 232,761 states. Trajectory, uncertainty, and 32-state compositional tests remain consistent with the theory. These results justify the method as a strong candidate-generation and validation pipeline. They do not yet justify an unconditional global guarantee. For intelligent-control deployment, the final scientific standard should be: architecture-aware learning, counterexample-rich testing, explicit uncertainty accounting, and a machine-checkable derivative proof on the claimed operating domain.")

    section(doc,"Declarations",1)
    add_body(doc,"Competing interests. The author declares no competing interests.")
    add_body(doc,"Funding. No external funding is reported for this synthesized study.")
    add_body(doc,"Data and code availability. The audited baseline PDF and related local literature are contained in the project folder. The public baseline repository is DeepDynaSim/DeepLyapunovFunction. The new deterministic MATLAB experiment is article_build/simulate_neural_lyapunov.m; its CSV metrics, MAT checkpoint, and publication figures are in article_build/results.")
    add_body(doc,"Author contributions. C.U.: conceptualization, methodology, software, validation, formal analysis, visualization, and manuscript preparation.")
    add_body(doc,"AI-assisted drafting disclosure. Generative AI assistance was used to organize the literature synthesis, scaffold reproducible document-generation code, and support language editing. The mathematical derivations, source audit, simulation outputs, and scientific claims were checked against the stated equations and deterministic MATLAB results; responsibility for publication remains with the author.")

    section(doc,"Appendix A. Derivations and audit details",1)
    section(doc,"A.1 Closed-form Lyapunov matrix",2)
    add_body(doc,"Substituting the symmetric matrix P=[[p11,p12],[p12,p22]] into AᵀP+PA=-I yields three independent linear equations. Their solution is p11=17/48, p12=7/24, and p22=5/3. The leading principal minors are positive, and the eigenvalues reported in Eq. (13) confirm P≻0. The nonlinear term cancels because yᵀJy=0 for every y when J is skew symmetric.")
    section(doc,"A.2 Finite-escape calculation",2)
    add_body(doc,"Separating variables in ẋ=-x² gives -1/x=t+C and x(t)=x0/(1+x0t). Negative x0 produces a pole at -1/x0. The paper's x0=-0.5 audit therefore has finite escape at t=2. In contrast, ẋ=-x³ yields x(t)=x0/sqrt(1+2x0²t), which is defined for all nonnegative time and converges to zero.")
    section(doc,"A.3 Reproducibility checklist",2)
    checklist_bullet_id = create_numbering(doc, bullet=True)
    for item in [
        "MATLAB R2024b with Control System Toolbox and Deep Learning Toolbox.",
        "Random seed 20260826; CPU execution; single precision for network training.",
        "Run simulate_neural_lyapunov from a filesystem path supported by MATLAB; outputs are written beside the script.",
        "Confirm ||AᵀP+PA+I||F=0 to displayed precision before training.",
        "Regenerate all seven figures and compare model_verification_metrics.csv, trajectory_metrics.csv, robustness_metrics.csv, and scaling_metrics.csv.",
        "For a formal paper claim, add a verifier log that proves mθ(x)<0 on the full selected domain or on an invariant sublevel set."
    ]:
        add_list_item(doc,item,checklist_bullet_id)

    section(doc,"References",1)
    references = [
        ("[1] Lyapunov, A.M. (1992). The General Problem of the Stability of Motion. Taylor & Francis.","https://doi.org/10.1080/00411457108231482"),
        ("[2] Khalil, H.K. (2002). Nonlinear Systems, 3rd ed. Prentice Hall.","https://www.pearson.com/en-us/subject-catalog/p/nonlinear-systems/P200000003223"),
        ("[3] Haddad, W.M., and Chellaboina, V. (2008). Nonlinear Dynamical Systems and Control: A Lyapunov-Based Approach. Princeton University Press.","https://doi.org/10.1515/9781400832243"),
        ("[4] Jiang, Z.-P., Teel, A.R., and Praly, L. (1994). Small-gain theorem for ISS systems and applications. Mathematics of Control, Signals and Systems, 7, 95-120.","https://doi.org/10.1007/BF01211469"),
        ("[5] Dashkovskiy, S.N., Rüffer, B.S., and Wirth, F.R. (2007). An ISS small gain theorem for general networks. Mathematics of Control, Signals, and Systems, 19, 93-122.","https://doi.org/10.1007/s00498-007-0014-8"),
        ("[6] Parrilo, P.A. (2000). Structured Semidefinite Programs and Semialgebraic Geometry Methods in Robustness and Optimization. PhD thesis, California Institute of Technology.","https://thesis.library.caltech.edu/1647/"),
        ("[7] Prajna, S., Papachristodoulou, A., and Parrilo, P.A. (2004). SOSTOOLS: Sum of squares optimization toolbox for MATLAB. Proceedings of the IEEE CDC.","https://doi.org/10.1109/CDC.2002.1184414"),
        ("[8] Uyulan, C. (2023). Efficient Computation of Lyapunov Functions Using Deep Neural Networks for the Assessment of Stability in Controller Design. Research Square preprint.","https://doi.org/10.21203/rs.3.rs-3698604/v1"),
        ("[9] Grüne, L. (2021). Computing Lyapunov functions using deep neural networks. Journal of Computational Dynamics, 8(2), 131-152.","https://doi.org/10.3934/jcd.2021006"),
        ("[10] Grüne, L. (2021). Overcoming the curse of dimensionality for approximating Lyapunov functions with deep neural networks under a small-gain condition. IFAC-PapersOnLine, 54(9), 317-322.","https://doi.org/10.1016/j.ifacol.2021.06.152"),
        ("[11] Richards, S.M., Berkenkamp, F., and Krause, A. (2018). The Lyapunov Neural Network: Adaptive stability certification for safe learning of dynamical systems. PMLR 87, 466-476.","https://proceedings.mlr.press/v87/richards18a.html"),
        ("[12] Chang, Y.-C., Roohi, N., and Gao, S. (2019). Neural Lyapunov control. Advances in Neural Information Processing Systems 32.","https://proceedings.neurips.cc/paper/2019/hash/2647c1dba23bc0e0f9cdf75339e120d2-Abstract.html"),
        ("[13] Abate, A., Ahmed, D., Giacobbe, M., and Peruffo, A. (2021). Formal synthesis of Lyapunov neural networks. IEEE Control Systems Letters, 5(3), 773-778.","https://doi.org/10.1109/LCSYS.2020.3005328"),
        ("[14] Gaby, N., Zhang, F., and Ye, X. (2021). Lyapunov-Net: A deep neural network architecture for Lyapunov function approximation. arXiv:2109.13359.","https://arxiv.org/abs/2109.13359"),
        ("[15] Boffi, N., Tu, S., Matni, N., Slotine, J.-J., and Sindhwani, V. (2021). Learning stability certificates from data. PMLR 155, 1341-1350.","https://proceedings.mlr.press/v155/boffi21a.html"),
        ("[16] Zhou, R., Quartz, T., De Sterck, H., and Liu, J. (2022). Neural Lyapunov control of unknown nonlinear systems with stability guarantees. Advances in Neural Information Processing Systems 35.","https://proceedings.neurips.cc/paper_files/paper/2022/hash/bba3160c42f4c1d23175b5abf04347f5-Abstract-Conference.html"),
        ("[17] Dawson, C., Gao, S., and Fan, C. (2023). Safe control with learned certificates: A survey of neural Lyapunov, barrier, and contraction methods for robotics and control. IEEE Transactions on Robotics, 39(3), 1749-1767.","https://doi.org/10.1109/TRO.2022.3232542"),
        ("[18] Zhang, S., Xiu, Y., Qu, G., and Fan, C. (2023). Compositional neural certificates for networked dynamical systems. PMLR 211, 272-285.","https://proceedings.mlr.press/v211/zhang23a.html"),
        ("[19] Wu, J., Clark, A., Kantaros, Y., and Vorobeychik, Y. (2023). Neural Lyapunov control for discrete-time systems. Advances in Neural Information Processing Systems 36.","https://papers.neurips.cc/paper_files/paper/2023/hash/08bf1773e94763b6cc366ee7c6582f27-Abstract-Conference.html"),
        ("[20] Yang, L., Dai, H., Shi, Z., Hsieh, C.-J., Tedrake, R., and Zhang, H. (2024). Lyapunov-stable neural control for state and output feedback: A novel formulation. PMLR 235, 56033-56046.","https://proceedings.mlr.press/v235/yang24f.html"),
        ("[21] Zhang, S., and Fan, C. (2024). Learning to stabilize high-dimensional unknown systems using Lyapunov-guided exploration. PMLR 242, 52-67.","https://proceedings.mlr.press/v242/zhang24a.html"),
        ("[22] Liu, J., Fitzsimmons, M., Zhou, R., and Meng, Y. (2024). Formally verified physics-informed neural control Lyapunov functions. arXiv:2409.20528.","https://arxiv.org/abs/2409.20528"),
        ("[23] Debauche, V., Edwards, A., Jungers, R.M., and Abate, A. (2025). Formal synthesis of Lyapunov stability certificates for linear switched systems using ReLU neural networks. PMLR 288, 352-364.","https://proceedings.mlr.press/v288/debauche25a.html"),
        ("[24] Shi, Z., Li, H., Hsieh, C.-J., and Zhang, H. (2026). Certified training with branch-and-bound for Lyapunov-stable neural control. PMLR 331, 788-808.","https://proceedings.mlr.press/v331/shi26a.html"),
        ("[25] Huh, S., Tonietti, G., and Bicchi, A. (2008). Neural network based robust adaptive control for a variable stiffness actuator. 16th Mediterranean Conference on Control and Automation, 1028-1033.","https://ieeexplore.ieee.org/document/4602116"),
        ("[26] Hornik, K., Stinchcombe, M., and White, H. (1989). Multilayer feedforward networks are universal approximators. Neural Networks, 2(5), 359-366.","https://doi.org/10.1016/0893-6080(89)90020-8"),
        ("[27] Kingma, D.P., and Ba, J. (2015). Adam: A method for stochastic optimization. ICLR.","https://arxiv.org/abs/1412.6980"),
        ("[28] Sontag, E.D. (1989). A universal construction of Artstein's theorem on nonlinear stabilization. Systems & Control Letters, 13(2), 117-123.","https://doi.org/10.1016/0167-6911(89)90028-5"),
        ("[29] Ames, A.D., Xu, X., Grizzle, J.W., and Tabuada, P. (2017). Control barrier function based quadratic programs for safety critical systems. IEEE Transactions on Automatic Control, 62(8), 3861-3876.","https://doi.org/10.1109/TAC.2016.2638961"),
        ("[30] Johansen, T.A. (2000). Computation of Lyapunov functions for smooth nonlinear systems using convex optimization. Automatica, 36(11), 1617-1626.","https://doi.org/10.1016/S0005-1098(00)00088-1")
    ]
    for text, url in references:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.28)
        p.paragraph_format.first_line_indent = Inches(-0.28)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(text + " ")
        set_run_font(r,size=9,color=BLACK)
        label = "DOI record" if "doi.org" in url else "Source record"
        add_hyperlink(p,label,url,color=BLUE,underline=False)

    doc.core_properties.title = "Structure-Preserving Neural Lyapunov Certificates for Intelligent Nonlinear Control"
    doc.core_properties.subject = "Neural Lyapunov stability, intelligent control, robustness, and compositional verification"
    doc.core_properties.author = "Çağlar Uyulan"
    doc.core_properties.keywords = "Lyapunov; neural networks; intelligent control; stability; robustness; verification"
    doc.core_properties.comments = "Simulation-validated research manuscript generated from the local project corpus."
    doc.settings.element.append(OxmlElement("w:updateFields"))
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
