import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

# --- 1. 环境配置 (Nature 风格) ---
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['pdf.fonttype'] = 42  # 确保字体在PDF中可编辑
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['ytick.direction'] = 'out'

# 设置物理尺寸: 60mm 宽 (约 2.36 英寸)
# Nature 常用字号为 5-7pt，这里统一设为 6pt
width_mm = 60
width_inch = width_mm / 25.4
height_inch = width_inch * 1.0  # 保持正方形比例
FS = 6  # Font Size

# --- 2. 数据处理 ---
try:
    df = pd.read_excel('excel/GDPvsPV.xlsx', sheet_name='DistributedPV')
except Exception:
    # 模拟数据供测试
    data = {
        'ShortName': ['CHN', 'USA', 'IND', 'DEU', 'JPN', 'ESP', 'MLT', 'LBN', 'ZAF', 'PAK', 'SOM', 'GUY'],
        'GDPPerCapita': [4.1, 4.9, 3.4, 4.7, 4.5, 4.5, 4.6, 3.5, 3.8, 3.2, 2.8, 4.3],
        'PVCapPerCapita': [-0.3, -0.1, -1.5, 0.0, 0.04, -0.1, 0.4, 0.1, -0.5, -1.0, -3.1, -3.4],
        'TotalCapacity': [60, 45, 15, 55, 50, 30, 5, 2, 10, 8, 0.5, 1]
    }
    df = pd.DataFrame(data)

x = df['GDPPerCapita']
y = df['PVCapPerCapita']
c = df.get('TotalCapacity', np.random.uniform(0, 65, len(df))) # 若无GW数据则随机模拟
x_med, y_med = x.median(), y.median()

# --- 3. 创建画布 ---
fig = plt.figure(figsize=(width_inch, height_inch + 0.5)) # 预留底部色条空间
ax = fig.add_axes([0.15, 0.25, 0.8, 0.7]) # [left, bottom, width, height]

# --- 4. 绘制象限背景 (精确匹配原图颜色) ---
# Quadrant II: 洋红色/深粉色
ax.add_patch(Rectangle((0, y_med), x_med, 2-y_med, color='#D83084', alpha=0.9, zorder=0))
# Quadrant I: 青绿色
ax.add_patch(Rectangle((x_med, y_med), 6-x_med, 2-y_med, color='#99C9C1', alpha=0.9, zorder=0))
# Quadrant III: 黄色
ax.add_patch(Rectangle((0, -4), x_med, y_med+4, color='#E9D154', alpha=0.9, zorder=0))
# Quadrant IV: 白色 (默认)

# --- 5. 核心绘图内容 ---
# 绘制中位数虚线
ax.axhline(y_med, color='#666666', linestyle=(0, (5, 5)), linewidth=0.8, zorder=1)
ax.axvline(x_med, color='#666666', linestyle=(0, (5, 5)), linewidth=0.8, zorder=1)

# 绘制 45度 参考线 (灰色)
ax.plot([2, 5.8], [-3, 0.7], color='#CCCCCC', linewidth=0.8, zorder=1)
ax.text(2.1, -2.2, '$45^{\circ}$', color='#2ecc71', fontsize=FS, zorder=2)

# 定义自定义 Colormap (Teal -> White -> Orange -> Brown)
colors = ["#006D5B", "#4DB6AC", "#F5F5DC", "#E65100", "#5D3011"]
cmap_custom = LinearSegmentedColormap.from_list("nature_dist", colors, N=256)

# 绘制散点
sc = ax.scatter(x, y, c=c, cmap=cmap_custom, s=12, edgecolors='none', alpha=0.9, zorder=3)

# --- 6. 标签与装饰 ---
# 象限编号
for label, pos in zip(['I', 'II', 'III', 'IV'], [(5.6, 1.7), (0.2, 1.7), (0.2, -3.8), (5.6, -3.8)]):
    ax.text(pos[0], pos[1], label, fontsize=FS+2, fontweight='normal')

# 标注 Median 字样
ax.text(x_med-0.1, 1.9, 'Median', fontsize=FS, rotation=0, ha='right')
ax.text(5.9, y_med, 'Median', fontsize=FS, rotation=-90, va='center')

# 国家标签 (精选部分展示，避免拥挤)
targets = ['CHN', 'USA', 'IND', 'LBN', 'PAK', 'SOM', 'GUY', 'MLT', 'ZAF']
for i, txt in enumerate(df['ShortName']):
    if txt in targets:
        ax.text(x[i]+0.05, y[i]+0.05, txt, fontsize=FS-1, color='#30336B', zorder=4)

# 坐标轴设置
ax.set_xlim(0, 6)
ax.set_ylim(-4, 2)
ax.set_xlabel('GDP per capita ($, log scale)', fontsize=FS)
ax.set_ylabel('Per capita PV capacity\n(MW/10000 person, log scale)', fontsize=FS)
ax.set_title('Distributed PV', fontsize=FS+1, loc='left', x=0.1, y=0.9)
ax.tick_params(labelsize=FS)

# --- 7. 底部色条 (Colorbar) ---
cax = fig.add_axes([0.2, 0.12, 0.7, 0.03]) # 底部位置
cb = plt.colorbar(sc, cax=cax, orientation='horizontal')
cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=FS, length=0)
cb.set_ticks([0, 65])
fig.text(0.85, 0.15, 'Unit: GW', fontsize=FS)

# 最终修饰
plt.savefig('Nature_PV_Plot.pdf', dpi=300, bbox_inches='tight') # 建议导出PDF
plt.show()