import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.interpolate import make_interp_spline

# --- 1. 全局 Nature 样式配置 ---
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'font.size': 6,             # Nature 常用字号 5-7pt
    'axes.linewidth': 0.5,      # 细边框
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.direction': 'out',
    'ytick.direction': 'out'
})

# 定义国家列表
COUNTRIES = ['China', 'United States', 'India', 'Germany', 'Japan', 'Spain', 'Australia', 'Mexico', 'Chile']

# 定义颜色方案 (Nature 风格)
COLOR_CENTRAL = '#E63946'  # 集中式：深红
COLOR_DISTRIB = '#1D3557'  # 分布式：深蓝

def export_distribution_plots(excel_path, output_dir='exported_plots'):
    """
    批量导出九个国家的装机量分布图
    """
    # 创建输出文件夹
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 加载数据
    df = pd.read_excel(excel_path)
    df.columns = [str(c).strip() for c in df.columns]
    
    # 确保 X 轴（光照）存在并排序
    if '光照' not in df.columns:
        print("错误：Excel 中未找到 '光照' 列")
        return
    df = df.sort_values(by='光照')
    x = df['光照'].values

    for country in COUNTRIES:
        # 尝试匹配列名（处理“国家 类别”或“类别 国家”两种情况）
        col_c = next((c for c in df.columns if country in c and '集中式' in c), None)
        col_d = next((c for c in df.columns if country in c and '分布式' in c), None)
        
        if not col_c or not col_d:
            print(f"跳过 {country}: 未找到对应数据列")
            continue

        # 创建符合比例的画布 (例如 40mm x 30mm)
        mm_to_inch = 1 / 25.4
        fig, ax = plt.subplots(figsize=(45 * mm_to_inch, 35 * mm_to_inch))

        # 绘图逻辑：平滑曲线 + 渐变填充
        for col_name, color, label in [(col_c, COLOR_CENTRAL, 'Centralized'), 
                                       (col_d, COLOR_DISTRIB, 'Distributed')]:
            y = df[col_name].values
            
            # 数据平滑处理
            mask = ~np.isnan(y)
            if len(x[mask]) > 3:
                x_smooth = np.linspace(x[mask].min(), x[mask].max(), 300)
                spl = make_interp_spline(x[mask], y[mask], k=3)
                y_smooth = np.maximum(spl(x_smooth), 0) # 确保无负值
                
                # 绘制主线
                ax.plot(x_smooth, y_smooth, color=color, linewidth=0.8, zorder=3)
                
                # 绘制 8 层渐变填充
                for i in range(1, 9):
                    ax.fill_between(x_smooth, 0, y_smooth, color=color, 
                                   alpha=0.08 * (i / 8), linewidth=0, zorder=2)

        # 细节美化
        ax.set_title(country, fontsize=7, fontweight='bold', pad=4)
        ax.set_xlabel('Solar Radiation', fontsize=5)
        ax.set_ylabel('Capacity', fontsize=5)
        
        # 移除上方和右侧边框
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 调整刻度
        ax.tick_params(axis='both', which='major', labelsize=5, length=2, pad=1)
        
        # 保存文件 (PDF 矢量格式最适合后期拼接)
        file_name = f"{country}_distribution.pdf"
        save_path = os.path.join(output_dir, file_name)
        plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=True)
        plt.close()
        print(f"已导出: {file_name}")

if __name__ == "__main__":
    # 请确保路径正确
    EXCEL_FILE = r"Fig2\excel\SolarDistributed.xlsx"
    export_distribution_plots(EXCEL_FILE)