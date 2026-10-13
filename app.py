import streamlit as st
import random
import streamlit.components.v1 as components  # 引入嵌入外部網頁的套件
from openai import OpenAI

# ==========================================
# 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="AI 客服互動體驗研究", 
    page_icon="💬",          
    layout="centered"
)

# ==========================================
# 透過 Streamlit Secrets 安全地讀取 API Key
# ==========================================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 初始化 session_state 變數，控制實驗流程
if "stage" not in st.session_state:
    st.session_state.stage = "welcome"  # 初始階段：歡迎與前測
    # 隨機分配機器人風格（測試時若想指定，可自行將這行改為寫死字串）
    st.session_state.bot_style = random.choice(["高語境 (High-Context)", "低語境 (Low-Context)"])
    st.session_state.messages = []

st.title("AI 聊天機器人溝通風格體驗研究")

# ==========================================
# 階段一：填寫前測 Google 表單 (嵌入版)
# ==========================================
if st.session_state.stage == "welcome":
    st.write("### 步驟一：填寫基本資料與前測")
    st.write("歡迎參與本次研究！請直接在下方框框內填寫語境測量問卷，填寫完畢請務必點擊表單最下方的「繼續」。")
    
    # ⬇️ 請將此處替換為你的【前測 Google 表單連結】 (記得網址結尾要有 ?embedded=true) ⬇️
    pre_test_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdBo7-W-GAzfvIeo1oZWWL1CG6gvJJSoSq871WpVA0gRon74A/viewform?usp=header?embedded=true"
    
    # 在網頁中嵌入表單 (可根據需要調整 height 高度)
    components.iframe(pre_test_form_url, width=800, height=1200, scrolling=True)
    
    st.divider()
    st.warning("⚠️ **請確認您已經在上方表單內按下「繼續」按鈕，再點擊下方的開始按鈕！**")
    
    if st.button("✅ 我已確實送出表單，開始對話任務", type="primary", use_container_width=True):
        st.session_state.stage = "chat_task"
        st.rerun()

# ==========================================
# 階段二：核心對話任務 (真實 AI 串接版)
# ==========================================
elif st.session_state.stage == "chat_task":
    st.write("### 步驟二：客服互動體驗")
    
    st.info(
        "💡 **【任務情境說明】**\n\n"
        "假設您上週在網路商城買了一件**「衣服」**，但收到包裹後發現**「衣服上有明顯的瑕疵（例如破洞或大片污漬）」**。\n\n"
        "👉 **您的任務：** 請透過下方的對話框，向客服機器人說明商品狀況，並**詢問該如何辦理退貨或換貨**。\n\n"
        "*(請盡量像平常遇到客訴情況一樣，自然地與機器人進行對話)*",
        icon="👕"
    )
    
    # 1. 根據分派的風格，設定 AI 的系統人設
    if "system_prompt_set" not in st.session_state:
        if st.session_state.bot_style == "高語境 (High-Context)":
            sys_prompt = """你是一家網路商城的客服，請嚴格遵循以下「高語境溝通」規則來回覆使用者：
            1. 社交客套與招呼：在解答問題前，必須先進行溫暖的社交問候與閒聊，建立對話關係背景。
            2. 委婉與緩和表達：避免過於直接的拒絕或字眼，改用緩和修飾語、抱歉與同理心詞彙以維持和諧。
            3. 非語言與情感線索：頻繁且適當地融入表情符號（Emojis），模擬人類對話中的面部表情與情緒線索。
            4. 情感協助與共感：表現出主動傾聽與同理心，營造專屬私密對話夥伴的陪伴氛圍與安全空間。
            5. 情境脈絡補充：回覆時適度補充背景原因、故事性說明或關懷提醒，提供豐富的情境資訊。"""
        else:
            sys_prompt = """你是一家網路商城的客服，請嚴格遵循以下「低語境溝通」規則來回覆使用者：
            1. 直接開門見山：省略所有社交閒聊與客套話，第一句話即直接給出問題的核心解答。
            2. 語言明確與精準：用字極度精準、客觀且無模糊空間，所有訊息均明示於文字編碼中，不留言外之意。
            3. 結構化與簡潔版面：善用條列式與清晰結構呈現資訊，方便快速擷取重點。
            4. 客觀與對話控制：保持專業客觀語氣，不添加個人情感評價，給予使用者高度的對話流程掌控權。"""
        
        st.session_state.messages.append({"role": "system", "content": sys_prompt})
        st.session_state.system_prompt_set = True

    # 2. 顯示對話紀錄
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    # 3. 接收使用者輸入與呼叫 API
    if prompt := st.chat_input("請輸入您的訊息... (例如：你好，我收到的衣服上面有破洞)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.3
            )
            
            bot_reply = response.choices[0].message.content
            message_placeholder.markdown(bot_reply)
        
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
    st.divider()
    
    # 4. 互動次數防呆機制
    user_msg_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
    MIN_INTERACTIONS = 5
    
    if user_msg_count >= MIN_INTERACTIONS:
        if st.button("✅ 任務已完成，結束對話並進行後測", type="primary", use_container_width=True):
            st.session_state.stage = "finish"
            st.rerun()
    else:
        remain = MIN_INTERACTIONS - user_msg_count
        if user_msg_count == 0:
            st.caption(f"👈 請在下方輸入框與客服對話。為確保體驗完整，請至少進行 **{MIN_INTERACTIONS} 次** 訊息傳送。")
        else:
            st.caption(f"💬 對話進行中... 請**再發送 {remain} 則訊息**與機器人互動，結束任務的按鈕就會出現喔！")

# ==========================================
# 階段三：填寫後測 Google 表單 (嵌入版)
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 對話任務已完成！非常感謝您的配合。")
    st.write("### 步驟三：完成後測問卷")
    st.write("請直接在下方框框內填寫最後的滿意度問卷，填寫完畢並按下「提交」即完成本次實驗。")
    
    # 提示受測者他們遇到的風格，以便回答問卷
    st.info(f"💡 提醒您：您剛才體驗的機器人風格為 **{st.session_state.bot_style}**。若問卷中有詢問，請以此為準填寫喔！")
    
    # ⬇️ 請將此處替換為你的【後測 Google 表單連結】 (記得網址結尾要有 ?embedded=true) ⬇️
    post_test_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdBo7-W-GAzfvIeo1oZWWL1CG6gvJJSoSq871WpVA0gRon74A/viewform?usp=header?embedded=true"
    
    # 嵌入後測表單
    components.iframe(post_test_form_url, width=800, height=1200, scrolling=True)
    
    st.divider()
    if st.button("重新開始一筆新測試"):
        st.session_state.clear()
        st.rerun()
