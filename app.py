import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# ลิงก์ดึงข้อมูล CSV ของชีท Master
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

try:
    # อ่านข้อมูลสดและแก้ปัญหาเครื่องหมายคั่นฟันหนู (Quote) จาก Google Sheet ให้แตกตัวแยกเป็นคอลัมน์ A-H อัตโนมัติ
    raw_data = pd.read_csv(sheet_url, header=None, quotechar='"')
    
    # กรณีข้อมูลถูกมองเป็นคอลัมน์เดียวพืด ให้สั่งแยกคอลัมน์แยกย่อยทันที
    if raw_data.shape[1] == 1:
        raw_data = raw_data[0].str.split(',', expand=True)
        
    # ตัดแถวหัวตารางตัวหนังสือทิ้งไปหากปนมาในแถวแรก
    try:
        float(raw_data.iloc[0, 2])
    except:
        raw_data = raw_data.iloc[1:].reset_index(drop=True)

    # ดึงค่าตามลำดับคอลัมน์ A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7
    df = pd.DataFrame()
    df['Date'] = raw_data[0].astype(str)
    df['TimeZoneForex'] = raw_data[1].astype(str)
    df['Open'] = pd.to_numeric(raw_data[2], errors='coerce')
    df['High'] = pd.to_numeric(raw_data[3], errors='coerce')
    df['Low'] = pd.to_numeric(raw_data[4], errors='coerce')
    df['Close'] = pd.to_numeric(raw_data[5], errors='coerce')
    df['Volume'] = raw_data[6].astype(str)
    df['TimeZoneThai'] = raw_data[7].astype(str)
    
    # ลบแถวเสียหรือค่าว่างทิ้ง
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. คำนวณหาเป้าหมาย 100 จุดสะสมไปข้างหน้า (สูตรคูณ 100,000)
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

    # 3. แสดงผลหน้าจอแยกซ้าย-ขวา
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("### 📈 กราฟแท่งเทียน (Candlestick Chart)")
        fig = go.Figure(data=[go.Candlestick(
            x=df['TimeZoneThai'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name="Candle"
        )])
        fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        show_cols = ['TimeZoneThai', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']
        st.dataframe(df[show_cols], height=500, use_container_width=True)

    st.success("✨ เชื่อมต่อ Google Sheet แบบเรียงคอลัมน์สดสำเร็จ! ต่อจากนี้ข้อมูลจะอัปเดตอัตโนมัติครับ")

except Exception as err:
    st.error(f"ระบบกำลังรอการซิงค์ข้อมูลจาก Google Sheet: {err}")

