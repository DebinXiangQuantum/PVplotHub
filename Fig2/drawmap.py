import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import sys
from shapely.geometry import box
import matplotlib as mpl
import sys

from matplotlib.colorbar import ColorbarBase
mm_to_inch = 1 / 25.4
nature_double_col_width = 180 * mm_to_inch

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['text.usetex'] = False
mpl.rcParams['font.size'] = 6
mpl.rcParams['axes.linewidth'] = 0.5

# 1. File Paths
solar_path = r"data/10km/Solar_10km.shp"
world_path = "data/map/世界国家地图.shp"

# 2. Load Data
print("Loading data...")
solar_gdf = gpd.read_file(solar_path)
world_gdf = gpd.read_file(world_path)
target_crs = "ESRI:54030" 
# D. 投影处理 (修复 180度横线问题 + 椭圆计算)
clean_bbox = box(-179.99, -57.99, 179.99, 89.99)

# 对底图和数据同时进行微量裁剪和修复
world_gdf = world_gdf.clip(clean_bbox).to_crs(target_crs)
solar_gdf = solar_gdf.clip(clean_bbox).to_crs(target_crs)

# 2. 转换世界地图投影

# 3. Data Preprocessing
solar_gdf['光照强'] = pd.to_numeric(solar_gdf['光照强'], errors='coerce')*12/1e6
for col in ['jizhong_ar','fenbu_area','total_area']:
    solar_gdf[col] = pd.to_numeric(solar_gdf[col], errors='coerce')*0.2/1e6

# 4. Define Visualization Parameters

# --- A. 自定义颜色和分级 (复刻您的截图) ---
# 分级断点 (注意：UserDefined 只需要指定中间的断点，不需要 min/max)
custom_bins = [2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000]

# 自定义颜色列表 (10个颜色，对应 10 个区间)
# 区间: <2500, 2500-3000, ..., 7000-8000, >8000
custom_colors = [
    '#3a0ca3', # <2500 (深蓝)
    '#4361ee', # 2500-3000
    '#4cc9f0', # 3000-3500
    '#00f5d4', # 3500-4000 (青)
    '#9ef01a', # 4000-4500 (浅绿)
    '#ccff33', # 4500-5000
    '#ffff00', # 5000-6000 (黄)
    '#ffb700', # 6000-7000
    '#ff7b00', # 7000-8000
    '#ff0000', # >8000 (红)
]
# 创建 Colormap 对象
cmap_custom = mcolors.ListedColormap(custom_colors)

# 5. Plotting
# 设置符合 Nature 要求的尺寸 (180mm 宽)
fig, ax = plt.subplots(figsize=(nature_double_col_width, nature_double_col_width*0.5)) 

# Layer 1: World Map (Background)
world_gdf.plot(
    ax=ax,
    color='#FFF',
    edgecolor='#bbbbbb',
    linewidth=0.3,
    zorder=1
)

# Layer 2: Solar Intensity (Filled Colors)
print("Plotting Solar Layer...")
solar_gdf.plot(
    column='光照强',
    ax=ax,
    scheme='UserDefined',
    classification_kwds={'bins': custom_bins},
    cmap=cmap_custom, 
    legend=True,
    legend_kwds={
        'title': 'Solar Radiation (MJ/m²)', 
        'loc': 'lower left',
        'fontsize': 5,
        'title_fontsize': 6,
        'frameon': False
    },
    alpha=1,
    # ★关键修改★：去掉边框，否则图会全黑！
    edgecolor='none', 
    linewidth=0,
    rasterized=True,
    zorder=2
)

# 确保 solar_gdf 也转换到同样的投影
# 复制一份用于画散点
solar_points = solar_gdf.copy()
solar_points = solar_points.dropna(subset=['total_area'])
solar_points = solar_points[solar_points['total_area'] > 1e-3]
# 在投影坐标系下计算质心，不会弹出警告
solar_points['geometry'] = solar_points.geometry.centroid
# 调整点的大小
scale_factor = 1
area_sizes = (solar_points['total_area'] / solar_points['total_area'].max()) * scale_factor
# 避免点太小看不到，加一个基数
area_sizes = area_sizes + 0.5 

# # 对数映射处理：
# # 使用 np.log10 让面积分布更均匀
# # 我们将 log 后的值线性映射到一个视觉舒适的尺寸范围
# log_area = np.log10(solar_points['total_area'])
# log_min, log_max = log_area.min(), log_area.max()

# # 这里的 3e-4 是你提到的参考值。在对数映射下，我们设置一个基础倍数
# # 你可以通过调整 base_size 来整体放大或缩小点
# base_size = 3e-4 
# # 映射到 [0.1, 5] 这种 matplotlib 标准 point 尺寸，或者直接按你的比例缩放
# solar_points['markersize'] = ((log_area - log_min) / (log_max - log_min)) * 5 + 0.1

# # --- 3. 抽样优化 (解决文件体积与渲染压力) ---
# # 如果点数超过 2 万，建议抽样。在 Robinson 投影下，2 万个分布均匀的点足以表达全球趋势
# if len(solar_points) > 20000:
#     plot_points = solar_points.sample(n=20000, random_state=42)
# else:
#     plot_points = solar_points

# 如果点数超过 5 万，建议抽样展示，否则 PDF 渲染依然会卡顿
if len(solar_points) > 50000:
    plot_points = solar_points.sample(n=50000, random_state=42)
else:
    plot_points = solar_points
# # Layer 3: Total Area (Scatter Points)
# print("Plotting Scatter Layer...")
plot_points.plot(
    ax=ax,
    markersize=0.3,
    marker='.',          # 使用圆点
    color='#800080',     # 紫色实心
    edgecolor='none',    # 【关键】移除边框，防止变成空心圆感
    linewidth=0,         # 线宽设为0
    alpha=0.7,           # 稍微透明一点可以让重叠部分更有质感
    zorder=3,
    rasterized=True,      # 【必须】解决 PDF 打不开的问题
    label='Total Area'
)

# 6. Final Touches
# plt.title('Global Solar Intensity and Total Area Distribution', fontsize=7)
plt.axis('off')
plt.tight_layout()

# Save
print("Saving figure...")
# 建议保存为高 DPI 的 PNG 以查看效果，PDF 用于投稿
plt.savefig('exported_plots/solar_visualization_fixed.pdf', dpi=300, bbox_inches='tight')
# plt.show()
print("Done.")
