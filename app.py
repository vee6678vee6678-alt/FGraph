import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# ลิงก์ดึงข้อมูล CSV ของชีท Master (ดึงแบบไม่ใช้แคชเพื่อให้ได้ข้อมูลสดใหม่เสมอ)
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

try:
    # อ่านข้อมูลโดยข้ามแถวแรก (แถวหัวตารางตัวหนังสือ) เพื่อให้เหลือแต่ตัวเลขราคาส่วนข้อมูลเพียวๆ
    df_raw = pd.read_csv(sheet_url, skiprows=1, header=None)
    
    # ถ้าข้อมูลส่งมารวมกันเป็น 1 คอลัมน์ ให้แยกออกจากกันด้วยเครื่องหมายคอมมา ,
    if df_raw.shape[1] == 1:
        df_raw = df_raw[0].str.split(',', expand=True)
        
    # สร้างตารางใหม่โดยดึงจากตำแหน่งลำดับคอลัมน์จริง (คอลัมน์ A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7)
    df = pd.DataFrame()
    df['Date'] = df_raw[0].astype(str)
    df['TimeZoneForex'] = df_raw[1].astype(str)
    df['Open'] = pd.to_numeric(df_raw[2], errors='coerce')   # คอลัมน์ C (Open)
    df['High'] = pd.to_numeric(df_raw[3], errors='coerce')   # คอลัมน์ D (High)
    df['Low'] = pd.to_numeric(df_raw[4], errors='coerce')    # คอลัมน์ E (Low)
    df['Close'] = pd.to_numeric(df_raw[5], errors='coerce')  # คอลัมน์ F (Close)
    df['Volume'] = df_raw[6].astype(str)
    df['TimeZoneThai'] = df_raw[7].astype(str)               # คอลัมน์ H (เวลาไทย)
    
    # ลบแถวที่เป็นค่าว่างออกเพื่อความแม่นยำในการคำนวณ
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. ลอจิกการคำนวณหาเวลาที่ชนเป้าหมาย 100 จุดจากราคา Open (สูตรคูณ 100,000)
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_p = df.loc[i, 'Open']
        h_time, l_time = "-", "-"
        
        # วิ่งหาแท่งถัด ๆ ไปเพื่อเช็กระยะจุด
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

    # บันทึกผลลัพธ์ลงคอลัมน์ใหม่
    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 3. จัดสัดส่วนแสดงผลแยกซ้าย-ขวาบนแดชบอร์ด
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

    st.success("✨ เชื่อมต่อ Google Sheet เรียบร้อย! ต่อไปข้อมูลจะอัปเดตตามชีทอัตโนมัติทุกวันแล้วครับ")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
