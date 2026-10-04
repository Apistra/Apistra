#!/usr/bin/env python3
"""Generate Apistra architecture, BPMN and design-reference visuals.

SVG and BPMN output use only the Python standard library. PNG previews require
Pillow. Run from anywhere; paths are resolved relative to this file.
"""

from __future__ import annotations

import base64
import html
import math
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ARCH = OUT / "architecture"
PROC = OUT / "processes"
DESIGN = OUT / "design"
LOGO = ROOT / "images" / "apistra-logo-primary.png"

BG = "#071414"
CHROME = "#0a1818"
SURFACE = "#102323"
SURFACE_2 = "#142c2b"
SURFACE_3 = "#1a3533"
TEXT = "#e7f1ef"
MUTED = "#8fa9a5"
BORDER = "#294643"
CYAN = "#2bd4cf"
PURPLE = "#8b6cf6"
GREEN = "#55c98c"
AMBER = "#e4b454"
RED = "#ed7070"
WHITE = "#ffffff"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def rect(x, y, w, h, fill=SURFACE, stroke=BORDER, radius=10, sw=1):
    return {
        "type": "rect",
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "fill": fill,
        "stroke": stroke,
        "radius": radius,
        "sw": sw,
    }


def text(x, y, value, size=14, fill=TEXT, weight="normal", anchor="start"):
    return {
        "type": "text",
        "x": x,
        "y": y,
        "value": value,
        "size": size,
        "fill": fill,
        "weight": weight,
        "anchor": anchor,
    }


def line(x1, y1, x2, y2, stroke=BORDER, sw=2, arrow=False, dash=None):
    return {
        "type": "line",
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "stroke": stroke,
        "sw": sw,
        "arrow": arrow,
        "dash": dash,
    }


def circle(cx, cy, r, fill=SURFACE, stroke=BORDER, sw=2):
    return {
        "type": "circle",
        "cx": cx,
        "cy": cy,
        "r": r,
        "fill": fill,
        "stroke": stroke,
        "sw": sw,
    }


def image_op(x, y, w, h, path):
    return {"type": "image", "x": x, "y": y, "w": w, "h": h, "path": Path(path)}


def add_wrapped(
    ops,
    x,
    y,
    value,
    width_chars=36,
    size=13,
    fill=MUTED,
    line_height=18,
    weight="normal",
    anchor="start",
):
    for idx, part in enumerate(textwrap.wrap(value, width=width_chars) or [""]):
        ops.append(text(x, y + idx * line_height, part, size, fill, weight, anchor))


def svg_from_ops(width, height, ops, title, description):
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        ),
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(description)}</desc>',
        "<defs>",
        (
            f'<marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" '
            f'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{BORDER}"/></marker>'
        ),
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
    ]
    for op in ops:
        kind = op["type"]
        if kind == "rect":
            parts.append(
                f'<rect x="{op["x"]}" y="{op["y"]}" width="{op["w"]}" height="{op["h"]}" '
                f'rx="{op["radius"]}" fill="{op["fill"]}" stroke="{op["stroke"]}" '
                f'stroke-width="{op["sw"]}"/>'
            )
        elif kind == "text":
            parts.append(
                f'<text x="{op["x"]}" y="{op["y"]}" fill="{op["fill"]}" '
                f'font-family="Inter, Segoe UI, Arial, sans-serif" font-size="{op["size"]}" '
                f'font-weight="{op["weight"]}" text-anchor="{op["anchor"]}">{esc(op["value"])}</text>'
            )
        elif kind == "line":
            dash = f' stroke-dasharray="{op["dash"]}"' if op["dash"] else ""
            arrow = ' marker-end="url(#arrow)"' if op["arrow"] else ""
            parts.append(
                f'<line x1="{op["x1"]}" y1="{op["y1"]}" x2="{op["x2"]}" y2="{op["y2"]}" '
                f'stroke="{op["stroke"]}" stroke-width="{op["sw"]}"{dash}{arrow}/>'
            )
        elif kind == "circle":
            parts.append(
                f'<circle cx="{op["cx"]}" cy="{op["cy"]}" r="{op["r"]}" '
                f'fill="{op["fill"]}" stroke="{op["stroke"]}" stroke-width="{op["sw"]}"/>'
            )
        elif kind == "image":
            encoded = base64.b64encode(op["path"].read_bytes()).decode("ascii")
            parts.append(
                f'<image x="{op["x"]}" y="{op["y"]}" width="{op["w"]}" height="{op["h"]}" '
                f'href="data:image/png;base64,{encoded}" preserveAspectRatio="xMidYMid meet"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_svg(path, width, height, ops, title, description):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        svg_from_ops(width, height, ops, title, description), encoding="utf-8"
    )


