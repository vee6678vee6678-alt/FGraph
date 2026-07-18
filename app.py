import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live Data)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet")

# ลิงก์ดึงข้อมูล CSV ของชีท Master
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

# ใช้ตรรกะไม่อ่านแคชค้างคืน เพื่อดึงค่าสดใหม่จริง ๆ เสมอ
def load_data_fresh(url):
    # ดึงข้อมูลมาเป็น DataFrame ตรงๆ
    raw_df = pd.read_csv(url)
    
    # ล้างช่องว่างที่หัวตารางออกทั้งหมด
    raw_df.columns = raw_df.columns.str.strip().str.replace(' ', '')
    
    # บังคับว่าถ้าหาชื่อคอลัมน์ไม่เจอ ให้แมตช์ตามลำดับจริงในตารางเลย (ป้องกัน Error เรื่องชื่อ)
    if 'Open' not in raw_df.columns:
        # กำหนดชื่อคอลัมน์ให้ใหม่ตามลำดับ A, B, C, D, E, F, G, H จากไฟล์ดึงใหม่
        raw_df = pd.read_csv(url, skiprows=1, header=None)
        raw_df.columns = ['Date', 'TimeZoneForex', 'Open', 'High', 'Low', 'Close', 'Volume', 'TimeZoneThai']
        
    return raw_df

try:
    # เรียกใช้ฟังก์ชันดึงข้อมูลสด
    df = load_data_fresh(sheet_url)
    
    # แปลงค่าราคาให้เป็นตัวเลขทศนิยมเพื่อใช้ในการคำนวณจุด
    df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
    df['High'] = pd.to_numeric(df['High'], errors='coerce')
    df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    # ลบแถวที่เป็นค่าว่างออกเพื่อป้องกัน Error
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    df = df.reset_index(drop=True)

    # 3. ลอจิกการคำนวณหาเวลาที่ชนเป้าหมาย 100 จุดจากราคา Open
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_price = df.loc[i, 'Open']
        high_reached_time = "-"
        low_reached_time = "-"
        
        # วิ่งหาแท่งถัด ๆ ไปเพื่อเช็กว่าสะสมครบ 100 จุดตอนไหน
        for j in range(i, len(df)):
            current_high = df.loc[j, 'High']
            current_low = df.loc[j, 'Low']
            
            # คำนวณระยะจุด (สูตรคูณ 100000 ตามที่คุณวีรพันธ์ระบุ)
            points_to_high = (current_high - open_price) * 100000
            points_to_low = (open_price - current_low) * 100000
            
            # เช็กเวลาเป้าหมายฝั่ง Buy (High)
            if high_reached_time == "-" and points_to_high >= 100:
                high_reached_time = str(df.loc[j, 'TimeZoneThai'])
                
            # เช็กเวลาเป้าหมายฝั่ง Sell (Low)
            if low_reached_time == "-" and points_to_low >= 100:
                low_reached_time = str(df.loc[j, 'TimeZoneThai'])
                
            if high_reached_time != "-" and low_reached_time != "-":
                break
                
        high_targets.append(high_reached_time)
        low_targets.append(low_reached_time)

    # เพิ่มข้อมูลผลลัพธ์ลงตารางหลัก
    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 4. แสดงผลแยกฝั่งซ้าย-ขวาบนหน้าแดชบอร์ด
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 📈 กราฟแท่งเทียน (Candlestick Chart)")
        
        fig = go.Figure(data=[go.Candlestick(
            x=df['TimeZoneThai'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#26a69a',  # ขึ้น = เขียว
            decreasing_line_color='#ef5350',  # ลง = แดง
            name="Candle"
        )])
        
        fig.update_layout(
            xaxis_title="เวลาไทย (TimeZoneThai)",
            yaxis_title="ราคา (Price)",
            xaxis_rangeslider_visible=False,
            height=600,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        st.write("ผลลัพธ์ประมวลผลคำนวณแบบเรียลไทม์จาก Google Sheet:")
        
        display_df = df[['TimeZoneThai', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']]
        st.dataframe(display_df, height=560, use_container_width=True)

    st.success("✨ ล้างแคชเก่าสำเร็จ ดึงข้อมูลจริงจากหน้า Google Sheet มาแสดงผลเรียบร้อยครับ!")

except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")


