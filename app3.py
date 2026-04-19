"""
╔══════════════════════════════════════════════════════════════════════════╗
║  SOFT ROBOTIC FINGER — COMPLETE DIGITAL TWIN  v3.0                       ║
║  STL input · Full structural analysis · Weak-point detection             ║
║  Load capacity · Fatigue estimate · Simulation engine                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Install:  pip install streamlit plotly numpy scipy                      ║
║  Run:      streamlit run app.py                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import struct, math, time
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# ════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Soft Finger Digital Twin",
    page_icon="🦾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════
# CSS — industrial dark / amber accent
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=DM+Sans:wght@300;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #080b10;
    color: #b8ccd8;
}
section[data-testid="stSidebar"] {
    background: #0c1018;
    border-right: 1px solid #182030;
}
div[data-testid="metric-container"] {
    background: #0f1520;
    border: 1px solid #1a2840;
    border-radius: 4px;
    padding: 10px 14px;
}
div[data-testid="metric-container"] label {
    color: #4a7a9b !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.35rem;
    color: #e0f0ff;
}
h1 { font-family:'DM Sans',sans-serif; font-weight:700; color:#ddeeff; letter-spacing:-0.03em; }
h2,h3 { font-family:'DM Sans',sans-serif; font-weight:500; color:#8aaabb; }
.tag {
    display:inline-block; padding:4px 14px; border-radius:2px;
    font-family:'Share Tech Mono',monospace; font-size:0.8rem;
    letter-spacing:0.12em; font-weight:600; text-transform:uppercase; margin:2px;
}
.tag-ok   { background:#0d1f0d; color:#44cc44; border:1px solid #226622; }
.tag-warn { background:#1f1900; color:#f5c44d; border:1px solid #886600; }
.tag-crit { background:#1f0a0a; color:#f56b4d; border:1px solid #882200; }
.tag-info { background:#0a1525; color:#4db6f5; border:1px solid #1a4a7a; }
.section-head {
    font-family:'Share Tech Mono',monospace; font-size:0.72rem;
    color:#2a5a7a; letter-spacing:0.2em; text-transform:uppercase;
    border-bottom:1px solid #182030; padding-bottom:4px; margin-bottom:12px;
}
.geo-card {
    background:#0c1520; border:1px solid #182840; border-radius:4px;
    padding:12px 16px; font-family:'Share Tech Mono',monospace;
    font-size:0.74rem; color:#4a8ab5; line-height:2;
}
.alert-box {
    padding:10px 16px; border-radius:4px; margin:6px 0;
    font-family:'Share Tech Mono',monospace; font-size:0.78rem;
}
.alert-red  { background:#1a0808; border-left:3px solid #cc3300; color:#ff7755; }
.alert-yel  { background:#1a1200; border-left:3px solid #cc8800; color:#ffcc44; }
.alert-grn  { background:#081408; border-left:3px solid #228822; color:#44cc66; }
.alert-blue { background:#08101a; border-left:3px solid #2266aa; color:#44aaff; }
hr { border-color:#182030; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# COLOUR TOKENS
# ════════════════════════════════════════════════════════════════════
BG   = "#080b10"
PBG  = "#0c1018"
GRID = "#151f2a"
FONT = "#5a8090"
C1   = "#3a9fd8"   # blue
C2   = "#f56b4d"   # orange
C3   = "#7be3a0"   # green
C4   = "#f5c44d"   # amber
C5   = "#c47bf5"   # purple

# ════════════════════════════════════════════════════════════════════
# ██  MATERIAL LIBRARY
# ════════════════════════════════════════════════════════════════════
MATERIALS = {
    "Soft Silicone (Dragon Skin 10)": dict(
        E=0.17e6, ultimate=0.9e6, elongation=10.0,
        density=1070, poisson=0.47, fatigue_coeff=0.40,
        wall_mult=1.0, color="#4db6f5",
    ),
    "Ecoflex 00-30": dict(
        E=0.059e6, ultimate=0.45e6, elongation=8.0,
        density=1040, poisson=0.499, fatigue_coeff=0.30,
        wall_mult=0.9, color="#7be3a0",
    ),
    "Dragon Skin 30": dict(
        E=0.43e6, ultimate=1.6e6, elongation=3.6,
        density=1080, poisson=0.46, fatigue_coeff=0.55,
        wall_mult=1.1, color="#f5c44d",
    ),
    "Polyurethane (Shore 40A)": dict(
        E=2.1e6, ultimate=4.5e6, elongation=6.0,
        density=1200, poisson=0.42, fatigue_coeff=0.65,
        wall_mult=1.2, color="#c47bf5",
    ),
    "Natural Rubber": dict(
        E=0.05e6, ultimate=0.3e6, elongation=7.0,
        density=920, poisson=0.499, fatigue_coeff=0.25,
        wall_mult=0.85, color="#f56b4d",
    ),
}

# ════════════════════════════════════════════════════════════════════
# ██  STL PARSER  (pure Python — no numpy-stl)
# ════════════════════════════════════════════════════════════════════
class STLGeometry:
    def __init__(self):
        self.triangles    = None
        self.normals      = None
        self.n_triangles  = 0
        self.bbox_min     = np.zeros(3)
        self.bbox_max     = np.zeros(3)
        self.dimensions   = np.zeros(3)
        self.surface_area = 0.0
        self.volume       = 0.0
        self.centroid     = np.zeros(3)
        self.long_ax      = 2
        # physics (set after parsing)
        self.finger_length  = 0.08
        self.cross_section  = 4e-4
        self.wall_thickness = 0.003
        self.max_angle      = 135.0
        self.max_pressure   = 200.0
        self.mass           = 0.0
        self.is_loaded      = False
        self.filename       = ""
        self.source         = "default"
        # segment-level data (N_SEG entries)
        self.seg_widths     = []   # width per segment (m)
        self.seg_areas      = []   # cross-section per segment

def _parse_binary(data):
    n = struct.unpack_from("<I", data, 80)[0]
    N = np.zeros((n,3),np.float32); T = np.zeros((n,3,3),np.float32)
    off = 84
    for i in range(n):
        N[i]    = struct.unpack_from("<3f",data,off); off+=12
        T[i,0]  = struct.unpack_from("<3f",data,off); off+=12
        T[i,1]  = struct.unpack_from("<3f",data,off); off+=12
        T[i,2]  = struct.unpack_from("<3f",data,off); off+=12
        off += 2
    return N, T

def _parse_ascii(data):
    txt = data.decode("utf-8","replace")
    NL, TL = [], []
    cn = None; vv = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if ln.startswith("facet normal"):
            p=ln.split(); cn=[float(p[2]),float(p[3]),float(p[4])]
        elif ln.startswith("vertex"):
            p=ln.split(); vv.append([float(p[1]),float(p[2]),float(p[3])])
        elif ln.startswith("endfacet") and len(vv)==3 and cn:
            NL.append(cn); TL.append(vv[:])
            vv=[]; cn=None
    if not TL: raise ValueError("No facets in ASCII STL")
    return np.array(NL,np.float32), np.array(TL,np.float32)

def parse_stl(uploaded_file) -> STLGeometry:
    geo = STLGeometry()
    geo.filename = uploaded_file.name
    geo.source   = "stl"
    data = uploaded_file.read()
    is_ascii = data[:5].lower().startswith(b"solid") and b"facet" in data[:512]
    try:
        geo.normals, geo.triangles = (_parse_ascii if is_ascii else _parse_binary)(data)
    except:
        geo.normals, geo.triangles = (_parse_binary if is_ascii else _parse_ascii)(data)

    geo.n_triangles = len(geo.triangles)
    vf = geo.triangles.reshape(-1,3)
    geo.bbox_min = vf.min(0); geo.bbox_max = vf.max(0)
    ext = geo.bbox_max - geo.bbox_min
    sc  = 1e-3 if ext.max() > 10 else 1.0
    geo.bbox_min  = geo.bbox_min.astype(float)*sc
    geo.bbox_max  = geo.bbox_max.astype(float)*sc
    geo.triangles = geo.triangles.astype(float)*sc
    geo.dimensions = geo.bbox_max - geo.bbox_min
    v0,v1,v2 = geo.triangles[:,0],geo.triangles[:,1],geo.triangles[:,2]
    cr = np.cross(v1-v0, v2-v0)
    geo.surface_area = float(0.5*np.linalg.norm(cr,axis=1).sum())
    geo.volume = float(abs(np.sum(v0[:,0]*(v1[:,1]*v2[:,2]-v2[:,1]*v1[:,2])))/6.0)
    geo.centroid = vf.mean(0)
    dims = geo.dimensions
    geo.long_ax = int(np.argmax(dims))
    geo.finger_length = float(dims[geo.long_ax])
    oth = [float(dims[i]) for i in range(3) if i != geo.long_ax]
    geo.cross_section   = float(oth[0]*oth[1])
    geo.wall_thickness  = max(float(dims.min())*0.05, 0.001)
    aspect = geo.finger_length / (math.sqrt(geo.cross_section)+1e-9)
    geo.max_angle    = float(np.clip(90+aspect*3.5, 60, 165))
    geo.max_pressure = float(np.clip(200*4e-4/(geo.cross_section+1e-8), 50, 500))
    # Estimate variable cross-section per 20 segments (uses bbox approximation)
    N_SEG = 20
    la = geo.long_ax
    seg_edges = np.linspace(geo.bbox_min[la], geo.bbox_max[la], N_SEG+1)
    for s in range(N_SEG):
        lo, hi = seg_edges[s], seg_edges[s+1]
        mask = (vf[:,la] >= lo) & (vf[:,la] <= hi)
        if mask.sum() > 0:
            sub = vf[mask]
            oth_dims = [sub[:,i] for i in range(3) if i!=la]
            w = float(oth_dims[0].max()-oth_dims[0].min())
            h = float(oth_dims[1].max()-oth_dims[1].min())
        else:
            w = math.sqrt(geo.cross_section)
            h = w
        geo.seg_widths.append(max(w, 0.001))
        geo.seg_areas.append(max(w*h, 1e-6))
    geo.is_loaded = True
    return geo

def make_default_geometry() -> STLGeometry:
    geo = STLGeometry()
    geo.finger_length=0.08; geo.cross_section=4e-4; geo.wall_thickness=0.003
    geo.max_angle=135.0; geo.max_pressure=200.0; geo.dimensions=np.array([0.02,0.02,0.08])
    geo.surface_area=2*(0.02*0.02+0.02*0.08*2); geo.volume=0.02*0.02*0.08
    geo.long_ax=2; geo.source="default"
    w=math.sqrt(geo.cross_section)
    geo.seg_widths=[w]*20; geo.seg_areas=[geo.cross_section]*20
    return geo

# ════════════════════════════════════════════════════════════════════
# ██  FULL STRUCTURAL ANALYSIS ENGINE
# ════════════════════════════════════════════════════════════════════

def full_analysis(pressure_kpa: float, geo: STLGeometry, mat: dict, N_SEG=20):
    """
    Compute per-segment physics for the entire finger.
    Returns a dict of arrays (one value per segment) plus scalars.
    """
    P_pa = pressure_kpa * 1e3
    L    = geo.finger_length
    seg_L = L / N_SEG

    # Use per-segment cross-sections if available
    if len(geo.seg_areas) == N_SEG:
        A_seg = np.array(geo.seg_areas)
        W_seg = np.array(geo.seg_widths)
    else:
        A_seg = np.full(N_SEG, geo.cross_section)
        W_seg = np.full(N_SEG, math.sqrt(geo.cross_section))

    t_seg = W_seg * 0.05  # wall thickness per segment (5% of width)
    t_seg = np.clip(t_seg, 0.001, None)

    # ── Equivalent radius per segment ────────────────────────────
    r_seg = np.sqrt(A_seg / math.pi)

    # ── Hoop stress (circumferential) σ_h = P·r/t ────────────────
    hoop_stress = P_pa * r_seg / t_seg          # Pa

    # ── Axial (longitudinal) stress σ_a = P·r/(2t) ───────────────
    axial_stress = P_pa * r_seg / (2.0 * t_seg) # Pa

    # ── Von Mises stress (thin shell) ────────────────────────────
    #    σ_vm = sqrt(σ_h² - σ_h·σ_a + σ_a²)
    vm_stress = np.sqrt(hoop_stress**2 - hoop_stress*axial_stress + axial_stress**2)

    # ── Force per segment  F = P·A ───────────────────────────────
    force_seg = P_pa * A_seg

    # ── Bending moment from arc model ────────────────────────────
    # Distribute the generated torque along the length; near the base
    # the segment must carry the full cumulative moment.
    total_angle_deg = pressure_to_angle(pressure_kpa, geo)
    angle_per_seg   = math.radians(total_angle_deg) / N_SEG
    # Moment at each segment = force × lever arm from that segment to tip
    lever = np.array([(N_SEG - i) * seg_L for i in range(N_SEG)])
    bending_moment = force_seg * lever * angle_per_seg   # N·m

    # ── Bending stress  σ_b = M·c/I  (circular cross-section) ───
    #    c = r (outer radius),  I = π·r⁴/4
    I_seg = math.pi * r_seg**4 / 4.0
    bending_stress = bending_moment * r_seg / (I_seg + 1e-30)  # Pa

    # ── Total combined stress ─────────────────────────────────────
    total_stress = vm_stress + bending_stress

    # ── Safety factor  SF = ultimate / σ_total ───────────────────
    ult = mat["ultimate"]
    safety_factor = ult / (total_stress + 1e-10)

    # ── Strain  ε = σ / E  (linear, approximate for large strains) ─
    E = mat["E"]
    strain = total_stress / E

    # ── Tip force (cumulative, projected) ────────────────────────
    tip_force = float(P_pa * geo.cross_section)

    # ── Max load capacity (pressure at SF=1) ─────────────────────
    # SF = ult / σ = 1  →  P_max = ult × t / r  (hoop governs)
    # Vectorise, take minimum (weakest segment governs)
    p_yield_seg = (ult * t_seg / (r_seg + 1e-12)) / 1e3   # kPa
    max_load_pressure = float(np.min(p_yield_seg))

    # ── Fatigue life estimate (Coffin-Manson inspired) ────────────
    # N_f = (ε_f / Δε)^(1/c)   where ε_f = mat fatigue coeff, c=0.5
    delta_eps = strain.max()
    eps_f = mat["fatigue_coeff"]
    if delta_eps > 0:
        n_fatigue = int((eps_f / (delta_eps + 1e-12)) ** 2)
        n_fatigue = min(n_fatigue, 10_000_000)
    else:
        n_fatigue = 10_000_000

    # ── Weak-point index (segment with lowest safety factor) ──────
    weak_idx = int(np.argmin(safety_factor))
    weak_pos  = (weak_idx + 0.5) * seg_L * 1000   # mm from base

    # ── Mass ─────────────────────────────────────────────────────
    mass = mat["density"] * geo.volume if geo.volume > 0 else mat["density"]*geo.cross_section*geo.finger_length*0.4

    # ── Tip displacement ─────────────────────────────────────────
    xs, ys = compute_arc(total_angle_deg, geo, N_SEG)
    tip_disp = math.sqrt(xs[-1]**2 + ys[-1]**2) * 1000  # mm

    return dict(
        # per-segment arrays
        hoop_stress    = hoop_stress,
        axial_stress   = axial_stress,
        vm_stress      = vm_stress,
        bending_stress = bending_stress,
        total_stress   = total_stress,
        safety_factor  = safety_factor,
        strain         = strain,
        force_seg      = force_seg,
        bending_moment = bending_moment,
        A_seg          = A_seg,
        # scalars
        tip_force           = tip_force,
        max_load_pressure   = max_load_pressure,
        n_fatigue           = n_fatigue,
        weak_idx            = weak_idx,
        weak_pos_mm         = weak_pos,
        total_angle_deg     = total_angle_deg,
        tip_disp_mm         = tip_disp,
        mass_g              = mass * 1000,
        xs=xs, ys=ys,
        min_sf = float(safety_factor.min()),
        max_vm = float(vm_stress.max()) / 1e3,   # kPa
        max_total = float(total_stress.max()) / 1e3,
    )

# ════════════════════════════════════════════════════════════════════
# ██  PHYSICS HELPERS
# ════════════════════════════════════════════════════════════════════

def pressure_to_angle(pressure_kpa: float, geo: STLGeometry) -> float:
    ref = 4e-4
    k = float(np.clip(2.5 * math.sqrt(ref / (geo.cross_section+1e-9)), 1.2, 4.5))
    pn = float(np.clip(pressure_kpa / geo.max_pressure, 0, 1))
    return float(geo.max_angle * math.tanh(k * pn))

def compute_arc(angle_deg, geo, n=20):
    ar = math.radians(angle_deg)
    sl = geo.finger_length / n
    sa = ar / n
    xs = np.zeros(n+1); ys = np.zeros(n+1)
    hd = math.pi / 2.0
    for i in range(n):
        hd -= sa
        xs[i+1] = xs[i] + sl*math.cos(hd)
        ys[i+1] = ys[i] + sl*math.sin(hd)
    return xs, ys

def noise(v, s=0.008):
    return v * (1 + np.random.normal(0, s))

def grip_tag(pressure_kpa, geo):
    r = pressure_kpa / geo.max_pressure
    if r < 0.25:   return "WEAK GRIP",    "tag-ok"
    if r < 0.80:   return "OPTIMAL GRIP", "tag-info"
    if r < 1.00:   return "HIGH LOAD",    "tag-warn"
    return "OVERLOAD",  "tag-crit"

def sf_tag(sf):
    if sf > 3.0:  return "SAFE",     "tag-ok"
    if sf > 1.5:  return "MARGINAL", "tag-warn"
    return "CRITICAL", "tag-crit"

# ════════════════════════════════════════════════════════════════════
# ██  PLOT HELPERS
# ════════════════════════════════════════════════════════════════════

def _base(height=340, rows=1, cols=1, **kw):
    fig = make_subplots(rows=rows, cols=cols, **kw) if (rows>1 or cols>1) else go.Figure()
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=PBG,
        font=dict(family="DM Sans", color=FONT),
        height=height, margin=dict(l=50,r=16,t=44,b=44),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#7a9ab5", size=11)),
    )
    return fig

def mono_title(fig, txt):
    fig.update_layout(title=dict(
        text=txt,
        font=dict(family="Share Tech Mono", size=12, color="#2a6080"),
        x=0.01,
    ))
    return fig

# ════════════════════════════════════════════════════════════════════
# ██  STRESS MAP (segment heatmap along finger)
# ════════════════════════════════════════════════════════════════════

def build_stress_heatmap(res: dict, geo: STLGeometry) -> go.Figure:
    N = len(res["total_stress"])
    pos = np.linspace(0, geo.finger_length*1000, N)
    ts  = res["total_stress"] / 1e3   # kPa
    sf  = res["safety_factor"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        subplot_titles=("Total Stress (kPa) along finger length",
                        "Safety Factor along finger length"))

    # Colour-code by danger level
    colours = []
    for s in sf:
        if s > 3:   colours.append(C3)
        elif s > 1.5: colours.append(C4)
        else:         colours.append(C2)

    fig.add_trace(go.Bar(x=pos, y=ts, marker_color=colours,
        name="Total Stress", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=pos, y=sf, mode="lines+markers",
        line=dict(color=C1, width=2),
        marker=dict(color=colours, size=7, line=dict(color="white",width=0.5)),
        name="Safety Factor"), row=2, col=1)
    fig.add_hline(y=1.0, line_dash="dot", line_color=C2, line_width=1, row=2, col=1)
    fig.add_hline(y=3.0, line_dash="dot", line_color=C3, line_width=1, row=2, col=1)

    # Mark weak point
    wi = res["weak_idx"]
    fig.add_vline(x=pos[wi], line_dash="dash", line_color=C2,
                  line_width=1.5, annotation_text="⚠ WEAK PT",
                  annotation_font_color=C2, annotation_font_size=10)

    for r in [1,2]:
        fig.update_xaxes(gridcolor=GRID, linecolor=GRID, row=r, col=1)
        fig.update_yaxes(gridcolor=GRID, linecolor=GRID, row=r, col=1)
    fig.update_xaxes(title_text="Position from base (mm)", row=2, col=1)
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=PBG,
        font=dict(family="DM Sans", color=FONT),
        height=400, margin=dict(l=50,r=16,t=44,b=36), showlegend=False)
    mono_title(fig, "STRESS DISTRIBUTION  &  SAFETY FACTOR")
    return fig


def build_2d_finger(res: dict, geo: STLGeometry, pressure_kpa: float) -> go.Figure:
    xs, ys = res["xs"], res["ys"]
    sf = res["safety_factor"]
    N  = len(xs) - 1
    fig = go.Figure()
    # Draw each segment coloured by safety factor
    for i in range(N):
        s = sf[i] if i < len(sf) else 3.0
        r_ = int(np.clip(255*(1-s/4), 50, 245))
        g_ = int(np.clip(255*(s/4),   50, 220))
        col = f"rgb({r_},{g_},80)"
        fig.add_trace(go.Scatter(
            x=[xs[i],xs[i+1]], y=[ys[i],ys[i+1]],
            mode="lines", line=dict(color=col, width=9),
            hoverinfo="text",
            hovertext=f"Seg {i+1}: SF={s:.2f}",
            showlegend=False,
        ))
    # Weak point marker
    wi = res["weak_idx"]
    fig.add_trace(go.Scatter(
        x=[(xs[wi]+xs[wi+1])/2], y=[(ys[wi]+ys[wi+1])/2],
        mode="markers+text",
        marker=dict(size=16, color=C2, symbol="x",
                    line=dict(color="white",width=1.5)),
        text=["⚠"], textposition="top right",
        textfont=dict(size=12, color=C2),
        name="Weak Point", showlegend=True,
    ))
    # Tip
    fig.add_trace(go.Scatter(
        x=[xs[-1]], y=[ys[-1]], mode="markers",
        marker=dict(size=12, color=C4, symbol="diamond",
                    line=dict(color="white",width=1.5)),
        name="Tip",
    ))
    # Base
    fig.add_shape(type="rect", x0=-0.014,x1=0.014,y0=-0.012,y1=0,
        fillcolor="#141f2a", line=dict(color="#2a4060",width=2))

    pad=0.02
    ax = np.concatenate([xs,[-0.02,0.02]]); ay = np.concatenate([ys,[-0.015]])
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=PBG,
        font=dict(family="Share Tech Mono",color=FONT),
        height=380, showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#7a9ab5",size=10)),
        margin=dict(l=8,r=8,t=44,b=8),
        xaxis=dict(range=[ax.min()-pad,ax.max()+pad],gridcolor=GRID,title="x (m)"),
        yaxis=dict(range=[ay.min()-pad,ay.max()+pad],gridcolor=GRID,title="y (m)",
                   scaleanchor="x",scaleratio=1),
        title=dict(text=f"STRESS-COLOURED ARC  ·  {res['total_angle_deg']:.1f}°  @  {pressure_kpa:.0f} kPa",
            font=dict(family="Share Tech Mono",size=11,color="#2a6080"),x=0.5),
    )
    return fig


def build_3d_mesh(geo: STLGeometry, angle_deg: float, sf_array=None) -> go.Figure:
    if not geo.is_loaded:
        return go.Figure()

    tris  = geo.triangles.copy()
    verts = tris.reshape(-1,3)

    la = geo.long_ax
    pa = (la + 1) % 3
    L  = geo.finger_length

    ar = math.radians(angle_deg)

    s = np.clip((verts[:, la] - geo.bbox_min[la]) / (L + 1e-9), 0, 1)

    nv = verts.copy()
    if ar > 1e-4:
        R = L / ar
        nv[:, la] += R * np.sin(s * ar) - (verts[:, la] - geo.bbox_min[la])
        nv[:, pa] += R * (1 - np.cos(s * ar))

    N = len(geo.triangles)

    x, y, z = nv[:, 0], nv[:, 1], nv[:, 2]
    ii = np.arange(0, 3 * N, 3)
    jj = ii + 1
    kk = ii + 2

    # -----------------------------------
    # COLORING (Safety Factor)
    # -----------------------------------
    if sf_array is not None and len(sf_array) == 20:
        seg_s = np.clip(
            ((verts[ii, la] + verts[jj, la] + verts[kk, la]) / 3 - geo.bbox_min[la]) / (L + 1e-9),
            0, 0.9999
        )

        seg_i = np.floor(seg_s * 20).astype(int)
        sf_v  = sf_array[np.clip(seg_i, 0, 19)]

        intensity = np.clip(sf_v, 0, 4)

        cscale = [
            [0, "rgb(200,50,30)"],
            [0.5, "rgb(220,180,40)"],
            [1, "rgb(60,200,120)"]
        ]

    else:
        intensity = None
        cscale = None

    # -----------------------------------
    # MESH SETUP
    # -----------------------------------
    mesh_kwargs = dict(
        x=x, y=y, z=z,
        i=ii, j=jj, k=kk,
        flatshading=True,
        opacity=0.78,
        lighting=dict(
            ambient=0.3,
            diffuse=0.85,
            specular=0.45,
            roughness=0.45
        ),
        lightposition=dict(x=100, y=200, z=150)
    )

    # -----------------------------------
    # APPLY COLORBAR (FIXED HERE)
    # -----------------------------------
    if intensity is not None:
        mesh_kwargs.update(
            intensity=intensity,
            colorscale=cscale,
            showscale=True,
            cmin=0,
            cmax=4,
            colorbar=dict(
                title=dict(   # ✅ FIXED (was titlefont)
                    text="Safety<br>Factor",
                    font=dict(color=FONT, size=10)
                ),
                tickfont=dict(color=FONT, size=9),
                bgcolor=PBG,
                bordercolor=GRID,
                thickness=12
            )
        )
    else:
        t_ = angle_deg / max(geo.max_angle, 1)
        mesh_kwargs["color"] = f"rgb({int(50+160*t_)},{int(160-80*t_)},{int(230-100*t_)})"

    # -----------------------------------
    # BUILD FIGURE
    # -----------------------------------
    fig = go.Figure(data=[go.Mesh3d(**mesh_kwargs)])

    fig.update_layout(
        paper_bgcolor=BG,
        scene=dict(
            bgcolor=PBG,
            xaxis=dict(backgroundcolor=PBG, gridcolor=GRID, showbackground=True, zerolinecolor=GRID),
            yaxis=dict(backgroundcolor=PBG, gridcolor=GRID, showbackground=True, zerolinecolor=GRID),
            zaxis=dict(backgroundcolor=PBG, gridcolor=GRID, showbackground=True, zerolinecolor=GRID),
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.8)),
            aspectmode="data"
        ),
        font=dict(family="Share Tech Mono", color=FONT),
        height=440,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(
            text=f"3-D MESH  ·  {geo.n_triangles:,} tris  ·  {angle_deg:.1f}°  bend",
            font=dict(family="Share Tech Mono", size=11, color="#2a6080"),
            x=0.5
        )
    )

    return fig


def build_pv_chart(current_p, geo, res_all=None) -> go.Figure:
    ps = np.linspace(0, geo.max_pressure, 200)
    angles = [pressure_to_angle(p, geo) for p in ps]
    fig = _base(320)
    fig.add_trace(go.Scatter(x=ps,y=angles,mode="lines",
        line=dict(color=C1,width=2.5),name="θ(P)",
        fill="tozeroy",fillcolor="rgba(58,159,216,0.06)"))
    fig.add_trace(go.Scatter(x=[current_p],y=[pressure_to_angle(current_p,geo)],
        mode="markers",name="Now",
        marker=dict(size=12,color=C4,symbol="diamond",line=dict(color="white",width=1.5))))
    if res_all:
        ml = res_all["max_load_pressure"]
        fig.add_vline(x=min(ml,geo.max_pressure), line_dash="dot",
                      line_color=C2, line_width=1,
                      annotation_text="yield P", annotation_font_color=C2, annotation_font_size=10)
    fig.add_vline(x=0.25*geo.max_pressure,line_dash="dot",line_color="#226622",line_width=1)
    fig.add_vline(x=0.80*geo.max_pressure,line_dash="dot",line_color="#662222",line_width=1)
    fig.update_xaxes(title_text="Pressure (kPa)"); fig.update_yaxes(title_text="Angle (°)")
    return mono_title(fig,"PRESSURE  vs  BENDING ANGLE")


def build_force_chart(current_p, geo) -> go.Figure:
    ps = np.linspace(0,geo.max_pressure,200)
    forces = [p*1e3*geo.cross_section for p in ps]
    fig = _base(320)
    fig.add_trace(go.Scatter(x=ps,y=forces,mode="lines",
        line=dict(color=C2,width=2.5),name="F(P)",
        fill="tozeroy",fillcolor="rgba(245,107,77,0.06)"))
    fig.add_trace(go.Scatter(x=[current_p],y=[current_p*1e3*geo.cross_section],
        mode="markers",name="Now",
        marker=dict(size=12,color=C4,symbol="diamond",line=dict(color="white",width=1.5))))
    fig.update_xaxes(title_text="Pressure (kPa)"); fig.update_yaxes(title_text="Force (N)")
    return mono_title(fig,"PRESSURE  vs  TIP FORCE")


def build_sf_vs_pressure(geo, mat, N_SEG=20) -> go.Figure:
    """Safety factor of the weakest segment vs pressure."""
    ps  = np.linspace(0.1, geo.max_pressure, 80)
    sfs = []
    for p in ps:
        r = full_analysis(p, geo, mat, N_SEG)
        sfs.append(r["min_sf"])
    fig = _base(320)
    fig.add_trace(go.Scatter(x=ps, y=sfs, mode="lines",
        line=dict(color=C3, width=2.5),name="Min SF",
        fill="tozeroy", fillcolor="rgba(123,227,160,0.06)"))
    fig.add_hline(y=1.0,line_dash="dot",line_color=C2,line_width=1.5,
        annotation_text="SF=1 (yield)",annotation_font_color=C2,annotation_font_size=10)
    fig.add_hline(y=3.0,line_dash="dot",line_color=C3,line_width=1,
        annotation_text="SF=3 (safe)",annotation_font_color=C3,annotation_font_size=10)
    fig.update_xaxes(title_text="Pressure (kPa)"); fig.update_yaxes(title_text="Safety Factor")
    return mono_title(fig,"SAFETY FACTOR  vs  PRESSURE  (weakest segment)")


def build_fatigue_chart(geo, mat) -> go.Figure:
    """Estimated fatigue life (cycles) vs pressure."""
    ps = np.linspace(0.1, geo.max_pressure, 80)
    Nf = []
    for p in ps:
        r = full_analysis(p, geo, mat, 20)
        Nf.append(r["n_fatigue"])
    fig = _base(320)
    fig.add_trace(go.Scatter(x=ps, y=Nf, mode="lines",
        line=dict(color=C5, width=2.5),name="N_fatigue"))
    fig.update_yaxes(type="log", title_text="Cycles to failure")
    fig.update_xaxes(title_text="Pressure (kPa)")
    return mono_title(fig,"FATIGUE LIFE ESTIMATE  (Coffin-Manson model)")


def build_stress_component_chart(res: dict, geo: STLGeometry) -> go.Figure:
    N   = len(res["hoop_stress"])
    pos = np.linspace(0, geo.finger_length*1000, N)
    fig = _base(320)
    for key, col, name in [
        ("hoop_stress",    C1, "Hoop σ"),
        ("axial_stress",   C3, "Axial σ"),
        ("bending_stress", C4, "Bending σ"),
        ("vm_stress",      C2, "Von Mises σ"),
    ]:
        fig.add_trace(go.Scatter(x=pos, y=res[key]/1e3, mode="lines",
            line=dict(color=col,width=2), name=name))
    fig.update_xaxes(title_text="Position from base (mm)")
    fig.update_yaxes(title_text="Stress (kPa)")
    return mono_title(fig,"STRESS COMPONENTS ALONG FINGER")


# ════════════════════════════════════════════════════════════════════
# ██  SIMULATION ENGINE
# ════════════════════════════════════════════════════════════════════

def run_simulation(mode: str, geo: STLGeometry, mat: dict,
                   p_start, p_end, n_steps, dt) -> dict:
    """
    Simulate a pressure profile over time.
    Modes: 'ramp', 'pulse', 'sinusoidal', 'step', 'fatigue_sweep'
    Returns time-series arrays.
    """
    t = np.linspace(0, n_steps*dt, n_steps)

    if mode == "Pressure Ramp":
        pressures = np.linspace(p_start, p_end, n_steps)

    elif mode == "Pulse (square wave)":
        period = n_steps // 6
        pressures = np.where((np.arange(n_steps) // period) % 2 == 0,
                             p_end, p_start)

    elif mode == "Sinusoidal":
        freq = 3 / (n_steps * dt)
        pressures = p_start + (p_end-p_start) * 0.5 * (
            1 + np.sin(2*math.pi*freq*t))

    elif mode == "Step response":
        pressures = np.where(t < t[-1]*0.3, p_start,
                    np.where(t < t[-1]*0.6, p_end, p_start))

    elif mode == "Fatigue sweep":
        cycles = 5
        pressures = p_start + (p_end-p_start) * 0.5 * (
            1 + np.sin(2*math.pi*cycles*t/t[-1]))

    else:
        pressures = np.full(n_steps, (p_start+p_end)/2)

    angles, forces, stresses, safety_factors, tip_disps = [],[],[],[],[]
    for p in pressures:
        pn = p + np.random.normal(0, p*0.008 + 0.1)
        pn = max(0, pn)
        r  = full_analysis(pn, geo, mat, 20)
        angles.append(noise(r["total_angle_deg"]))
        forces.append(noise(r["tip_force"]))
        stresses.append(noise(r["max_total"]))       # kPa
        safety_factors.append(noise(r["min_sf"]))
        tip_disps.append(noise(r["tip_disp_mm"]))

    return dict(
        t=t, pressures=pressures,
        angles=np.array(angles), forces=np.array(forces),
        stresses=np.array(stresses), safety_factors=np.array(safety_factors),
        tip_disps=np.array(tip_disps),
    )


def build_sim_chart(sim: dict) -> go.Figure:
    fig = make_subplots(rows=3, cols=2,
        subplot_titles=("Pressure (kPa)","Bending Angle (°)",
                        "Tip Force (N)","Tip Displacement (mm)",
                        "Peak Stress (kPa)","Safety Factor (min)"),
        vertical_spacing=0.10, horizontal_spacing=0.10)
    pairs = [
        (1,1, sim["pressures"], C4, "Pressure"),
        (1,2, sim["angles"],    C1, "Angle"),
        (2,1, sim["forces"],    C2, "Force"),
        (2,2, sim["tip_disps"], C3, "Tip Disp"),
        (3,1, sim["stresses"],  C5, "Stress"),
        (3,2, sim["safety_factors"], C3, "SF"),
    ]
    for row,col,y,c,name in pairs:
        fig.add_trace(go.Scatter(x=sim["t"], y=y, mode="lines",
            line=dict(color=c,width=1.7), name=name, showlegend=False),
            row=row,col=col)
        fig.update_xaxes(gridcolor=GRID,linecolor=GRID,row=row,col=col)
        fig.update_yaxes(gridcolor=GRID,linecolor=GRID,row=row,col=col)
    # SF=1 line
    fig.add_hline(y=1.0,line_dash="dot",line_color=C2,line_width=1,row=3,col=2)
    fig.update_xaxes(title_text="Time (s)", row=3, col=1)
    fig.update_xaxes(title_text="Time (s)", row=3, col=2)
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=PBG,
        font=dict(family="DM Sans",color=FONT),
        height=560, margin=dict(l=50,r=12,t=44,b=36))
    mono_title(fig,"SIMULATION TIME-SERIES OUTPUT")
    return fig


# ════════════════════════════════════════════════════════════════════
# ██  LIVE SENSOR HISTORY
# ════════════════════════════════════════════════════════════════════
if "history" not in st.session_state:
    st.session_state.history = {k:[] for k in
        ["pressure","angle","force","stress","sf","disp"]}

def record(p,a,f,s,sf,d):
    M=200; h=st.session_state.history
    for k,v in zip(["pressure","angle","force","stress","sf","disp"],[p,a,f,s,sf,d]):
        h[k].append(v)
        if len(h[k])>M: h[k]=h[k][-M:]

if "geo" not in st.session_state:
    st.session_state.geo = make_default_geometry()
if "_file_key" not in st.session_state:
    st.session_state["_file_key"] = None

# ════════════════════════════════════════════════════════════════════
# ██  SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🦾 Digital Twin")
    st.markdown("---")

    uploaded = st.file_uploader("Upload Finger STL",type=["stl"],
        help="ASCII or binary STL. mm or m auto-detected.")
    if uploaded:
        fk = f"{uploaded.name}_{uploaded.size}"
        if st.session_state["_file_key"] != fk:
            try:
                with st.spinner("Parsing STL…"):
                    g = parse_stl(uploaded)
                st.session_state.geo = g
                st.session_state["_file_key"] = fk
                st.session_state.history = {k:[] for k in
                    ["pressure","angle","force","stress","sf","disp"]}
                st.success(f"✓  {g.n_triangles:,} triangles")
            except Exception as e:
                st.error(f"Parse error: {e}")
    else:
        if st.session_state.geo.source=="default":
            st.info("No STL — using default 80 mm geometry.")

    geo: STLGeometry = st.session_state.geo

    st.markdown("---")
    st.markdown("**Material**")
    mat_name = st.selectbox("Material", list(MATERIALS.keys()), label_visibility="collapsed")
    mat = MATERIALS[mat_name]

    st.markdown("---")
    pressure = st.slider("Pressure (kPa)", 0.0, float(geo.max_pressure),
        float(geo.max_pressure*0.35),
        step=max(0.5, float(geo.max_pressure/200)), format="%.0f kPa")

    st.markdown("---")
    n_seg     = st.slider("Arc segments", 5, 40, 20, step=5)
    show_3d   = st.checkbox("3-D mesh view",    value=geo.is_loaded)
    show_hist = st.checkbox("Live history",      value=True)

    st.markdown("---")
    # Geometry info
    if geo.is_loaded:
        d=geo.dimensions*1000
        st.markdown(f"""<div class="geo-card">
