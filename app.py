

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live Data)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet")

# ลิงก์ดึงข้อมูล CSV ของชีท Master
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

@st.cache_data(ttl=5)  # อัปเดตข้อมูลไวขึ้นทุกๆ 5 วินาทีเมื่อกดรีเฟรช
def load_data(url):
    # อ่านข้อมูลดิบโดยข้ามแถวแรกที่เป็นหัวข้อหนังสือ เพื่อความแม่นยำทางตำแหน่งตัวเลข
    df = pd.read_csv(url, skiprows=1, header=None)
    return df

try:
    df = load_data(sheet_url)
    
    # บังคับแปลงตำแหน่งคอลัมน์ตามจริง (คอลัมน์ A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7)
    # ล็อกตำแหน่งราคา: Open (คอลัมน์ C คือตำแหน่ง 2), High (D คือ 3), Low (E คือ 4), Close (F คือ 5)
    df[2] = pd.to_numeric(df[2], errors='coerce')  # Open
    df[3] = pd.to_numeric(df[3], errors='coerce')  # High
    df[4] = pd.to_numeric(df[4], errors='coerce')  # Low
    df[5] = pd.to_numeric(df[5], errors='coerce')  # Close
    
    # ลบแถวที่เป็นค่าว่างหรือตัวหนังสือแปลกปลอมออก
    df = df.dropna(subset=[2, 3, 4, 5])
    df = df.reset_index(drop=True)

    # 3. ลอจิกการคำนวณหาเวลาที่ชนเป้าหมาย 100 จุดจากราคา Open
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_price = df.loc[i, 2]
        high_reached_time = "-"
        low_reached_time = "-"
        
        # วิ่งเช็กแท่งถัด ๆ ไปเพื่อหาผลรวมจุดสะสม
        for j in range(i, len(df)):
            current_high = df.loc[j, 3]
            current_low = df.loc[j, 4]
            
            # คำนวณระยะจุด (สูตรคูณ 100000 ตามที่คุณวีรพันธ์ระบุ)
            points_to_high = (current_high - open_price) * 100000
            points_to_low = (open_price - current_low) * 100000
            
            # เช็กเวลาเป้าหมายฝั่ง Buy (High) อ้างอิงเวลาไทยจากคอลัมน์ H (ตำแหน่ง 7)
            if high_reached_time == "-" and points_to_high >= 100:
                high_reached_time = str(df.loc[j, 7])
                
            # เช็กเวลาเป้าหมายฝั่ง Sell (Low) อ้างอิงเวลาไทยจากคอลัมน์ H (ตำแหน่ง 7)
            if low_reached_time == "-" and points_to_low >= 100:
                low_reached_time = str(df.loc[j, 7])
                
            if high_reached_time != "-" and low_reached_time != "-":
                break
                
        high_targets.append(high_reached_time)
        low_targets.append(low_reached_time)

    # ตั้งชื่อคอลัมน์ใหม่ให้สวยงามสำหรับนำไปแสดงผล
    final_df = pd.DataFrame({
        'Date': df[0],
        'TimeZoneThai': df[7],
        'Open': df[2],
        'High': df[3],
        'Low': df[4],
        'Close': df[5],
        'Buy Target (100 pts) at': high_targets,
        'Sell Target (100 pts) at': low_targets
    })

    # 4. แสดงผลแยกฝั่งซ้าย-ขวาบนหน้าแดชบอร์ด
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 📈 กราฟแท่งเทียน (Candlestick Chart)")
        
        # วาดกราฟแท่งเทียนโดยใช้แกน X เป็นเวลาไทย (TimeZoneThai)
        fig = go.Figure(data=[go.Candlestick(
            x=final_df['TimeZoneThai'],
            open=final_df['Open'],
            high=final_df['High'],
            low=final_df['Low'],
            close=final_df['Close'],
            increasing_line_color='#26a69a',  # กราฟขึ้น = สีเขียวมินต์
            decreasing_line_color='#ef5350',  # กราฟลง = สีแดงสด
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
        st.write("ผลลัพธ์การคำนวณจุดสิ้นสุดแบบเรียลไทม์จาก Google Sheet:")
        
        st.dataframe(
            final_df,
            height=560,
            use_container_width=True
        )

    st.success("✨ หน้าแดชบอร์ดซิงค์ข้อมูลสดและเสร็จสมบูรณ์เรียบร้อยแล้วครับ!")

except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
