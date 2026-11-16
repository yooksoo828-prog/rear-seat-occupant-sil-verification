#!/usr/bin/env python3
"""기말고사 제출물(Word 최종보고서, PowerPoint 발표자료) 자동 생성기.

  pip install python-docx python-pptx
  python deliverables/build_deliverables.py [--date YYYY-MM-DD]

입력(읽기 전용): sil_main/results_main/{summary.csv, tc11_side_by_side.csv, baseline_verification.csv,
                 trials.csv, config.json}, sil_main/baseline/baseline_v1.0.json
출력: deliverables/후석탑승자감지_SIL검증_최종보고서_v1.0.docx
      deliverables/후석탑승자감지_SIL검증_발표자료_v1.0.pptx

sil_prelim/, sil_main/baseline/, sil_main/results_main/ 의 파일은 읽기만 하며 수정하지 않는다.
수치는 모두 결과 파일에서 읽어 오고, 요청서와 다른 값이 나오면 중단한다.
"""
import collections
import csv
import datetime
import hashlib
import json
import sys
import zlib
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn as pqn
from pptx.util import Emu, Inches, Pt as PPt

# ----------------------------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent                      # deliverables/
ROOT = HERE.parent
RES = ROOT / "sil_main" / "results_main"
BASELINE = ROOT / "sil_main" / "baseline" / "baseline_v1.0.json"
DOCX_OUT = HERE / "후석탑승자감지_SIL검증_최종보고서_v1.0.docx"
PPTX_OUT = HERE / "후석탑승자감지_SIL검증_발표자료_v1.0.pptx"

FONT = "맑은 고딕"
NAVY, SLATE, LIGHT, PALE, GRID = "1B365D", "4A6FA5", "EEF2F8", "F6F8FB", "BFC8D6"
RED, GREEN, AMBER, GRAY = "B03A48", "2E7D5B", "B7791F", "5B6577"

REPO = "https://github.com/yooksoo828-prog/rear-seat-occupant-sil-verification"
REPORT_URL = REPO + "/blob/main/sil_main/results_main/ISO29119_Audit_Report.md"
TITLE = "초음파 센서 기반 후석 탑승자 감지 시스템 SIL 검증 결과 보고서"
SUBTITLE = "ISO/IEC/IEEE 29119-3 표준 기반 기준선 관리 및 통계적 검증"
DOC_ID = "ISO29119-SIL-RSPD-v1.0"
EXPECTED_SHA = "79f21ce910853ee7358d97c031a7553258a9fb2151bdcdaca17db3c1ea205f6d"
EXPECTED_STATUS = {"목표 충족(통계 확인)": 49, "일치": 27, "기준 충족(전 시행)": 12, "불합격": 3, "미실행": 4,
                   "기록(합격 판정 없음)": 44, "가정 기반 민감도 기록": 13}
STATUS_ORDER = ["목표 충족(통계 확인)", "일치", "기준 충족(전 시행)", "기록(합격 판정 없음)", "가정 기반 민감도 기록", "미실행", "불합격"]

COMMITS = [  # 5단계 생명주기 커밋(저장소 이력)
    ("1", "014bbbb", "chore(prelim)", "예비 SIL 모델·결과 보존(sil_prelim/)"),
    ("2", "5586f96", "feat(main)", "TC-01~16 시험 하니스, 기준선 확정 전 점검 기록"),
    ("3", "b6e1368", "build(baseline)", "기준선 v1.0 동결(D1~D8) + 태그 v1.0-baseline"),
    ("4", "7320969", "test(main)", "본시험 결과와 87항목 기준선 대조 기록"),
    ("5", "af7424d", "docs(iso29119)", "감사 보고서 생성기·README·CI 검증"),
]
ISSUES = [  # GitHub Issues(모두 Open)
    ("#1", "INC-01·02", "TC-04b-1/2 정지 화물(R1) 100% 오검출", "이상 보고 / SIL 한계"),
    ("#2", "INC-03", "TC-11 50 °C 보정 미적용 R0 오검출, 보정 채택 검토(D3)", "이상 보고 / 설계 검토"),
    ("#3", "D1", "실물 대상(O-A/B/C/S) 치수 확보, 착좌 위치 분포", "후속 조치 / TBR"),
    ("#4", "D4·D8", "초기 공석 d_empty 캘리브레이션, 시동-센서 전원 연동", "후속 조치 / TBR"),
]
TC_NAMES = {
    "TC-01": "빈 좌석 오검출", "TC-02": "최소 크기 대상 감지(O-A·O-B → R1·R2 대체)", "TC-03": "큰 체형 감지(O-C → R3 대체)",
    "TC-04": "화물 오검출(낮은 화물 R0, 같은 높이 화물 R1)", "TC-05": "흡음 표면·손실률·편향 민감도", "TC-06": "상체 기울임 60초",
    "TC-07": "임계값 경계·히스테리시스(±50% 민감도 포함)", "TC-08": "전원 인가 후 최초 판정", "TC-09": "상태 변화 응답(3초 이내, 1초 유지)",
    "TC-10": "같은 자세 60초 유지", "TC-11": "온도 0·20·50 °C × 보정 유/무", "TC-12": "소형 대상 O-S",
    "TC-13": "에코 없음 연속 발생과 복구", "TC-14": "유효 범위 밖 값 치환(1·401 cm)", "TC-15": "결과 전달 2초 중단 후 재개",
    "TC-16": "측정 주기 설정·로그 간격 점검",
}
SHORT = {"목표 충족(통계 확인)": "목표 충족", "일치": "일치", "기준 충족(전 시행)": "전 시행 충족", "기록(합격 판정 없음)": "기록",
         "가정 기반 민감도 기록": "민감도 기록", "미실행": "미실행", "불합격": "불합격"}

D_TABLE = [
    ("D1", "대상·반사면", "가상 반사면 R0~R3 = 5/20/40/60 cm, H_s 100 cm. O-A/B/C 원 조건·TC-12(O-S) 미실행"),
    ("D2", "T_db 시간 기준", "T_db 0.5 s, 후보 유지 시간은 측정 요청 시각 기준. 요청·수신 시각 모두 로그"),
    ("D3", "온도 구성", "기준 20 °C·보정 없음. TC-11은 0·20·50 °C 보정 유/무 병기. 보정 채택·SR-09 전체 충족 선언은 보류"),
    ("D4", "d_empty", "빈 좌석 기준 거리 100 cm 고정(초기 실측 보정은 후속)"),
    ("D5", "시행 횟수", "TC-01·TC-04 및 TC-11 각 조건 300회, 대상 합산 집계 금지"),
    ("D6", "합격 목표", "미검출 1%, 오검출 5%, 미확정 1%, 응답 3 s·정답 유지, 뒤집힘 0회. 사후 완화 금지"),
    ("D7", "입력 가정", "TC-04b-2 움직임 1 cm·0.25 Hz, TC-05 한 요인씩, 05a·05b 동일 모델, TC-07c ±50%"),
    ("D8", "전원 모델", "TC-08은 t = 0 전원 인가. 차량 시동·센서 전원 관계는 후속"),
]


# ----------------------------------------------------------------------------------------------
# 데이터 읽기
# ----------------------------------------------------------------------------------------------
def read_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pct(v):
    x = float(v) * 100
    return f"{x:.3f}".rstrip("0").rstrip(".") + "%"


def load():
    d = {"summary": read_csv(RES / "summary.csv"), "tc11": read_csv(RES / "tc11_side_by_side.csv"),
         "verif": read_csv(RES / "baseline_verification.csv"), "trials": read_csv(RES / "trials.csv"),
         "config": json.loads((RES / "config.json").read_text(encoding="utf-8"))}
    d["sha"] = sha256(BASELINE)
    d["cnt"] = collections.Counter(r["status"] for r in d["summary"])
    # ----- 검증: 요청서·보고서 수치와 다르면 중단
    assert d["sha"] == EXPECTED_SHA, "기준선 SHA-256 불일치"
    assert len(d["summary"]) == 152 and len(d["verif"]) == 87 and len(d["trials"]) == 9855
    assert all(r["일치"] == "일치" for r in d["verif"])
    assert {k: d["cnt"].get(k, 0) for k in EXPECTED_STATUS} == EXPECTED_STATUS, d["cnt"]
    base = int(d["config"]["config"]["seed"]["base_seed"])
    n_ok = sum(1 for t in d["trials"] if any(
        base * 2 ** 64 + zlib.crc32(f"{t['tc']}/{c}".encode()) * 2 ** 20 + int(t["trial"]) == int(t["seed"])
        for c in {t["cond"], t["cond"].split("/")[0]}))
    assert n_ok == 9855, "시드 재계산 불일치"
    # TC-11 R0 오검출 행
    d["r0"] = {int(r["온도(°C)"]): r for r in d["tc11"] if r["대상"].startswith("R0") and r["지표"] == "오검출률"}
    assert d["r0"][50]["보정 없음 k/n"] == "300/300" and d["r0"][50]["보정 있음 k/n"] == "0/300"
    assert pct(d["r0"][50]["보정 있음 상한95"]) == "0.994%"
    by_tc = collections.defaultdict(collections.Counter)
    for r in d["summary"]:
        by_tc[r["tc"]][r["status"]] += 1
    d["by_tc"] = dict(sorted(by_tc.items()))
    assert len(d["by_tc"]) == 16
    return d


