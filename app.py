import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. ตั้งค่าหน้าเว็บให้แสดงแบบกว้างเต็มจอ
st.set_page_config(layout="wide")

st.title("📊 Forex Candlestick & Target 100 Points Analyzer (Live Data)")
st.subheader("วิเคราะห์แท่งเทียนและคำนวณเป้าหมาย 100 จุด ดึงข้อมูลสดจาก Google Sheet")

# 2. ลิงก์ Google Sheet ของคุณวีรพันธ์ (ดึงข้อมูลเป็น CSV อัตโนมัติ)
sheet_url = "https://docs.google.com/spreadsheets/d/1PF1KT4G9NDeVsleFhjR9YIYCYvhJ7Xq8yilUyNrmVYk/export?format=csv&gid=1014151853"

@st.cache_data(ttl=60)
def load_data(url):
    columns = ['Date', 'ServerTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'ThaiTime']
    df = pd.read_csv(url, skiprows=1, names=columns)
    return df

try:
    df = load_data(sheet_url)
    
    # แปลงค่าตัวเลขราคาให้เป็นทศนิยม
    df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
    df['High'] = pd.to_numeric(df['High'], errors='coerce')
    df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    # 3. ลอจิกคำนวณเป้าหมาย 100 จุดจากราคา Open วิ่งเช็กไปทีละแท่งข้างหน้า
    high_targets = []
    low_targets = []

    for i in range(len(df)):
        open_price = df.iloc[i]['Open']
        high_reached_time = "-"
        low_reached_time = "-"
        
        for j in range(i, len(df)):
            current_high = df.iloc[j]['High']
            current_low = df.iloc[j]['Low']
            
            # สูตรคำนวณระยะจุด (* 100000)
            points_to_high = (current_high - open_price) * 100000
            points_to_low = (open_price - current_low) * 100000
            
            if high_reached_time == "-" and points_to_high >= 100:
                high_reached_time = df.iloc[j]['ThaiTime']
                
            if low_reached_time == "-" and points_to_low >= 100:
                low_reached_time = df.iloc[j]['ThaiTime']
                
            if high_reached_time != "-" and low_reached_time != "-":
                break
                
        high_targets.append(high_reached_time)
        low_targets.append(low_reached_time)

    df['Buy Target (100 pts) at'] = high_targets
    df['Sell Target (100 pts) at'] = low_targets

    # 4. แบ่งหน้าจอแสดงผลเป็น 2 ฝั่ง (ซ้าย: กราฟแท่งเทียน, ขวา: ตารางคำนวณ)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 📈 กราฟแท่งเทียน (Candlestick Chart)")
        fig = go.Figure(data=[go.Candlestick(
            x=df['ThaiTime'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='#26a69a',  # ขึ้น = เขียว
            decreasing_line_color='#ef5350',  # ลง = แดง
            name="Candle"
        )])
        
        fig.update_layout(
            xaxis_title="เวลาไทย (Thai Time)",
            yaxis_title="ราคา (Price)",
            xaxis_rangeslider_visible=False,
            height=600,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📋 ตารางสรุปเวลาเป้าหมาย 100 จุด")
        st.write("คำนวณจากข้อมูลล่าสุดบน Google Sheet:")
        
        display_df = df[['ThaiTime', 'Open', 'High', 'Low', 'Close', 'Buy Target (100 pts) at', 'Sell Target (100 pts) at']]
        st.dataframe(display_df, height=560, use_container_width=True)

    st.success("✨ ดึงข้อมูลและประมวลผลสำเร็จ!")

except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลจาก Google Sheet: {e}")
