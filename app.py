
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# ลิงก์ดึงข้อมูล CSV ของชีท Master 
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv"

try:
    # อ่านข้อมูลสดจากตาราง
    df_raw = pd.read_csv(sheet_url, header=None)
    
    if df_raw.shape[1] == 1:
        df_raw = df_raw[0].str.split(',', expand=True)
        
    start_idx = 0
    for idx in range(len(df_raw)):
        try:
            float(df_raw.iloc[idx, 2])
            start_idx = idx
            break
        except:
            continue
            
    df_raw = df_raw.iloc[start_idx:].reset_index(drop=True)

    # ประกอบร่างสร้างตารางใหม่ (A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7)
    df = pd.DataFrame()
    df['Date'] = df_raw[0].astype(str)
    df['TimeZoneForex'] = df_raw[1].astype(str)
    df['Open'] = pd.to_numeric(df_raw[2], errors='coerce')
    df['High'] = pd.to_numeric(df_raw[3], errors='coerce')
    df['Low'] = pd.to_numeric(df_raw[4], errors='coerce')
    df['Close'] = pd.to_numeric(df_raw[5], errors='coerce')
    df['Volume'] = df_raw[6].astype(str)
    df['TimeZoneThai'] = df_raw[7].astype(str)
    
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. ลоจิกคำนวณเป้าหมาย 100 จุดจากราคา Open
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_p = df.loc[i, 'Open']
        h_time, l_time = "-", "-"
        
        for j in range(i, len(df)):
            pts_high = (df.loc[j, 'High'] - open_p) * 100000
            pts_low = (open_p - df.loc[j, 'Low']) * 100000
            
            if h_time == "-" and pts_high >= 100:
                h_time = df.loc[j, 'TimeZoneThai']
            if l_time == "-" and pts_low >= 100:
                l_time = df.loc[j, 'TimeZoneThai']
            if h_time != "-" and l_time != "-":
                break
                
        high_targets.append(h_time)
        low_targets.append(l_time)

    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 3. จัดสัดส่วนแสดงผลแดชบอร์ด
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("### 📈 กราฟแท่งเทียน (คลิกที่แท่งเพื่อดูเวลาชนะ 100 จุด)")
        
        # ปรับแต่งข้อความป๊อปอัปตอนชี้หรือคลิกตามเงื่อนไขของคุณวีรพันธ์
        hover_texts = []
        for idx, row in df.iterrows():
            # แปลงค่าถ้าไม่ชนะ (-) ให้กลายเป็น No ตามบรีฟ
            buy_result = f"Buy = {row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "Buy = No"
            sell_result = f"Sell = {row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "Sell = No"
            
            text = (
                f"⏰ แท่งเวลาไทย: {row['TimeZoneThai']}<br>"
                f"--------------------<br>"
                f"🎯 {buy_result}<br>"
                f"🎯 {sell_result}<br>"
                f"--------------------<br>"
                f"🟢 Open: {row['Open']} | 🔴 Close: {row['Close']}<br>"
                f"🔼 High: {row['High']} | 🔽 Low: {row['Low']}"
            )
            hover_texts.append(text)

        fig = go.Figure(data=[go.Candlestick(
            x=df['TimeZoneThai'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name="Candle",
            text=hover_texts, hoverinfo='text' # สั่งให้โชว์กล่องข้อความที่เราแต่งเอง
        )])
        
        fig.update_layout(
            xaxis_title="เวลาไทย (TimeZoneThai)",
            yaxis_title="ราคา (Price)",
            xaxis_rangeslider_visible=False, 
            height=600, 
            template="plotly_dark",
            hovermode='x unified',
            clickmode='event+select'
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        show_cols = ['TimeZoneThai', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']
        st.dataframe(df[show_cols], height=550, use_container_width=True)

    st.success("✨ อัปเดตระบบมาร์คเวลาเป้าหมาย 100 จุดบนกราฟแท่งเทียนเรียบร้อยครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
