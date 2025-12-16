import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. 代理配置 (保持不变)
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 纳斯达克100指数 Ticker
ticker = "^NDX"


def analyze_nasdaq_interactive():
    print("-" * 40)
    print("🚀 纳斯达克 100 (Nasdaq-100) 科技股分析启动")
    print("-" * 40)

    # --- 新增：让用户选择时间周期 ---
    print("请输入你想查看的时间周期：")
    print("  1mo  = 过去1个月")
    print("  6mo  = 过去6个月")
    print("  1y   = 过去1年")
    print("  5y   = 过去5年 (推荐，看科技长牛)")
    print("  10y  = 过去10年")
    print("  ytd  = 今年至今")
    print("  max  = 所有历史数据")

    # 默认设为 1y，方便快速查看
    user_period = input("👉 请输入代码 (默认 1y): ").strip()
    if not user_period:
        user_period = "1y"

    print(f"\n正在获取 {ticker} 过去 [{user_period}] 的数据，请稍候...")

    # 2. 获取数据
    # 使用 period 参数直接下载
    try:
        data = yf.download(ticker, period=user_period, progress=False)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return

    if data.empty:
        print("❌ 未获取到数据，请检查网络或输入的时间周期代码是否正确。")
        return

    # 数据清洗
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 3. 计算指标
    data['MA200'] = data['Close'].rolling(window=200).mean()
    data['Peak'] = data['Close'].cummax()
    data['Drawdown'] = (data['Close'] - data['Peak']) / data['Peak']
    data['Bias'] = (data['Close'] - data['MA200']) / data['MA200']

    # 4. 获取最新数值
    current_price = data['Close'].iloc[-1].item()
    current_drawdown = data['Drawdown'].iloc[-1].item()

    # 处理 MA200 可能为空的情况 (当选择周期 < 200天时)
    if pd.notna(data['MA200'].iloc[-1]):
        ma200_price = data['MA200'].iloc[-1].item()
        current_bias = data['Bias'].iloc[-1].item()
        ma_status = "有效"
    else:
        ma200_price = 0
        current_bias = 0
        ma_status = "无效 (数据不足)"

    # 5. 打印报告 (保留了你的科技股专属话术)
    print("-" * 40)
    print(f"💻 纳斯达克 100 科技简报 [{datetime.now().strftime('%Y-%m-%d')}]")
    print(f"观察周期: {user_period}")
    print("-" * 40)
    print(f"当前指数点位: {current_price:,.2f}")

    if ma_status == "有效":
        print(f"200日均线   : {ma200_price:,.2f}")
        print(f"当前乖离率  : {current_bias:.2%}")

        if current_price > ma200_price:
            print("📈 趋势判断: 强势牛市 (科技股情绪高涨)")
        else:
            print("📉 趋势判断: 弱势区间 (均线下方)")

        # 乖离率阈值保持 20%
        if current_bias > 0.20:
            print("⚠️ 风险提示: 乖离率 > 20%，市场短期极度狂热，警惕回调！")
    else:
        print("⚠️ 提示: 数据不足200天，无法判断长期均线趋势。")

    print(f"当前回撤幅度: {current_drawdown:.2%}")

    # === 关键：针对纳斯达克调整了阈值 (保持不变) ===
    if current_drawdown < -0.30:
        print("💎 钻石手提示: 史诗级大坑 (跌超30%)！别人恐慌你贪婪，加大定投！")
    elif current_drawdown < -0.15:
        print("👀 机会提示: 像样的回调 (跌超15%)，适合分批买入。")
    else:
        print("☕️ 心态提示: 正常波动。科技股波动大，坐稳扶好。")

    # 6. Plotly 交互式绘图
    print("-" * 40)
    print("📊 正在生成交互式图表...")

    fig = go.Figure()

    # 纳斯达克曲线 (使用霓虹紫色)
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='Nasdaq-100',
        line=dict(color='#BD00FF', width=2),  # Neon Purple
        customdata=data['Bias'],
        hovertemplate=(
            '<b>日期</b>: %{x|%Y-%m-%d}<br>'
            '<b>点位</b>: %{y:,.0f}<br>'
            '<b>乖离率</b>: %{customdata:.2%}<extra></extra>'
        )
    ))

    # 200日均线 (只有有效时才画)
    if ma_status == "有效":
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA200'],
            mode='lines',
            name='200-Day MA',
            line=dict(color='#00FFCC', width=2, dash='dash'),  # Neon Cyan
            hovertemplate='<b>均线</b>: %{y:,.0f}<extra></extra>'
        ))

    fig.update_layout(
        title=dict(
            text=f'Nasdaq-100 科技股趋势分析 ({user_period})',
            font=dict(size=20)
        ),
        xaxis_title='Date',
        yaxis_title='Index Value',
        template='plotly_dark',  # 深色背景最适合科技股
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

    print("✅ 分析完成，窗口已打开。")
    fig.show()


if __name__ == "__main__":
    try:
        analyze_nasdaq_interactive()
    except KeyboardInterrupt:
        print("\n程序已取消")
    except Exception as e:
        print(f"运行出错: {e}")