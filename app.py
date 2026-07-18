import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json

# 1. ตั้งค่าหน้าเว็บให้แสดงผลเต็มพื้นที่จอ (เหมาะกับมือถือมาก)
st.set_page_config(layout="wide", page_title="Forex Live Chart Pro")

st.title("📊 Forex Pro Candlestick & Trend Analyzer")
st.subheader("แสดงผลเวลาแท่ง และเวลาชนะ 100 จุด บนหัวแท่งเทียนโดยตรง (จิ้มเพื่อล็อกแท่งค้างดูเทรนด์)")

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

    # 3. เตรียมข้อมูลแปลงเป็น JSON (เพิ่มตัวแปรเวลาของแท่งเทียนลงไปบนป้าย)
    chart_data = []
    for idx, row in df.iterrows():
        self_time = f"T:{row['TimeZoneThai']}" # เวลาตัวมันเอง
        buy_res = f"B:{row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "B:No"
        sell_res = f"S:{row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "S:No"
        
        # ประกอบร่างป้าย 3 บรรทัด (เวลาแท่ง -> เวลา Buy -> เวลา Sell)
        label_text = f"{self_time}<br>{buy_res}<br>{sell_res}"
        
        chart_data.append({
            'time': row['TimeZoneThai'],
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low'],
            'close': row['Close'],
            'label': label_text
        })
    
    json_data = json.dumps(chart_data)

    # 4. เขียนชุดคำสั่ง HTML + JS บังคับให้กราฟวาดข้อความค้างไว้บนหัวแท่งเทียน
    html_code = f"""
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <div id="chart-container" style="width: 100%; height: 620px;"></div>
    
    <script>
        const rawData = {json_data};
        
        const xData = rawData.map(d => d.time);
        const openData = rawData.map(d => d.open);
        const highData = rawData.map(d => d.high);
        const lowData = rawData.map(d => d.low);
        const closeData = rawData.map(d => d.close);
        const textLabels = rawData.map(d => d.label);
        
        // 1. ตัวกราฟแท่งเทียนหลัก
        const traceCandle = {{
            x: xData, open: openData, high: highData, low: lowData, close: closeData,
            type: 'candlestick',
            increasing: {{line: {{color: '#26a69a', width: 2}}}},
            decreasing: {{line: {{color: '#ef5350', width: 2}}}},
            hoverinfo: 'none',
            name: 'Forex'
        }};
        
        // 2. ตัวเลเยอร์พิเศษโชว์ค่าข้อความ T:เวลา / B:เวลา / S:เวลา ลอยอยู่บนจุด High
        const traceLabels = {{
            x: xData,
            y: highData.map(h => h + 0.0001), 
            mode: 'text',
            text: textLabels,
            textposition: 'top center',
            textfont: {{color: '#00ffcc', size: 9, family: 'sans-serif'}},
            hoverinfo: 'none',
            showlegend: false
        }};
        
        const layout = {{
            dragmode: 'pan',
            margin: {{l: 45, r: 10, t: 10, b: 40}},
            xaxis: {{rangeslider: {{visible: false}}, gridcolor: '#222', tickcolor: '#fff', color: '#fff'}},
            yaxis: {{gridcolor: '#222', tickcolor: '#fff', color: '#fff'}},
            plot_bgcolor: '#111',
            paper_bgcolor: '#111',
            shapes: []
        }};
        
        const config = {{responsive: true, displayModeBar: false}};
        const chartDiv = document.getElementById('chart-container');
        
        Plotly.newPlot(chartDiv, [traceCandle, traceLabels], layout, config);
        
        // 3. ระบบคลิกแล้วสร้างเส้นประไฮไลต์ล็อกค้างไว้ที่แท่งนั้น
        chartDiv.on('plotly_click', function(data){{
            if(!data || !data.points) return;
            const clickedX = data.points[0].x;
            
            const highlightShape = {{
                type: 'line',
                x0: clickedX,
                x1: clickedX,
                yref: 'paper',
                y0: 0,
                y1: 1,
                line: {{
                    color: '#ffcc00',
                    width: 2,
                    dash: 'dashdot'
                }}
            }};
            
            Plotly.relayout(chartDiv, {{shapes: [highlightShape]}});
        }});
    </script>
    """
    
    # รันโค้ดลงเว็บ
    components.html(html_code, height=640, scrolling=False)
    st.info("💡 ข้อมูลบนหัวแท่งเทียน: T = เวลาตัวมันเอง | B = เวลาชนะ Buy | S = เวลาชนะ Sell")

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
