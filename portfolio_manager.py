import pandas as pd
import yfinance as yf
from pyxirr import xirr
from datetime import datetime
import requests

# --- 配置区域 ---
EXCEL_PATH = 'trade_log.xlsx'
BARK_KEY = "qCYBDbni3Wp4r3FjypKQEJ"  # 🔴 记得把这里换回你的 Key！


def get_realtime_price(ticker_list):
    """从雅虎财经批量获取最新价格 (带向前填充功能)"""
    print("正在获取实时价格...")
    try:
        # 获取过去 5 天的数据，避免周一早上拿不到数据
        data = yf.download(ticker_list, period="5d", progress=False)['Close']
        # 向前填充：如果今天没数据，就用昨天的
        data = data.ffill()
        # 返回最新的一行
        return data.iloc[-1]
    except Exception as e:
        print(f"获取价格失败: {e}")
        return None


def get_usd_cny_rate():
    """获取美元兑人民币汇率"""
    try:
        rate = yf.Ticker("CNY=X").history(period="1d")['Close'].iloc[-1]
        print(f"当前汇率: 1 USD = {rate:.4f} CNY")
        return rate
    except:
        return 7.25


def send_to_iphone(content, profit_money):
    """发送高级美化版通知 (Bark)"""
    url = "https://api.day.app/push"

    today_str = datetime.now().strftime('%m-%d')
    title = f"📅 投资日报 ({today_str})"

    # 根据是否赚钱切换图标
    if profit_money >= 0:
        icon_url = "https://cdn-icons-png.flaticon.com/512/3177/3177440.png"  # 红色钱袋
        group_name = "我的定投(赚钱中)"
    else:
        icon_url = "https://cdn-icons-png.flaticon.com/512/2567/2567520.png"  # 绿色折线
        group_name = "我的定投(蓄力中)"

    payload = {
        "device_key": BARK_KEY,
        "title": title,
        "body": content,
        "group": "长期定投监控",
        "icon": icon_url,
        "sound": "glass",
        "level": "active",
        "url": "https://finance.yahoo.com/quote/SPY",  # 点击跳转
        "isArchive": 1,
        "badge": 1
    }

    try:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        requests.post(url, json=payload, headers=headers)
        print("✅ 推送已发送！")
    except Exception as e:
        print(f"❌ 推送失败: {e}")


def calculate_portfolio():
    """核心计算逻辑"""
    df = pd.read_excel(EXCEL_PATH)
    rate = get_usd_cny_rate()
    tickers = df['Ticker'].unique().tolist()

    current_prices = get_realtime_price(tickers)

    total_invested = 0
    total_value_cny = 0

    xirr_dates = []
    xirr_amounts = []

    print("\n--- 持仓详情 ---")
    for ticker in tickers:
        record = df[df['Ticker'] == ticker]
        total_shares = record['Shares'].sum()
        invested_cny = record['Cost_CNY'].sum()

        # 容错处理：如果某个资产价格没取到，暂时用0代替，避免程序崩溃
        if ticker in current_prices:
            current_price = current_prices[ticker]
        else:
            current_price = 0

        current_val = total_shares * current_price * rate

        total_invested += invested_cny
        total_value_cny += current_val

        # 只有当投入大于0才计算收益率，避免除以0
        if invested_cny > 0:
            profit_rate = (current_val - invested_cny) / invested_cny * 100
        else:
            profit_rate = 0

        print(f"[{ticker}] 持仓: {total_shares:.4f} | 现值: ¥{current_val:.2f} | 收益率: {profit_rate:.2f}%")

        for _, row in record.iterrows():
            xirr_dates.append(row['Date'])
            xirr_amounts.append(-row['Cost_CNY'])

    xirr_dates.append(datetime.now())
    xirr_amounts.append(total_value_cny)

    total_profit_money = total_value_cny - total_invested
    if total_invested > 0:
        total_profit_rate = total_profit_money / total_invested * 100
    else:
        total_profit_rate = 0

    try:
        portfolio_xirr = xirr(xirr_dates, xirr_amounts) * 100
    except:
        portfolio_xirr = 0.0

    result_msg = (
        f"总投入: ¥{total_invested:.0f}\n"
        f"总市值: ¥{total_value_cny:.0f}\n"
        f"总浮盈: ¥{total_profit_money:.0f} ({total_profit_rate:.2f}%)\n"
        f"年化效率 (XIRR): {portfolio_xirr:.2f}%"
    )
    print(result_msg)

    # 返回两个值：文本消息 和 浮盈金额
    return result_msg, total_profit_money


# --- 主程序入口 ---
if __name__ == "__main__":
    msg, profit = calculate_portfolio()
    send_to_iphone(msg, profit)