# 음속 계산(sil/config.py 의 c(T) = 331.4 + 0.6 T)
C50 = 331.4 + 0.6 * 50
C_FIX = 340.0
SCALE = C_FIX / C50
D_R0 = 100 - 5
D_APP = D_R0 * SCALE
DELTA_R0 = 100 - D_APP
DELTA_EMPTY = 100 - 100 * SCALE
assert abs(C50 - 361.4) < 1e-9 and abs(DELTA_R0 - 10.63) < 0.005


# ==============================================================================================
# Word
# ==============================================================================================
def rgb(h):
    return RGBColor.from_string(h)


def set_font(run, size=None, bold=None, color=None, font=FONT, italic=None):
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), font)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    if color:
        run.font.color.rgb = rgb(color)


def style_font(style, size, bold=False, color=None):
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.bold = bold
    if color:
        style.font.color.rgb = rgb(color)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]


def shade(cell, hex_):
    tcpr = cell._element.get_or_add_tcPr()
    for old in tcpr.findall(qn("w:shd")):
        tcpr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_)
    tcpr.append(shd)


def cell_borders(cell, color=GRID, sz=4, sides=("top", "left", "bottom", "right"), val="single"):
    tcpr = cell._element.get_or_add_tcPr()
    b = tcpr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcpr.append(b)
    for s in sides:
        e = b.find(qn(f"w:{s}"))
        if e is None:
            e = OxmlElement(f"w:{s}")
            b.append(e)
        e.set(qn("w:val"), val)
        e.set(qn("w:sz"), str(sz))
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), color)


def cell_margins(cell, top=60, bottom=60, left=90, right=90):
    tcpr = cell._element.get_or_add_tcPr()
    m = OxmlElement("w:tcMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tcpr.append(m)


def para_fmt(p, before=0, after=0, line=1.2, align=None, keep_next=False):
    pf = p.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
    if align is not None:
        p.alignment = align
    if keep_next:
        pf.keep_with_next = True


def write(cell_or_par, text, size=9.5, bold=False, color=None, align=None, font=FONT, first=True, before=0, after=0):
    """셀(또는 문단)에 텍스트 쓰기. '**굵게**' 표기를 지원."""
    p = cell_or_par.paragraphs[0] if (first and hasattr(cell_or_par, "paragraphs")) else (
        cell_or_par.add_paragraph() if hasattr(cell_or_par, "add_paragraph") else cell_or_par)
    para_fmt(p, before, after, 1.15, align)
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        set_font(r, size, bold or (i % 2 == 1), color, font)
    return p


def table(doc, headers, rows, widths, size=9, align=None, zebra=True, bold_first=False, hl=None):
    """네이비 헤더 표. align: 열별 'l'/'c'/'r'. hl: {행 인덱스: 채움색}."""
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    align = align or ["l"] * len(headers)
    amap = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.width = Cm(widths[i])
        shade(c, NAVY)
        cell_borders(c, NAVY)
        cell_margins(c)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        write(c, h, size, True, "FFFFFF", WD_ALIGN_PARAGRAPH.CENTER)
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        cant = OxmlElement("w:cantSplit")
        t.rows[-1]._tr.get_or_add_trPr().append(cant)
        for i, v in enumerate(row):
            c = cells[i]
            c.width = Cm(widths[i])
            cell_borders(c)
            cell_margins(c)
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            fill = (hl or {}).get(ri) or (PALE if zebra and ri % 2 == 1 else None)
            if fill:
                shade(c, fill)
            write(c, str(v), size, bold_first and i == 0, None, amap[align[i]])
    # 표가 쪽 경계에서 헤더만 남거나 쪼개지지 않도록: 작은 표는 통째로, 큰 표는 헤더+첫 행을 붙임
    n_keep = len(t.rows) - 1 if len(rows) <= 9 else 2
    for row in t.rows[:n_keep]:
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.keep_with_next = True
    return t


def spacer(doc, pts=4):
    p = doc.add_paragraph()
    para_fmt(p, 0, 0, 1.0)
    r = p.add_run("")
    r.font.size = Pt(pts)
    p.paragraph_format.space_after = Pt(pts)
    return p


def callout(doc, title, lines, width=17.0, fill=LIGHT, bar=NAVY, size=9.5):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    c = t.rows[0].cells[0]
    c.width = Cm(width)
    shade(c, fill)
    cell_borders(c, fill, 4)
    cell_borders(c, bar, 36, sides=("left",))
    cell_margins(c, 100, 100, 170, 140)
    write(c, title, size + 0.5, True, bar)
    for ln in lines:
        write(c, ln, size, False, None, first=False, before=2)
    return t


def h1(doc, text, page_break=True):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph(style="Heading 1")
    para_fmt(p, 0 if page_break else 22, 8, 1.1, keep_next=True)
    r = p.add_run(text)
    set_font(r, 17, True, NAVY)
    pPr = p._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    bt = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "12"), ("space", "4"), ("color", SLATE)):
        bt.set(qn(f"w:{k}"), v)
    bd.append(bt)
    pPr.append(bd)
    return p


def h2(doc, text):
    p = doc.add_paragraph(style="Heading 2")
    para_fmt(p, 10, 4, 1.1, keep_next=True)
    r = p.add_run(text)
    set_font(r, 12, True, NAVY)
    return p


