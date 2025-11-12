import streamlit as st

def render_progress_circle(percent, color, label=""):
    angle = (percent / 100) * 360
    style = f"""
    <div style="display: flex; flex-direction: column; align-items: center;">
        <div style="
            position: relative;
            width: 110px;
            height: 110px;
            border-radius: 50%;
            background: conic-gradient({color} {angle}deg, #2b2c36 {angle}deg);
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 105px;
                height: 105px;
                border-radius: 50%;
                background-color: #0e1117;
                font-size: 1.5em;
                font-weight: bold;
                color: {color};
                text-align: center;
                line-height: 105px; 
                z-index: 1; /* keep text above everything */
                box-sizing: border-box;
            ">
                {percent}%
            </div>
        </div>
        <p style="
            margin-top: 10px;
            font-weight: 600;
            font-size: 1.1em;
            color: {color};
            text-transform: uppercase;
        ">
            {label}
        </p>
    </div>
    """
    st.markdown(style, unsafe_allow_html=True)