import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json

# 1. ตั้งค่าหน้าเว็บกว้างเต็มจอ (เหมาะกับมือถือ)
st.set_page_config(layout="wide", page_title="Forex Live Chart")

st.title("📊 Forex Candlestick & Target 100 Points")
st.subheader("ดึงข้อมูลสดจาก Google Sheet อัตโนมัติ (เวอร์ชันคลิกล็อกค้างบนมือถือ)")

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

    # 2. ลอจิกคำนวณเป้าหมาย 100 จุดจากราคา Open
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

    # 3. เตรียมข้อมูลส่งไปให้ระบบ JavaScript จัดการคลิกล็อกค้าง
    chart_data = []
    for idx, row in df.iterrows():
        buy_res = f"{row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "No"
        sell_res = f"{row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "No"
        chart_data.append({
            'time': row['TimeZoneThai'],
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low'],
            'close': row['Close'],
            'buy': buy_res,
            'sell': sell_res
        })
    
    json_data = json.dumps(chart_data)

    # 4. ใช้ชุดคำสั่ง HTML + JS ปลดล็อกระบบคลิกค้างแบบอิสระ 100%
    html_code = f"""
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <div id="chart-container" style="width: 100%; height: 500px;"></div>
    
    <!-- กล่องโชว์ข้อมูลล็อกค้างด้านล่าง ดีไซน์สไตล์แอปเทรดมืด -->
    <div id="info-box" style="margin-top: 15px; padding: 15px; background: #1e1e1e; border-radius: 8px; color: #fff; font-family: sans-serif; display: none; position: relative; border: 1px solid #333;">
        <span id="close-btn" style="position: absolute; right: 15px; top: 10px; cursor: pointer; color: #ff5555; font-weight: bold; font-size: 20px;">&times;</span>
        <div style="font-size: 16px; margin-bottom: 8px; color: #00ffcc; font-weight: bold;">⏰ เวลาไทย: <span id="lbl-time"></span></div>
        <div style="display: flex; gap: 20px; font-size: 15px; margin-bottom: 8px;">
            <div>🟢 Buy = <span id="lbl-buy" style="font-weight:bold;"></span></div>
            <div>🔴 Sell = <span id="lbl-sell" style="font-weight:bold;"></span></div>
        </div>
        <div style="font-size: 13px; color: #aaa;">
            O: <span id="lbl-open"></span> | H: <span id="lbl-high"></span> | L: <span id="lbl-low"></span> | C: <span id="lbl-close"></span>
        </div>
    </div>

    <script>
        const rawData = {json_data};
        
        const xData = rawData.map(d => d.time);
        const openData = rawData.map(d => d.open);
        const highData = rawData.map(d => d.high);
        const lowData = rawData.map(d => d.low);
        const closeData = rawData.map(d => d.close);
        
        const trace = {{
            x: xData, open: openData, high: highData, low: lowData, close: closeData,
            type: 'candlestick',
            increasing: {{line: {{color: '#26a69a'}}}},
            decreasing: {{line: {{color: '#ef5350'}}}},
            hoverinfo: 'none' // ปิดป๊อปอัปน่ารำคาญแบบเก่า
        }};
        
        const layout = {{
            dragmode: 'pan',
            margin: {{l: 35, r: 10, t: 10, b: 30}},
            xaxis: {{rangeslider: {{visible: false}}, gridcolor: '#333', tickcolor: '#fff'}},
            yaxis: {{gridcolor: '#333', tickcolor: '#fff'}},
            plot_bgcolor: '#111',
            paper_bgcolor: '#111'
        }};
        
        const config = {{responsive: true, displayModeBar: false}};
        
        const chartDiv = document.getElementById('chart-container');
        Plotly.newPlot(chartDiv, [trace], layout, config);
        
        // ระบบดักจับการคลิก (จิ้ม) บนมือถือ/คอมพิวเตอร์
        chartDiv.on('plotly_click', function(data){{
            const pointIndex = data.points[0].pointIndex;
            const item = rawData[pointIndex];
            
            // อัปเดตข้อมูลใส่กล่อง
            document.getElementById('lbl-time').innerText = item.time;
            document.getElementById('lbl-buy').innerText = item.buy;
            document.getElementById('lbl-sell').innerText = item.sell;
            document.getElementById('lbl-open').innerText = item.open;
            document.getElementById('lbl-high').innerText = item.high;
            document.getElementById('lbl-low').innerText = item.low;
            document.getElementById('lbl-close').innerText = item.close;
            
            // เปลี่ยนสีตัวอักษรตามผลลัพธ์
            document.getElementById('lbl-buy').style.color = item.buy === 'No' ? '#ff5555' : '#00ff88';
            document.getElementById('lbl-sell').style.color = item.sell === 'No' ? '#ff5555' : '#00ff88';
            
            // สั่งแสดงผลกล่องข้อความล็อกค้างไว้ทันที
            document.getElementById('info-box').style.display = 'block';
        }});
        
        // ปุ่มกากบาทปิดกล่องข้อความ
        document.getElementById('close-btn').addEventListener('click', function(){{
            document.getElementById('info-box').style.display = 'none';
        }});
    </script>
    """
    
    # เรนเดอร์หน้าจอลงแอป
    components.html(html_code, height=720, scrolling=False)
    st.success("✨ เปิดใช้งานโหมดคลิกล็อกค้าง (Persistent Info) บนมือถือเรียบร้อยครับ!")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
