
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
st.subheader("แสดงผลเวลาแท่ง และเวลาชนะ 100 จุด บนหัวแท่งเทียนโดยตรง (โหมดพื้นหลังขาว คมชัดสูง)")

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

    # 3. เตรียมข้อมูลแปลงเป็น JSON (ข้อความตัวใหญ่ คมชัด)
    chart_data = []
    for idx, row in df.iterrows():
        self_time = f"T: {row['TimeZoneThai']}" 
        buy_res = f"B: {row['Buy Target (100 pts) at']}" if row['Buy Target (100 pts) at'] != "-" else "B: No"
        sell_res = f"S: {row['Sell Target (100 pts) at']}" if row['Sell Target (100 pts) at'] != "-" else "S: No"
        
        # ป้ายข้อมูล 3 บรรทัด
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

    # 4. เขียนชุดคำสั่ง HTML + JS ปรับหน้าจอให้เป็นสีขาวสว่างและตัวหนังสือสีดำใหญ่ชัดเจน
    html_code = f"""
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <div id="chart-container" style="width: 100%; height: 620px; background-color: #FFFFFF;"></div>
    
    <script>
        const rawData = {json_data};
        
        const xData = rawData.map(d => d.time);
        const openData = rawData.map(d => d.open);
        const highData = rawData.map(d => d.high);
        const lowData = rawData.map(d => d.low);
        const closeData = rawData.map(d => d.close);
        const textLabels = rawData.map(d => d.label);
        
        // 1. ตัวกราฟแท่งเทียนสีมาตรฐานสากล
        const traceCandle = {{
            x: xData, open: openData, high: highData, low: lowData, close: closeData,
            type: 'candlestick',
            increasing: {{line: {{color: '#00a087', width: 2.5}}, fillcolor: '#00a087'}, // เขียวคมชัด
            decreasing: {{line: {{color: '#dc3545', width: 2.5}}, fillcolor: '#dc3545'}, // แดงคมชัด
            hoverinfo: 'none'
        }};
        
        // 2. ป้ายข้อความบนหัวแท่ง ปรับขนาดใหญ่ขึ้น (size: 12) และเป็นสีดำเข้มสนิท (#000000) อ่านง่ายมาก
        const traceLabels = {{
            x: xData,
            y: highData.map(h => h + 0.0001), 
            mode: 'text',
            text: textLabels,
            textposition: 'top center',
            textfont: {{color: '#000000', size: 12, family: 'sans-serif', weight: 'bold'}},
            hoverinfo: 'none',
            showlegend: false
        }};
        
        const layout = {{
            dragmode: 'pan',
            margin: {{l: 50, r: 10, t: 15, b: 40}},
            xaxis: {{rangeslider: {{visible: false}}, gridcolor: '#E5E5E5', tickcolor: '#000', color: '#000'}},
            yaxis: {{gridcolor: '#E5E5E5', tickcolor: '#000', color: '#000'}},
            plot_bgcolor: '#FFFFFF',  // พื้นหลังกราฟสีขาว
            paper_bgcolor: '#FFFFFF', // พื้นหลังกระดาษสีขาว
            shapes: []
        }};
        
        const config = {{responsive: true, displayModeBar: false}};
        const chartDiv = document.getElementById('chart-container');
        
        Plotly.newPlot(chartDiv, [traceCandle, traceLabels], layout, config);
        
        // 3. ระบบคลิกล็อกแท่ง เปลี่ยนเป็นเส้นประสีน้ำเงินเข้มหนาชัดเจน
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
                    color: '#0056b3', // สีน้ำเงินเข้มเข้มข้น ตัดกับสีขาวชัดเจน
                    width: 3,
                    dash: 'dash'
                }}
            }};
            
            Plotly.relayout(chartDiv, {{shapes: [highlightShape]}});
        }});
    </script>
    """
    
    # รันโค้ดลงเว็บ
    components.html(html_code, height=640, scrolling=False)
    st.markdown("<p style='color:#000; font-size:15px;'>💡 ข้อมูลบนหัวแท่งเทียน: T = เวลาแท่งเทียน | B = เวลาชนะ Buy | S = เวลาชนะ Sell</p>", unsafe_allow_html=True)

except Exception as err:
    st.error(f"❌ เกิดข้อผิดพลาดในระบบตรวจจับตาราง: {err}")