def body(doc, text, size=10, after=4, before=0, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = doc.add_paragraph()
    para_fmt(p, before, after, 1.35, align)
    parts = text.split("**")
    for i, part in enumerate(parts):
        if part:
            set_font(p.add_run(part), size, i % 2 == 1)
    return p


def bullets(doc, items, size=10):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        para_fmt(p, 0, 2, 1.3)
        parts = it.split("**")
        for i, part in enumerate(parts):
            if part:
                set_font(p.add_run(part), size, i % 2 == 1)


def caption(doc, text):
    p = doc.add_paragraph()
    para_fmt(p, 2, 8, 1.1)
    set_font(p.add_run(text), 8.5, False, GRAY, italic=True)


def add_field(par, instr, size=8.5, color=GRAY):
    for kind, txt in (("begin", None), (None, instr), ("end", None)):
        r = par.add_run()
        set_font(r, size, False, color)
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            r._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = txt
            r._r.append(it)


TCPR_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
             "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
             "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]


def reorder(el, order):
    idx = {n: i for i, n in enumerate(order)}
    kids = list(el)
    kids.sort(key=lambda k: idx.get(k.tag.split("}")[1], 999))
    for k in kids:
        el.remove(k)
    for k in kids:
        el.append(k)


def fix_xml_order(doc):
    parts = [doc.element.body, doc.sections[0].header._element, doc.sections[0].footer._element]
    for root in parts:
        for tcpr in root.iter(qn("w:tcPr")):
            reorder(tcpr, TCPR_ORDER)
        for ppr in root.iter(qn("w:pPr")):
            reorder(ppr, PPR_ORDER)


def build_docx(d, date):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
    sec.different_first_page_header_footer = True
    for name, size, bold in (("Normal", 10, False), ("Heading 1", 17, True), ("Heading 2", 12, True), ("List Bullet", 10, False)):
        style_font(doc.styles[name], size, bold, NAVY if name.startswith("Heading") else None)
    # 머리글·바닥글(표지 제외)
    hp = sec.header.paragraphs[0]
    para_fmt(hp, 0, 0, 1.0, WD_ALIGN_PARAGRAPH.RIGHT)
    set_font(hp.add_run("후석 탑승자 감지 SIL 검증 최종보고서  |  v1.0-baseline"), 8.5, False, GRAY)
    fp = sec.footer.paragraphs[0]
    para_fmt(fp, 0, 0, 1.0, WD_ALIGN_PARAGRAPH.CENTER)
    set_font(fp.add_run("- "), 8.5, False, GRAY)
    add_field(fp, "PAGE")
    set_font(fp.add_run(" / "), 8.5, False, GRAY)
    add_field(fp, "NUMPAGES")
    set_font(fp.add_run(" -"), 8.5, False, GRAY)

    cnt = d["cnt"]
    # ------------------------------------------------------------------ 표지
    spacer(doc, 40)
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    c.width = Cm(17.0)
    shade(c, NAVY)
    cell_borders(c, NAVY)
    cell_margins(c, 500, 500, 400, 400)
    write(c, "Software-in-the-Loop Verification Report", 10.5, False, "AEC1E0")
    write(c, TITLE, 25, True, "FFFFFF", first=False, before=12)
    write(c, SUBTITLE, 13.5, False, "D6E0F0", first=False, before=14)
    spacer(doc, 26)
    info = [
        ("문서 ID", DOC_ID),
        ("기준선 버전", "v1.0-baseline  (2026-11-11 김윤수 확정, 결정 D1~D8)"),
        ("SHA-256", d["sha"]),
        ("작성일", date),
        ("작성자", "학번 / 성명 :  ______________  /  ______________      (GitHub: yooksoo828-prog)"),
        ("GitHub 저장소", REPO),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in info:
        cells = t.add_row().cells
        cells[0].width, cells[1].width = Cm(3.6), Cm(13.4)
        shade(cells[0], LIGHT)
        for cc in cells:
            cell_borders(cc)
            cell_margins(cc, 90, 90, 120, 120)
            cc.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        write(cells[0], k, 10, True, NAVY)
        mono = k == "SHA-256"
        write(cells[1], v, 8.6 if mono else 10, False, None, font="Consolas" if mono else FONT)
    spacer(doc, 30)
    body(doc, "본 보고서는 `sil_main/results_main/`의 검증된 결과 데이터와 통합 감사 보고서(ISO29119_Audit_Report.md)를 요약한 것이며, "
              "152행·87항목 전체 표는 아래 GitHub 저장소에서 확인할 수 있다.".replace("`", ""), 9.5, 4)
    body(doc, REPORT_URL, 8.5, 0)

    # ------------------------------------------------------------------ 1장
    h1(doc, "1장. 프로젝트 개요 및 SIL 시스템 아키텍처")
    h2(doc, "1.1 연구 목적")
    body(doc, "초음파 거리 센서 한 개로 후석의 점유 상태(OCCUPIED / UNOCCUPIED / UNKNOWN)를 판단하는 소프트웨어를, 실차 없이 **SIL(Software-in-the-Loop)** 로 검증한다. "
              "목표는 단순히 코드를 구현하는 데 그치지 않고, 검증 결과가 **신뢰할 수 있고(통계적 근거), 다시 만들 수 있으며(재현성), 요구사항과 연결되는(표준 추적성)** "
              "심사 가능한 체계를 갖추는 것이다. 이를 위해 ISO/IEC/IEEE 29119-3 시험 문서 체계와 Git 기반 형상 관리를 함께 적용했다.")
    callout(doc, "핵심 질문", [
        "① 판정 결과가 통계적으로 목표(미검출 1%, 오검출 5%)를 만족하는가?   ② 같은 입력으로 같은 결과를 다시 얻을 수 있는가?   "
        "③ 모든 요구사항(SR)이 시험(TC)과 결과로 추적되는가?"])
    h2(doc, "1.2 SIL 3단 파이프라인")
    t = doc.add_table(rows=2, cols=5)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    wd = [4.9, 0.9, 5.3, 0.9, 5.0]
    heads = ["① 센서 물리·환경 모델", None, "② 신호처리·판정 로직", None, "③ 독립 검증 하네스"]
    bodies = ["초음파 ToF 거리 생성\n음속 c(T) = 331.4 + 0.6T\n잡음·손실·편향·온도\n(sil/sensor_model.py 외)",
              None,
              "중앙값 필터(M = 5)\n히스테리시스 10 / 5 cm\n디바운스 0.5 s, 이상 시 UNKNOWN\n(sil/detector.py)",
              None,
              "TC-01~16, 정답 신호\n단측 95% 통계 판정\n기준선 대조, 로그 기록\n(main_lib/, run_main.py)"]
    for i in range(5):
        for r_i in (0, 1):
            c = t.rows[r_i].cells[i]
            c.width = Cm(wd[i])
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if i % 2 == 1:
                cell_borders(c, "FFFFFF", 4, val="nil")
                if r_i == 1:
                    write(c, "▶", 16, True, SLATE, WD_ALIGN_PARAGRAPH.CENTER)
            else:
                cell_borders(c, NAVY if r_i == 0 else GRID)
                cell_margins(c, 80, 80, 100, 100)
                if r_i == 0:
                    shade(c, NAVY)
                    write(c, heads[i], 10, True, "FFFFFF", WD_ALIGN_PARAGRAPH.CENTER)
                else:
                    shade(c, LIGHT)
                    c.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                    lines = bodies[i].split("\n")
                    write(c, lines[0], 9)
                    for ln in lines[1:]:
                        write(c, ln, 9, False, GRAY if ln.startswith("(") else None, first=False)
    caption(doc, "그림 1. SIL 3단 파이프라인. ③은 판정 알고리즘(②)과 분리된 정답·합격 판정 코드로 구성해 검증의 독립성을 확보했다.")
    table(doc, ["구분", "기준선 v1.0 설정값"], [
        ["센서 모델", "잡음 σ 1.0 cm, 측정 주기 0.1 s, 타임아웃 0.03 s, 손실률 0, 편향 0 (기준 수준)"],
        ["판정 로직", "필터 M = 5, Δ_on 10 cm / Δ_off 5 cm, T_db 0.5 s(요청 시각 기준), T_stale 1 s"],
        ["기하·환경", "H_s 100 cm, d_empty 100 cm, 유효 범위 2–400 cm, 기준 20 °C·보정 없음(고정 음속 340 m/s)"],
        ["평가", "관찰 3 s, 최초 판정 ≤ 1 s, 복구 ≤ 1 s, 응답 ≤ 3 s"],
    ], [2.8, 14.2], 9, ["c", "l"], bold_first=True)
    h2(doc, "1.3 요구사항 범위")
    body(doc, "시스템·소프트웨어 요구사항은 **SR-01~SR-14** 이며(SR-07은 (a) 최초 판정, (b) 상태 변화 응답으로 분리), 감지 성능(SR-01~04), 판정 로직·타이밍·온도(SR-05~09), "
              "이상 입력 처리와 출력 3값(SR-10~13), 미확정률(SR-14)로 구성된다. 모든 SR은 TC-01~16에 연결된다(추적성 행렬은 GitHub 감사 보고서 2.3절).")
    table(doc, ["SR", "내용", "연결 TC"], [
        ["SR-01 ~ 04", "점유 감지 성능(착석 미검출, 빈 좌석·화물 오검출)", "TC-01~06, 11"],
        ["SR-05", "거리 구분과 히스테리시스(임계값 경계)", "TC-07"],
        ["SR-06", "측정 요청 주기(설정값·로그 간격 점검)", "TC-16"],
        ["SR-07 (a)(b)", "전원 인가 후 최초 판정, 상태 변화 후 응답", "TC-08, 09"],
        ["SR-08", "자세 기울임·60초 유지 조건의 출력 안정", "TC-06, 10"],
        ["SR-09", "0–50 °C에서 SR-01~04·14 충족(온도 영향)", "TC-11"],
        ["SR-10 ~ 13", "에코 없음, 유효 범위 밖, 갱신 중단, 출력 3값 처리", "TC-13~15 (+TC-08)"],
        ["SR-14", "미확정(UNKNOWN) 비율 ≤ 1%", "TC-01~05, 11"],
    ], [2.8, 10.2, 4.0], 9, ["c", "l", "c"], bold_first=True)

    # ------------------------------------------------------------------ 2장
    h1(doc, "2장. 기준선(Baseline v1.0) 설계 및 무결성 통제", page_break=False)
    h2(doc, "2.1 핵심 설계 결정 D1~D8")
    body(doc, "시험을 실행하기 전에 입력 정의가 비어 있던 8개 항목을 2026-11-11에 결정(승인: 김윤수)하고 `baseline_v1.0.json`으로 고정했다. 결과를 본 뒤 값을 바꾸지 않는다.".replace("`", ""), 10, 4)
    table(doc, ["ID", "주제", "확정 내용"], [[a, b, c] for a, b, c in D_TABLE], [1.2, 2.8, 13.0], 9, ["c", "l", "l"], bold_first=True)
    h2(doc, "2.2 무결성 통제 3계층")
    table(doc, ["계층", "메커니즘", "결과"], [
        ["① 해시 고정", "기준선 파일의 SHA-256을 config.json에 기록하고 Git 태그 v1.0-baseline 으로 동결", "해시 일치 (파일·config·Git blob 동일)"],
        ["② 상수 자동 대조", "본시험 시작 시 기준선 JSON의 값과 코드에 들어간 값 87개를 비교하고, 하나라도 다르면 실행 중단", "87 / 87 일치"],
        ["③ 결정론적 시드", "seed = base_seed·2^64 + crc32('TC/조건')·2^20 + 시행 번호 (base_seed 20261111)", "9,855개 시행 시드 전부 재계산 일치"],
    ], [2.8, 9.7, 4.5], 9, ["c", "l", "l"], bold_first=True)
    spacer(doc, 4)
    callout(doc, "SHA-256 (baseline_v1.0.json)", [d["sha"]], size=9)
    spacer(doc, 4)
    bullets(doc, [
        "**재현성 검증:** `selftest.py`는 본시험을 임시 복사본에서 두 번 실행해 요약·시행·출력·사건 파일이 같은지 확인하고, 예비시험 5개 파일을 바이트 단위로 재현한다.".replace("`", ""),
        "**바이트 보존:** `.gitattributes`(`* -text`)로 줄바꿈 변환을 막아, 어떤 환경에서 체크아웃해도 기준선 해시가 달라지지 않는다.".replace("`", ""),
        "**집계 제외:** 사전점검(results_precheck)·추가 시험(results_p08r0)·확정 전 기록은 본시험 판정에 포함하지 않는다.",
    ])

    # ------------------------------------------------------------------ 3장
    h1(doc, "3장. 시험 설계 및 152개 조건 검증 결과 요약", page_break=False)
    h2(doc, "3.1 통계적 판정 기준")
    body(doc, "각 비율 지표는 시행 n회 중 오류 k회를 세어 **단측 95% 정확 이항(Clopper–Pearson) 상한**을 구하고 목표와 비교한다. "
              "k = 0이면 (1 − p_U)^n = 0.05 이므로, **n = 300회에서 오류가 없으면 상한은 0.994%** 로 1% 목표 이하임을 통계적으로 확인할 수 있다(최소 299회 필요).")
    from_stats = [("0", "0.994%", "4.87%"), ("1", "1.571%", "7.664%"), ("2", "2.084%", "10.124%"), ("3", "2.564%", "12.419%"), ("4", "3.025%", "14.61%")]
    table(doc, ["오류 k", "n = 300 상한 95%", "n = 60 상한 95%"], [list(x) for x in from_stats], [3.0, 5.0, 5.0], 9, ["c", "c", "c"])
    caption(doc, "표 1. 정확 이항 상한 (보고서 생성기가 독립 계산, selftest.py의 문서 수치와 일치)")
    table(doc, ["판정", "조건"], [
        ["목표 충족(통계 확인)", "관측 비율 ≤ 목표 이고 상한 95% ≤ 목표"],
        ["관측 충족(통계 미확인)", "관측 비율 ≤ 목표 이나 상한 95% > 목표(시행 수 부족). 이번 결과에는 해당 행 없음"],
        ["불합격", "관측 비율 > 목표. 목표를 바꾸지 않고 그대로 기록(D6)"],
    ], [4.6, 12.4], 9, ["l", "l"], bold_first=True)
    body(doc, "목표: 미검출 ≤ 1%, 오검출 ≤ 5%, 미확정 ≤ 1%, 응답 ≤ 3 s, 뒤집힘 0회.", 9.5, 2, 4)

    h2(doc, "3.2 종합 판정 분포 (152개 결과 행)")
    note = {"목표 충족(통계 확인)": "비율 지표, 상한 95% ≤ 목표", "일치": "결정적 시험의 기대 = 실제", "기준 충족(전 시행)": "모든 시행이 기준 만족",
            "기록(합격 판정 없음)": "참고 기록", "가정 기반 민감도 기록": "민감도 수준 기록(비율 행 10 + 전 시행 행 3), 판정 없음",
            "미실행": "입력 부재(O-A·O-B·O-C 원 조건, TC-12)", "불합격": "INC-01~03 (4장)"}
    rows = [[s, cnt[s], f"{cnt[s] / 152 * 100:.1f}%", note[s]] for s in STATUS_ORDER] + [["합계", 152, "100%", ""]]
    table(doc, ["상태", "행 수", "비율", "의미"], rows, [4.4, 1.7, 1.7, 9.2], 9, ["l", "c", "c", "l"], bold_first=True, hl={6: "FBE9EB"})
    caption(doc, "표 2. 152개 결과 행은 조건 × 지표 단위이며, 합격 판정이 없는 기록(57행)은 합격 건수에 포함하지 않는다.")

    h2(doc, "3.3 TC-01~16 종합 판정")
    rows = []
    hl = {}
    for i, (tc, c) in enumerate(d["by_tc"].items()):
        txt = " · ".join(f"{SHORT[s]} {c[s]}" for s in STATUS_ORDER if c.get(s))
        rows.append([tc, TC_NAMES[tc], sum(c.values()), txt])
        if c.get("불합격"):
            hl[i] = "FBE9EB"
    table(doc, ["TC", "내용", "행", "결과"], rows, [1.6, 7.2, 1.0, 7.2], 8.5, ["c", "l", "c", "l"], bold_first=True, hl=hl)
    caption(doc, "표 3. TC별 판정 요약. 전체 행 목록은 GitHub 보고서 부록 A 참조. 붉은 배경은 불합격이 있는 TC.")
    h2(doc, "3.4 시험 절차와 실행 순서")
    table(doc, ["단계", "명령 / 활동", "성격"], [
        ["1", "run_main.py status", "기준선 확정 전 상태 기록(모든 TC 미실행), 판정 아님"],
        ["2", "run_main.py precheck / additional", "사전점검(T_db 비교)·추가 시험 P-08-R0, 판정 아님·본시험 집계 제외"],
        ["3", "selftest.py", "통계 수치, 예비시험 재현, 재현성, 집계 재계산 점검"],
        ["4", "기준선 확정(2026-11-11)", "D1~D8 결정, baseline_v1.0.json 고정"],
        ["5", "실행 시작 시 87개 상수 대조", "기준선 JSON ↔ 코드 값, 불일치 시 중단"],
        ["6", "run_main.py main", "결정적 시험(TC-07·13·14·15·08) → 무작위 시험 → TC-16 순으로 실행, 결과를 본 뒤 기준을 바꾸지 않음"],
    ], [1.2, 5.6, 10.2], 9, ["c", "l", "l"])

    # ------------------------------------------------------------------ 4장
    h1(doc, "4장. 핵심 공학 분석 (온도 보정 효과 및 아키텍처 한계)", page_break=False)
    h2(doc, "4.1 TC-11: 50 °C 고온에서 온도 보정 효과")
    body(doc, "TC-11은 대상(빈 좌석·R2·R0) × 온도(0·20·50 °C) × 보정(없음·있음) 18개 조합을 각 300회 실행했다. 17개 조합은 목표를 충족했고, "
              "**50 °C·보정 없음·낮은 화물 R0 오검출만 300/300(100%)** 이었다. 보정을 켜면 같은 조건에서 0/300(상한 0.994%)으로 해소된다.")
    rows = []
    for T in (0, 20, 50):
        r = d["r0"][T]
        rows.append([f"{T} °C", r["보정 없음 k/n"], pct(r["보정 없음 상한95"]), r["보정 없음 판정"], r["보정 있음 k/n"], pct(r["보정 있음 상한95"]), r["보정 있음 판정"]])
    table(doc, ["온도", "보정 없음 k/n", "상한95", "판정", "보정 있음 k/n", "상한95", "판정"], rows, [1.7, 2.6, 1.8, 3.3, 2.6, 1.8, 3.2], 8.5,
          ["c", "c", "c", "c", "c", "c", "c"], hl={2: "FBE9EB"})
    caption(doc, "표 4. 낮은 화물 R0(5 cm) 오검출률(목표 ≤ 5%). 빈 좌석·R2의 미검출·오검출·미확정은 전 조합 0/300으로 목표 충족.")
    h2(doc, "4.2 원인: 음속 변화에 의한 거리 환산 오차")
    body(doc, f"음속 모델은 c(T) = 331.4 + 0.6·T 이므로 50 °C에서 **{C50:.1f} m/s** 이지만, 보정이 없으면 거리 환산에 고정 음속 **340 m/s** 를 쓴다. "
              f"실제 ToF가 짧아지므로 환산 거리는 {C_FIX:g}/{C50:.1f} = {SCALE:.4f} 배로 짧아진다.")
    table(doc, ["항목", "계산", "결과"], [
        ["R0 윗면까지 실제 거리", "H_s − R0 = 100 − 5", f"{D_R0:g} cm"],
        ["환산 거리(보정 없음)", f"{D_R0:g} × {SCALE:.4f}", f"{D_APP:.2f} cm"],
        ["Δ (d_empty = 100 cm 대비)", f"100 − {D_APP:.2f}", f"**{DELTA_R0:.2f} cm  ≥ Δ_on(10 cm) → OCCUPIED (오검출)**"],
        ["참고: 빈 좌석 Δ", f"100 − 100 × {SCALE:.4f}", f"{DELTA_EMPTY:.2f} cm  < 10 cm → TC-01 영향 없음"],
    ], [5.0, 4.6, 7.4], 9, ["l", "c", "l"], bold_first=True)
    caption(doc, "표 5. 잡음 없는 단순 계산. 추가 시험 P-08-R0의 계산값 10.63 cm와 일치.")
    callout(doc, "D3 유보 사유 — SR-09 전체 충족을 선언하지 않는 이유", [
        "• 온도 보정의 요구사항 채택 여부는 본시험 이후 결정하기로 했다(D3). 보정 없는 구성은 50 °C에서 SR-09를 충족하지 못했다.",
        "• TC-11은 빈 좌석·R2·R0, 0·20·50 °C, 보정 유/무 18개 조합만 다뤘으므로 SR-09는 **부분 커버**이다.",
        "• 따라서 보정 채택이 결정되고 시험 범위가 확장되기 전까지 SR-09 전체 충족 선언은 보류한다(GitHub Issue #2)."])
    h2(doc, "4.3 이상 보고 INC-01~03")
    table(doc, ["ID", "조건", "결과", "성격"], [
        ["INC-01", "TC-04 / 04b-1\n점유 대상과 같은 높이(R1 = 20 cm)의 정지 화물", "300/300 오검출\n(목표 ≤ 5%)", "단일 거리 센서의 구조적 한계"],
        ["INC-02", "TC-04 / 04b-2\n정지 화물(R1) 대 움직이는 점유 대상(±1.0 cm, 0.25 Hz)", "300/300 오검출\n(목표 ≤ 5%)", "INC-01과 같은 원인, 사후 완화 없이 기록(D6, D7)"],
        ["INC-03", "TC-11 / 11a-T50-nocomp/TC-04a\n50 °C, 보정 없음, 낮은 화물 R0", "300/300 오검출\n(보정 시 0/300)", "음속 변화, 보정 채택은 후속 결정(D3)"],
    ], [1.8, 7.3, 3.4, 4.5], 8.8, ["c", "l", "c", "l"], bold_first=True)
    h2(doc, "4.4 TC-04b가 소프트웨어 버그가 아닌 이유")
    bullets(doc, [
        "**입력이 같다:** 04b-1은 화물 윗면을 점유 대상과 같은 높이에 두고 같은 시드(= 같은 거리 이력)를 쓴다. 기록상 입력 동일 300/300, 출력 동일 300/300이다.",
        "**센서가 한 점만 본다:** 센서는 바로 아래 한 점까지의 거리만 측정하고 판정은 그 거리 이력(중앙값, Δ_on/Δ_off)만 쓴다. 높이가 같은 화물과 사람은 정보가 같다.",
        "**움직임도 쓰지 않는다:** 04b-2에서 점유 대상에 미세 움직임을 줘도 현재 알고리즘은 시간 변동을 쓰지 않아 출력 차이가 0/300이다(움직임 크기는 근거 없는 가정).",
        "**투명한 기록:** 합격선(5%)을 사후에 완화하거나 코드를 시험에 맞춰 고치지 않고 한계로 공식 기록했다(D6, D7). 개선은 새 기준선 버전으로만 가능하다.",
    ], 9.8)

    # ------------------------------------------------------------------ 5장
    h1(doc, "5장. 결론 및 형상·이슈 관리 증빙", page_break=False)
    h2(doc, "5.1 결론")
    body(doc, f"152개 결과 행 중 **목표 충족(통계 확인) 49, 결정적 시험 일치 27, 전 시행 기준 충족 12** 를 확인했고, 기준선·코드 87개 상수가 모두 일치하며 9,855개 시드가 재현된다. "
              f"불합격 3건(INC-01~03)과 미실행 4건은 숨기거나 기준을 바꾸지 않고 원인과 함께 기록했다. 결과는 SIL 모델과 입력 분포에 한정되며 실제 센서 성능을 입증하지 않는다.")
    bullets(doc, [
        "**성과:** 통계 기준(0.994%)·결정론적 재현성·SR↔TC 추적성을 갖춘 검증 체계를 구축했다.",
        "**한계:** 단일 거리 센서로는 같은 높이의 화물과 사람을 구분할 수 없으며, 고온에서는 온도 보정이 필요하다.",
        "**후속(TBR):** 실물 대상 치수 확보와 착좌 위치 분포, 초기 공석 d_empty 캘리브레이션, 시동-센서 전원 연동, 다중 특징량(시간 변동 등) 확장.",
    ])
    h2(doc, "5.2 GitHub 형상 관리 증빙")
    table(doc, ["단계", "커밋", "유형", "내용"], [[a, b, c, e] for a, b, c, e in COMMITS], [1.2, 2.2, 3.4, 10.2], 9, ["c", "c", "l", "l"])
    caption(doc, "표 6. 5단계 생명주기 커밋(이후 CLAUDE.md, 제출물 추가 커밋이 이어짐). 기준선 확정 커밋에 주석 태그 v1.0-baseline 을 부여했다.")
    table(doc, ["항목", "내용"], [
        ["태그", "v1.0-baseline — 주석 태그, 메시지에 SHA-256 포함. 기준선 확정 커밋(b6e1368)을 가리킴"],
        ["CI", "GitHub Actions `verify.yml`: main 브랜치 push·pull request 시 Python 3.11, numpy 설치 후 sil_main/에서 selftest.py 실행. 최근 두 커밋(af7424d, bb2b906)의 실행 모두 성공(success)".replace("`", "")],
        ["저장소", REPO],
    ], [2.6, 14.4], 9, ["l", "l"], bold_first=True)
    spacer(doc, 6)
    table(doc, ["Issue", "연계", "내용", "분류"], [list(x) for x in ISSUES], [1.5, 2.3, 9.0, 4.2], 9, ["c", "c", "l", "l"], bold_first=True)
    caption(doc, "표 7. 등록된 GitHub Issues 4건(모두 Open). 이상 보고 2건은 INC-01~03, 후속 조치 2건은 D1·D4·D8과 연결된다.")
    h2(doc, "5.3 ISO/IEC/IEEE 29119-3 산출물 대응")
    table(doc, ["29119-3 산출물", "이 프로젝트의 대응"], [
        ["Test Plan", "감사 보고서 1장, baseline_v1.0.json (범위·제외·판정 기준·D1~D8)"],
        ["Test Design / Procedure Specification", "감사 보고서 2장, sil_main/README.md, run_main.py, main_lib/"],
        ["Requirements Traceability", "trace_SR_TC_result.csv (SR → TC → 결과 상태)"],
        ["Test Environment / Data", "config.json (Python·NumPy·RNG·시드 규칙), sil/ 모델"],
        ["Test Result / Execution Log", "summary.csv(152행), trials.csv, output_log.csv, events.csv"],
        ["Test Incident Report", "감사 보고서 3.3절 INC-01~03, GitHub Issues #1·#2"],
        ["Test Completion Report", "감사 보고서 4장"],
    ], [5.6, 11.4], 9, ["l", "l"], bold_first=True)
    spacer(doc, 6)
    callout(doc, "전체 데이터 열람", [
        "152행 결과 표, 87항목 기준선 대조, 추적성 행렬 전체는 저장소의 통합 감사 보고서 부록에서 볼 수 있다.", REPORT_URL], size=9)
    doc.core_properties.title = TITLE
    doc.core_properties.subject = SUBTITLE
    doc.core_properties.author = "yooksoo828-prog"
    fix_xml_order(doc)
    doc.save(DOCX_OUT)


# ==============================================================================================
# PowerPoint
# ==============================================================================================
def prgb(h):
    return PRGB.from_string(h)


def run_font(run, size, bold=False, color="1F2937", font=FONT):
    f = run.font
    f.size, f.bold, f.name = PPt(size), bold, font
    f.color.rgb = prgb(color)
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(pqn(tag))
        if el is None:
            el = rpr.makeelement(pqn(tag), {})
            rpr.append(el)
        el.set("typeface", font)


def tbox(slide, x, y, w, h, paras, size=14, color="1F2937", bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         line=1.15, margin=0.05, space=4):
    """paras: 문자열 또는 (문자열, {size,bold,color,bullet}) 리스트. '**' 굵게 지원."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    if isinstance(paras, str):
        paras = [paras]
    for i, item in enumerate(paras):
        txt, o = (item, {}) if isinstance(item, str) else item
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = o.get("align", align)
        p.line_spacing = line
        p.space_after = PPt(o.get("space", space))
        if o.get("bullet"):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", "285750")
            pPr.set("indent", "-285750")
            bu = pPr.makeelement(pqn("a:buChar"), {"char": "•"})
            pPr.append(bu)
        parts = txt.split("**")
        for j, part in enumerate(parts):
            if part:
                r = p.add_run()
                r.text = part
                run_font(r, o.get("size", size), o.get("bold", bold) or j % 2 == 1, o.get("color", color))
    return tb


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = prgb(fill)
    if line:
        s.line.color.rgb = prgb(line)
        s.line.width = PPt(1)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def card(slide, x, y, w, h, value, label, fill=LIGHT, vcolor=NAVY, vsize=34, lsize=12):
    rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    rect(slide, x, y + 0.12, 0.07, h - 0.24, vcolor)
    tbox(slide, x + 0.15, y + 0.08, w - 0.25, h * 0.55, value, vsize, vcolor, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    tbox(slide, x + 0.1, y + h * 0.58, w - 0.2, h * 0.38, label, lsize, GRAY, False, PP_ALIGN.CENTER, MSO_ANCHOR.TOP, 1.05)


def ptable(slide, x, y, w, col_w, rows, headers, size=11, row_h=0.36, hl=None, align=None):
    n_r, n_c = len(rows) + 1, len(headers)
    gt = slide.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(w), Inches(row_h * n_r))
    tbl = gt.table
    tblPr = tbl._tbl.tblPr
    for a in ("bandRow", "firstRow"):
        tblPr.set(a, "0")
    sid = tblPr.find(pqn("a:tableStyleId"))
    if sid is not None:
        sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # No Style, Table Grid
    for i, cw in enumerate(col_w):
        tbl.columns[i].width = Inches(cw)
    for r in range(n_r):
        tbl.rows[r].height = Inches(row_h)
    align = align or [PP_ALIGN.LEFT] * n_c

    def setcell(cell, text, bold, color, fill, al):
        cell.fill.solid()
        cell.fill.fore_color.rgb = prgb(fill)
        cell.margin_left = cell.margin_right = Inches(0.07)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = al
        parts = str(text).split("**")
        for j, part in enumerate(parts):
            if part:
                r_ = p.add_run()
                r_.text = part
                run_font(r_, size, bold or j % 2 == 1, color)
        # 테두리
        tcPr = cell._tc.get_or_add_tcPr()
        for pos, tag in enumerate(("a:lnL", "a:lnR", "a:lnT", "a:lnB")):
            ln = tcPr.makeelement(pqn(tag), {"w": "9525"})
            sf = ln.makeelement(pqn("a:solidFill"), {})
            clr = sf.makeelement(pqn("a:srgbClr"), {"val": GRID})
            sf.append(clr)
            ln.append(sf)
            tcPr.insert(pos, ln)

    for c, h in enumerate(headers):
        setcell(tbl.cell(0, c), h, True, "FFFFFF", NAVY, PP_ALIGN.CENTER)
    for r, row in enumerate(rows, 1):
        fill = (hl or {}).get(r - 1) or ("FFFFFF" if r % 2 else PALE)
        for c, v in enumerate(row):
            setcell(tbl.cell(r, c), v, False, "1F2937", fill, align[c])
    return gt


def base_slide(prs, title, n, total=9):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, 13.333, 0.12, NAVY)
    tbox(s, 0.6, 0.32, 12.1, 0.8, title, 28, NAVY, True, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 0.65, 1.12, 1.4, 0.05, SLATE)
    tbox(s, 0.6, 7.02, 9, 0.3, "후석 탑승자 감지 SIL 검증  |  v1.0-baseline  |  ISO/IEC/IEEE 29119-3", 10, "8A94A6")
    tbox(s, 11.7, 7.02, 1.1, 0.3, f"{n} / {total}", 10, "8A94A6", False, PP_ALIGN.RIGHT)
    return s


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def build_pptx(d, date):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    cnt = d["cnt"]
    r0 = d["r0"]

    # ---------------- Slide 1 표지
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, 13.333, 7.5, NAVY)
    rect(s, 0.9, 2.05, 1.6, 0.07, "7F9CCB")
    tbox(s, 0.9, 1.2, 11, 0.5, "Software-in-the-Loop Verification  ·  ISO/IEC/IEEE 29119-3", 15, "AEC1E0")
    tbox(s, 0.9, 2.3, 11.6, 1.9, "초음파 센서 기반 후석 탑승자 감지 시스템\nSIL 검증 결과", 40, "FFFFFF", True, line=1.1)
    tbox(s, 0.9, 4.2, 11.6, 0.6, SUBTITLE, 20, "D6E0F0")
    rect(s, 0.9, 5.15, 11.5, 1.5, "27487A", shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    tbox(s, 1.15, 5.25, 11.0, 1.35, [
        ("발표자:  학번 / 성명  ______________ / ______________     (GitHub: yooksoo828-prog)", {"size": 15, "color": "FFFFFF"}),
        (f"GitHub:  {REPO}", {"size": 13, "color": "D6E0F0"}),
        (f"기준선:  v1.0-baseline   |   SHA-256 {d['sha'][:16]}…{d['sha'][-8:]}   |   {date}", {"size": 13, "color": "D6E0F0"}),
    ], 15, space=6)
    notes(s, "안녕하세요. 초음파 센서 기반 후석 탑승자 감지 소프트웨어를 SIL, 즉 소프트웨어 인 더 루프 방식으로 검증한 결과를 발표하겠습니다. "
             "이 프로젝트는 ISO/IEC/IEEE 29119-3 시험 문서 체계와 GitHub 기반 형상 관리를 적용했고, 검증 기준선은 v1.0-baseline 태그와 SHA-256 해시로 고정되어 있습니다. "
             "발표는 문제 정의, 시스템 구조, 통계 설계, 결과, 두 가지 심층 분석, 형상 관리, 결론 순서로 진행하겠습니다.")

    # ---------------- Slide 2 문제 정의
    s = base_slide(prs, "문제 정의 및 목표", 2)
    rect(s, 0.65, 1.55, 5.7, 4.95, PALE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 0.9, 1.7, 5.3, 0.5, "문제", 20, SLATE, True)
    tbox(s, 0.9, 2.3, 5.2, 4.0, [
        ("후석 점유 판단을 **단일 초음파 거리 센서**로 수행", {"bullet": True}),
        ("실차 없이 **SIL**로 성능·이상 입력 대응을 확인해야 함", {"bullet": True}),
        ("“돌아가는 코드”만으로는 **결과를 신뢰·재현·추적**할 수 없음", {"bullet": True}),
    ], 18, space=20, line=1.25)
    rect(s, 6.75, 1.55, 5.95, 4.95, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 7.05, 1.7, 5.4, 0.5, "목표: 인증 심사급 SIL 검증 체계", 20, "FFFFFF", True)
    tbox(s, 7.05, 2.3, 5.4, 4.0, [
        ("**신뢰성** — 단측 95% 정확 이항 상한으로 통계적 판정", {"bullet": True, "color": "FFFFFF"}),
        ("**재현성** — 해시 고정·상수 대조·결정론적 시드", {"bullet": True, "color": "FFFFFF"}),
        ("**표준 추적성** — ISO 29119-3, SR↔TC↔결과 연결", {"bullet": True, "color": "FFFFFF"}),
        ("한계는 **숨기지 않고 투명하게 기록**", {"bullet": True, "color": "FFFFFF"}),
    ], 18, "FFFFFF", space=20, line=1.25)
    notes(s, "문제는 단순합니다. 센서 한 개로 후석에 사람이 있는지 판단하는 소프트웨어를 실차 없이 검증해야 합니다. "
             "그런데 코드가 돌아간다는 것만으로는 결과를 믿을 수 있는지, 다시 만들 수 있는지, 요구사항과 연결되는지를 보일 수 없습니다. "
             "그래서 이번 프로젝트의 목표를 신뢰성, 재현성, 표준 추적성을 갖춘 심사 가능한 검증 체계로 잡았습니다. "
             "그리고 잘 안 되는 부분도 숨기지 않고 한계로 기록하는 것을 원칙으로 했습니다.")

    # ---------------- Slide 3 구조·무결성
    s = base_slide(prs, "SIL 시스템 구조 및 기준선 무결성", 3)
    boxes = [("① 센서 물리·환경 모델", ["초음파 ToF, 음속 c(T)", "잡음·손실·편향·온도", "sil/sensor_model.py 외"]),
             ("② 신호처리·판정 로직", ["중앙값 필터, 히스테리시스", "디바운스, UNKNOWN 처리", "sil/detector.py"]),
             ("③ 독립 검증 하네스", ["TC-01~16, 정답 신호", "통계 판정, 기준선 대조", "main_lib/, run_main.py"])]
    xs = [0.65, 4.95, 9.25]
    for (h, ls), x in zip(boxes, xs):
        rect(s, x, 1.5, 3.45, 0.55, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
        tbox(s, x, 1.5, 3.45, 0.55, h, 15, "FFFFFF", True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        rect(s, x, 2.1, 3.45, 1.5, LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
        tbox(s, x + 0.1, 2.18, 3.25, 1.35, [(l, {"bullet": True}) for l in ls], 13, space=4, anchor=MSO_ANCHOR.MIDDLE)
    for x in (4.2, 8.5):
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(1.6), Inches(0.7), Inches(0.35))
        a.fill.solid()
        a.fill.fore_color.rgb = prgb(SLATE)
        a.line.fill.background()
    tbox(s, 0.65, 3.75, 12.0, 0.4, "무결성 3계층", 18, NAVY, True)
    card(s, 0.65, 4.25, 3.9, 2.4, "SHA-256", "기준선 파일 해시 고정\n태그 v1.0-baseline", vsize=30)
    card(s, 4.72, 4.25, 3.9, 2.4, "87 / 87", "기준선 ↔ 코드 상수\n자동 대조 일치(불일치 시 중단)", vsize=34)
    card(s, 8.79, 4.25, 3.9, 2.4, "9,855", "CRC32 기반 시행 시드\n전부 재계산 일치", vsize=34)
    notes(s, "시스템은 세 단계입니다. 첫째, 센서 물리와 환경 모델이 초음파 비행 시간, 온도에 따른 음속, 잡음과 손실을 만듭니다. "
             "둘째, 판정 로직이 중앙값 필터와 히스테리시스, 디바운스를 거쳐 점유, 비점유, 미확정 세 값을 출력합니다. "
             "셋째, 이 둘과 분리된 독립 검증 하네스가 TC-01부터 16까지를 실행하고 통계로 판정합니다. "
             "무결성은 세 겹입니다. 기준선 파일의 SHA-256 해시를 고정하고, 실행 시작 때 기준선과 코드의 상수 87개를 자동 대조해 하나라도 다르면 중단합니다. "
             "또 CRC32로 만든 시드 9,855개가 전부 규칙대로 재계산되어 같은 입력에서 같은 결과가 나옵니다.")

    # ---------------- Slide 4 통계·추적성
    s = base_slide(prs, "통계적 시험 설계 및 요구사항 추적성", 4)
    card(s, 0.65, 1.5, 3.2, 1.9, "0.994%", "n = 300, 오류 0건일 때\n단측 95% 상한", vsize=34)
    tbox(s, 0.65, 4.75, 6.0, 2.2, [
        ("**1% 목표**를 통계로 확인하려면 오류 0건에서 최소 **299회**", {"bullet": True}),
        ("관측 비율이 목표 이하여도 **상한이 목표를 넘으면** ‘통계 미확인’", {"bullet": True}),
        ("목표를 넘으면 **불합격**, 기준은 사후에 바꾸지 않음(D6)", {"bullet": True}),
        ("TC-01·04·11 조건별 300회(D5)", {"bullet": True}),
    ], 14, space=6, line=1.15)
    ptable(s, 4.1, 1.5, 2.6, [1.0, 1.6], [["0", "0.994%"], ["1", "1.571%"], ["2", "2.084%"], ["3", "2.564%"], ["4", "3.025%"]],
           ["k", "n=300 상한"], 11, 0.36, align=[PP_ALIGN.CENTER, PP_ALIGN.CENTER])
    tbox(s, 7.0, 1.4, 5.7, 0.4, "추적성(RTM): SR-01~14 ↔ TC-01~16", 16, NAVY, True)
    ptable(s, 7.0, 1.9, 5.7, [1.6, 2.9, 1.2], [
        ["SR-01~04", "감지 성능(미검출·오검출)", "TC-01~06"],
        ["SR-05", "임계값·히스테리시스", "TC-07"],
        ["SR-07, 08", "최초 판정·응답·자세", "TC-06,08~10"],
        ["SR-09", "온도 0–50 °C", "TC-11"],
        ["SR-10~13", "이상 입력 처리·출력", "TC-13~15"],
        ["SR-14", "미확정률 ≤ 1%", "TC-01~05"],
    ], ["SR", "내용", "TC"], 11, 0.42, align=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER])
    tbox(s, 7.0, 5.1, 5.7, 1.3, "모든 SR이 TC와 결과 상태로 연결되며, 전체 행렬은 GitHub 감사 보고서(trace_SR_TC_result.csv)에 있음.", 12, GRAY)
    notes(s, "통계 설계입니다. 단측 95% 정확 이항 상한을 쓰는데, 시행 300회에서 오류가 한 번도 없으면 상한이 0.994%입니다. 그래서 1% 목표를 통계적으로 확인할 수 있습니다. "
             "관측 비율이 목표 이하라도 상한이 목표를 넘으면 통계 미확인으로 구분하고, 목표를 넘으면 불합격으로 두며 기준은 나중에 바꾸지 않습니다. "
             "오른쪽은 요구사항 추적성입니다. 요구사항 SR-01부터 14까지가 시험 TC-01부터 16과 연결되고, 각 연결마다 결과 상태가 집계됩니다. "
             "전체 행렬은 저장소의 감사 보고서에 있습니다.")

    # ---------------- Slide 5 종합 결과
    s = base_slide(prs, "152개 조건 종합 검증 결과", 5)
    cards = [("49", "목표 충족\n(통계 확인)", GREEN), ("27", "결정적 시험\n일치", GREEN), ("12", "전 시행\n기준 충족", GREEN),
             ("3", "불합격\n(INC-01~03)", RED), ("4", "미실행\n(문서화)", AMBER)]
    for i, (v, l, c) in enumerate(cards):
        card(s, 0.65 + i * 2.4625, 1.5, 2.2, 1.8, v, l, vcolor=c, vsize=36, lsize=12)
    note = {"목표 충족(통계 확인)": "비율 지표, 상한 ≤ 목표", "일치": "결정적 시험", "기준 충족(전 시행)": "모든 시행 만족",
            "기록(합격 판정 없음)": "참고 기록", "가정 기반 민감도 기록": "비율 10 + 전 시행 3", "미실행": "O-A·B·C 원 조건, TC-12",
            "불합격": "정지 화물 2, 50 °C 보정 無 1"}
    rows = [[SHORT_L(k), cnt[k], f"{cnt[k] / 152 * 100:.1f}%", note[k]] for k in STATUS_ORDER] + [["합계", 152, "100%", ""]]
    ptable(s, 0.65, 3.55, 7.6, [2.6, 0.9, 1.0, 3.1], rows, ["판정 상태", "행", "비율", "비고"], 11, 0.33, hl={6: "FBE9EB"},
           align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
    tbox(s, 8.5, 3.55, 4.3, 3.2, [
        ("판정 행: **88건 충족, 3건 불합격**", {"bullet": True}),
        ("기록 57행(참고·민감도)은 합격 건수에 **미포함**", {"bullet": True}),
        ("‘관측 충족(통계 미확인)’ 행: **0건**", {"bullet": True}),
        ("SR-09는 **부분 커버**, 전체 충족 선언 보류(D3)", {"bullet": True}),
    ], 12, space=8, line=1.2)
    notes(s, "전체 결과입니다. 152개 결과 행 가운데 통계적으로 목표를 확인한 것이 49개, 결정적 시험에서 기대와 실제가 일치한 것이 27개, 모든 시행이 기준을 만족한 것이 12개입니다. "
             "불합격은 3건이고 미실행은 4건입니다. 합격 판정 없이 기록만 한 57행은 합격 건수에 넣지 않았습니다. "
             "관측 충족이지만 통계는 미확인인 행은 없었고, SR-09는 시험 범위가 부분적이라 전체 충족 선언을 보류했습니다.")

    # ---------------- Slide 6 온도 보정
    s = base_slide(prs, "심층 분석 1 — 고온 환경 온도 보정 효과 (TC-11)", 6)
    tbox(s, 0.65, 1.4, 6.0, 0.4, "50 °C · 낮은 화물 R0 오검출률 (목표 ≤ 5%)", 16, NAVY, True)
    card(s, 0.65, 1.95, 2.9, 2.0, "300/300", "보정 미적용\n오검출 100% → 불합격", vcolor=RED, vsize=30)
    card(s, 3.75, 1.95, 2.9, 2.0, "0/300", "보정 적용\n상한 0.994% → 목표 충족", vcolor=GREEN, vsize=30)
    tbox(s, 0.65, 4.2, 6.0, 2.4, [
        ("0·20 °C에서는 **보정 없이도 0/300**", {"bullet": True}),
        ("빈 좌석·R2는 전 온도·구성에서 **0/300**", {"bullet": True}),
        ("보정 채택은 본시험 후 결정(D3) → **SR-09 전체 충족 선언 보류**", {"bullet": True}),
    ], 14, space=8, line=1.2)
    tbox(s, 7.1, 1.4, 5.7, 0.4, "원인: 음속 변화 → 거리 환산 오차", 16, NAVY, True)
    steps = [("음속", f"340 m/s (고정)  →  {C50:.1f} m/s (50 °C)"), ("환산 배율", f"340 / {C50:.1f} = {SCALE:.4f}"),
             ("R0 거리", f"{D_R0:g} cm  →  {D_APP:.2f} cm"), ("Δ (d_empty 100)", f"{DELTA_R0:.2f} cm  ≥  Δ_on 10 cm")]
    for i, (a, b) in enumerate(steps):
        y = 1.95 + i * 1.05
        last = i == len(steps) - 1
        rect(s, 7.1, y, 1.75, 0.85, RED if last else NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
        tbox(s, 7.1, y, 1.75, 0.85, a, 13, "FFFFFF", True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        rect(s, 8.9, y, 3.85, 0.85, "FBE9EB" if last else LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
        tbox(s, 8.95, y, 3.75, 0.85, b, 13, RED if last else "1F2937", last, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    tbox(s, 7.1, 6.2, 5.7, 0.7, f"→ OCCUPIED로 오판. 빈 좌석 Δ는 {DELTA_EMPTY:.2f} cm로 임계값 미만이라 영향 없음.", 12, GRAY)
    notes(s, "첫 번째 심층 분석은 고온에서의 온도 보정 효과입니다. TC-11에서 50도, 보정 없이, 높이 5센티미터의 낮은 화물 R0는 300번 모두 점유로 오판했습니다. "
             "원인은 음속입니다. 50도에서 음속은 361.4미터 매초인데 보정이 없으면 340으로 계산하므로 거리가 0.9408배로 짧게 나옵니다. "
             "R0까지 실제 95센티미터가 89.4센티미터로 계산되어 기준 100센티미터와의 차이가 10.63센티미터, 임계값 10을 넘습니다. "
             "보정을 켜면 같은 조건에서 0/300, 상한 0.994%로 해결됩니다. 다만 보정 채택은 본시험 이후 결정하기로 했고, TC-11이 일부 조합만 다뤘기 때문에 SR-09 전체 충족은 선언하지 않았습니다.")

    # ---------------- Slide 7 단일 센서 한계
    s = base_slide(prs, "심층 분석 2 — 단일 센서의 물리적 한계와 투명한 기록", 7)
    ptable(s, 0.65, 1.5, 12.05, [1.3, 6.4, 2.2, 2.15], [
        ["INC-01", "TC-04b-1  점유 대상과 같은 높이(R1 = 20 cm)의 정지 화물", "300/300 오검출", "목표 ≤ 5%"],
        ["INC-02", "TC-04b-2  정지 화물(R1) 대 움직이는 점유 대상(±1 cm, 0.25 Hz)", "300/300 오검출", "목표 ≤ 5%"],
    ], ["ID", "조건", "결과", "목표"], 12, 0.5, hl={0: "FBE9EB", 1: "FBE9EB"},
           align=[PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
    rect(s, 0.65, 3.45, 5.9, 3.3, PALE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 0.85, 3.55, 5.5, 0.45, "왜 버그가 아닌가", 20, SLATE, True)
    tbox(s, 0.85, 4.15, 5.5, 2.5, [
        ("화물과 사람의 **거리 이력이 동일**(입력·출력 동일 300/300)", {"bullet": True}),
        ("센서는 **한 점의 거리**만 측정, 판정은 거리만 사용", {"bullet": True}),
        ("움직임을 줘도 알고리즘은 **시간 변동을 쓰지 않음**(출력 차이 0/300)", {"bullet": True}),
    ], 16, space=12, line=1.2)
    rect(s, 6.8, 3.45, 5.9, 3.3, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 7.0, 3.55, 5.5, 0.45, "투명하게 기록한 이유", 20, "FFFFFF", True)
    tbox(s, 7.0, 4.15, 5.5, 2.5, [
        ("합격선(5%)을 **사후에 완화하지 않음**(D6, D7)", {"bullet": True, "color": "FFFFFF"}),
        ("코드를 시험에 맞춰 고치지 않고 **한계로 공식 기록**", {"bullet": True, "color": "FFFFFF"}),
        ("개선은 **새 기준선 버전**으로만 가능 → Issue #1로 추적", {"bullet": True, "color": "FFFFFF"}),
    ], 16, "FFFFFF", space=12, line=1.2)
    notes(s, "두 번째 분석은 단일 센서의 한계입니다. 정지한 화물의 윗면이 사람과 같은 높이 20센티미터이면 300번 모두 점유로 오판합니다. "
             "이것은 소프트웨어 버그가 아닙니다. 두 경우의 거리 이력이 완전히 같아서 입력과 출력이 300번 모두 동일했고, 센서는 바로 아래 한 점의 거리만 보기 때문입니다. "
             "사람에게 1센티미터 움직임을 줘도 현재 알고리즘은 시간 변동을 쓰지 않아 출력이 달라지지 않았습니다. "
             "그래서 합격선을 나중에 5퍼센트에서 완화하거나 코드를 시험에 맞춰 고치지 않고, 한계로 공식 기록했습니다. 개선하려면 새 기준선 버전으로 만들어야 하고, 이슈 1번으로 추적하고 있습니다.")

    # ---------------- Slide 8 GitHub
    s = base_slide(prs, "GitHub 기반 형상 관리 및 CI/CD 자동 검증", 8)
    tbox(s, 0.65, 1.4, 7.0, 0.4, "5단계 생명주기 커밋 + 태그", 16, NAVY, True)
    ptable(s, 0.65, 1.85, 7.0, [0.9, 1.5, 4.6], [[a, b, e] for a, b, c, e in COMMITS], ["단계", "커밋", "내용"], 11, 0.4,
           align=[PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
    tbox(s, 0.65, 4.4, 7.0, 2.4, [
        ("**태그 v1.0-baseline** — 기준선 확정 커밋에 주석 태그(해시 기록)", {"bullet": True}),
        ("**GitHub Actions `verify.yml`** — push·PR마다 selftest.py 자동 실행, 최근 두 커밋(af7424d, bb2b906) **success**".replace("`", ""), {"bullet": True}),
        ("**Issues 4건** — #1·#2 이상 보고, #3·#4 후속 조치(TBR)", {"bullet": True}),
    ], 13, space=8, line=1.2)
    ph = rect(s, 8.0, 1.45, 4.7, 5.3, "F3F6FB", line=SLATE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    ph.line.dash_style = MSO_LINE.DASH
    tbox(s, 8.1, 3.2, 4.5, 1.6, [
        ("[ 스크린샷 삽입 영역 ]", {"size": 16, "bold": True, "color": SLATE, "align": PP_ALIGN.CENTER}),
        ("GitHub Actions 실행 결과 및 Issues 목록 캡처를 여기에 붙여 넣으세요", {"size": 12, "color": GRAY, "align": PP_ALIGN.CENTER}),
    ], 12, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "형상 관리는 GitHub로 했습니다. 저장소 이력은 예비시험 보존, 시험 하니스 구현, 기준선 동결, 본시험 결과 기록, 감사 보고서와 CI 추가의 다섯 단계 커밋으로 정리했고, "
             "기준선 확정 커밋에 v1.0-baseline 주석 태그를 붙여 해시를 기록했습니다. "
             "GitHub Actions의 verify 워크플로는 push와 풀 리퀘스트마다 selftest를 자동 실행하며 최근 두 커밋 모두 성공했습니다. "
             "이상 보고와 후속 과제는 이슈 4건으로 등록해 추적합니다. 오른쪽 빈 영역에는 Actions 실행 화면과 이슈 목록 스크린샷을 넣을 수 있게 비워 두었습니다.")

    # ---------------- Slide 9 결론
    s = base_slide(prs, "결론 및 향후 고도화 방향", 9)
    rect(s, 0.65, 1.5, 5.9, 5.2, PALE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 0.85, 1.6, 5.5, 0.45, "프로젝트 성과", 20, SLATE, True)
    tbox(s, 0.85, 2.2, 5.5, 4.4, [
        ("**통계 기준**으로 판정 — 49건 목표 충족, 상한 0.994%", {"bullet": True}),
        ("**재현성** — 87개 상수 대조, 9,855개 시드 재현", {"bullet": True}),
        ("**추적성** — SR-01~14 ↔ TC-01~16 ↔ 결과", {"bullet": True}),
        ("**한계의 투명한 기록** — 불합격 3건, 미실행 4건", {"bullet": True}),
        ("결과는 SIL 모델 범위이며 실제 센서 성능의 입증은 아님", {"bullet": True, "color": GRAY}),
    ], 17, space=16, line=1.2)
    rect(s, 6.8, 1.5, 5.9, 5.2, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    tbox(s, 7.0, 1.6, 5.5, 0.45, "향후 과제 (TBR)", 20, "FFFFFF", True)
    tbox(s, 7.0, 2.2, 5.5, 4.4, [
        ("**실물 치수 확보** — O-A/B/C/S, 착좌 위치 분포, TC-12 실행 (#3)", {"bullet": True, "color": "FFFFFF"}),
        ("**초기 공석 캘리브레이션** — d_empty 실측, 시동-센서 전원 연동 (#4)", {"bullet": True, "color": "FFFFFF"}),
        ("**다중 특징량 확장** — 시간 변동 등으로 화물/사람 구분 (#1)", {"bullet": True, "color": "FFFFFF"}),
        ("**온도 보정 채택** 결정과 SR-09 시험 범위 확장 (#2)", {"bullet": True, "color": "FFFFFF"}),
    ], 17, "FFFFFF", space=16, line=1.2)
    notes(s, "정리하겠습니다. 이번 프로젝트는 통계 기준으로 판정하고, 상수 87개와 시드 9,855개로 재현성을 보이며, 요구사항과 시험을 추적하는 검증 체계를 만들었습니다. "
             "그리고 불합격 3건과 미실행 4건을 숨기지 않고 원인과 함께 기록했습니다. 다만 결과는 SIL 모델 범위이고 실제 센서 성능을 입증한 것은 아닙니다. "
             "향후에는 실물 대상 치수와 착좌 위치 분포 확보, 초기 공석 캘리브레이션과 시동·전원 연동, 시간 변동 같은 다중 특징량 확장, 온도 보정 채택 결정이 필요합니다. "
             "이상으로 발표를 마치겠습니다. 감사합니다.")
    prs.core_properties.title = TITLE
    prs.core_properties.author = "yooksoo828-prog"
    prs.save(PPTX_OUT)


def SHORT_L(k):
    return {"목표 충족(통계 확인)": "목표 충족(통계 확인)", "기준 충족(전 시행)": "기준 충족(전 시행)"}.get(k, k)


# ----------------------------------------------------------------------------------------------
def main(argv):
    date = datetime.date.today().isoformat()
    it = iter(argv)
    for a in it:
        if a == "--date":
            date = datetime.date.fromisoformat(next(it)).isoformat()
        else:
            raise SystemExit(__doc__)
    d = load()
    HERE.mkdir(exist_ok=True)
    build_docx(d, date)
    build_pptx(d, date)
    print("작성:", DOCX_OUT)
    print("작성:", PPTX_OUT)


if __name__ == "__main__":
    main(sys.argv[1:])