FILE   · {geo.filename}<br>TRIS   · {geo.n_triangles:,}<br>
L×W×H  · {d[0]:.1f}×{d[1]:.1f}×{d[2]:.1f} mm<br>
AREA   · {geo.surface_area*1e4:.2f} cm²<br>
VOL    · {geo.volume*1e6:.3f} cm³<br>
t_wall · {geo.wall_thickness*1e3:.2f} mm<br>
P_max  · {geo.max_pressure:.0f} kPa · θ_max {geo.max_angle:.0f}°
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="geo-card">
SOURCE · default<br>L · 80 mm · A · 4 cm²<br>
t · 3 mm · P_max · 200 kPa
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""<small style='color:#1a4060;font-family:Share Tech Mono;
font-size:0.68rem;line-height:1.9'>
MAT  · {mat_name.split("(")[0].strip()}<br>
E    · {mat['E']/1e6:.2f} MPa<br>
σ_u  · {mat['ultimate']/1e6:.2f} MPa<br>
ρ    · {mat['density']} kg/m³<br>
ν    · {mat['poisson']}
</small>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# ██  COMPUTE
# ════════════════════════════════════════════════════════════════════
res = full_analysis(pressure, geo, mat, n_seg)
xs, ys = res["xs"], res["ys"]

# Noisy sensor readings
angle_s = noise(res["total_angle_deg"])
force_s = noise(res["tip_force"])
disp_s  = noise(res["tip_disp_mm"])
sf_s    = noise(res["min_sf"])
stress_s= noise(res["max_total"])

