import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. 代理配置
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"


def compare_crypto_stock_interactive():
    print("-" * 50)
    print("⚔️  资产大对决: 比特币 (BTC) vs 标普500 (S&P 500)")
    print("-" * 50)

    # --- 1. 用户选择时间周期 ---
    print("请输入对比的时间周期：")
    print("  1mo  = 过去1个月")
    print("  6mo  = 过去6个月")
    print("  1y   = 过去1年 (默认)")
    print("  3y   = 过去3年")
    print("  5y   = 过去5年")
    print("  ytd  = 今年至今")

    user_period = input("👉 请输入代码 (默认 1y): ").strip()
    if not user_period:
        user_period = "1y"

    print(f"\n正在下载数据 (周期: {user_period})...")

    # 定义要对比的资产
    tickers = ['BTC-USD', '^GSPC']

    # 映射名称，方便展示
    names = {
        'BTC-USD': 'Bitcoin (BTC)',
        '^GSPC': 'S&P 500'
    }

    # --- 2. 获取数据 ---
    try:
        # group_by='ticker' 让列结构更清晰
        data = yf.download(tickers, period=user_period, progress=False, group_by='ticker')
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return

    # --- 3. 数据清洗 (关键步骤) ---
    # 提取 Close 列。因为 group_by='ticker'，结构变成了 (Ticker, Close)
    # 我们需要重构 DataFrame，只保留收盘价
    df_close = pd.DataFrame()

    for t in tickers:
        # yfinance有时返回多级索引，有时返回单级，做个兼容
        try:
            if isinstance(data.columns, pd.MultiIndex):
                # 尝试获取对应 Ticker 的 Close 列
                df_close[t] = data[t]['Close']
            else:
                # 如果下载单个可能会结构不同，但这里下载了俩，通常是MultiIndex
                pass
        except KeyError:
            print(f"❌ 无法找到 {t} 的数据")
            return

    # 检查数据完整性
    if df_close.empty:
        print("❌ 数据为空，请检查网络。")
        return

    # 填充空值 (bfill/ffill)
    # 解释: 美股周末休市，BTC周末不休市。如果不填充，计算时会导致大量NaN。
    # 用前一天的价格填补当天的空缺 (ffill) 是最合理的做法。
    df_close = df_close.ffill().bfill()

    # --- 4. 归一化计算 (改为百分比收益) ---
    # 公式: (当前价格 - 初始价格) / 初始价格
    # 结果: 0.10 代表涨了 10%
    normalized_data = (df_close / df_close.iloc[0]) - 1

    # --- 5. 终端打印简报 ---
    btc_return = normalized_data['BTC-USD'].iloc[-1]
    sp500_return = normalized_data['^GSPC'].iloc[-1]

    print("-" * 50)
    print(f"📊 最终战绩汇报 ({user_period})")
    print("-" * 50)
    print(f"🟠 比特币 (BTC) 累计收益: {btc_return:+.2%}")
    print(f"🔵 标普500 (S&P) 累计收益: {sp500_return:+.2%}")
    print("-" * 50)

    if btc_return > sp500_return:
        diff = (btc_return - sp500_return) * 100
        print(f"🏆 胜者: 比特币 (领先 {diff:.2f} 个百分点)")
    else:
        diff = (sp500_return - btc_return) * 100
        print(f"🏆 胜者: 标普500 (领先 {diff:.2f} 个百分点)")
    print("-" * 50)

    # --- 6. Plotly 交互式绘图 ---
    print(f"📊 正在启动交互式图表...")

    fig = go.Figure()

    # 比特币曲线
    fig.add_trace(go.Scatter(
        x=normalized_data.index,
        y=normalized_data['BTC-USD'],
        mode='lines',
        name=names['BTC-USD'],
        line=dict(color='#FFA500', width=2),  # 橙色
        hovertemplate='<b>日期</b>: %{x|%Y-%m-%d}<br><b>收益</b>: %{y:.2%}<extra></extra>'
    ))

    # 标普500曲线
    fig.add_trace(go.Scatter(
        x=normalized_data.index,
        y=normalized_data['^GSPC'],
        mode='lines',
        name=names['^GSPC'],
        line=dict(color='#4169E1', width=2),  # 皇家蓝
        hovertemplate='<b>日期</b>: %{x|%Y-%m-%d}<br><b>收益</b>: %{y:.2%}<extra></extra>'
    ))

    # 添加一条 0% 的基准线 (盈亏平衡线)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="0% 起跑线")

    # 配置布局
    fig.update_layout(
        title=dict(
            text=f'Bitcoin vs S&P 500 累计收益率对比 ({user_period})',
            font=dict(size=20)
        ),
        xaxis_title='日期',
        yaxis_title='累计收益率 (%)',  # 改为百分比标题
        yaxis_tickformat='.0%',  # Y轴刻度显示为百分比
        template='plotly_dark',
        hovermode="x unified",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0.5)"
        ),
        dragmode='zoom'
    )

    print("✅ 窗口已打开。")
    fig.show()


if __name__ == "__main__":
    try:
        compare_crypto_stock_interactive()
    except KeyboardInterrupt:
        print("\n程序已取消。")
    except Exception as e:
        print(f"运行出错: {e}")