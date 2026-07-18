import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# ลิงก์ดึงข้อมูล CSV ของชีท Master ต้นทางจริง
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

try:
    # โหลดตารางตรงๆ จาก Google Sheet และเคลียร์ spacebar ที่ชื่อคอลัมน์ออกทันที
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip().str.replace(' ', '')
    
    # แปลงข้อมูลราคาในตารางให้กลายเป็นตัวเลขทศนิยมเพื่อนำไปใช้ในการคำนวณสูตร
    df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
    df['High'] = pd.to_numeric(df['High'], errors='coerce')
    df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    # ลบแถวที่อาจเป็นค่าว่างออก ป้องกันตารางเออเร่อ
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. ลอจิกการคำนวณหาเวลาที่ชนเป้าหมาย 100 จุดจากราคา Open (สูตรคูณ 100,000)
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_p = df.loc[i, 'Open']
        h_time, l_time = "-", "-"
        
        # วิ่งหาแท่งถัด ๆ ไปเพื่อเช็กว่าสะสมครบ 100 จุดตอนไหน โดยใช้คอลัมน์ TimeZoneThai
        for j in range(i, len(df)):
            pts_high = (df.loc[j, 'High'] - open_p) * 100000
            pts_low = (open_p - df.loc[j, 'Low']) * 100000
            
            if h_time == "-" and pts_high >= 100:
                h_time = str(df.loc[j, 'TimeZoneThai'])
            if l_time == "-" and pts_low >= 100:
                l_time = str(df.loc[j, 'TimeZoneThai'])
            if h_time != "-" and l_time != "-":
                break
                
        high_targets.append(h_time)
        low_targets.append(l_time)

    # บันทึกเวลาเป้าหมายลงตาราง
    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 3. แบ่งพื้นที่แสดงผลหน้าจอแยกซ้าย-ขวาบนแดชบอร์ด
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("### 📈 กราฟแท่งเทียน (Candlestick Chart)")
        fig = go.Figure(data=[go.Candlestick(
            x=df['TimeZoneThai'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing_line_color='#26a69a', decreasing_line_color='#ef5350', name="Candle"
        )])
        fig.update_layout(
            xaxis_title="เวลาไทย (TimeZoneThai)",
            yaxis_title="ราคา (Price)",
            xaxis_rangeslider_visible=False, 
            height=580, 
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        show_cols = ['TimeZoneThai', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']
        st.dataframe(df[show_cols], height=530, use_container_width=True)

    st.success("✨ ซิงค์ตรงกับ Google Sheet เรียบร้อย! ข้อมูลอัปเดตอัตโนมัติแบบสด ๆ ทุกวันครับ")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
