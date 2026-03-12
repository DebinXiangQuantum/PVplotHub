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

# 定义投影 (Robinson)
target_crs = "ESRI:54030" 

print("Fixing 180-degree meridian issue and projecting...")
# 1. 在地理坐标系下预先裁切 180 度经线，防止产生横跨地图的长线
clean_bbox = box(-179.9, -85, 179.9, 85)
world_gdf = world_gdf.clip(clean_bbox)
solar_gdf = solar_gdf.clip(clean_bbox)

# 2. 转换到目标投影
world_gdf = world_gdf.to_crs(target_crs)
solar_gdf = solar_gdf.to_crs(target_crs)

# --- 修复裂缝：为多边形添加极小的缓冲区 (Robinson 投影单位为米，80米足以填补缝隙且不会造成明显的海岸线溢出) ---
print("Fine-tuning geometry...")
solar_gdf['geometry'] = solar_gdf.geometry.buffer(80, cap_style=3, join_style=2)

# 数据预处理
solar_gdf['光照强'] = pd.to_numeric(solar_gdf['光照强'], errors='coerce') * 12 / 1e6
for col in ['jizhong_ar', 'fenbu_area', 'total_area']:
    solar_gdf[col] = pd.to_numeric(solar_gdf[col], errors='coerce') * 0.2 / 1e6

# --- 3. 定义可视化参数 ---
custom_bins = [2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000]
custom_colors = [
    '#3a0ca3', '#4361ee', '#4cc9f0', '#00f5d4', '#9ef01a', 
    '#ccff33', '#ffff00', '#ffb700', '#ff7b00', '#ff0000'
]
legend_labels = [
    '<2500', '2500-3000', '3000-3500', '3500-4000', '4000-4500',
    '4500-5000', '5000-6000', '6000-7000', '7000-8000', '>8000'
]
cmap_custom = mcolors.ListedColormap(custom_colors)

# --- 4. 绘图 ---
fig, ax = plt.subplots(figsize=(nature_double_col_width, nature_double_col_width * 0.5))

# Layer 1: 世界底图 (填充白色背景)
world_gdf.plot(ax=ax, color='#FFFFFF', zorder=1)

# Layer 2: 光照强度填充层 (栅格化)
print("Plotting Solar intensity...")
# 调整参数：去掉 edgecolor='none'，改用极细的 linewidth 配合 antialiased=False 有助于消除缝隙
solar_gdf.plot(
    column='光照强',
    ax=ax,
    scheme='UserDefined',
    classification_kwds={'bins': custom_bins},
    cmap=cmap_custom, 
    legend=False, 
    linewidth=0.05, 
    antialiased=False, 
    rasterized=True,
    zorder=2
)

# Layer 2.5: 国界线 (置于光照层之上，确保清晰)
world_gdf.plot(ax=ax, facecolor='none', edgecolor="#FFFFFF", linewidth=0.15, zorder=6)

COLOR_DISTRIB  = '#FF00FF'  
COLOR_CENTRAL = "#0090F6"  
COLOR_BOTH    = "#000000"  

# Layer 3: 绘制 PV 散点层
print("Plotting PV types...")
# ... 保持 zorder 3, 4, 5 不变，或者也可以根据需要微调

# 逻辑筛选
j_mask = solar_gdf['jizhong_ar'] > 1e-5
d_mask = solar_gdf['fenbu_area'] > 1e-5

both_pts = solar_gdf[j_mask & d_mask].copy()
central_pts = solar_gdf[j_mask & ~d_mask].copy()
distrib_pts = solar_gdf[~j_mask & d_mask].copy()

# 转换为重心点并绘图
def plot_pv_layer(gdf, color, label_name, z_order):
    if gdf.empty:
        return
    print(f"  - {label_name}: {len(gdf)} points")
    gdf['geometry'] = gdf.geometry.centroid
    # 采样以防 PDF 过大
    if len(gdf) > 30000:
        gdf = gdf.sample(n=30000, random_state=42)
    gdf.plot(
        ax=ax, markersize=0.1, marker='o', color=color, 
        edgecolor='none', alpha=0.7, zorder=z_order, rasterized=True
    )

plot_pv_layer(distrib_pts, COLOR_DISTRIB, "Distributed PV Only", 3)
plot_pv_layer(central_pts, COLOR_CENTRAL, "Utility-scale PV Only", 4)
plot_pv_layer(both_pts, COLOR_BOTH, "Both PV Types", 5)

# --- 5. 手动定制图例 ---
# 5.1 光照强度图例
rad_handles = []
for i in range(len(custom_colors)):
    patch = mpatches.Patch(color=custom_colors[i], label=legend_labels[i])
    rad_handles.append(patch)

leg1 = ax.legend(
    handles=rad_handles,
    title='Solar Radiation\n (MJ/m2)',
    loc='lower left',
    bbox_to_anchor=(0.95, 0.30), 
    frameon=False,
    fontsize=6,
    title_fontsize=6,
    handlelength=1.2,
    handleheight=0.7,
    labelspacing=0.2
)
leg1._legend_box.align = "left"
ax.add_artist(leg1) # 必须手动添加，否则会被下一个 legend 覆盖

# 5.2 PV 类型图例
central_leg = plt.Line2D([0], [0], marker='o', color='w', label='Utility-scale Only',
                          markerfacecolor=COLOR_CENTRAL, markersize=4)
distrib_leg = plt.Line2D([0], [0], marker='o', color='w', label='Distributed Only',
                        markerfacecolor=COLOR_DISTRIB, markersize=4)
both_leg    = plt.Line2D([0], [0], marker='o', color='w', label='Both Types',
                        markerfacecolor=COLOR_BOTH, markersize=4)

pv_handles = [central_leg, distrib_leg, both_leg]

leg2 = ax.legend(
    handles=pv_handles,
    title='PV Type',
    loc='lower left',
    bbox_to_anchor=(0.95, 0.15), 
    frameon=False,
    fontsize=6,
    title_fontsize=6,
    handlelength=1.2,
    handleheight=0.7,
    labelspacing=0.2
)
leg2._legend_box.align = "left"

plt.axis('off')
plt.tight_layout()

# --- 6. 保存结果 ---
print("Saving figure...")
plt.savefig('exported_plots/solar_pv_combined_map.pdf', dpi=300, bbox_inches='tight')
print("Done.")