def render_png(path, width, height, ops):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    font_paths = [
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    bold_paths = [
        Path("C:/Windows/Fonts/segoeuib.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    def get_font(size, weight):
        paths = bold_paths if weight in ("600", "bold", "semibold") else font_paths
        for candidate in paths:
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        return ImageFont.load_default()

    def pillow_color(value):
        return None if value in (None, "none") else value

    for op in ops:
        kind = op["type"]
        if kind == "rect":
            draw.rounded_rectangle(
                [op["x"], op["y"], op["x"] + op["w"], op["y"] + op["h"]],
                radius=op["radius"],
                fill=pillow_color(op["fill"]),
                outline=pillow_color(op["stroke"]),
                width=op["sw"],
            )
        elif kind == "text":
            font = get_font(op["size"], op["weight"])
            anchor = {"start": "la", "middle": "ma", "end": "ra"}[op["anchor"]]
            draw.text(
                (op["x"], op["y"]),
                op["value"],
                fill=op["fill"],
                font=font,
                anchor=anchor,
            )
        elif kind == "line":
            draw.line(
                [op["x1"], op["y1"], op["x2"], op["y2"]],
                fill=op["stroke"],
                width=op["sw"],
            )
            if op["arrow"]:
                angle = math.atan2(op["y2"] - op["y1"], op["x2"] - op["x1"])
                length = 10
                a1 = angle + math.pi * 0.84
                a2 = angle - math.pi * 0.84
                points = [
                    (op["x2"], op["y2"]),
                    (
                        op["x2"] + length * math.cos(a1),
                        op["y2"] + length * math.sin(a1),
                    ),
                    (
                        op["x2"] + length * math.cos(a2),
                        op["y2"] + length * math.sin(a2),
                    ),
                ]
                draw.polygon(points, fill=op["stroke"])
        elif kind == "circle":
            draw.ellipse(
                [
                    op["cx"] - op["r"],
                    op["cy"] - op["r"],
                    op["cx"] + op["r"],
                    op["cy"] + op["r"],
                ],
                fill=pillow_color(op["fill"]),
                outline=pillow_color(op["stroke"]),
                width=op["sw"],
            )
        elif kind == "image":
            source = Image.open(op["path"]).convert("RGBA")
            source.thumbnail((op["w"], op["h"]))
            px = int(op["x"] + (op["w"] - source.width) / 2)
            py = int(op["y"] + (op["h"] - source.height) / 2)
            image.paste(source, (px, py), source)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return True


def labelled_box(ops, x, y, w, h, title_value, detail="", accent=CYAN):
    ops.append(rect(x, y, w, h, SURFACE, BORDER, 10))
    ops.append(rect(x, y, 5, h, accent, accent, 3))
    ops.append(text(x + 18, y + 28, title_value, 15, TEXT, "600"))
    if detail:
        add_wrapped(ops, x + 18, y + 51, detail, max(18, int(w / 8)), 12, MUTED, 16)


def architecture_context():
    ops = [
        text(
            50, 45, "ARC-CTX-01 · System context and trust boundaries", 22, TEXT, "600"
        )
    ]
    labelled_box(
        ops,
        470,
        190,
        360,
        210,
        "Apistra",
        "Design, publish and operate governed AI-assisted business processes.",
        CYAN,
    )
    actors = [
        (45, 120, "Administrator", "Configures and approves"),
        (45, 300, "API client", "Starts and observes runs"),
        (45, 480, "Maintainer", "Builds, stages and recovers"),
    ]
    for x, y, title_value, detail in actors:
        labelled_box(ops, x, y, 250, 110, title_value, detail, PURPLE)
        ops.append(line(x + 250, y + 55, 470, 255 + (y - 120) * 0.25, BORDER, 2, True))
    externals = [
        (965, 70, "Model and embedding endpoints", "Cloud or on-premise"),
        (965, 225, "Connector targets", "Files, REST, Git and later systems"),
        (965, 380, "Callback receivers", "Signed idempotent delivery"),
        (965, 535, "Softwaretest.it", "Engineering only; never runtime"),
    ]
    for x, y, title_value, detail in externals:
        labelled_box(
            ops, x, y, 300, 105, title_value, detail, AMBER if y < 500 else MUTED
        )
        target_y = 240 if y < 200 else 290 if y < 350 else 340 if y < 500 else 380
        ops.append(
            line(830, target_y, x, y + 52, BORDER, 2, True, "6 5" if y > 500 else None)
        )
    ops.append(rect(430, 150, 440, 290, "none", PURPLE, 16, 2))
    ops.append(
        text(
            650,
            465,
            "Installation trust boundary · one organisation, isolated projects",
            13,
            PURPLE,
            "600",
            "middle",
        )
    )
    return 1320, 690, ops


def architecture_containers():
    ops = [
        text(
            45,
            43,
            "ARC-CNT-01 · Runtime containers and responsibilities",
            22,
            TEXT,
            "600",
        )
    ]
    rows = [
        (
            80,
            110,
            "Web",
            "Next.js · authoring, administration, run and approval UI",
            PURPLE,
        ),
        (
            390,
            110,
            "API",
            "FastAPI · management API, Process API, policy enforcement",
            CYAN,
        ),
        (
            700,
            110,
            "Worker",
            "Durable activities · connectors, retrieval, tools and models",
            CYAN,
        ),
        (
            1010,
            110,
            "Durable engine",
            "Run state, timers, retries, pause and resume",
            AMBER,
        ),
        (
            235,
            360,
            "PostgreSQL",
            "Platform state, versions, audit and idempotency",
            GREEN,
        ),
        (555, 360, "Qdrant", "Embeddings with source provenance", GREEN),
        (
            875,
            360,
            "External adapters",
            "Endpoints, connectors, callbacks and tools",
            AMBER,
        ),
    ]
    for x, y, title_value, detail, accent in rows:
        labelled_box(ops, x, y, 250, 145, title_value, detail, accent)
    for x1, x2 in [(330, 390), (640, 700), (950, 1010)]:
        ops.append(line(x1, 182, x2, 182, BORDER, 2, True))
    ops += [
        line(515, 255, 360, 360, BORDER, 2, True),
        line(825, 255, 360, 360, BORDER, 2, True),
        line(825, 255, 680, 360, BORDER, 2, True),
        line(825, 255, 1000, 360, BORDER, 2, True),
        line(1135, 255, 825, 255, BORDER, 2, True),
    ]
    ops.append(
        text(
            660,
            570,
            "Static source dependencies follow inward-facing ports; runtime calls follow explicit contracts.",
            14,
            MUTED,
            "normal",
            "middle",
        )
    )
    return 1340, 620, ops


def architecture_modules():
    ops = [
        text(
            45,
            42,
            "ARC-MOD-01 · Approved module-first dependency direction",
            22,
            TEXT,
            "600",
        )
    ]
    layers = [
        (
            110,
            100,
            1120,
            100,
            "apps/web/app · backend/entrypoints/{api,worker}",
            "Explicit composition roots and transport",
            PURPLE,
        ),
        (
            170,
            235,
            1000,
            100,
            "backend/modules/*/adapters · backend/platform",
            "Persistence, providers and shared technical infrastructure",
            AMBER,
        ),
        (
            230,
            370,
            880,
            100,
            "backend/modules/*/{application,ports} · contracts · connector-sdk",
            "Use cases, inward ports and public contracts",
            CYAN,
        ),
        (
            290,
            505,
            760,
            100,
            "backend/modules/*/domain",
            "Provider-neutral rules, values and state models",
            GREEN,
        ),
    ]
    for x, y, w, h, title_value, detail, accent in layers:
        labelled_box(ops, x, y, w, h, title_value, detail, accent)
    for x in (430, 670, 910):
        ops.append(line(x, 235, x, 200, BORDER, 2, True))
        ops.append(line(x, 370, x, 335, BORDER, 2, True))
        ops.append(line(x, 505, x, 470, BORDER, 2, True))
    ops.append(
        text(
            670,
            650,
            "Cross-module imports use public.py · Softwaretest.it remains outside the runtime graph",
            14,
            RED,
            "600",
            "middle",
        )
    )
    return 1340, 700, ops


def architecture_deployment():
    ops = [
        text(
            45,
            42,
            "ARC-DEP-01 · Delivery and local staging deployment",
            22,
            TEXT,
            "600",
        )
    ]
    labelled_box(
        ops, 55, 115, 245, 120, "Feature branch", "Pull request into test", PURPLE
    )
    labelled_box(
        ops,
        375,
        115,
        245,
        120,
        "GitHub Actions",
        "Build, test, SBOM and result bundles",
        CYAN,
    )
    labelled_box(
        ops,
        695,
        115,
        245,
        120,
        "Immutable artefact store",
        "Images and candidate manifest by digest",
        GREEN,
    )
    labelled_box(
        ops,
        1015,
        115,
        245,
        120,
        "Human promotion",
        "test → staging → main; no deployment",
        AMBER,
    )
    for x1, x2 in [(300, 375), (620, 695), (940, 1015)]:
        ops.append(line(x1, 175, x2, 175, BORDER, 2, True))
    ops.append(rect(90, 320, 1180, 300, CHROME, PURPLE, 18, 2))
    ops.append(
        text(
            120,
            355,
            "Isolated local staging · manually started Compose project",
            17,
            PURPLE,
            "600",
        )
    )
    containers = [
        (130, 400, "Reverse proxy"),
        (315, 400, "Web"),
        (500, 400, "API"),
        (685, 400, "Worker"),
        (870, 400, "Durable engine"),
        (315, 520, "PostgreSQL"),
        (565, 520, "Qdrant"),
        (815, 520, "Local endpoints"),
    ]
    for x, y, label in containers:
        labelled_box(ops, x, y, 155, 70, label, "", CYAN if y == 400 else GREEN)
    ops.append(line(815, 235, 815, 320, BORDER, 2, True))
    ops.append(
        text(
            1100,
            585,
            "Separate network, volumes, ports, credentials and synthetic data",
            12,
            MUTED,
            "normal",
            "middle",
        )
    )
    return 1340, 680, ops


def architecture_domain():
    ops = [text(45, 42, "ARC-DOM-01 · Core domain model", 22, TEXT, "600")]
    entities = [
        (45, 100, "Organisation", "1 installation"),
        (280, 100, "Project", "isolation boundary"),
        (515, 100, "WorkflowDraft", "mutable"),
        (750, 100, "PublishedWorkflow", "immutable snapshot"),
        (985, 100, "Run", "durable execution"),
        (1100, 315, "NodeAttempt", "retry history"),
        (815, 315, "HumanTask", "approval state"),
        (530, 315, "AgentVersion", "endpoint + prompt + tools"),
        (245, 315, "KnowledgeSource", "sync + provenance"),
        (45, 315, "SecretReference", "encrypted value"),
        (245, 525, "ProvenanceRecord", "source + version + location"),
        (530, 525, "PolicyVersion", "write and citation rules"),
        (815, 525, "LimitSet", "time + calls + cost"),
    ]
    for x, y, title_value, detail in entities:
        labelled_box(
            ops,
            x,
            y,
            195,
            88,
            title_value,
            detail,
            CYAN if y < 200 else PURPLE if y < 500 else GREEN,
        )
    relations = [
        (240, 144, 280, 144),
        (475, 144, 515, 144),
        (710, 144, 750, 144),
        (945, 144, 985, 144),
        (1080, 190, 1170, 315),
        (985, 190, 910, 315),
        (750, 190, 625, 315),
        (515, 190, 340, 315),
        (280, 190, 140, 315),
        (340, 403, 340, 525),
        (625, 403, 625, 525),
        (910, 403, 910, 525),
    ]
    for x1, y1, x2, y2 in relations:
        ops.append(line(x1, y1, x2, y2, BORDER, 2, True))
    return 1280, 670, ops


def sequence_diagram(title_value, participants, messages):
    width = 1380
    height = 150 + len(messages) * 58
    ops = [text(45, 42, title_value, 22, TEXT, "600")]
    margin = 70
    spacing = (width - margin * 2) / max(1, len(participants) - 1)
    xs = {}
    for idx, name in enumerate(participants):
        x = margin + idx * spacing
        xs[name] = x
        ops.append(rect(x - 75, 72, 150, 45, SURFACE, BORDER, 8))
        ops.append(text(x, 100, name, 13, TEXT, "600", "middle"))
        ops.append(line(x, 117, x, height - 35, BORDER, 1, False, "5 5"))
    y = 155
    for src, dst, label, tone in messages:
        color = {
            "normal": BORDER,
            "success": GREEN,
            "warning": AMBER,
            "error": RED,
        }.get(tone, BORDER)
        ops.append(line(xs[src], y, xs[dst], y, color, 2, True))
        ops.append(
            text((xs[src] + xs[dst]) / 2, y - 9, label, 12, color, "normal", "middle")
        )
        y += 58
    return width, height, ops


def architecture_sequences():
    return {
        "sequence-run.svg": sequence_diagram(
            "ARC-SEQ-01 · Start and execute a durable run",
            [
                "API client",
                "Process API",
                "PostgreSQL",
                "Durable engine",
                "Worker",
                "Endpoint",
            ],
            [
                ("API client", "Process API", "start + idempotency key", "normal"),
                (
                    "Process API",
                    "PostgreSQL",
                    "verify project, version and key",
                    "normal",
                ),
                ("Process API", "Durable engine", "create durable run", "normal"),
                ("Durable engine", "Worker", "schedule node attempt", "normal"),
                ("Worker", "Endpoint", "governed model or tool call", "warning"),
                ("Worker", "PostgreSQL", "checkpoint attempt and usage", "normal"),
                ("Worker", "Durable engine", "complete node", "success"),
                ("Durable engine", "Process API", "complete run", "success"),
                ("Process API", "API client", "schema-valid result", "success"),
            ],
        ),
        "sequence-approval.svg": sequence_diagram(
            "ARC-SEQ-02 · Human approval and controlled write",
            [
                "Worker",
                "Policy",
                "Durable engine",
                "Human task API",
                "Administrator",
                "Tool",
            ],
            [
                ("Worker", "Policy", "classify planned write", "normal"),
                ("Policy", "Durable engine", "approval required", "warning"),
                ("Durable engine", "Human task API", "create pending task", "normal"),
                (
                    "Human task API",
                    "Administrator",
                    "present action, scope and context",
                    "normal",
                ),
                ("Administrator", "Human task API", "approve or reject", "warning"),
                (
                    "Human task API",
                    "Durable engine",
                    "record attributable decision",
                    "normal",
                ),
                ("Durable engine", "Worker", "resume exact checkpoint", "success"),
                ("Worker", "Tool", "execute once with idempotency", "success"),
            ],
        ),
        "sequence-knowledge-sync.svg": sequence_diagram(
            "ARC-SEQ-03 · Knowledge synchronisation and deletion",
            [
                "Scheduler",
                "Connector",
                "Pipeline",
                "Embedding endpoint",
                "PostgreSQL",
                "Qdrant",
            ],
            [
                ("Scheduler", "Connector", "sync with cursor", "normal"),
                ("Connector", "Pipeline", "canonical documents + provenance", "normal"),
                (
                    "Pipeline",
                    "Embedding endpoint",
                    "versioned embedding request",
                    "normal",
                ),
                ("Pipeline", "PostgreSQL", "store metadata and lineage", "normal"),
                ("Pipeline", "Qdrant", "idempotent vector upsert", "success"),
                ("Connector", "Pipeline", "removed source item", "warning"),
                ("Pipeline", "Qdrant", "deactivate or delete vectors", "warning"),
                (
                    "Pipeline",
                    "PostgreSQL",
                    "commit source version and cursor",
                    "success",
                ),
            ],
        ),
    }


PROCESS_SPECS = {
    "PRC-01": {
        "title": "Configure installation and project",
        "lanes": ["Administrator", "Web and API", "Platform services"],
        "nodes": [
            ("start", "start", "Open bootstrap", 0),
            ("auth", "task", "Create or sign in as Administrator", 0),
            ("project", "task", "Create isolated project", 0),
            ("validate", "gateway", "Configuration valid?", 1),
            ("persist", "task", "Persist project, limits and audit", 2),
            ("ready", "end", "Project ready", 0),
            ("reject", "end", "Validation rejected", 1),
        ],
        "edges": [
            ("start", "auth", ""),
            ("auth", "project", ""),
            ("project", "validate", ""),
            ("validate", "persist", "yes"),
            ("persist", "ready", ""),
            ("validate", "reject", "no"),
        ],
    },
    "PRC-02": {
        "title": "Connect and index knowledge",
        "lanes": [
            "Administrator or scheduler",
            "Connector and pipeline",
            "PostgreSQL and Qdrant",
        ],
        "nodes": [
            ("start", "start", "Start sync", 0),
            ("enumerate", "task", "Enumerate changes", 1),
            ("extract", "task", "Extract and normalise", 1),
            ("embed", "task", "Chunk and embed", 1),
            ("removed", "gateway", "Removed content?", 1),
            ("index", "task", "Upsert vectors and provenance", 2),
            ("delete", "task", "Deactivate derived data", 2),
            ("reconcile", "task", "Reconcile source version", 2),
            ("done", "end", "Sync complete", 0),
            ("retry", "end", "Retryable failure retained", 1),
        ],
        "edges": [
            ("start", "enumerate", ""),
            ("enumerate", "extract", ""),
            ("extract", "embed", ""),
            ("embed", "removed", ""),
            ("removed", "index", "no"),
            ("removed", "delete", "yes"),
            ("index", "reconcile", ""),
            ("delete", "reconcile", ""),
            ("reconcile", "done", ""),
        ],
    },
    "PRC-03": {
        "title": "Author and publish a workflow",
        "lanes": ["Administrator", "Authoring API", "Validation and versioning"],
        "nodes": [
            ("start", "start", "Create draft", 0),
            ("edit", "task", "Edit visual or canonical form", 0),
            ("validate", "task", "Validate graph and references", 1),
            ("valid", "gateway", "Valid?", 1),
            ("test", "task", "Execute draft snapshot test", 2),
            ("acceptable", "gateway", "Acceptable?", 0),
            ("publish", "task", "Publish immutable version", 2),
            ("done", "end", "Version published", 0),
            ("rejected", "end", "Return actionable findings", 1),
        ],
        "edges": [
            ("start", "edit", ""),
            ("edit", "validate", ""),
            ("validate", "valid", ""),
            ("valid", "test", "yes"),
            ("valid", "rejected", "no"),
            ("test", "acceptable", ""),
            ("acceptable", "publish", "yes"),
            ("acceptable", "edit", "no"),
            ("publish", "done", ""),
        ],
    },
    "PRC-04": {
        "title": "Execute a published process through the API",
        "lanes": [
            "API client",
            "Process API and durable engine",
            "Worker and adapters",
        ],
        "nodes": [
            ("start", "start", "POST run", 0),
            ("authenticate", "task", "Authenticate and validate input", 1),
            ("duplicate", "gateway", "Existing idempotent run?", 1),
            ("return", "task", "Return existing run ID", 1),
            ("create", "task", "Create durable run", 1),
            ("execute", "task", "Execute nodes and checkpoints", 2),
            ("human", "gateway", "Human task required?", 1),
            ("wait", "task", "Pause and resume", 1),
            ("result", "task", "Validate output and callback", 2),
            ("done", "end", "Result available", 0),
            ("failed", "end", "Failed or cancelled safely", 1),
        ],
        "edges": [
            ("start", "authenticate", ""),
            ("authenticate", "duplicate", ""),
            ("duplicate", "return", "yes"),
            ("return", "done", ""),
            ("duplicate", "create", "no"),
            ("create", "execute", ""),
            ("execute", "human", ""),
            ("human", "wait", "yes"),
            ("wait", "execute", "resume"),
            ("human", "result", "no"),
            ("result", "done", ""),
        ],
    },
    "PRC-05": {
        "title": "Complete a human approval",
        "lanes": ["Durable runtime", "Human task service", "Administrator"],
        "nodes": [
            ("start", "start", "Write requires approval", 0),
            ("create", "task", "Create pending task", 1),
            ("present", "task", "Present action, scope and context", 2),
            ("decision", "gateway", "Decision?", 2),
            ("approve", "task", "Record approval and resume", 1),
            ("reject", "task", "Record rejection reason", 1),
            ("timeout", "timer", "Timeout without execution", 1),
            ("approved", "end", "Run resumed", 0),
            ("rejected", "end", "Path rejected", 0),
            ("timedout", "end", "Timed out safely", 0),
        ],
        "edges": [
            ("start", "create", ""),
            ("create", "present", ""),
            ("present", "decision", ""),
            ("decision", "approve", "approve"),
            ("decision", "reject", "reject"),
            ("decision", "timeout", "timeout"),
            ("approve", "approved", ""),
            ("reject", "rejected", ""),
            ("timeout", "timedout", ""),
        ],
    },
    "PRC-06": {
        "title": "Evaluate workflow quality",
        "lanes": ["AI engineer", "Evaluation service", "Policy and review"],
        "nodes": [
            ("start", "start", "Select dataset and candidates", 0),
            ("run", "task", "Execute versioned evaluation", 1),
            ("metrics", "task", "Calculate quality, cost and latency", 1),
            ("calibrated", "gateway", "Policy calibrated?", 2),
            ("apply", "task", "Apply configured gate", 2),
            ("review", "task", "Request human review", 2),
            ("record", "task", "Record comparison evidence", 1),
            ("done", "end", "Evaluation complete", 0),
        ],
        "edges": [
            ("start", "run", ""),
            ("run", "metrics", ""),
            ("metrics", "calibrated", ""),
            ("calibrated", "apply", "yes"),
            ("calibrated", "review", "no"),
            ("apply", "record", ""),
            ("review", "record", ""),
            ("record", "done", ""),
        ],
    },
    "PRC-07": {
        "title": "Operate and recover Apistra",
        "lanes": ["Maintainer", "Delivery controls", "Local staging services"],
        "nodes": [
            ("start", "start", "Detect failed candidate or service", 0),
            ("inspect", "task", "Inspect health and correlation", 0),
            ("choice", "gateway", "Recovery path?", 1),
            ("rollback", "task", "Rollback compatible candidate", 1),
            ("rollforward", "task", "Deploy corrected candidate", 1),
            ("restore", "task", "Restore verified backup", 2),
            ("verify", "task", "Run health and smoke checks", 2),
            ("evidence", "task", "Record recovery evidence", 1),
            ("done", "end", "Known healthy state", 0),
        ],
        "edges": [
            ("start", "inspect", ""),
            ("inspect", "choice", ""),
            ("choice", "rollback", "rollback"),
            ("choice", "rollforward", "roll-forward"),
            ("choice", "restore", "restore"),
            ("rollback", "verify", ""),
            ("rollforward", "verify", ""),
            ("restore", "verify", ""),
            ("verify", "evidence", ""),
            ("evidence", "done", ""),
        ],
    },
}


def process_layout(spec):
    lane_h = 150
    lane_top = 95
    positions = {}
    x_positions = {}
    for idx, (node_id, _kind, _label, lane_idx) in enumerate(spec["nodes"]):
        x = 120 + idx * 150
        y = lane_top + lane_idx * lane_h + lane_h / 2
        positions[node_id] = (x, y)
        x_positions[node_id] = x
    width = max(1320, 240 + len(spec["nodes"]) * 150)
    height = lane_top + len(spec["lanes"]) * lane_h + 75
    return width, height, lane_top, lane_h, positions


def bpmn_preview(process_id, spec):
    width, height, lane_top, lane_h, positions = process_layout(spec)
    ops = [text(35, 42, f"{process_id} · {spec['title']}", 22, TEXT, "600")]
    for idx, lane_name in enumerate(spec["lanes"]):
        y = lane_top + idx * lane_h
        ops.append(
            rect(25, y, width - 50, lane_h, CHROME if idx % 2 == 0 else BG, BORDER, 0)
        )
        ops.append(text(42, y + 25, lane_name, 12, MUTED, "600"))
    for source, target, label in spec["edges"]:
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        ops.append(line(x1 + 45, y1, x2 - 45, y2, BORDER, 2, True))
        if label:
            ops.append(
                text(
                    (x1 + x2) / 2, (y1 + y2) / 2 - 9, label, 11, AMBER, "600", "middle"
                )
            )
    for node_id, kind, label, _lane_idx in spec["nodes"]:
        x, y = positions[node_id]
        if kind in ("start", "end", "timer"):
            stroke = GREEN if kind == "start" else RED if kind == "end" else AMBER
            ops.append(circle(x, y, 30, SURFACE, stroke, 3))
            if kind == "timer":
                ops.append(text(x, y + 5, "T", 14, AMBER, "600", "middle"))
        elif kind == "gateway":
            ops.append(rect(x - 32, y - 32, 64, 64, SURFACE_2, AMBER, 2, 2))
            ops.append(text(x, y + 5, "×", 20, AMBER, "600", "middle"))
        else:
            ops.append(rect(x - 58, y - 36, 116, 72, SURFACE, CYAN, 10, 2))
        add_wrapped(ops, x, y + 52, label, 18, 11, TEXT, 14, "normal", "middle")
    ops.append(
        text(
            width - 30,
            height - 18,
            "Readable preview · canonical process definition is the adjacent BPMN 2.0 file",
            11,
            MUTED,
            "normal",
            "end",
        )
    )
    return width, height, ops, positions, lane_top, lane_h


NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def q(prefix, tag):
    return f"{{{NS[prefix]}}}{tag}"


def write_bpmn(process_id, spec, path):
    width, _height, _ops, positions, lane_top, lane_h = bpmn_preview(process_id, spec)
    definitions = ET.Element(
        q("bpmn", "definitions"),
        {
            "id": f"Definitions_{process_id}",
            "targetNamespace": "https://apistra.dev/bpmn",
            "exporter": "Apistra BuildBySpec visual generator",
            "exporterVersion": "0.1",
        },
    )
    process = ET.SubElement(
        definitions,
        q("bpmn", "process"),
        {"id": process_id, "name": spec["title"], "isExecutable": "false"},
    )
    lane_set = ET.SubElement(
        process, q("bpmn", "laneSet"), {"id": f"LaneSet_{process_id}"}
    )
    lane_nodes = {idx: [] for idx in range(len(spec["lanes"]))}
    incoming = {node[0]: [] for node in spec["nodes"]}
    outgoing = {node[0]: [] for node in spec["nodes"]}
    for idx, (source, target, label) in enumerate(spec["edges"], start=1):
        flow_id = f"Flow_{process_id}_{idx:02d}"
        incoming[target].append(flow_id)
        outgoing[source].append(flow_id)
        attrs = {
            "id": flow_id,
            "sourceRef": f"{process_id}_{source}",
            "targetRef": f"{process_id}_{target}",
        }
        if label:
            attrs["name"] = label
        ET.SubElement(process, q("bpmn", "sequenceFlow"), attrs)
    element_map = {
        "start": "startEvent",
        "end": "endEvent",
        "task": "task",
        "gateway": "exclusiveGateway",
        "timer": "intermediateCatchEvent",
    }
    for node_id, kind, label, lane_idx in spec["nodes"]:
        attrs = {"id": f"{process_id}_{node_id}", "name": label}
        element = ET.SubElement(process, q("bpmn", element_map[kind]), attrs)
        for flow_id in incoming[node_id]:
            ET.SubElement(element, q("bpmn", "incoming")).text = flow_id
        for flow_id in outgoing[node_id]:
            ET.SubElement(element, q("bpmn", "outgoing")).text = flow_id
        if kind == "timer":
            event_def = ET.SubElement(
                element,
                q("bpmn", "timerEventDefinition"),
                {"id": f"TimerDef_{process_id}_{node_id}"},
            )
            ET.SubElement(event_def, q("bpmn", "timeDuration")).text = "PT0S"
        lane_nodes[lane_idx].append(f"{process_id}_{node_id}")
    for idx, lane_name in enumerate(spec["lanes"]):
        lane = ET.SubElement(
            lane_set,
            q("bpmn", "lane"),
            {"id": f"Lane_{process_id}_{idx + 1}", "name": lane_name},
        )
        for ref in lane_nodes[idx]:
            ET.SubElement(lane, q("bpmn", "flowNodeRef")).text = ref
    diagram = ET.SubElement(
        definitions, q("bpmndi", "BPMNDiagram"), {"id": f"Diagram_{process_id}"}
    )
    plane = ET.SubElement(
        diagram,
        q("bpmndi", "BPMNPlane"),
        {"id": f"Plane_{process_id}", "bpmnElement": process_id},
    )
    for idx, _lane_name in enumerate(spec["lanes"]):
        shape = ET.SubElement(
            plane,
            q("bpmndi", "BPMNShape"),
            {
                "id": f"Shape_Lane_{process_id}_{idx + 1}",
                "bpmnElement": f"Lane_{process_id}_{idx + 1}",
                "isHorizontal": "true",
            },
        )
        ET.SubElement(
            shape,
            q("dc", "Bounds"),
            {
                "x": "25",
                "y": str(lane_top + idx * lane_h),
                "width": str(width - 50),
                "height": str(lane_h),
            },
        )
    for node_id, kind, _label, _lane_idx in spec["nodes"]:
        x, y = positions[node_id]
        size = 60 if kind in ("start", "end", "timer", "gateway") else 116
        h = 60 if kind in ("start", "end", "timer", "gateway") else 72
        shape = ET.SubElement(
            plane,
            q("bpmndi", "BPMNShape"),
            {
                "id": f"Shape_{process_id}_{node_id}",
                "bpmnElement": f"{process_id}_{node_id}",
            },
        )
        ET.SubElement(
            shape,
            q("dc", "Bounds"),
            {
                "x": str(x - size / 2),
                "y": str(y - h / 2),
                "width": str(size),
                "height": str(h),
            },
        )
    for idx, (source, target, _label) in enumerate(spec["edges"], start=1):
        edge = ET.SubElement(
            plane,
            q("bpmndi", "BPMNEdge"),
            {
                "id": f"Edge_{process_id}_{idx:02d}",
                "bpmnElement": f"Flow_{process_id}_{idx:02d}",
            },
        )
        x1, y1 = positions[source]
        x2, y2 = positions[target]
        ET.SubElement(edge, q("di", "waypoint"), {"x": str(x1 + 45), "y": str(y1)})
        ET.SubElement(edge, q("di", "waypoint"), {"x": str(x2 - 45), "y": str(y2)})
    tree = ET.ElementTree(definitions)
    ET.indent(tree, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def app_chrome(title_value, subtitle, width, height, active_nav):
    ops = [
        rect(0, 0, width, height, BG, BG, 0),
        rect(0, 0, width, 64, CHROME, BORDER, 0),
        rect(0, 64, 210, height - 64, CHROME, BORDER, 0),
        rect(12, 8, 166, 48, TEXT, TEXT, 7),
        image_op(18, 10, 150, 44, LOGO),
        text(232, 31, title_value, 18, TEXT, "600"),
        text(232, 51, subtitle, 11, MUTED),
        rect(width - 178, 16, 154, 34, SURFACE_2, BORDER, 8),
        text(width - 101, 38, "Project Analyst", 12, TEXT, "600", "middle"),
    ]
    nav = [
        "Overview",
        "Workflows",
        "Agents",
        "Knowledge",
        "Connectors",
        "Runs",
        "Human Tasks",
        "Evaluations",
        "API Access",
        "Settings",
        "Audit",
    ]
    y = 96
    for item in nav:
        if item == active_nav:
            ops.append(rect(14, y - 22, 182, 36, SURFACE_3, CYAN, 7))
            color = TEXT
        else:
            color = MUTED
        ops.append(
            text(30, y, item, 13, color, "600" if item == active_nav else "normal")
        )
        y += 43
    return ops


def workflow_editor_ui():
    w, h = 1440, 900
    ops = app_chrome(
        "Customer Intake Analysis", "Draft · version 7 · saved", w, h, "Workflows"
    )
    ops += [
        rect(210, 64, w - 210, 54, CHROME, BORDER, 0),
        rect(230, 75, 92, 32, SURFACE_2, BORDER, 7),
        text(276, 96, "Validate", 12, TEXT, "600", "middle"),
        rect(330, 75, 78, 32, SURFACE_2, BORDER, 7),
        text(369, 96, "Test", 12, TEXT, "600", "middle"),
        rect(416, 75, 94, 32, CYAN, CYAN, 7),
        text(463, 96, "Publish", 12, BG, "600", "middle"),
        rect(522, 75, 118, 32, SURFACE_2, BORDER, 7),
        text(581, 96, "YAML / JSON", 12, TEXT, "600", "middle"),
        rect(210, 118, 190, h - 118, CHROME, BORDER, 0),
        rect(w - 310, 118, 310, h - 118, CHROME, BORDER, 0),
        text(232, 150, "NODE PALETTE", 11, MUTED, "600"),
        rect(228, 166, 154, 34, SURFACE, BORDER, 7),
        text(245, 188, "Search nodes…", 12, MUTED),
        text(w - 286, 150, "NODE SETTINGS", 11, MUTED, "600"),
        text(424, 148, "Workflow canvas", 12, MUTED, "600"),
    ]
    palette = [
        ("FLOW", MUTED),
        ("Input", CYAN),
        ("Decision", CYAN),
        ("Human Approval", AMBER),
        ("AI", MUTED),
        ("Agent", PURPLE),
        ("Retrieval", PURPLE),
        ("TOOLS", MUTED),
        ("Tool", GREEN),
        ("Transform", GREEN),
        ("Validation", GREEN),
    ]
    y = 232
    for label, color in palette:
        if label in ("FLOW", "AI", "TOOLS"):
            ops.append(text(232, y, label, 10, MUTED, "600"))
            y += 24
        else:
            ops.append(rect(228, y - 19, 154, 32, SURFACE, BORDER, 6))
            ops.append(circle(244, y - 3, 4, color, color, 1))
            ops.append(text(258, y + 1, label, 12, TEXT))
            y += 40
    nodes = [
        (460, 280, 180, 92, "Input", "Customer request", CYAN),
        (700, 280, 180, 92, "Retrieval", "Product knowledge", PURPLE),
        (940, 280, 180, 92, "Agent", "Analyse request", PURPLE),
        (700, 470, 180, 92, "Decision", "Confidence ≥ 0.80?", CYAN),
        (940, 470, 180, 92, "Human Approval", "Approve response", AMBER),
        (820, 660, 180, 92, "Output", "Validated response", GREEN),
    ]
    for x, y, nw, nh, title_value, detail, accent in nodes:
        ops.append(rect(x, y, nw, nh, SURFACE, accent, 10, 2))
        ops.append(text(x + 16, y + 27, title_value.upper(), 10, accent, "600"))
        ops.append(text(x + 16, y + 54, detail, 13, TEXT, "600"))
        ops.append(circle(x, y + nh / 2, 5, BG, accent, 2))
        ops.append(circle(x + nw, y + nh / 2, 5, BG, accent, 2))
    edges = [
        (640, 326, 700, 326),
        (880, 326, 940, 326),
        (1030, 372, 790, 470),
        (880, 516, 940, 516),
        (1030, 562, 910, 660),
    ]
    for edge in edges:
        ops.append(line(*edge, BORDER, 2, True))
    fields = [
        ("Node ID", "approval_response"),
        ("Policy", "Write approval required"),
        ("Timeout", "24 hours · never auto-approve"),
        ("Fallback", "Reject branch"),
    ]
    y = 188
    for label, value in fields:
        ops.append(text(w - 286, y, label, 11, MUTED, "600"))
        ops.append(rect(w - 286, y + 10, 260, 38, SURFACE, BORDER, 7))
        ops.append(text(w - 272, y + 35, value, 12, TEXT))
        y += 74
    ops.append(rect(w - 286, 520, 260, 102, SURFACE_2, AMBER, 8))
    ops.append(text(w - 270, 547, "Approval invariant", 12, AMBER, "600"))
    add_wrapped(
        ops,
        w - 270,
        571,
        "A timeout cannot execute the planned write.",
        32,
        12,
        TEXT,
        17,
    )
    return w, h, ops


def run_trace_ui():
    w, h = 1440, 900
    ops = app_chrome(
        "Run run_01J8ZK", "Workflow Customer Intake Analysis · v7", w, h, "Runs"
    )
    ops.append(rect(232, 92, 1178, 104, SURFACE, BORDER, 10))
    stats = [
        ("STATUS", "Waiting for approval", AMBER),
        ("STARTED", "14:32:06 UTC", TEXT),
        ("DURATION", "02m 41s", TEXT),
        ("COST", "$0.084", TEXT),
        ("TOKENS", "12,408", TEXT),
    ]
    x = 260
    for label, value, color in stats:
        ops.append(text(x, 120, label, 10, MUTED, "600"))
        ops.append(text(x, 153, value, 16, color, "600"))
        x += 218
    ops.append(text(232, 236, "Execution trace", 16, TEXT, "600"))
    trace = [
        ("14:32:06", "Input", "Completed", GREEN, "Input schema accepted"),
        ("14:32:07", "Retrieval", "Completed", GREEN, "8 cited chunks retrieved"),
        ("14:32:09", "Agent", "Completed", GREEN, "Model endpoint local-llm-01"),
        ("14:32:38", "Decision", "Completed", GREEN, "Confidence 0.74"),
        ("14:32:39", "Human Approval", "Waiting", AMBER, "Approval task task_083"),
    ]
    y = 282
    for idx, (time_value, node, state, color, detail) in enumerate(trace):
        ops.append(circle(265, y, 8, color, color, 1))
        if idx < len(trace) - 1:
            ops.append(line(265, y + 8, 265, y + 78, BORDER, 2))
        ops.append(text(295, y - 10, node, 14, TEXT, "600"))
        ops.append(text(295, y + 16, detail, 12, MUTED))
        ops.append(text(1150, y - 9, time_value, 11, MUTED, "normal", "end"))
        ops.append(rect(1180, y - 26, 112, 30, SURFACE_2, color, 15))
        ops.append(text(1236, y - 7, state, 11, color, "600", "middle"))
        y += 90
    ops.append(rect(1045, 670, 340, 162, SURFACE, BORDER, 10))
    ops.append(text(1068, 704, "Evidence context", 13, TEXT, "600"))
    add_wrapped(ops, 1068, 733, "Candidate digest sha256:7f…9a", 38, 11, MUTED, 18)
    add_wrapped(ops, 1068, 770, "Policy version approval-default@3", 38, 11, MUTED, 18)
    add_wrapped(ops, 1068, 807, "Correlation corr_01J8ZK", 38, 11, MUTED, 18)
    return w, h, ops


def approval_ui(width=1440, height=900, mobile=False):
    if mobile:
        w, h = width, height
        ops = [
            rect(0, 0, w, h, BG, BG, 0),
            rect(0, 0, w, 66, CHROME, BORDER, 0),
            rect(10, 9, 148, 46, TEXT, TEXT, 7),
            image_op(15, 12, 130, 40, LOGO),
            text(20, 104, "Human approval", 21, TEXT, "600"),
            text(20, 129, "task_083 · waiting", 12, AMBER, "600"),
        ]
        x, y, cw = 16, 158, w - 32
    else:
        w, h = width, height
        ops = app_chrome(
            "Human approval",
            "Task task_083 · waiting for decision",
            w,
            h,
            "Human Tasks",
        )
        x, y, cw = 275, 112, 890
    ops.append(rect(x, y, cw, 108, SURFACE, AMBER, 10, 2))
    ops.append(text(x + 22, y + 32, "Planned action", 11, AMBER, "600"))
    add_wrapped(
        ops,
        x + 22,
        y + 60,
        "Send the validated customer response to the configured CRM tool.",
        64 if not mobile else 42,
        15,
        TEXT,
        20,
        "600",
    )
    sections = [
        ("Scope", "Project Analyst · customer record C-1042 · crm.update"),
        ("Reason", "Workflow confidence is below the automatic threshold."),
        (
            "Input summary",
            "Customer asks whether the enterprise plan supports an offline installation.",
        ),
        (
            "Source evidence",
            "Product handbook v12, sections 4.2 and 8.1 · two citations",
        ),
    ]
    sy = y + 135
    for title_value, detail in sections:
        ops.append(rect(x, sy, cw, 82 if not mobile else 98, SURFACE, BORDER, 8))
        ops.append(text(x + 20, sy + 27, title_value, 11, MUTED, "600"))
        add_wrapped(
            ops, x + 20, sy + 53, detail, 78 if not mobile else 45, 13, TEXT, 18
        )
        sy += 94 if not mobile else 110
    ops.append(rect(x, sy + 4, cw, 92, SURFACE_2, BORDER, 8))
    ops.append(text(x + 20, sy + 31, "Decision note", 11, MUTED, "600"))
    ops.append(text(x + 20, sy + 61, "Required when rejecting", 12, MUTED))
    button_y = sy + 116
    if mobile:
        ops.append(rect(x, button_y, cw, 44, GREEN, GREEN, 8))
        ops.append(
            text(
                x + cw / 2, button_y + 28, "Approve and resume", 13, BG, "600", "middle"
            )
        )
        ops.append(rect(x, button_y + 56, cw, 44, SURFACE, RED, 8))
        ops.append(text(x + cw / 2, button_y + 84, "Reject", 13, RED, "600", "middle"))
    else:
        ops.append(rect(x + cw - 340, button_y, 160, 44, SURFACE, RED, 8))
        ops.append(
            text(x + cw - 260, button_y + 28, "Reject", 13, RED, "600", "middle")
        )
        ops.append(rect(x + cw - 166, button_y, 166, 44, GREEN, GREEN, 8))
        ops.append(
            text(
                x + cw - 83,
                button_y + 28,
                "Approve and resume",
                13,
                BG,
                "600",
                "middle",
            )
        )
    ops.append(
        text(
            x,
            min(h - 26, button_y + 125),
            "Timeout follows the configured non-executing path.",
            11,
            MUTED,
        )
    )
    return w, h, ops


def information_architecture():
    w, h = 1380, 830
    ops = [
        text(
            40, 42, "DSN-IA-01 · Application information architecture", 22, TEXT, "600"
        )
    ]
    labelled_box(
        ops,
        510,
        78,
        360,
        88,
        "Application shell",
        "Installation status · project switcher · navigation · Administrator",
        CYAN,
    )
    groups = [
        (
            40,
            250,
            "Build",
            ["Workflows", "Agents", "Knowledge", "Connectors", "Tools"],
            PURPLE,
        ),
        (360, 250, "Operate", ["Runs", "Human Tasks", "Audit"], AMBER),
        (680, 250, "Evaluate", ["Datasets", "Evaluations", "Comparisons"], GREEN),
        (
            1000,
            250,
            "Administer",
            ["Endpoints", "API Access", "Limits and policies", "Licence", "Settings"],
            CYAN,
        ),
    ]
    for x, y, title_value, items, accent in groups:
        labelled_box(ops, x, y, 280, 370, title_value, "Project-scoped", accent)
        iy = y + 105
        for item in items:
            ops.append(rect(x + 22, iy - 24, 236, 44, SURFACE_2, BORDER, 7))
            ops.append(text(x + 42, iy + 4, item, 13, TEXT))
            iy += 54
        ops.append(line(690, 166, x + 140, y, BORDER, 2, True))
    ops.append(
        text(
            690,
            690,
            "Global context remains visible: installation · environment · project · role · version",
            14,
            MUTED,
            "normal",
            "middle",
        )
    )
    ops.append(
        text(
            690,
            728,
            "Mobile priority: review, run status, human tasks and essential administration",
            13,
            MUTED,
            "normal",
            "middle",
        )
    )
    return w, h, ops


def cap02_administration_ui(width=1440, height=900, mobile=False):
    """Render the CAP-02 administration reference without implying implementation."""
    if mobile:
        w, h = width, height
        ops = [
            rect(0, 0, w, h, BG, BG, 0),
            rect(0, 0, w, 66, CHROME, BORDER, 0),
            rect(10, 9, 148, 46, TEXT, TEXT, 7),
            image_op(15, 12, 130, 40, LOGO),
            text(20, 104, "AI configuration", 21, TEXT, "600"),
            text(20, 129, "Project Analyst · Agents", 12, MUTED),
        ]
        x, y, content_w = 16, 158, w - 32
        tabs = ["Secrets", "Endpoints", "Agents", "Tools", "Limits"]
        tab_w = (content_w - 16) / 3
        for index, label in enumerate(tabs):
            row, column = divmod(index, 3)
            tx = x + column * (tab_w + 8)
            ty = y + row * 44
            selected = label == "Agents"
            ops.append(
                rect(
                    tx,
                    ty,
                    tab_w,
                    36,
                    SURFACE_3 if selected else SURFACE,
                    CYAN if selected else BORDER,
                    7,
                )
            )
            ops.append(
                text(
                    tx + tab_w / 2,
                    ty + 23,
                    label,
                    11,
                    TEXT if selected else MUTED,
                    "600" if selected else "normal",
                    "middle",
                )
            )
        y += 102
    else:
        w, h = width, height
        ops = app_chrome(
            "AI configuration",
            "Project Analyst · versioned and project-scoped",
            w,
            h,
            "Agents",
        )
        x, y, content_w = 245, 90, w - 285
        tabs = ["Secrets", "Endpoints", "Agents", "Tools", "Limits & policies"]
        tab_w = 170
        for index, label in enumerate(tabs):
            tx = x + index * (tab_w + 10)
            selected = label == "Agents"
            ops.append(
                rect(
                    tx,
                    y,
                    tab_w,
                    38,
                    SURFACE_3 if selected else SURFACE,
                    CYAN if selected else BORDER,
                    7,
                )
            )
            ops.append(
                text(
                    tx + tab_w / 2,
                    y + 24,
                    label,
                    12,
                    TEXT if selected else MUTED,
                    "600" if selected else "normal",
                    "middle",
                )
            )
        y += 66

    ops.append(text(x, y + 24, "Agent versions", 19, TEXT, "600"))
    subtitle = (
        "Immutable versions retain exact endpoint, prompt, tool and policy references."
    )
    if mobile:
        add_wrapped(ops, x, y + 49, subtitle, 48, 12, MUTED, 17)
    else:
        ops.append(text(x, y + 49, subtitle, 12, MUTED))
    button_w = 138 if not mobile else content_w
    button_x = x + content_w - button_w
    button_y = y + 88 if mobile else y + 2
    ops.append(rect(button_x, button_y, button_w, 38, CYAN, CYAN, 7))
    ops.append(
        text(
            button_x + button_w / 2,
            button_y + 24,
            "Create agent" if not mobile else "Create agent version",
            12,
            BG,
            "600",
            "middle",
        )
    )
    list_y = y + (144 if mobile else 78)
    cards = [
        ("Research Analyst", "v3 · Primary: local-llm · Fallback: none", GREEN),
        (
            "Document Classifier",
            "v5 · Primary: openai-prod · Fallback: local-llm",
            CYAN,
        ),
    ]
    for title_value, detail, accent in cards:
        card_h = 92 if mobile else 78
        ops.append(rect(x, list_y, content_w, card_h, SURFACE, BORDER, 9))
        ops.append(rect(x, list_y, 5, card_h, accent, accent, 3))
        ops.append(text(x + 20, list_y + 29, title_value, 14, TEXT, "600"))
        add_wrapped(
            ops,
            x + 20,
            list_y + 55,
            detail,
            44 if mobile else 90,
            11,
            MUTED,
            17,
        )
        list_y += card_h + 12

    panel_y = list_y + 10
    ops.append(
        rect(x, panel_y, content_w, 286 if mobile else 230, SURFACE_2, BORDER, 9)
    )
    ops.append(text(x + 20, panel_y + 30, "Create immutable version", 15, TEXT, "600"))
    fields = [
        ("Primary endpoint", "local-llm"),
        ("Fallback endpoint", "No fallback"),
        ("Tool set", "research-readonly@2"),
        ("Limits policy", "interactive-default@4"),
    ]
    fy = panel_y + 63
    for index, (label, value) in enumerate(fields):
        if mobile:
            ops.append(text(x + 20, fy, label, 10, MUTED, "600"))
            ops.append(rect(x + 20, fy + 10, content_w - 40, 34, SURFACE, BORDER, 6))
            ops.append(text(x + 32, fy + 32, value, 11, TEXT))
            fy += 52
        else:
            column = index % 2
            row = index // 2
            fx = x + 20 + column * ((content_w - 52) / 2 + 12)
            field_w = (content_w - 52) / 2
            field_y = panel_y + 62 + row * 72
            ops.append(text(fx, field_y, label, 10, MUTED, "600"))
            ops.append(rect(fx, field_y + 10, field_w, 36, SURFACE, BORDER, 6))
            ops.append(text(fx + 12, field_y + 33, value, 11, TEXT))
    footer_y = min(h - 76, panel_y + (310 if mobile else 250))
    footer = "Secret values are write-only. Connection tests return normalised outcomes only."
    if mobile:
        add_wrapped(ops, x, footer_y, footer, 48, 11, AMBER, 16)
    else:
        ops.append(text(x, footer_y, footer, 11, AMBER))
    return w, h, ops


def design_system():
    w, h = 1440, 900
    ops = [
        text(
            40,
            42,
            "DSN-SYS-01 · Dark technical design-system reference",
            22,
            TEXT,
            "600",
        )
    ]
    colors = [
        (BG, "canvas"),
        (CHROME, "chrome"),
        (SURFACE, "surface"),
        (SURFACE_3, "selected"),
        (CYAN, "accent"),
        (PURPLE, "AI"),
        (GREEN, "success"),
        (AMBER, "warning"),
        (RED, "error"),
    ]
    x = 50
    for color, label in colors:
        ops.append(rect(x, 85, 120, 78, color, BORDER, 8))
        ops.append(text(x + 60, 188, label, 11, MUTED, "normal", "middle"))
        x += 150
    ops.append(text(50, 255, "Typography", 17, TEXT, "600"))
    samples = [
        ("Page title", 28, "600"),
        ("Section title", 20, "600"),
        ("Body and operational copy", 14, "normal"),
        ("Metadata and labels", 11, "600"),
        ("Code and identifiers: run_01J8ZK", 13, "normal"),
    ]
    y = 300
    for value, size, weight in samples:
        ops.append(text(60, y, value, size, TEXT if size > 13 else MUTED, weight))
        y += 52
    ops.append(text(640, 255, "Components and states", 17, TEXT, "600"))
    states = [
        ("Default", BORDER, SURFACE),
        ("Focused", CYAN, SURFACE),
        ("Selected", PURPLE, SURFACE_3),
        ("Disabled", BORDER, CHROME),
        ("Warning", AMBER, SURFACE),
        ("Error", RED, SURFACE),
    ]
    y = 300
    for label, border, fill in states:
        ops.append(rect(650, y - 25, 190, 42, fill, border, 8, 2))
        ops.append(
            text(
                745,
                y + 1,
                label,
                12,
                TEXT if label != "Disabled" else MUTED,
                "600",
                "middle",
            )
        )
        y += 58
    ops.append(text(935, 255, "Spacing and shape", 17, TEXT, "600"))
    for idx, value in enumerate([4, 8, 12, 16, 24, 32]):
        y = 300 + idx * 52
        ops.append(text(945, y, f"{value}px", 12, MUTED))
        ops.append(
            rect(
                1005,
                y - 16,
                value * 6,
                22,
                SURFACE_3,
                CYAN if value == 16 else BORDER,
                5,
            )
        )
    ops.append(rect(50, 640, 1340, 180, CHROME, BORDER, 10))
    ops.append(text(78, 677, "Interaction invariants", 16, TEXT, "600"))
    invariants = [
        "No critical action depends on drag, hover or colour alone.",
        "Focus remains visible and returns predictably after dialogs.",
        "Dangerous writes show action, target, scope and consequence.",
        "Every loading, empty, validation, conflict, permission and offline state is explicit.",
    ]
    y = 713
    for item in invariants:
        ops.append(circle(82, y - 5, 4, CYAN, CYAN, 1))
        ops.append(text(98, y, item, 13, TEXT))
        y += 28
    return w, h, ops


def generate():
    for directory in (ARCH, PROC, DESIGN):
        directory.mkdir(parents=True, exist_ok=True)

    diagrams = {
        "system-context.svg": architecture_context(),
        "containers.svg": architecture_containers(),
        "module-dependencies.svg": architecture_modules(),
        "deployment.svg": architecture_deployment(),
        "domain-model.svg": architecture_domain(),
    }
    diagrams.update(architecture_sequences())
    for filename, (width, height, ops) in diagrams.items():
        write_svg(
            ARCH / filename,
            width,
            height,
            ops,
            filename.removesuffix(".svg"),
            "Apistra architecture planning diagram. No implementation evidence.",
        )
        render_png(ARCH / filename.replace(".svg", ".png"), width, height, ops)

    for process_id, spec in PROCESS_SPECS.items():
        width, height, ops, _positions, _lane_top, _lane_h = bpmn_preview(
            process_id, spec
        )
        slug = process_id.lower()
        write_svg(
            PROC / f"{slug}.svg",
            width,
            height,
            ops,
            f"{process_id} {spec['title']}",
            "Readable process preview. The adjacent BPMN file is canonical.",
        )
        render_png(PROC / f"{slug}.png", width, height, ops)
        write_bpmn(process_id, spec, PROC / f"{slug}.bpmn")

    design_items = {
        "information-architecture": information_architecture(),
        "cap02-administration-desktop": cap02_administration_ui(),
        "cap02-administration-mobile": cap02_administration_ui(390, 1160, True),
        "workflow-editor-desktop": workflow_editor_ui(),
        "run-trace-desktop": run_trace_ui(),
        "human-approval-desktop": approval_ui(),
        "human-approval-mobile": approval_ui(390, 1100, True),
        "design-system": design_system(),
    }
    rendered = []
    for name, (width, height, ops) in design_items.items():
        write_svg(
            DESIGN / f"{name}.svg",
            width,
            height,
            ops,
            name.replace("-", " ").title(),
            "Apistra design reference. Planning artefact, not implemented UI.",
        )
        if render_png(DESIGN / f"{name}.png", width, height, ops):
            rendered.append(f"{name}.png")

    manifest = [
        "# Generated visual manifest",
        "",
        "Generator: docs/visuals/generate_visuals.py",
        "",
        "Architecture sources and rendered previews:",
        *[f"- architecture/{name} and .png" for name in sorted(diagrams)],
        "",
        "BPMN and previews:",
        *[
            f"- processes/{process_id.lower()}.bpmn, .svg, and .png"
            for process_id in PROCESS_SPECS
        ],
        "",
        "Design sources and rendered previews:",
        *[f"- design/{name}.svg and .png" for name in design_items],
        "",
        "PNG previews generated: "
        + (", ".join(rendered) if rendered else "No; install Pillow."),
        "",
    ]
    (OUT / "GENERATED.md").write_text("\n".join(manifest), encoding="utf-8")


if __name__ == "__main__":
    generate()
