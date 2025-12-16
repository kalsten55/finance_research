import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from prophet import Prophet
from prophet.plot import plot_plotly
import platform

# --- 1. 基础配置 ---
st.set_page_config(page_title="金融指挥中心 Pro", layout="wide", page_icon="🏦")

# 智能代理配置
# 只有检测到是 macOS 系统 (你的电脑) 时才开启代理
# 云端通常是 Linux 系统，这行代码会自动跳过，不会报错
if platform.system() == "Darwin":
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    print("🍎 检测到 macOS，已开启本地代理")
else:
    print("☁️ 检测到云端环境，直连模式")


# --- 2. 核心函数: 计算技术指标 ---
def add_technical_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['MA20'] + (df['STD20'] * 2)
    df['Lower_Band'] = df['MA20'] - (df['STD20'] * 2)

    # MA200
    df['MA200'] = df['Close'].rolling(window=200).mean()
    return df


# --- 3. 初始化 Session State ---
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = pd.DataFrame(
        columns=["Ticker", "Quantity", "Unit_Cost_USD", "Date", "Original_Currency"])
    # 预设数据演示
    initial_data = pd.DataFrame([
        {"Ticker": "BTC-USD", "Quantity": 0.5, "Unit_Cost_USD": 40000.0, "Date": "2023-01-01",
         "Original_Currency": "USD"}
    ])
    st.session_state.portfolio_data = pd.concat([st.session_state.portfolio_data, initial_data], ignore_index=True)

# --- 4. 侧边栏导航 ---
st.sidebar.title("🎛️ 全能控制台")
menu = st.sidebar.radio("功能导航",
                        ["个股/加密货币分析", "资产对比 (PK模式)", "💰 我的实盘账户(汇率版)", "🔥 资产相关性热力图","🔮 AI 趋势预测 (Prophet)"])

