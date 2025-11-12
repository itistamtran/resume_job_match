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
                width: 105px;
                height: 105px;
                border-radius: 50%;
                background-color: #0e1117;  /* inner hole for thinner ring */
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5em;
                font-weight: bold;
                color: {color};
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