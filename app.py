
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

# สั่งล้างแคชระบบ Streamlit ทุกรอบที่มีการเปิดหน้าเว็บ เพื่อป้องกันการจำโค้ดเก่าที่มี Error
st.cache_data.clear()

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live Data)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet")

# ลิงก์ดึงข้อมูล CSV ของชีท Master
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

def load_data_final(url):
    # ใช้ requests ไปดาวน์โหลดข้อมูลดิบตรงๆ จาก Google Sheet ป้องกันการล็อกพารามิเตอร์
    response = requests.get(url)
    response.encoding = 'utf-8'
    
    # อ่านข้อมูลเข้ามาโดยไม่ระบุคอลัมน์ล่วงหน้า เพื่อให้โหลดผ่านชัวร์ 100%
    raw_text = response.text
    
    # แปลงข้อความดิบให้กลายเป็นตาราง DataFrame
    lines = [line.split(',') for line in raw_text.strip().split('\n')]
    
    # แปลงเป็นตาราง
    df_parsed = pd.DataFrame(lines)
    
    # ตรวจสอบและตัดแถวหัวข้อออกหากมีตัวอักษรปนมาในแถวแรก
    try:
        float(df_parsed.iloc[0, 2])
    except:
        df_parsed = df_parsed.iloc[1:].reset_index(drop=True)
        
    # คัดเลือกเฉพาะ 8 คอลัมน์แรกตามโครงสร้างจริง ป้องกันคอลัมน์ว่างเกินมาสร้างปัญหา
    df_parsed = df_parsed.iloc[:, :8]
    
    # ตั้งชื่อคอลัมน์มาตรฐานสากลที่ระบบใช้งาน
    df_parsed.columns = ['Date', 'TimeZoneForex', 'Open', 'High', 'Low', 'Close', 'Volume', 'TimeZoneThai']
    return df_parsed

try:
    # เรียกใช้ฟังก์ชันแกะกล่องข้อมูลแบบปลอดภัยสูง
    df = load_data_final(sheet_url)
    
    # แปลงค่าราคาให้เป็นตัวเลขทศนิยมเพื่อใช้ในการคำนวณจุด
    df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
    df['High'] = pd.to_numeric(df['High'], errors='coerce')
    df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    # ลบแถวที่เป็นค่าว่างออกเพื่อป้องกันการคำนวณผิดพลาด
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
            increasing_line_color='#26a69a',  # ขึ้น = สีเขียวมินต์
            decreasing_line_color='#ef5350',  # ลง = แดงสด
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

    st.success("✨ ล้างแคชเวอร์ชันเก่าทิ้งสำเร็จ! ระบบแสดงผลตามข้อมูลจริงเรียบร้อยครับ")

except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