# =========================================================
# 模块一：个股分析
# =========================================================
if menu == "个股/加密货币分析":
    st.title("📈 深度技术分析")
    ticker = st.sidebar.text_input("输入代码", "BTC-USD").upper()
    period = st.sidebar.selectbox("周期", ["6mo", "1y", "3y", "5y"], index=1)

    st.sidebar.subheader("图表设置")
    show_ma200 = st.sidebar.checkbox("MA200 (牛熊线)", True)
    show_boll = st.sidebar.checkbox("布林带", False)
    sub_chart = st.sidebar.radio("副图指标", ["无", "RSI", "MACD"])

    if st.sidebar.button("开始分析", type="primary"):
        with st.spinner('正在分析数据...'):
            try:
                df = yf.download(ticker, period=period, progress=False)
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

                if df.empty:
                    st.error("❌ 无数据，请检查代码拼写。")
                else:
                    df = add_technical_indicators(df)
                    curr = df['Close'].iloc[-1].item()
                    rsi = df['RSI'].iloc[-1].item() if pd.notna(df['RSI'].iloc[-1]) else 50

                    # 顶部指标
                    c1, c2, c3 = st.columns(3)
                    c1.metric("当前价格", f"${curr:,.2f}")

                    rsi_state = "正常"
                    if rsi > 70:
                        rsi_state = "🔥 超买"
                    elif rsi < 30:
                        rsi_state = "🧊 超卖"
                    c2.metric("RSI (14)", f"{rsi:.1f}", rsi_state)

                    if pd.notna(df['MA200'].iloc[-1]):
                        bias = (curr - df['MA200'].iloc[-1].item()) / df['MA200'].iloc[-1].item()
                        c3.metric("乖离率", f"{bias:+.2%}")

                    # 绘图
                    rows = 2 if sub_chart != "无" else 1
                    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                                        row_heights=[0.7, 0.3] if rows == 2 else [1])

                    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Price', line=dict(color='#00BFFF')),
                                  row=1, col=1)
                    if show_ma200: fig.add_trace(
                        go.Scatter(x=df.index, y=df['MA200'], name='MA200', line=dict(color='orange', dash='dash')),
                        row=1, col=1)
                    if show_boll:
                        fig.add_trace(go.Scatter(x=df.index, y=df['Upper_Band'], showlegend=False, line=dict(width=0)),
                                      row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['Lower_Band'], fill='tonexty',
                                                 fillcolor='rgba(255,255,255,0.1)', showlegend=False,
                                                 line=dict(width=0)), row=1, col=1)

                    if sub_chart == "RSI":
                        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=2,
                                      col=1)
                        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
                    elif sub_chart == "MACD":
                        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='DIF', line=dict(color='yellow')),
                                      row=2, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], name='DEA', line=dict(color='cyan')),
                                      row=2, col=1)
                        fig.add_trace(go.Bar(x=df.index, y=(df['MACD'] - df['Signal_Line']) * 2, name='Hist'), row=2,
                                      col=1)

                    fig.update_layout(height=600, template="plotly_dark", hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(str(e))

# =========================================================
# 模块二：资产对比
# =========================================================
elif menu == "资产对比 (PK模式)":
    st.title("⚔️ 资产对比")
    assets = st.sidebar.text_area("输入代码 (逗号分隔)", "BTC-USD, ^GSPC, NVDA, GLD")
    if st.sidebar.button("开始PK"):
        try:
            ts = [x.strip() for x in assets.split(',')]
            data = yf.download(ts, period="1y", group_by='ticker', progress=False)
            df_c = pd.DataFrame()
            for t in ts:
                if isinstance(data.columns, pd.MultiIndex):
                    # 尝试取 Close，若无取 Adj Close
                    df_c[t] = data[t]['Close']
                elif len(ts) == 1:
                    df_c[ts[0]] = data['Close']

            # 归一化并绘图
            st.line_chart((df_c.ffill().bfill() / df_c.ffill().bfill().iloc[0]) - 1)
        except Exception as e:
            st.error(f"数据错误: {e}")

# =========================================================
# 模块三：我的实盘账户 (V5.0 完整修复版)
# =========================================================
elif menu == "💰 我的实盘账户(汇率版)":
    st.title("🌏 智能资产管家 (CNY/USD)")

    # --- 智能录入 ---
    with st.expander("➕ 新增交易 (智能换汇)", expanded=True):
        with st.form("add_trade_form"):
            c1, c2 = st.columns(2)
            new_ticker = c1.text_input("代码", "NVDA").upper()
            new_date = c2.date_input("日期", datetime.now())
            c3, c4 = st.columns(2)
            currency_type = c3.radio("币种", ["USD", "CNY"], horizontal=True)
            new_amount = c4.number_input("总金额", 1.0, value=10000.0)

            if st.form_submit_button("🚀 录入"):
                with st.spinner(f"正在回溯历史数据..."):
                    try:
                        start_str = new_date.strftime('%Y-%m-%d')
                        end_str = (new_date + timedelta(days=5)).strftime('%Y-%m-%d')

                        # 获取资产价格
                        asset_data = yf.download(new_ticker, start=start_str, end=end_str, progress=False)
                        if isinstance(asset_data.columns,
                                      pd.MultiIndex): asset_data.columns = asset_data.columns.get_level_values(0)

                        if asset_data.empty:
                            st.error(f"❌ 无法获取 {new_ticker} 数据")
                        else:
                            execution_price = asset_data['Close'].iloc[0].item()
                            execution_date = asset_data.index[0].strftime('%Y-%m-%d')

                            # 汇率处理
                            final_usd_amount = new_amount
                            if currency_type == "CNY":
                                fx_data = yf.download("CNY=X", start=start_str, end=end_str, progress=False)
                                if isinstance(fx_data.columns,
                                              pd.MultiIndex): fx_data.columns = fx_data.columns.get_level_values(0)
                                fx_rate = fx_data['Close'].iloc[0].item() if not fx_data.empty else 7.2
                                final_usd_amount = new_amount / fx_rate

                            quantity = final_usd_amount / execution_price

                            new_row = pd.DataFrame([{
                                "Ticker": new_ticker, "Quantity": quantity,
                                "Unit_Cost_USD": execution_price, "Date": execution_date,
                                "Original_Currency": currency_type
                            }])
                            st.session_state.portfolio_data = pd.concat([st.session_state.portfolio_data, new_row],
                                                                        ignore_index=True)
                            st.success(f"✅ 录入成功！持有 {quantity:.4f} 股/币")
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")

    # --- 持仓表格 ---
    st.subheader("📋 持仓清单 (USD本位)")
    edited_df = st.data_editor(st.session_state.portfolio_data, num_rows="dynamic", use_container_width=True,
                               key="portfolio_editor_final")

    # --- 计算市值 (含 Weekend Bug 修复) ---
    if st.button("🔄 刷新最新市值"):
        if edited_df.empty:
            st.warning("空空如也")
        else:
            with st.spinner('连接华尔街...'):
                try:
                    calc_df = edited_df.copy()
                    tickers = calc_df["Ticker"].unique().tolist()
                    live_data = yf.download(tickers, period="5d", group_by='ticker', progress=False)
                    current_prices = {}

                    for t in tickers:
                        try:
                            # 提取并清洗空值
                            if isinstance(live_data.columns, pd.MultiIndex):
                                series = live_data[t]['Close']
                            else:
                                series = live_data['Close']
                            series = series.dropna()  # 关键修复
                            current_prices[t] = series.iloc[-1].item() if not series.empty else 0
                        except:
                            current_prices[t] = 0

                    calc_df["Current_Price"] = calc_df["Ticker"].map(current_prices)
                    calc_df["Market_Value"] = calc_df["Quantity"] * calc_df["Current_Price"]
                    calc_df["PnL"] = (calc_df["Current_Price"] - calc_df["Unit_Cost_USD"]) * calc_df["Quantity"]

                    total_pnl = calc_df["PnL"].sum()

                    c1, c2 = st.columns(2)
                    c1.metric("💰 总市值 (USD)", f"${calc_df['Market_Value'].sum():,.2f}")
                    c2.metric("💸 总盈亏 (USD)", f"${total_pnl:+,.2f}")

                    col_pie, col_bar = st.columns(2)
                    with col_pie:
                        st.plotly_chart(px.pie(calc_df, values='Market_Value', names='Ticker', title='仓位分布'),
                                        use_container_width=True)
                    with col_bar:
                        calc_df['Color'] = calc_df['PnL'].apply(lambda x: '#00FF00' if x >= 0 else '#FF4500')
                        st.plotly_chart(
                            go.Figure(go.Bar(x=calc_df['Ticker'], y=calc_df['PnL'], marker_color=calc_df['Color'])),
                            use_container_width=True)

                except Exception as e:
                    st.error(f"计算出错: {e}")

# =========================================================
# 模块四：资产相关性热力图 (V6.0 精致版)
# =========================================================
elif menu == "🔥 资产相关性热力图":
    st.title("🔥 资产相关性分析")
    st.info("💡 寻找最佳对冲资产：越红越危险(同步)，越蓝越安全(互补)。")

    st.sidebar.subheader("设置")
    default_symbols = "BTC-USD, ETH-USD, NVDA, TSLA, GLD, ^GSPC"
    user_symbols = st.sidebar.text_area("资产代码", value=default_symbols, height=100)
    lookback = st.sidebar.selectbox("回测时间", ["6mo", "1y", "3y"], index=1)

    if st.button("🔍 计算矩阵", type="primary"):
        tickers = [x.strip().upper() for x in user_symbols.split(',')]
        with st.spinner('清洗数据中...'):
            try:
                data = yf.download(tickers, period=lookback, progress=False, auto_adjust=False)
                df_close = pd.DataFrame()

                # 增强型数据提取
                for t in tickers:
                    try:
                        if isinstance(data.columns, pd.MultiIndex):
                            if 'Adj Close' in data.columns.get_level_values(0) and t in data['Adj Close']:
                                series = data['Adj Close'][t]
                            elif 'Close' in data.columns.get_level_values(0) and t in data['Close']:
                                series = data['Close'][t]
                            else:
                                continue
                        else:
                            series = data['Adj Close'] if 'Adj Close' in data.columns else data['Close']
                        df_close[t] = series
                    except:
                        pass

                df_close = df_close.dropna(axis=0)  # 去除空值行

                if df_close.empty:
                    st.error("数据不足，请尝试使用 ETF (如 GLD) 代替期货。")
                else:
                    corr_matrix = df_close.pct_change().dropna().corr()

                    st.subheader(f"📊 Pearson 相关系数矩阵 ({lookback})")

                    # === 布局优化：左图右白 ===
                    c_chart, c_none = st.columns([3, 2])
                    with c_chart:
                        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)  # 尺寸控制
                        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1,
                                    square=True, linewidths=.5, fmt=".2f", ax=ax, cbar_kws={"shrink": 0.7})
                        plt.xticks(fontsize=8);
                        plt.yticks(fontsize=8)
                        st.pyplot(fig, use_container_width=True)

                    # 智能解读
                    st.markdown("---")
                    corr_unstack = corr_matrix.unstack().sort_values(ascending=False)
                    top_corr = corr_unstack[corr_unstack < 0.9999].head(1)
                    bot_corr = corr_unstack.tail(1)

                    if not top_corr.empty: st.warning(
                        f"⚠️ 最高同步: {top_corr.index[0]} (Coef: {top_corr.values[0]:.2f})")
                    if not bot_corr.empty: st.success(
                        f"🛡️ 最佳对冲: {bot_corr.index[0]} (Coef: {bot_corr.values[0]:.2f})")

            except Exception as e:
                st.error(f"Error: {e}")

