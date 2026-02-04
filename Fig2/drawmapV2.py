import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
from shapely.geometry import box
import matplotlib as mpl

# --- 1. Nature 标准环境设置 ---
mm_to_inch = 1 / 25.4
nature_double_col_width = 180 * mm_to_inch

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.size'] = 6
mpl.rcParams['axes.linewidth'] = 0.5

# --- 2. 路径与数据加载 ---
solar_path = r"data/10km/Solar_10km.shp"
world_path = "data/map/世界国家地图.shp"

print("Loading and projecting data...")
solar_gdf = gpd.read_file(solar_path)
world_gdf = gpd.read_file(world_path)

# 定义投影 (Robinson) 并修复 180 度经线裁切问题
target_crs = "ESRI:54030" 
clean_bbox = box(-179.9, -58, 179.9, 85)
world_gdf = world_gdf.clip(clean_bbox).to_crs(target_crs)
solar_gdf = solar_gdf.clip(clean_bbox).to_crs(target_crs)

# 数据预处理
solar_gdf['光照强'] = pd.to_numeric(solar_gdf['光照强'], errors='coerce') * 12 / 1e6
for col in ['jizhong_ar', 'fenbu_area', 'total_area']:
    solar_gdf[col] = pd.to_numeric(solar_gdf[col], errors='coerce') * 0.2 / 1e6

# --- 3. 定义可视化参数 (精准复刻原图色阶) ---
custom_bins = [2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000]
custom_colors = [
    '#3a0ca3', # <2500
    '#4361ee', # 2500-3000
    '#4cc9f0', # 3000-3500
    '#00f5d4', # 3500-4000
    '#9ef01a', # 4000-4500
    '#ccff33', # 4500-5000
    '#ffff00', # 5000-6000
    '#ffb700', # 6000-7000
    '#ff7b00', # 7000-8000
    '#ff0000', # >8000
]
legend_labels = [
    '<2500', '2500-3000', '3000-3500', '3500-4000', '4000-4500',
    '4500-5000', '5000-6000', '6000-7000', '7000-8000', '>8000'
]
cmap_custom = mcolors.ListedColormap(custom_colors)

# --- 4. 绘图 ---
fig, ax = plt.subplots(figsize=(nature_double_col_width, nature_double_col_width * 0.45))

# Layer 1: 世界底图 (灰色边框)
world_gdf.plot(ax=ax, color='#FFFFFF', edgecolor='#d0d0d0', linewidth=0.2, zorder=1)

# Layer 2: 光照强度填充层 (栅格化处理以减小体积)
print("Plotting Solar intensity...")
solar_gdf.plot(
    column='光照强',
    ax=ax,
    scheme='UserDefined',
    classification_kwds={'bins': custom_bins},
    cmap=cmap_custom, 
    legend=False,  # 我们稍后手动添加图例
    edgecolor='none', 
    linewidth=0,
    rasterized=True,
    zorder=2
)

# Layer 3: 分布式 PV 散点层
print("Plotting Scatter points...")
solar_points = solar_gdf.dropna(subset=['total_area']).copy()
solar_points = solar_points[solar_points['total_area'] > 1e-4]
solar_points['geometry'] = solar_points.geometry.centroid

# 采样优化
if len(solar_points) > 40000:
    solar_points = solar_points.sample(n=40000, random_state=42)

solar_points.plot(
    ax=ax,
    markersize=0.15,
    marker='o',
    color='#5e2ca5', # 深紫色
    edgecolor='none',
    alpha=0.7,
    zorder=3,
    rasterized=True
)

# --- 5. 手动定制条形色块图例 ---
legend_handles = []
for i in range(len(custom_colors)):
    patch = mpatches.Patch(color=custom_colors[i], label=legend_labels[i])
    legend_handles.append(patch)

leg = ax.legend(
    handles=legend_handles,
    title='Solar Radiation(MJ/m2)',
    loc='lower left',
    bbox_to_anchor=(0.02, 0.1), 
    frameon=False,
    fontsize=5,
    title_fontsize=6,
    handlelength=1.2,  # 条形块长度
    handleheight=0.7,  # 条形块高度
    labelspacing=0.35  # 条目间距
)
leg._legend_box.align = "left"

# # --- 6. 装饰元素 (指北针 & 标题) ---
# # 指北针
# ax.text(0.96, 0.95, 'N', transform=ax.transAxes, fontsize=10, ha='center', fontweight='bold')
# ax.annotate('', xy=(0.96, 0.88), xytext=(0.96, 0.95),
#             transform=ax.transAxes, arrowprops=dict(facecolor='black', width=0.8, headwidth=4))

# 左上角大标题
# ax.text(0.02, 0.95, 'Distributed PV', transform=ax.transAxes, fontsize=8, fontweight='bold', ha='left')

plt.axis('off')
plt.tight_layout()

# --- 7. 保存结果 ---
print("Saving figure...")
plt.savefig('exported_plots/solar_visualization_fixed.pdf', dpi=300, bbox_inches='tight')
print("Done.")