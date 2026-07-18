import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import urllib.request

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ")

# ลิงก์ดึงข้อมูล CSV ของชีท Master
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

def load_data_from_sheet(url):
    # ดึงข้อมูลดิบเป็นข้อความยาวๆ เพื่อไม่ให้พึ่งพาตัวอ่านคอลัมน์ของระบบที่มักจะเออเร่อ
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        raw_text = response.read().decode('utf-8')
    
    parsed_rows = []
    # วิ่งแยกแยะข้อมูลทีละบรรทัดด้วยระบบแมนนวล ปลอดภัยที่สุด
    for line in raw_text.strip().split('\n'):
        # ล้างเครื่องหมายคำพูดฟันหนู " และล้างช่องว่างทิ้ง
        clean_line = line.replace('"', '').strip()
        if not clean_line:
            continue
        
        # แยกชิ้นส่วนด้วยเครื่องหมายคอมมา
        parts = clean_line.split(',')
        
        # ข้อมูลที่สมบูรณ์ต้องมีอย่างน้อย 8 คอลัมน์ (A ถึง H)
        if len(parts) >= 8:
            # ตรวจสอบว่าคอลัมน์ Open (ตำแหน่งที่ 2) เป็นตัวเลขราคารึเปล่า ถ้าใช่คือบรรทัดข้อมูลจริง
            try:
                float(parts[2])
                parsed_rows.append(parts[:8])
            except ValueError:
                # ถ้าไม่ใช่ตัวเลข (เช่น เป็นแถวหัวข้อหนังสือ) ให้ข้ามไป
                continue
                
    # นำข้อมูลที่ผ่านการกรองแล้วมาสร้างเป็นตารางใหม่เอี่ยม 8 คอลัมน์มาตรฐาน
    df_new = pd.DataFrame(parsed_rows, columns=['Date', 'TimeZoneForex', 'Open', 'High', 'Low', 'Close', 'Volume', 'TimeZoneThai'])
    return df_new

try:
    # เรียกใช้ฟังก์ชันแกะกล่องข้อมูล
    df = load_data_from_sheet(sheet_url)
    
    # แปลงค่าราคาให้กลายเป็นตัวเลขทศนิยมเพื่อใช้ในการคำนวณสูตรจุด
    df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
    df['High'] = pd.to_numeric(df['High'], errors='coerce')
    df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    # ลบแถวค่าว่าง (ถ้ามี)
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index(drop=True)

    # 2. ลอจิกการคำนวณหาเวลาที่ชนเป้าหมาย 100 จุดจากราคา Open (สูตรคูณ 100,000)
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

    # 3. แสดงผลหน้าจอแยกซ้าย-ขวาแบบแดชบอร์ดมืออาชีพ
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
            height=550, 
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        show_cols = ['TimeZoneThai', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']
        st.dataframe(df[show_cols], height=500, use_container_width=True)

    st.success("✨ ซิงค์สดเชื่อมต่อ Google Sheet เรียบร้อยแล้ว! ข้อมูลจะอัปเดตเองทุกวันครับ")

except Exception as err:
    st.error(f"ระบบกำลังรอข้อมูลอัปเดตที่สมบูรณ์จากหน้า Google Sheet: {err}")
