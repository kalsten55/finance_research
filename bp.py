import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. 代理配置 (保持你原有的设置)
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

ticker = "^GSPC"


def analyze_sp500_interactive():
    print("-" * 40)
    print("🚀 标普500 (S&P 500) 趋势分析启动")
    print("-" * 40)

    # --- 新增：让用户选择时间周期 ---
    print("请输入你想查看的时间周期：")
    print("  1mo  = 过去1个月")
    print("  6mo  = 过去6个月")
    print("  1y   = 过去1年")
    print("  5y   = 过去5年")
    print("  10y  = 过去10年")
    print("  ytd  = 今年至今 (Year To Date)")
    print("  max  = 所有历史数据")

    # 获取用户输入，如果用户直接回车，默认使用 '1y'
    user_period = input("👉 请输入代码 (默认 1y): ").strip()
    if not user_period:
        user_period = "1y"

    print(f"\n正在获取 {ticker} 过去 [{user_period}] 的数据，请稍候...")

    # 2. 获取数据与清洗
    # 使用 period 参数直接下载，无需手动计算 start_date
    try:
        data = yf.download(ticker, period=user_period, progress=False)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return

    # 检查数据是否为空
    if data.empty:
        print("❌ 未获取到数据，请检查网络或输入的时间周期代码是否正确。")
        return

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 3. 计算指标
    # 注意：如果选择的时间太短（如1mo），MA200 将无法计算（显示为NaN），这是正常的数学逻辑
    data['MA200'] = data['Close'].rolling(window=200).mean()
    data['Peak'] = data['Close'].cummax()
    data['Drawdown'] = (data['Close'] - data['Peak']) / data['Peak']
    data['Bias'] = (data['Close'] - data['MA200']) / data['MA200']  # 乖离率

    # 4. 获取最新数值
    current_price = data['Close'].iloc[-1].item()

    # 处理可能为空的 MA200 (防止报错)
    if pd.notna(data['MA200'].iloc[-1]):
        ma200_price = data['MA200'].iloc[-1].item()
        current_bias = data['Bias'].iloc[-1].item()
        ma_status = "有效"
    else:
        ma200_price = 0
        current_bias = 0
        ma_status = "无效 (数据量不足200天)"

    current_drawdown = data['Drawdown'].iloc[-1].item()

    # 5. 打印报告
    print("-" * 40)
    print(f"📊 标普500 市场简报 [{datetime.now().strftime('%Y-%m-%d')}]")
    print(f"观察周期: {user_period}")
    print("-" * 40)
    print(f"当前指数点位: {current_price:,.2f}")

    if ma_status == "有效":
        print(f"200日均线   : {ma200_price:,.2f}")
        print(f"当前乖离率  : {current_bias:.2%}")

        if current_price > ma200_price:
            print("📈 趋势判断: 位于牛熊线【上方】，长期趋势向上。")
        else:
            print("📉 趋势判断: 位于牛熊线【下方】，市场处于弱势区间。")

        if current_bias > 0.15:
            print("⚠️ 风险提示: 乖离率过大，市场可能短期过热。")
    else:
        print("⚠️ 提示: 选定的时间范围内数据不足200天，无法计算200日均线和乖离率。")

    print(f"当前回撤幅度: {current_drawdown:.2%}")

    if current_drawdown < -0.20:
        print("⚠️ 机会提示: 市场已下跌超过 20% (技术性熊市)！")
    elif current_drawdown < -0.10:
        print("👀 机会提示: 市场回调超过 10%，适合保持定投。")
    else:
        print("☕️ 心态提示: 市场波动正常，安心持有。")

    # ==========================================
    # 6. Plotly 交互式绘图部分
    # ==========================================
    print("-" * 40)
    print("📊 正在生成交互式图表...")

    fig = go.Figure()

    # --- 添加收盘价曲线 ---
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='S&P 500 Price',
        line=dict(color='#00BFFF', width=2),
        customdata=data['Bias'],
        hovertemplate=(
            '<b>日期</b>: %{x|%Y-%m-%d}<br>'
            '<b>价格</b>: $%{y:,.2f}<br>'
            '<b>乖离率</b>: %{customdata:.2%}<extra></extra>'
        )
    ))

    # --- 添加 200日均线 (只有当数据足够时才显示) ---
    if ma_status == "有效":
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA200'],
            mode='lines',
            name='200-Day MA (Bull/Bear Line)',
            line=dict(color='orange', width=2, dash='dash'),
            hovertemplate='<b>均线成本</b>: $%{y:,.2f}<extra></extra>'
        ))

    # --- 配置布局 ---
    fig.update_layout(
        title=dict(
            text=f'S&P 500 趋势分析 ({user_period})',
            font=dict(size=20)
        ),
        xaxis_title='Date',
        yaxis_title='Price (USD)',
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

    print("✅ 窗口已打开。请在浏览器中查看图表。")
    fig.show()


if __name__ == "__main__":
    # 在 PyCharm 中运行时，请确保在下方的 Run 窗口输入内容
    try:
        analyze_sp500_interactive()
    except KeyboardInterrupt:
        print("\n程序已取消。")
    except Exception as e:
        print(f"运行出错: {e}")