grip_lbl, grip_cls = grip_tag(pressure, geo)
sf_lbl,   sf_cls   = sf_tag(res["min_sf"])
record(pressure, angle_s, force_s, stress_s, sf_s, disp_s)

# ════════════════════════════════════════════════════════════════════
# ██  TABS
# ════════════════════════════════════════════════════════════════════
st.markdown("# Soft Robotic Finger — Digital Twin")
src = f"`{geo.filename}`" if geo.is_loaded else "*default 80 mm geometry*"
st.markdown(f"Full structural analysis · {src} · material: **{mat_name}**")

col_tags = st.columns([1,1,1,5])
with col_tags[0]:
    st.markdown(f'<span class="tag {grip_cls}">{grip_lbl}</span>', unsafe_allow_html=True)
with col_tags[1]:
    st.markdown(f'<span class="tag {sf_cls}">SF {res["min_sf"]:.2f}</span>', unsafe_allow_html=True)
with col_tags[2]:
    st.markdown(f'<span class="tag tag-info">⚠ {res["weak_pos_mm"]:.1f} mm</span>', unsafe_allow_html=True)

st.markdown("---")

TAB_LIVE, TAB_STRUCT, TAB_LOAD, TAB_SIM = st.tabs([
    "📡  Live Monitor",
    "🔬  Structural Analysis",
    "⚖️  Load Capacity",
    "🎬  Simulation",
])