# =========================================================
# 🆕 模块五：AI 趋势预测 (Machine Learning)
# =========================================================
elif menu == "🔮 AI 趋势预测 (Prophet)":
    st.title("🔮 AI 价格趋势预测 (Prophet)")
    st.info(
        "💡 基于 Meta (Facebook) 开源的 Prophet 模型。它不仅看趋势，还能捕捉'季节性'规律（比如比特币周末由于美股休市可能出现的独立行情）。")

    # 1. 侧边栏设置
    st.sidebar.subheader("模型参数")
    ticker = st.sidebar.text_input("预测资产", "BTC-USD").upper()

    # 训练数据长度：数据越多，模型“见多识广”，但太久远的数据可能对现在没参考意义
    train_years = st.sidebar.slider("训练数据 (年)", 1, 5, 2)

    # 预测未来多久
    predict_days = st.sidebar.slider("预测未来 (天)", 30, 365, 90)

    if st.button("🚀 启动 AI 预测", type="primary"):
        with st.spinner(f'正在训练 AI 模型 ({ticker})... 请稍候，这也需要消耗算力'):
            try:
                # 2. 获取训练数据
                # 必须足够长，Prophet 才能学到规律
                data = yf.download(ticker, period=f"{train_years}y", progress=False)

                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                if data.empty:
                    st.error("❌ 无法获取数据")
                else:
                    # 3. 数据预处理 (Prophet 的格式要求极其严格)
                    # 必须只有两列：'ds' (时间) 和 'y' (数值)
                    df_train = data.reset_index()[['Date', 'Close']]
                    df_train.columns = ['ds', 'y']

                    # ⚠️ 关键修复：去除时区信息 (tz-naive)，否则 Prophet 会报错
                    df_train['ds'] = df_train['ds'].dt.tz_localize(None)

                    # 4. 初始化并训练模型
                    # daily_seasonality=True 强制开启日线规律分析
                    model = Prophet(daily_seasonality=True)
                    model.fit(df_train)

                    # 5. 构建未来时间表
                    future = model.make_future_dataframe(periods=predict_days)

                    # 6. 进行预测
                    forecast = model.predict(future)

                    # 7. 可视化 (使用 Plotly 交互图)
                    st.subheader(f"📈 {ticker} 未来 {predict_days} 天走势预测")

                    # 绘制主图 (包含历史数据、拟合线、置信区间)
                    fig_main = plot_plotly(model, forecast)
                    fig_main.update_layout(
                        title=f"AI Prediction: {ticker}",
                        yaxis_title="Price",
                        xaxis_title="Date",
                        height=600,
                        template="plotly_dark"  # 保持你的深色风格
                    )
                    st.plotly_chart(fig_main, use_container_width=True)

                    # 8. 趋势分解 (Data Science 最有价值的部分)
                    st.markdown("---")
                    st.subheader("🔍 深度归因分析 (Model Components)")
                    st.caption("AI 发现了什么规律？")

                    # 获取组件数据
                    # 趋势项
                    fig_trend = go.Figure()
                    fig_trend.add_trace(
                        go.Scatter(x=forecast['ds'], y=forecast['trend'], mode='lines', name='总体趋势'))
                    fig_trend.update_layout(title="1. 总体长期趋势 (Trend)", height=300, template="plotly_dark")
                    st.plotly_chart(fig_trend, use_container_width=True)

                    # 周度规律 (Weekly Seasonality)
                    # 看看周几容易涨，周几容易跌
                    if 'weekly' in forecast.columns:
                        # 提取一周7天的数据
                        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                        # Prophet 的 weekly 数据是周期性的，我们需要取巧提取一下
                        # 这里我们简化处理，直接画出 forecast 里的最后 7 天的 weekly component 即可看出规律

                        # 为了准确展示“周几”，我们用 Prophet 内置的画图更方便，但为了交互性，我们手动画一个简单的
                        # 提取最近一周的 weekly component
                        weekly_df = forecast.tail(7).copy()
                        weekly_df['day_name'] = weekly_df['ds'].dt.day_name()

                        # 按周一到周日排序
                        weekly_df['day_index'] = weekly_df['ds'].dt.dayofweek
                        weekly_df = weekly_df.sort_values('day_index')

                        fig_week = go.Figure()
                        fig_week.add_trace(go.Bar(
                            x=weekly_df['day_name'],
                            y=weekly_df['weekly'],
                            marker_color=['green' if x > 0 else 'red' for x in weekly_df['weekly']]
                        ))
                        fig_week.update_layout(title="2. 周度效应 (Weekly Seasonality) - 周几适合买?", height=300,
                                               template="plotly_dark")
                        st.plotly_chart(fig_week, use_container_width=True)
                        st.info("👆 柱子向上(绿色)代表这天通常会上涨，向下(红色)代表通常会下跌。")

            except Exception as e:
                st.error(f"AI 预测模型崩溃了: {e}")