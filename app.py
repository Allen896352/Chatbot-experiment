import streamlit as st
import streamlit.components.v1 as components
import uuid
import random
from openai import OpenAI

# ==========================================
# 網頁基本設定 (必須放在最上方)
# ==========================================
st.set_page_config(
    page_title="AI 客服互動體驗研究", 
    page_icon="💬",          
    layout="centered"
)

# 透過 Streamlit Secrets 讀取 API Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 初始化 session_state 變數，控制實驗流程與儲存資料
if "stage" not in st.session_state:
    st.session_state.stage = "pre_test"  
    st.session_state.user_id = str(uuid.uuid4())[:8] # 產生 8 碼的專屬受測者 ID
    st.session_state.hc_score = 0
    st.session_state.lc_score = 0
    st.session_state.bot_style = ""
    st.session_state.messages = []

st.title("🛍️ 網購客服 AI 互動測試")

# ==========================================
# 階段一：語境判斷 (隨機打亂題目 + 7分量表)
# ==========================================
if st.session_state.stage == "pre_test":
    st.write("### 步驟一：語境判斷")
    st.write("請根據您平時的溝通習慣，評估以下描述（1=非常不同意，7=非常同意）：")
    
    # 1. 建立題庫：標註每題的屬性 (HC=高語境, LC=低語境)
    if "shuffled_questions" not in st.session_state:
        questions = [
            {"id": "q1", "text": "即使別人沒有直接說出來，我也能察覺他們的意思。", "type": "HC"},
            {"id": "q2", "text": "我習慣以間接的方式進行溝通。", "type": "HC"},
            {"id": "q3", "text": "當被逼問意見時，我會以模稜兩可的立場來回應。", "type": "HC"},
            {"id": "q4", "text": "我在與他人溝通時會盡力保持關係的和諧。", "type": "HC"},
            {"id": "q5", "text": "我在溝通時喜歡精確無誤。", "type": "LC"},
            {"id": "q6", "text": "我是一個表達非常精準的溝通者。", "type": "LC"},
            {"id": "q7", "text": "我是一個極度開放的溝通者。", "type": "LC"},
            {"id": "q8", "text": "我很樂意向他人透露關於我自己的私事。", "type": "LC"}
        ]
        random.shuffle(questions)
        st.session_state.shuffled_questions = questions

    # 2. 建立作答表單
    with st.form("context_test_form"):
        options = [1, 2, 3, 4, 5, 6, 7] 
        responses = {}
        
        for i, q in enumerate(st.session_state.shuffled_questions):
            responses[q["id"]] = st.radio(f"**{i+1}. {q['text']}**", options, horizontal=True)
            st.write("") 
            
        submitted = st.form_submit_button("✅ 送出並開始對話", type="primary", use_container_width=True)
        
        if submitted:
            hc_total = 0
            lc_total = 0
            
            # 3. 系統自動分類計分
            for q in st.session_state.shuffled_questions:
                score = responses[q["id"]]
                if q["type"] == "HC":
                    hc_total += score
                else:
                    lc_total += score
                    
            st.session_state.hc_score = hc_total
            st.session_state.lc_score = lc_total
            
            # 4. 判定邏輯
            if hc_total >= lc_total:
                st.session_state.bot_style = "高語境 (High-Context)"
            else:
                st.session_state.bot_style = "低語境 (Low-Context)"
                
            st.session_state.stage = "chat_task"
            st.rerun()

# ==========================================
# 階段二：核心對話任務 (依據測驗結果配對)
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

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    if prompt := st.chat_input("請輸入您的訊息..."):
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
    
    user_msg_count = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
    MIN_INTERACTIONS = 3
    
    if user_msg_count >= MIN_INTERACTIONS:
        if st.button("✅ 任務已完成，結束對話並進行問卷", type="primary", use_container_width=True):
            st.session_state.stage = "finish"
            st.rerun()
    else:
        remain = MIN_INTERACTIONS - user_msg_count
        if user_msg_count == 0:
            st.caption(f"👈 請在下方輸入框與客服對話。需至少進行 **{MIN_INTERACTIONS} 次** 訊息傳送才會出現結束按鈕。")
        else:
            st.caption(f"💬 對話進行中... 請**再發送 {remain} 則訊息**與機器人互動。")

# ==========================================
# 階段三：嵌入後測 Google 表單 
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 對話任務已完成！非常感謝您的配合。")
    st.write("### 步驟三：完成滿意度問卷")
    st.write("請直接在下方框框內填寫最後的問卷，填寫完畢並按下「提交」即完成本次實驗。")
    
    # ⚠️ 替換成你的 Google 表單網址與 entry ID
    base_form_url = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?embedded=true"
    
    post_test_form_url = (
        f"{base_form_url}"
        f"&entry.11111={st.session_state.user_id}"       
        f"&entry.22222={st.session_state.bot_style}"     
        f"&entry.33333={st.session_state.hc_score}"      
        f"&entry.44444={st.session_state.lc_score}"      
    )
    
    components.iframe(post_test_form_url, width=700, height=1200, scrolling=True)
    
    st.divider()
    if st.button("重新開始一筆新測試 (僅供測試除錯用)"):
        st.session_state.clear()
        st.rerun()