# ───────────────────────────────────────────────────────────────────
# TAB 1 — LIVE MONITOR
# ───────────────────────────────────────────────────────────────────
with TAB_LIVE:
    st.markdown('<div class="section-head">REAL-TIME PHYSICS OUTPUT</div>', unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("Pressure",     f"{pressure:.0f} kPa")
    c2.metric("Angle",        f"{angle_s:.1f} °")
    c3.metric("Tip Disp.",    f"{disp_s:.1f} mm")
    c4.metric("Tip Force",    f"{force_s:.4f} N")
    c5.metric("Peak Stress",  f"{stress_s:.1f} kPa")
    c6.metric("Safety Factor",f"{sf_s:.2f}")
    c7.metric("Weak Point",   f"{res['weak_pos_mm']:.1f} mm")

    st.markdown("")

    col_vis, col_charts = st.columns([1,1.4], gap="large")
    with col_vis:
        st.plotly_chart(build_2d_finger(res, geo, pressure),
            use_container_width=True, config={"displayModeBar":False})
        # Weak point callout
        st.markdown(f"""<div class="alert-box alert-yel">
⚠ <b>WEAK POINT</b> at {res['weak_pos_mm']:.1f} mm from base
· Safety Factor = <b>{res['min_sf']:.2f}</b>
· Stress = <b>{res['total_stress'][res['weak_idx']]/1e3:.1f} kPa</b>
</div>""", unsafe_allow_html=True)

        ml = res["max_load_pressure"]
        pct = pressure / ml * 100 if ml > 0 else 0
        if pct < 60:
            cls_ = "alert-grn"; msg = f"Operating at {pct:.0f}% of yield pressure — SAFE"
        elif pct < 90:
            cls_ = "alert-yel"; msg = f"Operating at {pct:.0f}% of yield pressure — CAUTION"
        else:
            cls_ = "alert-red"; msg = f"Operating at {pct:.0f}% of yield pressure — DANGER"
        st.markdown(f'<div class="alert-box {cls_}">{msg}</div>', unsafe_allow_html=True)

    with col_charts:
        st.plotly_chart(build_pv_chart(pressure, geo, res),
            use_container_width=True, config={"displayModeBar":False})
        st.plotly_chart(build_force_chart(pressure, geo),
            use_container_width=True, config={"displayModeBar":False})

    if show_3d and geo.is_loaded:
        st.markdown("---")
        st.plotly_chart(build_3d_mesh(geo, angle_s, res["safety_factor"]),
            use_container_width=True, config={"displayModeBar":True})
        st.caption("Mesh colour = Safety Factor per segment  (red < 1.5 < yellow < 3 < green)")

    if show_hist:
        st.markdown("---")
        st.markdown('<div class="section-head">LIVE SENSOR HISTORY</div>', unsafe_allow_html=True)
        h = st.session_state.history
        if len(h["pressure"]) >= 2:
            t_ = list(range(len(h["pressure"])))
            fig_h = make_subplots(rows=2,cols=3,
                subplot_titles=("Pressure","Angle","Force","Displacement","Stress","Safety Factor"),
                vertical_spacing=0.14, horizontal_spacing=0.08)
            pairs_h=[
                (1,1,h["pressure"],C4),(1,2,h["angle"],C1),(1,3,h["force"],C2),
                (2,1,h["disp"],C3),(2,2,h["stress"],C5),(2,3,h["sf"],C3),
            ]
            for row,col,yy,c in pairs_h:
                fig_h.add_trace(go.Scatter(x=t_,y=yy,mode="lines",
                    line=dict(color=c,width=1.5),showlegend=False),row=row,col=col)
                fig_h.update_xaxes(gridcolor=GRID,linecolor=GRID,row=row,col=col)
                fig_h.update_yaxes(gridcolor=GRID,linecolor=GRID,row=row,col=col)
            fig_h.update_layout(paper_bgcolor=BG,plot_bgcolor=PBG,
                font=dict(family="DM Sans",color=FONT),
                height=380,margin=dict(l=44,r=12,t=44,b=36))
            mono_title(fig_h,"LIVE SENSOR HISTORY")
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar":False})
        else:
            st.caption("Adjust pressure to start recording.")

# ───────────────────────────────────────────────────────────────────
# TAB 2 — STRUCTURAL ANALYSIS
# ───────────────────────────────────────────────────────────────────
with TAB_STRUCT:
    st.markdown('<div class="section-head">FULL STRUCTURAL ANALYSIS</div>', unsafe_allow_html=True)

    # Summary metrics
    cs1,cs2,cs3,cs4,cs5 = st.columns(5)
    cs1.metric("Max Hoop σ",   f"{res['hoop_stress'].max()/1e3:.1f} kPa")
    cs2.metric("Max Axial σ",  f"{res['axial_stress'].max()/1e3:.1f} kPa")
    cs3.metric("Max Bending σ",f"{res['bending_stress'].max()/1e3:.1f} kPa")
    cs4.metric("Max Von Mises",f"{res['vm_stress'].max()/1e3:.1f} kPa")
    cs5.metric("Max Strain ε", f"{res['strain'].max()*100:.2f} %")

    st.markdown("")
    st.plotly_chart(build_stress_heatmap(res, geo),
        use_container_width=True, config={"displayModeBar":False})
    st.plotly_chart(build_stress_component_chart(res, geo),
        use_container_width=True, config={"displayModeBar":False})

    # Segment table
    st.markdown('<div class="section-head">PER-SEGMENT DATA TABLE</div>', unsafe_allow_html=True)
    N_ = len(res["total_stress"])
    pos_ = [f"{(i+0.5)*geo.finger_length*1000/N_:.1f}" for i in range(N_)]
    table_fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Pos (mm)","Area (mm²)","Hoop σ (kPa)",
                    "Bending σ (kPa)","VM σ (kPa)","Total σ (kPa)","Safety Factor"],
            fill_color="#0c1520", line_color=GRID,
            font=dict(family="Share Tech Mono",color="#4a8ab5",size=10),
            align="center",
        ),
        cells=dict(
            values=[
                pos_,
                [f"{a*1e6:.2f}" for a in res["A_seg"]],
                [f"{v/1e3:.1f}" for v in res["hoop_stress"]],
                [f"{v/1e3:.1f}" for v in res["bending_stress"]],
                [f"{v/1e3:.1f}" for v in res["vm_stress"]],
                [f"{v/1e3:.1f}" for v in res["total_stress"]],
                [f"{v:.2f}" for v in res["safety_factor"]],
            ],
            fill_color=[
                ["#0c1520"]*N_,
                ["#0c1520"]*N_,
                ["#0c1520"]*N_,
                ["#0c1520"]*N_,
                ["#0c1520"]*N_,
                ["#0c1520"]*N_,
                [("#1a0808" if sf<1.5 else "#1a1200" if sf<3 else "#081408")
                 for sf in res["safety_factor"]],
            ],
            line_color=GRID,
            font=dict(family="Share Tech Mono",color="#c8d6e5",size=10),
            align="center", height=24,
        ),
    )])
    table_fig.update_layout(paper_bgcolor=BG, height=380,
        margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(table_fig, use_container_width=True, config={"displayModeBar":False})

# ───────────────────────────────────────────────────────────────────
# TAB 3 — LOAD CAPACITY
# ───────────────────────────────────────────────────────────────────
with TAB_LOAD:
    st.markdown('<div class="section-head">LOAD CAPACITY  &  FAILURE ANALYSIS</div>', unsafe_allow_html=True)

    ml = res["max_load_pressure"]
    ml_angle  = pressure_to_angle(min(ml, geo.max_pressure), geo)
    ml_force  = min(ml,geo.max_pressure)*1e3*geo.cross_section
    pct_used  = pressure/ml*100 if ml>0 else 0
    safety_margin = ml - pressure

    cl1,cl2,cl3,cl4 = st.columns(4)
    cl1.metric("Yield Pressure",  f"{ml:.1f} kPa", help="Pressure at which weakest segment yields")
    cl2.metric("Max Tip Force",   f"{ml_force:.4f} N", help="Force at yield pressure")
    cl3.metric("Safety Margin",   f"{safety_margin:.1f} kPa")
    cl4.metric("Fatigue Life",    f"{res['n_fatigue']:,} cycles",
               help="Estimated cycles to failure at current pressure (Coffin-Manson)")

    st.markdown("")

    # Risk summary
    if pct_used < 50:
        st.markdown(f"""<div class="alert-box alert-grn">
✓ FINGER IS OPERATING SAFELY.  Current pressure is {pct_used:.0f}% of yield pressure.
  Remaining margin: {safety_margin:.1f} kPa.  Estimated fatigue life: {res['n_fatigue']:,} cycles.</div>""",
            unsafe_allow_html=True)
    elif pct_used < 80:
        st.markdown(f"""<div class="alert-box alert-yel">
⚠ APPROACHING SAFE LIMIT.  Current pressure is {pct_used:.0f}% of yield pressure.
  Reduce pressure if continuous operation is intended.
  Weak point at {res['weak_pos_mm']:.1f} mm from base.</div>""",
            unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="alert-box alert-red">
✖ OVERLOAD — FAILURE RISK.  Current pressure ({pressure:.0f} kPa) exceeds {pct_used:.0f}% of yield ({ml:.1f} kPa).
  Segment {res['weak_idx']+1} at {res['weak_pos_mm']:.1f} mm is at critical stress.
  Reduce pressure immediately.</div>""",
            unsafe_allow_html=True)

    st.markdown("")
    col_sf, col_fat = st.columns(2, gap="large")
    with col_sf:
        st.plotly_chart(build_sf_vs_pressure(geo, mat),
            use_container_width=True, config={"displayModeBar":False})
    with col_fat:
        st.plotly_chart(build_fatigue_chart(geo, mat),
            use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div class="section-head">MULTI-MATERIAL COMPARISON AT CURRENT PRESSURE</div>',
        unsafe_allow_html=True)
    mat_names_ = list(MATERIALS.keys())
    sfs_   = []; forces_ = []; mls_ = []
    for mn in mat_names_:
        m_ = MATERIALS[mn]
        r_ = full_analysis(pressure, geo, m_, 20)
        sfs_.append(r_["min_sf"])
        forces_.append(r_["tip_force"]*1000)   # mN
        mls_.append(r_["max_load_pressure"])
    comp_fig = make_subplots(rows=1,cols=3,
        subplot_titles=("Safety Factor","Tip Force (mN)","Yield Pressure (kPa)"),
        horizontal_spacing=0.10)
    colors_ = [MATERIALS[m]["color"] for m in mat_names_]
    labels_ = [m.split("(")[0].strip() for m in mat_names_]
    for col_i, vals in enumerate([sfs_, forces_, mls_], start=1):
        comp_fig.add_trace(go.Bar(x=labels_,y=vals,marker_color=colors_,
            showlegend=False), row=1, col=col_i)
        comp_fig.update_xaxes(gridcolor=GRID,linecolor=GRID,
            tickangle=-30,tickfont=dict(size=9),row=1,col=col_i)
        comp_fig.update_yaxes(gridcolor=GRID,linecolor=GRID,row=1,col=col_i)
    if len(sfs_) > 0:
        comp_fig.add_hline(y=1.0,line_dash="dot",line_color=C2,row=1,col=1)
        comp_fig.add_hline(y=3.0,line_dash="dot",line_color=C3,row=1,col=1)
    comp_fig.update_layout(paper_bgcolor=BG,plot_bgcolor=PBG,
        font=dict(family="DM Sans",color=FONT),
        height=340,margin=dict(l=44,r=12,t=44,b=64))
    mono_title(comp_fig,"MATERIAL COMPARISON")
    st.plotly_chart(comp_fig, use_container_width=True, config={"displayModeBar":False})

# ───────────────────────────────────────────────────────────────────
# TAB 4 — SIMULATION
# ───────────────────────────────────────────────────────────────────
with TAB_SIM:
    st.markdown('<div class="section-head">SIMULATION ENGINE</div>', unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        sim_mode = st.selectbox("Simulation mode", [
            "Pressure Ramp","Pulse (square wave)","Sinusoidal",
            "Step response","Fatigue sweep",
        ])
    with sc2:
        p_start_s = st.slider("Start pressure (kPa)", 0.0, float(geo.max_pressure),
            0.0, step=1.0)
        p_end_s   = st.slider("End pressure (kPa)",   0.0, float(geo.max_pressure),
            float(geo.max_pressure*0.7), step=1.0)
    with sc3:
        n_steps_s = st.slider("Steps", 50, 500, 200, step=50)
        dt_s      = st.slider("Δt (s)", 0.01, 0.5, 0.05, step=0.01)

    if st.button("▶  Run Simulation", use_container_width=True):
        with st.spinner(f"Running '{sim_mode}' simulation — {n_steps_s} steps…"):
            sim_res = run_simulation(sim_mode, geo, mat,
                                     p_start_s, p_end_s, n_steps_s, dt_s)
        st.session_state["sim_res"] = sim_res
        st.session_state["sim_mode"] = sim_mode

    if "sim_res" in st.session_state:
        sim = st.session_state["sim_res"]
        mode_lbl = st.session_state.get("sim_mode","")
        st.plotly_chart(build_sim_chart(sim),
            use_container_width=True, config={"displayModeBar":False})

        # Summary stats
        st.markdown('<div class="section-head">SIMULATION SUMMARY</div>', unsafe_allow_html=True)
        ss1,ss2,ss3,ss4,ss5 = st.columns(5)
        ss1.metric("Max Angle",      f"{sim['angles'].max():.1f} °")
        ss2.metric("Max Force",      f"{sim['forces'].max():.5f} N")
        ss3.metric("Max Stress",     f"{sim['stresses'].max():.1f} kPa")
        ss4.metric("Min Safety F.",  f"{sim['safety_factors'].min():.2f}")
        ss5.metric("Max Tip Disp.",  f"{sim['tip_disps'].max():.1f} mm")

        # Any overload events?
        overload_steps = int((sim["safety_factors"] < 1.0).sum())
        if overload_steps > 0:
            st.markdown(f"""<div class="alert-box alert-red">
✖ OVERLOAD DETECTED in {overload_steps} / {n_steps_s} steps.
  Finger exceeded yield stress during simulation.
  Consider reducing peak pressure or choosing a stronger material.</div>""",
                unsafe_allow_html=True)
        elif (sim["safety_factors"] < 1.5).any():
            st.markdown(f"""<div class="alert-box alert-yel">
⚠ MARGINAL SAFETY FACTOR reached during simulation (min SF = {sim['safety_factors'].min():.2f}).
  Monitor closely during real operation.</div>""",
                unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="alert-box alert-grn">
✓ SIMULATION COMPLETED SAFELY.  Minimum safety factor: {sim['safety_factors'].min():.2f}.
  Finger operated within safe limits throughout the entire cycle.</div>""",
                unsafe_allow_html=True)
    else:
        st.info("Configure parameters above and press **▶ Run Simulation** to begin.")

# ════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<small style='color:#182030;font-family:Share Tech Mono'>"
    "SOFT FINGER DIGITAL TWIN v3.0  ·  hoop + axial + bending + Von Mises stress  ·  "
    "Coffin-Manson fatigue  ·  per-segment safety factor  ·  5 material models  ·  "
    "pure-Python STL parser  ·  no FEM"
    "</small>",
    unsafe_allow_html=True,
)
