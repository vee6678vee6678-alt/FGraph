import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มพื้นที่จอ (เหมาะกับมือถือมาก)
st.set_page_config(layout="wide", page_title="Forex Live Chart")

st.title("📊 Forex Candlestick & Target 100 Points")
st.subheader("ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ (เน้นใช้งานบนมือถือ)")

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

    # 3. จัดการแสดงผลกราฟเดี่ยวๆ เต็มจอ (เอาตารางฝั่งขวาออกแล้ว)
    st.markdown("### 📈 กราฟแท่งเทียน (จิ้มแท่งเทียนเพื่อเปิด/ปิดกล่องสรุปเวลาชนะ)")
    
    # ปรับแต่งชุดข้อความป๊อปอัปเมื่อชี้หรือกดเลือก
    hover_texts = []
    for idx, row in df.iterrows():
        buy_result = f"Buy = {row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "Buy = No"
        sell_result = f"Sell = {row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "Sell = No"
        
        text = (
            f"⏰ เวลาไทย: {row['TimeZoneThai']}<br>"
            f"🎯 {buy_result}<br>"
            f"🎯 {sell_result}<br>"
            f"🟢 O: {row['Open']} | 🔴 C: {row['Close']}"
        )
        hover_texts.append(text)

    # วาดกราฟแท่งเทียน
    fig = go.Figure(data=[go.Candlestick(
        x=df['TimeZoneThai'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name="Candle",
        text=hover_texts, hoverinfo='text'
    )])
    
    # ปรับแต่งระบบการคลิกและเครื่องมือให้เหมาะกับหน้าจอมือถือ
    fig.update_layout(
        xaxis_title="เวลาไทย (TimeZoneThai)",
        yaxis_title="ราคา (Price)",
        xaxis_rangeslider_visible=False, 
        height=650, # ปรับความสูงกราฟให้พอดีกับหน้าจอมือถือแนวตั้ง
        template="plotly_dark",
        hovermode='closest', # ให้โชว์ดีเทลเฉพาะแท่งที่เมาส์จิ้มตรงๆ
        clickmode='event+select', # คลิกแล้วล็อกค้างไว้ได้
        margin=dict(l=10, r=10, t=20, b=20) # บีบขอบซ้ายขวาให้จอกราฟกว้างที่สุดบนมือถือ
    )
    
    # ปรับปรุงแถบเครื่องมือด่วนด้านบนกราฟ (สั่งโชว์ปุ่มกากบาทเพื่อปิดกล่องข้อความได้อิสระ)
    fig.update_traces(
        selectedpoints=None,
        selector=dict(type='candlestick')
    )
    
    # เปิดการแสดงผลกราฟแบบ Responsive ขยายตามจอมือถืออัตโนมัติ
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']})

    st.success("✨ ปรับแต่งโหมดมือถือ กราฟเต็มจอเรียบร้อยแล้วครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
