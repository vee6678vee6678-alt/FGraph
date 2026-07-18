import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# เปลี่ยนลิงก์ดึงข้อมูล CSV ใหม่ โดยเจาะจงให้โหลดแผ่นงานแรกสุดของไฟล์โดยตรง ป้องกันข้อผิดพลาด
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv"

try:
    # อ่านข้อมูลสดจากตารางโดยตรง
    df_raw = pd.read_csv(sheet_url, header=None)
    
    # ถ้าหากข้อมูลที่ดึงมามีแถวหรือคอลัมน์ไม่พอ หรือยุบรวมกัน ให้กระจายคอลัมน์อัตโนมัติ
    if df_raw.shape[1] == 1:
        df_raw = df_raw[0].str.split(',', expand=True)
        
    # ส่องหาแถวแรกที่เป็นตัวเลขราคาจริง โดยข้ามแถวหัวข้อที่เป็นตัวหนังสือทิ้งไปโดยไม่สนชื่อ
    start_idx = 0
    for idx in range(len(df_raw)):
        try:
            # ลองแปลงคอลัมน์ C (พิกัดตำแหน่งที่ 2) ให้เป็นตัวเลขดู
            float(df_raw.iloc[idx, 2])
            start_idx = idx
            break
        except:
            continue
            
    # ตัดเอาเฉพาะแถวข้อมูลตัวเลขเป็นต้นไปมาใช้งาน
    df_raw = df_raw.iloc[start_idx:].reset_index(drop=True)

    # ประกอบร่างสร้างตารางใหม่ อ้างอิงตามลำดับคอลัมน์จริงใน Google Sheet (A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7)
    df = pd.DataFrame()
    df['Date'] = df_raw[0].astype(str)
    df['TimeZoneForex'] = df_raw[1].astype(str)
    df['Open'] = pd.to_numeric(df_raw[2], errors='coerce')   # ราคา Open (คอลัมน์ C)
    df['High'] = pd.to_numeric(df_raw[3], errors='coerce')   # ราคา High (คอลัมน์ D)
    df['Low'] = pd.to_numeric(df_raw[4], errors='coerce')    # ราคา Low (คอลัมน์ E)
    df['Close'] = pd.to_numeric(df_raw[5], errors='coerce')  # ราคา Close (คอลัมน์ F)
    df['Volume'] = df_raw[6].astype(str)
    df['TimeZoneThai'] = df_raw[7].astype(str)               # เวลาไทย (คอลัมน์ H)
    
    # ลบแถวเสียหรือค่าว่างที่ปนมาทิ้ง
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. ลоจิกคำนวณเป้าหมาย 100 จุดจากราคา Open วิ่งเช็กไปทีละแท่งข้างหน้า (*100,000)
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_p = df.loc[i, 'Open']
        h_time, l_time = "-", "-"
        
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

    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 3. แบ่งหน้าจอแสดงผลแดชบอร์ด
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

    st.success("✨ ลิงก์ตรงสำเร็จ! ระบบจะดึงข้อมูลราคาล่าสุดมาอัปเดตให้อัตโนมัติทุกวันแล้วครับ")

except Exception as err:
    st.error(f"❌ กำลังรอข้อมูลอัปเดตที่สมบูรณ์จากตาราง: {err}")
