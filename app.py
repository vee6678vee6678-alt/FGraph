import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json

# 1. ตั้งค่าหน้าเว็บกว้างเต็มจอ (ปรับโทนธีมสว่างในแอป)
st.set_page_config(layout="wide", page_title="Forex Live Chart Pro")

# บังคับปรับสไตล์พื้นหลังหน้าเว็บ Streamlit ให้เป็นสีขาวและตัวอักษรดำเข้มสะใจ
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    h1, h3, p, span {
        color: #000000 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Forex Pro Candlestick & Trend Analyzer")
st.subheader("ระบบคัดกรองเวลาอัจฉริยะ: จิ้มแท่งเทียนเพื่อเปิด/ปิดป้ายข้อมูลล็อกค้างแยกรายแท่ง")

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

    # 2. ลоจิกคำนวณเป้าหมาย 100 จุดจากราคา Open
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

    # 3. เตรียมข้อมูลโครงสร้าง JSON และลоจิกคำนวณตำแหน่งสลับฟันปลาล่วงหน้า
    chart_data = []
    for idx, row in df.iterrows():
        self_time = f"T: {row['TimeZoneThai']}" 
        buy_res = f"B: {row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "B: No"
        sell_res = f"S: {row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "S: No"
        
        label_text = f"{self_time}<br>{buy_res}<br>{sell_res}"
        
        if idx % 2 == 0:
            target_y = float(row['High']) + 0.0001
            pos_text = "top center"
        else:
            target_y = float(row['Low']) - 0.0001
            pos_text = "bottom center"
            
        chart_data.append({
            'time': row['TimeZoneThai'],
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low'],
            'close': row['Close'],
            'label': label_text,
            'y_pos': target_y,
            'text_pos': pos_text
        })
    
    json_data = json.dumps(chart_data)

    # 4. ใช้โหมดข้อความดิบ (Raw String) จัดการคุมเอนจิ้นกราฟผ่านจาวาสคริปต์
    html_code = r"""
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <div id="chart-container" style="width: 100%; height: 620px; background-color: #FFFFFF;"></div>
    
    <script>
        const rawData = JSON_DATA_PLACEHOLDER;
        
        const xData = rawData.map(d => d.time);
        const openData = rawData.map(d => d.open);
        const highData = rawData.map(d => d.high);
        const lowData = rawData.map(d => d.low);
        const closeData = rawData.map(d => d.close);
        
        // อาร์เรย์สำหรับบันทึกสถานะป้ายที่ถูกเลือก (เริ่มต้นเป็นค่าว่างเพื่อให้กราฟโล่งคลีน)
        let activeLabels = rawData.map(() => "");
        let activeY = rawData.map(() => null);
        let activePositions = rawData.map(() => "top center");
        
        // 1. เลเยอร์แท่งเทียนหลัก
        const traceCandle = {
            x: xData, open: openData, high: highData, low: lowData, close: closeData,
            type: 'candlestick',
            increasing: {line: {color: '#00a087', width: 2.5}, fillcolor: '#00a087'},
            decreasing: {line: {color: '#dc3545', width: 2.5}, fillcolor: '#dc3545'},
            hoverinfo: 'none'
        };
        
        // 2. เลเยอร์ป้ายข้อความ (ตัวหนังสือขนาด 13 หนาเข้มชัดเจนมาก)
        const traceLabels = {
            x: xData,
            y: activeY, 
            mode: 'text',
            text: activeLabels,
            textposition: activePositions,
            textfont: {color: '#000000', size: 13, family: 'sans-serif', weight: '900'},
            hoverinfo: 'none',
            showlegend: false
        };
        
        const layout = {
            dragmode: 'pan',
            margin: {l: 50, r: 10, t: 25, b: 40},
            xaxis: {rangeslider: {visible: false}, gridcolor: '#E5E5E5', tickcolor: '#000', color: '#000'},
            yaxis: {gridcolor: '#E5E5E5', tickcolor: '#000', color: '#000'},
            plot_bgcolor: '#FFFFFF',
            paper_bgcolor: '#FFFFFF',
            shapes: []
        };
        
        const config = {responsive: true, displayModeBar: false};
        const chartDiv = document.getElementById('chart-container');
        
        Plotly.newPlot(chartDiv, [traceCandle, traceLabels], layout, config);
        
        // เก็บบันทึกรายการเส้นประไฮไลต์รายแท่ง
        let selectedShapes = {};
        
        // 3. ระบบจิ้มเพื่อเปิดป้ายค้างไว้ จิ้มซ้ำอีกทีเพื่อปิด (Toggle System)
        chartDiv.on('plotly_click', function(data){
            if(!data || !data.points) return;
            const pointIndex = data.points[0].pointIndex;
            const clickedX = data.points[0].x;
            const item = rawData[pointIndex];
            
            // เช็กสถานะ: ถ้าแท่งนี้ยังไม่ได้ถูกเปิดใช้งาน
            if (activeLabels[pointIndex] === "") {
                // เปิดป้ายข้อความฟันปลาล็อกค้างไว้
                activeLabels[pointIndex] = item.label;
                activeY[pointIndex] = item.y_pos;
                activePositions[pointIndex] = item.text_pos;
                
                // สร้างเส้นประไฮไลต์สีน้ำเงินเข้มหนา 3px ล็อกเฉพาะแท่งนี้
                selectedShapes[pointIndex] = {
                    type: 'line',
                    x0: clickedX, x1: clickedX, yref: 'paper', y0: 0, y1: 1,
                    line: { color: '#0056b3', width: 3, dash: 'dash' }
                };
            } else {
                // ถ้าจิ้มซ้ำแท่งเดิม ให้ปิดการแสดงผลและลบเส้นออกทันที
                activeLabels[pointIndex] = "";
                activeY[pointIndex] = null;
                delete selectedShapes[pointIndex];
            }
            
            // อัปเดตข้อมูลลงกราฟแบบเรียลไทม์
            Plotly.animate(chartDiv, {
                data: [traceCandle, { y: activeY, text: activeLabels, textposition: activePositions }]
            }, {
                transition: { duration: 0 },
                frame: { duration: 0, redraw: true }
            });
            
            // อัปเดตเส้นไฮไลต์ทับลงบนตารางรูปทรง
            const currentShapes = Object.values(selectedShapes);
            Plotly.relayout(chartDiv, { shapes: currentShapes });
        });
    </script>
    """.replace("JSON_DATA_PLACEHOLDER", json_data)
    
    # เรนเดอร์ลงเว็บแอป
    components.html(html_code, height=640, scrolling=False)
    st.markdown("<p style='color:#000; font-size:16px; font-weight:bold;'>📱 วิธีคัดกรอง: หน้าจอจะโล่งคลีนเมื่อเปิดมา -> ใช้นิ้วจิ้มแท่งเทียนที่ต้องการเพื่อเปิดป้ายข้อมูลล็อกค้างไว้ -> จิ้มซ้ำที่แท่งเดิมเพื่อปิดป้ายออกได้ตลอดเวลาครับ</p>", unsafe_allow_html=True)

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
