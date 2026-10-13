import streamlit as st
import streamlit.components.v1 as components
import uuid
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
    st.session_state.stage = "pre_test"  # 初始階段設定為前測
    st.session_state.user_id = str(uuid.uuid4())[:8] # 產生 8 碼的專屬受測者 ID
    st.session_state.hc_score = 0
    st.session_state.q_index = 0
    st.session_state.bot_style = ""
    st.session_state.messages = []

st.title("🛍️ 網購客服 AI 互動測試")

# ==========================================
# 階段一：Streamlit 原生前測 (系統自動計分與分派)
# ==========================================
if st.session_state.stage == "pre_test":
    st.write("### 步驟一：情境決策小測驗")
    st.write("請根據直覺回答以下日常情境題，系統將為您安排適合的客服人員：")
    
    questions = [
        {"q": "情境一：主管交代任務，你偏好哪種方式？", "lc": "給我清晰的步驟與明確清單。", "hc": "告訴我大方向與背景原因即可。"},
        {"q": "情境二：拒絕朋友邀約，你會怎麼說？", "lc": "我那天剛好有事，去不了。", "hc": "聽起來很棒！但我最近有點忙，我再看看喔。"}
    ]
    
    # 逐題顯示
    if st.session_state.q_index < len(questions):
        current_q = questions[st.session_state.q_index]
        st.info(f"🤔 **{current_q['q']}**", icon="💡")
        st.write("請點擊最符合您直覺的作法：")
        st.write("") 
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(current_q['lc'], key=f"lc_{st.session_state.q_index}", use_container_width=True):
                st.session_state.q_index += 1
                st.rerun()
        with col2:
            if st.button(current_q['hc'], key=f"hc_{st.session_state.q_index}", use_container_width=True):
                st.session_state.hc_score += 1 # 選了高語境選項，分數 +1
                st.session_state.q_index += 1
                st.rerun()
    else:
        # 🔥 核心邏輯：測驗結束，根據 hc_score 精準配對機器人風格
        if st.session_state.hc_score >= 1:
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
    
    # 1. 根據前測分派的風格，設定 AI 的系統人設
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
            
            # 使用 GPT-4o-mini 並加入 temperature 控制
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.3
            )
            bot_reply = response.choices[0].message.content
            message_placeholder.markdown(bot_reply)
        
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
    st.divider()
    
    # 4. 互動次數防呆機制 (設定至少要對話 3 次)
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
# 階段三：嵌入後測 Google 表單 (自動帶入 ID、風格與分數)
# ==========================================
elif st.session_state.stage == "finish":
    st.success("🎉 對話任務已完成！非常感謝您的配合。")
    st.write("### 步驟三：完成滿意度問卷")
    st.write("請直接在下方框框內填寫最後的問卷，填寫完畢並按下「提交」即完成本次實驗。")
    
    # ⚠️【非常重要】你要修改的地方在這裡 ⬇️
    # 1. 替換成你真實的表單網址 (保留 /viewform?embedded=true)
    # 2. 找出表單題目對應的 entry.碼，把 11111, 22222, 33333 換掉
    base_form_url = "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform?embedded=true"
    
    post_test_form_url = (
        f"{base_form_url}"
        f"&entry.11111={st.session_state.user_id}"       # 傳送受測者 ID
        f"&entry.22222={st.session_state.bot_style}"     # 傳送分配到的機器人風格
        f"&entry.33333={st.session_state.hc_score}"      # 傳送前測高語境分數
    )
    
    # 嵌入 Google 表單 (height=1200 可確保手機版不用瘋狂滑動)
    components.iframe(post_test_form_url, width=700, height=1200, scrolling=True)
    
    st.divider()
    # 開放給受測者前，可將此除錯按鈕註解掉
    if st.button("重新開始一筆新測試 (僅供測試除錯用)"):
        st.session_state.clear()
        st.rerun()
