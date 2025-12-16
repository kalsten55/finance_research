import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 1. 代理配置
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"


def get_user_input():
    print("-" * 40)
    print("🚀 加密货币 (Crypto) 市场深度分析")
    print("-" * 40)
    print("请输入分析周期：")
    print("  1y   = 过去1年 (适合短线)")
    print("  4y   = 过去4年 (包含一个完整减半周期，推荐)")
    print("  ytd  = 今年至今")
    print("  max  = 所有历史数据")

    period = input("👉 请输入代码 (默认 4y): ").strip()
    if not period:
        period = "4y"
    return period


def analyze_single_crypto(ticker, name, color_code, period):
    print(f"\n📡 正在获取 {name} ({ticker}) 数据...")

    # --- 2. 动态阈值配置 (Domain Knowledge) ---
    # 针对不同币种设定不同的"恐慌线"
    if "BTC" in ticker:
        crash_threshold = -0.50  # 比特币: 跌50%算大机会
        bias_threshold = 0.60  # 比特币: 乖离率60%算过热
        ma_color = 'orange'
    else:
        crash_threshold = -0.60  # 以太坊: 波动更大，跌60%才算大机会
        bias_threshold = 0.80  # 以太坊: 乖离率80%才算过热
        ma_color = 'cyan'  # 均线颜色区分

    # --- 3. 获取数据 ---
    try:
        data = yf.download(ticker, period=period, progress=False)
    except Exception as e:
        print(f"❌ {name} 下载失败: {e}")
        return

    if data.empty:
        print(f"❌ {name} 数据为空。")
        return

    # 清洗数据
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # --- 4. 计算指标 ---
    data['MA200'] = data['Close'].rolling(window=200).mean()
    data['Peak'] = data['Close'].cummax()
    data['Drawdown'] = (data['Close'] - data['Peak']) / data['Peak']
    data['Bias'] = (data['Close'] - data['MA200']) / data['MA200']

    # 获取最新数据
    current_price = data['Close'].iloc[-1].item()
    current_drawdown = data['Drawdown'].iloc[-1].item()

    # 检查 MA200 是否有效
    if pd.notna(data['MA200'].iloc[-1]):
        ma200_price = data['MA200'].iloc[-1].item()
        current_bias = data['Bias'].iloc[-1].item()
        ma_status = "有效"
    else:
        ma200_price = 0
        current_bias = 0
        ma_status = "无效"

    # --- 5. 打印分析报告 ---
    print("-" * 40)
    print(f"💎 {name} 分析报告 [{datetime.now().strftime('%Y-%m-%d')}]")
    print("-" * 40)
    print(f"当前价格   : ${current_price:,.2f}")

    if ma_status == "有效":
        print(f"200日均线  : ${ma200_price:,.2f}")
        print(f"当前乖离率 : {current_bias:.2%} (警戒线: {bias_threshold:.0%})")

        if current_price > ma200_price:
            print("📈 长期趋势 : 牛市 (价格 > 200日均线)")
        else:
            print("🥶 长期趋势 : 熊市 (价格 < 200日均线)")

        if current_bias > bias_threshold:
            print("⚠️ 风险警告 : 市场极度贪婪，随时可能回调，切勿梭哈！")
    else:
        print("⚠️ 提示: 数据量不足，无法计算200日均线。")

    print(f"当前回撤   : {current_drawdown:.2%} (机会线: {crash_threshold:.0%})")

    # 投资建议逻辑
    if current_drawdown < crash_threshold:
        print(f"🚨 机会提示 : 史诗级大底 (跌破 {crash_threshold:.0%})！建议加大定投！")
    elif current_drawdown < (crash_threshold / 1.5):
        print("👀 机会提示 : 深度回调，适合分批买入。")
    else:
        print("☕️ 操作建议 : 正常波动区间，保持定投节奏。")

    # --- 6. Plotly 交互式绘图 ---
    fig = go.Figure()

    # 价格线
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name=f'{name} Price',
        line=dict(color=color_code, width=2),
        customdata=data['Bias'],  # 传入乖离率数据供显示
        hovertemplate=(
            '<b>日期</b>: %{x|%Y-%m-%d}<br>'
            '<b>价格</b>: $%{y:,.2f}<br>'
            '<b>乖离率</b>: %{customdata:.2%}<extra></extra>'
        )
    ))

    # 200日均线
    if ma_status == "有效":
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['MA200'],
            mode='lines',
            name='200-Day Bull/Bear Line',
            line=dict(color=ma_color, width=2, dash='dash'),
            hovertemplate='<b>均线成本</b>: $%{y:,.2f}<extra></extra>'
        ))

    # 布局设置
    fig.update_layout(
        title=dict(
            text=f'{name} 趋势分析 ({period})',
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
        )
    )

    print(f"✅ {name} 图表已生成 (浏览器标签页)。")
    fig.show()


def main():
    # 获取用户输入的时间周期
    target_period = get_user_input()

    # 1. 分析比特币 (BTC) - 橙色
    analyze_single_crypto(
        ticker="BTC-USD",
        name="Bitcoin (BTC)",
        color_code="#FFA500",
        period=target_period
    )

    # 2. 分析以太坊 (ETH) - 蓝紫色
    analyze_single_crypto(
        ticker="ETH-USD",
        name="Ethereum (ETH)",
        color_code="#6A5ACD",  # SlateBlue
        period=target_period
    )

    print("\n🎉 所有分析已完成，请查看浏览器。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已取消。")
    except Exception as e:
        print(f"运行出错: {e}")